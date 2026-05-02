from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..dependencies import get_current_user
from ..schemas.interaction import RateRequest, RateResponse
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
