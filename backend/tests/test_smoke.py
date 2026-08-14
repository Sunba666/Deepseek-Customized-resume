"""端到端冒烟测试：覆盖解析/脱敏/画像/推荐/导出核心链路（无 LLM Key，规则引擎模式）。"""
import io

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE_RESUME = """张三
电话：13812345678  邮箱：zhangsan@example.com
身份证号：110101199001011234
地址：北京市朝阳区建国路88号SOHO现代城A座1201室

教育背景
北京大学 计算机科学与技术 本科 2018-2022

工作经历
2022-2024 某互联网公司 数据分析师
负责用户增长数据分析，使用 SQL 和 Python 处理千万级数据，输出业务报表
参与搭建数据看板，提升报表产出效率

项目经历
2023 用户流失预测项目
负责特征工程与模型训练，使用机器学习方法预测用户流失，准确率提升15%
"""


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["llm_enabled"] is False


def test_parse_resume():
    r = client.post("/api/resume/parse", files={
        "file": ("resume.txt", io.BytesIO(SAMPLE_RESUME.encode("utf-8")), "text/plain"),
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert "138****5678" in body["redacted_text"]       # 手机号脱敏
    assert "[邮箱已隐藏]" in body["redacted_text"]       # 邮箱脱敏
    assert "身份证号" not in body["redacted_text"] or "********" in body["redacted_text"]
    assert body["preview"]["inferred_role"]              # 推断出岗位


def test_parse_rejects_bad_ext():
    r = client.post("/api/resume/parse", files={
        "file": ("evil.exe", io.BytesIO(b"MZ"), "application/octet-stream"),
    })
    assert r.status_code == 400


def test_portrait_rule_engine():
    r = client.post("/api/analysis/portrait", json={
        "text": SAMPLE_RESUME,
        "target_role": "数据分析师-偏业务方向",
        "city": "北京",
    })
    assert r.status_code == 200
    p = r.json()
    assert p["target_role"]
    assert p["from_llm"] is False


def test_recommend_plan():
    portrait = {
        "target_role": "数据分析师-偏业务方向",
        "skills": ["Python", "SQL", "机器学习", "数据分析"],
        "years_experience": "2 年",
        "industries": ["互联网"],
        "city": "北京",
        "summary": "测试画像",
        "from_llm": False,
    }
    r = client.post("/api/companies/recommend", json={
        "portrait": portrait,
        "city": "北京",
        "with_star": True,
        "resume_text": SAMPLE_RESUME,
    })
    assert r.status_code == 200, r.text
    plan = r.json()
    assert 10 <= len(plan["companies"]) <= 20
    for c in plan["companies"]:
        assert c["risk"] is not None
        assert 0 <= c["match_score"] <= 100
    assert plan["star_advice"]  # 开启 STAR 后有建议


def test_export_markdown():
    portrait = {
        "target_role": "数据分析师", "skills": ["SQL"], "years_experience": "",
        "industries": ["互联网"], "city": "", "summary": "", "from_llm": False,
    }
    plan = {
        "portrait": portrait,
        "companies": [{
            "name": "测试公司", "city": "北京", "industry": "互联网", "size": "100人",
            "channels": [{"name": "官网", "url": "https://example.com", "note": ""}],
            "risk": {
                "level": "caution", "label": "🟡 需注意", "summary": "模拟",
                "items": [{"type": "经营异常", "level": "caution", "description": "模拟",
                           "source_url": "https://www.gsxt.gov.cn/", "source_name": "公示系统",
                           "fetched_at": "2026-08-14"}],
                "is_mock": True, "data_time": "2026-08-14",
            },
            "match_score": 80, "match_reasons": ["技能匹配"], "recommend_reason": "", "is_mock": True,
        }],
        "star_advice": [],
        "generated_at": "2026-08-14 10:00", "llm_used": False, "mock_notice": "模拟",
    }
    r = client.post("/api/export/markdown", json={"plan": plan, "redacted": True})
    assert r.status_code == 200
    md = r.json()["markdown"]
    assert "# 定制化求职方案" in md
    assert "测试公司" in md
    assert "风险等级" in md
