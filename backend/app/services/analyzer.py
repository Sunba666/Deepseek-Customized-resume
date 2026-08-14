"""核心分析流水线：解析 → 脱敏 → LLM 职业画像 → 搜索 → LLM 筛选与风险评估 → 结构化 JSON。

PRD 要求（PRD #9）：
- 搜索 API 返回的所有原始内容（标题、链接、摘要、正文）只能作为 LLM 输入素材，
  绝不能直接出现在最终 API 响应中（禁止 search_results_raw / snippets / organic_results 等字段）。
- LLM 必须执行「公司筛选与风险评估」：从搜索结果识别真实公司 → 正规性判断
  （劳动仲裁/欠薪/失信/经营异常等）→ 剔除高风险或信息严重不足的公司 → 只输出通过筛选的公司。
- 未配置搜索时，LLM 基于自身知识生成真实公司，同样进行自我判断，并标注「信息可能滞后」。
- LLM 使用 OpenAI 兼容 API，配置由前端传入（Base URL / Key / 模型），温度 0.3，输出 JSON。
"""
import json
import logging
import re
from pathlib import Path
from typing import Optional

from openai import OpenAI

from . import parser, redactor
from .search_client import search

logger = logging.getLogger(__name__)

# PRD #9 强化版系统提示词
SYSTEM_PROMPT = (
    "你是一名资深职业规划师和企业背景调查分析师。你会收到简历解析结果、职业画像、"
    "以及一段来自搜索引擎的原始文本（可能包含公司信息、风险记录、招聘信息）。\n"
    "你的任务是从这段文本中提取、筛选、分析并输出推荐公司。你必须：\n"
    "- 只推荐真实存在且你判断为正规的公司；\n"
    "- 如果文本中包含该公司的风险信息，必须提及并给出来源链接；\n"
    "- 如果文本信息不足，你可以基于自身知识补充，但需标注「未知」；\n"
    "- 不得输出搜索原文，只输出结构化结果；\n"
    "- 不得编造公司或风险信息。"
)

PORTRAIT_PROMPT = (
    "根据以下简历文本（已脱敏），生成职业画像。\n"
    '输出 JSON：{"target_role":"目标岗位(含方向细分，如 数据分析师-偏业务方向)",'
    '"skills":["技能标签"],"years_experience":"经验年限","education":"学历推断",'
    '"city":"期望城市(可为空)"}\n'
    "简历文本：\n__RESUME_TEXT__"
)

ANALYZE_PROMPT = (
    "你是资深职业规划师 + 企业背景调查分析师。基于简历画像与搜索原始文本，执行【公司筛选与风险评估】并输出求职方案。\n"
    "请严格输出如下 JSON 结构：\n"
    '{\n'
    '  "career_profile": {"target_role":"...","skills":[...],"years_experience":"...","education":"...","city":"..."},\n'
    '  "recommended_companies": [{"name":"公司名","city":"城市","industry":"行业",'
    '"risk_level":"normal|caution|high|unknown","risk_label":"🟢 正常 / 🟡 需注意 / 🔴 高风险 / ⚪ 未知",'
    '"recommendation_reason":"推荐理由(LLM生成)",'
    '"channels":[{"name":"渠道名","url":"链接"}],'
    '"risk_details":[{"description":"风险说明","source_url":"证据链接(仅当有依据时)"}],'
    '"note":"补充说明，如 信息基于搜索结果，建议人工核实"}],\n'
    '  "resume_advice": [{"quote":"简历原文","problem":"问题","situation":"S","task":"T","action":"A","result":"R",'
    '"rewrite":"优化示例"}]\n'
    '}\n'
    "必须执行的公司筛选与风险评估流程：\n"
    "1. 从搜索原始文本中识别出【真实存在】的公司名称（严禁虚构、严禁从任何预置列表读取）；\n"
    "2. 对每家公司做正规性判断：结合搜索到的风险信息（劳动仲裁、欠薪、失信、经营异常等），"
    "判断该公司是否正规、是否值得推荐；\n"
    "3. 剔除明显高风险或信息严重不足的公司；\n"
    "4. 只输出【通过筛选】的公司，推荐 5~15 家；每家公司必须给出：推荐理由、风险等级、"
    "风险说明及证据链接（来自搜索结果的 URL）、投递渠道（官网、邮箱、招聘平台等）；\n"
    "5. 若搜索原始文本为空（未配置搜索）：基于自身知识生成真实公司，同样进行自我判断，"
    "只推荐你判断正规、可信的公司，并在 note 中标注「信息可能滞后，建议人工核实」；\n"
    "6. 简历优化建议基于原文，使用 STAR 法则，不得凭空添加经历。\n"
    "硬性约束：\n"
    "- 【不得】在输出中包含任何搜索原始文本、标题、摘要或片段，只输出结构化提炼结果；\n"
    "- 【不得】编造公司、风险或渠道信息；风险说明无证据时 risk_details 留空、risk_level 标 unknown；\n"
    "- 风险等级只允许 normal / caution / high / unknown 四种。\n"
    "简历画像：\n__PORTRAIT__\n"
    "搜索原始文本（仅作为素材，可能为空）：\n__SEARCH__\n"
    "简历文本（已脱敏）：\n__RESUME__"
)


class AnalyzeError(Exception):
    """分析过程中的可预期错误（向前端返回明确信息）。"""


