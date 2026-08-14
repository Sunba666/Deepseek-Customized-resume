import { useState } from 'react'
import type { Company } from '../types'
import RiskBadge from './RiskBadge'

export default function CompanyCard({ company }: { company: Company }) {
  const [open, setOpen] = useState(false)

  return (
    <div className="rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold">
            {company.name}
            {company.is_mock && (
              <span className="ml-2 rounded bg-stone-100 px-1.5 py-0.5 text-[10px] text-muted">模拟</span>
            )}
          </h3>
          <p className="mt-0.5 text-sm text-muted">
            {[company.city, company.industry, company.size].filter(Boolean).join(' · ') || '信息待补充'}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          {company.risk && <RiskBadge level={company.risk.level} />}
          <span className="text-xs text-muted">匹配度 {company.match_score}/100</span>
        </div>
      </div>

      {company.recommend_reason && (
        <p className="mt-2 text-sm text-muted">{company.recommend_reason}</p>
      )}

      <button
        onClick={() => setOpen(!open)}
        className="no-print mt-3 text-xs text-stone-500 hover:text-ink"
      >
        {open ? '收起详情 ▲' : '展开详情 ▼'}
      </button>

      {open && (
        <div className="mt-3 space-y-3 border-t border-stone-100 pt-3 text-sm">
          {/* 风险 */}
          {company.risk && (
            <div>
              <p className="font-medium text-xs text-muted mb-1">
                风险核验
                {company.risk.is_mock && <span className="ml-1">（模拟数据 · 数据获取 {company.risk.data_time}）</span>}
              </p>
              <p>{company.risk.summary}</p>
              <ul className="mt-1 space-y-1 text-xs">
                {company.risk.items.map((it, i) => (
                  <li key={i} className="text-muted">
                    • {it.type}：{it.description}
                    {it.source_url && (
                      <>
                        {' '}
                        <a className="underline" href={it.source_url} target="_blank" rel="noreferrer">
                          {it.source_name || '证据来源'}
                        </a>
                      </>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 投递渠道 */}
          {company.channels.length > 0 && (
            <div>
              <p className="font-medium text-xs text-muted mb-1">投递渠道</p>
              <ul className="space-y-0.5 text-xs">
                {company.channels.map((ch, i) => (
                  <li key={i}>
                    {ch.url ? (
                      <a className="text-stone-700 underline" href={ch.url} target="_blank" rel="noreferrer">
                        {ch.name}
                      </a>
                    ) : (
                      ch.name
                    )}
                    {ch.note && <span className="text-muted">（{ch.note}）</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 匹配理由 */}
          {company.match_reasons.length > 0 && (
            <div>
              <p className="font-medium text-xs text-muted mb-1">匹配理由</p>
              <ul className="list-disc pl-4 space-y-0.5 text-xs text-muted">
                {company.match_reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
