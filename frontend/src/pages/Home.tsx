import { useEffect, useRef, useState } from 'react'
import UploadZone from '../components/UploadZone'
import { parseResume } from '../api'

interface AnalysisState {
  status: 'idle' | 'uploading' | 'analyzing' | 'done'
  fileName?: string
  fileSize?: number
  inferred?: { role: string; skills: string[]; years: string }
  text?: string
  error?: string
}

export default function Home() {
  const [state, setState] = useState<AnalysisState>({ status: 'idle' })
  const timerRef = useRef<number | null>(null)

  // 组件卸载时清理模拟分析定时器
  useEffect(() => {
    return () => {
      if (timerRef.current) window.clearTimeout(timerRef.current)
    }
  }, [])

  const handleFile = async (file: File) => {
    // 清理上一次的模拟分析定时器
    if (timerRef.current) window.clearTimeout(timerRef.current)
    setState({ status: 'uploading', fileName: file.name, fileSize: file.size })
    try {
      // 保留后端能力：真实解析（脱敏 + 画像推断）
      const r = await parseResume(file)
      setState({
        status: 'analyzing',
        fileName: file.name,
        fileSize: file.size,
        inferred: {
          role: r.preview.inferred_role,
          skills: r.preview.skills,
          years: r.preview.years_experience,
        },
        text: r.redacted_text,
      })
      // 模拟 AI 深度分析延迟
      timerRef.current = window.setTimeout(() => {
        setState((prev) => ({ ...prev, status: 'done' }))
      }, 1500)
    } catch (e) {
      setState({
        status: 'idle',
        fileName: file.name,
        error: e instanceof Error ? e.message : '解析失败',
      })
    }
  }

  const handleRemove = () => {
    if (timerRef.current) window.clearTimeout(timerRef.current)
    setState({ status: 'idle' })
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* 左栏：简历上传区 */}
      <section className="lg:h-[calc(100vh-10rem)] lg:overflow-y-auto">
        <h2 className="mb-3 text-sm font-medium text-muted dark:text-gray-400">简历上传</h2>
        <UploadZone
          onFile={handleFile}
          onRemove={handleRemove}
          loading={state.status === 'uploading' || state.status === 'analyzing'}
          fileName={state.fileName}
          fileSize={state.fileSize}
        />
        {state.error && (
          <p className="mt-2 rounded-lg border border-red-200 bg-red-50 p-2 text-xs text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-300">
            {state.error}
          </p>
        )}
      </section>

      {/* 右栏：AI 分析窗口 */}
      <section className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800 lg:h-[calc(100vh-10rem)] lg:overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-medium text-muted dark:text-gray-400">AI 分析</h2>
          {state.status === 'done' && (
            <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">
              分析完成
            </span>
          )}
        </div>

        {state.status === 'idle' && (
          <div className="flex h-64 flex-col items-center justify-center text-center text-muted dark:text-gray-400">
            <div className="text-4xl mb-3">🤖</div>
            <p className="text-sm">上传简历后自动开始分析</p>
          </div>
        )}

        {state.status === 'uploading' && (
          <div className="flex h-64 flex-col items-center justify-center text-center">
            <div className="mb-3 h-8 w-8 animate-spin rounded-full border-2 border-stone-300 border-t-stone-900 dark:border-gray-600 dark:border-t-gray-100" />
            <p className="text-sm text-muted dark:text-gray-400">解析中…</p>
          </div>
        )}

        {state.status === 'analyzing' && (
          <div className="flex h-64 flex-col items-center justify-center text-center">
            <div className="mb-3 h-8 w-8 animate-spin rounded-full border-2 border-stone-300 border-t-stone-900 dark:border-gray-600 dark:border-t-gray-100" />
            <p className="text-sm text-muted dark:text-gray-400">正在分析…</p>
          </div>
        )}

        {state.status === 'done' && state.inferred && (
          <div className="space-y-4">
            {/* 岗位画像 */}
            <div>
              <h3 className="mb-2 text-sm font-semibold">🎯 岗位画像</h3>
              <p className="text-sm">
                目标岗位：<b className="text-ink dark:text-gray-100">{state.inferred.role}</b>
              </p>
              {state.inferred.years && (
                <p className="mt-1 text-xs text-muted dark:text-gray-400">
                  经验：{state.inferred.years}
                </p>
              )}
              {state.inferred.skills.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {state.inferred.skills.map((s) => (
                    <span
                      key={s}
                      className="rounded-full bg-stone-100 px-2.5 py-0.5 text-xs text-stone-700 dark:bg-gray-700 dark:text-gray-200"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* 模拟 AI 分析结果 */}
            <div className="rounded-xl bg-stone-50 p-4 text-sm leading-relaxed text-stone-700 dark:bg-gray-900/50 dark:text-gray-300">
              <p className="mb-2 font-medium text-ink dark:text-gray-100">📊 AI 深度分析（模拟数据）</p>
              <ul className="list-disc space-y-1.5 pl-4">
                <li>
                  <b>匹配方向</b>：您的经历与「{state.inferred.role}」高度相关，建议优先投递该方向的
                  数据/业务团队。
                </li>
                <li>
                  <b>技能亮点</b>：{state.inferred.skills.slice(0, 3).join('、') || '未识别到明确技能'}，
                  与岗位要求匹配度良好。
                </li>
                <li>
                  <b>优化建议</b>：建议在经历描述中补充量化成果（如「效率提升 X% / 覆盖用户 Y 万」），
                  并突出个人贡献角色。
                </li>
                <li>
                  <b>风险提示</b>：本分析为演示数据，接入 LLM API Key 后可获得更深入的针对性建议。
                </li>
              </ul>
            </div>

            <p className="text-xs text-muted dark:text-gray-500">
              已按脱敏规则隐藏手机号/邮箱/身份证/住址；完整解析文本仅保存在本地。
            </p>
          </div>
        )}
      </section>
    </div>
  )
}
