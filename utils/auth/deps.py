from fastapi import Depends, HTTPException, status, Request
from utils.auth.auth import get_current_user
from utils.i18n import get_translation


def audit_action(action: str):
    """
    Creates dependency that logs user action.
    """
    async def wrapper(request: Request, user=Depends(get_current_user)):
        return user
    return wrapper

async def active_user(user=Depends(get_current_user), t=Depends(get_translation)):
    """
    Ensures user is active.
    """
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=t.get("inactive_user", "User is inactive")
        )
    return user

async def admin_required(user=Depends(get_current_user), t=Depends(get_translation)):
    """
    Ensures user has admin privileges.
    """
    if not (user.is_staff and user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=t.get("permission_denied", "Permission denied")
        )
    return user