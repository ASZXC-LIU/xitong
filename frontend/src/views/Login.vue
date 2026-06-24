<template>
  <div class='login-wrap'>
    <div class='login-card'>
      <h2>分单系统</h2>
      <div class="tab-bar">
        <span :class="'tab-item ' + (tab==='account' ? 'active' : '')" @click="tab='account'">账号登录</span>
        <span :class="'tab-item ' + (tab==='phone' ? 'active' : '')" @click="tab='phone'">短信登录</span>
      </div>
      <div v-if="tab==='account'">
        <input v-model='username' placeholder='用户名' @keyup.enter='doLogin' />
        <input v-model='password' type='password' placeholder='密码' @keyup.enter='doLogin' />
      </div>
      <div v-if="tab==='phone'">
        <div class="phone-row">
          <input v-model='phone' type="number" maxlength="11" placeholder='手机号' class="phone-input" @keyup.enter='sendCode' />
          <button class="btn-code" @click="sendCode" :disabled="codeSending || codeCountdown > 0">
            {{ codeCountdown > 0 ? codeCountdown + "s" : codeSending ? "发送中..." : "获取验证码" }}
          </button>
        </div>
        <input v-model='verifyCode' type="number" maxlength="6" placeholder='输入验证码' @keyup.enter='doLogin' />
      </div>
      <button class='btn btn-primary' style='width:100%' @click='doLogin' :disabled='loading'>{{ loading ? '登录中...' : '登 录' }}</button>
      <p v-if='error' style='color:#f56c6c;margin-top:12px'>{{ error }}</p>
      <p style='margin-top:16px;font-size:12px;color:#999'>
        管理员: admin / admin123 或 手机验证码
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
const router = useRouter();
const API = 'http://localhost:5000/api';
const tab = ref('account');
const username = ref('');
const password = ref('');
const phone = ref('');
const verifyCode = ref('');
const loading = ref(false);
const codeSending = ref(false);
const codeCountdown = ref(0);
let codeTimer = null;
const error = ref('');

async function sendCode() {
  if (!phone.value || phone.value.length < 11) { error.value = '请输入正确的手机号'; return; }
  error.value = ''; codeSending.value = true;
  try {
    const res = await fetch(API + '/send-code', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone: phone.value }),
    });
    const data = await res.json();
    if (!res.ok) { error.value = data.error; return; }
    if (data.debug_code) console.log('验证码:', data.debug_code);
    codeCountdown.value = 60;
    if (codeTimer) clearInterval(codeTimer);
    codeTimer = setInterval(() => { codeCountdown.value--; if (codeCountdown.value <= 0) clearInterval(codeTimer); }, 1000);
  } catch { error.value = '发送失败' }
  finally { codeSending.value = false; }
}

async function doLogin() {
  error.value = '';
  let url, body;
  if (tab.value === 'phone') {
    if (!phone.value) { error.value = '请输入手机号'; return; }
    if (!verifyCode.value) { error.value = '请输入验证码'; return; }
    url = API + '/login/verify-code';
    body = { phone: phone.value, code: verifyCode.value };
  } else {
    if (!username.value) { error.value = '请输入用户名'; return; }
    if (!password.value) { error.value = '请输入密码'; return; }
    url = API + '/login';
    body = { username: username.value, password: password.value };
  }
  loading.value = true;
  try {
    const res = await fetch(url, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) { error.value = data.error; return; }
    localStorage.setItem('user', JSON.stringify(data));
    if (data.token) localStorage.setItem('token', data.token);
    router.push(data.role === 'admin' ? '/admin' : '/employee');
  } catch { error.value = '无法连接服务器，请确认后端已启动'; }
  finally { loading.value = false; }
}
</script>

<style scoped>
.login-wrap { display: flex; justify-content: center; align-items: center; min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.login-card { background: #fff; border-radius: 16px; padding: 40px; width: 380px; max-width: 90vw; box-shadow: 0 20px 60px rgba(0,0,0,0.15); }
.login-card h2 { text-align: center; margin-bottom: 20px; font-size: 22px; color: #303133; }
.login-card input { display:block; width:100%; height:40px; line-height:40px; padding:0 12px; border:1px solid #dcdfe6; border-radius:4px; font-size:14px; margin-bottom:14px; box-sizing:border-box; }
.tab-bar { display: flex; margin-bottom: 16px; border-bottom: 1px solid #eee; }
.tab-item { flex: 1; text-align: center; padding: 8px 0; font-size: 14px; color: #909399; position: relative; cursor: pointer; }
.tab-item.active { color: #409eff; font-weight: 600; }
.tab-item.active::after { content: ""; position: absolute; bottom: -1px; left: 20%; right: 20%; height: 2px; background: #409eff; border-radius: 1px; }
.phone-row { display: flex; gap: 8px; align-items: center; margin-bottom: 14px; }
.phone-input { flex: 1; margin-bottom: 0 !important; }
.btn-code { white-space: nowrap; padding: 0 12px; height: 40px; border: 1px solid #409eff; border-radius: 4px; background: #ecf5ff; color: #409eff; font-size: 13px; cursor: pointer; }
.btn-code:disabled { border-color: #dcdfe6; background: #f5f5f5; color: #bbb; }
.btn-primary { background: #409eff; border-color: #409eff; color: #fff; border-radius: 4px; padding: 8px; font-size: 14px; cursor: pointer; border: none; width: 100%; }
</style>
