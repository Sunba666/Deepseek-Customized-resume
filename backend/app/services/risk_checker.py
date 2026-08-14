"""风险核验：结构化风险指标聚合 + 等级判定 + 模拟数据回退。

遵循 CONTEXT.md：
- 风险等级不得由 AI 凭空判断，必须基于数据源指标；数据不足标注「未知」。
- 每条风险附证据来源链接 + 数据获取时间。
- 无真实数据源 Key 时使用模拟数据，并明确标注 is_mock=True。
"""
import logging
from datetime import date
from typing import Optional

from ..models.schemas import RiskCheck, RiskItem
from . import local_db

logger = logging.getLogger(__name__)

_RISK_SOURCES = [
    ("国家企业信用信息公示系统", "https://www.gsxt.gov.cn/"),
    ("中国裁判文书网", "https://wenshu.court.gov.cn/"),
    ("中国执行信息公开网", "http://zxgk.court.gov.cn/"),
    ("信用中国", "https://www.creditchina.gov.cn/"),
]

# 模拟数据模板：按行业关键词生成不同的演示风险
_MOCK_RISKS: dict[str, list[dict]] = {
    "互联网": [
        {"type": "经营异常", "level": "caution", "description": "模拟数据：该企业曾列入经营异常名录（已移出），请以官方公示为准。",
         "source_name": "国家企业信用信息公示系统", "source_url": "https://www.gsxt.gov.cn/"},
        {"type": "行政处罚", "level": "caution", "description": "模拟数据：存在 1 条行政处罚记录（广告法相关），模拟演示。",
         "source_name": "信用中国", "source_url": "https://www.creditchina.gov.cn/"},
    ],
    "金融": [
        {"type": "经营异常", "level": "caution", "description": "模拟数据：该企业曾列入经营异常名录，模拟演示。",
         "source_name": "国家企业信用信息公示系统", "source_url": "https://www.gsxt.gov.cn/"},
        {"type": "劳动仲裁", "level": "caution", "description": "模拟数据：近一年有 2 起劳动仲裁记录（模拟），建议投递前核实。",
         "source_name": "中国裁判文书网", "source_url": "https://wenshu.court.gov.cn/"},
    ],
    "游戏": [
        {"type": "劳动仲裁", "level": "caution", "description": "模拟数据：存在劳动仲裁记录（模拟），建议核实。",
         "source_name": "中国裁判文书网", "source_url": "https://wenshu.court.gov.cn/"},
    ],
}


def check_company(name: str, industry: str = "") -> RiskCheck:
    """核验单家公司风险。优先级：本地库 > 模拟数据。"""
    local = local_db.get_company_risk(name)
    if local:
        return RiskCheck(**local)

    # 模拟回退
    items = []
    key = _match_mock_key(industry)
    for tpl in _MOCK_RISKS.get(key, _MOCK_RISKS.get("互联网", [])):
        items.append(RiskItem(**tpl, fetched_at=date.today().isoformat()))

    level = "caution" if items else "normal"
    label = {"high": "🔴 高风险", "caution": "🟡 需注意", "normal": "🟢 正常", "unknown": "⚪ 未知"}[level]
    summary = "模拟数据：未接入真实企业信用数据源，风险信息为演示用途，请通过官方渠道核实。" if items else \
        "模拟数据：未发现风险（演示用途）。"
    return RiskCheck(
        level=level, label=label, summary=summary, items=items,
        is_mock=True, data_time=date.today().isoformat(),
    )


def _match_mock_key(industry: str) -> str:
    for key in _MOCK_RISKS:
        if key in industry:
            return key
    return "互联网"


def available_sources() -> list[dict]:
    return [{"name": n, "url": u} for n, u in _RISK_SOURCES]
