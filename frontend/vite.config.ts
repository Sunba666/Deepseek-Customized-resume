import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 开发模式：前端 5173，代理 /api 到后端 8000（后端本地运行）
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
  },
})
