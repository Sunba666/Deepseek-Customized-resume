"""LLM 调用封装：OpenAI 兼容 API（支持自定义 Base URL）。

- 默认 DeepSeek；可指向 Ollama 等任意 OpenAI 兼容端点。
- 未配置 Key 时 llm_enabled=False，调用方应回退规则引擎。
- 统一走 chat.completions，约束 JSON 输出，超时/失败抛异常由调用方兜底。
"""
import json
import logging
from typing import Optional

from ..config import get_settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "你是一位资深职业规划师 + 企业背景调查分析师 + 招聘信息分析师。\n"
    "你会收到三部分信息：简历解析结果、用户确认的目标岗位/城市、公司风险数据 JSON。\n"
    "请输出结构化结果（JSON 格式），包含：岗位画像、推荐公司列表（含风险等级、推荐理由、投递渠道）、"
    "简历优化建议（如果用户开启）。\n"
    "约束：\n"
    "- 只能使用提供的数据，不得编造公司或风险信息；\n"
    "- 每条风险结论必须附来源 URL；\n"
    "- 数据不足时标注\"未知\"，不要猜测；\n"
    "- 不推荐明显高风险公司；\n"
    "- 对用户隐私信息进行脱敏处理；\n"
    "- 简历优化建议必须基于原文，使用 STAR 法则，并给出可量化的改写示例；\n"
    "- 如不确定，明确说\"建议人工核实\"。"
)


def system_prompt() -> str:
    """软件内嵌系统提示词，供 LLM 调用使用。"""
    return _SYSTEM_PROMPT


def llm_enabled() -> bool:
    return get_settings().llm_enabled


def chat_json(messages: list[dict], temperature: Optional[float] = None) -> dict:
    """调用 OpenAI 兼容接口，要求返回 JSON 对象。失败抛异常。"""
    from openai import OpenAI

    s = get_settings()
    client = OpenAI(base_url=s.llm_base_url, api_key=s.llm_api_key, timeout=60)
    resp = client.chat.completions.create(
        model=s.llm_model,
        messages=messages,
        temperature=s.llm_temperature if temperature is None else temperature,
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content or "{}"
    # 兼容偶发的 markdown 代码块包裹
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:]
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.warning("llm returned non-json: %s", e)
        raise ValueError("LLM 返回内容无法解析为 JSON") from e


def complete_text(prompt: str, temperature: Optional[float] = None) -> str:
    """普通文本补全（如 STAR 建议，不需要严格 JSON）。"""
    from openai import OpenAI

    s = get_settings()
    client = OpenAI(base_url=s.llm_base_url, api_key=s.llm_api_key, timeout=60)
    resp = client.chat.completions.create(
        model=s.llm_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=s.llm_temperature if temperature is None else temperature,
    )
    return resp.choices[0].message.content or ""
