from __future__ import annotations

from typing import Optional

import pandas as pd
from sqlalchemy.orm import Session

from ..recommendation.content_seeded import content_seeded_recommend
from ..recommendation.data_loader import (
    lightfm_has_user,
    lightfm_supports_cold_start,
    to_lightfm_app_user_id,
)
from ..recommendation.lightfm import lightfm_recommend
from ..recommendation.popularity import popularity_recommend
from ..recommendation.profile import profile_recommend
from ..schemas.recommendation import RecommendationItem, RecommendationPath
from ..services.interaction_service import (
    get_top_rated_product_ids,
    get_user_interactions,
    user_has_app_history,
)

_EXPLANATIONS: dict[str, str] = {
    "lightfm": (
        "LightFM collaborative filtering modeli kullanıldı. "
        "Cilt profiline benzer kullanıcıların davranış örüntüleri temel alınarak "
        "senin için en olası ürünler sıralandı."
    ),
    "hybrid": (
        "Sephora verisetindeki geçmişin bulundu. Sistem, sana benzer kullanıcıların "
        "beğendiği ürünleri collaborative filtering ile buldu; ardından içerik "
        "benzerliğiyle yeniden sıraladı."
    ),
    "content_seeded": (
        "Puanladığın ürünler temel alınarak, benzer içerikteki ürünler önerildi. "
        "Daha fazla ürün puanladıkça öneriler kişiselleşmeye devam eder."
    ),
    "profile": (
        "Cilt tipine ve cilt tonuna göre, aynı profile sahip kullanıcıların "
        "yüksek puan verdiği ürünler önerildi. İlk ürünleri puanlamaya başladığında "
        "sistem kişisel geçmişini de kullanmaya başlayacak."
    ),
    "popularity": (
        "Bu kategoride topluluk tarafından en çok beğenilen ürünler gösteriliyor."
    ),
    "hybrid_fallback_popularity": (
        "Kişisel geçmişin bu kategoriyi henüz kapsamıyor; "
        "şimdilik en popüler ürünler gösteriliyor."
    ),
}


def _df_to_items(df: pd.DataFrame) -> list[RecommendationItem]:
    items: list[RecommendationItem] = []
    for _, row in df.iterrows():
        score = row.get("score")
        if pd.isna(score):
            score = row.get("cf_score")
        if pd.isna(score):
            score = row.get("profile_score")
        if pd.isna(score):
            score = row.get("popularity_score")
        items.append(
            RecommendationItem(
                product_id=str(row.get("product_id", "")),
                product_name=str(row.get("product_name", "unknown")),
                brand_name=str(row.get("brand_name", "unknown")),
                primary_category=str(row.get("primary_category", "unknown")),
                secondary_category=str(row.get("secondary_category", "unknown")),
                tertiary_category=str(row.get("tertiary_category", "unknown")),
                price_usd=float(row["price_usd"]) if pd.notna(row.get("price_usd")) else None,
                rating=float(row["rating"]) if pd.notna(row.get("rating")) else None,
                score=float(score) if pd.notna(score) else None,
            )
        )
    return items


def get_recommendations(
    category: str,
    top_n: int,
    user_id: int,
    skin_type: str,
    skin_tone: str,
    db: Session,
) -> tuple[RecommendationPath, str, list[RecommendationItem]]:
    """
    Recommendation routing — from strongest to weakest signal:

    1. User exists in current LightFM artifact  → LightFM CF
    2. App interaction history                  → content-seeded
    3. Skin profile + LightFM feature space     → LightFM cold-start
    4. Skin profile                             → profile-based
    5. No context                               → popularity baseline
    """
    df: pd.DataFrame | None = None

    # ── Path 1: LightFM for known artifact users ───────────────────
    current_user_id = to_lightfm_app_user_id(user_id)
    if lightfm_has_user(current_user_id):
        df = lightfm_recommend(
            current_user_id,
            category,
            top_n,
            skin_type=skin_type,
            skin_tone=skin_tone,
        )
        if df is not None and not df.empty:
            return "lightfm", _EXPLANATIONS["lightfm"], _df_to_items(df)

    # ── Path 2: App interaction history ──────────────────────────
    if user_has_app_history(db, user_id):
        already_rated = {i.product_id for i in get_user_interactions(db, user_id)}
        seeds = get_top_rated_product_ids(db, user_id, min_rating=4)
        if not seeds:
            seeds = get_top_rated_product_ids(db, user_id, min_rating=1)

        df = content_seeded_recommend(seeds, already_rated, category, top_n)
        if df is not None and not df.empty:
            return "content_seeded", _EXPLANATIONS["content_seeded"], _df_to_items(df)

    # ── Path 3: LightFM cold-start for new users with profile data ─
    if skin_type and skin_tone and lightfm_supports_cold_start():
        df = lightfm_recommend(
            current_user_id,
            category,
            top_n,
            skin_type=skin_type,
            skin_tone=skin_tone,
        )
        if df is not None and not df.empty:
            return "lightfm", _EXPLANATIONS["lightfm"], _df_to_items(df)

    # ── Path 4: Skin profile ──────────────────────────────────────
    if skin_type and skin_tone:
        df = profile_recommend(skin_type, skin_tone, category, top_n)
        if df is not None and not df.empty:
            return "profile", _EXPLANATIONS["profile"], _df_to_items(df)

    # ── Path 5: Popularity fallback ───────────────────────────────
    df = popularity_recommend(category, top_n)
    return "popularity", _EXPLANATIONS["popularity"], _df_to_items(df)
