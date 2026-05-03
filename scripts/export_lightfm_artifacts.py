from __future__ import annotations

import pickle
import sqlite3
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.config import settings
from app.recommendation.data_loader import load_interactions, to_lightfm_app_user_id
from src.advanced_models import build_user_feature_tuples, train_lightfm_model


def load_app_interactions() -> pd.DataFrame:
    conn = sqlite3.connect(settings.project_root / "app.db")
    try:
        df = pd.read_sql_query(
            """
            SELECT
                CAST(user_id AS TEXT) AS author_id,
                CAST(product_id AS TEXT) AS product_id,
                rating,
                created_at AS submission_time
            FROM interactions
            """,
            conn,
        )
    finally:
        conn.close()

    if df.empty:
        return df

    df["author_id"] = df["author_id"].map(to_lightfm_app_user_id)
    df["product_id"] = df["product_id"].astype(str)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["submission_time"] = pd.to_datetime(df["submission_time"], errors="coerce")
    return df.dropna(subset=["author_id", "product_id", "rating"]).reset_index(drop=True)


def load_dataset_user_features() -> pd.DataFrame:
    path = settings.data_interim_dir / "reviews_full_features.csv"
    if not path.exists():
        return pd.DataFrame(columns=["author_id", "skin_type", "skin_tone"])

    df = pd.read_csv(path, low_memory=False)
    required_cols = {"author_id", "skin_type", "skin_tone"}
    if not required_cols.issubset(df.columns):
        return pd.DataFrame(columns=["author_id", "skin_type", "skin_tone"])

    result = df[["author_id", "skin_type", "skin_tone"]].copy()
    result["author_id"] = result["author_id"].astype(str)
    return result.drop_duplicates(subset=["author_id"]).reset_index(drop=True)


def load_app_user_features() -> pd.DataFrame:
    conn = sqlite3.connect(settings.project_root / "app.db")
    try:
        df = pd.read_sql_query(
            """
            SELECT
                id,
                skin_type,
                skin_tone
            FROM users
            """,
            conn,
        )
    finally:
        conn.close()

    if df.empty:
        return pd.DataFrame(columns=["author_id", "skin_type", "skin_tone"])

    df["author_id"] = df["id"].map(to_lightfm_app_user_id)
    return df[["author_id", "skin_type", "skin_tone"]].drop_duplicates(
        subset=["author_id"]
    ).reset_index(drop=True)


def build_user_features_frame() -> pd.DataFrame:
    dataset_users = load_dataset_user_features()
    app_users = load_app_user_features()
    combined = pd.concat([dataset_users, app_users], ignore_index=True)
    if combined.empty:
        return combined

    combined["author_id"] = combined["author_id"].astype(str)
    return combined.drop_duplicates(subset=["author_id"]).reset_index(drop=True)


def build_training_interactions() -> pd.DataFrame:
    dataset_interactions = load_interactions()[
        ["author_id", "product_id", "rating", "submission_time"]
    ].copy()
    app_interactions = load_app_interactions()

    if app_interactions.empty:
        return dataset_interactions.reset_index(drop=True)

    merged = pd.concat([dataset_interactions, app_interactions], ignore_index=True)
    merged["author_id"] = merged["author_id"].astype(str)
    merged["product_id"] = merged["product_id"].astype(str)
    merged["rating"] = pd.to_numeric(merged["rating"], errors="coerce")
    merged["submission_time"] = pd.to_datetime(merged["submission_time"], errors="coerce")
    return merged.dropna(subset=["author_id", "product_id", "rating"]).reset_index(drop=True)


def main() -> None:
    interactions = build_training_interactions()
    user_ids = interactions["author_id"].astype(str).unique()
    item_ids = interactions["product_id"].astype(str).unique()
    user_features_df = build_user_features_frame()
    training_user_features = user_features_df[
        user_features_df["author_id"].isin(user_ids)
    ].copy()
    user_feature_tuples = build_user_feature_tuples(
        training_user_features,
        user_col="author_id",
        feature_columns=["skin_type", "skin_tone"],
    )

    artifacts = train_lightfm_model(
        interactions_df=interactions[["author_id", "product_id", "rating"]],
        user_ids=user_ids,
        item_ids=item_ids,
        user_feature_tuples=user_feature_tuples,
        positive_threshold=4.0,
        loss="warp",
        no_components=32,
        epochs=15,
        num_threads=4,
    )

    positive_df = interactions[interactions["rating"] >= 4].copy()
    seen_items_by_user = (
        positive_df.groupby("author_id")["product_id"]
        .agg(lambda values: sorted({str(value) for value in values}))
        .to_dict()
    )

    payload = {
        "model": artifacts.model,
        "user_to_idx": artifacts.user_to_idx,
        "item_ids": artifacts.item_ids,
        "user_features_matrix": artifacts.user_features_matrix,
        "item_features_matrix": artifacts.item_features_matrix,
        "interaction_shape": artifacts.interaction_shape,
        "positive_interactions": artifacts.positive_interactions,
        "seen_items_by_user": seen_items_by_user,
        "training_user_count": len(user_ids),
        "training_item_count": len(item_ids),
        "app_user_count": int(load_app_interactions()["author_id"].nunique()),
    }

    if user_feature_tuples:
        from lightfm.data import Dataset

        user_feature_tokens = sorted(
            {feature for _, features in user_feature_tuples for feature in features}
        )
        dataset = Dataset()
        dataset.fit(
            users=[str(user_id) for user_id in user_ids],
            items=[str(item_id) for item_id in item_ids],
            user_features=user_feature_tokens,
        )
        _, user_feature_map, _, _ = dataset.mapping()
        payload["user_feature_map"] = dict(user_feature_map)

    settings.app_models_dir.mkdir(parents=True, exist_ok=True)
    output_path = settings.app_models_dir / "lightfm_data.pkl"
    with output_path.open("wb") as f:
        pickle.dump(payload, f)

    print(f"LightFM artifact exported to {output_path}")
    print(f"Training users: {len(user_ids)}")
    print(f"Training items: {len(item_ids)}")
    print(f"Interaction shape: {artifacts.interaction_shape}")
    print(f"Positive interactions: {artifacts.positive_interactions}")
    print(f"App users included: {payload['app_user_count']}")


if __name__ == "__main__":
    main()
