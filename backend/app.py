# -*- coding: utf-8 -*-
"""
分单系统 - Flask 后端
所有数据存 SQLite，API 供前端调用
"""
import os
import random
import time
import uuid
import hashlib
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(basedir, 'data.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "fen-dan-xi-tong-2025"

CORS(app, supports_credentials=True)
db = SQLAlchemy(app)

# ======================== 数 据 库 模 型 ========================

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)        # admin / employee
    display_name = db.Column(db.String(80), nullable=False) # 显示姓名
    phone = db.Column(db.String(20), unique=True, nullable=True)  # 手机号
    wechat_openid = db.Column(db.String(100), unique=True, nullable=True) # 微信openid
    token = db.Column(db.String(64), unique=True, nullable=True)  # 登录令牌
    token_expiry = db.Column(db.DateTime, nullable=True)          # 令牌过期时间


class CargoType(db.Model):
    __tablename__ = "cargo_types"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    default_unit = db.Column(db.String(50), default="")


class UnitType(db.Model):
    __tablename__ = "unit_types"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)


class Batch(db.Model):
    __tablename__ = "batches"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)        # 如 "6月22日报货"
    arrival_time = db.Column(db.String(200), nullable=False) # 到货时间（日期）
    created_at = db.Column(db.String(30), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    batch_code = db.Column(db.String(50), default="")
    batch_remark = db.Column(db.String(500), default="")


class BatchItem(db.Model):
    __tablename__ = "batch_items"
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("batches.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)  # 货品名称
    unit = db.Column(db.String(50), nullable=False)    # 单位
    status = db.Column(db.String(20), default="未分货") # 未分货 → 未报货 → 已完成
    spec = db.Column(db.String(200), default="")
    remark = db.Column(db.String(500), default="")
    batch = db.relationship("Batch", backref="items")


class ItemAssignment(db.Model):
    __tablename__ = "item_assignments"
    id = db.Column(db.Integer, primary_key=True)
    batch_item_id = db.Column(db.Integer, db.ForeignKey("batch_items.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    allocated_quantity = db.Column(db.Float, default=0)
    actual_quantity = db.Column(db.Float, nullable=True)  # None = 员工还没填
    item = db.relationship("BatchItem", backref="assignments")
    user = db.relationship("User", backref="assignments")


# ======================== 工 具 函 数 ========================

def update_item_status(item_id):
    """根据分配和报数情况自动更新货品状态"""
    item = BatchItem.query.get(item_id)
    if not item:
        return
    assignments = ItemAssignment.query.filter_by(batch_item_id=item_id).all()
    if not assignments:
        item.status = "未分货"
    elif all(a.actual_quantity is not None for a in assignments):
        item.status = "已完成"
    else:
        item.status = "未报货"
    db.session.commit()


def item_dict(item):
    return {"id": item.id, "batch_id": item.batch_id, "name": item.name, "unit": item.unit, "status": item.status, "spec": item.spec, "remark": item.remark, "assignments": [assignment_dict(a) for a in ItemAssignment.query.filter_by(batch_item_id=item.id).all()]}


def assignment_dict(a):
    return {
        "id": a.id, "batch_item_id": a.batch_item_id,
        "user_id": a.user_id, "user_name": a.user.display_name,
        "allocated_quantity": a.allocated_quantity,
        "actual_quantity": a.actual_quantity,
    }


# ======================== 认 证 ========================

@app.route("/api/login", methods=["POST"])
def login():
    """用户名或手机号 + 密码登录"""
    data = request.json
    username = data.get("username", "")
    password = data.get("password", "")
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User.query.filter_by(phone=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "用户名/手机号或密码错误"}), 401
    user.token = generate_token()
    user.token_expiry = datetime.utcnow() + timedelta(days=30)
    db.session.commit()
    return jsonify(user_login_dict(user))

# ======================== 短信验证码登录 ========================
verification_codes = {}

def generate_token():
    raw = str(uuid.uuid4()) + str(time.time())
    return hashlib.sha256(raw.encode()).hexdigest()

def user_login_dict(user):
    return {
        "id": user.id, "username": user.username,
        "role": user.role, "display_name": user.display_name,
        "phone": user.phone or "",
        "wechat_binded": bool(user.wechat_openid),
        "token": user.token,
    }


@app.route("/api/send-code", methods=["POST"])
def send_verification_code():
    # 强制尝试解析 JSON，即使没有标准 Header，如果解析失败返回空字典 {}
    data = request.get_json(silent=True) or {}

    phone = str(data.get("phone", "")).strip()
    if not phone or len(phone) < 11:
        return jsonify({"error": "请输入正确的手机号"}), 400

    code = str(random.randint(100000, 999999))
    verification_codes[phone] = {"code": code, "expiry": time.time() + 300}
    print(f"[验证码] 手机: {phone} 验证码: {code}")
    return jsonify({"message": "验证码已发送", "debug_code": code})

@app.route("/api/login/verify-code", methods=["POST"])
def login_by_verify_code():
    data = request.json
    phone = str(data.get("phone", "")).strip()
    code = str(data.get("code", "")).strip()
    if not phone or not code:
        return jsonify({"error": "请输入手机号和验证码"}), 400
    stored = verification_codes.get(phone)
    if not stored:
        return jsonify({"error": "请先获取验证码"}), 400
    if time.time() > stored["expiry"]:
        verification_codes.pop(phone, None)
        return jsonify({"error": "验证码已过期，请重新获取"}), 400
    if stored["code"] != code:
        return jsonify({"error": "验证码错误"}), 400
    verification_codes.pop(phone, None)
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return jsonify({"error": "该手机号未注册，请联系管理员添加"}), 404
    user.token = generate_token()
    user.token_expiry = datetime.utcnow() + timedelta(days=30)
    db.session.commit()
    return jsonify(user_login_dict(user))

# ======================== 微信小程序登录 ========================

@app.route("/api/login/wechat", methods=["POST"])
def login_by_wechat():
    import requests as http_req
    data = request.json
    code = data.get("code", "")
    if not code:
        return jsonify({"error": "缺少微信code"}), 400
    if not WECHAT_SECRET:
        return jsonify({"error": "微信登录未配置（请在环境变量设置 WECHAT_SECRET）"}), 400
    resp = http_req.get(WECHAT_CODE2SESSION_URL, params={
        "appid": WECHAT_APPID, "secret": WECHAT_SECRET, "js_code": code, "grant_type": "authorization_code"
    })
    wx_data = resp.json()
    if "openid" not in wx_data:
        return jsonify({"error": "微信登录失败", "detail": wx_data.get("errmsg", "")}), 400
    openid = wx_data["openid"]
    user = User.query.filter_by(wechat_openid=openid).first()
    if not user:
        return jsonify({"wechat_openid": openid, "need_bind": True, "message": "未绑定账号，请绑定"}), 200
    user.token = generate_token()
    user.token_expiry = datetime.utcnow() + timedelta(days=30)
    db.session.commit()
    return jsonify(user_login_dict(user))

@app.route("/api/login/bind-wechat", methods=["POST"])
def bind_wechat():
    data = request.json
    openid = data.get("wechat_openid", "")
    phone = str(data.get("phone", "")).strip()
    code = str(data.get("code", "")).strip()
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return jsonify({"error": "手机号未注册，请联系管理员"}), 404
    if user.wechat_openid:
        return jsonify({"error": "该账号已绑定微信"}), 400
    if User.query.filter_by(wechat_openid=openid).first():
        return jsonify({"error": "该微信已被其他账号绑定"}), 400
    stored = verification_codes.get(phone)
    if not stored or time.time() > stored["expiry"]:
        return jsonify({"error": "验证码已过期，请重新获取"}), 400
    if stored["code"] != code:
        return jsonify({"error": "验证码错误"}), 400
    verification_codes.pop(phone, None)
    user.wechat_openid = openid
    user.token = generate_token()
    user.token_expiry = datetime.utcnow() + timedelta(days=30)
    db.session.commit()
    bind_result = user_login_dict(user)
    bind_result["message"] = "微信绑定成功"
    return jsonify(bind_result)

# ======================== 自动登录 ========================

@app.route("/api/auto-login", methods=["POST"])
def auto_login():
    data = request.json
    token = data.get("token", "")
    if not token:
        return jsonify({"error": "无效的令牌"}), 401
    user = User.query.filter_by(token=token).first()
    if not user:
        return jsonify({"error": "令牌无效"}), 401
    if user.token_expiry and datetime.utcnow() > user.token_expiry:
        user.token = None
        user.token_expiry = None
        db.session.commit()
        return jsonify({"error": "登录已过期，请重新登录"}), 401
    return jsonify(user_login_dict(user))

# ======================== 基础信息：货品种类 ========================

@app.route("/api/cargo-types", methods=["GET"])
def list_cargo_types():
    types = CargoType.query.order_by(CargoType.id).all()
    return jsonify([{"id": t.id, "name": t.name, "default_unit": t.default_unit} for t in types])


@app.route("/api/cargo-types", methods=["POST"])
def create_cargo_type():
    data = request.json
    if CargoType.query.filter_by(name=data["name"]).first():
        return jsonify({"error": "货品种类已存在"}), 400
    ct = CargoType(name=data["name"], default_unit=data.get("default_unit", ""))
    db.session.add(ct)
    db.session.commit()
    return jsonify({"id": ct.id, "message": "货品种类已添加"})


@app.route("/api/cargo-types/<int:cid>", methods=["PUT"])
def update_cargo_type(cid):
    ct = CargoType.query.get_or_404(cid)
    data = request.json
    if "name" in data:
        ct.name = data["name"]
    if "default_unit" in data:
        ct.default_unit = data["default_unit"]
    db.session.commit()
    return jsonify({"message": "已更新"})


@app.route("/api/cargo-types/<int:cid>", methods=["DELETE"])
def delete_cargo_type(cid):
    ct = CargoType.query.get_or_404(cid)
    db.session.delete(ct)
    db.session.commit()
    return jsonify({"message": "已删除"})


# ======================== 基础信息：单位管理 ========================

@app.route("/api/unit-types", methods=["GET"])
def list_unit_types():
    units = UnitType.query.order_by(UnitType.id).all()
    return jsonify([{"id": u.id, "name": u.name} for u in units])


@app.route("/api/unit-types", methods=["POST"])
def create_unit_type():
    data = request.json
    if UnitType.query.filter_by(name=data["name"]).first():
        return jsonify({"error": "单位已存在"}), 400
    ut = UnitType(name=data["name"])
    db.session.add(ut)
    db.session.commit()
    return jsonify({"id": ut.id, "message": "单位已添加"})


@app.route("/api/unit-types/<int:uid>", methods=["PUT"])
def update_unit_type(uid):
    ut = UnitType.query.get_or_404(uid)
    data = request.json
    if "name" in data:
        ut.name = data["name"]
    db.session.commit()
    return jsonify({"message": "已更新"})


@app.route("/api/unit-types/<int:uid>", methods=["DELETE"])
def delete_unit_type(uid):
    ut = UnitType.query.get_or_404(uid)
    db.session.delete(ut)
    db.session.commit()
    return jsonify({"message": "已删除"})


# ======================== 管理员：人员管理 ========================

@app.route("/api/employees", methods=["GET"])
def list_employees():
    users = User.query.filter_by(role="employee").all()
    return jsonify([{"id": u.id, "display_name": u.display_name, "username": u.username, "phone": u.phone or "", "wechat_binded": bool(u.wechat_openid)} for u in users])


@app.route("/api/employees", methods=["POST"])
def create_employee():
    data = request.json
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "用户名已存在"}), 400
    user = User(
        username=data["username"],
        password_hash=generate_password_hash(data.get("password", "123456")),
        role="employee",
        display_name=data["display_name"],
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"id": user.id, "message": "人员已添加", "phone": user.phone})


