<template>
  <div class='login-wrap'>
    <div class='login-card'>
      <h2>分单系统</h2>
      <div class="login-form">
        <input v-model='username' type="number" placeholder='请输入手机号' @keyup.enter='doLogin' />
        <input v-model='password' type='password' placeholder='请输入密码' @keyup.enter='doLogin' />
      </div>
      
      <button class='btn btn-primary' style='width:100%; margin-top: 10px;' @click='doLogin' :disabled='loading'>
        {{ loading ? '登录中...' : '登 录' }}
      </button>
      
      <p v-if='error' style='color:#f56c6c; margin-top:12px; text-align:center;'>{{ error }}</p>
      <p style='margin-top:16px; font-size:12px; color:#999; text-align:center;'>
        默认管理员账号: 13800000000 / 123456
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
const router = useRouter();
const API = '/api';

const username = ref('');
const password = ref('');
const loading = ref(false);
const error = ref('');

async function doLogin() {
  error.value = '';
  if (!username.value) { error.value = '请输入手机号'; return; }
  if (!password.value) { error.value = '请输入密码'; return; }
  
  loading.value = true;
  try {
    const res = await fetch(API + '/login', {
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value, password: password.value }),
    });
    const data = await res.json();
    
    if (!res.ok) { 
      error.value = data.error; 
      return; 
    }
    
    localStorage.setItem('user', JSON.stringify(data));
    if (data.token) localStorage.setItem('token', data.token);
    router.push(data.role === 'admin' ? '/admin' : '/employee');
  } catch { 
    error.value = '无法连接服务器，请确认后端已启动'; 
  } finally { 
    loading.value = false; 
  }
}
</script>
<style scoped>
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
.login-card h2 { 
  text-align: center; margin-bottom: 24px; font-size: 22px; color: #303133; 
}
.login-card input { 
  display:block; width:100%; height:40px; line-height:40px; 
  padding:0 12px; border:1px solid #dcdfe6; border-radius:4px; 
  font-size:14px; margin-bottom:16px; box-sizing:border-box; 
}
.login-card input:focus {
  border-color: #409eff; outline: none;
}
.btn-primary { 
  background: #409eff; border-color: #409eff; color: #fff; 
  border-radius: 4px; padding: 10px; font-size: 15px; 
  cursor: pointer; border: none; width: 100%; transition: 0.2s;
}
.btn-primary:hover {
  background: #66b1ff;
}
.btn-primary:disabled {
  background: #a0cfff; cursor: not-allowed;
}
</style>