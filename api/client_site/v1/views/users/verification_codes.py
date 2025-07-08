from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from typing import Dict
from redis.asyncio import Redis

from ...serializers.users import CheckOTPSerializer, CheckOTPResponseSerializer
from services.users import VerificationService, UserService
from models.users import VerificationType
from utils.auth import create_access_token, create_refresh_token
from utils.i18n import get_translation
from utils.arq_pool import get_arq_redis
from config import REDIS_URL

router = APIRouter()
bearer = HTTPBearer()

@router.post(
    "/verify-otp/",
    response_model=CheckOTPResponseSerializer,
    status_code=status.HTTP_200_OK
)
async def verify_otp(
    data: CheckOTPSerializer,
    t: Dict[str, str] = Depends(get_translation),
    redis: Redis = Depends(get_arq_redis)
) -> CheckOTPResponseSerializer:
    """
    Verify a one-time password (OTP) and return JWT tokens upon success:
    1. Validate input and confirm OTP code.
    2. If registration, mark the user as verified.
    3. Generate access and refresh tokens.
    4. Delete any unused codes for this email and type.
    5. Enqueue an activity log job.
    6. Return a success message with tokens.
    """
    # Step 1: Verify the OTP code
    try:
        user = await VerificationService.verify_code(
            email=data.email,
            code=str(data.code),
            verification_type=data.verification_type,
            t=t
        )
    except HTTPException as exc:
        detail = (
            exc.detail if isinstance(exc.detail, str)
            else t.get("otp_verification_failed", "Verification failed.")
        )
        raise HTTPException(status_code=exc.status_code, detail=detail)

    # Step 2: Mark user verified if registering
    if data.verification_type == VerificationType.REGISTER:
        await UserService.update_user(user.id, t, is_verified=True)

    # Step 3: Generate tokens
    access_token = await create_access_token(subject=str(user.id), email=user.email)
    refresh_token = await create_refresh_token(subject=str(user.id), email=user.email)

    # Step 4: Delete unused verification codes
    await VerificationService.delete_unused_codes(
        email=data.email,
        verification_type=data.verification_type
    )

    # Step 5: Enqueue activity log job
    await redis.enqueue_job(
        "log_user_activity",
        user_id=user.id,
        action=f"verify_{data.verification_type}"
    )

    # Step 6: Return response with tokens
    return CheckOTPResponseSerializer(
        message=t.get("code_confirmed", "Verification successful."),
        access_token=access_token,
        refresh_token=refresh_token
    )
