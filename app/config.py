from __future__ import annotations

import secrets
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # JWT
    secret_key: str = secrets.token_hex(32)
    algorithm: str = "HS256"
    access_token_expire_days: int = 30

    # Database
    database_url: str = "sqlite:///./app.db"

    # CORS — tighten in production
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Paths
    project_root: Path = Path(__file__).resolve().parent.parent

    @property
    def data_interim_dir(self) -> Path:
        return self.project_root / "data_interim"

    @property
    def app_models_dir(self) -> Path:
        return self.project_root / "app" / "models"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
