from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re

class ProfileSerializer(BaseModel):
    """Serializer for user profile data."""
    email: EmailStr
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    age: Optional[int] = Field(None, ge=0, le=120, description="User's age")
    photo: Optional[str] = Field(None, description="User photo URL (/media/ only)")
    tokens: int = Field(..., description="User's token balance")
    is_premium: bool = Field(..., description="Whether the user has a premium tariff")
    tariff_id: Optional[int] = Field(None, description="User's current tariff id")

    @field_validator("photo")
    @classmethod
    def validate_photo(cls, v):
        if v is None:
            return v
        if v.startswith("/media/") or v.startswith("http://") or v.startswith("https://"):
            return v
        raise ValueError("Photo URL must start with /media/ or be a full http(s) URL")
    
    model_config = {"from_attributes": True}

class ProfileUpdateSerializer(BaseModel):
    """Serializer for updating user profile fields."""
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    age: Optional[int] = Field(None, ge=0, le=120, description="User's age")
    photo: Optional[str] = Field(None, description="User photo URL (/media/ only)")

    @field_validator("photo")
    @classmethod
    def validate_photo(cls, v):
        if v is None:
            return v
        if v.startswith("/media/") or v.startswith("http://") or v.startswith("https://"):
            return v
        raise ValueError("Photo URL must start with /media/ or be a full http(s) URL")
    
    model_config = {"from_attributes": True}

class ProfilePasswordUpdateSerializer(BaseModel):
    """Serializer for updating user password."""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (min 8 chars, 1 digit, 1 lowercase, 1 uppercase)")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit")
        return value
    
    model_config = {"from_attributes": True}
