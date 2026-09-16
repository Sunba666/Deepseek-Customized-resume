"""analyze 接口测试：mock LLM 与搜索，验证流水线行为。

- 无 LLM Key → 400 明确提示
- 正常流程 → 结构化 JSON（画像/公司/STAR/非实时标注）
- 配置搜索 → realtime=True 且无非实时提示
"""
import io
import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import analyzer

client = TestClient(app)

SAMPLE = """张三
电话：13812345678 邮箱：zhangsan@example.com
教育背景
北京大学 计算机 本科
工作经历
2022-2024 某互联网公司 数据分析师
负责用户增长数据分析，使用 SQL 和 Python 处理千万级数据
"""


@pytest.fixture(autouse=True)
def _mock_llm(monkeypatch):
    """mock _chat_json：按调用次数返回画像 / 最终结果。"""
    calls = {"n": 0}

    def fake_chat(base_url, api_key, model, messages):
        calls["n"] += 1
        if calls["n"] == 1:
            return {
                "target_role": "数据分析师-偏业务方向",
                "skills": ["Python", "SQL", "数据分析"],
                "years_experience": "2 年",
                "education": "本科",
                "city": "北京",
            }
        return {
            "career_profile": {
                "target_role": "数据分析师-偏业务方向",
                "skills": ["Python", "SQL"],
                "years_experience": "2 年",
                "education": "本科",
                "city": "北京",
            },
            "recommended_companies": [
                {
                    "name": f"真实科技{i}",
                    "city": "北京",
                    "industry": "互联网",
                    "risk_level": "normal",
                    "risk_label": "🟢 正常",
                    "recommendation_reason": f"匹配岗位 {i}",
                    "channels": [{"name": "官网", "url": f"https://example.com/{i}"}],
                    "risk_details": [],
                    "note": "信息基于搜索结果，建议人工核实",
                }
                for i in range(6)  # 6 家，处于 5~15 区间
            ],
            "resume_advice": [{
                "quote": "负责用户增长数据分析",
                "problem": "缺少量化",
                "situation": "S",
                "task": "T",
                "action": "A",
                "result": "R",
                "rewrite": "优化示例",
            }],
        }

    monkeypatch.setattr(analyzer, "_chat_json", fake_chat)
    monkeypatch.setattr(analyzer, "search", lambda *args, **kwargs: [])


def _post(extra: dict | None = None):
    return client.post(
        "/api/analyze",
        data=extra or {},
        files={"file": ("r.txt", io.BytesIO(SAMPLE.encode()), "text/plain")},
    )


def test_analyze_requires_llm_key():
    r = _post({"llm_api_key": ""})
    assert r.status_code == 400
    assert "LLM API Key" in r.json()["detail"]


def test_analyze_no_search_marks_non_realtime():
    r = _post({
        "llm_api_key": "sk-test",
        "llm_base_url": "https://api.openai.com/v1",
        "llm_model": "gpt-4o",
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["realtime"] is False
    assert "未配置搜索" in body["notice"]
    assert "建议人工核实" in body["notice"]
    assert body["career_profile"]["target_role"] == "数据分析师-偏业务方向"
    # 5~15 家公司（LLM 动态生成，非静态列表）
    assert 5 <= len(body["recommended_companies"]) <= 15
    assert len(body["resume_advice"]) == 1


def test_no_raw_search_leakage():
    """响应中不得包含任何搜索原始字段（PRD #9 硬性要求）。"""
    r = _post({
        "llm_api_key": "sk-test",
        "search_provider": "serper",
        "search_api_key": "sk-serper",
    })
    assert r.status_code == 200
    body = r.json()
    for key in ("search_results_raw", "snippets", "organic_results", "search_text", "raw_search"):
        assert key not in body, f"响应泄露了原始搜索字段 {key}"
    # 公司信息必须是结构化字段，而非原始片段
    assert "recommended_companies" in body
    first = body["recommended_companies"][0]
    for field in ("name", "recommendation_reason", "channels", "risk_details", "note"):
        assert field in first
    assert "risk_items" not in first  # 旧字段不得残留


def test_scrub_search_echo(monkeypatch):
    """防御性清洗：LLM 把搜索片段复读进 recommendation_reason 时应被截断。"""
    long_line = "这是一段非常长的搜索摘要，包含了很多关于该公司招聘和风险的具体描述信息，长度超过六十个字符以确保能被检测到。"
    monkeypatch.setattr(analyzer, "search", lambda provider, key, query, max_results=5: [long_line])

    def fake_chat(base_url, api_key, model, messages):
        return {
            "career_profile": {"target_role": "数据分析师", "skills": [], "years_experience": "",
                               "education": "", "city": ""},
            "recommended_companies": [{
                "name": "测试公司", "city": "北京", "industry": "互联网", "risk_level": "normal",
                "risk_label": "🟢 正常", "recommendation_reason": long_line,  # 复读原始片段
                "channels": [], "risk_details": [], "note": "",
            }],
            "resume_advice": [],
        }

    monkeypatch.setattr(analyzer, "_chat_json", fake_chat)
    r = _post({
        "llm_api_key": "sk-test",
        "search_provider": "serper",
        "search_api_key": "sk-serper",
    })
    assert r.status_code == 200
    body = r.json()
    reason = body["recommended_companies"][0]["recommendation_reason"]
    assert "原始搜索文本已按隐私策略移除" in reason  # 复读片段被替换
    assert long_line not in r.text  # 原始长片段不出现在任何响应中


def test_analyze_with_search_realtime(monkeypatch):
    monkeypatch.setattr(analyzer, "search", lambda provider, key, query, max_results=5: ["字节跳动有限公司 招聘 数据分析师 [https://jobs.bytedance.com]"])
    r = _post({
        "llm_api_key": "sk-test",
        "search_provider": "serper",
        "search_api_key": "sk-serper",
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["realtime"] is True
    assert body["notice"] == ""
    assert "search_text" not in body  # 即使搜索了，原始素材也不得出现在响应


def test_extract_company_names():
    text = "字节跳动有限公司 招聘数据分析师；腾讯科技（深圳）有限公司 也在招人；某某网络科技有限公司 欢迎投递"
    names = analyzer._extract_company_names(text)
    assert "字节跳动有限公司" in names
    assert "某某网络科技有限公司" in names
    # 去重
    text2 = "字节跳动有限公司 与 字节跳动有限公司 都招人"
    assert analyzer._extract_company_names(text2).count("字节跳动有限公司") == 1


def test_analyze_rejects_bad_ext():
    r = client.post(
        "/api/analyze",
        data={"llm_api_key": "sk-test"},
        files={"file": ("evil.exe", io.BytesIO(b"MZ"), "application/octet-stream")},
    )
    assert r.status_code == 400
