// 与后端 models/schemas.py 对应的 TypeScript 类型

export type RiskLevel = 'normal' | 'caution' | 'high' | 'unknown'

export interface RiskItem {
  type: string
  level: RiskLevel
  description: string
  source_url: string
  source_name: string
  fetched_at: string
}

export interface RiskCheck {
  level: RiskLevel
  label: string
  summary: string
  items: RiskItem[]
  is_mock: boolean
  data_time: string
}

export interface Channel {
  name: string
  url: string
  note: string
}

export interface Company {
  name: string
  city: string
  industry: string
  size: string
  channels: Channel[]
  risk: RiskCheck | null
  match_score: number
  match_reasons: string[]
  recommend_reason: string
  is_mock: boolean
}

export interface Portrait {
  target_role: string
  skills: string[]
  years_experience: string
  industries: string[]
  city: string
  summary: string
  from_llm: boolean
}

export interface StarSuggestion {
  quote: string
  problem: string
  situation: string
  task: string
  action: string
  result: string
  rewrite: string
}

export interface Plan {
  portrait: Portrait
  companies: Company[]
  star_advice: StarSuggestion[]
  generated_at: string
  llm_used: boolean
  mock_notice: string
}

export interface ResumeParseResult {
  filename: string
  text: string
  redacted_text: string
  preview: {
    contact: Record<string, string>
    inferred_role: string
    skills: string[]
    years_experience: string
  }
}

export interface Settings {
  llm_base_url: string
  llm_api_key: string
  llm_model: string
  llm_enabled: boolean
  risk_sources: { name: string; url: string }[]
}
