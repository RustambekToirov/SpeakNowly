from pydantic import BaseModel, EmailStr, Field
from typing import Literal

class ResendOTPSchema(BaseModel):
    """Serializer for resending OTP code."""
    email: EmailStr = Field(..., description="Email to resend the verification code")
    verification_type: Literal[
        "register",
        "login",
        "reset_password",
        "forget_password",
        "update_email"
    ] = Field(..., description="Type of verification")

class ResendOTPResponseSerializer(BaseModel):
    """Serializer for resend OTP response."""
    message: str = Field(..., description="Result message of the operation")