@app.route("/api/employees/<int:eid>", methods=["PUT"])
def update_employee(eid):
    user = User.query.get_or_404(eid)
    if user.role != "employee":
        return jsonify({"error": "不能修改管理员"}), 400
    data = request.json
    if "display_name" in data:
        user.display_name = data["display_name"]
    if "password" in data:
        user.password_hash = generate_password_hash(data["password"])
    db.session.commit()
    return jsonify({"message": "已更新"})


@app.route("/api/employees/<int:eid>", methods=["DELETE"])
def delete_employee(eid):
    user = User.query.get_or_404(eid)
    if user.role != "employee":
        return jsonify({"error": "不能删除管理员"}), 400
    ItemAssignment.query.filter_by(user_id=eid).delete()
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "已删除"})


# ======================== 管 理 员：批 次 ========================

@app.route("/api/batches", methods=["GET"])
def list_batches():
    batches = Batch.query.order_by(Batch.created_at.desc()).all()
    return jsonify([{
        "id": b.id, "name": b.name, "arrival_time": b.arrival_time,
        "created_at": b.created_at, "batch_remark": b.batch_remark or "",
        "item_count": BatchItem.query.filter_by(batch_id=b.id).count(),
    } for b in batches])


@app.route("/api/batches", methods=["POST"])
def create_batch():
    data = request.json
    batch = Batch(name=data["name"], arrival_time=data["arrival_time"], batch_remark=data.get("batch_remark", ""))
    db.session.add(batch)
    db.session.flush()
    for it in data.get("items", []):
        db.session.add(BatchItem(batch_id=batch.id, name=it["name"], unit=it["unit"], spec=it.get("spec", ""), remark=it.get("remark", "")))
    db.session.commit()
    return jsonify({"id": batch.id, "message": "批次创建成功"})


