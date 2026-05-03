#!/usr/bin/env python
"""
Retrain LightFM model with skin_type + skin_tone user features.

After retraining, new app users can get LightFM recommendations
by passing their skin profile as a feature vector — no Sephora
history required.

Usage:
    python scripts/retrain_lightfm_with_features.py
"""

import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATA_INTERIM = PROJECT_ROOT / "data_interim"
OUTPUT_PATH = PROJECT_ROOT / "app" / "models" / "lightfm_data.pkl"


def main() -> None:
    print("Loading data...")
    cf_data = pd.read_csv(DATA_INTERIM / "reviews_cf_last.csv", low_memory=False)
    full_features = pd.read_csv(DATA_INTERIM / "reviews_full_features.csv", low_memory=False)

    cf_data["author_id"] = cf_data["author_id"].astype(str)
    cf_data["product_id"] = cf_data["product_id"].astype(str)
    full_features["author_id"] = full_features["author_id"].astype(str)

    # Keep users with enough interactions (same filter as original training)
    user_counts = cf_data.groupby("author_id").size()
    active_users = user_counts[user_counts >= 3].index
    cf_filtered = cf_data[cf_data["author_id"].isin(active_users)].copy()

    item_counts = cf_filtered.groupby("product_id").size()
    active_items = item_counts[item_counts >= 5].index
    cf_filtered = cf_filtered[cf_filtered["product_id"].isin(active_items)].copy()

    print(f"Filtered interactions: {len(cf_filtered):,} rows")
    print(f"Users: {cf_filtered['author_id'].nunique():,}, Items: {cf_filtered['product_id'].nunique():,}")

    # Build user feature tuples from skin_type + skin_tone
    skin_info = full_features[["author_id", "skin_type", "skin_tone"]].dropna().drop_duplicates("author_id")
    skin_map = skin_info.set_index("author_id")[["skin_type", "skin_tone"]].to_dict("index")

    training_users = cf_filtered["author_id"].unique()
    user_feature_tuples = []
    for uid in training_users:
        if uid in skin_map:
            st = skin_map[uid]["skin_type"]
            stn = skin_map[uid]["skin_tone"]
            features = []
            if pd.notna(st):
                features.append(f"skin_type:{st}")
            if pd.notna(stn):
                features.append(f"skin_tone:{stn}")
            if features:
                user_feature_tuples.append((uid, features))

    print(f"Users with skin features: {len(user_feature_tuples):,} / {len(training_users):,}")

    user_ids = cf_filtered["author_id"].unique().tolist()
    item_ids = cf_filtered["product_id"].unique().tolist()

    from src.advanced_models import train_lightfm_model

    print("Training LightFM model with user features...")
    artifacts = train_lightfm_model(
        interactions_df=cf_filtered[["author_id", "product_id", "rating"]],
        user_ids=user_ids,
        item_ids=item_ids,
        user_feature_tuples=user_feature_tuples,
        positive_threshold=4.0,
        loss="warp",
        no_components=32,
        learning_rate=0.05,
        epochs=15,
        num_threads=4,
    )

    print(f"Training done. Positive interactions: {artifacts.positive_interactions:,}")
    print(f"user_features_matrix: {artifacts.user_features_matrix.shape}")

    # Build seen_items_by_user
    seen_items_by_user = (
        cf_filtered.groupby("author_id")["product_id"]
        .apply(list)
        .to_dict()
    )

    # Collect all unique feature tokens for cold-start lookup
    all_skin_types = sorted({f.split(":")[1] for _, feats in user_feature_tuples for f in feats if f.startswith("skin_type:")})
    all_skin_tones = sorted({f.split(":")[1] for _, feats in user_feature_tuples for f in feats if f.startswith("skin_tone:")})

    payload = {
        "model": artifacts.model,
        "user_to_idx": artifacts.user_to_idx,
        "item_ids": artifacts.item_ids,
        "user_features_matrix": artifacts.user_features_matrix,
        "item_features_matrix": artifacts.item_features_matrix,
        "seen_items_by_user": seen_items_by_user,
        "training_user_count": len(user_ids),
        "training_item_count": len(item_ids),
        "app_user_count": 0,
        # Extra: feature space info for cold-start new users
        "dataset_user_to_idx": artifacts.user_to_idx,
        "known_skin_types": all_skin_types,
        "known_skin_tones": all_skin_tones,
    }

    # We need the LightFM Dataset object to build new-user feature vectors at inference.
    # Reconstruct it and save the feature mapping.
    from lightfm.data import Dataset
    dataset = Dataset()
    user_feature_tokens = sorted(
        {f for _, feats in user_feature_tuples for f in feats}
    )
    dataset.fit(
        users=user_ids,
        items=item_ids,
        user_features=user_feature_tokens,
    )
    _, user_feature_map, _, _ = dataset.mapping()
    payload["user_feature_map"] = dict(user_feature_map)

    print(f"User feature tokens: {len(user_feature_tokens)}")
    print(f"Sample tokens: {user_feature_tokens[:5]}")

    with open(OUTPUT_PATH, "wb") as f:
        pickle.dump(payload, f, protocol=4)

    print(f"\nSaved to {OUTPUT_PATH}")
    print("Done.")


if __name__ == "__main__":
    main()
