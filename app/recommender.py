from __future__ import annotations

from typing import List

import pandas as pd

from .data_loader import (
    load_products,
    user_has_history,
)
from .schemas import RecommendationItem


# ------------------------------------------------------------------
# BASİT POPULARITY MODEL (MVP)
# ------------------------------------------------------------------

def _popularity_recommendation(category: str, top_n: int) -> pd.DataFrame:
    """
    Basit popularity-based öneri.
    Şu an için ürünleri rating değerine göre sıralıyoruz.
    """

    products = load_products().copy()

    # Kategori filtreleme
    if "tertiary_category" in products.columns:
        products = products[
            products["tertiary_category"].astype(str).str.lower() == category.lower()
        ]

    # Eğer filtre sonrası hiç ürün kalmadıysa tüm ürünlerde fallback yap
    if products.empty:
        products = load_products().copy()

    # Rating varsa ona göre sırala
    if "rating" in products.columns:
        products = products.sort_values("rating", ascending=False)
    else:
        # Son çare fallback
        products = products.sort_values("product_id")

    return products.head(top_n)


# ------------------------------------------------------------------
# PROFILE-BASED (ŞU AN BASİT VERSİYON)
# ------------------------------------------------------------------

def _profile_recommendation(category: str, top_n: int) -> pd.DataFrame:
    """
    Şimdilik profile-based = kategori + popularity mantığı ile çalışıyor.

    İleride:
    - skin_type
    - skin_tone
    - undertone
    gibi alanlar burada aktif şekilde kullanılacak.
    """

    return _popularity_recommendation(category, top_n)


# ------------------------------------------------------------------
# HYBRID (ŞU AN PLACEHOLDER)
# ------------------------------------------------------------------

def _hybrid_recommendation(user_id: str, category: str, top_n: int) -> pd.DataFrame:
    """
    Şimdilik MVP için hybrid yerine popularity kullanıyoruz.

    İleride notebook'ta geliştirdiğimiz gerçek hybrid model
    bu fonksiyon içine bağlanacak.
    """

    return _popularity_recommendation(category, top_n)


# ------------------------------------------------------------------
# ANA PIPELINE
# ------------------------------------------------------------------

def get_recommendations(
    user_id: str | None,
    category: str,
    top_n: int,
) -> tuple[str, List[RecommendationItem]]:
    """
    Final recommendation decision logic.

    Kullanıcı geçmişi varsa:
        hybrid
    Kullanıcı geçmişi yoksa ama kategori varsa:
        profile
    Aksi durumda:
        popularity

    Returns
    -------
    tuple[str, List[RecommendationItem]]
        model_used, recommendation list
    """

    # --------------------------------------------------------------
    # MODEL SEÇİMİ
    # --------------------------------------------------------------

    if user_id and user_has_history(user_id):
        df = _hybrid_recommendation(user_id, category, top_n)
        model_used = "hybrid"

    elif category:
        df = _profile_recommendation(category, top_n)
        model_used = "profile"

    else:
        df = _popularity_recommendation(category, top_n)
        model_used = "popularity"

    # --------------------------------------------------------------
    # RESPONSE FORMAT
    # --------------------------------------------------------------

    items: List[RecommendationItem] = []

    for _, row in df.iterrows():
        items.append(
            RecommendationItem(
                product_id=str(row.get("product_id", "")),
                product_name=str(row.get("product_name", "unknown")),
                brand_name=str(row.get("brand_name", "unknown")),
                primary_category=str(row.get("primary_category", "unknown")),
                secondary_category=str(row.get("secondary_category", "unknown")),
                tertiary_category=str(row.get("tertiary_category", "unknown")),
                price_usd=row.get("price_usd"),
                score=None,
            )
        )

    return model_used, items