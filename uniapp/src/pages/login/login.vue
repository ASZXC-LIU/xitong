<template>
  <view class="login-page">
    <view class="login-card">
      <view class="brand-mark">分</view>
      <text class="login-title">员工报货</text>
      <text class="login-description">使用管理员登记的手机号快捷登录</text>

      <view v-if="checking" class="status-panel" aria-live="polite">
        <view class="loading-dot"></view>
        <text>正在检查登录状态…</text>
      </view>

      <template v-else>
        <!-- #ifdef MP-WEIXIN -->
        <!-- DEV_LOGIN_START -->
        <template v-if="developmentLoginEnabled">
          <view class="development-panel">
            <text class="development-title">本地调试模式</text>
            <text class="development-description">已跳过微信手机号授权，将使用本地测试员工进入系统。</text>
            <button class="phone-login-button" :disabled="loading" @click="startDevelopmentLogin">
              {{ loading ? "正在进入…" : "进入员工测试页面" }}
            </button>
          </view>
        </template>
        <!-- DEV_LOGIN_END -->
        <template v-if="!developmentLoginEnabled">
          <button
            class="phone-login-button"
            open-type="getPhoneNumber"
            :disabled="loading"
            @getphonenumber="onPhoneNumber"
          >
            {{ loading ? "登录中…" : "手机号快捷登录" }}
          </button>
          <button
            id="privacy-authorize-button"
            class="privacy-authorize-button"
            open-type="agreePrivacyAuthorization"
            @agreeprivacyauthorization="onAgreePrivacyAuthorization"
          >
            同意隐私指引
          </button>
          <text class="privacy-hint">仅用于匹配管理员已登记的员工信息，不会创建新账号</text>
        </template>
        <!-- #endif -->

        <!-- #ifndef MP-WEIXIN -->
        <view class="environment-hint">请在微信小程序中使用手机号快捷登录</view>
        <!-- #endif -->
      </template>

      <view v-if="error" class="error-panel" role="alert">
        <text class="error-title">暂时无法登录</text>
        <text class="error-message">{{ error }}</text>
        <text class="error-help">如手机号尚未登记或账号已停用，请联系管理员。</text>
      </view>
    </view>
  </view>
</template>

<script>
import { apiPost } from "../../utils/request"
import { getStorage, removeStorage, setStorage } from "../../utils/storage"

/* DEV_LOGIN_START */
// 开发服务器才会保留此入口；生产构建前由 vite.config.js 移除整个标记块。
const developmentLoginEnabled = import.meta.env.DEV
  && import.meta.env.VITE_ENABLE_DEV_LOGIN === "true"
/* DEV_LOGIN_END */

export default {
  data() {
    return {
      checking: true,
      loading: false,
      error: "",
      /* DEV_LOGIN_START */
      developmentLoginEnabled,
      /* DEV_LOGIN_END */
    }
  },
  onLoad() {
    this.tryAutoLogin()
  },
  methods: {
    async tryAutoLogin() {
      /* DEV_LOGIN_START */
      if (this.developmentLoginEnabled) {
        await this.startDevelopmentLogin()
        return
      }
      /* DEV_LOGIN_END */
      if (!getStorage("token")) {
        this.checking = false
        return
      }
      try {
        const data = await apiPost("/auto-login", {})
        if (data.role !== "employee") throw new Error("请使用员工微信账号登录")
        this.enterEmployee(data)
      } catch (_error) {
        removeStorage("token")
        removeStorage("user")
        this.checking = false
      }
    },
    /* DEV_LOGIN_START */
    async startDevelopmentLogin() {
      if (!this.developmentLoginEnabled || this.loading) return
      this.loading = true
      this.error = ""
      try {
        const data = await apiPost("/dev/login/employee", {})
        if (data.role !== "employee" || !data.token) {
          throw new Error("本地调试登录没有返回员工会话")
        }
        this.enterEmployee(data)
      } catch (error) {
        this.error = error.message || "本地调试登录失败，请检查后端开发配置。"
      } finally {
        this.loading = false
        this.checking = false
      }
    },
    /* DEV_LOGIN_END */
    async onPhoneNumber(event) {
      const detail = event && event.detail ? event.detail : {}
      if (!detail.code || !String(detail.errMsg || "").includes("ok")) {
        const errMsg = String(detail.errMsg || "未返回授权凭证")
        console.warn("微信手机号授权失败", errMsg)
        if (/deny|cancel/i.test(errMsg)) {
          this.error = "您未同意手机号授权，请点击“同意隐私指引”后再重新登录。"
        } else if (/privacy|permission|scope/i.test(errMsg)) {
          this.error = "小程序尚未获得手机号接口权限，请管理员完成微信公众平台的隐私指引与认证配置。"
        } else {
          this.error = `微信未返回手机号授权凭证：${errMsg}`
        }
        return
      }

      this.loading = true
      this.error = ""
      try {
        const loginResult = await uni.login({ provider: "weixin" })
        const loginData = Array.isArray(loginResult) ? loginResult[1] : loginResult
        if (!loginData || !loginData.code) throw new Error("未能取得微信登录凭证，请重试")
        const data = await apiPost("/login/wechat-phone", {
          phone_code: detail.code,
          login_code: loginData.code,
        })
        if (data.role !== "employee") throw new Error("未找到员工信息，请联系管理员")
        this.enterEmployee(data)
      } catch (error) {
        this.error = error.message || "微信登录失败，请稍后重试"
      } finally {
        this.loading = false
      }
    },
    onAgreePrivacyAuthorization() {
      this.error = ""
    },
    enterEmployee(data) {
      setStorage("token", data.token)
      setStorage("user", data)
      uni.reLaunch({ url: "/pages/employee/employee" })
    },
  },
}
</script>

