from __future__ import annotations

from fastapi import FastAPI

from .data_loader import get_available_categories
from .recommender import get_recommendations
from .schemas import (
    CategoriesResponse,
    HealthResponse,
    RecommendationRequest,
    RecommendationResponse,
)


# -------------------------------------------------------------------
# FASTAPI APP
# -------------------------------------------------------------------

app = FastAPI(
    title="Cosmetic Recommendation API",
    description="Kozmetik ürün öneri sistemi için backend API",
    version="1.0.0",
)


# -------------------------------------------------------------------
# HEALTH CHECK
# -------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    API çalışıyor mu kontrol etmek için basit endpoint
    """

    return HealthResponse(
        status="ok",
        message="Cosmetic Recommendation API is running"
    )


# -------------------------------------------------------------------
# KATEGORİLER
# -------------------------------------------------------------------

@app.get("/categories", response_model=CategoriesResponse)
def get_categories() -> CategoriesResponse:
    """
    Frontend tarafında kategori dropdown doldurmak için kategori listesi döner
    """

    categories = get_available_categories()

    return CategoriesResponse(categories=categories)


# -------------------------------------------------------------------
# RECOMMENDATION ENDPOINT
# -------------------------------------------------------------------

@app.post("/recommend", response_model=RecommendationResponse)
def recommend(request: RecommendationRequest) -> RecommendationResponse:
    """
    Ana öneri endpoint'i

    Kullanıcı bilgisine göre:
    - history varsa hybrid yolu
    - history yoksa profile yolu
    - fallback olarak popularity yolu
    """

    model_used, recommendations = get_recommendations(
        user_id=request.user_id,
        category=request.category,
        top_n=request.top_n,
    )

    return RecommendationResponse(
        model_used=model_used,
        total_recommendations=len(recommendations),
        recommendations=recommendations,
    )