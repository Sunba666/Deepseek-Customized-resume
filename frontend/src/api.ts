// 与后端通信的 API 封装（开发模式经 Vite proxy 转发到 127.0.0.1:8000）
import type {
  Plan,
  Portrait,
  ResumeParseResult,
  Settings,
  StarSuggestion,
} from './types'

const BASE = '/api'

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(detail || `请求失败 (${res.status})`)
  }
  return res.json() as Promise<T>
}

export function parseResume(file: File): Promise<ResumeParseResult> {
  const form = new FormData()
  form.append('file', file)
  return fetch(`${BASE}/resume/parse`, { method: 'POST', body: form }).then(async (res) => {
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  })
}

export function generatePortrait(req: {
  text?: string
  redacted_text?: string
  target_role?: string
  city?: string
}): Promise<Portrait> {
  return post('/analysis/portrait', req)
}

export function recommend(req: {
  portrait: Portrait
  city?: string
  with_star?: boolean
  resume_text?: string
}): Promise<Plan> {
  return post('/companies/recommend', req)
}

export function starAdvice(req: {
  text?: string
  redacted_text?: string
  target_role?: string
}): Promise<StarSuggestion[]> {
  return post('/analysis/star', req)
}

export function exportMarkdown(plan: Plan, redacted = true): Promise<{ markdown: string; filename: string }> {
  return post('/export/markdown', { plan, redacted })
}

export function health(): Promise<Settings & { status: string }> {
  return fetch(`${BASE}/health`).then((r) => r.json())
}

export function saveSettings(settings: {
  llm_base_url: string
  llm_api_key: string
  llm_model: string
}): Promise<{ ok: boolean }> {
  // 本地优先：设置仅保存到 localStorage（后端不存储任何用户配置）
  localStorage.setItem('ra_settings', JSON.stringify(settings))
  return Promise.resolve({ ok: true })
}

export function loadSettings(): {
  llm_base_url: string
  llm_api_key: string
  llm_model: string
} {
  try {
    const raw = localStorage.getItem('ra_settings')
    if (raw) return JSON.parse(raw)
  } catch {
    /* ignore */
  }
  return { llm_base_url: 'https://api.deepseek.com', llm_api_key: '', llm_model: 'deepseek-chat' }
}