@app.route("/api/batches/<int:bid>", methods=["DELETE"])
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
def update_batch(bid):
    batch = Batch.query.get_or_404(bid)
    data = request.json
    if "name" in data:
        batch.name = data["name"]
    if "arrival_time" in data:
        batch.arrival_time = data["arrival_time"]
    if "batch_remark" in data:
        batch.batch_remark = data["batch_remark"]
    db.session.commit()
    return jsonify({"message": "批次已更新", "id": batch.id})


@app.route("/api/batches/<int:bid>/items", methods=["GET"])
def list_items(bid):
    items = BatchItem.query.filter_by(batch_id=bid).all()
    # Auto-sync: ensure all cargo types have corresponding BatchItems
    cargo_types = CargoType.query.all()
    existing_names = {i.name for i in items}
    for ct in cargo_types:
        if ct.name not in existing_names:
            item = BatchItem(batch_id=bid, name=ct.name, unit=ct.default_unit or "")
            db.session.add(item)
            db.session.flush()
            items.append(item)
            existing_names.add(ct.name)
    if cargo_types:
        db.session.commit()
        # Re-fetch to get complete data including empty assignments
        items = BatchItem.query.filter_by(batch_id=bid).all()
    return jsonify([item_dict(i) for i in items])


@app.route("/api/batches/<int:bid>/items", methods=["POST"])
def add_item(bid):
    data = request.json
    item = BatchItem(batch_id=bid, name=data["name"], unit=data["unit"],
                       spec=data.get("spec", ""), remark=data.get("remark", ""))
    db.session.add(item)
    db.session.commit()
    return jsonify(item_dict(item))