<style>
.login-page {
  min-height: 100vh;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: #f5f7fa;
}

.login-card {
  width: 100%;
  max-width: 420px;
  box-sizing: border-box;
  padding: 32px 24px;
  border: 1px solid #d0d5dd;
  border-radius: 12px;
  background: #ffffff;
}

.brand-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  margin: 0 auto 16px;
  border-radius: 12px;
  background: #07c160;
  color: #ffffff;
  font-size: 26px;
  font-weight: 700;
}

.login-title,
.login-description,
.privacy-hint,
.error-title,
.error-message,
.error-help {
  display: block;
}

.login-title {
  color: #1f2937;
  font-size: 24px;
  font-weight: 700;
  text-align: center;
}

.login-description {
  margin-top: 8px;
  color: #667085;
  font-size: 16px;
  line-height: 1.6;
  text-align: center;
}

.phone-login-button {
  width: 100%;
  min-height: 52px;
  margin-top: 28px;
  border: 0;
  border-radius: 8px;
  background: #07c160;
  color: #ffffff;
  font-size: 18px;
  font-weight: 600;
  line-height: 52px;
}

.phone-login-button::after {
  border: 0;
}

.phone-login-button[disabled] {
  background: #9bdcb7;
  color: #ffffff;
}

.privacy-authorize-button {
  width: auto;
  margin-top: 12px;
  padding: 0;
  border: 0;
  background: transparent;
  color: #475467;
  font-size: 14px;
  line-height: 1.5;
  text-decoration: underline;
}

.privacy-authorize-button::after {
  border: 0;
}

/* DEV_LOGIN_START */
.development-panel {
  margin-top: 28px;
  padding: 16px;
  border: 1px solid #b9d7c4;
  border-radius: 8px;
  background: #f2fbf5;
}

.development-title,
.development-description {
  display: block;
}

.development-title {
  color: #16803c;
  font-size: 16px;
  font-weight: 700;
}

.development-description {
  margin-top: 6px;
  color: #475467;
  font-size: 14px;
  line-height: 1.6;
}

.development-panel .phone-login-button {
  margin-top: 16px;
}
/* DEV_LOGIN_END */

.privacy-hint {
  margin-top: 12px;
  color: #667085;
  font-size: 14px;
  line-height: 1.6;
  text-align: center;
}

.status-panel,
.environment-hint {
  margin-top: 28px;
  padding: 16px;
  border-radius: 8px;
  background: #f2f4f7;
  color: #475467;
  font-size: 16px;
  line-height: 1.5;
  text-align: center;
}

.loading-dot {
  width: 10px;
  height: 10px;
  margin: 0 auto 10px;
  border-radius: 50%;
  background: #07c160;
}

.error-panel {
  margin-top: 20px;
  padding: 16px;
  border: 1px solid #fecdca;
  border-radius: 8px;
  background: #fff6f5;
}

.error-title {
  color: #c4320a;
  font-size: 16px;
  font-weight: 700;
}

.error-message {
  margin-top: 6px;
  color: #912018;
  font-size: 16px;
  line-height: 1.5;
}

.error-help {
  margin-top: 8px;
  color: #667085;
  font-size: 14px;
  line-height: 1.5;
}
</style>
