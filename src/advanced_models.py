from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
import pandas as pd


@dataclass
class LightFMArtifacts:
    model: object
    user_to_idx: dict[str, int]
    item_to_idx: dict[str, int]
    user_ids: np.ndarray
    item_ids: np.ndarray
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
    user_col: str = "author_id",
    item_col: str = "product_id",
    rating_col: str = "rating",
    positive_threshold: float = 4.0,
    loss: str = "warp",
    no_components: int = 32,
    learning_rate: float = 0.05,
    epochs: int = 15,
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
    dataset.fit(
        users=resolved_user_ids.tolist(),
        items=resolved_item_ids.tolist(),
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
        random_state=42,
    )
    model.fit(
        interactions=interactions,
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
        interaction_shape=interactions.shape,
        positive_interactions=int(interactions.nnz),
    )
