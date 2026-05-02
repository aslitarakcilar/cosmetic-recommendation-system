from __future__ import annotations

import pandas as pd
import numpy as np

from .data_loader import load_hybrid_data, load_products, get_user_history
from .popularity import popularity_recommend


def _min_max(series: pd.Series) -> pd.Series:
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series(0.0, index=series.index)
    return (series - lo) / (hi - lo)


def hybrid_recommend(author_id: str, category: str, top_n: int) -> tuple[pd.DataFrame, str]:
    """
    Dynamic CF-first hybrid recommendation.

    Retrieval: collaborative filtering scores (TruncatedSVD predicted scores)
    Reranking: multi-seed TF-IDF content similarity

    Beta (content weight) adapts to history depth:
      ≥20 interactions → β=0.03  (trust CF heavily)
       10–19           → β=0.07
       <10             → β=0.12  (lean more on content for sparse users)

    Returns (recommendations_df, path_label).
    Falls back to popularity when hybrid data is unavailable or user is unknown.
    """
    hybrid_data = load_hybrid_data()

    if hybrid_data is None:
        return popularity_recommend(category, top_n), "popularity"

    train_df = hybrid_data["train_df"]
    similarity_matrix = hybrid_data["similarity_matrix"]
    productid_to_index = hybrid_data["productid_to_index"]
    index_to_productid = hybrid_data["index_to_productid"]
    user_to_idx = hybrid_data["user_to_idx"]
    predicted_scores = hybrid_data["predicted_scores"]
    item_ids = hybrid_data["item_ids"]

    author_id = str(author_id)

    user_train = train_df[train_df["author_id"].astype(str) == author_id].copy()
    if user_train.empty or author_id not in user_to_idx:
        return popularity_recommend(category, top_n), "popularity"

    # Determine beta from history depth
    history_count = len(user_train)
    if history_count >= 20:
        beta, seed_count = 0.03, 2
    elif history_count >= 10:
        beta, seed_count = 0.07, 3
    else:
        beta, seed_count = 0.12, 4

    # --- CF scores ---
    user_idx = user_to_idx[author_id]
    user_cf_scores = predicted_scores[user_idx]

    already_rated = set(user_train["product_id"].astype(str))

    cf_rec = pd.DataFrame({
        "product_id": [str(x) for x in item_ids],
        "cf_score": user_cf_scores,
    })
    cf_rec = cf_rec[~cf_rec["product_id"].isin(already_rated)]

    # --- Multi-seed content scores ---
    relevant = user_train[user_train["rating"] >= 4].sort_values(
        by=["rating", "submission_time"], ascending=[False, False]
    )
    seeds = relevant["product_id"].astype(str).unique()[:seed_count]
    seeds = [s for s in seeds if s in productid_to_index]

    content_scores: dict[str, float] = {}
    for seed in seeds:
        seed_idx = productid_to_index[seed]
        for rank_idx, sim_score in enumerate(similarity_matrix[seed_idx]):
            pid = str(index_to_productid[rank_idx])
            if pid == seed or pid in already_rated:
                continue
            content_scores[pid] = content_scores.get(pid, 0.0) + float(sim_score)

    if content_scores:
        content_rec = pd.DataFrame(
            [{"product_id": pid, "content_score": s} for pid, s in content_scores.items()]
        )
    else:
        content_rec = pd.DataFrame(columns=["product_id", "content_score"])

    # --- Merge and combine ---
    hybrid_df = cf_rec.merge(content_rec, on="product_id", how="outer")
    hybrid_df["cf_score"] = hybrid_df["cf_score"].fillna(0.0)
    hybrid_df["content_score"] = hybrid_df["content_score"].fillna(0.0)

    hybrid_df["cf_norm"] = _min_max(hybrid_df["cf_score"])
    hybrid_df["content_norm"] = _min_max(hybrid_df["content_score"])
    hybrid_df["score"] = hybrid_df["cf_norm"] + beta * hybrid_df["content_norm"]

    # --- Category filter ---
    products = load_products().copy()
    products["product_id"] = products["product_id"].astype(str)
    hybrid_df = hybrid_df.merge(products, on="product_id", how="left")

    cat_lower = category.strip().lower()
    filtered = hybrid_df[
        hybrid_df["tertiary_category"].astype(str).str.strip().str.lower() == cat_lower
    ].copy()

    if filtered.empty:
        return popularity_recommend(category, top_n), "hybrid_fallback_popularity"

    filtered = filtered.sort_values("score", ascending=False).head(top_n).reset_index(drop=True)
    return filtered, "hybrid"
