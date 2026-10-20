import os
import unittest
from datetime import timedelta
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-only-secret"
os.environ["CORS_ORIGINS"] = "http://localhost"

from backend.app import User, app, db, utcnow


class DevelopmentLoginTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.context = app.app_context()
        self.context.push()
        db.drop_all()
        db.create_all()
        self.employee = User(
            role="employee",
            display_name="本地调试员工",
            phone="13900000000",
            is_active=True,
        )
        db.session.add(self.employee)
        db.session.commit()
        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def test_development_login_issues_a_real_employee_session(self):
        with patch.dict(os.environ, {
            "APP_ENV": "development",
            "DEV_LOGIN_ENABLED": "true",
            "DEV_LOGIN_EMPLOYEE_PHONE": self.employee.phone,
        }, clear=False):
            response = self.client.post("/api/dev/login/employee")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["id"], self.employee.id)
        self.assertEqual(payload["role"], "employee")
        self.assertTrue(payload["token"])
        db.session.refresh(self.employee)
        self.assertGreater(self.employee.token_expiry, utcnow() + timedelta(days=29))

    def test_development_login_is_hidden_when_disabled_or_not_development(self):
        for app_env, enabled in (("development", "false"), ("production", "true")):
            with self.subTest(app_env=app_env, enabled=enabled):
                with patch.dict(os.environ, {
                    "APP_ENV": app_env,
                    "DEV_LOGIN_ENABLED": enabled,
                    "DEV_LOGIN_EMPLOYEE_PHONE": self.employee.phone,
                }, clear=False):
                    response = self.client.post("/api/dev/login/employee")
                self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
