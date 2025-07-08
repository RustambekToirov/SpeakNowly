from fastapi import APIRouter, Depends, status
from utils.auth import get_current_user
from utils.i18n import get_translation
from utils.arq_pool import get_arq_redis

router = APIRouter()

@router.post(
    "/logout/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def logout(
    current_user=Depends(get_current_user),
    t: dict = Depends(get_translation),
    redis=Depends(get_arq_redis)
):
    """
    Log out current user and enqueue activity log job.
    """
    await redis.enqueue_job(
        "log_user_activity", user_id=current_user.id, action="logout"
    )
    return {"message": t["logout_successful"]}