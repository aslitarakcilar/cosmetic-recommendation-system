from __future__ import annotations

from typing import List, Tuple

import pandas as pd

from .data_loader import (
    load_hybrid_data,
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
    Kategori bazlı sıkı filtre uygular.
    """

    products = load_products().copy()

    if "tertiary_category" in products.columns:
        filtered = products[
            products["tertiary_category"].astype(str).str.strip().str.lower() == category.strip().lower()
        ].copy()
    else:
        filtered = pd.DataFrame()

    if filtered.empty:
        return pd.DataFrame(columns=products.columns)

    if "rating" in filtered.columns:
        filtered = filtered.sort_values("rating", ascending=False)
    else:
        filtered = filtered.sort_values("product_id")

    return filtered.head(top_n)


# ------------------------------------------------------------------
# PROFILE-BASED (ŞU AN BASİT VERSİYON)
# ------------------------------------------------------------------

def _profile_recommendation(category: str, top_n: int) -> pd.DataFrame:
    """
    Şimdilik profile-based = kategori + popularity mantığı ile çalışıyor.
    """

    return _popularity_recommendation(category, top_n)


# ------------------------------------------------------------------
# HYBRID (GERÇEK MODEL)
# ------------------------------------------------------------------

def _hybrid_recommendation(user_id: str, category: str, top_n: int) -> Tuple[pd.DataFrame, str]:
    """
    Notebook'ta eğitilmiş gerçek hybrid modeli kullanır.

    Returns
    -------
    tuple[pd.DataFrame, str]
        öneri dataframe'i ve kullanılan gerçek yol etiketi
    """

    hybrid_data = load_hybrid_data()

    train_df = hybrid_data["train_df"]
    similarity_matrix = hybrid_data["similarity_matrix"]
    productid_to_index = hybrid_data["productid_to_index"]
    index_to_productid = hybrid_data["index_to_productid"]
    user_to_idx = hybrid_data["user_to_idx"]
    predicted_scores = hybrid_data["predicted_scores"]
    item_ids = hybrid_data["item_ids"]

    user_id = str(user_id)

    # --------------------------------------------------------------
    # Seed item seçimi
    # --------------------------------------------------------------
    user_train = train_df[train_df["author_id"].astype(str) == user_id].copy()

    if user_train.empty:
        return _popularity_recommendation(category, top_n), "popularity"

    user_relevant = user_train[user_train["rating"] >= 4].copy()

    if user_relevant.empty:
        return _popularity_recommendation(category, top_n), "popularity"

    user_relevant = user_relevant.sort_values(
        by=["rating", "submission_time"],
        ascending=[False, False]
    )

    seed_item = str(user_relevant.iloc[0]["product_id"])

    if seed_item not in productid_to_index:
        return _popularity_recommendation(category, top_n), "popularity"

    # --------------------------------------------------------------
    # Content tarafı
    # --------------------------------------------------------------
    seed_index = productid_to_index[seed_item]

    similarity_scores = list(enumerate(similarity_matrix[seed_index]))
    similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
    similarity_scores = similarity_scores[1:]

    train_rated_items = set(user_train["product_id"].astype(str))

    content_rows = []

    for idx, score in similarity_scores:
        product_id = str(index_to_productid[idx])

        if product_id in train_rated_items:
            continue

        content_rows.append({
            "product_id": product_id,
            "similarity_score": score
        })

        if len(content_rows) >= 50:
            break

    content_rec = pd.DataFrame(content_rows)

    # --------------------------------------------------------------
    # CF tarafı
    # --------------------------------------------------------------
    if user_id not in user_to_idx:
        return _popularity_recommendation(category, top_n), "popularity"

    user_idx = user_to_idx[user_id]
    user_scores = predicted_scores[user_idx]

    cf_rec = pd.DataFrame({
        "product_id": [str(x) for x in item_ids],
        "cf_score": user_scores
    })

    cf_rec = cf_rec[~cf_rec["product_id"].isin(train_rated_items)]
    cf_rec = cf_rec.sort_values("cf_score", ascending=False).head(50)

    # --------------------------------------------------------------
    # Hybrid birleştirme
    # --------------------------------------------------------------
    hybrid_df = content_rec.merge(
        cf_rec,
        on="product_id",
        how="outer"
    )

    if hybrid_df.empty:
        return _popularity_recommendation(category, top_n), "popularity"

    hybrid_df["similarity_score"] = hybrid_df["similarity_score"].fillna(0)
    hybrid_df["cf_score"] = hybrid_df["cf_score"].fillna(0)

    def min_max_normalize(series: pd.Series) -> pd.Series:
        min_val = series.min()
        max_val = series.max()

        if max_val == min_val:
            return pd.Series([0] * len(series), index=series.index)

        return (series - min_val) / (max_val - min_val)

    hybrid_df["content_score_norm"] = min_max_normalize(hybrid_df["similarity_score"])
    hybrid_df["cf_score_norm"] = min_max_normalize(hybrid_df["cf_score"])

    # Final alpha = 0.3
    hybrid_df["score"] = (
        0.3 * hybrid_df["content_score_norm"] +
        0.7 * hybrid_df["cf_score_norm"]
    )

    # --------------------------------------------------------------
    # Ürün bilgilerini ekle
    # --------------------------------------------------------------
    products = load_products().copy()
    products["product_id"] = products["product_id"].astype(str)

    hybrid_df = hybrid_df.merge(
        products,
        on="product_id",
        how="left"
    )

    # --------------------------------------------------------------
    # Kategori filtresi
    # --------------------------------------------------------------
    if "tertiary_category" in hybrid_df.columns:
        filtered = hybrid_df[
            hybrid_df["tertiary_category"].astype(str).str.strip().str.lower() == category.strip().lower()
        ].copy()

        # Hybrid içinde bu kategoriden ürün yoksa category-specific fallback
        if filtered.empty:
            fallback_df = _popularity_recommendation(category, top_n)
            return fallback_df, "hybrid_fallback_popularity"

        hybrid_df = filtered

    hybrid_df = hybrid_df.sort_values("score", ascending=False)

    return hybrid_df.head(top_n), "hybrid"


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
    """

    if user_id and user_has_history(user_id):
        df, model_used = _hybrid_recommendation(user_id, category, top_n)

    elif category:
        df = _profile_recommendation(category, top_n)
        model_used = "profile"

    else:
        df = _popularity_recommendation(category, top_n)
        model_used = "popularity"

    if df is None:
        df = pd.DataFrame()

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
                score=float(row["score"]) if "score" in row and pd.notna(row["score"]) else None,
            )
        )

    return model_used, items