from pydantic import BaseModel, EmailStr, Field, field_validator


class EmailUpdateSerializer(BaseModel):
    """Serializer for updating email."""
    email: EmailStr = Field(..., description="New email of the user")

    model_config = {"from_attributes": True}


class CheckOTPEmailSerializer(BaseModel):
    """Serializer for verifying OTP code."""
    new_email: EmailStr = Field(..., description="New email to confirm")
    code: int = Field(..., ge=10000, le=99999, description="OTP code (5 digits)")

    model_config = {"from_attributes": True}

    @field_validator("new_email")
    @classmethod
    def validate_email_domain(cls, value):
        if "spam" in value:
            raise ValueError("Email must not contain the word 'spam'")
        return value
