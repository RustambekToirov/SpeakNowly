from pydantic import BaseModel, EmailStr, Field, field_validator
import re

class RegisterSerializer(BaseModel):
    """Serializer for user registration."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(
        ...,
        min_length=8,
        description="Password (min 8 chars, 1 digit, 1 lowercase, 1 uppercase)"
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower().strip()

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

class RegisterResponseSerializer(BaseModel):
    """Serializer for registration response."""
    message: str = Field(..., description="Informational message about the registration step")
