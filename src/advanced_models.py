from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import ast

import numpy as np
import pandas as pd


@dataclass
class LightFMArtifacts:
    model: object
    user_to_idx: dict[str, int]
    item_to_idx: dict[str, int]
    user_ids: np.ndarray
    item_ids: np.ndarray
    user_features_matrix: object | None
    item_features_matrix: object | None
    interaction_shape: tuple[int, int]
    positive_interactions: int


def _coerce_texts(texts: Iterable[object]) -> list[str]:
    normalized: list[str] = []
    for text in texts:
        if pd.isna(text):
            normalized.append("")
        else:
            normalized.append(str(text))
    return normalized


def _normalize_feature_value(value: object, unknown_token: str = "unknown") -> list[str]:
    if pd.isna(value):
        return [unknown_token]

    if isinstance(value, list):
        values = value
    else:
        text = str(value).strip()
        if not text:
            return [unknown_token]

        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = ast.literal_eval(text)
            except (ValueError, SyntaxError):
                parsed = None
            if isinstance(parsed, list):
                values = parsed
            else:
                values = [text]
        elif "," in text:
            values = [part.strip() for part in text.split(",")]
        else:
            values = [text]

    cleaned = []
    for item in values:
        item_text = str(item).strip().lower().replace(" ", "_")
        if item_text:
            cleaned.append(item_text)

    return cleaned or [unknown_token]


def build_item_feature_tuples(
    items_df: pd.DataFrame,
    item_col: str,
    feature_columns: Sequence[str],
) -> list[tuple[str, list[str]]]:
    tuples: list[tuple[str, list[str]]] = []
    for _, row in items_df.iterrows():
        features: list[str] = []
        for column in feature_columns:
            for value in _normalize_feature_value(row.get(column)):
                features.append(f"{column}:{value}")
        tuples.append((str(row[item_col]), features))
    return tuples


def build_user_feature_tuples(
    users_df: pd.DataFrame,
    user_col: str,
    feature_columns: Sequence[str],
) -> list[tuple[str, list[str]]]:
    tuples: list[tuple[str, list[str]]] = []
    deduped_users = users_df.drop_duplicates(subset=[user_col]).copy()
    for _, row in deduped_users.iterrows():
        features: list[str] = []
        for column in feature_columns:
            for value in _normalize_feature_value(row.get(column)):
                features.append(f"{column}:{value}")
        tuples.append((str(row[user_col]), features))
    return tuples


