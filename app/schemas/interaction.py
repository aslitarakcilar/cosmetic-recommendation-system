from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RateRequest(BaseModel):
    product_id: str
    rating: int = Field(..., ge=1, le=5)
    recommendation_event_id: int | None = Field(default=None, ge=1)


class RateResponse(BaseModel):
    product_id: str
    rating: int
    created_at: datetime
    recommendation_event_id: int | None = None
    recommended_rank: int | None = None
    attributed_within_window: bool = False

    model_config = {"from_attributes": True}


class RatedProductDetail(BaseModel):
    product_id: str
    rating: int
    rated_at: datetime
    product_name: str
    brand_name: str
    tertiary_category: str
    price_usd: float | None


class InteractionSummary(BaseModel):
    total_ratings: int
    recommendation_path: str
    path_explanation: str
