from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from redis.asyncio import Redis

from ...serializers.users import EmailUpdateSerializer, CheckOTPEmailSerializer
from services.users import VerificationService, UserService
from models.users import VerificationType
from utils.limiters import EmailUpdateLimiter
from utils.auth import get_current_user
from utils.i18n import get_translation
from utils.arq_pool import get_arq_redis
from config import REDIS_URL

router = APIRouter()
bearer = HTTPBearer()

# Initialize rate limiter with Redis client
redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
email_update_limiter = EmailUpdateLimiter(redis_client)

@router.post(
    "/email-update/", status_code=status.HTTP_200_OK
)
async def request_email_update(
    data: EmailUpdateSerializer,
    current=Depends(get_current_user),
    t: dict = Depends(get_translation),
    redis=Depends(get_arq_redis)
):
    """
    Handle email update request:
    1. Validate and normalize new email
    2. Check rate limits
    3. Send verification code
    4. Enqueue activity logging job
    5. Return success message
    """
    user_id = current.id
    new_email = data.email.lower().strip()

    # Check if email is already taken
    existing = await UserService.get_by_email(new_email)
    if existing and existing.id != user_id:
        raise HTTPException(status_code=400, detail=t["user_already_registered"])

    # Rate limit check
    if await email_update_limiter.is_blocked(new_email):
        raise HTTPException(status_code=429, detail=t["too_many_attempts"])
    await email_update_limiter.register_attempt(new_email)

    # Send OTP code
    try:
        await VerificationService.send_verification_code(
            email=new_email,
            verification_type=VerificationType.UPDATE_EMAIL,
            t=t
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else t["otp_resend_failed"]
        raise HTTPException(status_code=exc.status_code, detail=detail)

    # Enqueue activity log job
    await redis.enqueue_job(
        "log_user_activity", user_id=user_id, action="email_update_request"
    )

    return {"message": t["verification_sent"]}


@router.post(
    "/email-update/confirm/", status_code=status.HTTP_200_OK
)
async def confirm_email_update(
    data: CheckOTPEmailSerializer,
    current=Depends(get_current_user),
    t: dict = Depends(get_translation),
    redis=Depends(get_arq_redis)
):
    """
    Confirm email update using OTP:
    1. Verify OTP code
    2. Update user email
    3. Clear rate limiter
    4. Enqueue activity logging job
    5. Return confirmation message
    """
    user_id = current.id
    new_email = data.new_email.lower().strip()

    # Prevent duplicate email assignment
    existing = await UserService.get_by_email(new_email)
    if existing and existing.id != user_id:
        raise HTTPException(status_code=400, detail=t["user_already_registered"])

    # Verify OTP
    try:
        await VerificationService.verify_code(
            email=new_email,
            code=str(data.code),
            verification_type=VerificationType.UPDATE_EMAIL,
            user_id=user_id,
            t=t
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else t["otp_verification_failed"]
        raise HTTPException(status_code=exc.status_code, detail=detail)

    # Reset limiter and update user
    await email_update_limiter.register_attempt(new_email)
    await UserService.update_user(user_id, t, email=new_email)
    await VerificationService.delete_unused_codes(
        email=new_email,
        verification_type=VerificationType.UPDATE_EMAIL
    )

    # Enqueue activity log job
    await redis.enqueue_job(
        "log_user_activity", user_id=user_id, action="email_update_confirm"
    )

    return {"message": t["code_confirmed"]}