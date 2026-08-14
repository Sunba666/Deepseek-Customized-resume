# resume-advisor · 定制化求职方案生成器

一个**本地优先**的桌面求职辅助软件：上传简历 → 分析职业画像 → 推荐公司 + 风险核验 + 投递渠道 → 导出求职方案。

> ⚠️ 隐私承诺：简历解析、分析、报告生成默认**全部在本地完成**，不上传任何服务器；导出文件自动脱敏。
> 仅当你自行填写 LLM API Key 时，才会调用你指定的 OpenAI 兼容接口（默认 DeepSeek，可换 Ollama 等）。

## 功能

- 📄 **简历解析**：支持 PDF / DOCX / TXT，本地文本提取 + 隐私脱敏（手机号/邮箱/身份证/住址）
- 🎯 **职业画像**：推断目标岗位（含方向细分）、技能标签、经验年限，支持手动修正
- 🏢 **公司推荐**：根据画像与城市推荐 10~20 家公司，含投递渠道
- 🛡 **风险核验**：🟢/🟡/🔴 风险等级 + 证据来源链接 + 数据获取时间；数据不足标注「未知」，禁止编造
- 📊 **岗位匹配度**：技能 / 经验 / 学历 / 薪资四维评分
- ✍️ **STAR 优化建议**（可选开关，默认关闭）：针对经历类内容给出 S/T/A/R 改写示例
- 📤 **报告导出**：Markdown 一键下载，或浏览器打印另存为 PDF，默认脱敏

## 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | React 18 + TypeScript + Tailwind CSS（Vite） |
| 后端 | Python 3.11+ + FastAPI（本机 3.14 已验证） |
| 桌面壳 | Tauri 2.0（预留骨架，见 ADR-0001） |
| 解析 | pypdf / python-docx / python-pptx |
| LLM | OpenAI 兼容格式，默认 DeepSeek，无 Key 时规则引擎兜底 |
| 数据 | 复用 Company-lookup 本地库 + 内置模拟数据回退 |

## 快速开始（开发模式）

### 1. 启动后端

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt     # Windows
# source .venv/bin/pip install -r requirements.txt  # macOS/Linux
python run.py        # 监听 http://127.0.0.1:8000
```

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173（/api 自动代理到后端）
```

浏览器打开 http://localhost:5173 即可使用。

### 3. 配置 LLM（可选）

设置页填入 Base URL / API Key / 模型名，或复制 `backend/.env.example` 为 `backend/.env` 填写：

```ini
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=sk-xxx
LLM_MODEL=deepseek-chat
```

**不填 Key 也能用**：内置规则引擎完成岗位画像、匹配度、STAR 建议与风险摘要（文本较生硬）。

### 4. 公司本地库（可选）

在 `backend/.env` 中配置：

```ini
COMPANY_DB_PATH=E:\自己制作的项目\Company-lookup\company_data.db
```

未配置时使用内置模拟数据（界面明确标注「模拟」）。

## 生产模式（单端口）

```bash
cd frontend && npm run build     # 产物输出到 frontend/dist
cd ../backend && .venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

后端会自动托管前端静态文件，浏览器访问 http://127.0.0.1:8000 即可。

## 构建桌面安装包（最后阶段，需 Rust）

1. 安装 [Rust](https://rustup.rs/) + MSVC 构建工具
2. `cd src-tauri && cargo tauri build`（首次编译较慢）

## 项目结构

```
resume-advisor/
├── frontend/          # React 前端（3 个页面 + 4 个组件）
├── backend/           # FastAPI 后端（路由 / 服务 / 模型 / 工具）
│   ├── app/
│   │   ├── routers/   # resume / analysis / companies / export
│   │   ├── services/  # parser / redactor / portrait / risk_checker / matcher / star_optimizer / llm_client / recommender / local_db / exporter
│   │   ├── models/    # Pydantic 数据模型
│   │   └── utils/     # file_handler 临时存储
│   ├── requirements.txt
│   └── .env.example
├── src-tauri/         # Tauri 2.0 桌面壳（预留）
├── docs/adr/          # 架构决策记录
└── CONTEXT.md         # 领域术语表
```

## API 一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/resume/parse` | 上传简历（multipart），返回脱敏文本与预览 |
| POST | `/api/analysis/portrait` | 生成职业画像（LLM 或规则引擎） |
| POST | `/api/companies/recommend` | 生成方案：公司推荐 + 风险核验 + 匹配度 + STAR |
| POST | `/api/analysis/star` | 单独生成 STAR 优化建议 |
| POST | `/api/export/markdown` | 导出脱敏 Markdown 报告 |
| GET | `/api/health` | 服务健康 / LLM 配置状态 |

## 模拟数据说明

- **公司**：内置 12 家虚构公司（名称/城市/行业/渠道均为演示数据），未接入真实数据源时使用
- **风险**：模拟风险条目（经营异常/行政处罚/劳动仲裁等）带「模拟数据」标注，证据链接指向官方公示系统入口
- **本地库**：配置 `COMPANY_DB_PATH` 后优先读真实本地企业库（不含在仓库中）
- 所有模拟数据均可在界面与导出报告中明确识别（「模拟」标签 / 标注）

## 常见问题

- **PDF 解析不出文本？** 扫描件/图片型 PDF 暂不支持 OCR，请使用文字版 PDF。
- **后端 8000 端口被占用？** 修改 `backend/.env` 的 `PORT`。
- **想换 Ollama？** 设置页 Base URL 填 `http://127.0.0.1:11434/v1`，模型名填已下载的模型（如 `qwen2.5:7b`）。
- **控制台出现 `v[w] is not a function` / VM 前缀报错？** 本应用源码不使用 `onload` 且 dev 模式不压缩，此类带压缩变量名（`v[w]`）的报错来自**第三方注入脚本**（常见名称：`aegisInject`、`SideBar`、`yuke`），多为浏览器扩展或 DNS 层广告劫持注入，与应用无关。排查与隔离：
  1. 无痕窗口（禁用全部扩展）打开 http://localhost:5173，若报错消失即为扩展注入；逐个禁用扩展定位元凶并卸载。
  2. 若报错仍存在，检查浏览器代理/网络设置是否有 DNS 层注入，用杀毒软件（如火绒）全盘扫描。
  3. 代码侧已内置隔离：生产构建自动注入 CSP 元标签，拦截 DOM 注入的内联脚本（`yuke` 等）；扩展 content script 运行于隔离世界，不受页面 CSP 约束，仍需浏览器侧处理。
- **控制台有 React Router `future` 警告？** 已消除：`main.tsx` 中 `HashRouter` 已设置 `future={{ v7_startTransition: true, v7_relativeSplatPath: true }}`。
- **控制台有 Permissions-Policy 提示？** 多为浏览器对未声明功能特性的提示，可忽略；Vite 配置已显式关闭本应用不需要的权限（摄像头/麦克风/定位等），正常不再出现。

## 开源协议

MIT License
