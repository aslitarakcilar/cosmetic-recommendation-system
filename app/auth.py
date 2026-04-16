from __future__ import annotations

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .models import User

# Şifre hash sistemi
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create_user(
    db: Session,
    name: str,
    email: str,
    password: str,
    skin_type: str | None = None,
    skin_tone: str | None = None,
) -> User:

    hashed_password = hash_password(password)

    user = User(
        name=name,
        email=email,
        password=hashed_password,
        skin_type=skin_type,
        skin_tone=skin_tone,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user