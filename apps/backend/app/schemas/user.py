from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.user import UserRole

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    full_name: str
    role: UserRole 
    is_active: bool
    is_verified: bool
    last_login: datetime | None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserRoleUpdate(BaseModel):
    role: UserRole

class UserStatusUpdate(BaseModel):
    is_active: bool

class UserVerificationUpdate(BaseModel):
    is_verified: bool

class Token(BaseModel):
    access_token: str
    token_type: str
