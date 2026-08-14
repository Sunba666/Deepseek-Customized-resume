"""生成内置模拟数据（演示用途）说明脚本。

PRD 约束：仓库不包含任何真实公司数据。本脚本生成的 mock_companies.json
为虚构演示数据，可随仓库分发。
"""
import json
from pathlib import Path

MOCK = [
    {"name": "星云数据科技有限公司", "city": "北京", "industry": "互联网/大数据", "size": "100-499人",
     "channels": [{"name": "官网招聘页", "url": "https://www.example.com/nebula/careers", "note": "模拟渠道"},
                  {"name": "Boss直聘", "url": "https://www.example.com/jobs/nebula", "note": "模拟渠道"}],
     "recommend_reason": "大数据方向，与数据分析岗匹配"},
    {"name": "云帆网络科技", "city": "上海", "industry": "互联网", "size": "500-999人",
     "channels": [{"name": "官网招聘页", "url": "https://www.example.com/yunfan/careers", "note": "模拟渠道"}],
     "recommend_reason": "电商/增长方向，运营与数据分析岗位多"},
    {"name": "深蓝人工智能实验室", "city": "深圳", "industry": "人工智能", "size": "50-99人",
     "channels": [{"name": "拉勾网", "url": "https://www.example.com/jobs/shenlan", "note": "模拟渠道"}],
     "recommend_reason": "AI 研发方向"},
]


def main():
    out = Path(__file__).resolve().parent.parent / "data" / "mock_companies.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"is_mock": True, "notice": "模拟数据（演示用途）", "companies": MOCK},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"written {out}")


if __name__ == "__main__":
    main()
