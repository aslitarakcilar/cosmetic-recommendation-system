from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    skin_type: str = Field(..., description="dry | oily | combination | normal | sensitive")
    skin_tone: str = Field(..., description="fair | light | medium | tan | dark | rich | deep")
    undertone: str = Field(..., description="warm | cool | neutral | olive")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
