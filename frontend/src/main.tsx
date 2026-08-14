import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { loadTheme, applyTheme } from './hooks/useTheme'
import './index.css'

// 渲染前应用已保存的主题，避免首帧闪烁
applyTheme(loadTheme())

// React Router v6 + future 标志：消除 v7 升级警告
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
