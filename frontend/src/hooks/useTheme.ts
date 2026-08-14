import { useEffect, useState } from 'react'

export type Theme = 'light' | 'dark' | 'system'

const THEME_KEY = 'ra_theme'

export function loadTheme(): Theme {
  try {
    const raw = localStorage.getItem(THEME_KEY)
    if (raw === 'light' || raw === 'dark' || raw === 'system') return raw
  } catch {
    /* ignore */
  }
  return 'system'
}

function saveTheme(t: Theme) {
  try {
    localStorage.setItem(THEME_KEY, t)
  } catch {
    /* ignore */
  }
}

export function applyTheme(theme: Theme) {
  const mq = window.matchMedia('(prefers-color-scheme: dark)')
  const dark = theme === 'dark' || (theme === 'system' && mq.matches)
  document.documentElement.classList.toggle('dark', dark)
}

/**
 * 主题管理：默认跟随系统（prefers-color-scheme），手动切换后覆盖系统设置。
 * 切换时在根 <html> 上添加/移除 dark 类（tailwind darkMode: 'class'）。
 */
export function useTheme() {
  const [theme, setTheme] = useState<Theme>(loadTheme)

  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const apply = () => applyTheme(theme)
    apply()
    // 系统主题变化时响应（system 模式下实时跟随）
    mq.addEventListener('change', apply)
    return () => mq.removeEventListener('change', apply)
  }, [theme])

  const changeTheme = (t: Theme) => {
    setTheme(t)
    saveTheme(t)
    applyTheme(t)
  }

  return { theme, changeTheme }
}
