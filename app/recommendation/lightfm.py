from __future__ import annotations

import numpy as np
import pandas as pd
import scipy.sparse as sp

from .data_loader import load_lightfm_data, load_products


def _build_cold_start_features(
    skin_type: str,
    skin_tone: str,
    user_feature_map: dict,
    n_features: int,
) -> sp.csr_matrix:
    """Build a (1, n_features) sparse feature row for a new user."""
    indices = []
    for token in (f"skin_type:{skin_type.lower()}", f"skin_tone:{skin_tone.lower()}"):
        if token in user_feature_map:
            indices.append(user_feature_map[token])

    if not indices:
        return None

    data = np.ones(len(indices), dtype=np.float32)
    row = np.zeros(len(indices), dtype=np.int32)
    col = np.array(indices, dtype=np.int32)
    return sp.csr_matrix((data, (row, col)), shape=(1, n_features))


def lightfm_recommend(
    author_id: str,
    category: str,
    top_n: int,
    skin_type: str | None = None,
    skin_tone: str | None = None,
) -> pd.DataFrame | None:
    """
    LightFM collaborative filtering inference.

    Works in two modes:
    - Known user (in user_to_idx): uses learned user embedding
    - New user (cold-start): builds feature vector from skin_type + skin_tone
      using the feature space learned during training
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
    user_feature_map = lightfm_data.get("user_feature_map")

    if model is None or item_ids is None:
        return None

    author_id = str(author_id)
    is_known_user = author_id in user_to_idx

    # Cold-start: build feature vector if user not in training set
    cold_start_features = None
    if not is_known_user:
        if not skin_type or not skin_tone or not user_feature_map or user_features_matrix is None:
            return None
        n_features = user_features_matrix.shape[1]
        cold_start_features = _build_cold_start_features(
            skin_type, skin_tone, user_feature_map, n_features
        )
        if cold_start_features is None:
            return None

    products = load_products().copy()
    products["product_id"] = products["product_id"].astype(str)

    cat_lower = category.strip().lower()
    category_products = products[
        products["tertiary_category"].astype(str).str.strip().str.lower() == cat_lower
    ].copy()
    if category_products.empty:
        return None

    item_ids_arr = np.array([str(item_id) for item_id in item_ids], dtype=object)
    item_to_position = {pid: idx for idx, pid in enumerate(item_ids_arr)}
    category_positions = np.array(
        [
            item_to_position[pid]
            for pid in category_products["product_id"].astype(str)
            if pid in item_to_position
        ],
        dtype=np.int32,
    )
    if category_positions.size == 0:
        return None

    if is_known_user:
        user_idx = int(user_to_idx[author_id])
        user_array = np.full(category_positions.shape, user_idx, dtype=np.int32)
        scores = model.predict(
            user_array,
            category_positions,
            item_features=item_features_matrix,
            user_features=user_features_matrix,
            num_threads=1,
        )
    else:
        # Cold-start: predict for virtual user index 0 using only features
        user_array = np.zeros(category_positions.shape, dtype=np.int32)
        # Stack cold_start_features to match number of items
        n_items = len(category_positions)
        stacked_features = sp.vstack([cold_start_features] * n_items)
        scores = model.predict(
            user_array,
            category_positions,
            item_features=item_features_matrix,
            user_features=stacked_features,
            num_threads=1,
        )

    seen_items = {str(pid) for pid in seen_items_by_user.get(author_id, [])}
    ranking = np.argsort(-scores)
    ranked_ids = [
        pid
        for pid in item_ids_arr[category_positions[ranking]]
        if pid not in seen_items
    ]
    if not ranked_ids:
        return None

    ranked = category_products.set_index("product_id").reindex(ranked_ids).reset_index()
    score_map = {
        str(item_ids_arr[int(category_positions[int(i)])]): float(scores[int(i)])
        for i in ranking
    }
    ranked["score"] = ranked["product_id"].astype(str).map(score_map)
    return ranked.head(top_n).reset_index(drop=True)
