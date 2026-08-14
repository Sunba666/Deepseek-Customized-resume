import { useRef, useState } from 'react'
import UploadZone from '../components/UploadZone'
import AnalysisWindow from '../components/AnalysisWindow'
import { analyzeResume, loadSettings } from '../api'
import type { AnalyzeResult } from '../api'

type Status = 'idle' | 'uploading' | 'analyzing' | 'done' | 'error'

interface FileInfo {
  name: string
  size: number
}

export default function Home() {
  const [fileInfo, setFileInfo] = useState<FileInfo | null>(null)
  const [status, setStatus] = useState<Status>('idle')
  const [result, setResult] = useState<AnalyzeResult>()
  const [error, setError] = useState('')
  const analyzingRef = useRef(false)

  const handleFile = async (file: File) => {
    if (analyzingRef.current) return
    setError('')
    setResult(undefined)
    setFileInfo({ name: file.name, size: file.size })
    setStatus('uploading')
    try {
      const settings = loadSettings()
      // 上传后立即调用后端分析接口（真实 LLM + 可选搜索）
      setStatus('analyzing')
      analyzingRef.current = true
      const r = await analyzeResume(file, settings)
      setResult(r)
      setStatus('done')
    } catch (e) {
      setError(e instanceof Error ? e.message : '分析失败')
      setStatus('error')
    } finally {
      analyzingRef.current = false
    }
  }

  const handleRemove = () => {
    if (analyzingRef.current) return
    setFileInfo(null)
    setResult(undefined)
    setError('')
    setStatus('idle')
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* 左栏：简历上传区 */}
      <section className="lg:h-[calc(100vh-10rem)] lg:overflow-y-auto">
        <h2 className="mb-3 text-sm font-medium text-muted dark:text-gray-400">简历上传</h2>
        <UploadZone
          onFile={handleFile}
          onRemove={handleRemove}
          loading={status === 'uploading' || status === 'analyzing'}
          fileName={fileInfo?.name}
          fileSize={fileInfo?.size}
        />
      </section>

      {/* 右栏：AI 分析窗口 */}
      <AnalysisWindow status={status} result={result} error={error} />
    </div>
  )
}
