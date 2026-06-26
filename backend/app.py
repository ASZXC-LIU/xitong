# -*- coding: utf-8 -*-
"""
分单系统 - Flask 后端（最终整合版 - 纯账号密码）
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
    username = db.Column(db.String(80), unique=True, nullable=False)  # 账号（强制为手机号）
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin / employee
    display_name = db.Column(db.String(80), nullable=False)  # 显示姓名
    phone = db.Column(db.String(20), unique=True, nullable=True)  # 手机号（与username同步）
    wechat_openid = db.Column(db.String(100), unique=True, nullable=True)
    token = db.Column(db.String(64), unique=True, nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)


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
    name = db.Column(db.String(200), nullable=False)
    arrival_time = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.String(30), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    batch_code = db.Column(db.String(50), default="")
    batch_remark = db.Column(db.String(500), default="")


class BatchItem(db.Model):
    __tablename__ = "batch_items"
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("batches.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default="未分货")
    spec = db.Column(db.String(200), default="")
    remark = db.Column(db.String(500), default="")
    batch = db.relationship("Batch", backref="items")


class ItemAssignment(db.Model):
    __tablename__ = "item_assignments"
    id = db.Column(db.Integer, primary_key=True)
    batch_item_id = db.Column(db.Integer, db.ForeignKey("batch_items.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    allocated_quantity = db.Column(db.Float, default=0)
    actual_quantity = db.Column(db.Float, nullable=True)
    item = db.relationship("BatchItem", backref="assignments")
    user = db.relationship("User", backref="assignments")


# ======================== 工 具 函 数 ========================

def update_item_status(item_id):
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
    return {"id": item.id, "batch_id": item.batch_id, "name": item.name, "unit": item.unit, "status": item.status,
            "spec": item.spec, "remark": item.remark,
            "assignments": [assignment_dict(a) for a in ItemAssignment.query.filter_by(batch_item_id=item.id).all()]}


def assignment_dict(a):
    return {
        "id": a.id, "batch_item_id": a.batch_item_id,
        "user_id": a.user_id, "user_name": a.user.display_name,
        "allocated_quantity": a.allocated_quantity,
        "actual_quantity": a.actual_quantity,
    }


def generate_token():
    raw = str(uuid.uuid4()) + str(time.time())
    return hashlib.sha256(raw.encode()).hexdigest()


def user_login_dict(user):
    return {
        "id": user.id, "username": user.username,
        "role": user.role, "display_name": user.display_name,
        "phone": user.phone or "",
        "token": user.token,
    }


# ======================== 账 号 密 码 登 录 ========================

@app.route("/api/login", methods=["POST"])
def login():
    """手机号账号 + 密码 登录"""
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "请输入账号和密码"}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        user = User.query.filter_by(phone=username).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "账号或密码错误"}), 401

    user.token = generate_token()
    user.token_expiry = datetime.utcnow() + timedelta(days=30)
    db.session.commit()
    return jsonify(user_login_dict(user))


@app.route("/api/auto-login", methods=["POST"])
def auto_login():
    data = request.get_json(silent=True) or {}
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
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return jsonify({"error": "种类名称不能为空"}), 400
    if CargoType.query.filter_by(name=data["name"]).first():
        return jsonify({"error": "货品种类已存在"}), 400
    ct = CargoType(name=data["name"], default_unit=data.get("default_unit", ""))
    db.session.add(ct)
    db.session.commit()
    return jsonify({"id": ct.id, "message": "货品种类已添加"})


@app.route("/api/cargo-types/<int:cid>", methods=["PUT"])
def update_cargo_type(cid):
    ct = CargoType.query.get_or_404(cid)
    data = request.get_json(silent=True) or {}
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
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return jsonify({"error": "单位名称不能为空"}), 400
    if UnitType.query.filter_by(name=data["name"]).first():
        return jsonify({"error": "单位已存在"}), 400
    ut = UnitType(name=data["name"])
    db.session.add(ut)
    db.session.commit()
    return jsonify({"id": ut.id, "message": "单位已添加"})


@app.route("/api/unit-types/<int:uid>", methods=["PUT"])
def update_unit_type(uid):
    ut = UnitType.query.get_or_404(uid)
    data = request.get_json(silent=True) or {}
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


# ======================== 管理员：人员管理 (CRUD 手机号强制 & 包含管理员编辑) ========================

@app.route("/api/employees", methods=["GET"])
def list_employees():
    """查：获取所有用户列表（包含管理员）"""
    users = User.query.all()
    return jsonify(
        [{"id": u.id, "display_name": u.display_name, "username": u.username, "phone": u.phone or "", "role": u.role}
         for u in users])


@app.route("/api/employees", methods=["POST"])
def create_employee():
    """增：添加新员工（强制账号为11位手机号，密码默认为 123456）"""
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()  # 登录账号即手机号
    display_name = str(data.get("display_name", "")).strip()

    if not username or len(username) != 11 or not username.isdigit():
        return jsonify({"error": "账号必须是11位手机号"}), 400
    if not display_name:
        return jsonify({"error": "员工姓名不能为空"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "该手机号账号已存在"}), 400

    # 密码默认设为 123456
    password = data.get("password", "123456")
    if not password:
        password = "123456"

    user = User(
        username=username,
        phone=username,
        password_hash=generate_password_hash(password),
        role="employee",
        display_name=display_name,
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"id": user.id, "message": "人员已添加", "username": user.username})


@app.route("/api/employees/<int:eid>", methods=["PUT"])
def update_employee(eid):
    """改：修改员工或管理员信息"""
    user = User.query.get_or_404(eid)
    data = request.get_json(silent=True) or {}

    if "username" in data and data["username"]:
        username = str(data["username"]).strip()
        if len(username) != 11 or not username.isdigit():
            return jsonify({"error": "账号必须是11位手机号"}), 400
        existing = User.query.filter_by(username=username).first()
        if existing and existing.id != eid:
            return jsonify({"error": "该手机号已被其他账号占用"}), 400
        user.username = username
        user.phone = username

    if "display_name" in data and data["display_name"]:
        display_name = str(data["display_name"]).strip()
        if not display_name:
            return jsonify({"error": "姓名不能为空"}), 400
        user.display_name = display_name

    if "password" in data and data["password"]:
        user.password_hash = generate_password_hash(data["password"])

    db.session.commit()
    return jsonify({"message": "已更新"})


@app.route("/api/employees/<int:eid>", methods=["DELETE"])
def delete_employee(eid):
    """删：删除员工 (管理员绝对防删除保护)"""
    user = User.query.get_or_404(eid)
    if user.role == "admin":
        return jsonify({"error": "不能删除管理员账户"}), 400
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
    data = request.get_json(silent=True) or {}
    if not data.get("name") or not data.get("arrival_time"):
        return jsonify({"error": "批次名称和到货时间不能为空"}), 400
    batch = Batch(name=data["name"], arrival_time=data["arrival_time"], batch_remark=data.get("batch_remark", ""))
    db.session.add(batch)
    db.session.flush()
    for it in data.get("items", []):
        db.session.add(BatchItem(batch_id=batch.id, name=it["name"], unit=it["unit"], spec=it.get("spec", ""),
                                 remark=it.get("remark", "")))
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
    data = request.get_json(silent=True) or {}
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
        items = BatchItem.query.filter_by(batch_id=bid).all()
    return jsonify([item_dict(i) for i in items])


@app.route("/api/batches/<int:bid>/items", methods=["POST"])
def add_item(bid):
    data = request.get_json(silent=True) or {}
    if not data.get("name") or not data.get("unit"):
        return jsonify({"error": "货品名称与单位不能为空"}), 400
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
    data = request.get_json(silent=True) or []
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
    from sqlalchemy import func
    rows = db.session.query(
        BatchItem.name, BatchItem.unit,
        func.sum(ItemAssignment.actual_quantity).label("total_actual")
    ).join(ItemAssignment, ItemAssignment.batch_item_id == BatchItem.id) \
        .filter(ItemAssignment.actual_quantity.isnot(None)) \
        .group_by(BatchItem.name, BatchItem.unit).all()
    return jsonify([{"name": r[0], "unit": r[1], "total_actual": r[2] or 0} for r in rows])


# ======================== 员 工 功能 ========================

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
    data = request.get_json(silent=True) or {}
    if "assignment_id" in data and data["assignment_id"]:
        a = ItemAssignment.query.get(data["assignment_id"])
        if a:
            a.actual_quantity = data["actual_quantity"]
            db.session.commit()
            update_item_status(a.batch_item_id)
            item = BatchItem.query.get(a.batch_item_id)
            return jsonify({"message": "报数成功", "item_status": item.status if item else None})

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
    return jsonify(
        {"totalBatches": total_batches, "totalItems": total_items, "pendingItems": pending, "doneItems": done})


# ======================== 初始化数据库与兼容升级 ========================

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
        conn.commit()
        conn.close()
    except Exception as e:
        print('迁移警告:', e)


def init_db():
    migrate_schema()
    db.create_all()

    if not CargoType.query.first():
        for name in ["蔬菜", "水果", "肉类", "水产", "粮油", "干货", "调味品", "饮品"]:
            db.session.add(CargoType(name=name, default_unit="斤"))

    if not UnitType.query.first():
        for name in ["斤", "公斤", "箱", "件", "袋", "瓶", "桶", "包", "盒", "个"]:
            db.session.add(UnitType(name=name))

    # === 兼容旧数据库的账号升级逻辑 ===
    # 查找并更新管理员
    admin = User.query.filter_by(role="admin").first()
    if not admin:
        db.session.add(User(username="13800000000", password_hash=generate_password_hash("123456"),
                            role="admin", display_name="管理员", phone="13800000000"))
    else:
        admin.username = "13800000000"
        admin.phone = "13800000000"

    # 查找并更新张三 (兼容旧库里的 employee1)
    emp1 = User.query.filter((User.phone == "13800000001") | (User.username == "employee1")).first()
    if not emp1:
        db.session.add(User(username="13800000001", password_hash=generate_password_hash("123456"),
                            role="employee", display_name="张三", phone="13800000001"))
    else:
        emp1.username = "13800000001"
        emp1.phone = "13800000001"

    # 查找并更新李四 (兼容旧库里的 employee2)
    emp2 = User.query.filter((User.phone == "13800000002") | (User.username == "employee2")).first()
    if not emp2:
        db.session.add(User(username="13800000002", password_hash=generate_password_hash("123456"),
                            role="employee", display_name="李四", phone="13800000002"))
    else:
        emp2.username = "13800000002"
        emp2.phone = "13800000002"

    db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True, port=5000)