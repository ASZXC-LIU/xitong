import io
import os
import unittest
from datetime import timedelta
from decimal import Decimal

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-only-secret"
os.environ["CORS_ORIGINS"] = "http://localhost"

from openpyxl import Workbook
from werkzeug.security import generate_password_hash

from backend.app import (
    Batch,
    BatchItem,
    CargoType,
    ItemAssignment,
    User,
    app,
    db,
    generate_token,
    utcnow,
)


class BatchCreationAndImportTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.context = app.app_context()
        self.context.push()
        db.drop_all()
        db.create_all()
        self.admin = User(
            username="batch-admin",
            password_hash=generate_password_hash("password"),
            role="admin",
            display_name="管理员",
        )
        self.employee_a = User(phone="13800000101", role="employee", display_name="员工甲")
        self.employee_b = User(phone="13800000102", role="employee", display_name="员工乙")
        self.cargo_a = CargoType(name="手动产品甲", default_unit="箱")
        self.cargo_b = CargoType(name="手动产品乙", default_unit="件")
        db.session.add_all([self.admin, self.employee_a, self.employee_b, self.cargo_a, self.cargo_b])
        db.session.commit()
        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def headers(self):
        self.admin.token = generate_token()
        self.admin.token_expiry = utcnow() + timedelta(hours=1)
        db.session.commit()
        return {"Authorization": f"Bearer {self.admin.token}"}

    @staticmethod
    def workbook_bytes(reference="参考批次", rows=(), title="原始导入表", headers=("产品简称", "曲周")):
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = title
        worksheet["A1"] = reference
        worksheet["A2"], worksheet["B2"] = headers
        for index, row in enumerate(rows, start=3):
            for column, value in enumerate(row, start=1):
                worksheet.cell(index, column).value = value
        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        return output

    def create_manual_batch(self, company_quantity=100):
        response = self.client.post(
            "/api/batches",
            json={
                "name": "手动批次",
                "arrival_time": "2026-10-20",
                "items": [{"cargo_type_id": self.cargo_a.id, "company_quantity": company_quantity}],
            },
            headers=self.headers(),
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        return BatchItem.query.filter_by(batch_id=response.get_json()["id"]).one()

    def test_manual_batch_only_creates_selected_products_and_empty_employee_matrix(self):
        item = self.create_manual_batch()
        self.assertEqual(BatchItem.query.count(), 1)
        self.assertEqual(item.name, "手动产品甲")
        self.assertEqual(item.company_quantity, Decimal("100"))
        self.assertEqual(ItemAssignment.query.filter_by(batch_item_id=item.id).count(), 2)

        listed = self.client.get(f"/api/batches/{item.batch_id}/items", headers=self.headers())
        self.assertEqual(listed.status_code, 200)
        self.assertEqual([row["name"] for row in listed.get_json()], ["手动产品甲"])

    def test_company_100_with_allocations_30_and_40_saves_with_remaining_30(self):
        item = self.create_manual_batch(100)
        response = self.client.put(
            f"/api/items/{item.id}/assignments",
            json={"company_quantity": 100, "assignments": [
                {"user_id": self.employee_a.id, "allocated_quantity": 30},
                {"user_id": self.employee_b.id, "allocated_quantity": 40},
            ]},
            headers=self.headers(),
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        total = sum((row.allocated_quantity for row in ItemAssignment.query.filter_by(batch_item_id=item.id)), Decimal("0"))
        self.assertEqual(Decimal(item.company_quantity) - total, Decimal("30"))

    def test_company_100_with_total_110_is_rejected_without_overwriting_saved_values(self):
        item = self.create_manual_batch(100)
        first = self.client.put(
            f"/api/items/{item.id}/assignments",
            json=[{"user_id": self.employee_a.id, "allocated_quantity": 30}],
            headers=self.headers(),
        )
        self.assertEqual(first.status_code, 200)
        rejected = self.client.put(
            f"/api/items/{item.id}/assignments",
            json=[
                {"user_id": self.employee_a.id, "allocated_quantity": 50},
                {"user_id": self.employee_b.id, "allocated_quantity": 60},
            ],
            headers=self.headers(),
        )
        self.assertEqual(rejected.status_code, 400)
        self.assertIn("不能大于", rejected.get_json()["error"])
        self.assertEqual(
            ItemAssignment.query.filter_by(batch_item_id=item.id, user_id=self.employee_a.id).one().allocated_quantity,
            Decimal("30"),
        )

    def test_zero_company_quantity_allows_empty_assignments_but_rejects_positive_assignment(self):
        item = self.create_manual_batch(0)
        empty = self.client.put(
            f"/api/items/{item.id}/assignments", json={"company_quantity": 0, "assignments": []}, headers=self.headers()
        )
        self.assertEqual(empty.status_code, 200)
        rejected = self.client.put(
            f"/api/items/{item.id}/assignments",
            json=[{"user_id": self.employee_a.id, "allocated_quantity": 0.1}],
            headers=self.headers(),
        )
        self.assertEqual(rejected.status_code, 400)

    def test_admin_assignment_save_does_not_modify_employee_actual_quantity(self):
        item = self.create_manual_batch(100)
        row = ItemAssignment.query.filter_by(batch_item_id=item.id, user_id=self.employee_a.id).one()
        row.allocated_quantity = Decimal("10")
        row.actual_quantity = Decimal("4")
        row.report_status = "已锁定"
        db.session.commit()
        response = self.client.put(
            f"/api/items/{item.id}/assignments",
            json=[{"user_id": self.employee_a.id, "allocated_quantity": 10}],
            headers=self.headers(),
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(row.actual_quantity, Decimal("4"))

    def test_batch_report_returns_product_employee_and_batch_totals(self):
        item = self.create_manual_batch(100)
        rows = ItemAssignment.query.filter_by(batch_item_id=item.id).order_by(ItemAssignment.user_id).all()
        rows[0].allocated_quantity = Decimal("30")
        rows[0].actual_quantity = Decimal("0")
        rows[0].report_status = "已锁定"
        rows[1].allocated_quantity = Decimal("40")
        rows[1].actual_quantity = Decimal("25")
        rows[1].report_status = "已锁定"
        db.session.commit()

        response = self.client.get(f"/api/batches/{item.batch_id}/report", headers=self.headers())
        self.assertEqual(response.status_code, 200, response.get_json())
        payload = response.get_json()
        self.assertEqual(payload["details"][0]["company_quantity"], 100)
        self.assertEqual(payload["details"][0]["total_allocated"], 70)
        self.assertEqual(payload["details"][0]["total_actual"], 25)
        self.assertEqual(payload["details"][0]["remaining_quantity"], 30)
        self.assertEqual(payload["employee_totals"], [
            {"user_id": self.employee_a.id, "user_name": "员工甲",
             "allocated_quantity": 30, "actual_quantity": 0},
            {"user_id": self.employee_b.id, "user_name": "员工乙",
             "allocated_quantity": 40, "actual_quantity": 25},
        ])
        self.assertEqual(payload["totals"], {
            "company_quantity": 100,
            "allocated_quantity": 70,
            "actual_quantity": 25,
            "remaining_quantity": 30,
        })

    def test_batch_report_excludes_unlocked_preserved_actual_from_totals(self):
        item = self.create_manual_batch(20)
        row = ItemAssignment.query.filter_by(batch_item_id=item.id, user_id=self.employee_a.id).one()
        row.allocated_quantity = Decimal("10")
        row.actual_quantity = Decimal("8")
        row.report_status = "已解锁待重报"
        db.session.commit()

        response = self.client.get(f"/api/batches/{item.batch_id}/report", headers=self.headers())
        payload = response.get_json()
        self.assertEqual(payload["details"][0]["assignments"][0]["actual_quantity"], 8)
        self.assertEqual(payload["details"][0]["total_actual"], 0)
        self.assertEqual(payload["employee_totals"][0]["actual_quantity"], 0)
        self.assertEqual(payload["totals"]["actual_quantity"], 0)

    def test_import_uses_quzhou_quantity_and_ignores_employee_columns(self):
        response = self.client.post(
            "/api/batches/import",
            data={
                "name": "正式导入批次",
                "arrival_time": "2026-10-20",
                "file": (self.workbook_bytes(rows=[("导入产品甲", 88.5, 999)]), "source.xlsx"),
            },
            headers=self.headers(),
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        item = BatchItem.query.one()
        self.assertEqual(item.name, "导入产品甲")
        self.assertEqual(item.company_quantity, Decimal("88.5"))
        self.assertIsNone(item.cargo_type_id)
        self.assertTrue(all(row.allocated_quantity is None for row in item.assignments))

    def test_import_returns_all_errors_and_creates_no_partial_batch(self):
        workbook = self.workbook_bytes(
            reference="",
            headers=("错误产品列", "错误数量列"),
            rows=[("", -1), ("重复产品", "abc"), ("重复产品", 1.23)],
        )
        response = self.client.post(
            "/api/batches/import",
            data={
                "name": "不应创建", "arrival_time": "2026-10-20", "file": (workbook, "bad.xlsx")
            },
            headers=self.headers(),
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertGreaterEqual(len(payload["errors"]), 6)
        self.assertEqual(Batch.query.count(), 0)
        self.assertEqual(BatchItem.query.count(), 0)

    def test_large_import_validation_returns_all_rows_without_writing(self):
        rows = [(f"大文件产品{index}", index / 10) for index in range(1, 1001)]
        response = self.client.post(
            "/api/batches/import/validate",
            data={"file": (self.workbook_bytes(rows=rows), "large.xlsx")},
            headers=self.headers(),
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(len(response.get_json()["items"]), 1000)
        self.assertEqual(Batch.query.count(), 0)
        self.assertEqual(BatchItem.query.count(), 0)


if __name__ == "__main__":
    unittest.main()
