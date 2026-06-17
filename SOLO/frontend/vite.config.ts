import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 3000,
    proxy: {
      '/api': {
        // 使用 127.0.0.1 避免 localhost 在部分 Windows 环境优先解析到 IPv6 ::1，导致代理连接异常/超时
        target: 'http://127.0.0.1:8010',
        changeOrigin: true,
        timeout: 300000,  // 代理超时 300 秒
        proxyTimeout: 300000
      }
    }
  },
  resolve: {
    alias: {
      '@': '/src'
    }
  }
})
