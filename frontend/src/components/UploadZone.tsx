import { useCallback, useRef, useState } from 'react'

interface Props {
  onFile: (file: File) => void
  loading?: boolean
}

export default function UploadZone({ onFile, loading }: Props) {
  const [drag, setDrag] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setDrag(false)
      const file = e.dataTransfer.files?.[0]
      if (file) onFile(file)
    },
    [onFile],
  )

  return (
    <div
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault()
        setDrag(true)
      }}
      onDragLeave={() => setDrag(false)}
      onDrop={handleDrop}
      className={`cursor-pointer rounded-xl border-2 border-dashed p-10 text-center transition-colors ${
        drag ? 'border-stone-900 bg-stone-100' : 'border-stone-300 hover:border-stone-400'
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx,.txt"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) onFile(file)
          e.target.value = ''
        }}
      />
      <div className="text-3xl mb-2">📄</div>
      <p className="font-medium">{loading ? '解析中…' : '拖拽简历到这里，或点击选择文件'}</p>
      <p className="mt-1 text-xs text-muted">支持 PDF / DOCX / TXT · 本地解析，不上传服务器</p>
    </div>
  )
}
