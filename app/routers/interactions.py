from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..dependencies import get_current_user
from ..recommendation.data_loader import load_products
from ..schemas.interaction import RateRequest, RateResponse, RatedProductDetail
from ..services.interaction_service import get_user_interactions, upsert_rating
from ..user_model import User

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.post("/rate", response_model=RateResponse)
def rate_product(
    request: RateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RateResponse:
    interaction = upsert_rating(
        db=db,
        user_id=current_user.id,
        product_id=request.product_id,
        rating=request.rating,
    )
    return RateResponse.model_validate(interaction)


@router.get("/mine", response_model=list[RateResponse])
def my_interactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RateResponse]:
    interactions = get_user_interactions(db, current_user.id)
    return [RateResponse.model_validate(i) for i in interactions]


@router.get("/mine/detailed", response_model=list[RatedProductDetail])
def my_interactions_detailed(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RatedProductDetail]:
    interactions = get_user_interactions(db, current_user.id)
    if not interactions:
        return []

    products = load_products().set_index("product_id")
    result: list[RatedProductDetail] = []
    for i in interactions:
        pid = i.product_id
        row = products.loc[pid] if pid in products.index else None
        result.append(
            RatedProductDetail(
                product_id=pid,
                rating=i.rating,
                rated_at=i.created_at,
                product_name=str(row["product_name"]) if row is not None else pid,
                brand_name=str(row["brand_name"]) if row is not None else "—",
                tertiary_category=str(row["tertiary_category"]) if row is not None else "—",
                price_usd=float(row["price_usd"]) if row is not None and pd.notna(row.get("price_usd")) else None,
            )
        )
    return result
