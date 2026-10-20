import os
import unittest
from datetime import timedelta
from decimal import Decimal

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-only-secret"
os.environ["CORS_ORIGINS"] = "http://localhost"

from backend.app import (
    AuditLog,
    Batch,
    BatchItem,
    ItemAssignment,
    User,
    app,
    db,
    generate_token,
    utcnow,
)


class FinalModelBaselineTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.context = app.app_context()
        self.context.push()
        db.drop_all()
        db.create_all()
        self.admin = User(
            username="admin-model",
            role="admin",
            display_name="管理员",
            password_hash="unused-in-these-tests",
        )
        self.employee = User(
            phone="13800000003",
            role="employee",
            display_name="员工丙",
        )
        db.session.add_all([self.admin, self.employee])
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

    def create_item(self, company_quantity=10):
        batch = Batch(name="模型批次", arrival_time="2026-10-02")
        db.session.add(batch)
        db.session.flush()
        item = BatchItem(
            batch_id=batch.id,
            name="产品简称（含规格）",
            unit="箱",
            company_quantity=company_quantity,
        )
        db.session.add(item)
        db.session.commit()
        return item

    def test_final_fields_and_audit_model_are_persisted(self):
        item = self.create_item(Decimal("12.5"))
        assignment = ItemAssignment(
            batch_item_id=item.id,
            user_id=self.employee.id,
            employee_name=self.employee.display_name,
            allocated_quantity=Decimal("3.5"),
        )
        log = AuditLog(
            actor_user_id=self.admin.id,
            action="baseline_test",
            target_type="batch_item",
            target_id=item.id,
        )
        db.session.add_all([assignment, log])
        db.session.commit()

        self.assertEqual(item.company_quantity, Decimal("12.5"))
        self.assertEqual(item.batch.status, "进行中")
        self.assertTrue(self.employee.is_active)
        self.assertEqual(assignment.report_status, "待提交")
        self.assertEqual(AuditLog.query.count(), 1)

    def test_allocation_must_not_exceed_company_quantity(self):
        item = self.create_item(10)
        token = self.token_for(self.admin)
        response = self.client.put(
            f"/api/items/{item.id}/assignments",
            json=[{"user_id": self.employee.id, "allocated_quantity": 10.1}],
            headers=self.header(token),
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["code"], "BAD_REQUEST")
        self.assertEqual(ItemAssignment.query.count(), 0)

    def test_quantity_rejects_more_than_one_decimal_place(self):
        item = self.create_item(10)
        token = self.token_for(self.admin)
        response = self.client.put(
            f"/api/items/{item.id}/assignments",
            json=[{"user_id": self.employee.id, "allocated_quantity": 1.25}],
            headers=self.header(token),
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("一位小数", response.get_json()["error"])

    def test_inactive_user_token_is_rejected(self):
        token = self.token_for(self.employee)
        self.employee.is_active = False
        db.session.commit()
        response = self.client.get(
            "/api/employee/tasks", headers=self.header(token)
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["code"], "UNAUTHORIZED")

    def test_api_404_uses_standard_error_shape(self):
        response = self.client.get("/api/not-a-real-route")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.get_json(),
            {"error": "请求的资源不存在", "code": "NOT_FOUND"},
        )


if __name__ == "__main__":
    unittest.main()
