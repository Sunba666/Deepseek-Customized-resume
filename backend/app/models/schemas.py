"""Pydantic 数据模型：简历、画像、公司、风险、方案等请求/响应结构。

遵循 CONTEXT.md 术语表：Resume / Portrait / Plan / Company / RiskCheck / MatchScore / STARAdvice。
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field

# ---------- 风险 ----------

RiskLevel = Literal["normal", "caution", "high", "unknown"]


class RiskItem(BaseModel):
    """单条风险，必须附证据来源。"""
    type: str = Field(description="风险类型，如 劳动仲裁 / 欠薪 / 经营异常")
    level: RiskLevel
    description: str = ""
    source_url: str = ""
    source_name: str = ""
    fetched_at: str = Field(default="", description="数据获取时间 YYYY-MM-DD")


class RiskCheck(BaseModel):
    """一家公司的风险核验结果。"""
    level: RiskLevel
    label: str = Field(description="中文标签：🟢 正常 / 🟡 需注意 / 🔴 高风险 / ⚪ 未知")
    summary: str = ""
    items: list[RiskItem] = []
    is_mock: bool = False
    data_time: str = ""


# ---------- 公司 ----------

class Channel(BaseModel):
    name: str = ""
    url: str = ""
    note: str = ""


class Company(BaseModel):
    name: str
    city: str = ""
    industry: str = ""
    size: str = ""
    channels: list[Channel] = []
    risk: Optional[RiskCheck] = None
    match_score: int = Field(default=0, ge=0, le=100)
    match_reasons: list[str] = []
    recommend_reason: str = ""
    is_mock: bool = False


# ---------- 简历与画像 ----------

class ResumeParseResult(BaseModel):
    filename: str
    text: str
    redacted_text: str
    preview: dict = Field(default_factory=dict, description="基本信息预览：姓名/电话/邮箱/教育/工作年限")


class Portrait(BaseModel):
    target_role: str = Field(description="目标岗位，含方向细分，如 数据分析师-偏业务方向")
    skills: list[str] = []
    years_experience: str = ""
    industries: list[str] = []
    city: str = ""
    summary: str = ""
    from_llm: bool = False


# ---------- STAR 优化 ----------

class StarSuggestion(BaseModel):
    quote: str = Field(description="简历原文引用")
    problem: str = Field(description="缺少的要素说明")
    situation: str = ""
    task: str = ""
    action: str = ""
    result: str = ""
    rewrite: str = Field(description="完整改写示例，含可量化数据")


# ---------- 方案 ----------

class Plan(BaseModel):
    portrait: Portrait
    companies: list[Company]
    star_advice: list[StarSuggestion] = []
    generated_at: str = ""
    llm_used: bool = False
    mock_notice: str = ""


# ---------- 请求体 ----------

class PortraitRequest(BaseModel):
    text: str = ""
    redacted_text: str = ""
    target_role: str = ""
    city: str = ""


class RecommendRequest(BaseModel):
    portrait: Portrait
    city: str = ""
    with_star: bool = False
    resume_text: str = Field(default="", description="脱敏后的简历文本，开启 STAR 优化时必传")
