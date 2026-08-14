"""核心分析流水线：解析 → 脱敏 → LLM 职业画像 → 搜索 → LLM 深度蒸馏 → 结构化 JSON。

PRD 要求（PRD #7）：
- 所有分析结果真实来自模型推理与搜索数据，不得使用模拟数据。
- 未配置搜索时跳过搜索步骤，LLM 仅基于内部知识，并标注「非实时」。
- LLM 使用 OpenAI 兼容 API，配置由前端传入（Base URL / Key / 模型），温度 0.3，输出 JSON。
"""
import json
import logging
from pathlib import Path
from typing import Optional

from openai import OpenAI

from . import parser, redactor
from .search_client import search

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是资深职业规划师 + 企业背景调查分析师。基于简历和搜索数据，输出包含职业画像、"
    "推荐公司（含风险等级和投递渠道）、简历优化建议的结构化结果。"
    "要求信息准确，不得编造；风险信息需附来源 URL；如数据不足，明确标注「未知」。"
)

PORTRAIT_PROMPT = (
    "根据以下简历文本（已脱敏），生成职业画像。\n"
    '输出 JSON：{"target_role":"目标岗位(含方向细分，如 数据分析师-偏业务方向)",'
    '"skills":["技能标签"],"years_experience":"经验年限","education":"学历推断",'
    '"city":"期望城市(可为空)"}\n'
    "简历文本：\n__RESUME_TEXT__"
)

ANALYZE_PROMPT = (
    "你是资深职业规划师 + 企业背景调查分析师。基于简历画像与搜索结果，输出求职方案。\n"
    "请严格输出如下 JSON 结构：\n"
    '{\n'
    '  "portrait": {"target_role":"...","skills":[...],"years_experience":"...","education":"...","city":"..."},\n'
    '  "companies": [{"name":"公司名","city":"城市","industry":"行业","risk_level":"normal|caution|high|unknown",'
    '"risk_label":"🟢 正常 / 🟡 需注意 / 🔴 高风险 / ⚪ 未知","recommend_reason":"推荐理由",'
    '"channels":[{"name":"渠道名","url":"链接"}],"risk_items":[{"type":"风险类型","description":"说明","source_url":"来源URL"}]}],\n'
    '  "star_advice": [{"quote":"简历原文","problem":"问题","situation":"S","task":"T","action":"A","result":"R",'
    '"rewrite":"优化示例"}]\n'
    '}\n'
    "约束：\n"
    "- 只能基于简历与搜索结果，不得编造公司、风险或渠道信息；\n"
    "- 风险结论必须附来源 URL；数据不足标注「未知」，禁止编造；\n"
    "- 推荐 3~8 家公司；\n"
    "- 简历优化建议基于原文，使用 STAR 法则，不得凭空添加经历。\n"
    "简历画像：\n__PORTRAIT__\n"
    "搜索结果（可能为空）：\n__SEARCH__\n"
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
    """完整分析流水线，返回结构化结果 dict。"""
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

    # 3) 搜索（可选）
    search_text = ""
    realtime = False
    if search_provider and search_api_key:
        queries = [
            f"{target_role} 招聘 公司 {city}".strip(),
            f"{target_role} 招聘 公司",
        ]
        collected: list[str] = []
        for q in queries:
            if not q:
                continue
            collected.extend(search(search_provider, search_api_key, q))
        # 风险与渠道查询（仅当已有目标公司名时）
        companies_found = [c.get("name") for c in portrait.get("companies") or []]
        for name in companies_found[:3]:
            collected.extend(search(search_provider, search_api_key, f"{name} 劳动仲裁 欠薪 失信"))
            collected.extend(search(search_provider, search_api_key, f"{name} 官网 招聘 投递渠道"))
        search_text = "\n".join(collected[:30])[:8000]
        realtime = bool(collected)
        logger.info("search done: %d snippets, realtime=%s", len(collected), realtime)

    # 4) 第二次 LLM 调用：深度蒸馏输出结构化 JSON
    result = _chat_json(llm_base_url, llm_api_key, llm_model, [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": ANALYZE_PROMPT
            .replace("__PORTRAIT__", json.dumps(portrait, ensure_ascii=False))
            .replace("__SEARCH__", search_text or "（未配置搜索或搜索无结果）")
            .replace("__RESUME__", redacted[:6000])},
    ])

    result["realtime"] = realtime
    result["notice"] = (
        ""
        if realtime
        else "当前未配置搜索 API，信息基于模型内部知识，可能滞后"
    )
    return result
