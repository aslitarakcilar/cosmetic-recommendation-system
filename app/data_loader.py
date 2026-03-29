from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

import pandas as pd
import pickle 


# -------------------------------------------------------------------
# PROJE YOLLARI
# -------------------------------------------------------------------

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
DATA_INTERIM_DIR = PROJECT_ROOT / "data_interim"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


# -------------------------------------------------------------------
# DOSYA YOLU YARDIMCI FONKSİYONU
# -------------------------------------------------------------------

def _resolve_data_file(filename: str) -> Path:
    """
    data_interim içindeki bir dosyanın gerçekten var olup olmadığını kontrol eder.
    """

    file_path = DATA_INTERIM_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Gerekli veri dosyası bulunamadı: {file_path}")

    return file_path


# -------------------------------------------------------------------
# ÜRÜN TABLOSU
# -------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_products() -> pd.DataFrame:
    """
    Temizlenmiş ürün tablosunu yükler.
    """

    file_path = _resolve_data_file("products_clean.csv")
    df = pd.read_csv(file_path)

    if "product_id" in df.columns:
        df["product_id"] = df["product_id"].astype(str)

    text_cols = [
        "product_name",
        "brand_name",
        "primary_category",
        "secondary_category",
        "tertiary_category",
    ]

    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna("unknown")

    return df


# -------------------------------------------------------------------
# ETKİLEŞİM TABLOSU
# -------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_interactions() -> pd.DataFrame:
    """
    Kullanıcı-ürün etkileşim tablosunu yükler.
    Şu an reviews_cf_last.csv kullanılıyor.
    """

    file_path = _resolve_data_file("reviews_cf_last.csv")
    df = pd.read_csv(file_path)

    if "author_id" in df.columns:
        df["author_id"] = df["author_id"].astype(str)

    if "product_id" in df.columns:
        df["product_id"] = df["product_id"].astype(str)

    if "submission_time" in df.columns:
        df["submission_time"] = pd.to_datetime(df["submission_time"], errors="coerce")

    return df


# -------------------------------------------------------------------
# PROFİL TABLOSU (OPSİYONEL)
# -------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_product_profile() -> Optional[pd.DataFrame]:
    """
    Eğer product_profile benzeri çıktı dosyası varsa yükler.
    Yoksa None döner.
    """

    candidate_files = [
        "product_profile.csv",
        "product_profile_final.csv",
    ]

    for filename in candidate_files:
        file_path = DATA_INTERIM_DIR / filename

        if file_path.exists():
            df = pd.read_csv(file_path)

            if "product_id" in df.columns:
                df["product_id"] = df["product_id"].astype(str)

            return df

    return None


# -------------------------------------------------------------------
# YARDIMCI FONKSİYONLAR
# -------------------------------------------------------------------

def get_available_categories() -> list[str]:
    """
    Ürün tablosundaki benzersiz tertiary_category değerlerini döndürür.
    """

    products = load_products()

    if "tertiary_category" not in products.columns:
        return []

    categories = (
        products["tertiary_category"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    categories = [cat for cat in categories.unique().tolist() if cat]
    categories.sort()

    return categories


def get_user_history(user_id: str) -> pd.DataFrame:
    """
    Belirli bir kullanıcının geçmiş etkileşimlerini döndürür.
    """

    interactions = load_interactions()
    user_id = str(user_id)

    return interactions[interactions["author_id"] == user_id].copy()


def user_has_history(user_id: str, min_interactions: int = 3) -> bool:
    """
    Kullanıcının öneri motorunda history-based yol için yeterli etkileşimi
    olup olmadığını kontrol eder.
    """

    history = get_user_history(user_id)
    return len(history) >= min_interactions
# -------------------------------------------------------------------
# HYBRID MODEL VERİSİNİ YÜKLEME
# -------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_hybrid_data() -> dict:
    """
    Notebook'ta kaydedilmiş hybrid model objelerini yükler.
    """

    file_path = PROJECT_ROOT / "app" / "models" / "hybrid_data.pkl"

    if not file_path.exists():
        raise FileNotFoundError(f"Hybrid model dosyası bulunamadı: {file_path}")

    with open(file_path, "rb") as f:
        hybrid_data = pickle.load(f)

    return hybrid_data