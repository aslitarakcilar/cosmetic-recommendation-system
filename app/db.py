from __future__ import annotations

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables() -> None:
    # Import models here so Base.metadata knows about them
    from . import interaction_model, recommendation_event_model, user_model  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _apply_runtime_migrations()


def _apply_runtime_migrations() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "interactions" not in tables:
        return

    columns = {column["name"] for column in inspector.get_columns("interactions")}
    statements: list[str] = []

    if "recommendation_event_id" not in columns:
        statements.append("ALTER TABLE interactions ADD COLUMN recommendation_event_id INTEGER")
    if "recommended_rank" not in columns:
        statements.append("ALTER TABLE interactions ADD COLUMN recommended_rank INTEGER")

    if not statements:
        return

    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))
