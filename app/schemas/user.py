from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    city: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    is_admin: bool = False
    role: str = "player"

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    city: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None
    role: Optional[str] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
