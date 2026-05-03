from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint

from .db import Base


class RecommendationEvent(Base):
    __tablename__ = "recommendation_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String, nullable=False, index=True)
    model_used = Column(String, nullable=False, index=True)
    requested_top_n = Column(Integer, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )


class RecommendationEventItem(Base):
    __tablename__ = "recommendation_event_items"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_event_id = Column(
        Integer,
        ForeignKey("recommendation_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = Column(String, nullable=False, index=True)
    rank = Column(Integer, nullable=False)
    score = Column(Float, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "recommendation_event_id",
            "product_id",
            name="uq_recommendation_event_product",
        ),
    )


class RecommendationClick(Base):
    __tablename__ = "recommendation_clicks"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_event_id = Column(
        Integer,
        ForeignKey("recommendation_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String, nullable=False, index=True)
    rank = Column(Integer, nullable=False)
    clicked_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
