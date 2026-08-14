import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import CompanyCard from '../components/CompanyCard'
import STARAdvice from '../components/STARAdvice'
import { exportMarkdown } from '../api'
import type { Plan } from '../types'

export default function Result() {
  const location = useLocation()
  const navigate = useNavigate()
  const plan: Plan | undefined = location.state?.plan
  const [exporting, setExporting] = useState(false)
  const [done, setDone] = useState('')

  if (!plan) {
    return (
      <div className="text-center py-16">
        <p className="text-muted mb-4">还没有方案，请先上传简历生成</p>
        <button
          onClick={() => navigate('/')}
          className="rounded-lg bg-stone-900 px-4 py-2 text-sm text-white"
        >
          返回首页
        </button>
      </div>
    )
  }

  const handleExport = async () => {
    setExporting(true)
    setDone('')
    try {
      const { markdown, filename } = await exportMarkdown(plan, true)
      const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' })
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = filename
      a.click()
      URL.revokeObjectURL(a.href)
      setDone('Markdown 已导出（默认脱敏）。PDF 请点「打印」→ 目标选「另存为 PDF」。')
    } catch (e) {
      setDone(e instanceof Error ? e.message : '导出失败')
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="no-print flex items-center justify-between">
        <button
          onClick={() => navigate('/')}
          className="text-sm text-muted hover:text-ink"
        >
          ← 返回修改
        </button>
        <div className="flex gap-2">
          <button
            onClick={handleExport}
            disabled={exporting}
            className="rounded-lg border border-stone-300 px-3 py-1.5 text-sm hover:border-stone-500 disabled:opacity-50"
          >
            {exporting ? '导出中…' : '⬇ 导出 Markdown'}
          </button>
          <button
            onClick={() => window.print()}
            className="rounded-lg bg-stone-900 px-3 py-1.5 text-sm text-white hover:bg-stone-700"
          >
            🖨 打印 / 另存为 PDF
          </button>
        </div>
      </div>
      {done && <p className="no-print text-xs text-muted">{done}</p>}
      {plan.mock_notice && (
        <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          ⚠️ {plan.mock_notice}
        </p>
      )}

      {/* 职业画像 */}
      <section className="rounded-xl border border-stone-200 bg-white p-5 shadow-sm">
        <h2 className="font-semibold mb-2">🎯 职业画像</h2>
        <p className="text-sm">
          目标岗位：<b>{plan.portrait.target_role}</b>
          {plan.portrait.city && <> · 城市：{plan.portrait.city}</>}
        </p>
        {plan.portrait.years_experience && (
          <p className="text-sm text-muted mt-1">经验：{plan.portrait.years_experience}</p>
        )}
        {plan.portrait.skills.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {plan.portrait.skills.map((s) => (
              <span key={s} className="rounded-full bg-stone-100 px-2.5 py-0.5 text-xs text-stone-700">
                {s}
              </span>
            ))}
          </div>
        )}
        {plan.portrait.summary && <p className="mt-2 text-xs text-muted">{plan.portrait.summary}</p>}
      </section>

      {/* 公司列表 */}
      <section>
        <h2 className="font-semibold mb-3">
          推荐公司（{plan.companies.length} 家）
          <span className="ml-2 text-xs font-normal text-muted">生成于 {plan.generated_at}</span>
        </h2>
        <div className="space-y-3">
          {plan.companies.map((c) => (
            <CompanyCard key={c.name} company={c} />
          ))}
        </div>
      </section>

      {/* STAR 建议 */}
      <STARAdvice advice={plan.star_advice} />
    </div>
  )
}
