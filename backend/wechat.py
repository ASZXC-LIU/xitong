"""微信小程序手机号登录适配器。

把微信 HTTP 契约隔离在业务路由之外，测试可注入模拟交换器，生产环境只从
环境变量读取 AppID/Secret。任何上游响应都不记录凭证或密钥。
"""
from dataclasses import dataclass
import time

import requests


class WechatServiceError(Exception):
    """可安全展示给客户端的微信服务错误。"""

    def __init__(self, message, *, code="WECHAT_SERVICE_ERROR", status=502):
        super().__init__(message)
        self.code = code
        self.status = status


@dataclass(frozen=True)
class WechatCredentials:
    phone: str
    openid: str = ""


class WechatClient:
    STABLE_TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/stable_token"
    PHONE_URL = "https://api.weixin.qq.com/wxa/business/getuserphonenumber"
    SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"

    def __init__(self, app_id, app_secret, *, session=None, timeout=8):
        if not app_id or not app_secret:
            raise WechatServiceError(
                "微信登录尚未配置，请联系管理员",
                code="WECHAT_NOT_CONFIGURED",
                status=503,
            )
        self.app_id = app_id
        self.app_secret = app_secret
        self.session = session or requests.Session()
        self.timeout = timeout
        self._access_token = ""
        self._access_token_expires_at = 0

    @staticmethod
    def _json(response):
        try:
            payload = response.json()
        except ValueError as exc:
            raise WechatServiceError("微信服务返回了无法识别的数据") from exc
        if not isinstance(payload, dict):
            raise WechatServiceError("微信服务返回了无法识别的数据")
        return payload

    @staticmethod
    def _raise_upstream(payload, fallback):
        errcode = payload.get("errcode", 0)
        if errcode not in (0, "0", None):
            raise WechatServiceError(fallback)

    def _get_access_token(self):
        if self._access_token and time.time() < self._access_token_expires_at:
            return self._access_token
        try:
            response = self.session.post(
                self.STABLE_TOKEN_URL,
                json={
                    "grant_type": "client_credential",
                    "appid": self.app_id,
                    "secret": self.app_secret,
                    "force_refresh": False,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise WechatServiceError("暂时无法连接微信服务，请稍后重试") from exc
        payload = self._json(response)
        self._raise_upstream(payload, "微信登录配置不可用，请联系管理员")
        token = payload.get("access_token", "")
        if not token:
            raise WechatServiceError("微信登录配置不可用，请联系管理员")
        expires_in = max(int(payload.get("expires_in", 7200)) - 300, 60)
        self._access_token = token
        self._access_token_expires_at = time.time() + expires_in
        return token

    def _exchange_phone(self, phone_code):
        try:
            response = self.session.post(
                self.PHONE_URL,
                params={"access_token": self._get_access_token()},
                json={"code": phone_code},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise WechatServiceError("暂时无法获取手机号，请稍后重试") from exc
        payload = self._json(response)
        self._raise_upstream(payload, "手机号授权已失效，请重新授权")
        phone_info = payload.get("phone_info") or {}
        phone = str(
            phone_info.get("purePhoneNumber") or phone_info.get("phoneNumber") or ""
        ).strip()
        if not phone:
            raise WechatServiceError("未能获取手机号，请重新授权")
        return phone

    def _exchange_openid(self, login_code):
        if not login_code:
            return ""
        try:
            response = self.session.get(
                self.SESSION_URL,
                params={
                    "appid": self.app_id,
                    "secret": self.app_secret,
                    "js_code": login_code,
                    "grant_type": "authorization_code",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise WechatServiceError("暂时无法建立微信登录状态，请稍后重试") from exc
        payload = self._json(response)
        self._raise_upstream(payload, "微信登录凭证已失效，请重新登录")
        return str(payload.get("openid", "")).strip()

    def exchange_credentials(self, phone_code, login_code=""):
        return WechatCredentials(
            phone=self._exchange_phone(phone_code),
            openid=self._exchange_openid(login_code),
        )
