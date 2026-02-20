# ===========================================
# File: backend/app/routers/auth.py
#     /\
#    / K2\
#   /______\
#  ~~~~~~~~~~
#   8,611m
# ===========================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import os

from app.database import get_db
from app.models import User, Patient
from app.schemas import SignupRequest, LoginRequest, AuthResponse

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET  = os.getenv("JWT_SECRET", "changeme_secret")
JWT_EXPIRE  = int(os.getenv("JWT_EXPIRE_MINUTES", 60))
ALGORITHM   = "HS256"


def _hash(password: str) -> str:
    return pwd_context.hash(password)


def _verify(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRE)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


@router.post("/signup", response_model=AuthResponse)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    # Check if email already exists
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    user = User(email=body.email, password_hash=_hash(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    return AuthResponse(
        token=_create_token(user.id),
        user_id=user.id,
        is_new_user=True
    )


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()

    if not user or not _verify(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    # Check if profile exists to determine is_new_user
    has_profile = db.query(Patient).filter(Patient.user_id == user.id).first() is not None

    return AuthResponse(
        token=_create_token(user.id),
        user_id=user.id,
        is_new_user=not has_profile
    )
