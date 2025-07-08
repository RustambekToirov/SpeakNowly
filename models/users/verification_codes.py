from fastapi import HTTPException
from tortoise.validators import MinValueValidator, MaxValueValidator
from tortoise import fields
from ..base import BaseModel
import random
from datetime import datetime, timezone, timedelta
from enum import Enum

class VerificationType(str, Enum):
    """Enumeration for different types of verification."""
    REGISTER = "register"
    LOGIN = "login"
    RESET_PASSWORD = "reset_password"
    FORGET_PASSWORD = "forget_password"
    UPDATE_EMAIL = "update_email"

class VerificationCode(BaseModel):
    """Model representing a verification code for user actions."""
    email = fields.CharField(max_length=255, null=True, description="Email")
    user = fields.ForeignKeyField('models.User', related_name='verification_codes', null=True, description="User")
    verification_type = fields.CharEnumField(VerificationType, description="Verification Type")
    code = fields.IntField(null=True, description="Code", validators=[MinValueValidator(10000), MaxValueValidator(99999)])
    is_used = fields.BooleanField(default=False, description="Used")
    is_expired = fields.BooleanField(default=False, description="Expired")
    created_at = fields.DatetimeField(auto_now_add=True, description="Created at")

    class Meta:
        table = "verification_codes"
        verbose_name = "Verification Code"
        verbose_name_plural = "Verification Codes"
        unique_together = ("email", "verification_type")

    def __str__(self):
        user_name = self.user.get_full_name() if self.user else "Unknown User"
        return f"{user_name} - {self.verification_type} - {self.code} - {self.is_used} - {self.is_expired}"

    def is_code_expired(self) -> bool:
        """Checks if the code has expired based on TTL."""
        ttl = timedelta(minutes=10)  # Use the same TTL as in service
        return self.is_expired or (datetime.now(timezone.utc) - self.created_at > ttl)

    @staticmethod
    async def is_resend_blocked(email: str, verification_type: VerificationType) -> bool:
        """Check if the resend limit is reached."""
        time_limit = datetime.now(timezone.utc) - timedelta(minutes=1)
        recent_code = await VerificationCode.filter(
            email=email,
            verification_type=verification_type,
            updated_at__gte=time_limit,
        ).first()
        return recent_code is not None

    @staticmethod
    def generate_otp() -> int:
        """Generates a 5-digit OTP."""
        return random.randint(10000, 99999)

    @staticmethod
    async def update_or_create_verification_code(user, data, code):
        if await VerificationCode.is_resend_blocked(data.email, VerificationType.REGISTER):
            raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")

        # Generate and save the verification code
        code = random.randint(10000, 99999)
        await VerificationCode.update_or_create(
            user_id=user.id,
            email=data.email,
            verification_type=VerificationType.REGISTER,
            defaults={"code": code, "is_used": False, "is_expired": False},
        )
