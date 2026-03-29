

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

import pandas as pd


# -------------------------------------------------------------------
# PROJE YOLLARI
#
# Bu dosya uygulama içinde veri yükleme işlerini tek bir yerde toplar.
# Böylece:
# - dosya yolları her yerde tekrar yazılmaz
# - backend tarafında kod daha temiz kalır
# - ileride CSV yerine veritabanına geçiş kolaylaşır
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
    İstenen dosyanın data_interim klasörü içinde gerçekten var olup
    olmadığını kontrol eder.

    Parameters
    ----------
    filename : str
        Yüklenecek CSV dosyasının adı.

    Returns
    -------
    Path
        Dosyanın tam yolu.

    Raises
    ------
    FileNotFoundError
        Dosya bulunamazsa hata verir.
    """

    file_path = DATA_INTERIM_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"Gerekli veri dosyası bulunamadı: {file_path}"
        )

    return file_path


# -------------------------------------------------------------------
# ÜRÜN TABLOSU
# -------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_products() -> pd.DataFrame:
    """
    Temizlenmiş ürün tablosunu yükler.

    Backend tarafında öneri sonuçlarını kullanıcıya gösterebilmek için
    ürün adı, marka, kategori ve fiyat gibi alanlara ihtiyaç vardır.
    Bu fonksiyon products_clean.csv dosyasını belleğe alır ve tekrar tekrar
    diskten okunmasını önlemek için cache kullanır.
    """

    file_path = _resolve_data_file("products_clean.csv")
    df = pd.read_csv(file_path)

    # Kimlik kolonlarını string'e çevirerek merge problemlerini engelle
    if "product_id" in df.columns:
        df["product_id"] = df["product_id"].astype(str)

    # API tarafında null değerlerle uğraşmamak için temel metin alanlarını temizle
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
# CF / ETKİLEŞİM TABLOSU
# -------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_interactions() -> pd.DataFrame:
    """
    Kullanıcı-ürün etkileşim tablosunu yükler.

    Şu an uygulama tarafında history kontrolü yapmak için temel olarak
    reviews_cf_last.csv dosyasını kullanıyoruz.
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
# PROFİL TABLOSU (opsiyonel)
# -------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_product_profile() -> Optional[pd.DataFrame]:
    """
    product_profile benzeri ara çıktı varsa yükler.

    Bu dosya bazı sistemlerde henüz kaydedilmemiş olabilir. Bu yüzden
    zorunlu değil, bulunamazsa None döndürür.
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
    Ürün tablosundaki tertiary_category değerlerini benzersiz ve sıralı
    liste halinde döndürür.
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

    Parameters
    ----------
    user_id : str
        Kullanıcı kimliği.
    """

    interactions = load_interactions()
    user_id = str(user_id)

    return interactions[interactions["author_id"] == user_id].copy()


def user_has_history(user_id: str, min_interactions: int = 3) -> bool:
    """
    Kullanıcının hibrit / CF tabanlı öneri alabilecek kadar geçmişi olup
    olmadığını kontrol eder.

    Parameters
    ----------
    user_id : str
        Kullanıcı kimliği.
    min_interactions : int, default=3
        Geçmiş var kabul etmek için minimum etkileşim sayısı.
    """

    history = get_user_history(user_id)
    return len(history) >= min_interactions