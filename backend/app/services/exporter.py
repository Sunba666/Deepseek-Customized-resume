"""报告导出：将 Plan 渲染为 Markdown（默认脱敏）。

PDF 由前端调用浏览器打印（见 ADR-0004），后端只产出确定性 Markdown。
"""
from datetime import date

from ..models.schemas import Plan


def plan_to_markdown(plan: Plan, redacted: bool = True) -> str:
    """渲染求职方案为 Markdown 文本。"""
    lines: list[str] = []
    lines.append("# 定制化求职方案")
    lines.append("")
    lines.append(f"> 生成时间：{plan.generated_at} | 脱敏：{'是' if redacted else '否'}")
    if plan.mock_notice:
        lines.append(f"> ⚠️ {plan.mock_notice}")
    lines.append("")

    # 职业画像
    lines.append("## 一、职业画像")
    lines.append("")
    p = plan.portrait
    lines.append(f"- **目标岗位**：{p.target_role}")
    lines.append(f"- **经验**：{p.years_experience or '未知'}")
    lines.append(f"- **技能**：{'、'.join(p.skills) or '未识别'}")
    lines.append(f"- **行业**：{'、'.join(p.industries) or '未知'}")
    if p.summary:
        lines.append(f"- **摘要**：{p.summary}")
    lines.append("")

    # 推荐公司
    lines.append("## 二、推荐公司（{} 家）".format(len(plan.companies)))
    lines.append("")
    for i, c in enumerate(plan.companies, 1):
        lines.append(f"### {i}. {c.name}")
        lines.append("")
        lines.append(f"- **城市**：{c.city or '未知'} | **行业**：{c.industry or '未知'} | **规模**：{c.size or '未知'}")
        lines.append(f"- **匹配度**：{c.match_score}/100")
        if c.match_reasons:
            lines.append(f"- **匹配理由**：{'；'.join(c.match_reasons)}")
        if c.recommend_reason:
            lines.append(f"- **推荐理由**：{c.recommend_reason}")
        lines.append("")
        if c.risk:
            r = c.risk
            lines.append(f"- **风险等级**：{r.label}" + ("（模拟数据）" if r.is_mock else ""))
            lines.append(f"- **数据获取时间**：{r.data_time}")
            if r.summary:
                lines.append(f"- **风险摘要**：{r.summary}")
            if r.items:
                lines.append("- **风险详情**：")
                for it in r.items:
                    src = f"[{it.source_name}]({it.source_url})" if it.source_url else (it.source_name or "来源未知")
                    lines.append(f"  - {it.type}（{_level_label(it.level)}）：{it.description} 证据：{src}（{it.fetched_at}）")
            lines.append("")
        if c.channels:
            lines.append("- **投递渠道**：")
            for ch in c.channels:
                link = f"[{ch.name}]({ch.url})" if ch.url else ch.name
                note = f"（{ch.note}）" if ch.note else ""
                lines.append(f"  - {link}{note}")
            lines.append("")

    # STAR 建议
    if plan.star_advice:
        lines.append("## 三、简历优化建议（STAR 法则）")
        lines.append("")
        for i, s in enumerate(plan.star_advice, 1):
            lines.append(f"### {i}. 原文：{s.quote}")
            lines.append("")
            lines.append(f"**问题**：{s.problem}")
            lines.append("")
            lines.append(f"- **S（情境）**：{s.situation}")
            lines.append(f"- **T（任务）**：{s.task}")
            lines.append(f"- **A（行动）**：{s.action}")
            lines.append(f"- **R（结果）**：{s.result}")
            if s.rewrite:
                lines.append(f"- **改写示例**：{s.rewrite}")
            lines.append("")

    lines.append("---")
    lines.append(f"*本报告由 resume-advisor 本地生成，风险信息数据获取时间：{date.today().isoformat()}，请通过官方渠道人工核实。*")
    return "\n".join(lines)


def _level_label(level: str) -> str:
    return {"high": "高风险", "caution": "需注意", "normal": "正常", "unknown": "未知"}.get(level, level)
