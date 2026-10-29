from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.auth import TokenResponse, UserResponse
from ..security import (
    DUMMY_HASH,
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# 1. Login and generate JWT
@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    query = text("""
        SELECT
            user_id,
            password_hash,
            is_active
        FROM app_users
        WHERE username = :username
    """)

    user = db.execute(query, {"username": form.username}).mappings().first()

    stored_hash = user["password_hash"] if user else DUMMY_HASH

    valid_password = verify_password(form.password, stored_hash)

    if not user or not valid_password or not user["is_active"]:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "access_token": create_access_token(user["user_id"]),
        "token_type": "bearer",
    }


# 2. Retrieve current user
@router.get("/me", response_model=UserResponse)
def get_me(user: dict = Depends(get_current_user)):
    return user
