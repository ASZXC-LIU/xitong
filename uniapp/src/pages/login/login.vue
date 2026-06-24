<template>
  <view class="login-wrap">
    <view class="login-card">
      <text class="login-title">分单系统</text>

      <!-- 登录方式切换 -->
      <view class="tab-bar">
        <text :class="'tab-item ' + (tab==='account' ? 'active' : '')" @click="switchTab('account')">账号登录</text>
        <text :class="'tab-item ' + (tab==='phone' ? 'active' : '')" @click="switchTab('phone')">短信登录</text>
      </view>

      <!-- 账号登录 -->
      <view v-if="tab==='account'">
        <input class="uni-input" v-model="username" placeholder="用户名" @confirm="doLogin" />
        <input class="uni-input" v-model="password" type="password" placeholder="密码" @confirm="doLogin" />
        <button class="btn btn-primary" style="width:100%;margin-top:8px" @click="doLogin" :disabled="loading">
          {{ loading ? "登录中..." : "登 录" }}
        </button>
      </view>

      <!-- 短信验证码登录 -->
      <view v-if="tab==='phone'">
        <view class="phone-row">
          <input class="uni-input phone-input" v-model="phone" type="number" maxlength="11" placeholder="手机号" @confirm="sendCode" />
          <button class="btn btn-code" @click="sendCode" :disabled="codeSending || codeCountdown > 0">
            {{ codeCountdown > 0 ? codeCountdown + "s" : codeSending ? "发送中..." : "获取验证码" }}
          </button>
        </view>
        <input class="uni-input" v-model="verifyCode" type="number" maxlength="6" placeholder="输入验证码" @confirm="doLogin" />
        <button class="btn btn-primary" style="width:100%;margin-top:8px" @click="doLogin" :disabled="loading">
          {{ loading ? "登录中..." : "登 录" }}
        </button>
      </view>

      <!-- 微信快捷登录（仅小程序） -->
      <!-- #ifdef MP-WEIXIN -->
      <view class="wx-section">
        <view class="wx-divider"><text class="wx-divider-text">或</text></view>
        <button class="btn btn-wx" @click="wechatLogin" :disabled="wxLoading">
          {{ wxLoading ? "微信登录中..." : "微信快捷登录" }}
        </button>
      </view>
      <!-- #endif -->

      <!-- 微信绑定弹窗 -->
      <view v-if="showBindForm" class="modal-mask" @click="showBindForm=false">
        <view class="modal-card" @click.stop>
          <text class="modal-title">绑定账号</text>
          <text class="bind-hint">首次使用微信，请验证手机号绑定已有账号</text>
          <view class="phone-row">
            <input class="uni-input phone-input" v-model="bindPhone" type="number" maxlength="11" placeholder="手机号" @confirm="sendBindCode" />
            <button class="btn btn-code" @click="sendBindCode" :disabled="bindCodeSending || bindCodeCountdown > 0">
              {{ bindCodeCountdown > 0 ? bindCodeCountdown + "s" : bindCodeSending ? "发送中..." : "获取验证码" }}
            </button>
          </view>
          <input class="uni-input" v-model="bindCode" type="number" maxlength="6" placeholder="输入验证码" @confirm="doBind" />
          <view class="modal-actions">
            <button class="btn" @click="showBindForm=false">取消</button>
            <button class="btn btn-primary" @click="doBind" :disabled="bindLoading">
              {{ bindLoading ? "绑定中..." : "绑定并登录" }}
            </button>
          </view>
        </view>
      </view>

      <text v-if="error" class="error-text">{{ error }}</text>
      <text class="hint-text">管理员: admin / admin123 或 手机验证码</text>
    </view>
  </view>
</template>

<script>
import { apiPost } from "../../utils/request"
import { setStorage } from "../../utils/storage"

