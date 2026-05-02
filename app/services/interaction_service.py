from __future__ import annotations

from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from ..interaction_model import Interaction

MIN_HISTORY_FOR_PERSONALIZATION = 3


def upsert_rating(db: Session, user_id: int, product_id: str, rating: int) -> Interaction:
    """Insert or update a user's rating for a product (one rating per product per user)."""
    stmt = (
        insert(Interaction)
        .values(user_id=user_id, product_id=product_id, rating=rating)
        .on_conflict_do_update(
            index_elements=["user_id", "product_id"],
            set_={"rating": rating},
        )
    )
    db.execute(stmt)
    db.commit()
    return (
        db.query(Interaction)
        .filter(Interaction.user_id == user_id, Interaction.product_id == product_id)
        .first()
    )


def get_user_interactions(db: Session, user_id: int) -> list[Interaction]:
    return (
        db.query(Interaction)
        .filter(Interaction.user_id == user_id)
        .order_by(Interaction.rating.desc(), Interaction.created_at.desc())
        .all()
    )


def get_top_rated_product_ids(db: Session, user_id: int, min_rating: int = 4, limit: int = 5) -> list[str]:
    rows = (
        db.query(Interaction.product_id)
        .filter(Interaction.user_id == user_id, Interaction.rating >= min_rating)
        .order_by(Interaction.rating.desc(), Interaction.created_at.desc())
        .limit(limit)
        .all()
    )
    return [r.product_id for r in rows]


def user_has_app_history(db: Session, user_id: int) -> bool:
    count = (
        db.query(Interaction)
        .filter(Interaction.user_id == user_id)
        .count()
    )
    return count >= MIN_HISTORY_FOR_PERSONALIZATION
