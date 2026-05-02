from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

import pandas as pd
import pickle

from ..config import settings


def _require(filename: str) -> Path:
    path = settings.data_interim_dir / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Required data file not found: {path}\n"
            "Run notebook 02_preprocessing.ipynb to generate data_interim/ files."
        )
    return path


@lru_cache(maxsize=1)
def load_products() -> pd.DataFrame:
    df = pd.read_csv(_require("products_clean.csv"))
    df["product_id"] = df["product_id"].astype(str)
    for col in ["product_name", "brand_name", "primary_category", "secondary_category", "tertiary_category"]:
        if col in df.columns:
            df[col] = df[col].fillna("unknown")
    return df


@lru_cache(maxsize=1)
def load_interactions() -> pd.DataFrame:
    df = pd.read_csv(_require("reviews_cf_last.csv"))
    df["author_id"] = df["author_id"].astype(str)
    df["product_id"] = df["product_id"].astype(str)
    if "submission_time" in df.columns:
        df["submission_time"] = pd.to_datetime(df["submission_time"], errors="coerce")
    return df


@lru_cache(maxsize=1)
def load_product_profile() -> Optional[pd.DataFrame]:
    for name in ["product_profile.csv", "product_profile_final.csv"]:
        path = settings.data_interim_dir / name
        if path.exists():
            df = pd.read_csv(path)
            df["product_id"] = df["product_id"].astype(str)
            return df
    return None


@lru_cache(maxsize=1)
def load_hybrid_data() -> Optional[dict]:
    path = settings.app_models_dir / "hybrid_data.pkl"
    if not path.exists():
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


def get_user_history(author_id: str) -> pd.DataFrame:
    interactions = load_interactions()
    return interactions[interactions["author_id"] == author_id].copy()


def user_has_history(author_id: str, min_interactions: int = 3) -> bool:
    return len(get_user_history(author_id)) >= min_interactions


def get_available_categories() -> list[str]:
    products = load_products()
    if "tertiary_category" not in products.columns:
        return []
    categories = (
        products["tertiary_category"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )
    return sorted(c for c in categories if c)
