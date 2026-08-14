import { useEffect, useState } from 'react'
import { loadSettings, saveSettings } from '../api'
import type { AppSettings, SearchProvider } from '../api'
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
  const [draft, setDraft] = useState<AppSettings>(loadSettings)
  const [showKey, setShowKey] = useState(false)
  const [showSearchKey, setShowSearchKey] = useState(false)

  // 打开模态框时回显已保存的设置值
  useEffect(() => {
    if (open) {
      setDraft(loadSettings())
      setShowKey(false)
      setShowSearchKey(false)
    }
  }, [open])

  if (!open) return null

  const set = <K extends keyof AppSettings>(key: K, value: AppSettings[K]) =>
    setDraft((prev) => ({ ...prev, [key]: value }))

  const handleSave = () => {
    saveSettings(draft)
    onClose()
  }

  const handleCancel = () => {
    setDraft(loadSettings()) // 丢弃修改
    onClose()
  }

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

          {/* LLM Base URL */}
          <label className="block text-sm">
            <span className="text-muted dark:text-gray-300">LLM Base URL</span>
            <input
              value={draft.llm_base_url}
              onChange={(e) => set('llm_base_url', e.target.value)}
              className={inputCls}
              placeholder="https://api.openai.com/v1（Ollama: http://localhost:11434/v1）"
            />
          </label>

          {/* LLM 模型名称 */}
          <label className="block text-sm">
            <span className="text-muted dark:text-gray-300">LLM 模型名称</span>
            <input
              value={draft.llm_model}
              onChange={(e) => set('llm_model', e.target.value)}
              className={inputCls}
              placeholder="gpt-4o / deepseek-chat"
            />
          </label>

          {/* 搜索服务选择 */}
          <label className="block text-sm">
            <span className="text-muted dark:text-gray-300">搜索服务</span>
            <select
              value={draft.search_provider}
              onChange={(e) => set('search_provider', e.target.value as SearchProvider)}
              className={inputCls}
            >
              <option value="">None（仅用 LLM 内部知识，标注“非实时”）</option>
              <option value="serper">Serper.dev</option>
              <option value="tavily">Tavily</option>
            </select>
          </label>

          {/* 搜索 API Key */}
          <label className="block text-sm">
            <span className="text-muted dark:text-gray-300">
              搜索 API Key <span className="text-xs">（可选）</span>
            </span>
            <div className="relative mt-1">
              <input
                type={showSearchKey ? 'text' : 'password'}
                value={draft.search_api_key}
                onChange={(e) => set('search_api_key', e.target.value)}
                className={`${inputCls} pr-16`}
                placeholder="Serper.dev 或 Tavily 的 Key，留空则不搜索"
              />
              <button
                type="button"
                onClick={() => setShowSearchKey((v) => !v)}
                className="absolute right-2 top-1/2 -translate-y-1/2 rounded px-2 py-1 text-xs text-muted hover:bg-stone-100 dark:text-gray-400 dark:hover:bg-gray-700"
                title={showSearchKey ? '隐藏' : '显示'}
              >
                {showSearchKey ? '🙈 隐藏' : '👁 显示'}
              </button>
            </div>
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

          <p className="rounded-lg bg-amber-50 p-3 text-xs text-amber-800 dark:bg-amber-900/30 dark:text-amber-200">
            ⚠️ 隐私提示：简历文本会发送给您配置的 LLM API 和搜索 API 进行处理，请确认信任该服务。
          </p>
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
