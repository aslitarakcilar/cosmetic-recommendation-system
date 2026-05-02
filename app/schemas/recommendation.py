from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


RecommendationPath = Literal[
    "lightfm",
    "hybrid",
    "content_seeded",
    "profile",
    "popularity",
    "hybrid_fallback_popularity",
]


class RecommendRequest(BaseModel):
    category: str = Field(..., min_length=1)
    top_n: int = Field(default=10, ge=1, le=50)


class RecommendationItem(BaseModel):
    product_id: str
    product_name: str
    brand_name: str
    primary_category: str
    secondary_category: str
    tertiary_category: str
    price_usd: Optional[float] = None
    rating: Optional[float] = None
    score: Optional[float] = None


class RecommendResponse(BaseModel):
    model_used: RecommendationPath
    model_explanation: str
    total_recommendations: int
    recommendations: list[RecommendationItem]
