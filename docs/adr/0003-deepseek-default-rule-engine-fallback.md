# ADR-0003: LLM 默认 DeepSeek + 规则引擎兜底

- 状态：已接受
- 日期：2026-08-14

## 背景

PRD 要求 LLM 调用走 OpenAI 兼容 API（支持自定义 Base URL，如 Ollama、DeepSeek），同时「未填 Key 时使用内置规则引擎完成基础岗位画像和风险摘要」。本机无任何预置 LLM Key。

## 决策

- 设置页提供 OpenAI 兼容配置：Base URL + API Key + 模型名，**默认预填 DeepSeek**（`https://api.deepseek.com`，用户改 Key 即可用）。
- 无 Key / 调用失败时，**规则引擎兜底**：正则 + 关键词 + 模板，本地生成岗位画像、匹配度、STAR 建议与风险摘要。规则版输出可正常使用但文本较生硬。
- LLM 只做「摘要/解释/优化建议」，**不做风险判定**——风险等级一律由结构化数据源指标计算，LLM 仅解释。

## 后果

- 优点：离线完全可用；符合「本地优先」；换模型零代码改动。
- 代价：规则引擎需要维护关键词/模板库，覆盖面不如 LLM；LLM 输出需严格约束 JSON 结构与「禁止编造」。
- 所有 LLM 调用在代码中标注 `provider=openai-compatible`，模型名、温度等可在 `.env` 调整。
