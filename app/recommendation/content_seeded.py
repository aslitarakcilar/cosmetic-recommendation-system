from __future__ import annotations

import pandas as pd

from .data_loader import load_hybrid_data, load_products


def content_seeded_recommend(
    seed_product_ids: list[str],
    already_rated: set[str],
    category: str,
    top_n: int,
) -> pd.DataFrame | None:
    """
    Content-based recommendation seeded from the user's own highly-rated products.

    Uses the pre-computed TF-IDF cosine similarity matrix from hybrid_data.pkl.
    Aggregates similarity scores across multiple seed items (multi-seed).

    Returns None if the similarity matrix is not available yet (pkl not generated).
    Falls back gracefully — caller must handle None.
    """
    hybrid_data = load_hybrid_data()
    if hybrid_data is None:
        return None

    similarity_matrix = hybrid_data["similarity_matrix"]
    productid_to_index = hybrid_data["productid_to_index"]
    index_to_productid = hybrid_data["index_to_productid"]

    seeds = [pid for pid in seed_product_ids if pid in productid_to_index]
    if not seeds:
        return None

    # Aggregate similarity from all seeds
    agg: dict[str, float] = {}
    for seed in seeds[:5]:
        seed_idx = productid_to_index[seed]
        for idx, sim in enumerate(similarity_matrix[seed_idx]):
            pid = str(index_to_productid[idx])
            if pid in already_rated or pid == seed:
                continue
            agg[pid] = agg.get(pid, 0.0) + float(sim)

    if not agg:
        return None

    ranked = pd.DataFrame(
        [{"product_id": pid, "score": s} for pid, s in agg.items()]
    ).sort_values("score", ascending=False)

    # Join product metadata and filter by category
    products = load_products().copy()
    products["product_id"] = products["product_id"].astype(str)
    ranked = ranked.merge(products, on="product_id", how="left")

    cat_lower = category.strip().lower()
    filtered = ranked[
        ranked["tertiary_category"].astype(str).str.strip().str.lower() == cat_lower
    ]

    if filtered.empty:
        return None

    return filtered.head(top_n).reset_index(drop=True)