@app.route("/api/items/<int:iid>", methods=["DELETE"])
def delete_item(iid):
    item = BatchItem.query.get_or_404(iid)
    ItemAssignment.query.filter_by(batch_item_id=iid).delete()
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "货品已删除"})


@app.route("/api/items/<int:iid>/assignments", methods=["PUT"])
def save_assignments(iid):
    """全量替换货品下的员工分配"""
    data = request.json  # [{user_id, allocated_quantity}, ...]
    ItemAssignment.query.filter_by(batch_item_id=iid).delete()
    for a in data:
        db.session.add(ItemAssignment(
            batch_item_id=iid,
            user_id=a["user_id"],
            allocated_quantity=a.get("allocated_quantity", 0),
        ))
    db.session.commit()
    update_item_status(iid)
    return jsonify({"message": "分配已保存"})


@app.route("/api/items/<int:iid>/assignments", methods=["GET"])
def get_assignments(iid):
    return jsonify([assignment_dict(a) for a in ItemAssignment.query.filter_by(batch_item_id=iid).all()])


# ======================== 管 理 员：报 表 ========================

@app.route("/api/batches/<int:bid>/report", methods=["GET"])
def batch_report(bid):
    batch = Batch.query.get_or_404(bid)
    items = BatchItem.query.filter_by(batch_id=bid).all()
    details = []
    for item in items:
        assignments = ItemAssignment.query.filter_by(batch_item_id=item.id).all()
        total = sum(a.actual_quantity for a in assignments if a.actual_quantity is not None)
        details.append({
            "item_name": item.name, "item_unit": item.unit, "item_status": item.status,
            "item_spec": item.spec, "item_remark": item.remark,
            "assignments": [assignment_dict(a) for a in assignments],
            "total_actual": total,
        })
    return jsonify({
        "batch_name": batch.name, "arrival_time": batch.arrival_time,
        "created_at": batch.created_at, "details": details,
    })


