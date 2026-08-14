"""公司推荐：根据职业画像和城市推荐 10~20 家公司，附风险核验与匹配度。

数据优先级：本地公司库（Company-lookup）> 内置模拟公司。
所有推荐公司都跑风险核验（risk_checker）与匹配度（matcher）。
"""
import logging
from datetime import datetime
from typing import Optional

from ..models.schemas import Channel, Company, Plan, Portrait
from . import local_db, matcher, risk_checker

logger = logging.getLogger(__name__)

# 内置模拟公司：名称/城市/行业/规模/投递渠道/推荐理由（演示用，均为虚构）
_MOCK_COMPANIES: list[dict] = [
    {"name": "星云数据科技有限公司", "city": "北京", "industry": "互联网/大数据", "size": "100-499人",
     "channels": [{"name": "官网招聘页", "url": "https://www.example.com/nebula/careers", "note": "模拟渠道"},
                  {"name": "Boss直聘", "url": "https://www.example.com/jobs/nebula", "note": "模拟渠道"}],
     "recommend_reason": "模拟数据：大数据方向，与数据分析岗匹配"},
    {"name": "云帆网络科技", "city": "上海", "industry": "互联网", "size": "500-999人",
     "channels": [{"name": "官网招聘页", "url": "https://www.example.com/yunfan/careers", "note": "模拟渠道"}],
     "recommend_reason": "模拟数据：电商/增长方向，运营与数据分析岗位多"},
    {"name": "深蓝人工智能实验室", "city": "深圳", "industry": "人工智能", "size": "50-99人",
     "channels": [{"name": "拉勾网", "url": "https://www.example.com/jobs/shenlan", "note": "模拟渠道"}],
     "recommend_reason": "模拟数据：AI 研发方向"},
    {"name": "山海教育科技", "city": "杭州", "industry": "教育/互联网", "size": "1000人以上",
     "channels": [{"name": "官网招聘页", "url": "https://www.example.com/shanhai/careers", "note": "模拟渠道"}],
     "recommend_reason": "模拟数据：在线教育，产品与内容运营岗位多"},
    {"name": "极光互娱", "city": "广州", "industry": "游戏", "size": "100-499人",
     "channels": [{"name": "官网招聘页", "url": "https://www.example.com/jiguang/careers", "note": "模拟渠道"}],
     "recommend_reason": "模拟数据：游戏研发与发行"},
    {"name": "磐石金融科技", "city": "北京", "industry": "金融/科技", "size": "500-999人",
     "channels": [{"name": "官网招聘页", "url": "https://www.example.com/panshi/careers", "note": "模拟渠道"}],
     "recommend_reason": "模拟数据：金融科技，风控/数据岗多"},
    {"name": "青柠文化传媒", "city": "成都", "industry": "文化传媒", "size": "50-99人",
     "channels": [{"name": "拉勾网", "url": "https://www.example.com/jobs/qingning", "note": "模拟渠道"}],
     "recommend_reason": "模拟数据：内容运营与市场方向"},
    {"name": "微澜智能硬件", "city": "武汉", "industry": "制造/智能硬件", "size": "100-499人",
     "channels": [{"name": "官网招聘页", "url": "https://www.example.com/weilan/careers", "note": "模拟渠道"}],
     "recommend_reason": "模拟数据：智能硬件研发"},
    {"name": "白泽云服务", "city": "南京", "industry": "互联网/云计算", "size": "500-999人",
     "channels": [{"name": "官网招聘页", "url": "https://www.example.com/baize/careers", "note": "模拟渠道"}],
     "recommend_reason": "模拟数据：云计算/后端方向"},
    {"name": "半夏医疗器械", "city": "苏州", "industry": "医疗/器械", "size": "100-499人",
     "channels": [{"name": "官网招聘页", "url": "https://www.example.com/banxia/careers", "note": "模拟渠道"}],
     "recommend_reason": "模拟数据：医疗信息化"},
    {"name": "初芒新能源", "city": "合肥", "industry": "新能源/制造", "size": "1000人以上",
     "channels": [{"name": "官网招聘页", "url": "https://www.example.com/chumang/careers", "note": "模拟渠道"}],
     "recommend_reason": "模拟数据：新能源行业高速发展"},
    {"name": "拾光设计工作室", "city": "上海", "industry": "设计/互联网", "size": "20-49人",
     "channels": [{"name": "站酷", "url": "https://www.example.com/jobs/shiguang", "note": "模拟渠道"}],
     "recommend_reason": "模拟数据：UI/UX 设计方向"},
]


def recommend(portrait: Portrait, city: str = "", with_star: bool = False) -> Plan:
    """生成完整求职方案。"""
    city = city or portrait.city or "不限"
    companies = _collect_companies(portrait, city)

    # 统一附风险 + 匹配度
    for comp in companies:
        comp.risk = risk_checker.check_company(comp.name, comp.industry)
        score, reasons = matcher.match_score(portrait)
        comp.match_score = score
        comp.match_reasons = reasons

    mock_used = any(c.is_mock for c in companies)
    mock_notice = "部分公司数据为模拟数据（演示用途），请通过官方渠道核实。" if mock_used else ""

    plan = Plan(
        portrait=portrait,
        companies=companies,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        llm_used=False,
        mock_notice=mock_notice,
    )
    return plan


def _collect_companies(portrait: Portrait, city: str) -> list[Company]:
    """从本地库 + mock 收集公司，按行业相关性排序，取 10~20 家。"""
    local = local_db.list_companies()
    companies: list[Company] = []
    used_names: set[str] = set()

    # 本地库公司（is_mock=False）
    for row in local:
        name = row.get("name") or ""
        if not name or name in used_names:
            continue
        used_names.add(name)
        companies.append(Company(
            name=name,
            city="",
            industry="",
            size="",
            channels=[],
            is_mock=False,
            recommend_reason="来自本地企业库",
        ))

    # mock 回退（补足到至少 10 家）
    for row in _MOCK_COMPANIES:
        if len(companies) >= 20:
            break
        if row["name"] in used_names:
            continue
        used_names.add(row["name"])
        companies.append(Company(
            name=row["name"], city=row["city"], industry=row["industry"], size=row["size"],
            channels=[Channel(**c) for c in row["channels"]],
            is_mock=True, recommend_reason=row["recommend_reason"],
        ))

    # 行业相关性排序：画像行业命中靠前；城市命中靠前
    def sort_key(c: Company):
        industry_hit = any(ind in (c.industry or "") for ind in portrait.industries) or \
                       (c.industry or "") in "".join(portrait.industries)
        city_hit = city == "不限" or city in (c.city or "")
        return (0 if industry_hit else 1, 0 if city_hit else 1, c.name)

    companies.sort(key=sort_key)
    return companies[:20]
