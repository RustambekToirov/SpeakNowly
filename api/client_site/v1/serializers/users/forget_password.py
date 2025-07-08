from pydantic import BaseModel, EmailStr, Field, field_validator
import re

class ForgetPasswordSerializer(BaseModel):
    """Serializer for requesting a password reset."""
    email: EmailStr = Field(..., description="User's email address")

class ResetPasswordSerializer(BaseModel):
    """Serializer for verifying OTP and setting a new password."""
    email: EmailStr = Field(..., description="User's email address")
    code: int = Field(..., description="Verification code sent to the email")
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
