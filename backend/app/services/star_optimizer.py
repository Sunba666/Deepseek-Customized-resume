"""STAR 法则简历优化建议生成：规则版 + LLM 版。

规则版：定位经历类句子（工作/项目/实习经历行），按 STAR 四要素给改写模板。
约束（CONTEXT.md）：只对经历类内容优化；必须基于原文；不得凭空添加经历。
"""
import logging
import re

from ..models.schemas import StarSuggestion
from . import llm_client

logger = logging.getLogger(__name__)

# 经历段落常见引导词
_EXPERIENCE_MARKERS = ("工作经历", "项目经历", "实习经历", "项目经验", "工作履历", "实习经验")
# 弱句特征：无量化数字
_NUMBER_RE = re.compile(r"\d+")
# 常见弱动词（无结果的描述性开头）
_WEAK_STARTS = ("负责", "参与", "协助", "跟进", "配合", "支持", "从事", "处理")


def _split_experience_lines(text: str) -> list[str]:
    """粗略切出经历块内的行。返回候选经历句。"""
    lines = text.splitlines()
    candidates = []
    for i, line in enumerate(lines):
        line = line.strip()
        is_exp_section = any(m in line for m in _EXPERIENCE_MARKERS)
        if is_exp_section:
            # 该段落后 8 行内属于经历内容
            for sub in lines[i + 1: i + 9]:
                s = sub.strip()
                if not s or len(s) < 8:
                    continue
                if any(m in s for m in _EXPERIENCE_MARKERS) or re.match(r"^(教育|技能|证书|自我评价|项目|实习)", s):
                    break
                candidates.append(s)
    return candidates


def generate_star_advice(text: str, target_role: str = "", max_items: int = 3) -> list[StarSuggestion]:
    """生成 STAR 优化建议。LLM 可用时优先，失败/无 Key 回退规则版。"""
    if llm_client.llm_enabled():
        try:
            return _llm_star(text, target_role, max_items)
        except Exception as e:
            logger.warning("LLM STAR failed, fallback to rule engine: %s", e)
    return _rule_star(text, max_items)


def _rule_star(text: str, max_items: int) -> list[StarSuggestion]:
    suggestions: list[StarSuggestion] = []
    for line in _split_experience_lines(text):
        if len(suggestions) >= max_items:
            break
        has_number = bool(_NUMBER_RE.search(line))
        weak = any(line.startswith(w) or line.startswith(w) for w in _WEAK_STARTS)
        if has_number and not weak:
            continue  # 已有量化且非弱句，跳过
        suggestions.append(_build_rule_suggestion(line))
    return suggestions


def _build_rule_suggestion(line: str) -> StarSuggestion:
    problem_parts = []
    if not _NUMBER_RE.search(line):
        problem_parts.append("缺少量化数据（如规模、时长、百分比、金额）")
    if any(line.startswith(w) for w in _WEAK_STARTS):
        problem_parts.append("以「负责/参与」开头，未体现个人贡献与结果")

    return StarSuggestion(
        quote=line,
        problem="；".join(problem_parts) or "描述偏笼统，缺少情境与结果",
        situation="补充项目/任务发生的背景：业务场景、规模（如用户量、数据量、团队人数）。",
        task="明确您在这段经历中的具体职责与目标（量化目标，如「将转化率提升至 X%」）。",
        action="按顺序写您采取的关键行动：方法、工具、协作方式，突出您的个人角色。",
        result="用可量化结果收尾：指标前后对比（如「X → Y，提升 Z%」）、产出物、获奖/认可。",
        rewrite=_compose_rewrite(line),
    )


def _compose_rewrite(line: str) -> str:
    """基于原文生成改写示例（不添加虚构经历，只结构化重写）。"""
    content = line.strip().rstrip("。；;")
    if content.startswith(tuple(_WEAK_STARTS)):
        # 「负责 X」→ 结构化为 STAR 表述，量化处留占位提示
        return f"{content}（情境：补充项目背景与规模；行动：明确您个人负责的具体环节；结果：量化产出，如「X → Y，提升 Z%」）"
    return f"{content}（任务：明确目标；结果：补充可量化产出，如「效率提升 X% / 覆盖用户 Y 万」）"


def _llm_star(text: str, target_role: str, max_items: int) -> list[StarSuggestion]:
    prompt = (
        "你是资深简历优化师。基于以下简历原文，找出与目标岗位相关的经历类句子，"
        "对最值得优化的句子给出 STAR 法则改写建议。\n"
        f"目标岗位: {target_role or '自动推断'}\n"
        f"最多输出 {max_items} 条。\n"
        '输出 JSON: {"advice":[{"quote":"原文引用","problem":"缺少要素","situation":"S情境","task":"T任务",'
        '"action":"A行动","result":"R结果","rewrite":"完整改写示例，含可量化数据"}]}\n'
        "约束：只基于原文，不得凭空添加经历。\n"
        f"简历文本:\n{text[:6000]}"
    )
    data = llm_client.chat_json([
        {"role": "system", "content": llm_client.system_prompt()},
        {"role": "user", "content": prompt},
    ])
    items = data.get("advice") or []
    return [StarSuggestion(**it) for it in items[:max_items] if isinstance(it, dict)]
