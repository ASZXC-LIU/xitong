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
    CargoType,
    ItemAssignment,
    UnitType,
    User,
    app,
    db,
    generate_token,
    utcnow,
)
from backend.wechat import WechatClient, WechatServiceError


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeWechatSession:
    def __init__(self):
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        if url.endswith("stable_token"):
            return FakeResponse({"access_token": "access-test", "expires_in": 7200})
        return FakeResponse({
            "errcode": 0,
            "phone_info": {"purePhoneNumber": "13800000011"},
        })

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        return FakeResponse({"openid": "openid-from-session"})


class StageOneTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        app.config.pop("WECHAT_CREDENTIAL_EXCHANGER", None)
        self.context = app.app_context()
        self.context.push()
        db.drop_all()
        db.create_all()
        self.admin = User(
            username="admin-m1",
            password_hash=generate_password_hash("admin-password"),
            role="admin",
            display_name="管理员",
        )
        self.employee = User(
            phone="13800000011",
            password_hash=None,
            role="employee",
            display_name="张三",
        )
        self.inactive_employee = User(
            phone="13800000012",
            password_hash=None,
            role="employee",
            display_name="李四",
            is_active=False,
        )
        db.session.add_all([self.admin, self.employee, self.inactive_employee])
        db.session.commit()
        self.client = app.test_client()

    def tearDown(self):
        app.config.pop("WECHAT_CREDENTIAL_EXCHANGER", None)
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

    def inject_wechat(self, phone, openid="openid-test"):
        app.config["WECHAT_CREDENTIAL_EXCHANGER"] = (
            lambda phone_code, login_code: {"phone": phone, "openid": openid}
        )

    def test_wechat_phone_login_matches_employee_and_binds_openid(self):
        self.inject_wechat(self.employee.phone)
        response = self.client.post(
            "/api/login/wechat-phone",
            json={"phone_code": "phone-once", "login_code": "login-once"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["id"], self.employee.id)
        self.assertEqual(payload["role"], "employee")
        self.assertTrue(payload["token"])
        db.session.refresh(self.employee)
        self.assertEqual(self.employee.wechat_openid, "openid-test")
        self.assertIsNone(self.employee.password_hash)

        auto_login = self.client.post(
            "/api/auto-login", headers=self.header(payload["token"])
        )
        self.assertEqual(auto_login.status_code, 200)
        self.assertEqual(auto_login.get_json()["id"], self.employee.id)

    def test_wechat_adapter_exchanges_official_codes_without_exposing_secret(self):
        session = FakeWechatSession()
        client = WechatClient("appid-test", "secret-test", session=session)
        credentials = client.exchange_credentials("phone-code", "login-code")
        self.assertEqual(credentials.phone, "13800000011")
        self.assertEqual(credentials.openid, "openid-from-session")
        self.assertEqual([call[0] for call in session.calls], ["POST", "POST", "GET"])
        phone_call = session.calls[1]
        self.assertEqual(phone_call[2]["json"], {"code": "phone-code"})
        self.assertNotIn("secret", str(phone_call[2]))

    def test_wechat_login_never_accepts_client_phone_as_identity(self):
        response = self.client.post(
            "/api/login/wechat-phone", json={"phone": self.employee.phone}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["code"], "PHONE_AUTH_REQUIRED")

    def test_unmatched_and_inactive_phone_are_rejected_clearly(self):
        self.inject_wechat("13800000999")
        unmatched = self.client.post(
            "/api/login/wechat-phone", json={"phone_code": "unknown"}
        )
        self.assertEqual(unmatched.status_code, 403)
        self.assertEqual(unmatched.get_json()["code"], "EMPLOYEE_NOT_FOUND")

        self.inject_wechat(self.inactive_employee.phone)
        inactive = self.client.post(
            "/api/login/wechat-phone", json={"phone_code": "inactive"}
        )
        self.assertEqual(inactive.status_code, 403)
        self.assertEqual(inactive.get_json()["code"], "ACCOUNT_INACTIVE")

    def test_wechat_adapter_failure_is_normalized(self):
        def fail(_phone_code, _login_code):
            raise WechatServiceError("手机号授权已失效，请重新授权")

        app.config["WECHAT_CREDENTIAL_EXCHANGER"] = fail
        response = self.client.post(
            "/api/login/wechat-phone", json={"phone_code": "expired"}
        )
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.get_json()["code"], "WECHAT_SERVICE_ERROR")

    def test_employee_can_be_deactivated_and_reactivated_without_losing_history(self):
        cargo = CargoType(name="君乐宝乐钙箱", default_unit="箱")
        unit = UnitType(name="箱")
        batch = Batch(name="历史批次", arrival_time="2026-10-02")
        db.session.add_all([cargo, unit, batch])
        db.session.flush()
        item = BatchItem(
            batch_id=batch.id,
            cargo_type_id=cargo.id,
            name=cargo.name,
            unit=unit.name,
            company_quantity=10,
        )
        db.session.add(item)
        db.session.flush()
        assignment = ItemAssignment(
            batch_item_id=item.id,
            user_id=self.employee.id,
            employee_name=self.employee.display_name,
            allocated_quantity=5,
        )
        db.session.add(assignment)
        db.session.commit()
        token = self.token_for(self.admin)

        stopped = self.client.delete(
            f"/api/employees/{self.employee.id}", headers=self.header(token)
        )
        self.assertEqual(stopped.status_code, 200)
        self.assertFalse(db.session.get(User, self.employee.id).is_active)
        self.assertEqual(ItemAssignment.query.count(), 1)
        self.assertEqual(assignment.employee_name, "张三")

        restored = self.client.put(
            f"/api/employees/{self.employee.id}",
            json={"is_active": True},
            headers=self.header(token),
        )
        self.assertEqual(restored.status_code, 200)
        self.assertTrue(db.session.get(User, self.employee.id).is_active)
        self.assertEqual(item.name, "君乐宝乐钙箱")
        self.assertEqual(item.unit, "箱")

    def test_product_and_unit_support_status_restore(self):
        cargo = CargoType(name="测试产品", default_unit="包")
        unit = UnitType(name="包")
        db.session.add_all([cargo, unit])
        db.session.commit()
        token = self.token_for(self.admin)

        for path, model, object_id in (
            ("cargo-types", CargoType, cargo.id),
            ("unit-types", UnitType, unit.id),
        ):
            stopped = self.client.delete(
                f"/api/{path}/{object_id}", headers=self.header(token)
            )
            self.assertEqual(stopped.status_code, 200)
            self.assertFalse(db.session.get(model, object_id).is_active)
            restored = self.client.put(
                f"/api/{path}/{object_id}",
                json={"is_active": True},
                headers=self.header(token),
            )
            self.assertEqual(restored.status_code, 200)
            self.assertTrue(db.session.get(model, object_id).is_active)


if __name__ == "__main__":
    unittest.main()
