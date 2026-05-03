from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..dependencies import get_admin_user
from ..schemas.analytics import OfflineEvaluationResponse, RecommendationMetricsResponse
from ..services.offline_evaluation_service import load_offline_evaluation
from ..services.recommendation_tracking_service import build_recommendation_metrics
from ..user_model import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/recommendation-metrics", response_model=RecommendationMetricsResponse)
def recommendation_metrics(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> RecommendationMetricsResponse:
    _ = current_user
    return build_recommendation_metrics(db)


@router.get("/offline-model-evaluation", response_model=OfflineEvaluationResponse)
def offline_model_evaluation(
    current_user: User = Depends(get_admin_user),
) -> OfflineEvaluationResponse:
    _ = current_user
    return load_offline_evaluation()