def build_sbert_embeddings(
    texts: Iterable[object],
    model_name: str = "all-MiniLM-L6-v2",
    batch_size: int = 64,
    show_progress_bar: bool = True,
) -> np.ndarray:
    try:
        from sentence_transformers import SentenceTransformer
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "sentence-transformers is required for SBERT embeddings. "
            "Install it before running this notebook."
        ) from exc

    model = SentenceTransformer(model_name)
    embeddings = model.encode(
        _coerce_texts(texts),
        batch_size=batch_size,
        show_progress_bar=show_progress_bar,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return np.asarray(embeddings, dtype=np.float32)


def build_similarity_frame_from_embeddings(
    seed_product_id: str,
    embeddings: np.ndarray,
    productid_to_index: dict[str, int],
    index_to_productid: dict[int, str],
    top_n: int = 10,
    exclude_product_ids: Sequence[str] | None = None,
    score_col: str = "similarity_score",
) -> pd.DataFrame | None:
    seed_product_id = str(seed_product_id)
    if seed_product_id not in productid_to_index:
        return None

    exclude_ids = {str(product_id) for product_id in (exclude_product_ids or [])}
    seed_index = productid_to_index[seed_product_id]
    similarities = embeddings @ embeddings[seed_index]
    ranking = np.argsort(-similarities)

    rows: list[dict[str, float | str]] = []
    for idx in ranking:
        if int(idx) == seed_index:
            continue

        product_id = index_to_productid[int(idx)]
        if product_id in exclude_ids:
            continue

        rows.append(
            {
                "product_id": product_id,
                score_col: float(similarities[int(idx)]),
            }
        )
        if len(rows) >= top_n:
            break

    return pd.DataFrame(rows) if rows else None


def train_lightfm_model(
    interactions_df: pd.DataFrame,
    user_ids: Sequence[object] | None = None,
    item_ids: Sequence[object] | None = None,
    item_feature_tuples: Sequence[tuple[str, list[str]]] | None = None,
    user_feature_tuples: Sequence[tuple[str, list[str]]] | None = None,
    user_col: str = "author_id",
    item_col: str = "product_id",
    rating_col: str = "rating",
    positive_threshold: float = 4.0,
    loss: str = "warp",
    no_components: int = 32,
    learning_rate: float = 0.05,
    epochs: int = 15,
    item_alpha: float = 0.0,
    user_alpha: float = 0.0,
    max_sampled: int = 10,
    num_threads: int = 4,
) -> LightFMArtifacts:
    try:
        from lightfm import LightFM
        from lightfm.data import Dataset
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "lightfm is required for LightFM training. Install it before running this notebook."
        ) from exc

    working_df = interactions_df.copy()
    working_df[user_col] = working_df[user_col].astype(str)
    working_df[item_col] = working_df[item_col].astype(str)

    if rating_col in working_df.columns:
        positive_df = working_df[working_df[rating_col] >= positive_threshold].copy()
    else:
        positive_df = working_df.copy()

    if positive_df.empty:
        raise ValueError("No positive interactions available for LightFM training.")

    resolved_user_ids = (
        np.array([str(user_id) for user_id in user_ids], dtype=object)
        if user_ids is not None
        else positive_df[user_col].astype(str).unique()
    )
    resolved_item_ids = (
        np.array([str(item_id) for item_id in item_ids], dtype=object)
        if item_ids is not None
        else positive_df[item_col].astype(str).unique()
    )

    dataset = Dataset()
    item_feature_tokens = sorted(
        {
            feature
            for _, features in (item_feature_tuples or [])
            for feature in features
        }
    )
    user_feature_tokens = sorted(
        {
            feature
            for _, features in (user_feature_tuples or [])
            for feature in features
        }
    )

    dataset.fit(
        users=resolved_user_ids.tolist(),
        items=resolved_item_ids.tolist(),
        user_features=user_feature_tokens or None,
        item_features=item_feature_tokens or None,
    )

    interactions, _ = dataset.build_interactions(
        (
            (str(user_id), str(item_id))
            for user_id, item_id in positive_df[[user_col, item_col]].itertuples(index=False)
        )
    )

    model = LightFM(
        loss=loss,
        no_components=no_components,
        learning_rate=learning_rate,
        item_alpha=item_alpha,
        user_alpha=user_alpha,
        max_sampled=max_sampled,
        random_state=42,
    )
    item_features_matrix = (
        dataset.build_item_features(item_feature_tuples)
        if item_feature_tuples
        else None
    )
    user_features_matrix = (
        dataset.build_user_features(user_feature_tuples)
        if user_feature_tuples
        else None
    )

    model.fit(
        interactions=interactions,
        item_features=item_features_matrix,
        user_features=user_features_matrix,
        epochs=epochs,
        num_threads=num_threads,
    )

    user_to_idx, _, item_to_idx, _ = dataset.mapping()
    ordered_user_ids = np.array(
        [str(user_id) for user_id, _ in sorted(user_to_idx.items(), key=lambda item: item[1])],
        dtype=object,
    )
    ordered_item_ids = np.array(
        [str(item_id) for item_id, _ in sorted(item_to_idx.items(), key=lambda item: item[1])],
        dtype=object,
    )
    return LightFMArtifacts(
        model=model,
        user_to_idx={str(key): int(value) for key, value in user_to_idx.items()},
        item_to_idx={str(key): int(value) for key, value in item_to_idx.items()},
        user_ids=ordered_user_ids,
        item_ids=ordered_item_ids,
        user_features_matrix=user_features_matrix,
        item_features_matrix=item_features_matrix,
        interaction_shape=interactions.shape,
        positive_interactions=int(interactions.nnz),
    )
