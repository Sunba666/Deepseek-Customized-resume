import type { RiskLevel } from '../types'

const styles: Record<RiskLevel, string> = {
  normal: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  caution: 'bg-amber-50 text-amber-700 border-amber-200',
  high: 'bg-red-50 text-red-700 border-red-200',
  unknown: 'bg-stone-50 text-stone-500 border-stone-200',
}

const labels: Record<RiskLevel, string> = {
  normal: '🟢 正常',
  caution: '🟡 需注意',
  high: '🔴 高风险',
  unknown: '⚪ 未知',
}

export default function RiskBadge({ level }: { level: RiskLevel }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${styles[level]}`}
    >
      {labels[level]}
    </span>
  )
}
