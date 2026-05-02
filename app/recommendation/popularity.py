from __future__ import annotations

import pandas as pd

from .data_loader import load_products


def popularity_recommend(category: str, top_n: int) -> pd.DataFrame:
    """
    Popularity baseline: weighted Bayesian average within category.
    Formula: (v * R + m * C) / (v + m)  where m = prior count, C = global mean.
    """
    products = load_products().copy()

    if "tertiary_category" not in products.columns:
        return pd.DataFrame()

    cat_lower = category.strip().lower()
    mask = products["tertiary_category"].astype(str).str.strip().str.lower() == cat_lower
    filtered = products[mask].copy()

    if filtered.empty:
        return pd.DataFrame()

    if "rating" in filtered.columns and "reviews" in filtered.columns:
        R = filtered["rating"].fillna(0)
        v = filtered["reviews"].fillna(0)
        C = R.mean()
        m = 20
        filtered["popularity_score"] = (v * R + m * C) / (v + m)
        filtered = filtered.sort_values("popularity_score", ascending=False)
    elif "rating" in filtered.columns:
        filtered = filtered.sort_values("rating", ascending=False)

    return filtered.head(top_n).reset_index(drop=True)