@app.route("/api/summary", methods=["GET"])
def global_summary():
    """全品类汇总：跨所有批次，按货品名称分组求和"""
    from sqlalchemy import func
    rows = db.session.query(
        BatchItem.name, BatchItem.unit,
        func.sum(ItemAssignment.actual_quantity).label("total_actual")
    ).join(ItemAssignment, ItemAssignment.batch_item_id == BatchItem.id)\
     .filter(ItemAssignment.actual_quantity.isnot(None))\
     .group_by(BatchItem.name, BatchItem.unit).all()
    return jsonify([{"name": r[0], "unit": r[1], "total_actual": r[2] or 0} for r in rows])


# ======================== 员 工 ========================

@app.route("/api/employee/tasks", methods=["GET"])
def employee_tasks():
    uid = request.args.get("user_id", type=int)
    if not uid:
        return jsonify({"error": "缺少user_id"}), 400
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
            "allocated_quantity": a.allocated_quantity,
            "actual_quantity": a.actual_quantity,
            "item_status": item.status, "batch_item_id": item.id,
        })
    return jsonify(result)


@app.route("/api/employee/submit", methods=["POST"])
def employee_submit():
    data = request.json
    if "assignment_id" in data and data["assignment_id"]:
        a = ItemAssignment.query.get(data["assignment_id"])
        if a:
            a.actual_quantity = data["actual_quantity"]
            db.session.commit()
            update_item_status(a.batch_item_id)
            item = BatchItem.query.get(a.batch_item_id)
            return jsonify({"message": "报数成功", "item_status": item.status if item else None})
    # Fallback: find or create assignment by batch_item_id + user_id
    bid = data.get("batch_item_id")
    uid = data.get("user_id")
    if bid and uid:
        a = ItemAssignment.query.filter_by(batch_item_id=bid, user_id=uid).first()
        if not a:
            a = ItemAssignment(batch_item_id=bid, user_id=uid, allocated_quantity=0)
            db.session.add(a)
            db.session.flush()
        a.actual_quantity = data["actual_quantity"]
        db.session.commit()
        update_item_status(bid)
        item = BatchItem.query.get(bid)
        return jsonify({"message": "报数成功", "assignment_id": a.id, "item_status": item.status if item else None})
    return jsonify({"error": "缺少参数"}), 400


@app.route("/api/employee/my-batches", methods=["GET"])
def employee_my_batches():
    uid = request.args.get("user_id", type=int)
    if not uid:
        return jsonify({"error": "缺少user_id"}), 400
    from sqlalchemy import func
    batch_ids = db.session.query(BatchItem.batch_id).join(ItemAssignment).filter(
        ItemAssignment.user_id == uid, ItemAssignment.allocated_quantity > 0
    ).distinct().all()
    batch_ids = [b[0] for b in batch_ids]
    batches = Batch.query.filter(Batch.id.in_(batch_ids)).order_by(Batch.created_at.desc()).all()
    return jsonify([{
        "id": b.id, "name": b.name, "arrival_time": b.arrival_time,
        "item_count": BatchItem.query.filter_by(batch_id=b.id).count(),
        "created_at": b.created_at,
    } for b in batches])