def _chat_json(base_url: str, api_key: str, model: str, messages: list[dict]) -> dict:
    """按请求配置调用 OpenAI 兼容 API，要求 JSON 输出。"""
    client = OpenAI(base_url=base_url, api_key=api_key, timeout=90)
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content or "{}"
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.warning("LLM 返回非 JSON: %s", content[:200])
        raise AnalyzeError("LLM 返回内容无法解析为 JSON，请重试或更换模型") from e


def analyze_resume(
    file_path: Path,
    llm_base_url: str,
    llm_api_key: str,
    llm_model: str,
    search_provider: str = "",
    search_api_key: str = "",
) -> dict:
    """完整分析流水线，返回结构化结果 dict。

    返回结构（PRD #9）：{career_profile, recommended_companies, resume_advice, realtime, notice}
    绝不含任何搜索原始字段。
    """
    if not llm_api_key:
        raise AnalyzeError("请先在设置中配置 LLM API Key")

    # 1) 解析 + 脱敏
    try:
        text = parser.extract_text(file_path)
    except ValueError as e:
        raise AnalyzeError(str(e)) from e
    redacted = redactor.redact(text)

    # 2) 第一次 LLM 调用：职业画像
    portrait = _chat_json(llm_base_url, llm_api_key, llm_model, [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": PORTRAIT_PROMPT.replace("__RESUME_TEXT__", redacted[:6000])},
    ])
    target_role = portrait.get("target_role") or ""
    city = portrait.get("city") or ""

    # 3) 搜索（可选）：原始结果只收集为 LLM 素材，绝不外泄
    search_text = ""
    realtime = False
    if search_provider and search_api_key:
        collected: list[str] = []
        base_queries = [
            f"{target_role} 招聘 公司 {city}".strip() or f"{target_role} 招聘 公司",
            f"{city} {target_role} 知名公司".strip() or f"{target_role} 招聘 公司",
        ]
        for q in base_queries:
            collected.extend(search(search_provider, search_api_key, q))

        # 从招聘搜索结果中提取候选公司名，追加风险/渠道查询
        candidates = _extract_company_names("\n".join(collected))
        logger.info("extracted %d candidate companies from search", len(candidates))
        for name in candidates[:5]:
            collected.extend(search(search_provider, search_api_key, f"{name} 劳动仲裁 欠薪 失信"))
            collected.extend(search(search_provider, search_api_key, f"{name} 官网 招聘 投递渠道"))

        search_text = "\n".join(collected[:40])[:10000]
        realtime = bool(collected)
        logger.info("search done: %d snippets, realtime=%s", len(collected), realtime)

    # 4) 第二次 LLM 调用：公司筛选与风险评估，输出结构化 JSON（素材不外泄）
    result = _chat_json(llm_base_url, llm_api_key, llm_model, [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": ANALYZE_PROMPT
            .replace("__PORTRAIT__", json.dumps(portrait, ensure_ascii=False))
            .replace("__SEARCH__", search_text or "（未配置搜索，无搜索素材）")
            .replace("__RESUME__", redacted[:6000])},
    ])

    # 5) 归一化：确保关键字段存在；剥离任何可能残留的原始搜索字段
    result["career_profile"] = result.get("career_profile") or portrait
    result["recommended_companies"] = result.get("recommended_companies") or []
    result["resume_advice"] = result.get("resume_advice") or []
    for key in ("search_results_raw", "snippets", "organic_results", "search_text", "raw_search"):
        result.pop(key, None)
    result["realtime"] = realtime
    result["notice"] = (
        ""
        if realtime
        else "当前未配置搜索 API，信息基于模型内部知识，可能滞后，投递渠道等信息建议人工核实"
    )
    # 防御：LLM 若在文本字段里复读搜索片段（含 URL 的原始摘要），截断为结构化摘要
    if search_text:
        _scrub_search_echo(result, search_text)
    return result


def _scrub_search_echo(result: dict, search_text: str) -> None:
    """防御性清洗：若 LLM 把搜索原始片段复制进输出文本字段，替换为结构化说明。

    PRD #9：前端展示的任何内容必须是 LLM 生成的结构化内容，不得是搜索结果的复制粘贴。
    """
    # 收集原始片段中较长的行（>40 字符），用于检测复制粘贴
    raw_lines = [ln.strip() for ln in search_text.splitlines() if len(ln.strip()) > 40]
    if not raw_lines:
        return
    for comp in result.get("recommended_companies") or []:
        for field in ("recommendation_reason", "note"):
            val = comp.get(field) or ""
            if any(rl and rl in val for rl in raw_lines):
                # 直接替换为结构化说明，绝不保留原始搜索文本
                comp[field] = "（原始搜索文本已按隐私策略移除，建议通过官方渠道人工核实）"


# 公司名提取：懒惰前缀 + 收尾后缀（只保留能作为公司名结尾的尾缀，
# 避免「网络科技/科技集团」等组合把 XX有限公司 拦腰截断）
_COMPANY_RE = re.compile(
    r"([\u4e00-\u9fa5A-Za-z0-9]{2,24}?"
    r"(?:有限责任公司|股份有限公司|有限公司|集团|股份))"
)

# 明显非公司名的噪音词
_NOISE = ("招聘", "招人", "欢迎", "科技公司招聘", "公司招聘")


def _extract_company_names(text: str) -> list[str]:
    """从文本中提取去重后的候选公司名（去重保序，剔除常见噪音词）。"""
    names: list[str] = []
    seen: set[str] = set()
    for m in _COMPANY_RE.finditer(text):
        name = m.group(1).strip()
        if len(name) < 4 or name in seen:
            continue
        if any(n in name for n in _NOISE):
            continue
        seen.add(name)
        names.append(name)
    return names
