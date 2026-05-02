from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RateRequest(BaseModel):
    product_id: str
    rating: int = Field(..., ge=1, le=5)


class RateResponse(BaseModel):
    product_id: str
    rating: int
    created_at: datetime

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
