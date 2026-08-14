"""报告导出接口：POST /api/export/markdown。

默认脱敏。前端拿到 Markdown 后提供下载/复制，PDF 走浏览器打印（ADR-0004）。
"""
import logging

from fastapi import APIRouter
from pydantic import BaseModel

from ..models.schemas import Plan
from ..services.exporter import plan_to_markdown

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/export", tags=["export"])


class ExportRequest(BaseModel):
    plan: Plan
    redacted: bool = True


class ExportResponse(BaseModel):
    markdown: str
    filename: str


@router.post("/markdown", response_model=ExportResponse)
def export_markdown(req: ExportRequest):
    md = plan_to_markdown(req.plan, redacted=req.redacted)
    filename = f"求职方案_{req.plan.generated_at.replace(':', '').replace(' ', '_')}.md"
    return ExportResponse(markdown=md, filename=filename)
