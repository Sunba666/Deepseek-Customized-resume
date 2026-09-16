import { useCallback, useRef, useState } from 'react'

interface Props {
  onFile: (file: File) => void
  onRemove?: () => void
  loading?: boolean
  fileName?: string
  fileSize?: number
}

const ALLOWED = ['.pdf', '.docx', '.txt']
const MAX_UPLOAD_BYTES = 10 * 1024 * 1024

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}

export default function UploadZone({ onFile, onRemove, loading, fileName, fileSize }: Props) {
  const [drag, setDrag] = useState(false)
  const [typeError, setTypeError] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const pick = useCallback(
    (file: File | undefined) => {
      if (!file) return
      const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
      if (!ALLOWED.includes(ext)) {
        setTypeError(`不支持的文件类型：${ext || '(无扩展名)'}，仅支持 PDF / DOCX / TXT`)
        return
      }
      if (file.size === 0 || file.size > MAX_UPLOAD_BYTES) {
        setTypeError(file.size === 0 ? '上传文件为空' : '文件不能超过 10 MB')
        return
      }
      setTypeError('')
      onFile(file)
    },
    [onFile],
  )

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setDrag(false)
      pick(e.dataTransfer.files?.[0])
    },
    [pick],
  )

  // 已上传文件 → 展示文件信息 + 移除按钮
  if (fileName) {
    return (
      <div className="rounded-xl border border-stone-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="text-2xl shrink-0">📄</div>
            <div className="min-w-0">
              <p className="font-medium truncate text-ink dark:text-gray-100">{fileName}</p>
              {fileSize !== undefined && (
                <p className="text-xs text-muted dark:text-gray-400">
                  {formatSize(fileSize)} · 已解析，自动脱敏
                </p>
              )}
            </div>
          </div>
          <button
            onClick={() => {
              if (inputRef.current) inputRef.current.value = ''
              onRemove?.()
            }}
            disabled={loading}
            className="shrink-0 rounded-lg border border-stone-300 px-3 py-1.5 text-xs hover:border-red-400 hover:text-red-600 disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:border-red-400 dark:hover:text-red-400"
            title="移除并重新上传"
          >
            ✕ 移除
          </button>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault()
          setDrag(true)
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={handleDrop}
        className={`cursor-pointer rounded-xl border-2 border-dashed p-10 text-center transition-colors ${
          drag
            ? 'border-stone-900 bg-stone-100 dark:border-gray-100 dark:bg-gray-700'
            : 'border-stone-300 hover:border-stone-400 dark:border-gray-600 dark:hover:border-gray-400'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          className="hidden"
          onChange={(e) => {
            pick(e.target.files?.[0])
            e.target.value = ''
          }}
        />
        <div className="text-3xl mb-2">{loading ? '⏳' : '📄'}</div>
        <p className="font-medium text-ink dark:text-gray-100">
          {loading ? '解析中…' : '拖拽简历到这里，或点击选择文件'}
        </p>
        <p className="mt-1 text-xs text-muted dark:text-gray-400">支持 PDF / DOCX / TXT · 本地解析，不上传服务器</p>
      </div>
      {typeError && (
        <p className="mt-2 rounded-lg border border-red-200 bg-red-50 p-2 text-xs text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-300">
          {typeError}
        </p>
      )}
    </div>
  )
}
