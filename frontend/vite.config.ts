import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'

// 开发模式：前端 5173，代理 /api 到后端 8000（后端本地运行）
export default defineConfig({
  plugins: [react(), cspBuildPlugin()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
    // 权限策略响应头：本应用不需要摄像头/麦克风/定位等权限，显式关闭
    // （消除控制台 Permissions-Policy 相关提示，同时收紧浏览器能力）
    headers: {
      'Permissions-Policy':
        'camera=(), microphone=(), geolocation=(), payment=(), usb=(), battery=()',
    },
  },
  preview: {
    headers: {
      'Permissions-Policy':
        'camera=(), microphone=(), geolocation=(), payment=(), usb=(), battery=()',
    },
  },
  build: {
    outDir: 'dist',
  },
})

/**
 * 生产构建专用：往 index.html 注入 CSP 元标签，拦截第三方注入的
 * 内联脚本（如 aegisInject / yuke / SideBar 等广告/劫持脚本）。
 *
 * - 只在 build 时注入（apply: 'build'）：开发模式依赖 Vite 的 react-refresh
 *   内联预热脚本，加 CSP 会破坏 HMR，故开发环境不启用。
 * - 注意：浏览器扩展的 content script 运行在隔离世界，不受页面 CSP 约束；
 *   对付扩展级注入仍需在浏览器侧禁用可疑扩展（见 README FAQ）。
 */
function cspBuildPlugin(): Plugin {
  return {
    name: 'inject-csp-meta',
    apply: 'build',
    transformIndexHtml(html) {
      const csp = [
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data:",
        "font-src 'self' data:",
        "connect-src 'self' http://127.0.0.1:8000",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
      ].join('; ')
      const meta = `<meta http-equiv="Content-Security-Policy" content="${csp}" />`
      return html.replace('<meta name="viewport"', `${meta}\n    <meta name="viewport"`)
    },
  }
}
