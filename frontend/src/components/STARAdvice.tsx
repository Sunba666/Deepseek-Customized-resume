import { useState } from 'react'
import type { StarSuggestion } from '../types'

export default function STARAdvice({ advice }: { advice: StarSuggestion[] }) {
  const [open, setOpen] = useState<number | null>(0)

  if (advice.length === 0) return null

  return (
    <div className="mt-8">
      <h2 className="text-lg font-semibold mb-3">简历优化建议（STAR 法则）</h2>
      <div className="space-y-3">
        {advice.map((s, i) => (
          <div key={i} className="rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
            <button
              onClick={() => setOpen(open === i ? null : i)}
              className="w-full text-left text-sm"
            >
              <span className="font-medium">原文：{s.quote}</span>
            </button>
            {open === i && (
              <div className="mt-3 space-y-2 text-sm border-t border-stone-100 pt-3">
                <p className="text-amber-700">⚠️ {s.problem}</p>
                <p><span className="font-medium text-muted">S（情境）：</span>{s.situation}</p>
                <p><span className="font-medium text-muted">T（任务）：</span>{s.task}</p>
                <p><span className="font-medium text-muted">A（行动）：</span>{s.action}</p>
                <p><span className="font-medium text-muted">R（结果）：</span>{s.result}</p>
                {s.rewrite && (
                  <p className="rounded-lg bg-stone-50 p-3 text-xs">
                    <span className="font-medium">✍️ 改写示例：</span>
                    {s.rewrite}
                  </p>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
