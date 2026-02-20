# ===========================================
# File: backend/app/routers/auth.py
#     /\
#    / K2\
#   /______\
#  ~~~~~~~~~~
#   8,611m
# ===========================================

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import os

from app.schemas import SignupRequest, LoginRequest, AuthResponse
from app.pandas_store import create_user, get_user_by_email, has_patient_for_user, ensure_vaccines_seeded

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
def signup(body: SignupRequest):
    ensure_vaccines_seeded()
    try:
        user = create_user(body.email, _hash(body.password))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return AuthResponse(
        token=_create_token(int(user["id"])),
        user_id=int(user["id"]),
        is_new_user=True
    )


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest):
    ensure_vaccines_seeded()
    user = get_user_by_email(body.email)

    if not user or not _verify(body.password, str(user["password_hash"])):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    has_profile = has_patient_for_user(int(user["id"]))

    return AuthResponse(
        token=_create_token(int(user["id"])),
        user_id=int(user["id"]),
        is_new_user=not has_profile
    )