@app.route("/api/employee/my-items", methods=["GET"])
def employee_my_items():
    uid = request.args.get("user_id", type=int)
    bid = request.args.get("batch_id", type=int)
    if not uid or not bid:
        return jsonify({"error": "缺少参数"}), 400
    items = BatchItem.query.filter_by(batch_id=bid).all()
    result = []
    for item in items:
        my_assign = ItemAssignment.query.filter_by(batch_item_id=item.id, user_id=uid).first()
        result.append({
            "item_id": item.id, "item_name": item.name,
            "item_unit": item.unit, "item_spec": item.spec,
            "item_remark": item.remark, "item_status": item.status,
            "allocated_quantity": my_assign.allocated_quantity if my_assign else 0,
            "actual_quantity": my_assign.actual_quantity if my_assign else None,
            "assignment_id": my_assign.id if my_assign else None,
        })
    return jsonify(result)



# ======================== 统 计 ========================

@app.route("/api/stats", methods=["GET"])
def get_stats():
    all_items = BatchItem.query.all()
    total_batches = Batch.query.count()
    total_items = len(all_items)
    pending = sum(1 for i in all_items if i.status == "未报货")
    done = sum(1 for i in all_items if i.status == "已完成")
    return jsonify({"totalBatches": total_batches, "totalItems": total_items, "pendingItems": pending, "doneItems": done})

# ======================== 初 始 化 ========================

def migrate_schema():
    import sqlite3
    db_path = os.path.join(basedir, 'data.db')
    if not os.path.exists(db_path):
        return
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('PRAGMA table_info(users)')
        cols = [row[1] for row in cursor.fetchall()]
        if 'phone' not in cols:
            cursor.execute('ALTER TABLE users ADD COLUMN phone VARCHAR(20)')
            print('迁移：添加 phone 列')
        if 'wechat_openid' not in cols:
            cursor.execute('ALTER TABLE users ADD COLUMN wechat_openid VARCHAR(100)')
            print('迁移：添加 wechat_openid 列')
        if 'token' not in cols:
            cursor.execute('ALTER TABLE users ADD COLUMN token VARCHAR(64)')
            print('迁移：添加 token 列')
        if 'token_expiry' not in cols:
            cursor.execute('ALTER TABLE users ADD COLUMN token_expiry TIMESTAMP')
            print('迁移：添加 token_expiry 列')
        conn.commit()
        conn.close()
    except Exception as e:
        print('迁移警告:', e)

def init_db():
    migrate_schema()
    db.create_all()
    # 默认货品种类
    if not CargoType.query.first():
        for name in ["蔬菜", "水果", "肉类", "水产", "粮油", "干货", "调味品", "饮品"]:
            db.session.add(CargoType(name=name, default_unit="斤"))
    # 默认单位
    if not UnitType.query.first():
        for name in ["斤", "公斤", "箱", "件", "袋", "瓶", "桶", "包", "盒", "个"]:
            db.session.add(UnitType(name=name))
    # 默认用户
    if not User.query.filter_by(username="admin").first():
        db.session.add(User(username="admin", password_hash=generate_password_hash("admin123"),
                            role="admin", display_name="管理员", phone="13800000000"))
    if not User.query.filter_by(username="employee1").first():
        db.session.add(User(username="employee1", password_hash=generate_password_hash("123456"),
                            role="employee", display_name="张三", phone="13800000001"))
    if not User.query.filter_by(username="employee2").first():
        db.session.add(User(username="employee2", password_hash=generate_password_hash("123456"),
                            role="employee", display_name="李四", phone="13800000002"))
    db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True, port=5000)
