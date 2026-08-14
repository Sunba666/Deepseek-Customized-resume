import { useState } from 'react'
import Home from './pages/Home'
import SettingsModal from './components/SettingsModal'
import { useTheme } from './hooks/useTheme'

export default function App() {
  const [settingsOpen, setSettingsOpen] = useState(false)
  const { theme, changeTheme } = useTheme()

  return (
    <div className="min-h-screen">
      {/* 顶栏：仅标题 + 齿轮按钮（右上角） */}
      <header className="no-print border-b border-stone-200 bg-white/80 backdrop-blur sticky top-0 z-10 dark:border-gray-700 dark:bg-gray-800/80">
        <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
          <h1 className="font-semibold text-lg tracking-tight">
            resume-advisor
            <span className="ml-2 text-xs font-normal text-muted dark:text-gray-400">
              极简简历分析
            </span>
          </h1>
          <button
            onClick={() => setSettingsOpen(true)}
            className="rounded-lg p-2 text-lg text-muted hover:bg-stone-100 dark:text-gray-400 dark:hover:bg-gray-700"
            title="设置"
            aria-label="打开设置"
          >
            ⚙️
          </button>
        </div>
      </header>

      {/* 单页主体：左右两栏 */}
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Home />
      </main>

      <footer className="no-print mx-auto max-w-6xl px-4 pb-8 text-xs text-muted dark:text-gray-400">
        本地运行 · 简历与报告不上传任何服务器 · 数据默认脱敏
      </footer>

      {settingsOpen && (
        <SettingsModal
          open={settingsOpen}
          theme={theme}
          onThemeChange={changeTheme}
          onClose={() => setSettingsOpen(false)}
        />
      )}
    </div>
  )
}
