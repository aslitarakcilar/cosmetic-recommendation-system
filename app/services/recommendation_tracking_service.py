from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..interaction_model import Interaction
from ..recommendation_event_model import (
    RecommendationClick,
    RecommendationEvent,
    RecommendationEventItem,
)
from ..schemas.analytics import (
    ModelPerformanceMetric,
    RankPerformanceMetric,
    RecommendationMetricsResponse,
)

ATTRIBUTION_WINDOW_HOURS = 24
ATTRIBUTION_WINDOW = timedelta(hours=ATTRIBUTION_WINDOW_HOURS)


@dataclass
class RatingAttribution:
    recommendation_event_id: int | None
    recommended_rank: int | None
    attributed_within_window: bool


def log_recommendation_event(
    db: Session,
    *,
    user_id: int,
    category: str,
    model_used: str,
    requested_top_n: int,
    items: list[object],
) -> RecommendationEvent:
    event = RecommendationEvent(
        user_id=user_id,
        category=category,
        model_used=model_used,
        requested_top_n=requested_top_n,
    )
    db.add(event)
    db.flush()

    for index, item in enumerate(items, start=1):
        db.add(
            RecommendationEventItem(
                recommendation_event_id=event.id,
                product_id=str(_item_value(item, "product_id", "")),
                rank=index,
                score=_to_float_or_none(_item_value(item, "score")),
            )
        )

    db.commit()
    db.refresh(event)
    return event


def resolve_rating_attribution(
    db: Session,
    *,
    user_id: int,
    product_id: str,
    recommendation_event_id: int | None,
) -> RatingAttribution:
    if recommendation_event_id is None:
        return RatingAttribution(None, None, False)

    event = (
        db.query(RecommendationEvent)
        .filter(
            RecommendationEvent.id == recommendation_event_id,
            RecommendationEvent.user_id == user_id,
        )
        .first()
    )
    if event is None or _is_outside_attribution_window(event.created_at):
        return RatingAttribution(None, None, False)

    event_item = (
        db.query(RecommendationEventItem)
        .filter(
            RecommendationEventItem.recommendation_event_id == recommendation_event_id,
            RecommendationEventItem.product_id == product_id,
        )
        .first()
    )
    if event_item is None:
        return RatingAttribution(None, None, False)

    return RatingAttribution(event.id, event_item.rank, True)


def log_recommendation_click(
    db: Session,
    *,
    user_id: int,
    recommendation_event_id: int,
    product_id: str,
) -> bool:
    event = (
        db.query(RecommendationEvent)
        .filter(
            RecommendationEvent.id == recommendation_event_id,
            RecommendationEvent.user_id == user_id,
        )
        .first()
    )
    if event is None:
        return False

    event_item = (
        db.query(RecommendationEventItem)
        .filter(
            RecommendationEventItem.recommendation_event_id == recommendation_event_id,
            RecommendationEventItem.product_id == product_id,
        )
        .first()
    )
    if event_item is None:
        return False

    db.add(
        RecommendationClick(
            recommendation_event_id=recommendation_event_id,
            user_id=user_id,
            product_id=product_id,
            rank=event_item.rank,
        )
    )
    db.commit()
    return True


