from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserProfile(BaseModel):
    id: int
    email: EmailStr
    skin_type: str
    skin_tone: str
    undertone: str
    created_at: datetime

    model_config = {"from_attributes": True}
