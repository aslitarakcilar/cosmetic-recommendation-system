from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..dependencies import get_current_user
from ..recommendation.data_loader import get_available_categories
from ..schemas.recommendation import RecommendRequest, RecommendResponse
from ..services.recommendation_service import get_recommendations
from ..user_model import User

router = APIRouter(tags=["recommendations"])


@router.get("/categories")
def categories() -> dict:
    return {"categories": get_available_categories()}


@router.post("/recommendations", response_model=RecommendResponse)
def recommend(
    request: RecommendRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecommendResponse:
    path, explanation, items = get_recommendations(
        category=request.category,
        top_n=request.top_n,
        user_id=current_user.id,
        skin_type=current_user.skin_type,
        skin_tone=current_user.skin_tone,
        db=db,
    )
    return RecommendResponse(
        model_used=path,
        model_explanation=explanation,
        total_recommendations=len(items),
        recommendations=items,
    )
