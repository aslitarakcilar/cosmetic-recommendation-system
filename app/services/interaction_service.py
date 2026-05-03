from __future__ import annotations

from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from ..interaction_model import Interaction
from .recommendation_tracking_service import resolve_rating_attribution

MIN_HISTORY_FOR_PERSONALIZATION = 3


def upsert_rating(
    db: Session,
    user_id: int,
    product_id: str,
    rating: int,
    recommendation_event_id: int | None = None,
) -> tuple[Interaction, bool]:
    """Insert or update a user's rating for a product (one rating per product per user)."""
    attribution = resolve_rating_attribution(
        db,
        user_id=user_id,
        product_id=product_id,
        recommendation_event_id=recommendation_event_id,
    )
    stmt = (
        insert(Interaction)
        .values(
            user_id=user_id,
            product_id=product_id,
            rating=rating,
            recommendation_event_id=attribution.recommendation_event_id,
            recommended_rank=attribution.recommended_rank,
        )
        .on_conflict_do_update(
            index_elements=["user_id", "product_id"],
            set_={
                "rating": rating,
                "recommendation_event_id": attribution.recommendation_event_id,
                "recommended_rank": attribution.recommended_rank,
            },
        )
    )
    db.execute(stmt)
    db.commit()
    interaction = (
        db.query(Interaction)
        .filter(Interaction.user_id == user_id, Interaction.product_id == product_id)
        .first()
    )
    return interaction, attribution.attributed_within_window


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
