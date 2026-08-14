import { useEffect, useState } from 'react'
import { loadSettings, saveSettings } from '../api'
import type { AppSettings } from '../api'
import type { Theme } from '../hooks/useTheme'

interface Props {
  open: boolean
  theme: Theme
  onThemeChange: (t: Theme) => void
  onClose: () => void
}

const inputCls =
  'mt-1 w-full rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm text-ink focus:outline-none focus:border-stone-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:focus:border-gray-400'

export default function SettingsModal({ open, theme, onThemeChange, onClose }: Props) {
  const [settings, setSettings] = useState<AppSettings>(loadSettings)
  const [showKey, setShowKey] = useState(false)
  const [draft, setDraft] = useState<AppSettings>(settings)

  // 打开模态框时回显已保存的设置值
  useEffect(() => {
    if (open) {
      const s = loadSettings()
      setSettings(s)
      setDraft(s)
      setShowKey(false)
    }
  }, [open])

  if (!open) return null

  const set = <K extends keyof AppSettings>(key: K, value: AppSettings[K]) =>
    setDraft((prev) => ({ ...prev, [key]: value }))

  const handleSave = () => {
    saveSettings(draft)
    setSettings(draft)
    onClose()
  }

  const handleCancel = () => {
    setDraft(settings) // 丢弃修改
    onClose()
  }

  // 阻止点击遮罩层时关闭（仅通过 保存/取消/× 关闭）
  const stop = (e: React.MouseEvent) => e.stopPropagation()

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={onClose}
    >
      <div
        onClick={stop}
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl dark:bg-gray-800"
        role="dialog"
        aria-modal="true"
        aria-label="设置"
      >
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold">⚙️ 设置</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-muted hover:bg-stone-100 dark:text-gray-400 dark:hover:bg-gray-700"
            aria-label="关闭"
          >
            ✕
          </button>
        </div>

        <div className="space-y-5">
          {/* LLM API Key */}
          <label className="block text-sm">
            <span className="text-muted dark:text-gray-300">LLM API Key</span>
            <div className="relative mt-1">
              <input
                type={showKey ? 'text' : 'password'}
                value={draft.llm_api_key}
                onChange={(e) => set('llm_api_key', e.target.value)}
                className={`${inputCls} pr-16`}
                placeholder="例如 sk-...（OpenAI 或兼容服务）"
              />
              <button
                type="button"
                onClick={() => setShowKey((v) => !v)}
                className="absolute right-2 top-1/2 -translate-y-1/2 rounded px-2 py-1 text-xs text-muted hover:bg-stone-100 dark:text-gray-400 dark:hover:bg-gray-700"
                title={showKey ? '隐藏' : '显示'}
              >
                {showKey ? '🙈 隐藏' : '👁 显示'}
              </button>
            </div>
          </label>

          {/* Base URL */}
          <label className="block text-sm">
            <span className="text-muted dark:text-gray-300">Base URL</span>
            <input
              value={draft.llm_base_url}
              onChange={(e) => set('llm_base_url', e.target.value)}
              className={inputCls}
              placeholder="https://api.deepseek.com（Ollama: http://localhost:11434/v1）"
            />
          </label>

          {/* 数据源 API Key */}
          <label className="block text-sm">
            <span className="text-muted dark:text-gray-300">
              数据源 API Key <span className="text-xs">（可选）</span>
            </span>
            <input
              type="password"
              value={draft.qcc_api_key}
              onChange={(e) => set('qcc_api_key', e.target.value)}
              className={inputCls}
              placeholder="企查查/天眼查开放平台 Key，留空使用模拟数据"
            />
          </label>

          {/* 主题切换 */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted dark:text-gray-300">主题</span>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted dark:text-gray-400">
                {theme === 'dark' ? '深色' : theme === 'light' ? '浅色' : '跟随系统'}
              </span>
              <button
                type="button"
                role="switch"
                aria-checked={theme === 'dark'}
                onClick={() => onThemeChange(theme === 'dark' ? 'light' : 'dark')}
                className={`relative h-6 w-11 rounded-full transition-colors ${
                  theme === 'dark' ? 'bg-stone-900 dark:bg-gray-100' : 'bg-stone-300 dark:bg-gray-600'
                }`}
              >
                <span
                  className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all ${
                    theme === 'dark' ? 'left-[22px]' : 'left-0.5'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={handleCancel}
            className="rounded-lg border border-stone-300 px-4 py-2 text-sm hover:border-stone-500 dark:border-gray-600 dark:text-gray-300 dark:hover:border-gray-400"
          >
            取消
          </button>
          <button
            onClick={handleSave}
            className="rounded-lg bg-stone-900 px-4 py-2 text-sm text-white hover:bg-stone-700 dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-white"
          >
            保存
          </button>
        </div>
      </div>
    </div>
  )
}
