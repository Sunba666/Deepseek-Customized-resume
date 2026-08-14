"""岗位画像、匹配度、STAR 优化接口：POST /api/analysis/..."""
import logging

from fastapi import APIRouter

from ..models.schemas import Portrait, PortraitRequest, StarSuggestion
from ..services import portrait as portrait_svc
from ..services import star_optimizer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/portrait", response_model=Portrait)
def generate_portrait(req: PortraitRequest):
    """生成职业画像。LLM 可用时深度生成，否则规则引擎。"""
    return portrait_svc.generate_portrait(
        text=req.text or req.redacted_text,
        target_role=req.target_role,
        city=req.city,
    )


@router.post("/star", response_model=list[StarSuggestion])
def star_advice(req: PortraitRequest):
    """STAR 法则简历优化建议（需用户开启）。"""
    if not (req.text or req.redacted_text):
        return []
    return star_optimizer.generate_star_advice(
        text=req.text or req.redacted_text,
        target_role=req.target_role,
    )
