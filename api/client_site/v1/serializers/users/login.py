from typing import Literal
from pydantic import BaseModel, EmailStr, Field


class LoginSerializer(BaseModel):
    """Serializer for user login."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password (minimum 8 characters)")


class OAuth2SignInSerializer(BaseModel):
    """Serializer for OAuth2 sign-in request."""
    token: str = Field(..., description="OAuth2 provider token")
    auth_type: Literal['google', 'apple'] = Field(..., description="OAuth2 provider type")
    client_id: str = Field(..., description="OAuth2 client ID for Apple verification")


class StartTelegramAuthSerializer(BaseModel):
    telegram_id: int = Field(..., description="Telegram user ID")
    phone: str = Field(..., description="User's phone number")
    lang: str = Field("en", description="Language code: uz/ru/en")


class TelegramAuthSerializer(BaseModel):
    id: int = Field(..., description="Telegram user ID")
    first_name: str = Field(..., description="First name from Telegram")
    last_name: str | None = Field(None, description="Last name from Telegram")
    username: str | None = Field(None, description="Username from Telegram")
    photo_url: str | None = Field(None, description="Profile photo URL")
    auth_date: int = Field(..., description="Auth date timestamp")
    hash: str = Field(..., description="Telegram data signature")


class AuthResponseSerializer(BaseModel):
    """Serializer for authentication response."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    auth_type: str = Field(..., description="Auth type, e.g., Bearer")