def build_recommendation_metrics(db: Session) -> RecommendationMetricsResponse:
    events = db.query(RecommendationEvent).all()
    event_items = db.query(RecommendationEventItem).all()
    clicks = db.query(RecommendationClick).all()
    attributed_ratings = (
        db.query(Interaction)
        .filter(Interaction.recommendation_event_id.isnot(None))
        .all()
    )

    event_by_id = {event.id: event for event in events}
    item_key_to_item = {
        (item.recommendation_event_id, item.product_id): item for item in event_items
    }
    click_keys = {(click.recommendation_event_id, click.product_id) for click in clicks}

    model_buckets: dict[str, dict[str, list[float] | set | int]] = {}
    rank_buckets: dict[int, dict[str, list[float] | set | int]] = {}

    for event in events:
        bucket = model_buckets.setdefault(
            event.model_used,
            {
                "events": 0,
                "impressions": 0,
                "clicks": set(),
                "ratings": [],
                "positives": 0,
            },
        )
        bucket["events"] += 1

    for item in event_items:
        event = event_by_id.get(item.recommendation_event_id)
        if event is None:
            continue

        model_bucket = model_buckets.setdefault(
            event.model_used,
            {
                "events": 0,
                "impressions": 0,
                "clicks": set(),
                "ratings": [],
                "positives": 0,
            },
        )
        model_bucket["impressions"] += 1

        rank_bucket = rank_buckets.setdefault(
            item.rank,
            {"impressions": 0, "clicks": set(), "ratings": []},
        )
        rank_bucket["impressions"] += 1

        key = (item.recommendation_event_id, item.product_id)
        if key in click_keys:
            model_bucket["clicks"].add(key)
            rank_bucket["clicks"].add(key)

    for interaction in attributed_ratings:
        if interaction.recommendation_event_id is None:
            continue
        item = item_key_to_item.get((interaction.recommendation_event_id, interaction.product_id))
        event = event_by_id.get(interaction.recommendation_event_id)
        if item is None or event is None:
            continue

        model_bucket = model_buckets.setdefault(
            event.model_used,
            {
                "events": 0,
                "impressions": 0,
                "clicks": set(),
                "ratings": [],
                "positives": 0,
            },
        )
        model_bucket["ratings"].append(float(interaction.rating))
        if interaction.rating >= 4:
            model_bucket["positives"] += 1

        rank_bucket = rank_buckets.setdefault(
            item.rank,
            {"impressions": 0, "clicks": set(), "ratings": []},
        )
        rank_bucket["ratings"].append(float(interaction.rating))

    model_metrics = [
        ModelPerformanceMetric(
            model_used=model_used,
            recommendation_events=int(bucket["events"]),
            impressions=int(bucket["impressions"]),
            clicks=len(bucket["clicks"]),
            ctr=_ratio(len(bucket["clicks"]), int(bucket["impressions"])),
            attributed_ratings=len(bucket["ratings"]),
            rating_conversion=_ratio(len(bucket["ratings"]), int(bucket["impressions"])),
            positive_rating_rate=_ratio(int(bucket["positives"]), len(bucket["ratings"])),
            average_attributed_rating=_average(bucket["ratings"]),
        )
        for model_used, bucket in sorted(model_buckets.items())
    ]

    rank_metrics = [
        RankPerformanceMetric(
            rank=rank,
            impressions=int(bucket["impressions"]),
            clicks=len(bucket["clicks"]),
            ctr=_ratio(len(bucket["clicks"]), int(bucket["impressions"])),
            attributed_ratings=len(bucket["ratings"]),
            rating_conversion=_ratio(len(bucket["ratings"]), int(bucket["impressions"])),
            average_attributed_rating=_average(bucket["ratings"]),
        )
        for rank, bucket in sorted(rank_buckets.items())
    ]

    total_impressions = len(event_items)
    total_clicks = len(click_keys)
    total_attributed_ratings = len(attributed_ratings)
    positive_count = len([rating for rating in attributed_ratings if rating.rating >= 4])

    return RecommendationMetricsResponse(
        attribution_window_hours=ATTRIBUTION_WINDOW_HOURS,
        total_recommendation_events=len(events),
        total_impressions=total_impressions,
        total_clicks=total_clicks,
        total_attributed_ratings=total_attributed_ratings,
        overall_ctr=_ratio(total_clicks, total_impressions),
        overall_rating_conversion=_ratio(total_attributed_ratings, total_impressions),
        overall_positive_rating_rate=_ratio(positive_count, total_attributed_ratings),
        average_attributed_rating=_average([float(item.rating) for item in attributed_ratings]),
        model_metrics=model_metrics,
        rank_metrics=rank_metrics,
    )


def _average(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


def _is_outside_attribution_window(created_at: datetime) -> bool:
    created = created_at if created_at.tzinfo is not None else created_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - created > ATTRIBUTION_WINDOW


def _to_float_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _item_value(item: object, key: str, default: object = None) -> object:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)
