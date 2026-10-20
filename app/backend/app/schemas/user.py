from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserRoleEnum(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    STAFF = "staff"
    ANALYST = "analyst"


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, min_length=1, max_length=120)
    email: EmailStr
    role: UserRoleEnum = UserRoleEnum.STAFF
    is_active: bool = True


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRoleEnum = UserRoleEnum.STAFF
    is_active: bool = True


class UserSignup(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRoleEnum] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6)


class UserProfileUpdate(BaseModel):
    email: Optional[EmailStr] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = Field(None, min_length=6)


class UserRead(UserBase):
    user_id: int
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserRead


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None
    token_type: Optional[str] = None
    exp: Optional[int] = None