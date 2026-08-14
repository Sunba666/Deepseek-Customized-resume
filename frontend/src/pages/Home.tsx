import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import UploadZone from '../components/UploadZone'
import { generatePortrait, parseResume, recommend } from '../api'
import type { Plan, Portrait } from '../types'

export default function Home() {
  const navigate = useNavigate()
  const [parsing, setParsing] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')

  const [fileName, setFileName] = useState('')
  const [fileSize, setFileSize] = useState(0)
  const [redactedText, setRedactedText] = useState('')
  const [inferred, setInferred] = useState<{ role: string; skills: string[]; years: string } | null>(null)

  const [targetRole, setTargetRole] = useState('')
  const [city, setCity] = useState('')
  const [withStar, setWithStar] = useState(false)
  const [portrait, setPortrait] = useState<Portrait | null>(null)

  const handleFile = async (file: File) => {
    setError('')
    setParsing(true)
    setPortrait(null)
    setInferred(null)
    try {
      const r = await parseResume(file)
      setFileName(r.filename)
      setFileSize(file.size)
      setRedactedText(r.redacted_text)
      setInferred({
        role: r.preview.inferred_role,
        skills: r.preview.skills,
        years: r.preview.years_experience,
      })
      setTargetRole(r.preview.inferred_role)
    } catch (e) {
      setError(e instanceof Error ? e.message : '解析失败')
    } finally {
      setParsing(false)
    }
  }

  const handleRemove = () => {
    setFileName('')
    setFileSize(0)
    setRedactedText('')
    setInferred(null)
    setPortrait(null)
    setTargetRole('')
    setCity('')
    setError('')
  }

  const handleGenerate = async () => {
    if (!redactedText) {
      setError('请先上传简历')
      return
    }
    setError('')
    setGenerating(true)
    try {
      // 1) 生成/确认职业画像
      const p = await generatePortrait({
        redacted_text: redactedText,
        target_role: targetRole,
        city,
      })
      setPortrait(p)
      // 2) 生成完整方案（含 STAR 建议，若开启）
      const plan = await recommend({
        portrait: p,
        city,
        with_star: withStar,
        resume_text: redactedText,
      })
      navigate('/result', { state: { plan } })
    } catch (e) {
      setError(e instanceof Error ? e.message : '生成失败')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="space-y-6">
      <section>
        <h1 className="text-2xl font-semibold mb-1">生成定制化求职方案</h1>
        <p className="text-sm text-muted">
          上传简历 → 确认岗位画像 → 获得公司推荐、风险核验与投递渠道
        </p>
      </section>

      <UploadZone
        onFile={handleFile}
        onRemove={handleRemove}
        loading={parsing}
        fileName={fileName}
        fileSize={fileSize}
      />

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {inferred && (
        <section className="rounded-xl border border-stone-200 bg-white p-4 shadow-sm space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="font-medium">✅ 解析完成，请确认以下信息</h2>
            <button
              onClick={() => {
                const blob = new Blob([redactedText], { type: 'text/plain;charset=utf-8' })
                const a = document.createElement('a')
                a.href = URL.createObjectURL(blob)
                a.download = `匿名简历_${fileName}.txt`
                a.click()
                URL.revokeObjectURL(a.href)
              }}
              className="rounded-lg border border-stone-300 px-3 py-1.5 text-xs hover:border-stone-500"
              title="导出脱敏后的简历文本，可安全分享"
            >
              ⬇ 导出匿名简历
            </button>
          </div>
          <p className="text-sm text-muted">
            推断岗位：<b>{inferred.role}</b> · 技能：{inferred.skills.join('、') || '未识别'} · 经验：{inferred.years || '未识别'}
          </p>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block text-sm">
              <span className="text-muted">目标岗位（可修改）</span>
              <input
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                className="mt-1 w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:outline-none focus:border-stone-500"
                placeholder="如：数据分析师-偏业务方向"
              />
            </label>
            <label className="block text-sm">
              <span className="text-muted">期望城市（可选）</span>
              <input
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className="mt-1 w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:outline-none focus:border-stone-500"
                placeholder="如：北京 / 上海 / 不限"
              />
            </label>
          </div>

          <label className="flex items-center gap-2 text-sm cursor-pointer select-none">
            <input
              type="checkbox"
              checked={withStar}
              onChange={(e) => setWithStar(e.target.checked)}
              className="accent-stone-900"
            />
            分析简历并给出优化建议（基于 STAR 法则）
            <span className="text-xs text-muted">默认关闭</span>
          </label>

          <button
            onClick={handleGenerate}
            disabled={generating}
            className="w-full rounded-lg bg-stone-900 py-2.5 text-sm font-medium text-white hover:bg-stone-700 disabled:opacity-50"
          >
            {generating ? '生成中…' : '生成方案'}
          </button>
        </section>
      )}

      {portrait && !generating && (
        <p className="text-xs text-muted">职业画像已生成：{portrait.summary}</p>
      )}

      {/* 隐私提示 */}
      <p className="border-t border-stone-200 pt-4 text-xs text-muted">
        本地运行 · 简历与报告不上传任何服务器 · 数据默认脱敏
      </p>
    </div>
  )
}
