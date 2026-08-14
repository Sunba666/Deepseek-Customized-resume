import { Link, NavLink, Outlet } from 'react-router-dom'

export default function App() {
  return (
    <div className="min-h-screen">
      {/* 顶部导航 */}
      <header className="no-print border-b border-stone-200 bg-white/80 backdrop-blur sticky top-0 z-10">
        <div className="mx-auto max-w-3xl px-4 py-3 flex items-center justify-between">
          <Link to="/" className="font-semibold text-lg tracking-tight">
            resume-advisor
            <span className="ml-2 text-xs font-normal text-muted">定制化求职方案</span>
          </Link>
          <nav className="flex gap-4 text-sm text-muted">
            <NavLink
              to="/"
              className={({ isActive }) => (isActive ? 'text-ink font-medium' : 'hover:text-ink')}
            >
              首页
            </NavLink>
            <NavLink
              to="/settings"
              className={({ isActive }) => (isActive ? 'text-ink font-medium' : 'hover:text-ink')}
            >
              设置
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-8">
        <Outlet />
      </main>

      <footer className="no-print mx-auto max-w-3xl px-4 pb-8 text-xs text-muted">
        本地运行 · 简历与报告不上传任何服务器 · 数据默认脱敏
      </footer>
    </div>
  )
}
