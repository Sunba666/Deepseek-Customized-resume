"""公司推荐接口：POST /api/companies/recommend。"""
import logging

from fastapi import APIRouter

from ..models.schemas import Plan, RecommendRequest
from ..services import recommender, star_optimizer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.post("/recommend", response_model=Plan)
def recommend(req: RecommendRequest):
    """根据画像和城市生成求职方案（公司推荐 + 风险核验 + 匹配度 + 可选 STAR）。"""
    plan = recommender.recommend(req.portrait, city=req.city)
    if req.with_star and req.resume_text.strip():
        plan.star_advice = star_optimizer.generate_star_advice(
            text=req.resume_text,
            target_role=req.portrait.target_role,
        )
    return plan
