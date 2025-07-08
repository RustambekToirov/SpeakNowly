from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
import re


class UserBaseSerializer(BaseModel):
    """Base serializer for user display."""
    email: EmailStr = Field(..., description="User's email address")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    age: Optional[int] = Field(None, ge=0, le=120, description="User's age")
    photo: Optional[str] = Field(None, description="User photo URL (/media/ only)")
    is_verified: bool = Field(..., description="Is the user verified")
    is_active: bool = Field(..., description="Is the user active")

    @field_validator("photo")
    @classmethod
    def validate_photo(cls, v):
        if v is None:
            return v
        if v.startswith("/media/") or v.startswith("http://") or v.startswith("https://"):
            return v
        raise ValueError("Photo URL must start with /media/ or be a full http(s) URL")
    

class UserCreateSerializer(BaseModel):
    """Serializer for creating a new user (admin only)."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="Password (min 8 chars, 1 digit, 1 lowercase, 1 uppercase)")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    age: Optional[int] = Field(None, ge=0, le=120, description="User's age")
    photo: Optional[str] = Field(None, description="User photo URL (/media/ only)")
    is_active: Optional[bool] = Field(True, description="Is the user active")
    is_verified: Optional[bool] = Field(False, description="Is the user verified")
    is_staff: Optional[bool] = Field(False, description="Is the user staff")
    is_superuser: Optional[bool] = Field(False, description="Is the user superuser")

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit")
        return value

    @field_validator("photo")
    @classmethod
    def validate_photo(cls, v):
        if v is None:
            return v
        if v.startswith("/media/") or v.startswith("http://") or v.startswith("https://"):
            return v
        raise ValueError("Photo URL must start with /media/ or be a full http(s) URL")
    


class UserUpdateSerializer(BaseModel):
    """Serializer for updating user fields (admin only)."""
    email: Optional[EmailStr] = Field(None, description="User's email address")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    age: Optional[int] = Field(None, ge=0, le=120, description="User's age")
    photo: Optional[str] = Field(None, description="User photo URL (/media/ only)")
    is_active: Optional[bool] = Field(None, description="Is the user active")
    is_verified: Optional[bool] = Field(None, description="Is the user verified")
    is_staff: Optional[bool] = Field(None, description="Is the user staff")
    is_superuser: Optional[bool] = Field(None, description="Is the user superuser")

    @field_validator("photo")
    @classmethod
    def validate_photo(cls, v):
        if v is None:
            return v
        if v.startswith("/media/") or v.startswith("http://") or v.startswith("https://"):
            return v
        raise ValueError("Photo URL must start with /media/ or be a full http(s) URL")
    


class UserResponseSerializer(UserBaseSerializer):
    """Full user response serializer."""
    id: int = Field(..., description="User ID")
    tokens: int = Field(..., ge=0, description="User's token balance")
    is_staff: bool = Field(..., description="Is the user staff")
    is_superuser: bool = Field(..., description="Is the user superuser")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    model_config = {"from_attributes": True}


class UserActivityLogSerializer(BaseModel):
    """Serializer for a single user activity log entry."""
    user_id: int = Field(..., description="User ID")
    action: str = Field(..., description="Action performed")
    timestamp: datetime = Field(..., description="When the action occurred")
