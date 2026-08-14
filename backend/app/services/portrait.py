"""职业画像生成：规则版 + LLM 版。

规则版：正则 + 关键词推断目标岗位、技能标签、经验年限；LLM 版：OpenAI 兼容接口深挖。
用户始终可手动修正结果（前端确认步骤）。
"""
import json
import logging
import re

from ..models.schemas import Portrait
from . import llm_client

logger = logging.getLogger(__name__)

# 岗位关键词库：方向 -> 关键词列表（按优先级匹配）
_ROLE_KEYWORDS: list[tuple[str, list[str]]] = [
    ("数据分析师-偏业务方向", ["数据分析", "数据运营", "业务分析", "sql", "excel", "数据指标"]),
    ("数据分析师-偏技术方向", ["python", "pandas", "数据挖掘", "机器学习", "特征工程", "etl"]),
    ("后端开发工程师", ["java", "spring", "django", "flask", "后端", "微服务", "golang", "go语言", "接口开发"]),
    ("前端开发工程师", ["react", "vue", "typescript", "前端", "html", "css", "小程序"]),
    ("算法工程师", ["算法", "深度学习", "pytorch", "tensorflow", "nlp", "推荐系统", "强化学习"]),
    ("产品经理", ["产品", "prd", "需求分析", "用户调研", "竞品分析", "roadmap"]),
    ("运营专员", ["运营", "用户增长", "活动策划", "内容运营", "社群", "转化率"]),
    ("测试工程师", ["测试", "自动化测试", "selenium", "pytest", "接口测试", "性能测试"]),
    ("运维工程师", ["运维", "docker", "kubernetes", "k8s", "ci/cd", "linux"]),
    ("UI/UX 设计师", ["ui", "ux", "figma", "sketch", "交互设计", "视觉设计"]),
    ("人力资源专员", ["人力资源", "招聘", "hr", "绩效", "薪酬", "员工关系"]),
    ("市场专员", ["市场营销", "品牌", "广告", "投放", "seo", "sem"]),
    ("财务专员", ["会计", "财务", "记账", "报表", "审计", "税务"]),
    ("销售代表", ["销售", "客户", "商务", "业绩", "to b", "to c"]),
    ("行政专员", ["行政", "办公", "后勤", "固定资产"]),
]

_SKILL_KEYWORDS: list[tuple[str, list[str]]] = [
    ("Python", ["python"]), ("Java", ["java"]), ("Go", ["golang", "go语言", " go "]),
    ("SQL", ["sql"]), ("JavaScript", ["javascript", "js"]), ("TypeScript", ["typescript"]),
    ("React", ["react"]), ("Vue", ["vue"]), ("Node.js", ["node"]), ("C++", ["c++", "cpp"]),
    ("机器学习", ["机器学习", "深度学习", "pytorch", "tensorflow", "sklearn", "scikit"]),
    ("数据分析", ["数据分析", "pandas", "numpy", "excel", "tableau", "power bi"]),
    ("Docker/K8s", ["docker", "kubernetes", "k8s"]), ("Linux", ["linux"]),
    ("云计算", ["aws", "阿里云", "腾讯云", "华为云", "云原生"]),
    ("产品设计", ["prd", "axure", "原型", "流程图", "交互设计"]),
    ("项目管理", ["项目管理", "敏捷", "scrum", "pmp"]),
    ("英语", ["英语", "cet-4", "cet-6", "ielts", "toefl", "六级", "四级"]),
]

_INDUSTRY_KEYWORDS: list[tuple[str, list[str]]] = [
    ("互联网", ["互联网", "软件", "科技", "电商", "saas", "app"]),
    ("金融", ["金融", "银行", "证券", "保险", "支付", "基金"]),
    ("人工智能", ["人工智能", "ai", "大模型", "智能"]),
    ("游戏", ["游戏", "游戏开发", "unity", "ue4"]),
    ("教育", ["教育", "培训", "在线教育", "教研"]),
    ("制造", ["制造", "工业", "汽车", "硬件", "电子"]),
    ("医疗", ["医疗", "医药", "健康", "生物"]),
    ("咨询", ["咨询", "战略", "市场研究"]),
]

_YEAR_RE = re.compile(r"(?:(\d+)\s*[年]|(?:工作经验|从业|工作)\s*[:：]?\s*(\d+)\s*[年+]?)|(?:(\d{4})\s*[-—~至]\s*(\d{4}))")


def infer_portrait(text: str, target_role: str = "", city: str = "") -> Portrait:
    """规则版画像：从简历文本推断岗位/技能/年限/行业。"""
    lowered = text.lower()
    role = target_role or _match_role(lowered)
    skills = _match_skills(lowered)
    years = _match_years(text)
    industries = _match_industries(lowered)
    summary = f"根据简历推断，您的目标岗位方向为「{role}」，"
    if years:
        summary += f"经验约 {years}，"
    summary += f"核心技能：{'、'.join(skills[:6]) or '待补充'}。"

    return Portrait(
        target_role=role,
        skills=skills,
        years_experience=years,
        industries=industries,
        city=city,
        summary=summary,
        from_llm=False,
    )


def _match_role(lowered: str) -> str:
    best, best_score = "通用岗位", 0
    for role, kws in _ROLE_KEYWORDS:
        score = sum(1 for k in kws if k in lowered)
        if score > best_score:
            best, best_score = role, score
    return best


def _match_skills(lowered: str) -> list[str]:
    found = []
    for name, kws in _SKILL_KEYWORDS:
        if any(k in lowered for k in kws):
            found.append(name)
    return found


def _match_years(text: str) -> str:
    m = _YEAR_RE.search(text)
    if not m:
        return ""
    if m.group(1) or m.group(2):
        y = m.group(1) or m.group(2)
        return f"{y} 年"
    if m.group(3) and m.group(4):
        return f"{int(m.group(4)) - int(m.group(3))} 年"
    return ""


def _match_industries(lowered: str) -> list[str]:
    found = []
    for name, kws in _INDUSTRY_KEYWORDS:
        if any(k in lowered for k in kws):
            found.append(name)
    return found


def generate_portrait(text: str, target_role: str = "", city: str = "") -> Portrait:
    """LLM 版画像；未配置 Key 或失败时回退规则版。"""
    if not llm_client.llm_enabled():
        return infer_portrait(text, target_role, city)
    try:
        prompt = (
            "根据以下简历文本，生成职业画像。\n"
            "输出 JSON：{\"target_role\":\"岗位(含方向细分，如 数据分析师-偏业务方向)\","
            "\"skills\":[\"技能标签\"],\"years_experience\":\"经验年限\","
            "\"industries\":[\"行业\"],\"city\":\"城市\",\"summary\":\"一句话摘要\"}\n"
            f"用户目标岗位(可能为空): {target_role or '自动推断'}\n"
            f"期望城市(可能为空): {city or '未知'}\n"
            f"简历文本:\n{text[:6000]}"
        )
        data = llm_client.chat_json([
            {"role": "system", "content": llm_client.system_prompt()},
            {"role": "user", "content": prompt},
        ])
        portrait = Portrait(
            target_role=data.get("target_role") or target_role or "通用岗位",
            skills=data.get("skills") or [],
            years_experience=str(data.get("years_experience") or ""),
            industries=data.get("industries") or [],
            city=data.get("city") or city,
            summary=data.get("summary") or "",
            from_llm=True,
        )
        return portrait
    except Exception as e:
        logger.warning("LLM portrait failed, fallback to rule engine: %s", e)
        return infer_portrait(text, target_role, city)
