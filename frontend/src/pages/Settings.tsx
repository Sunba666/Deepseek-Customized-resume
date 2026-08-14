import { useEffect, useState } from 'react'
import { health, loadSettings, saveSettings } from '../api'

export default function Settings() {
  const [baseUrl, setBaseUrl] = useState('https://api.deepseek.com')
  const [apiKey, setApiKey] = useState('')
  const [model, setModel] = useState('deepseek-chat')
  const [saved, setSaved] = useState('')
  const [serverInfo, setServerInfo] = useState<{ llm_enabled: boolean; llm_model: string; risk_sources?: { name: string; url: string }[] } | null>(null)

  useEffect(() => {
    const s = loadSettings()
    setBaseUrl(s.llm_base_url)
    setApiKey(s.llm_api_key)
    setModel(s.llm_model)
    health()
      .then((h) => setServerInfo(h))
      .catch(() => setServerInfo({ llm_enabled: false, llm_model: '后端未启动' }))
  }, [])

  const handleSave = () => {
    saveSettings({ llm_base_url: baseUrl, llm_api_key: apiKey, llm_model: model })
    setSaved('已保存（本地存储，重启后端后生效）')
    setTimeout(() => setSaved(''), 3000)
  }

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
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            className="mt-1 w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:outline-none focus:border-stone-500"
            placeholder="https://api.deepseek.com"
          />
        </label>
        <label className="block text-sm">
          <span className="text-muted">API Key</span>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            className="mt-1 w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:outline-none focus:border-stone-500"
            placeholder="sk-..."
          />
        </label>
        <label className="block text-sm">
          <span className="text-muted">模型名</span>
          <input
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="mt-1 w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:outline-none focus:border-stone-500"
            placeholder="deepseek-chat"
          />
        </label>

        <button
          onClick={handleSave}
          className="rounded-lg bg-stone-900 px-4 py-2 text-sm text-white hover:bg-stone-700"
        >
          保存
        </button>
        {saved && <span className="ml-3 text-xs text-emerald-700">{saved}</span>}
      </section>

      {/* 数据源与隐私 */}
      <section className="rounded-xl border border-stone-200 bg-white p-5 shadow-sm space-y-3">
        <h2 className="font-medium">🛡 数据源与隐私</h2>
        <ul className="text-sm text-muted space-y-1.5">
          <li>• 简历解析、分析、报告生成默认全部在本地完成</li>
          <li>• 导出文件自动脱敏（手机号 / 邮箱 / 身份证 / 住址）</li>
          <li>• 提供「导出匿名简历」能力（脱敏后分享）</li>
          <li>
            • 公司数据优先读取本地企业库，无真实数据源 Key 时使用模拟数据并标注
          </li>
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

      {/* 匿名简历导出说明 */}
      <section className="rounded-xl border border-stone-200 bg-white p-5 shadow-sm">
        <h2 className="font-medium mb-2">📤 导出匿名简历</h2>
        <p className="text-sm text-muted">
          在结果页导出 Markdown 或打印 PDF 时，报告已自动脱敏；如需分享匿名简历，请使用脱敏后的文本。
        </p>
      </section>
    </div>
  )
}
