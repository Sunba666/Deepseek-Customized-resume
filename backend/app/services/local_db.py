"""公司本地库适配：复用 Company-lookup 的 SQLite 数据库。

- 读取 company_data.db 的 companies / company_cache 表。
- 未配置 COMPANY_DB_PATH 或读取失败时返回空列表，由调用方回退 mock。
- 本模块不修改任何外部数据，只读。
"""
import json
import logging
import sqlite3
from datetime import date
from pathlib import Path
from typing import Optional

from ..config import get_settings

logger = logging.getLogger(__name__)


def _db_path() -> Optional[Path]:
    raw = get_settings().company_db_path.strip()
    if not raw:
        return None
    p = Path(raw)
    return p if p.exists() else None


def list_companies(limit: int = 200) -> list[dict]:
    """列出本地库中的公司（名称/别名/城市/行业，若可得）。"""
    db = _db_path()
    if not db:
        return []
    try:
        con = sqlite3.connect(str(db), timeout=5)
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT id, name, aliases FROM companies ORDER BY id LIMIT ?", (limit,)
        ).fetchall()
        con.close()
        return [dict(r) for r in rows]
    except sqlite3.Error as e:
        logger.warning("local company db read failed: %s", e)
        return []


def get_company_risk(name: str) -> Optional[dict]:
    """按公司名查本地库风险缓存（company_cache.data_json）。

    返回结构：{level, items, summary, data_time, is_mock} 或 None。
    """
    db = _db_path()
    if not db:
        return None
    try:
        con = sqlite3.connect(str(db), timeout=5)
        row = con.execute(
            "SELECT c.data_json FROM company_cache c "
            "JOIN companies cp ON cp.id = c.company_id "
            "WHERE cp.name = ? OR cp.aliases LIKE ? "
            "ORDER BY c.fetched_at DESC LIMIT 1",
            (name, f"%{name}%"),
        ).fetchone()
        con.close()
        if not row:
            return None
        data = json.loads(row[0])
        return _adapt_cache(data)
    except (sqlite3.Error, json.JSONDecodeError) as e:
        logger.warning("risk cache read failed for %s: %s", name, e)
        return None


def _adapt_cache(data: dict) -> dict:
    """把 Company-lookup 缓存结构转成 resume-advisor 的风险结构。"""
    raw = data.get("raw_data") or {}
    ai = data.get("ai_result") or {}
    report = ai.get("report")

    items = []
    # tavily/wenshu/salary 三类来源
    if raw.get("wenshu"):
        items.append({
            "type": "司法涉诉记录",
            "level": "caution",
            "description": "裁判文书网存在相关涉诉记录，建议人工核实具体案情",
            "source_url": "https://wenshu.court.gov.cn/",
            "source_name": "中国裁判文书网",
            "fetched_at": date.today().isoformat(),
        })
    if raw.get("salary"):
        items.append({
            "type": "薪资争议相关",
            "level": "caution",
            "description": "存在薪资相关公开讨论，建议核实",
            "source_url": "",
            "source_name": "公开网络信息",
            "fetched_at": date.today().isoformat(),
        })
    # report 可能是 markdown 文本或 dict（含 risk_items）
    if isinstance(report, dict) and report.get("risk_items"):
        for it in report["risk_items"][:6]:
            items.append({
                "type": it.get("type", "其他"),
                "level": it.get("level", "unknown"),
                "description": it.get("description", ""),
                "source_url": it.get("source_url", ""),
                "source_name": it.get("source_name", ""),
                "fetched_at": it.get("fetched_at", date.today().isoformat()),
            })

    has_risk = any(it["level"] in ("high", "caution") for it in items)
    level = "high" if any(it["level"] == "high" for it in items) else (
        "caution" if has_risk else "normal")
    label = {"high": "🔴 高风险", "caution": "🟡 需注意", "normal": "🟢 正常"}.get(level, "⚪ 未知")

    # report 为文本时截取摘要，dict 时取 summary 字段
    if isinstance(report, str) and report.strip():
        summary = report.strip().splitlines()[0][:120]
    elif isinstance(report, dict) and report.get("summary"):
        summary = report["summary"]
    else:
        summary = (f"本地信用库查到 {len(items)} 条风险线索" if items else "本地信用库暂未发现明显风险")

    return {
        "level": level,
        "label": label,
        "summary": summary,
        "items": items,
        "data_time": ai.get("analysis_time") or data.get("fetched_at") or date.today().isoformat(),
        "is_mock": False,
    }
