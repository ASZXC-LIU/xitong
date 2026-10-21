import os
import unittest
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-only-secret"
os.environ["CORS_ORIGINS"] = "http://localhost"

from werkzeug.security import generate_password_hash

from backend.app import (
    Batch,
    BatchItem,
    ItemAssignment,
    User,
    app,
    db,
    generate_token,
    utcnow,
)


class AuthSecurityTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.context = app.app_context()
        self.context.push()
        db.drop_all()
        db.create_all()
        self.admin = User(
            username="admin-test",
            phone=None,
            password_hash=generate_password_hash("test-password"),
            role="admin",
            display_name="测试管理员",
        )
        self.employee = User(
            username="13800000001",
            phone="13800000001",
            password_hash=generate_password_hash("unused-password"),
            role="employee",
            display_name="员工甲",
        )
        self.other_employee = User(
            username="13800000002",
            phone="13800000002",
            password_hash=generate_password_hash("unused-password"),
            role="employee",
            display_name="员工乙",
        )
        db.session.add_all([self.admin, self.employee, self.other_employee])
        db.session.commit()
        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def token_for(self, user):
        user.token = generate_token()
        user.token_expiry = utcnow() + timedelta(hours=1)
        db.session.commit()
        return user.token

    @staticmethod
    def header(token):
        return {"Authorization": f"Bearer {token}"}

    def test_admin_login_and_protected_api(self):
        login = self.client.post("/api/login", json={
            "username": "admin-test",
            "password": "test-password",
        })
        self.assertEqual(login.status_code, 200)
        token = login.get_json()["token"]
        response = self.client.get("/api/employees", headers=self.header(token))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_and_employee_cannot_use_admin_api(self):
        self.assertEqual(self.client.get("/api/batches").status_code, 401)
        employee_token = self.token_for(self.employee)
        response = self.client.get("/api/batches", headers=self.header(employee_token))
        self.assertEqual(response.status_code, 403)

    def test_employee_query_uses_authenticated_identity_not_user_id(self):
        employee_token = self.token_for(self.employee)
        response = self.client.get(
            f"/api/employee/tasks?user_id={self.other_employee.id}",
            headers=self.header(employee_token),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])

    def test_employee_cannot_submit_another_employees_assignment(self):
        batch = Batch(name="测试批次", arrival_time="2026-10-02")
        db.session.add(batch)
        db.session.flush()
        item = BatchItem(batch_id=batch.id, name="测试产品", unit="箱")
        db.session.add(item)
        db.session.flush()
        assignment = ItemAssignment(
            batch_item_id=item.id,
            user_id=self.other_employee.id,
            employee_name=self.other_employee.display_name,
            allocated_quantity=10,
        )
        db.session.add(assignment)
        db.session.commit()

        employee_token = self.token_for(self.employee)
        response = self.client.post(
            "/api/employee/submit",
            json={"assignment_id": assignment.id, "actual_quantity": 5},
            headers=self.header(employee_token),
        )
        self.assertEqual(response.status_code, 404)
        db.session.refresh(assignment)
        self.assertIsNone(assignment.actual_quantity)

    def test_report_zero_is_valid_and_second_submit_is_idempotent(self):
        batch = Batch(name="测试批次", arrival_time="2026-10-02")
        db.session.add(batch)
        db.session.flush()
        item = BatchItem(batch_id=batch.id, name="测试产品", unit="箱")
        db.session.add(item)
        db.session.flush()
        assignment = ItemAssignment(
            batch_item_id=item.id,
            user_id=self.employee.id,
            employee_name=self.employee.display_name,
            allocated_quantity=10,
        )
        db.session.add(assignment)
        db.session.commit()
        employee_token = self.token_for(self.employee)

        first = self.client.post(
            "/api/employee/submit",
            json={"assignment_id": assignment.id, "actual_quantity": 0},
            headers=self.header(employee_token),
        )
        self.assertEqual(first.status_code, 200)
        second = self.client.post(
            "/api/employee/submit",
            json={"assignment_id": assignment.id, "actual_quantity": 5},
            headers=self.header(employee_token),
        )
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.get_json()["actual_quantity"], 0)

    def test_batch_completion_close_reopen_and_closed_submit(self):
        batch = Batch(name="状态批次", arrival_time="2026-10-02")
        db.session.add(batch)
        db.session.flush()
        item = BatchItem(batch_id=batch.id, name="状态产品", unit="箱")
        db.session.add(item)
        db.session.flush()
        assignment = ItemAssignment(
            batch_item_id=item.id,
            user_id=self.employee.id,
            employee_name=self.employee.display_name,
            allocated_quantity=10,
        )
        db.session.add(assignment)
        db.session.commit()

        admin_token = self.token_for(self.admin)
        not_ready = self.client.post(
            f"/api/batches/{batch.id}/close", headers=self.header(admin_token)
        )
        self.assertEqual(not_ready.status_code, 400)

        employee_token = self.token_for(self.employee)
        submitted = self.client.post(
            "/api/employee/submit",
            json={"assignment_id": assignment.id, "actual_quantity": 4},
            headers=self.header(employee_token),
        )
        self.assertEqual(submitted.status_code, 200, submitted.get_json())
        db.session.refresh(batch)
        self.assertEqual(batch.status, "已完成")

        closed = self.client.post(
            f"/api/batches/{batch.id}/close", headers=self.header(admin_token)
        )
        self.assertEqual(closed.status_code, 200, closed.get_json())
        self.assertEqual(closed.get_json()["status"], "已关闭")

        blocked = self.client.post(
            "/api/employee/submit",
            json={"assignment_id": assignment.id, "actual_quantity": 4},
            headers=self.header(employee_token),
        )
        self.assertEqual(blocked.status_code, 400)

        reopened = self.client.post(
            f"/api/batches/{batch.id}/reopen", headers=self.header(admin_token)
        )
        self.assertEqual(reopened.status_code, 200, reopened.get_json())
        self.assertEqual(reopened.get_json()["status"], "已完成")

    def test_admin_unlock_preserves_report_and_allows_resubmit(self):
        batch = Batch(name="更正批次", arrival_time="2026-10-02", status="已完成")
        db.session.add(batch)
        db.session.flush()
        item = BatchItem(batch_id=batch.id, name="更正产品", unit="箱", status="已完成")
        db.session.add(item)
        db.session.flush()
        assignment = ItemAssignment(
            batch_item_id=item.id,
            user_id=self.employee.id,
            employee_name=self.employee.display_name,
            allocated_quantity=10,
            actual_quantity=0,
            report_status="已锁定",
        )
        db.session.add(assignment)
        db.session.commit()

        admin_token = self.token_for(self.admin)
        unlocked = self.client.post(
            f"/api/assignments/{assignment.id}/unlock", headers=self.header(admin_token)
        )
        self.assertEqual(unlocked.status_code, 200, unlocked.get_json())
        db.session.refresh(assignment)
        db.session.refresh(item)
        db.session.refresh(batch)
        self.assertEqual(assignment.report_status, "已解锁待重报")
        self.assertEqual(assignment.actual_quantity, 0)
        self.assertEqual(item.status, "待报货")
        self.assertEqual(batch.status, "进行中")

        employee_token = self.token_for(self.employee)
        resubmitted = self.client.post(
            "/api/employee/submit",
            json={"assignment_id": assignment.id, "actual_quantity": 6},
            headers=self.header(employee_token),
        )
        self.assertEqual(resubmitted.status_code, 200, resubmitted.get_json())
        db.session.refresh(assignment)
        db.session.refresh(batch)
        self.assertEqual(assignment.actual_quantity, 6)
        self.assertEqual(assignment.report_status, "已锁定")
        self.assertEqual(batch.status, "已完成")

        batch.status = "已关闭"
        db.session.commit()
        blocked = self.client.post(
            f"/api/assignments/{assignment.id}/unlock", headers=self.header(admin_token)
        )
        self.assertEqual(blocked.status_code, 400)

    def test_unlock_and_resubmit_updates_all_effective_report_totals(self):
        batch = Batch(name="汇总更正批次", arrival_time="2026-10-02")
        db.session.add(batch)
        db.session.flush()
        item = BatchItem(batch_id=batch.id, name="汇总产品", unit="箱")
        db.session.add(item)
        db.session.flush()
        assignment = ItemAssignment(
            batch_item_id=item.id,
            user_id=self.employee.id,
            employee_name=self.employee.display_name,
            allocated_quantity=10,
        )
        db.session.add(assignment)
        db.session.commit()

        employee_token = self.token_for(self.employee)
        admin_token = self.token_for(self.admin)
        submitted = self.client.post(
            "/api/employee/submit",
            json={"assignment_id": assignment.id, "actual_quantity": 8},
            headers=self.header(employee_token),
        )
        self.assertEqual(submitted.status_code, 200, submitted.get_json())
        first_report = self.client.get(f"/api/batches/{batch.id}/report", headers=self.header(admin_token))
        self.assertEqual(first_report.get_json()["totals"]["actual_quantity"], 8)

        unlocked = self.client.post(
            f"/api/assignments/{assignment.id}/unlock", headers=self.header(admin_token)
        )
        self.assertEqual(unlocked.status_code, 200, unlocked.get_json())
        unlocked_report = self.client.get(f"/api/batches/{batch.id}/report", headers=self.header(admin_token))
        self.assertEqual(unlocked_report.get_json()["details"][0]["assignments"][0]["actual_quantity"], 8)
        self.assertEqual(unlocked_report.get_json()["totals"]["actual_quantity"], 0)
        global_after_unlock = self.client.get("/api/summary", headers=self.header(admin_token))
        self.assertEqual(global_after_unlock.get_json(), [])

        resubmitted = self.client.post(
            "/api/employee/submit",
            json={"assignment_id": assignment.id, "actual_quantity": 6},
            headers=self.header(employee_token),
        )
        self.assertEqual(resubmitted.status_code, 200, resubmitted.get_json())
        final_report = self.client.get(f"/api/batches/{batch.id}/report", headers=self.header(admin_token))
        self.assertEqual(final_report.get_json()["totals"]["actual_quantity"], 6)
        global_after_resubmit = self.client.get("/api/summary", headers=self.header(admin_token))
        self.assertEqual(global_after_resubmit.get_json(), [{
            "name": "汇总产品", "unit": "箱", "total_actual": 6,
        }])

    def test_only_empty_batch_can_be_deleted(self):
        empty_batch = Batch(name="空批次", arrival_time="2026-10-02")
        db.session.add(empty_batch)
        db.session.flush()
        empty_item = BatchItem(batch_id=empty_batch.id, name="空产品", unit="箱")
        db.session.add(empty_item)
        db.session.flush()
        db.session.add(ItemAssignment(
            batch_item_id=empty_item.id,
            user_id=self.employee.id,
            employee_name=self.employee.display_name,
            allocated_quantity=None,
        ))

        active_batch = Batch(name="已有分货批次", arrival_time="2026-10-03")
        db.session.add(active_batch)
        db.session.flush()
        active_item = BatchItem(batch_id=active_batch.id, name="已分货产品", unit="箱")
        db.session.add(active_item)
        db.session.flush()
        db.session.add(ItemAssignment(
            batch_item_id=active_item.id,
            user_id=self.employee.id,
            employee_name=self.employee.display_name,
            allocated_quantity=1,
        ))
        db.session.commit()

        admin_token = self.token_for(self.admin)
        deleted = self.client.delete(
            f"/api/batches/{empty_batch.id}", headers=self.header(admin_token)
        )
        self.assertEqual(deleted.status_code, 200, deleted.get_json())
        self.assertIsNone(db.session.get(Batch, empty_batch.id))

        rejected = self.client.delete(
            f"/api/batches/{active_batch.id}", headers=self.header(admin_token)
        )
        self.assertEqual(rejected.status_code, 400)
        self.assertIn("不能删除", rejected.get_json()["error"])
        self.assertIsNotNone(db.session.get(Batch, active_batch.id))

    def test_employee_history_first_loads_15_days_then_15_day_pages(self):
        def create_batch(name, days_ago):
            batch = Batch(name=name, arrival_date=date.today() - timedelta(days=days_ago))
            db.session.add(batch)
            db.session.flush()
            item = BatchItem(batch_id=batch.id, name=name + "产品", unit="箱")
            db.session.add(item)
            db.session.flush()
            db.session.add(ItemAssignment(
                batch_item_id=item.id,
                user_id=self.employee.id,
                employee_name=self.employee.display_name,
                allocated_quantity=1,
            ))
            db.session.commit()
            return batch

        current = create_batch("当前任务", 0)
        recent = create_batch("近期待办", 10)
        older = create_batch("历史任务", 100)
        employee_token = self.token_for(self.employee)

        first = self.client.get(
            "/api/employee/my-batches?window_days=15", headers=self.header(employee_token)
        )
        self.assertEqual(first.status_code, 200, first.get_json())
        first_payload = first.get_json()
        self.assertEqual([row["id"] for row in first_payload["batches"]], [current.id, recent.id])
        self.assertIsNotNone(first_payload["next_cursor"])

        cursor = first_payload["next_cursor"]
        more = self.client.get(
            "/api/employee/my-batches?window_days=15"
            f"&before_date={cursor['before_date']}&before_id={cursor['before_id']}",
            headers=self.header(employee_token),
        )
        self.assertEqual(more.status_code, 200, more.get_json())
        more_payload = more.get_json()
        self.assertEqual([row["id"] for row in more_payload["batches"]], [older.id])
        self.assertIsNone(more_payload["next_cursor"])


if __name__ == "__main__":
    unittest.main()
