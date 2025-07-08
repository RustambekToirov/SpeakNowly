from fastapi import APIRouter, HTTPException, status, Depends
from redis.asyncio import Redis

from ...serializers.users import RegisterSerializer, RegisterResponseSerializer
from services.users import VerificationService, UserService
from models.users import VerificationType
from utils.limiters import get_register_limiter
from utils.i18n import get_translation
from utils.arq_pool import get_arq_redis
from config import REDIS_URL

router = APIRouter()
# Initialize rate limiter for registration attempts
redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
register_limiter = get_register_limiter(redis_client)

@router.post(
    "/register/",
    response_model=RegisterResponseSerializer,
    status_code=status.HTTP_201_CREATED
)
async def register(
    data: RegisterSerializer,
    t: dict = Depends(get_translation),
    redis=Depends(get_arq_redis)
) -> RegisterResponseSerializer:
    """
    Register a new user:
    - Normalize email input
    - Enforce registration rate limit
    - Prevent duplicate verified accounts
    - Create or reuse unverified user
    - Send email verification code
    - Record attempt and enqueue activity log
    - Return success message
    """
    email = data.email.lower().strip()

    # Check rate limit for registration
    if await register_limiter.is_blocked(email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=t["too_many_attempts"]
        )

    # Prevent re-registration if already verified
    existing_user = await UserService.get_by_email(email)
    if existing_user and existing_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=t["user_already_registered"]
        )

    # Create new user or reuse unverified profile
    if not existing_user:
        user = await UserService.register(email=email, password=data.password, t=t)
        first_time = True
    else:
        user = existing_user
        first_time = False

    # Send verification code
    try:
        await VerificationService.send_verification_code(
            email=email,
            verification_type=VerificationType.REGISTER,
            t=t
        )
    except HTTPException:
        # Propagate verification errors
        raise

    # Record attempt in limiter
    await register_limiter.register_attempt(email)

    # Enqueue activity logging job
    await redis.enqueue_job(
        "log_user_activity",
        user_id=user.id,
        action="register"
    )

    # Choose appropriate message key
    message_key = "verification_sent" if first_time else "verification_resent"
    return RegisterResponseSerializer(message=t[message_key])
