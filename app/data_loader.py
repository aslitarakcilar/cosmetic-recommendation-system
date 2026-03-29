from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


# -------------------------------------------------------------------
# REQUEST MODELLERİ
# -------------------------------------------------------------------

class RecommendationRequest(BaseModel):
    """
    /recommend endpoint'ine gelecek istek gövdesi.

    user_id:
        Kullanıcı daha önce sistemde etkileşim üretmişse gönderilir.
        Böylece backend hibrit / collaborative mantığı kullanabilir.

    skin_type, skin_tone:
        Yeni kullanıcılar veya profile-based fallback için kullanılır.

    category:
        Kullanıcının ürün istediği kategori.

    top_n:
        Kaç öneri dönüleceği.
    """

    user_id: Optional[str] = Field(
        default=None,
        description="Opsiyonel kullanıcı kimliği"
    )
    skin_type: Optional[str] = Field(
        default=None,
        description="Kullanıcının cilt tipi"
    )
    skin_tone: Optional[str] = Field(
        default=None,
        description="Kullanıcının cilt tonu"
    )
    category: str = Field(
        ...,
        min_length=1,
        description="Öneri istenen ürün kategorisi"
    )
    top_n: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Döndürülecek öneri sayısı"
    )


# -------------------------------------------------------------------
# RESPONSE MODELLERİ
# -------------------------------------------------------------------

class RecommendationItem(BaseModel):
    """
    Tek bir öneri ürününü temsil eder.
    """

    product_id: str
    product_name: str
    brand_name: str
    primary_category: str
    secondary_category: str
    tertiary_category: str
    price_usd: Optional[float] = None
    score: Optional[float] = None


class RecommendationResponse(BaseModel):
    """
    /recommend endpoint'inin döndüreceği ana response modeli.
    """

    model_used: Literal["hybrid", "profile", "popularity"]
    total_recommendations: int
    recommendations: list[RecommendationItem]


class HealthResponse(BaseModel):
    """
    Basit health check cevabı.
    """

    status: str
    message: str


class CategoriesResponse(BaseModel):
    """
    Kategori listesini döndürmek için response modeli.
    """

    categories: list[str]