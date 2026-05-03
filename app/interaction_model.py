from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint

from .db import Base


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)  # 1–5
    recommendation_event_id = Column(Integer, ForeignKey("recommendation_events.id", ondelete="SET NULL"), nullable=True, index=True)
    recommended_rank = Column(Integer, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_user_product"),
    )
