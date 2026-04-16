from __future__ import annotations

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .data_loader import get_available_categories
from .recommender import get_recommendations
from .schemas import (
    CategoriesResponse,
    HealthResponse,
    RecommendationRequest,
    RecommendationResponse,
)

from sqlalchemy.orm import Session

from .auth import create_user, get_user_by_email
from .database import get_db
from .schemas import UserRegisterRequest, UserResponse


# -------------------------------------------------------------------
# FASTAPI APP
# -------------------------------------------------------------------

app = FastAPI(
    title="Cosmetic Recommendation API",
    description="Kozmetik ürün öneri sistemi için backend API",
    version="1.0.0",

)
# -------------------------------------------------------------------
# CORS AYARI (FRONTEND BAĞLANTISI İÇİN)
# -------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # şimdilik açık bırakıyoruz
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
# -------------------------------------------------------------------
# REGISTER
# -------------------------------------------------------------------

@app.post("/register", response_model=UserResponse)
def register_user(request: UserRegisterRequest, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, request.email)

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Bu email ile kayıtlı kullanıcı zaten var."
        )

    user = create_user(
        db=db,
        name=request.name,
        email=request.email,
        password=request.password,
        skin_type=request.skin_type,
        skin_tone=request.skin_tone,
    )

    return user