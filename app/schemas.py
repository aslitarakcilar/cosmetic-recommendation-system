

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    """/recommend endpoint'ine gelecek istek gövdesi."""

    user_id: Optional[str] = Field(default=None)
    skin_type: Optional[str] = Field(default=None)
    skin_tone: Optional[str] = Field(default=None)
    category: str = Field(..., min_length=1)
    top_n: int = Field(default=10, ge=1, le=50)


class RecommendationItem(BaseModel):
    """Tek bir öneri ürününü temsil eder."""

    product_id: str
    product_name: str
    brand_name: str
    primary_category: str
    secondary_category: str
    tertiary_category: str
    price_usd: Optional[float] = None
    score: Optional[float] = None


class RecommendationResponse(BaseModel):
    """/recommend endpoint'inin döndüreceği cevap modeli."""

    model_used: Literal["hybrid", "profile", "popularity"]
    total_recommendations: int
    recommendations: list[RecommendationItem]


class HealthResponse(BaseModel):
    """Basit health check cevabı."""

    status: str
    message: str


class CategoriesResponse(BaseModel):
    """Kategori listesini döndürmek için cevap modeli."""

    categories: list[str]