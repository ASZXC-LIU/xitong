<template>
  <view class="login-wrap">
    <view class="login-card">
      <text class="login-title">分单系统</text>
      <input class="uni-input" v-model="username" placeholder="用户名" @confirm="login" />
      <input class="uni-input" v-model="password" type="password" placeholder="密码" @confirm="login" />
      <button class="btn btn-primary" style="width:100%;margin-top:8px" @click="login" :disabled="loading">
        {{ loading ? "登录中..." : "登 录" }}
      </button>
      <text v-if="error" class="error-text">{{ error }}</text>
      <text class="hint-text">
        管理员: admin / admin123
      </text>
    </view>
  </view>
</template>

<script>
import { apiPost } from "../../utils/request"
import { setStorage } from "../../utils/storage"

export default {
  data() {
    return { username: "", password: "", loading: false, error: "" }
  },
  methods: {
    async login() {
      if (!this.username || !this.password) { this.error = "请输入用户名和密码"; return }
      this.loading = true; this.error = ""
      try {
        const data = await apiPost("/login", {
          username: this.username, password: this.password
        })
        setStorage("user", data)
        if (data.role === "admin") {
          uni.navigateTo({ url: "/pages/admin/dashboard" })
        } else {
          uni.navigateTo({ url: "/pages/employee/employee" })
        }
      } catch (e) {
        this.error = e.message || "无法连接服务器，请确认后端已启动"
      } finally { this.loading = false }
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
  background: #fff; border-radius: 16px; padding: 40px;
  width: 380px; max-width: 90vw;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15);
}
.login-title {
  display: block; text-align: center; margin-bottom: 28px;
  font-size: 22px; color: #303133; font-weight: bold;
}
.login-card .uni-input {
  display: block; width: 100%; height: 40px; line-height: 40px;
  padding: 0 12px; border: 1px solid #dcdfe6; border-radius: 4px;
  font-size: 14px; margin-bottom: 14px;
  box-sizing: border-box;
}
.error-text {
  display: block; color: #f56c6c; margin-top: 12px; text-align: center;
}
.hint-text {
  display: block; margin-top: 16px; font-size: 12px;
  color: #999; text-align: center;
}
.btn-primary {
  background: #409eff; border-color: #409eff; color: #fff;
}
</style>