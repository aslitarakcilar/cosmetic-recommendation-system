from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..dependencies import get_current_user
from ..schemas.user import UpdateProfileRequest, UserProfile
from ..services.user_service import update_user_profile
from ..user_model import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
def get_me(current_user: User = Depends(get_current_user)) -> UserProfile:
    return UserProfile.model_validate(current_user)


@router.patch("/me", response_model=UserProfile)
def update_me(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfile:
    updated = update_user_profile(
        db=db,
        user=current_user,
        skin_type=body.skin_type,
        skin_tone=body.skin_tone,
        undertone=body.undertone,
    )
    return UserProfile.model_validate(updated)
