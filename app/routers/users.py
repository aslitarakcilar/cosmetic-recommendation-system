from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dependencies import get_current_user
from ..schemas.user import UserProfile
from ..user_model import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
def get_me(current_user: User = Depends(get_current_user)) -> UserProfile:
    return UserProfile.model_validate(current_user)
