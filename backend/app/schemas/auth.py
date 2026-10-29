from typing import Literal
from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"]


class UserResponse(BaseModel):
    user_id: int
    username: str
    role: Literal["admin", "manager"]
    is_active: bool
