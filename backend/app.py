# -*- coding: utf-8 -*-
"""
分单系统 - Flask 后端（管理员账号登录，员工微信登录适配待接入）
所有数据存 SQLite，API 供前端调用
"""
import os
import time
import uuid
import hashlib
import secrets
from functools import wraps
from decimal import Decimal, InvalidOperation
from datetime import date, datetime, timedelta, timezone
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

try:
    from .wechat import WechatClient, WechatCredentials, WechatServiceError
except ImportError:  # 兼容直接执行 backend/app.py
    from wechat import WechatClient, WechatCredentials, WechatServiceError

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
# 仅加载本机、且已被 Git 忽略的配置文件；部署环境变量优先。
load_dotenv(os.path.join(basedir, ".env"), override=False)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'data.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(32)

cors_origins = [
    value.strip()
    for value in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if value.strip()
]
CORS(app, origins=cors_origins, supports_credentials=False,
     allow_headers=["Content-Type", "Authorization"])
db = SQLAlchemy(app)
_wechat_client = None


def utcnow():
    """数据库统一保存无时区 UTC，界面层按 Asia/Shanghai 展示。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)


# ======================== 数 据 库 模 型 ========================

class User(TimestampMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=True)  # 仅管理员使用账号
    password_hash = db.Column(db.String(256), nullable=True)  # 员工使用微信手机号登录
    role = db.Column(db.String(20), nullable=False)  # admin / employee
    display_name = db.Column(db.String(80), nullable=False)  # 显示姓名
    phone = db.Column(db.String(20), unique=True, nullable=True)  # 手机号（与username同步）
    wechat_openid = db.Column(db.String(100), unique=True, nullable=True)
    token = db.Column(db.String(64), unique=True, nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)


class CargoType(TimestampMixin, db.Model):
    __tablename__ = "cargo_types"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    default_unit = db.Column(db.String(50), default="")
    is_active = db.Column(db.Boolean, nullable=False, default=True)


class UnitType(TimestampMixin, db.Model):
    __tablename__ = "unit_types"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)


class Batch(TimestampMixin, db.Model):
    __tablename__ = "batches"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    reference_name = db.Column(db.String(200), nullable=False, default="")
    arrival_date = db.Column(db.Date, nullable=False)
    source_type = db.Column(db.String(20), nullable=False, default="manual")
    status = db.Column(db.String(20), nullable=False, default="进行中", index=True)
    batch_remark = db.Column(db.String(500), nullable=False, default="")
    closed_at = db.Column(db.DateTime, nullable=True)

    @property
    def arrival_time(self):
        return self.arrival_date.isoformat() if self.arrival_date else ""

    @arrival_time.setter
    def arrival_time(self, value):
        if isinstance(value, date):
            self.arrival_date = value
        else:
            self.arrival_date = date.fromisoformat(str(value))


class BatchItem(TimestampMixin, db.Model):
    __tablename__ = "batch_items"
    __table_args__ = (db.UniqueConstraint("batch_id", "name", name="uq_batch_item_name"),)
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("batches.id"), nullable=False)
    cargo_type_id = db.Column(db.Integer, db.ForeignKey("cargo_types.id"), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    unit = db.Column(db.String(50), nullable=False, default="")
    company_quantity = db.Column(db.Numeric(12, 1), nullable=False, default=0)
    status = db.Column(db.String(20), default="未分货")
    remark = db.Column(db.String(500), default="")
    batch = db.relationship("Batch", backref="items")


class ItemAssignment(TimestampMixin, db.Model):
    __tablename__ = "item_assignments"
    __table_args__ = (
        db.UniqueConstraint("batch_item_id", "user_id", name="uq_item_employee"),
    )
    id = db.Column(db.Integer, primary_key=True)
    batch_item_id = db.Column(db.Integer, db.ForeignKey("batch_items.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    employee_name = db.Column(db.String(80), nullable=False)
    allocated_quantity = db.Column(db.Numeric(12, 1), nullable=True)
    actual_quantity = db.Column(db.Numeric(12, 1), nullable=True)
    report_status = db.Column(db.String(30), nullable=False, default="待提交")
    reported_at = db.Column(db.DateTime, nullable=True)
    item = db.relationship("BatchItem", backref="assignments")
    user = db.relationship("User", backref="assignments")


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(50), nullable=False, index=True)
    target_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.Integer, nullable=True)
    detail = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)


# ======================== 工 具 函 数 ========================

def update_item_status(item_id):
    item = db.session.get(BatchItem, item_id)
    if not item:
        return
    assignments = ItemAssignment.query.filter(
        ItemAssignment.batch_item_id == item_id,
        ItemAssignment.allocated_quantity.isnot(None),
        ItemAssignment.allocated_quantity > 0,
    ).all()
    if not assignments:
        item.status = "未分货"
    elif all(a.report_status == "已锁定" for a in assignments):
        item.status = "已完成"
    else:
        item.status = "待报货"
    db.session.commit()


def item_dict(item):
    return {"id": item.id, "batch_id": item.batch_id, "name": item.name, "unit": item.unit, "status": item.status,
            "spec": "", "remark": item.remark,
            "company_quantity": quantity_value(item.company_quantity),
            "assignments": [assignment_dict(a) for a in ItemAssignment.query.filter_by(batch_item_id=item.id).all()]}


def assignment_dict(a):
    return {
        "id": a.id, "batch_item_id": a.batch_item_id,
        "user_id": a.user_id, "user_name": a.employee_name,
        "allocated_quantity": quantity_value(a.allocated_quantity),
        "actual_quantity": quantity_value(a.actual_quantity),
        "report_status": a.report_status,
    }


def quantity_value(value):
    if value is None:
        return None
    value = Decimal(value)
    return int(value) if value == value.to_integral() else float(value)


def datetime_value(value):
    return value.isoformat(timespec="seconds") + "Z" if value else None


def generate_token():
    raw = str(uuid.uuid4()) + str(time.time())
    return hashlib.sha256(raw.encode()).hexdigest()


def issue_token(user):
    user.token = generate_token()
    user.token_expiry = utcnow() + timedelta(days=30)


def development_login_enabled():
    """仅在显式本地开发配置下开放调试员工会话。"""
    return (
        os.getenv("APP_ENV", "").strip().lower() == "development"
        and os.getenv("DEV_LOGIN_ENABLED", "").strip().lower()
        in {"1", "true", "yes"}
    )


def development_employee_config():
    """读取服务端专用的开发员工标识；绝不接受客户端传入身份。"""
    return {
        "phone": os.getenv("DEV_LOGIN_EMPLOYEE_PHONE", "").strip(),
        "name": os.getenv("DEV_LOGIN_EMPLOYEE_NAME", "本地调试员工").strip(),
    }


def exchange_wechat_credentials(phone_code, login_code=""):
    """使用测试注入器或微信官方适配器交换手机号与 openid。"""
    exchanger = app.config.get("WECHAT_CREDENTIAL_EXCHANGER")
    if exchanger:
        result = exchanger(phone_code, login_code)
        if isinstance(result, WechatCredentials):
            return result
        return WechatCredentials(
            phone=str(result.get("phone", "")).strip(),
            openid=str(result.get("openid", "")).strip(),
        )

    global _wechat_client
    app_id = os.getenv("WECHAT_APP_ID", "").strip()
    app_secret = os.getenv("WECHAT_APP_SECRET", "").strip()
    if (_wechat_client is None or _wechat_client.app_id != app_id
            or _wechat_client.app_secret != app_secret):
        _wechat_client = WechatClient(app_id, app_secret)
    return _wechat_client.exchange_credentials(phone_code, login_code)


def user_login_dict(user):
    return {
        "id": user.id, "username": user.username,
        "role": user.role, "display_name": user.display_name,
        "phone": user.phone or "",
        "is_active": user.is_active,
        "token": user.token,
    }


def api_error(message, status=400, code="BAD_REQUEST"):
    return jsonify({"error": message, "code": code}), status


def bearer_token():
    auth_header = request.headers.get("Authorization", "")
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() == "bearer" and token.strip():
        return token.strip()
    return ""


def find_token_user(token):
    if not token:
        return None
    user = User.query.filter_by(token=token).first()
    if not user:
        return None
    if user.token_expiry and utcnow() > user.token_expiry:
        user.token = None
        user.token_expiry = None
        db.session.commit()
        return None
    return user if user.is_active else None


def auth_required(role=None):
    """在现有路由上增加统一认证，不改变原 API 路径。"""
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = find_token_user(bearer_token())
            if not user:
                return api_error("请先登录或重新登录", 401, "UNAUTHORIZED")
            if role and user.role != role:
                return api_error("没有权限执行此操作", 403, "FORBIDDEN")
            g.current_user = user
            return view(*args, **kwargs)
        return wrapped
    return decorator


def parse_quantity(value, *, allow_zero=True):
    try:
        quantity = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("数量必须是数字")
    if quantity.as_tuple().exponent < -1:
        raise ValueError("数量最多保留一位小数")
    if quantity < 0 or (not allow_zero and quantity == 0):
        raise ValueError("数量必须大于 0" if not allow_zero else "数量不能小于 0")
    return quantity


def parse_active(value):
    if not isinstance(value, bool):
        raise ValueError("启用状态必须为布尔值")
    return value


@app.after_request
def normalize_api_error(response):
    """保持旧路由可复用，同时统一所有 API 错误的 JSON 结构。"""
    if request.path.startswith("/api/") and response.status_code >= 400 and response.is_json:
        payload = response.get_json(silent=True)
        if isinstance(payload, dict) and "error" in payload and "code" not in payload:
            default_codes = {
                400: "BAD_REQUEST",
                401: "UNAUTHORIZED",
                403: "FORBIDDEN",
                404: "NOT_FOUND",
                409: "CONFLICT",
            }
            payload["code"] = default_codes.get(response.status_code, "REQUEST_FAILED")
            response.set_data(app.json.dumps(payload))
            response.content_type = "application/json; charset=utf-8"
    return response


@app.errorhandler(404)
def handle_not_found(_error):
    if request.path.startswith("/api/"):
        return api_error("请求的资源不存在", 404, "NOT_FOUND")
    return _error


@app.errorhandler(405)
def handle_method_not_allowed(_error):
    if request.path.startswith("/api/"):
        return api_error("请求方法不允许", 405, "METHOD_NOT_ALLOWED")
    return _error


@app.errorhandler(500)
def handle_internal_error(_error):
    db.session.rollback()
    if request.path.startswith("/api/"):
        return api_error("服务器处理失败", 500, "INTERNAL_ERROR")
    return _error


# ======================== 账 号 密 码 登 录 ========================

@app.route("/api/login", methods=["POST"])
def login():
    """管理员账号密码登录；员工登录在微信手机号快捷登录接口中实现。"""
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "请输入账号和密码"}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        user = User.query.filter_by(phone=username).first()

    if (not user or user.role != "admin" or not user.password_hash
            or not check_password_hash(user.password_hash, password)):
        return jsonify({"error": "账号或密码错误"}), 401

    if not user.is_active:
        return api_error("账号已停用", 403, "ACCOUNT_INACTIVE")
    issue_token(user)
    db.session.commit()
    return jsonify(user_login_dict(user))


@app.route("/api/auto-login", methods=["POST"])
def auto_login():
    data = request.get_json(silent=True) or {}
    token = bearer_token() or data.get("token", "")
    if not token:
        return jsonify({"error": "无效的令牌"}), 401
    user = User.query.filter_by(token=token).first()
    if not user:
        return jsonify({"error": "令牌无效"}), 401
    if not user.is_active:
        return api_error("账号已停用", 403, "ACCOUNT_INACTIVE")
    if user.token_expiry and utcnow() > user.token_expiry:
        user.token = None
        user.token_expiry = None
        db.session.commit()
        return jsonify({"error": "登录已过期，请重新登录"}), 401
    return jsonify(user_login_dict(user))


@app.route("/api/login/wechat-phone", methods=["POST"])
def wechat_phone_login():
    """员工使用微信一次性手机号凭证登录，不接受客户端直接提交手机号。"""
    data = request.get_json(silent=True) or {}
    phone_code = str(data.get("phone_code", "")).strip()
    login_code = str(data.get("login_code", "")).strip()
    if not phone_code:
        return api_error("请先授权获取微信手机号", 400, "PHONE_AUTH_REQUIRED")

    try:
        credentials = exchange_wechat_credentials(phone_code, login_code)
    except WechatServiceError as exc:
        return api_error(str(exc), exc.status, exc.code)
    except Exception:
        return api_error("微信登录暂时不可用，请稍后重试", 502, "WECHAT_SERVICE_ERROR")

    if not credentials.phone:
        return api_error("未能获取手机号，请重新授权", 400, "PHONE_AUTH_REQUIRED")
    employee = User.query.filter_by(
        phone=credentials.phone, role="employee"
    ).first()
    if not employee:
        return api_error(
            "未找到员工信息，请联系管理员", 403, "EMPLOYEE_NOT_FOUND"
        )
    if not employee.is_active:
        return api_error("账号已停用，请联系管理员", 403, "ACCOUNT_INACTIVE")

    if credentials.openid:
        bound = User.query.filter(
            User.wechat_openid == credentials.openid,
            User.id != employee.id,
        ).first()
        if bound:
            return api_error(
                "该微信已绑定其他员工，请联系管理员",
                409,
                "WECHAT_ALREADY_BOUND",
            )
        employee.wechat_openid = credentials.openid
    issue_token(employee)
    db.session.commit()
    return jsonify(user_login_dict(employee))


@app.route("/api/dev/login/employee", methods=["POST"])
def development_employee_login():
    """为本地调试指定员工签发正常会话；生产环境中不可访问。"""
    if not development_login_enabled():
        return api_error("请求的资源不存在", 404, "NOT_FOUND")

    config = development_employee_config()
    if not config["phone"]:
        return api_error("未配置本地调试员工", 503, "DEV_LOGIN_NOT_CONFIGURED")

    employee = User.query.filter_by(
        phone=config["phone"], role="employee"
    ).first()
    if not employee:
        return api_error("本地调试员工不存在", 503, "DEV_LOGIN_EMPLOYEE_NOT_FOUND")
    if not employee.is_active:
        return api_error("本地调试员工已停用", 403, "ACCOUNT_INACTIVE")

    issue_token(employee)
    db.session.commit()
    return jsonify(user_login_dict(employee))


# ======================== 基础信息：货品种类 ========================

@app.route("/api/cargo-types", methods=["GET"])
@auth_required("admin")
def list_cargo_types():
    types = CargoType.query.order_by(CargoType.id).all()
    return jsonify([{"id": t.id, "name": t.name, "default_unit": t.default_unit,
                     "is_active": t.is_active} for t in types])


@app.route("/api/cargo-types", methods=["POST"])
@auth_required("admin")
def create_cargo_type():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    default_unit = str(data.get("default_unit", "")).strip()
    if not name:
        return jsonify({"error": "种类名称不能为空"}), 400
    if CargoType.query.filter_by(name=name).first():
        return jsonify({"error": "货品种类已存在"}), 400
    ct = CargoType(name=name, default_unit=default_unit)
    db.session.add(ct)
    db.session.commit()
    return jsonify({"id": ct.id, "message": "货品种类已添加"})


@app.route("/api/cargo-types/<int:cid>", methods=["PUT"])
@auth_required("admin")
def update_cargo_type(cid):
    ct = CargoType.query.get_or_404(cid)
    data = request.get_json(silent=True) or {}
    if "name" in data:
        name = str(data["name"]).strip()
        if not name:
            return api_error("种类名称不能为空")
        existing = CargoType.query.filter_by(name=name).first()
        if existing and existing.id != cid:
            return api_error("货品种类已存在")
        ct.name = name
    if "default_unit" in data:
        ct.default_unit = str(data["default_unit"]).strip()
    if "is_active" in data:
        try:
            ct.is_active = parse_active(data["is_active"])
        except ValueError as exc:
            return api_error(str(exc))
    db.session.commit()
    return jsonify({"message": "已更新"})


@app.route("/api/cargo-types/<int:cid>", methods=["DELETE"])
@auth_required("admin")
def delete_cargo_type(cid):
    ct = CargoType.query.get_or_404(cid)
    ct.is_active = False
    db.session.commit()
    return jsonify({"message": "已停用"})


# ======================== 基础信息：单位管理 ========================

@app.route("/api/unit-types", methods=["GET"])
@auth_required("admin")
def list_unit_types():
    units = UnitType.query.order_by(UnitType.id).all()
    return jsonify([{"id": u.id, "name": u.name, "is_active": u.is_active} for u in units])


@app.route("/api/unit-types", methods=["POST"])
@auth_required("admin")
def create_unit_type():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    if not name:
        return jsonify({"error": "单位名称不能为空"}), 400
    if UnitType.query.filter_by(name=name).first():
        return jsonify({"error": "单位已存在"}), 400
    ut = UnitType(name=name)
    db.session.add(ut)
    db.session.commit()
    return jsonify({"id": ut.id, "message": "单位已添加"})


@app.route("/api/unit-types/<int:uid>", methods=["PUT"])
@auth_required("admin")
def update_unit_type(uid):
    ut = UnitType.query.get_or_404(uid)
    data = request.get_json(silent=True) or {}
    if "name" in data:
        name = str(data["name"]).strip()
        if not name:
            return api_error("单位名称不能为空")
        existing = UnitType.query.filter_by(name=name).first()
        if existing and existing.id != uid:
            return api_error("单位已存在")
        ut.name = name
    if "is_active" in data:
        try:
            ut.is_active = parse_active(data["is_active"])
        except ValueError as exc:
            return api_error(str(exc))
    db.session.commit()
    return jsonify({"message": "已更新"})


@app.route("/api/unit-types/<int:uid>", methods=["DELETE"])
@auth_required("admin")
def delete_unit_type(uid):
    ut = UnitType.query.get_or_404(uid)
    ut.is_active = False
    db.session.commit()
    return jsonify({"message": "已停用"})


# ======================== 管理员：人员管理 (CRUD 手机号强制 & 包含管理员编辑) ========================

@app.route("/api/employees", methods=["GET"])
@auth_required("admin")
def list_employees():
    """查：获取所有用户列表（包含管理员）"""
    query = User.query
    if request.args.get("active_only") in {"1", "true"}:
        query = query.filter_by(role="employee", is_active=True)
    users = query.order_by(User.id).all()
    return jsonify(
        [{"id": u.id, "display_name": u.display_name, "username": u.username, "phone": u.phone or "", "role": u.role,
          "is_active": u.is_active}
         for u in users])


@app.route("/api/employees", methods=["POST"])
@auth_required("admin")
def create_employee():
    """新增员工；手机号用于微信快捷登录匹配，不创建员工密码。"""
    data = request.get_json(silent=True) or {}
    phone = str(data.get("phone") or data.get("username") or "").strip()
    display_name = str(data.get("display_name", "")).strip()

    if not phone or len(phone) != 11 or not phone.isdigit():
        return jsonify({"error": "手机号必须是11位数字"}), 400
    if not display_name:
        return jsonify({"error": "员工姓名不能为空"}), 400

    if User.query.filter_by(phone=phone).first():
        return jsonify({"error": "该手机号已存在"}), 400

    user = User(
        username=None,
        phone=phone,
        password_hash=None,
        role="employee",
        display_name=display_name,
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"id": user.id, "message": "人员已添加", "phone": user.phone})


@app.route("/api/employees/<int:eid>", methods=["PUT"])
@auth_required("admin")
def update_employee(eid):
    """改：修改员工或管理员信息"""
    user = User.query.get_or_404(eid)
    data = request.get_json(silent=True) or {}

    if user.role == "employee" and ("phone" in data or "username" in data):
        phone = str(data.get("phone") or data.get("username") or "").strip()
        if len(phone) != 11 or not phone.isdigit():
            return jsonify({"error": "手机号必须是11位数字"}), 400
        existing = User.query.filter_by(phone=phone).first()
        if existing and existing.id != eid:
            return jsonify({"error": "该手机号已被其他员工占用"}), 400
        user.phone = phone

    if "display_name" in data and data["display_name"]:
        display_name = str(data["display_name"]).strip()
        if not display_name:
            return jsonify({"error": "姓名不能为空"}), 400
        user.display_name = display_name

    if user.role == "admin" and "password" in data and data["password"]:
        user.password_hash = generate_password_hash(data["password"])
    if "is_active" in data:
        try:
            is_active = parse_active(data["is_active"])
        except ValueError as exc:
            return api_error(str(exc))
        if user.role == "admin" and not is_active:
            return api_error("不能停用管理员账户")
        user.is_active = is_active
        if not user.is_active:
            user.token = None
            user.token_expiry = None

    db.session.commit()
    return jsonify({"message": "已更新"})


@app.route("/api/employees/<int:eid>", methods=["DELETE"])
@auth_required("admin")
def delete_employee(eid):
    """停用员工，保留批次历史中的人员快照和审计关系。"""
    user = User.query.get_or_404(eid)
    if user.role == "admin":
        return jsonify({"error": "不能删除管理员账户"}), 400
    user.is_active = False
    user.token = None
    user.token_expiry = None
    db.session.commit()
    return jsonify({"message": "已停用"})


# ======================== 管 理 员：批 次 ========================

@app.route("/api/batches", methods=["GET"])
@auth_required("admin")
def list_batches():
    batches = Batch.query.order_by(Batch.created_at.desc()).all()
    return jsonify([{
        "id": b.id, "name": b.name, "arrival_time": b.arrival_time,
        "created_at": datetime_value(b.created_at), "batch_remark": b.batch_remark or "",
        "reference_name": b.reference_name, "source_type": b.source_type, "status": b.status,
        "item_count": BatchItem.query.filter_by(batch_id=b.id).count(),
    } for b in batches])


@app.route("/api/batches", methods=["POST"])
@auth_required("admin")
def create_batch():
    data = request.get_json(silent=True) or {}
    if not data.get("name") or not data.get("arrival_time"):
        return jsonify({"error": "批次名称和到货时间不能为空"}), 400
    try:
        arrival_date = date.fromisoformat(str(data["arrival_time"]))
    except ValueError:
        return api_error("到货日期格式必须为 YYYY-MM-DD")
    batch = Batch(
        name=str(data["name"]).strip(),
        reference_name=str(data.get("reference_name", "")).strip(),
        arrival_date=arrival_date,
        source_type=data.get("source_type", "manual"),
        batch_remark=data.get("batch_remark", ""),
    )
    db.session.add(batch)
    db.session.flush()
    for it in data.get("items", []):
        try:
            company_quantity = parse_quantity(it.get("company_quantity", 0), allow_zero=True)
        except ValueError as exc:
            db.session.rollback()
            return api_error(str(exc))
        db.session.add(BatchItem(
            batch_id=batch.id, cargo_type_id=it.get("cargo_type_id"),
            name=it["name"], unit=it.get("unit", ""),
            company_quantity=company_quantity, remark=it.get("remark", ""),
        ))
    db.session.commit()
    return jsonify({"id": batch.id, "message": "批次创建成功"})


@app.route("/api/batches/<int:bid>", methods=["DELETE"])
@auth_required("admin")
def delete_batch(bid):
    batch = Batch.query.get_or_404(bid)
    items = BatchItem.query.filter_by(batch_id=bid).all()
    for item in items:
        ItemAssignment.query.filter_by(batch_item_id=item.id).delete()
    BatchItem.query.filter_by(batch_id=bid).delete()
    db.session.delete(batch)
    db.session.commit()
    return jsonify({"message": "批次已删除"})


@app.route("/api/batches/<int:bid>", methods=["PUT"])
@auth_required("admin")
def update_batch(bid):
    batch = Batch.query.get_or_404(bid)
    data = request.get_json(silent=True) or {}
    if "name" in data:
        batch.name = data["name"]
    if "arrival_time" in data:
        try:
            batch.arrival_date = date.fromisoformat(str(data["arrival_time"]))
        except ValueError:
            return api_error("到货日期格式必须为 YYYY-MM-DD")
    if "batch_remark" in data:
        batch.batch_remark = data["batch_remark"]
    db.session.commit()
    return jsonify({"message": "批次已更新", "id": batch.id})


@app.route("/api/batches/<int:bid>/items", methods=["GET"])
@auth_required("admin")
def list_items(bid):
    items = BatchItem.query.filter_by(batch_id=bid).all()
    cargo_types = CargoType.query.filter_by(is_active=True).all()
    existing_names = {i.name for i in items}
    for ct in cargo_types:
        if ct.name not in existing_names:
            item = BatchItem(batch_id=bid, cargo_type_id=ct.id, name=ct.name,
                             unit=ct.default_unit or "", company_quantity=0)
            db.session.add(item)
            db.session.flush()
            items.append(item)
            existing_names.add(ct.name)
    if cargo_types:
        db.session.commit()
        items = BatchItem.query.filter_by(batch_id=bid).all()
    return jsonify([item_dict(i) for i in items])


@app.route("/api/batches/<int:bid>/items", methods=["POST"])
@auth_required("admin")
def add_item(bid):
    data = request.get_json(silent=True) or {}
    if not data.get("name") or not data.get("unit"):
        return jsonify({"error": "货品名称与单位不能为空"}), 400
    try:
        company_quantity = parse_quantity(data.get("company_quantity", 0), allow_zero=True)
    except ValueError as exc:
        return api_error(str(exc))
    item = BatchItem(batch_id=bid, cargo_type_id=data.get("cargo_type_id"),
                     name=data["name"], unit=data["unit"],
                     company_quantity=company_quantity, remark=data.get("remark", ""))
    db.session.add(item)
    db.session.commit()
    return jsonify(item_dict(item))


@app.route("/api/items/<int:iid>", methods=["DELETE"])
@auth_required("admin")
def delete_item(iid):
    item = BatchItem.query.get_or_404(iid)
    ItemAssignment.query.filter_by(batch_item_id=iid).delete()
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "货品已删除"})


@app.route("/api/items/<int:iid>/assignments", methods=["PUT"])
@auth_required("admin")
def save_assignments(iid):
    data = request.get_json(silent=True) or []
    if isinstance(data, dict):
        data = data.get("assignments", [])
    if not isinstance(data, list):
        return api_error("分货数据格式不正确")
    item = BatchItem.query.get_or_404(iid)
    existing = {row.user_id: row for row in ItemAssignment.query.filter_by(batch_item_id=iid).all()}
    keep_user_ids = set()
    requested = []
    for source in data:
        user_id = source.get("user_id") or source.get("employee_id")
        raw_quantity = source.get("allocated_quantity", source.get("quantity"))
        if not user_id:
            return api_error("员工分货记录缺少员工")
        if user_id in keep_user_ids:
            return api_error("同一员工不能重复分货")
        try:
            allocated = parse_quantity(raw_quantity, allow_zero=False)
        except ValueError as exc:
            if raw_quantity in (None, "", 0, "0", "0.0"):
                continue
            return api_error(str(exc))
        user = User.query.filter_by(id=user_id, role="employee", is_active=True).first()
        if not user:
            return api_error("分货员工不存在")
        row = existing.get(user_id)
        if row and row.report_status == "已锁定" and Decimal(str(row.allocated_quantity)) != allocated:
            return api_error("已提交报货的记录必须先由管理员解锁")
        requested.append((user, row, allocated))
        keep_user_ids.add(user_id)
    total_allocated = sum((entry[2] for entry in requested), Decimal("0"))
    if total_allocated > Decimal(item.company_quantity):
        return api_error("总分货数量不能大于分给公司的数量")
    for user, row, allocated in requested:
        if not row:
            row = ItemAssignment(batch_item_id=item.id, user_id=user.id,
                                 employee_name=user.display_name)
            db.session.add(row)
        row.employee_name = user.display_name
        row.allocated_quantity = allocated
    for user_id, row in existing.items():
        if user_id not in keep_user_ids:
            if row.report_status == "已锁定":
                return api_error("已提交报货的记录不能直接移除")
            db.session.delete(row)
    db.session.commit()
    update_item_status(iid)
    return jsonify({"message": "分配已保存"})


@app.route("/api/items/<int:iid>/assignments", methods=["GET"])
@auth_required("admin")
def get_assignments(iid):
    return jsonify([assignment_dict(a) for a in ItemAssignment.query.filter_by(batch_item_id=iid).all()])


# ======================== 管 理 员：报 表 ========================

@app.route("/api/batches/<int:bid>/report", methods=["GET"])
@auth_required("admin")
def batch_report(bid):
    batch = Batch.query.get_or_404(bid)
    items = BatchItem.query.filter_by(batch_id=bid).all()
    details = []
    for item in items:
        assignments = ItemAssignment.query.filter_by(batch_item_id=item.id).all()
        total = sum((a.actual_quantity for a in assignments if a.actual_quantity is not None), Decimal("0"))
        details.append({
            "item_name": item.name, "item_unit": item.unit, "item_status": item.status,
            "item_spec": "", "item_remark": item.remark,
            "assignments": [assignment_dict(a) for a in assignments],
            "total_actual": quantity_value(total),
        })
    return jsonify({
        "batch_name": batch.name, "arrival_time": batch.arrival_time,
        "created_at": datetime_value(batch.created_at), "details": details,
    })


@app.route("/api/summary", methods=["GET"])
@auth_required("admin")
def global_summary():
    from sqlalchemy import func
    rows = db.session.query(
        BatchItem.name, BatchItem.unit,
        func.sum(ItemAssignment.actual_quantity).label("total_actual")
    ).join(ItemAssignment, ItemAssignment.batch_item_id == BatchItem.id) \
        .filter(ItemAssignment.actual_quantity.isnot(None)) \
        .group_by(BatchItem.name, BatchItem.unit).all()
    return jsonify([{"name": r[0], "unit": r[1], "total_actual": quantity_value(r[2] or 0)} for r in rows])


# ======================== 员 工 功能 ========================

@app.route("/api/employee/tasks", methods=["GET"])
@auth_required("employee")
def employee_tasks():
    uid = g.current_user.id
    assignments = ItemAssignment.query.filter_by(user_id=uid).all()
    result = []
    for a in assignments:
        item = BatchItem.query.get(a.batch_item_id)
        if not item:
            continue
        batch = Batch.query.get(item.batch_id)
        result.append({
            "assignment_id": a.id, "batch_name": batch.name,
            "arrival_time": batch.arrival_time,
            "item_name": item.name, "item_unit": item.unit,
            "allocated_quantity": quantity_value(a.allocated_quantity),
            "actual_quantity": quantity_value(a.actual_quantity),
            "report_status": a.report_status,
            "item_status": item.status, "batch_item_id": item.id,
        })
    return jsonify(result)


@app.route("/api/employee/submit", methods=["POST"])
@auth_required("employee")
def employee_submit():
    data = request.get_json(silent=True) or {}
    assignment_id = data.get("assignment_id")
    if not assignment_id:
        return api_error("缺少报货任务")
    assignment = ItemAssignment.query.filter_by(
        id=assignment_id, user_id=g.current_user.id
    ).first()
    if not assignment:
        return api_error("未找到本人的报货任务", 404, "NOT_FOUND")
    if assignment.report_status == "已锁定":
        return jsonify({
            "message": "该记录已提交",
            "assignment_id": assignment.id,
            "actual_quantity": quantity_value(assignment.actual_quantity),
            "item_status": assignment.item.status,
        })
    try:
        actual = parse_quantity(data.get("actual_quantity"), allow_zero=True)
    except ValueError as exc:
        return api_error(str(exc))
    if actual > Decimal(str(assignment.allocated_quantity)):
        return api_error("报货数量不能大于分货数量")
    assignment.actual_quantity = actual
    assignment.report_status = "已锁定"
    assignment.reported_at = utcnow()
    db.session.commit()
    update_item_status(assignment.batch_item_id)
    return jsonify({
        "message": "报货成功",
        "assignment_id": assignment.id,
        "actual_quantity": quantity_value(assignment.actual_quantity),
        "item_status": assignment.item.status,
    })


@app.route("/api/employee/my-batches", methods=["GET"])
@auth_required("employee")
def employee_my_batches():
    uid = g.current_user.id
    batch_ids = db.session.query(BatchItem.batch_id).join(ItemAssignment).filter(
        ItemAssignment.user_id == uid, ItemAssignment.allocated_quantity > 0
    ).distinct().all()
    batch_ids = [b[0] for b in batch_ids]
    batches = Batch.query.filter(Batch.id.in_(batch_ids)).order_by(Batch.created_at.desc()).all()
    return jsonify([{
        "id": b.id, "name": b.name, "arrival_time": b.arrival_time,
        "item_count": BatchItem.query.filter_by(batch_id=b.id).count(),
        "created_at": datetime_value(b.created_at),
    } for b in batches])


@app.route("/api/employee/my-items", methods=["GET"])
@auth_required("employee")
def employee_my_items():
    uid = g.current_user.id
    bid = request.args.get("batch_id", type=int)
    if not bid:
        return jsonify({"error": "缺少参数"}), 400
    assignments = ItemAssignment.query.join(BatchItem).filter(
        BatchItem.batch_id == bid,
        ItemAssignment.user_id == uid,
        ItemAssignment.allocated_quantity > 0,
    ).all()
    result = []
    for my_assign in assignments:
        item = my_assign.item
        result.append({
            "item_id": item.id, "item_name": item.name,
            "item_unit": item.unit, "item_spec": "",
            "item_remark": item.remark, "item_status": item.status,
            "allocated_quantity": quantity_value(my_assign.allocated_quantity),
            "actual_quantity": quantity_value(my_assign.actual_quantity),
            "report_status": my_assign.report_status,
            "assignment_id": my_assign.id,
        })
    return jsonify(result)


# ======================== 统 计 ========================

@app.route("/api/stats", methods=["GET"])
@auth_required("admin")
def get_stats():
    all_items = BatchItem.query.all()
    total_batches = Batch.query.count()
    total_items = len(all_items)
    pending = sum(1 for i in all_items if i.status == "待报货")
    done = sum(1 for i in all_items if i.status == "已完成")
    return jsonify(
        {"totalBatches": total_batches, "totalItems": total_items, "pendingItems": pending, "doneItems": done})


# ======================== 初始化数据库 ========================


def init_db():
    db.create_all()

    admin_username = os.getenv("ADMIN_USERNAME", "").strip()
    admin_password = os.getenv("ADMIN_PASSWORD", "")
    if bool(admin_username) != bool(admin_password):
        raise RuntimeError("ADMIN_USERNAME 与 ADMIN_PASSWORD 必须同时配置")
    if admin_username and admin_password:
        admin = User.query.filter_by(role="admin").first()
        if not admin:
            admin = User(role="admin", display_name=os.getenv("ADMIN_DISPLAY_NAME", "管理员"))
            db.session.add(admin)
        admin.username = admin_username
        admin.phone = None
        admin.password_hash = generate_password_hash(admin_password)

    # 测试员工只在两个开发开关均明确开启时创建，生产环境绝不生成。
    if development_login_enabled():
        dev_employee = development_employee_config()
        if not dev_employee["phone"]:
            raise RuntimeError("开发登录已开启但未配置 DEV_LOGIN_EMPLOYEE_PHONE")
        if len(dev_employee["phone"]) != 11 or not dev_employee["phone"].isdigit():
            raise RuntimeError("DEV_LOGIN_EMPLOYEE_PHONE 必须是 11 位数字")
        employee = User.query.filter_by(phone=dev_employee["phone"]).first()
        if not employee:
            db.session.add(User(
                username=None,
                password_hash=None,
                role="employee",
                display_name=dev_employee["name"] or "本地调试员工",
                phone=dev_employee["phone"],
                is_active=True,
            ))

    db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() in {"1", "true", "yes"},
    )