export default {
  data() {
    return {
      tab: "account",
      username: "", password: "",
      phone: "", verifyCode: "",
      loading: false, codeSending: false, codeCountdown: 0, codeTimer: null,
      wxLoading: false, error: "",
      // 微信绑定
      showBindForm: false,
      bindOpenid: "",
      bindPhone: "", bindCode: "", bindLoading: false,
      bindCodeSending: false, bindCodeCountdown: 0, bindCodeTimer: null,
    }
  },
  methods: {
    switchTab(tab) {
      this.tab = tab
      this.error = ""
    },
    // 发送验证码
    async sendCode() {
      if (!this.phone || this.phone.length < 11) { this.error = "请输入正确的手机号"; return }
      this.error = ""
      this.codeSending = true
      try {
        await apiPost("/send-code", { phone: this.phone })
        this.startCountdown()
      } catch (e) { this.error = e.message || "发送失败" }
      finally { this.codeSending = false }
    },
    async sendBindCode() {
      if (!this.bindPhone || this.bindPhone.length < 11) { this.error = "请输入正确的手机号"; return }
      this.error = ""
      this.bindCodeSending = true
      try {
        await apiPost("/send-code", { phone: this.bindPhone })
        this.bindCodeCountdown = 60
        if (this.bindCodeTimer) clearInterval(this.bindCodeTimer)
        this.bindCodeTimer = setInterval(() => {
          this.bindCodeCountdown--
          if (this.bindCodeCountdown <= 0) clearInterval(this.bindCodeTimer)
        }, 1000)
      } catch (e) { this.error = e.message || "发送失败" }
      finally { this.bindCodeSending = false }
    },
    startCountdown() {
      this.codeCountdown = 60
      if (this.codeTimer) clearInterval(this.codeTimer)
      this.codeTimer = setInterval(() => {
        this.codeCountdown--
        if (this.codeCountdown <= 0) clearInterval(this.codeTimer)
      }, 1000)
    },
    // 登录
    async doLogin() {
      this.error = ""
      if (this.tab === "phone") {
        if (!this.phone) { this.error = "请输入手机号"; return }
        if (!this.verifyCode) { this.error = "请输入验证码"; return }
        this.loading = true
        try {
          const data = await apiPost("/login/verify-code", { phone: this.phone, code: this.verifyCode })
          this.onLoginSuccess(data)
        } catch (e) { this.error = e.message || "登录失败" }
        finally { this.loading = false }
      } else {
        if (!this.username) { this.error = "请输入用户名"; return }
        if (!this.password) { this.error = "请输入密码"; return }
        this.loading = true
        try {
          const data = await apiPost("/login", { username: this.username, password: this.password })
          this.onLoginSuccess(data)
        } catch (e) { this.error = e.message || "登录失败" }
        finally { this.loading = false }
      }
    },
    async wechatLogin() {
      // #ifdef MP-WEIXIN
      this.wxLoading = true; this.error = ""
      try {
        const loginRes = await uni.login()
        const data = await apiPost("/login/wechat", { code: loginRes.code })
        if (data.need_bind) {
          this.bindOpenid = data.wechat_openid
          this.showBindForm = true
          this.wxLoading = false
          return
        }
        this.onLoginSuccess(data)
      } catch (e) { this.error = e.message || "微信登录失败" }
      finally { this.wxLoading = false }
      // #endif
    },
    async doBind() {
      if (!this.bindPhone || !this.bindCode) { this.error = "请输入手机号和验证码"; return }
      this.bindLoading = true; this.error = ""
      try {
        const data = await apiPost("/login/bind-wechat", {
          wechat_openid: this.bindOpenid,
          phone: this.bindPhone,
          code: this.bindCode,
        })
        this.showBindForm = false
        this.onLoginSuccess(data)
      } catch (e) { this.error = e.message || "绑定失败" }
      finally { this.bindLoading = false }
    },
    onLoginSuccess(data) {
      setStorage("token", data.token)
      setStorage("user", data)
      if (data.role === "admin") {
        uni.navigateTo({ url: "/pages/admin/app", redirect: true })
      } else {
        uni.navigateTo({ url: "/pages/employee/employee", redirect: true })
      }
    }
  }
}
</script>

<style>
.login-wrap {
  display: flex; justify-content: center; align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  background: rgba(255,255,255,0.95); border-radius: 16px; padding: 32px 28px;
  width: 380px; max-width: 90vw;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15);
}
.login-title {
  display: block; text-align: center; margin-bottom: 20px;
  font-size: 22px; color: #303133; font-weight: bold;
}
.tab-bar {
  display: flex; margin-bottom: 16px; border-bottom: 1px solid #eee;
}
.tab-item {
  flex: 1; text-align: center; padding: 8px 0; font-size: 14px;
  color: #909399; position: relative; cursor: pointer;
}
.tab-item.active {
  color: #409eff; font-weight: 600;
}
.tab-item.active::after {
  content: ""; position: absolute; bottom: -1px; left: 20%; right: 20%;
  height: 2px; background: #409eff; border-radius: 1px;
}
.login-card .uni-input {
  display: block; width: 100%; height: 40px; line-height: 40px;
  padding: 0 12px; border: 1px solid #dcdfe6; border-radius: 4px;
  font-size: 14px; margin-bottom: 14px;
  box-sizing: border-box;
}
.phone-row { display: flex; gap: 8px; align-items: center; margin-bottom: 14px; }
.phone-input { flex: 1; margin-bottom: 0 !important; }
.btn-code {
  white-space: nowrap; padding: 0 12px; height: 40px; line-height: 40px;
  border: 1px solid #409eff; border-radius: 4px; background: #ecf5ff;
  color: #409eff; font-size: 13px; cursor: pointer;
}
.btn-code[disabled] { border-color: #dcdfe6; background: #f5f5f5; color: #bbb; }
.error-text {
  display: block; color: #f56c6c; margin-top: 12px; text-align: center;
}
.hint-text {
  display: block; margin-top: 16px; font-size: 12px;
  color: #999; text-align: center;
}
.btn { display: inline-block; padding: 8px 14px; border: 1px solid #dcdfe6; border-radius: 4px; background: #fff; font-size: 14px; text-align: center; }
.btn-primary {
  background: #409eff; border-color: #409eff; color: #fff;
  border-radius: 4px; padding: 8px; font-size: 14px; text-align: center;
}

/* 微信登录 */
.wx-section { margin-top: 16px; }
.wx-divider { display: flex; align-items: center; margin-bottom: 12px; }
.wx-divider::before, .wx-divider::after { content: ""; flex: 1; height: 1px; background: #e0e0e0; }
.wx-divider-text { padding: 0 12px; font-size: 12px; color: #ccc; }
.btn-wx {
  width: 100%; background: #07c160; border-color: #07c160; color: #fff;
  border-radius: 4px; padding: 10px; font-size: 14px; cursor: pointer;
}

/* 绑定弹窗 */
.modal-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal-card { background: #fff; border-radius: 10px; padding: 24px; width: 380px; max-width: 90vw; }
.modal-title { font-size: 18px; font-weight: 600; margin-bottom: 8px; display: block; }
.bind-hint { font-size: 13px; color: #909399; margin-bottom: 16px; display: block; }
.modal-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
</style>
