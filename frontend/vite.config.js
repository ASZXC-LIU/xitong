import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: { 
    port: 5173,
    // 新增代理配置，指向本地后端地址
    proxy: {
      '/api': {
        target: 'http://localhost:5000', // 请确保这里填写的是你后端真实运行的端口（比如 5000 或 8080）
        changeOrigin: true
      }
    }
  },
});