from fastapi import APIRouter, HTTPException, status, Depends
from redis.asyncio import Redis

from ...serializers.users import ForgetPasswordSerializer, ResetPasswordSerializer
from services.users import VerificationService, UserService
from models.users import VerificationType
from utils.limiters import get_forget_password_limiter
from utils.i18n import get_translation
from utils.arq_pool import get_arq_redis
from config import REDIS_URL

router = APIRouter()
redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
forget_password_limiter = get_forget_password_limiter(redis_client)

@router.post(
    "/forget-password/", status_code=status.HTTP_200_OK
)
async def request_password_reset(
    data: ForgetPasswordSerializer,
    t: dict = Depends(get_translation),
    redis=Depends(get_arq_redis)
):
    """
    Request password reset OTP:
    - Validate user existence
    - Rate limit
    - Send verification code
    - Enqueue activity log
    - Return response
    """
    normalized_email = data.email.lower().strip()

    # Check user
    user = await UserService.get_by_email(normalized_email)
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail=t["user_not_found"])

    # Rate limit check
    if await forget_password_limiter.is_blocked(normalized_email):
        raise HTTPException(status_code=429, detail=t["too_many_attempts"])
    await forget_password_limiter.register_attempt(normalized_email)

    # Send OTP code
    try:
        await VerificationService.send_verification_code(
            email=normalized_email,
            verification_type=VerificationType.FORGET_PASSWORD,
            t=t
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else t["otp_resend_failed"]
        raise HTTPException(status_code=exc.status_code, detail=detail)

    # Enqueue activity log job
    await redis.enqueue_job(
        "log_user_activity", user_id=user.id, action="forget_password_request"
    )

    return {"message": t["verification_sent"]}


@router.post(
    "/forget-password/confirm/", status_code=status.HTTP_200_OK
)
async def confirm_password_reset(
    data: ResetPasswordSerializer,
    t: dict = Depends(get_translation),
    redis=Depends(get_arq_redis)
):
    """
    Confirm password reset OTP and set new password:
    - Verify OTP
    - Reset limiter
    - Change password
    - Enqueue activity log
    """
    normalized_email = data.email.lower().strip()

    # Verify OTP and retrieve user
    user = await VerificationService.verify_code(
        email=normalized_email,
        code=str(data.code),
        verification_type=VerificationType.FORGET_PASSWORD,
        t=t
    )

    # Reset limiter and update password
    await forget_password_limiter.register_attempt(normalized_email)
    await UserService.change_password(user.id, data.new_password, t)
    await VerificationService.delete_unused_codes(
        email=normalized_email,verification_type=VerificationType.FORGET_PASSWORD
    )

    # Enqueue activity log job
    await redis.enqueue_job(
        "log_user_activity", user_id=user.id, action="forget_password_confirm"
    )

    return {"message": t["password_updated"]}