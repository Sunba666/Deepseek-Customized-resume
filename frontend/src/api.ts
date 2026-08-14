// 与后端通信的 API 封装
// 基础路径可配置：默认相对路径 /api（开发模式经 Vite proxy 转发到 127.0.0.1:8000，
// 生产模式由 FastAPI 同源托管）。可用环境变量 VITE_API_BASE 或 localStorage 的
// ra_api_base 覆盖为绝对地址（如 http://localhost:8000/api）。
import type {
  Plan,
  Portrait,
  ResumeParseResult,
  Settings,
  StarSuggestion,
} from './types'

function resolveBase(): string {
  const stored = (() => {
    try {
      return localStorage.getItem('ra_api_base') || ''
    } catch {
      return ''
    }
  })()
  const fromEnv = import.meta.env?.VITE_API_BASE as string | undefined
  const base = stored || fromEnv || '/api'
  return base.endsWith('/') ? base.slice(0, -1) : base
}

const BASE = resolveBase()

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

// ---------- 设置（仅本地存储，后端不保存任何用户配置） ----------

export interface AppSettings {
  llm_base_url: string
  llm_api_key: string
  llm_model: string
  qcc_api_key: string
  tianyancha_api_key: string
  redact_by_default: boolean
}

export const DEFAULT_SETTINGS: AppSettings = {
  llm_base_url: 'https://api.deepseek.com',
  llm_api_key: '',
  llm_model: 'deepseek-chat',
  qcc_api_key: '',
  tianyancha_api_key: '',
  redact_by_default: true,
}

const SETTINGS_KEY = 'ra_settings'

export function saveSettings(settings: AppSettings): Promise<{ ok: boolean }> {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings))
  return Promise.resolve({ ok: true })
}

export function loadSettings(): AppSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY)
    if (raw) return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) }
  } catch {
    /* ignore */
  }
  return { ...DEFAULT_SETTINGS }
}

export function resetSettings(): AppSettings {
  localStorage.removeItem(SETTINGS_KEY)
  return { ...DEFAULT_SETTINGS }
}
