from __future__ import annotations

from pydantic import BaseModel, Field


class RecommendationClickRequest(BaseModel):
    recommendation_event_id: int = Field(..., ge=1)
    product_id: str = Field(..., min_length=1)


class RecommendationClickResponse(BaseModel):
    logged: bool


class ModelPerformanceMetric(BaseModel):
    model_used: str
    recommendation_events: int
    impressions: int
    clicks: int
    ctr: float | None
    attributed_ratings: int
    rating_conversion: float | None
    positive_rating_rate: float | None
    average_attributed_rating: float | None


class RankPerformanceMetric(BaseModel):
    rank: int
    impressions: int
    clicks: int
    ctr: float | None
    attributed_ratings: int
    rating_conversion: float | None
    average_attributed_rating: float | None


class RecommendationMetricsResponse(BaseModel):
    attribution_window_hours: int
    total_recommendation_events: int
    total_impressions: int
    total_clicks: int
    total_attributed_ratings: int
    overall_ctr: float | None
    overall_rating_conversion: float | None
    overall_positive_rating_rate: float | None
    average_attributed_rating: float | None
    model_metrics: list[ModelPerformanceMetric]
    rank_metrics: list[RankPerformanceMetric]


class OfflineModelEvaluationRow(BaseModel):
    model: str
    precision_at_10: float
    hit_rate_at_10: float
    ndcg_at_10: float
    auc: float
    coverage: float
    user_coverage: float
    diversity: float
    evaluated_rows: int


class MetricLeader(BaseModel):
    metric: str
    model: str
    value: float


class OfflineEvaluationResponse(BaseModel):
    source_file: str
    rows: list[OfflineModelEvaluationRow]
    leaders: list[MetricLeader]
