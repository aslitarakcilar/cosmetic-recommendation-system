from __future__ import annotations

import numpy as np
import pandas as pd

from .data_loader import load_lightfm_data, load_products


def lightfm_recommend(author_id: str, category: str, top_n: int) -> pd.DataFrame | None:
    """
    Pure LightFM collaborative filtering inference.

    Requires a serialized artifact bundle at app/models/lightfm_data.pkl
    containing:
      - model
      - user_to_idx
      - item_ids
      - user_features_matrix (optional)
      - item_features_matrix (optional)
    """
    lightfm_data = load_lightfm_data()
    if lightfm_data is None:
        return None

    model = lightfm_data.get("model")
    user_to_idx = lightfm_data.get("user_to_idx") or {}
    item_ids = lightfm_data.get("item_ids")
    user_features_matrix = lightfm_data.get("user_features_matrix")
    item_features_matrix = lightfm_data.get("item_features_matrix")
    seen_items_by_user = lightfm_data.get("seen_items_by_user") or {}

    author_id = str(author_id)
    if model is None or item_ids is None or author_id not in user_to_idx:
        return None

    products = load_products().copy()
    products["product_id"] = products["product_id"].astype(str)

    cat_lower = category.strip().lower()
    category_products = products[
        products["tertiary_category"].astype(str).str.strip().str.lower() == cat_lower
    ].copy()
    if category_products.empty:
        return None

    item_ids = np.array([str(item_id) for item_id in item_ids], dtype=object)
    item_to_position = {product_id: idx for idx, product_id in enumerate(item_ids)}
    category_positions = np.array(
        [
            item_to_position[product_id]
            for product_id in category_products["product_id"].astype(str)
            if product_id in item_to_position
        ],
        dtype=np.int32,
    )
    if category_positions.size == 0:
        return None

    user_idx = int(user_to_idx[author_id])
    user_array = np.full(category_positions.shape, user_idx, dtype=np.int32)
    scores = model.predict(
        user_array,
        category_positions,
        item_features=item_features_matrix,
        user_features=user_features_matrix,
        num_threads=1,
    )

    seen_items = {str(product_id) for product_id in seen_items_by_user.get(author_id, [])}
    ranking = np.argsort(-scores)
    ranked_ids = [
        product_id
        for product_id in item_ids[category_positions[ranking]]
        if product_id not in seen_items
    ]
    if not ranked_ids:
        return None

    ranked = category_products.set_index("product_id").reindex(ranked_ids).reset_index()
    score_map = {
        str(item_ids[int(category_positions[int(local_idx)])]): float(scores[int(local_idx)])
        for local_idx in ranking
    }
    ranked["score"] = ranked["product_id"].astype(str).map(score_map)
    return ranked.head(top_n).reset_index(drop=True)
