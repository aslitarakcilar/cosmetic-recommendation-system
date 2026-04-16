from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


def _normalize_category(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def _series_mode_or_none(series: pd.Series) -> str | None:
    cleaned = series.dropna()
    if cleaned.empty:
        return None
    mode = cleaned.mode()
    if mode.empty:
        return None
    return str(mode.iloc[0])


def _min_max_normalize(series: pd.Series) -> pd.Series:
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series([0.0] * len(series), index=series.index)
    return (series - min_val) / (max_val - min_val)


@dataclass
class FastEvaluationModels:
    train_df: pd.DataFrame
    products_clean: pd.DataFrame
    profile_df: pd.DataFrame
    popularity_stats: pd.DataFrame
    predicted_scores: np.ndarray
    train_item_ids: np.ndarray
    user_to_idx: dict[str, int]
    similarity_matrix: np.ndarray
    productid_to_index: dict[str, int]
    index_to_productid: dict[int, str]
    sbert_embeddings: np.ndarray | None = None
    lightfm_model_obj: Any | None = None
    lightfm_user_to_idx: dict[str, int] | None = None
    lightfm_item_ids: np.ndarray | None = None
    candidate_pool_size: int = 200

    def __post_init__(self) -> None:
        self.products_clean = self.products_clean.copy()
        self.products_clean["product_id"] = self.products_clean["product_id"].astype(str)
        self.products_clean["category_norm"] = self.products_clean["tertiary_category"].apply(_normalize_category)

        self.train_df = self.train_df.copy()
        self.train_df["author_id"] = self.train_df["author_id"].astype(str)
        self.train_df["product_id"] = self.train_df["product_id"].astype(str)
        self.train_df["category_norm"] = self.train_df["tertiary_category"].apply(_normalize_category)

        self.profile_df = self.profile_df.copy()
        self.profile_df["product_id"] = self.profile_df["product_id"].astype(str)
        self.profile_df["category_norm"] = self.profile_df["tertiary_category"].apply(_normalize_category)

        self.popularity_stats = self.popularity_stats.copy()
        self.popularity_stats["product_id"] = self.popularity_stats["product_id"].astype(str)
        self.popularity_stats["category_norm"] = self.popularity_stats["tertiary_category"].apply(_normalize_category)

        self.train_item_ids = np.array([str(item_id) for item_id in self.train_item_ids], dtype=object)
        self.productid_to_index = {str(k): int(v) for k, v in self.productid_to_index.items()}
        self.index_to_productid = {int(k): str(v) for k, v in self.index_to_productid.items()}
        self.lightfm_user_to_idx = {
            str(k): int(v) for k, v in (self.lightfm_user_to_idx or {}).items()
        }
        self.lightfm_item_ids = (
            np.array([str(item_id) for item_id in self.lightfm_item_ids], dtype=object)
            if self.lightfm_item_ids is not None
            else None
        )
        if self.sbert_embeddings is not None:
            embeddings = np.asarray(self.sbert_embeddings, dtype=np.float32)
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms = np.clip(norms, 1e-12, None)
            self.sbert_embeddings = embeddings / norms

        self.product_to_category = dict(
            zip(self.products_clean["product_id"], self.products_clean["category_norm"])
        )

        self.train_seen_by_user = (
            self.train_df.groupby("author_id")["product_id"]
            .agg(lambda values: set(values.astype(str)))
            .to_dict()
        )

        self.seed_item_by_user: dict[str, str | None] = {}
        self.relevant_items_by_user: dict[str, list[str]] = {}
        self.user_profile_by_user: dict[str, tuple[str | None, str | None]] = {}
        self.user_history_count: dict[str, int] = {}
        for user_id, group in self.train_df.groupby("author_id"):
            relevant = group[group["rating"] >= 4].copy()
            if relevant.empty:
                self.seed_item_by_user[user_id] = None
                self.relevant_items_by_user[user_id] = []
            else:
                relevant = relevant.sort_values(
                    by=["rating", "submission_time"],
                    ascending=[False, False],
                )
                self.seed_item_by_user[user_id] = str(relevant.iloc[0]["product_id"])
                self.relevant_items_by_user[user_id] = relevant["product_id"].astype(str).head(5).tolist()

            self.user_profile_by_user[user_id] = (
                _series_mode_or_none(group["skin_type"]),
                _series_mode_or_none(group["skin_tone"]),
            )
            self.user_history_count[user_id] = int(len(group))

        self.popularity_rankings_by_category: dict[str, list[tuple[str, float]]] = {}
        for category, group in self.popularity_stats.groupby("category_norm"):
            ranking = list(
                zip(
                    group.sort_values("popularity_score", ascending=False)["product_id"].tolist(),
                    group.sort_values("popularity_score", ascending=False)["popularity_score"].tolist(),
                )
            )
            self.popularity_rankings_by_category[category] = ranking

        self.profile_candidates_by_category: dict[str, pd.DataFrame] = {
            category: group.reset_index(drop=True)
            for category, group in self.profile_df.groupby("category_norm")
        }

        item_categories = np.array(
            [self.product_to_category.get(product_id, "") for product_id in self.train_item_ids],
            dtype=object,
        )
        self.category_to_item_positions: dict[str, np.ndarray] = {}
        for category in np.unique(item_categories):
            self.category_to_item_positions[str(category)] = np.where(item_categories == category)[0]

        self.lightfm_category_to_item_positions: dict[str, np.ndarray] = {}
        if self.lightfm_item_ids is not None:
            lightfm_categories = np.array(
                [self.product_to_category.get(product_id, "") for product_id in self.lightfm_item_ids],
                dtype=object,
            )
            for category in np.unique(lightfm_categories):
                self.lightfm_category_to_item_positions[str(category)] = np.where(lightfm_categories == category)[0]

        self._seed_rankings: dict[str, np.ndarray] = {}
        self._sbert_seed_rankings: dict[str, np.ndarray] = {}
        self._content_cache: dict[tuple[str, str], pd.DataFrame] = {}
        self._sbert_cache: dict[tuple[str, str], pd.DataFrame] = {}
        self._multi_seed_content_cache: dict[tuple[str, str, int], pd.DataFrame] = {}
        self._cf_cache: dict[tuple[str, str], pd.DataFrame] = {}
        self._lightfm_cache: dict[tuple[str, str], pd.DataFrame] = {}
        self._profile_cache: dict[tuple[str, str | None, str | None], pd.DataFrame | None] = {}

    @staticmethod
    def _empty_content_frame() -> pd.DataFrame:
        return pd.DataFrame(
            {
                "product_id": pd.Series(dtype="str"),
                "similarity_score": pd.Series(dtype="float64"),
            }
        )

    @staticmethod
    def _empty_cf_frame() -> pd.DataFrame:
        return pd.DataFrame(
            {
                "product_id": pd.Series(dtype="str"),
                "cf_score": pd.Series(dtype="float64"),
            }
        )

    def _get_seed_ranking(self, seed_item: str) -> np.ndarray:
        if seed_item not in self._seed_rankings:
            seed_index = self.productid_to_index[seed_item]
            self._seed_rankings[seed_item] = np.argsort(-self.similarity_matrix[seed_index])
        return self._seed_rankings[seed_item]

    def _get_sbert_seed_ranking(self, seed_item: str) -> np.ndarray:
        if self.sbert_embeddings is None:
            return np.array([], dtype=int)

        if seed_item not in self._sbert_seed_rankings:
            seed_index = self.productid_to_index[seed_item]
            similarities = self.sbert_embeddings @ self.sbert_embeddings[seed_index]
            self._sbert_seed_rankings[seed_item] = np.argsort(-similarities)
        return self._sbert_seed_rankings[seed_item]

    def _build_ranked_content_frame(
        self,
        user_id: str,
        category: str,
        ranking: np.ndarray,
        score_lookup: callable,
    ) -> pd.DataFrame:
        seed_item = self.seed_item_by_user.get(user_id)
        if seed_item is None or seed_item not in self.productid_to_index or ranking.size == 0:
            return self._empty_content_frame()

        seed_index = self.productid_to_index[seed_item]
        seen_items = self.train_seen_by_user.get(user_id, set())
        rows: list[dict[str, float | str]] = []

        for idx in ranking:
            if int(idx) == seed_index:
                continue

            product_id = self.index_to_productid[int(idx)]
            if product_id in seen_items:
                continue
            if self.product_to_category.get(product_id, "") != category:
                continue

            rows.append(
                {
                    "product_id": product_id,
                    "similarity_score": float(score_lookup(seed_index, int(idx))),
                }
            )
            if len(rows) >= self.candidate_pool_size:
                break

        return pd.DataFrame(rows)

    def popularity_model(self, row: pd.Series, top_n: int = 10) -> pd.DataFrame | None:
        user_id = str(row["author_id"])
        category = _normalize_category(row["tertiary_category"])
        ranking = self.popularity_rankings_by_category.get(category)
        if not ranking:
            return None

        seen_items = self.train_seen_by_user.get(user_id, set())
        results: list[dict[str, float | str]] = []
        for product_id, score in ranking:
            if product_id in seen_items:
                continue
            results.append({"product_id": product_id, "popularity_score": float(score)})
            if len(results) >= top_n:
                break

        return pd.DataFrame(results) if results else None

    def profile_model(self, row: pd.Series, top_n: int = 10) -> pd.DataFrame | None:
        user_id = str(row["author_id"])
        category = _normalize_category(row["tertiary_category"])
        skin_type, skin_tone = self.user_profile_by_user.get(user_id, (None, None))
        cache_key = (category, skin_type, skin_tone)

        if cache_key not in self._profile_cache:
            category_df = self.profile_candidates_by_category.get(category)
            if category_df is None or (skin_type is None and skin_tone is None):
                self._profile_cache[cache_key] = None
            else:
                df = category_df.copy()

                if skin_type is not None:
                    type_score_col = f"{skin_type.lower()}_score"
                    type_count_col = f"{skin_type.lower()}_count"
                    type_score = df[type_score_col] if type_score_col in df.columns else pd.Series(np.nan, index=df.index)
                    type_count = df[type_count_col] if type_count_col in df.columns else pd.Series(0, index=df.index)
                else:
                    type_score = pd.Series(np.nan, index=df.index)
                    type_count = pd.Series(0, index=df.index)

                if skin_tone is not None:
                    tone_score_col = f"{skin_tone}_tone_score"
                    tone_count_col = f"{skin_tone}_tone_count"
                    tone_score = df[tone_score_col] if tone_score_col in df.columns else pd.Series(np.nan, index=df.index)
                    tone_count = df[tone_count_col] if tone_count_col in df.columns else pd.Series(0, index=df.index)
                else:
                    tone_score = pd.Series(np.nan, index=df.index)
                    tone_count = pd.Series(0, index=df.index)

                type_strength = np.sqrt(type_count.fillna(0))
                tone_strength = np.sqrt(tone_count.fillna(0))
                weighted_type = 0.7 * type_strength
                weighted_tone = 0.3 * tone_strength
                total_weight = (weighted_type + weighted_tone).replace(0, 1)

                dynamic_type_weight = weighted_type / total_weight
                dynamic_tone_weight = weighted_tone / total_weight
                dynamic_type_weight = dynamic_type_weight.where(type_score.notna(), 0)
                dynamic_tone_weight = dynamic_tone_weight.where(tone_score.notna(), 0)

                normalized_sum = (dynamic_type_weight + dynamic_tone_weight).replace(0, 1)
                dynamic_type_weight = dynamic_type_weight / normalized_sum
                dynamic_tone_weight = dynamic_tone_weight / normalized_sum

                scores = (
                    dynamic_type_weight * type_score.fillna(0)
                    + dynamic_tone_weight * tone_score.fillna(0)
                )

                ranked = pd.DataFrame(
                    {
                        "product_id": df["product_id"],
                        "profile_score": scores,
                    }
                ).sort_values("profile_score", ascending=False)

                self._profile_cache[cache_key] = ranked.reset_index(drop=True)

        ranked_df = self._profile_cache.get(cache_key)
        if ranked_df is None or ranked_df.empty:
            return None

        seen_items = self.train_seen_by_user.get(user_id, set())
        if not seen_items:
            return ranked_df.head(top_n).copy()

        mask = ~ranked_df["product_id"].isin(seen_items)
        result = ranked_df.loc[mask].head(top_n).copy()
        return result if not result.empty else None

    def content_model(self, row: pd.Series, top_n: int = 10) -> pd.DataFrame | None:
        user_id = str(row["author_id"])
        category = _normalize_category(row["tertiary_category"])
        cache_key = (user_id, category)

        if cache_key not in self._content_cache:
            seed_item = self.seed_item_by_user.get(user_id)
            ranking = self._get_seed_ranking(seed_item) if seed_item is not None else np.array([], dtype=int)
            self._content_cache[cache_key] = self._build_ranked_content_frame(
                user_id=user_id,
                category=category,
                ranking=ranking,
                score_lookup=lambda seed_idx, idx: self.similarity_matrix[seed_idx][idx],
            )

        result = self._content_cache[cache_key].head(top_n).copy()
        return result if not result.empty else None

    def sbert_content_model(self, row: pd.Series, top_n: int = 10) -> pd.DataFrame | None:
        if self.sbert_embeddings is None:
            return None

        user_id = str(row["author_id"])
        category = _normalize_category(row["tertiary_category"])
        cache_key = (user_id, category)

        if cache_key not in self._sbert_cache:
            seed_item = self.seed_item_by_user.get(user_id)
            ranking = self._get_sbert_seed_ranking(seed_item) if seed_item is not None else np.array([], dtype=int)
            self._sbert_cache[cache_key] = self._build_ranked_content_frame(
                user_id=user_id,
                category=category,
                ranking=ranking,
                score_lookup=lambda seed_idx, idx: self.sbert_embeddings[seed_idx] @ self.sbert_embeddings[idx],
            )

        result = self._sbert_cache[cache_key].head(top_n).copy()
        return result if not result.empty else None

    def content_model_multi_seed(self, row: pd.Series, top_n: int = 10, seed_count: int = 3) -> pd.DataFrame | None:
        user_id = str(row["author_id"])
        category = _normalize_category(row["tertiary_category"])
        cache_key = (user_id, category, seed_count)

        if cache_key not in self._multi_seed_content_cache:
            seed_items = [
                seed_item
                for seed_item in self.relevant_items_by_user.get(user_id, [])[:seed_count]
                if seed_item in self.productid_to_index
            ]

            if not seed_items:
                self._multi_seed_content_cache[cache_key] = self._empty_content_frame()
            else:
                seen_items = self.train_seen_by_user.get(user_id, set())
                candidate_scores: dict[str, list[float]] = {}

                for seed_item in seed_items:
                    seed_index = self.productid_to_index[seed_item]
                    for idx in self._get_seed_ranking(seed_item):
                        if idx == seed_index:
                            continue
                        product_id = self.index_to_productid[idx]
                        if product_id in seen_items:
                            continue
                        if self.product_to_category.get(product_id, "") != category:
                            continue
                        candidate_scores.setdefault(product_id, []).append(
                            float(self.similarity_matrix[seed_index][idx])
                        )
                        if len(candidate_scores) >= self.candidate_pool_size * 4:
                            break

                rows = [
                    {
                        "product_id": product_id,
                        "similarity_score": float(np.mean(scores)),
                    }
                    for product_id, scores in candidate_scores.items()
                ]
                ranked = pd.DataFrame(rows).sort_values("similarity_score", ascending=False).head(self.candidate_pool_size)
                self._multi_seed_content_cache[cache_key] = ranked.reset_index(drop=True)

        result = self._multi_seed_content_cache[cache_key].head(top_n).copy()
        return result if not result.empty else None

    def cf_model(self, row: pd.Series, top_n: int = 10) -> pd.DataFrame | None:
        user_id = str(row["author_id"])
        category = _normalize_category(row["tertiary_category"])
        cache_key = (user_id, category)

        if cache_key not in self._cf_cache:
            if user_id not in self.user_to_idx or category not in self.category_to_item_positions:
                self._cf_cache[cache_key] = self._empty_cf_frame()
            else:
                seen_items = self.train_seen_by_user.get(user_id, set())
                item_positions = self.category_to_item_positions[category]
                category_scores = self.predicted_scores[self.user_to_idx[user_id], item_positions]
                ranking_positions = np.argsort(-category_scores)

                rows: list[dict[str, float | str]] = []
                for local_idx in ranking_positions:
                    product_id = self.train_item_ids[item_positions[local_idx]]
                    if product_id in seen_items:
                        continue
                    rows.append(
                        {
                            "product_id": product_id,
                            "cf_score": float(category_scores[local_idx]),
                        }
                    )
                    if len(rows) >= self.candidate_pool_size:
                        break

                self._cf_cache[cache_key] = pd.DataFrame(rows)

        result = self._cf_cache[cache_key].head(top_n).copy()
        return result if not result.empty else None

    def lightfm_model(self, row: pd.Series, top_n: int = 10) -> pd.DataFrame | None:
        user_id = str(row["author_id"])
        category = _normalize_category(row["tertiary_category"])
        cache_key = (user_id, category)

        if cache_key not in self._lightfm_cache:
            if (
                self.lightfm_model_obj is None
                or self.lightfm_item_ids is None
                or user_id not in self.lightfm_user_to_idx
                or category not in self.lightfm_category_to_item_positions
            ):
                self._lightfm_cache[cache_key] = self._empty_cf_frame()
            else:
                seen_items = self.train_seen_by_user.get(user_id, set())
                item_positions = self.lightfm_category_to_item_positions[category].astype(np.int32)
                user_idx = int(self.lightfm_user_to_idx[user_id])
                user_array = np.full(item_positions.shape, user_idx, dtype=np.int32)
                category_scores = self.lightfm_model_obj.predict(user_array, item_positions, num_threads=1)
                ranking_positions = np.argsort(-category_scores)

                rows: list[dict[str, float | str]] = []
                for local_idx in ranking_positions:
                    product_id = self.lightfm_item_ids[int(item_positions[int(local_idx)])]
                    if product_id in seen_items:
                        continue
                    rows.append(
                        {
                            "product_id": product_id,
                            "cf_score": float(category_scores[int(local_idx)]),
                        }
                    )
                    if len(rows) >= self.candidate_pool_size:
                        break

                self._lightfm_cache[cache_key] = pd.DataFrame(rows)

        result = self._lightfm_cache[cache_key].head(top_n).copy()
        return result if not result.empty else None

    def hybrid_model(self, row: pd.Series, top_n: int = 10, alpha: float = 0.3) -> pd.DataFrame | None:
        content_rec = self.content_model(row, top_n=self.candidate_pool_size)
        cf_rec = self.cf_model(row, top_n=self.candidate_pool_size)

        if content_rec is None and cf_rec is None:
            return None

        if content_rec is None:
            content_rec = self._empty_content_frame()
        if cf_rec is None:
            cf_rec = self._empty_cf_frame()

        hybrid_df = content_rec.merge(cf_rec, on="product_id", how="outer")
        if hybrid_df.empty:
            return None

        hybrid_df["similarity_score"] = hybrid_df["similarity_score"].astype("float64").fillna(0.0)
        hybrid_df["cf_score"] = hybrid_df["cf_score"].astype("float64").fillna(0.0)
        hybrid_df["content_norm"] = _min_max_normalize(hybrid_df["similarity_score"])
        hybrid_df["cf_norm"] = _min_max_normalize(hybrid_df["cf_score"])
        hybrid_df["final_score"] = alpha * hybrid_df["content_norm"] + (1 - alpha) * hybrid_df["cf_norm"]

        result = hybrid_df[["product_id", "final_score"]].sort_values("final_score", ascending=False).head(top_n)
        return result if not result.empty else None

    def hybrid_cf_rerank(
        self,
        row: pd.Series,
        top_n: int = 10,
        beta: float = 0.1,
        cf_depth: int = 100,
        seed_count: int = 3,
    ) -> pd.DataFrame | None:
        cf_rec = self.cf_model(row, top_n=min(cf_depth, self.candidate_pool_size))
        if cf_rec is None or cf_rec.empty:
            return None

        content_rec = self.content_model_multi_seed(row, top_n=self.candidate_pool_size, seed_count=seed_count)
        if content_rec is None:
            content_rec = self._empty_content_frame()

        rerank_df = cf_rec.merge(content_rec, on="product_id", how="left")
        rerank_df["similarity_score"] = rerank_df["similarity_score"].astype("float64").fillna(0.0)
        rerank_df["cf_score"] = rerank_df["cf_score"].astype("float64")

        rerank_df["cf_norm"] = _min_max_normalize(rerank_df["cf_score"])
        rerank_df["content_norm"] = _min_max_normalize(rerank_df["similarity_score"])
        rerank_df["final_score"] = rerank_df["cf_norm"] + beta * rerank_df["content_norm"]

        result = (
            rerank_df[["product_id", "final_score"]]
            .sort_values("final_score", ascending=False)
            .head(top_n)
        )
        return result if not result.empty else None

    def hybrid_dynamic(self, row: pd.Series, top_n: int = 10) -> pd.DataFrame | None:
        user_id = str(row["author_id"])
        history_count = self.user_history_count.get(user_id, 0)

        if history_count >= 20:
            beta = 0.03
            seed_count = 2
        elif history_count >= 10:
            beta = 0.07
            seed_count = 3
        else:
            beta = 0.12
            seed_count = 4

        return self.hybrid_cf_rerank(
            row,
            top_n=top_n,
            beta=beta,
            cf_depth=100,
            seed_count=seed_count,
        )
