from __future__ import annotations

import numpy as np
import pandas as pd

from .data_loader import load_product_profile, load_products
from .popularity import popularity_recommend


def profile_recommend(
    skin_type: str,
    skin_tone: str,
    category: str,
    top_n: int,
) -> pd.DataFrame:
    """
    Profile-based recommendation using product_profile.csv.

    Scores each product by a dynamically weighted combination of:
      - skin_type compatibility score  (column: {skin_type}_score)
      - skin_tone compatibility score  (column: {skin_tone}_tone_score)

    Weights are proportional to sqrt(review_count) — products with more
    skin-type/tone reviews get higher confidence and dominate the blend.

    Falls back to popularity if profile data is unavailable or the category
    has no profile candidates.
    """
    profile_df = load_product_profile()

    if profile_df is None:
        return popularity_recommend(category, top_n)

    cat_lower = category.strip().lower()
    mask = profile_df["tertiary_category"].astype(str).str.strip().str.lower() == cat_lower
    category_df = profile_df[mask].copy()

    if category_df.empty:
        return popularity_recommend(category, top_n)

    skin_type_norm = skin_type.strip().lower()
    skin_tone_norm = skin_tone.strip().lower()

    type_score_col = f"{skin_type_norm}_score"
    type_count_col = f"{skin_type_norm}_count"
    tone_score_col = f"{skin_tone_norm}_tone_score"
    tone_count_col = f"{skin_tone_norm}_tone_count"

    has_type = type_score_col in category_df.columns
    has_tone = tone_score_col in category_df.columns

    if not has_type and not has_tone:
        return popularity_recommend(category, top_n)

    type_score = category_df[type_score_col].fillna(0) if has_type else pd.Series(0.0, index=category_df.index)
    type_count = category_df[type_count_col].fillna(0) if (has_type and type_count_col in category_df.columns) else pd.Series(0.0, index=category_df.index)
    tone_score = category_df[tone_score_col].fillna(0) if has_tone else pd.Series(0.0, index=category_df.index)
    tone_count = category_df[tone_count_col].fillna(0) if (has_tone and tone_count_col in category_df.columns) else pd.Series(0.0, index=category_df.index)

    # Dynamic weighting: confidence proportional to sqrt(review count)
    # Skin type gets a 70/30 prior weight advantage over skin tone
    type_strength = 0.7 * np.sqrt(type_count)
    tone_strength = 0.3 * np.sqrt(tone_count)
    total = (type_strength + tone_strength).replace(0, 1)

    w_type = type_strength / total
    w_tone = tone_strength / total

    scores = w_type * type_score + w_tone * tone_score

    ranked = pd.DataFrame(
        {"product_id": category_df["product_id"], "profile_score": scores}
    ).sort_values("profile_score", ascending=False).reset_index(drop=True)

    if ranked.empty:
        return popularity_recommend(category, top_n)

    # Join product metadata
    products = load_products().copy()
    result = ranked.merge(products, on="product_id", how="left").head(top_n)
    return result.reset_index(drop=True)
