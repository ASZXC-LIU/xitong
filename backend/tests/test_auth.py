import os
import unittest
from datetime import timedelta

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


if __name__ == "__main__":
    unittest.main()
