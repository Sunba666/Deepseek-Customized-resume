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
            "portrait": {
                "target_role": "数据分析师-偏业务方向",
                "skills": ["Python", "SQL"],
                "years_experience": "2 年",
                "education": "本科",
                "city": "北京",
            },
            "companies": [{
                "name": "测试数据科技",
                "city": "北京",
                "industry": "互联网",
                "risk_level": "normal",
                "risk_label": "🟢 正常",
                "recommend_reason": "匹配岗位",
                "channels": [{"name": "官网", "url": "https://example.com"}],
                "risk_items": [],
            }],
            "star_advice": [{
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
    assert body["portrait"]["target_role"] == "数据分析师-偏业务方向"
    assert len(body["companies"]) == 1
    assert len(body["star_advice"]) == 1


def test_analyze_with_search_realtime(monkeypatch):
    monkeypatch.setattr(analyzer, "search", lambda provider, key, query, max_results=5: ["某公司 招聘信息 [https://x.com]"])
    r = _post({
        "llm_api_key": "sk-test",
        "search_provider": "serper",
        "search_api_key": "sk-serper",
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["realtime"] is True
    assert body["notice"] == ""


def test_analyze_rejects_bad_ext():
    r = client.post(
        "/api/analyze",
        data={"llm_api_key": "sk-test"},
        files={"file": ("evil.exe", io.BytesIO(b"MZ"), "application/octet-stream")},
    )
    assert r.status_code == 400
