import { useEffect, useState } from 'react'
import { health, loadSettings, resetSettings, saveSettings } from '../api'
import type { AppSettings } from '../api'

export default function Settings() {
  const [settings, setSettings] = useState<AppSettings>(loadSettings)
  const [saved, setSaved] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [serverInfo, setServerInfo] = useState<{ llm_enabled: boolean; llm_model: string; risk_sources?: { name: string; url: string }[] } | null>(null)

  useEffect(() => {
    const s = loadSettings()
    setSettings(s)
    health()
      .then((h) => setServerInfo(h))
      .catch(() => setServerInfo({ llm_enabled: false, llm_model: '后端未启动' }))
  }, [])

  const set = <K extends keyof AppSettings>(key: K, value: AppSettings[K]) =>
    setSettings((prev) => ({ ...prev, [key]: value }))

  const handleSave = () => {
    saveSettings(settings)
    setSaved('已保存（本地存储，重启后端后生效）')
    setTimeout(() => setSaved(''), 3000)
  }

  const handleReset = () => {
    const d = resetSettings()
    setSettings(d)
    setSaved('已恢复默认设置')
    setTimeout(() => setSaved(''), 3000)
  }

  const inputCls =
    'mt-1 w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:outline-none focus:border-stone-500'

  return (
    <div className="space-y-6 max-w-2xl">
      <section>
        <h1 className="text-2xl font-semibold">设置</h1>
        <p className="text-sm text-muted">全部配置仅保存在本地，不上传任何服务器</p>
      </section>

      {/* LLM 配置 */}
      <section className="rounded-xl border border-stone-200 bg-white p-5 shadow-sm space-y-4">
        <h2 className="font-medium">🤖 LLM 配置（OpenAI 兼容格式）</h2>
        <p className="text-xs text-muted">
          不填 Key 时使用本地规则引擎（岗位画像/匹配度/STAR 建议仍可用，文本较生硬）
        </p>

        <label className="block text-sm">
          <span className="text-muted">Base URL</span>
          <input
            value={settings.llm_base_url}
            onChange={(e) => set('llm_base_url', e.target.value)}
            className={inputCls}
            placeholder="https://api.deepseek.com（Ollama 可填 http://localhost:11434/v1）"
          />
        </label>

        <label className="block text-sm">
          <span className="text-muted">LLM API Key</span>
          <div className="relative mt-1">
            <input
              type={showKey ? 'text' : 'password'}
              value={settings.llm_api_key}
              onChange={(e) => set('llm_api_key', e.target.value)}
              className={`${inputCls} pr-16`}
              placeholder="例如 sk-...（OpenAI 或兼容服务）"
            />
            <button
              type="button"
              onClick={() => setShowKey((v) => !v)}
              className="absolute right-2 top-1/2 -translate-y-1/2 rounded px-2 py-1 text-xs text-muted hover:bg-stone-100"
              title={showKey ? '隐藏' : '显示'}
            >
              {showKey ? '🙈 隐藏' : '👁 显示'}
            </button>
          </div>
        </label>

        <label className="block text-sm">
          <span className="text-muted">模型名</span>
          <input
            value={settings.llm_model}
            onChange={(e) => set('llm_model', e.target.value)}
            className={inputCls}
            placeholder="deepseek-chat"
          />
        </label>
      </section>

      {/* 数据源配置 */}
      <section className="rounded-xl border border-stone-200 bg-white p-5 shadow-sm space-y-4">
        <h2 className="font-medium">🏢 数据源 API（可选）</h2>
        <p className="text-xs text-muted">
          留空时使用本地企业库 / 模拟数据；填入企查查、天眼查开放平台 Key 后可获取真实企业信用数据
        </p>

        <label className="block text-sm">
          <span className="text-muted">企查查 API Key</span>
          <input
            type="password"
            value={settings.qcc_api_key}
            onChange={(e) => set('qcc_api_key', e.target.value)}
            className={inputCls}
            placeholder="可留空，留空时使用模拟数据"
          />
        </label>
        <label className="block text-sm">
          <span className="text-muted">天眼查 API Key</span>
          <input
            type="password"
            value={settings.tianyancha_api_key}
            onChange={(e) => set('tianyancha_api_key', e.target.value)}
            className={inputCls}
            placeholder="可留空，留空时使用模拟数据"
          />
        </label>
      </section>

      {/* 隐私 */}
      <section className="rounded-xl border border-stone-200 bg-white p-5 shadow-sm space-y-4">
        <h2 className="font-medium">🛡 隐私</h2>
        <label className="flex items-center justify-between gap-3 cursor-pointer select-none">
          <span className="text-sm">
            默认开启本地脱敏
            <span className="block text-xs text-muted">导出报告与匿名简历时自动隐藏手机号/邮箱/身份证/住址</span>
          </span>
          <button
            type="button"
            role="switch"
            aria-checked={settings.redact_by_default}
            onClick={() => set('redact_by_default', !settings.redact_by_default)}
            className={`relative h-6 w-11 rounded-full transition-colors ${
              settings.redact_by_default ? 'bg-stone-900' : 'bg-stone-300'
            }`}
          >
            <span
              className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all ${
                settings.redact_by_default ? 'left-[22px]' : 'left-0.5'
              }`}
            />
          </button>
        </label>
        <ul className="text-sm text-muted space-y-1.5">
          <li>• 简历解析、分析、报告生成默认全部在本地完成</li>
          <li>• 公司数据优先读取本地企业库，无真实数据源 Key 时使用模拟数据并标注</li>
        </ul>
        {serverInfo && (
          <div className="rounded-lg bg-stone-50 p-3 text-xs text-muted space-y-1">
            <p>后端状态：{serverInfo.llm_model === '后端未启动' ? '未启动' : '运行中'}</p>
            {serverInfo.llm_model !== '后端未启动' && (
              <p>
                LLM：{serverInfo.llm_enabled ? '已配置' : '未配置（规则引擎模式）'} · 模型：{serverInfo.llm_model}
              </p>
            )}
            {serverInfo.risk_sources && serverInfo.risk_sources.length > 0 && (
              <p>风险数据源：{serverInfo.risk_sources.map((s) => s.name).join('、')}</p>
            )}
          </div>
        )}
      </section>

      {/* 操作按钮 */}
      <section className="flex items-center gap-3">
        <button
          onClick={handleSave}
          className="rounded-lg bg-stone-900 px-5 py-2 text-sm text-white hover:bg-stone-700"
        >
          保存
        </button>
        <button
          onClick={handleReset}
          className="rounded-lg border border-stone-300 px-5 py-2 text-sm hover:border-stone-500"
        >
          恢复默认
        </button>
        {saved && <span className="text-xs text-emerald-700">{saved}</span>}
      </section>
    </div>
  )
}
