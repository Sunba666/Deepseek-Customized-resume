import type { AnalyzeResult } from '../api'

interface Props {
  status: 'idle' | 'uploading' | 'analyzing' | 'done' | 'error'
  result?: AnalyzeResult
  error?: string
}

const riskStyles: Record<string, string> = {
  normal: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/40 dark:text-emerald-300 dark:border-emerald-800',
  caution: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/40 dark:text-amber-300 dark:border-amber-800',
  high: 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/40 dark:text-red-300 dark:border-red-800',
  unknown: 'bg-stone-50 text-stone-500 border-stone-200 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600',
}

function RiskBadge({ level, label }: { level: string; label: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${riskStyles[level] || riskStyles.unknown}`}
    >
      {label}
    </span>
  )
}

export default function AnalysisWindow({ status, result, error }: Props) {
  return (
    <div className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800 lg:h-[calc(100vh-10rem)] lg:overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-medium text-muted dark:text-gray-400">AI 分析</h2>
        {status === 'done' && result && (
          <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">
            分析完成{result.realtime ? '' : ' · 非实时'}
          </span>
        )}
      </div>

      {/* 初始提示 */}
      {status === 'idle' && (
        <div className="flex h-64 flex-col items-center justify-center text-center text-muted dark:text-gray-400">
          <div className="text-4xl mb-3">🤖</div>
          <p className="text-sm">上传简历后自动开始分析</p>
        </div>
      )}

      {/* 解析中 */}
      {status === 'uploading' && (
        <div className="flex h-64 flex-col items-center justify-center text-center">
          <div className="mb-3 h-8 w-8 animate-spin rounded-full border-2 border-stone-300 border-t-stone-900 dark:border-gray-600 dark:border-t-gray-100" />
          <p className="text-sm text-muted dark:text-gray-400">解析中…</p>
        </div>
      )}

      {/* 深度分析中 */}
      {status === 'analyzing' && (
        <div className="flex h-64 flex-col items-center justify-center text-center">
          <div className="mb-3 h-8 w-8 animate-spin rounded-full border-2 border-stone-300 border-t-stone-900 dark:border-gray-600 dark:border-t-gray-100" />
          <p className="text-sm text-muted dark:text-gray-400">正在深度分析中…</p>
          <p className="mt-1 text-xs text-muted dark:text-gray-400">调用 LLM 处理中，可能需要数十秒</p>
        </div>
      )}

      {/* 错误 */}
      {status === 'error' && (
        <div className="flex h-64 flex-col items-center justify-center text-center">
          <div className="text-3xl mb-3">⚠️</div>
          <p className="text-sm text-red-600 dark:text-red-400">{error || '分析失败'}</p>
          <p className="mt-2 text-xs text-muted dark:text-gray-400">
            请检查设置中的 LLM API Key 与网络连接后重试
          </p>
        </div>
      )}

      {/* 结果 */}
      {status === 'done' && result && (
        <div className="space-y-6">
          {result.notice && (
            <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-800 dark:bg-amber-900/30 dark:text-amber-200">
              ⚠️ {result.notice}
            </p>
          )}

          {/* 职业画像 */}
          <section>
            <h3 className="mb-2 text-sm font-semibold">🎯 职业画像</h3>
            <p className="text-sm">
              目标岗位：<b className="text-ink dark:text-gray-100">{result.portrait.target_role}</b>
            </p>
            <div className="mt-1.5 space-y-0.5 text-xs text-muted dark:text-gray-400">
              {result.portrait.years_experience && <p>经验：{result.portrait.years_experience}</p>}
              {result.portrait.education && <p>学历：{result.portrait.education}</p>}
              {result.portrait.city && <p>城市：{result.portrait.city}</p>}
            </div>
            {result.portrait.skills.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {result.portrait.skills.map((s) => (
                  <span
                    key={s}
                    className="rounded-full bg-stone-100 px-2.5 py-0.5 text-xs text-stone-700 dark:bg-gray-700 dark:text-gray-200"
                  >
                    {s}
                  </span>
                ))}
              </div>
            )}
          </section>

          {/* 推荐公司 */}
          <section>
            <h3 className="mb-2 text-sm font-semibold">🏢 推荐公司</h3>
            <div className="space-y-3">
              {result.companies.map((c, i) => (
                <div key={i} className="rounded-xl border border-stone-200 p-3 dark:border-gray-700">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-ink dark:text-gray-100">{c.name}</p>
                      <p className="text-xs text-muted dark:text-gray-400">
                        {[c.city, c.industry].filter(Boolean).join(' · ') || '信息未知'}
                      </p>
                    </div>
                    <RiskBadge level={c.risk_level} label={c.risk_label} />
                  </div>
                  {c.recommend_reason && (
                    <p className="mt-1.5 text-xs text-muted dark:text-gray-400">{c.recommend_reason}</p>
                  )}
                  {/* 投递渠道 */}
                  {c.channels.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs font-medium text-muted dark:text-gray-400">投递渠道</p>
                      <ul className="mt-0.5 space-y-0.5">
                        {c.channels.map((ch, j) => (
                          <li key={j} className="text-xs">
                            {ch.url ? (
                              <a className="underline text-stone-700 dark:text-gray-200" href={ch.url} target="_blank" rel="noreferrer">
                                {ch.name}
                              </a>
                            ) : (
                              <span className="text-stone-700 dark:text-gray-200">{ch.name}</span>
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {/* 风险详情 */}
                  {c.risk_items.length > 0 && (
                    <ul className="mt-2 space-y-1">
                      {c.risk_items.map((it, j) => (
                        <li key={j} className="text-xs text-muted dark:text-gray-400">
                          • {it.type}：{it.description}
                          {it.source_url && (
                            <>
                              {' '}
                              <a className="underline" href={it.source_url} target="_blank" rel="noreferrer">
                                来源
                              </a>
                            </>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* STAR 优化建议 */}
          {result.star_advice.length > 0 && (
            <section>
              <h3 className="mb-2 text-sm font-semibold">✍️ 简历优化建议（STAR 法则）</h3>
              <div className="space-y-3">
                {result.star_advice.map((s, i) => (
                  <div key={i} className="rounded-xl border border-stone-200 p-3 text-xs dark:border-gray-700">
                    <p className="text-stone-700 dark:text-gray-200">
                      <span className="font-medium">原文：</span>{s.quote}
                    </p>
                    <p className="mt-1 text-amber-700 dark:text-amber-300">⚠️ {s.problem}</p>
                    <ul className="mt-1.5 space-y-0.5 text-muted dark:text-gray-400">
                      <li><b>S（情境）</b>：{s.situation}</li>
                      <li><b>T（任务）</b>：{s.task}</li>
                      <li><b>A（行动）</b>：{s.action}</li>
                      <li><b>R（结果）</b>：{s.result}</li>
                    </ul>
                    {s.rewrite && (
                      <p className="mt-1.5 rounded-lg bg-stone-50 p-2 text-stone-700 dark:bg-gray-900/50 dark:text-gray-200">
                        <span className="font-medium">✍️ 优化示例：</span>{s.rewrite}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  )
}
