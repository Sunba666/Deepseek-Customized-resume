"""岗位匹配度计算：技能 / 经验 / 学历 / 薪资四维加权评分（0-100）。

规则引擎实现，纯本地；无 LLM 依赖。每家推荐公司给出匹配分与理由。
"""
import re
from typing import Optional

from ..models.schemas import Portrait

# 权重
W_SKILL, W_EXP, W_EDU, W_SALARY = 0.45, 0.25, 0.20, 0.10


def match_score(portrait: Portrait, resume_text: str = "", jd_keywords: Optional[list[str]] = None) -> tuple[int, list[str]]:
    """计算匹配度，返回 (分数, 理由列表)。

    resume_text: 简历文本（脱敏后）；jd_keywords: 目标岗位 JD 关键词（可为空，用画像技能代替）。
    """
    reasons: list[str] = []
    lowered = (resume_text or "").lower()
    skills = [s.lower() for s in (portrait.skills or [])]

    # 1) 技能匹配
    if jd_keywords:
        hit = sum(1 for k in jd_keywords if k.lower() in lowered)
        skill_score = min(100, int(hit / max(len(jd_keywords), 1) * 100)) if jd_keywords else 50
    else:
        hit = sum(1 for s in skills if s in lowered or s in portrait.target_role.lower())
        skill_score = min(100, int(hit / max(len(skills), 1) * 100)) if skills else 50
    if skill_score >= 70:
        reasons.append(f"技能关键词命中 {hit} 项，与目标岗位较匹配")
    elif skill_score >= 40:
        reasons.append(f"技能部分匹配（命中 {hit} 项），建议补充岗位关键词")

    # 2) 经验年限
    years = _parse_years(portrait.years_experience)
    if years is not None:
        if years >= 3:
            exp_score = 90
            reasons.append(f"经验 {years} 年，符合多数岗位 3 年以上要求")
        elif years >= 1:
            exp_score = 70
            reasons.append(f"经验 {years} 年，适合初级/中级岗位")
        else:
            exp_score = 50
            reasons.append("经验较浅，建议突出项目与实习成果")
    else:
        exp_score = 55
        reasons.append("未识别到明确经验年限，按通用标准评估")

    # 3) 学历
    edu_score = _edu_score(lowered)
    if edu_score >= 80:
        reasons.append("学历背景良好（硕士及以上或名校）")
    elif edu_score >= 60:
        reasons.append("学历满足大部分岗位要求（本科）")

    # 4) 薪资期望（如简历含期望薪资，与行业均值近似比较——此处无真实数据，按中性给分）
    salary_score = 70
    if "期望薪资" in lowered or "薪资要求" in lowered:
        salary_score = 75
        reasons.append("简历包含薪资期望，建议与岗位薪资范围核对")

    total = int(skill_score * W_SKILL + exp_score * W_EXP + edu_score * W_EDU + salary_score * W_SALARY)
    return max(0, min(100, total)), reasons


def _parse_years(expr: str) -> Optional[float]:
    if not expr:
        return None
    m = re.search(r"(\d+(?:\.\d+)?)\s*年", expr)
    return float(m.group(1)) if m else None


def _edu_score(lowered: str) -> int:
    if any(k in lowered for k in ("博士", "phd")):
        return 95
    if "硕士" in lowered or "研究生" in lowered:
        return 85
    if "本科" in lowered or "学士" in lowered or "大学" in lowered:
        return 70
    if "大专" in lowered or "专科" in lowered:
        return 55
    return 50
