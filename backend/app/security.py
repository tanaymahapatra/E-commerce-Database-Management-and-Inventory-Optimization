
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import get_db

# Load JWT secret from root .env
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is missing from .env")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# 1. Hash passwords using bcrypt
def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")

    if len(password_bytes) > 72:
        raise ValueError("Password exceeds 72 bytes")

    hashed = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt(rounds=12)
    )

    return hashed.decode("utf-8")


# 2. Verify entered password
def verify_password(password: str, stored_hash: str) -> bool:
    password_bytes = password.encode("utf-8")

    if len(password_bytes) > 72:
        return False

    try:
        return bcrypt.checkpw(
            password_bytes,
            stored_hash.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


# Dummy hash for unknown usernames
DUMMY_HASH = hash_password("dummy-password-for-login")


# 3. Create JWT access token
def create_access_token(user_id: int) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=30)

    return jwt.encode(
        {
            "sub": str(user_id),
            "exp": expires
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# 4. Identify the logged-in user
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    invalid_token = HTTPException(
        status_code=401,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "exp"]}
        )

        user_id = int(payload["sub"])

    except (InvalidTokenError, ValueError, TypeError, KeyError):
        raise invalid_token

    user = db.execute(
        text("""
            SELECT user_id, username, role, is_active
            FROM app_users
            WHERE user_id = :user_id
        """),
        {"user_id": user_id}
    ).mappings().first()

    if user is None or not user["is_active"]:
        raise invalid_token

    return dict(user)


# 5. Check warehouse access
def check_warehouse_access(
    db: Session,
    user: dict,
    warehouse_id: int
):

    # Admin can access every warehouse
    if user["role"] == "admin":
        return

    if user["role"] !="manager":
        raise HTTPException(
            status_code=403,
            detail="Role not permitted"
        )

    # For warehouse users, user_id must match warehouse_id
    if user["user_id"] != warehouse_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied for this warehouse"
        )

    # Verify assignment in MariaDB
    allowed = db.execute(
        text("""
            SELECT 1
            FROM user_warehouse_access
            WHERE user_id = :user_id
              AND warehouse_id = :warehouse_id
        """),
        {
            "user_id": user["user_id"],
            "warehouse_id": warehouse_id
        }
    ).scalar_one_or_none()

    if allowed is None:
        raise HTTPException(
            status_code=403,
            detail="Access denied for this warehouse"
        )


# 6. Admin-only authorization
def require_admin(
    user: dict = Depends(get_current_user)
):
    if user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return user
