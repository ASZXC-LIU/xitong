<template>
  <div class='login-wrap'>
    <div class='login-card'>
      <h2>分单系统</h2>
      <input v-model='username' placeholder='用户名' @keyup.enter='login' />
      <input v-model='password' type='password' placeholder='密码' @keyup.enter='login' />
      <button class='btn btn-primary' style='width:100%' @click='login' :disabled='loading'>{{ loading ? '登录中...' : '登 录' }}</button>
      <p v-if='error' style='color:#f56c6c;margin-top:12px'>{{ error }}</p>
      <p style='margin-top:16px;font-size:12px;color:#999'>
        管理员: admin / admin123<br/>员工: employee1 / 123456
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
const router = useRouter();
const username = ref('');
const password = ref('');
const loading = ref(false);
const error = ref('');

async function login() {
  if (!username.value || !password.value) { error.value = '请输入用户名和密码'; return; }
  loading.value = true; error.value = '';
  try {
    const res = await fetch('http://localhost:5000/api/login', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value, password: password.value }),
    });
    const data = await res.json();
    if (!res.ok) { error.value = data.error; return; }
    localStorage.setItem('user', JSON.stringify(data));
    router.push(data.role === 'admin' ? '/admin' : '/employee');
  } catch { error.value = '无法连接服务器，请确认后端已启动'; }
  finally { loading.value = false; }
}
</script>

<style scoped>
.login-wrap { display: flex; justify-content: center; align-items: center; min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.login-card { background: #fff; border-radius: 16px; padding: 40px; width: 380px; max-width: 90vw; box-shadow: 0 20px 60px rgba(0,0,0,0.15); }
.login-card h2 { text-align: center; margin-bottom: 28px; font-size: 22px; color: #303133; }
.login-card input { margin-bottom: 14px; }
</style>
