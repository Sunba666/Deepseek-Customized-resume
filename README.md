# Deepseek-Customized-resume · 定制化求职方案生成器

上传简历 → LLM 深度分析 → 输出职业画像、推荐公司（含风险核验）、投递渠道与 STAR 简历优化建议。

**本地优先**：数据默认留在本地；仅当你配置 Key 时，简历文本会发送给你指定的 LLM / 搜索 API 处理。

## 功能

- 📄 简历解析（PDF / DOCX / TXT）+ 隐私脱敏
- 🎯 职业画像：目标岗位、技能、经验、学历推断
- 🏢 推荐公司：LLM 筛选 + 风险评估（🟢🟡🔴）+ 投递渠道 + 证据链接
- ✍️ STAR 简历优化建议
- 🌙 深色模式（跟随系统，可手动切换）
- 🔍 可选集成 Serper.dev / Tavily 搜索获取实时信息

## 快速开始

```bash
# 后端（端口 8000）
cd backend
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python run.py

# 前端（端口 5173）
cd frontend
npm install && npm run dev
```

浏览器打开 http://localhost:5173。

## 配置

点右上角 ⚙️ 填写（保存在本地 localStorage）：

| 项 | 说明 |
| --- | --- |
| LLM API Key | OpenAI 兼容服务（OpenAI / DeepSeek / Ollama） |
| LLM Base URL | 默认 `https://api.openai.com/v1` |
| LLM 模型 | 如 `gpt-4o`、`deepseek-chat` |
| 搜索服务 / Key | 可选；不填则结果标注「非实时」 |

## 技术栈

React 18 + TypeScript + Tailwind（前端）· Python + FastAPI（后端）

## API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/analyze` | 上传简历，返回结构化分析（画像 / 公司 / 建议） |
| GET | `/api/health` | 健康检查 |

## 协议

MIT

## 上传与稳定性更新（2026-09-16）

- PDF / DOCX / TXT 单个文件上限为 10 MB，前后端均校验大小。
- 空白文件、损坏文档返回可读错误，处理失败也会清理临时文件。
- 简历解析和深度分析在线程池中运行，分析等待期间健康检查仍可响应。
- 上游异常详情不会直接返回给浏览器。

### 验证

```powershell
# 在 backend 目录运行；先按快速开始安装依赖
.venv/Scripts/python -m pytest tests -q
```

21 项测试覆盖解析、脱敏、分析、上传大小、损坏文件、临时文件清理及分析期间健康检查的并发响应。
测试中的 LLM 和搜索服务使用模拟响应，不需要真实 API Key。

在 `frontend` 目录执行 `npm run build`，完成 TypeScript 检查和生产构建。
