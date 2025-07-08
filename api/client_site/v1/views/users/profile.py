from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
import aiofiles
import pathlib
from uuid import uuid4

from ...serializers.users import ProfileSerializer, ProfilePasswordUpdateSerializer
from services.users import UserService
from utils.auth import get_current_user
from utils.i18n import get_translation
from utils.arq_pool import get_arq_redis

router = APIRouter()

@router.get(
    "/me/",
    response_model=ProfileSerializer,
    status_code=status.HTTP_200_OK
)
async def get_profile(
    current_user = Depends(get_current_user),
    t: dict = Depends(get_translation)
) -> ProfileSerializer:
    """
    Retrieve the current user's profile:
    1. Ensure the user is active.
    2. Fetch related tariff data.
    3. Return the serialized profile.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=t["inactive_user"]
        )

    await current_user.fetch_related("tariff")

    return ProfileSerializer(
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        age=current_user.age,
        photo=current_user.photo,
        tokens=current_user.tokens,
        is_premium=current_user.is_premium,
        tariff_id=current_user.tariff.id if current_user.tariff else None
    )

@router.put(
    "/me/",
    response_model=ProfileSerializer,
    status_code=status.HTTP_200_OK
)
async def update_profile(
    first_name: str = Form(None),
    last_name: str = Form(None),
    age: int = Form(None),
    photo: UploadFile = File(None),
    current_user = Depends(get_current_user),
    t: dict = Depends(get_translation),
    redis = Depends(get_arq_redis)
) -> ProfileSerializer:
    """
    Update the current user's profile and optionally upload a photo:
    1. Validate that the user is active.
    2. Build a dict of fields to update.
    3. Save the uploaded photo asynchronously and add its URL.
    4. Persist changes in the database.
    5. Fetch related tariff data.
    6. Enqueue an activity log job.
    7. Return the updated profile.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=t["inactive_user"]
        )

    # Prepare fields for update
    update_fields = {}
    if first_name is not None:
        update_fields["first_name"] = first_name
    if last_name is not None:
        update_fields["last_name"] = last_name
    if age is not None:
        if age < 0 or age > 120:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=t.get("invalid_age", "Age must be between 0 and 120")
            )
        update_fields["age"] = age

    # Handle photo upload
    if photo is not None:
        if photo.content_type not in ("image/jpeg", "image/png", "image/gif"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image type"
            )

        file_ext = pathlib.Path(photo.filename).suffix
        save_dir = pathlib.Path("media/user_photos") / str(current_user.id)
        save_dir.mkdir(parents=True, exist_ok=True)

        file_name = f"{uuid4()}{file_ext}"
        file_path = save_dir / file_name

        content = await photo.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty"
            )

        # Write file asynchronously
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        # Set photo URL for update
        update_fields["photo"] = f"/media/user_photos/{current_user.id}/{file_name}"

    # Update user record
    updated_user = await UserService.update_user(
        current_user.id,
        t,
        **update_fields
    )

    # Refresh related data and log activity
    await updated_user.fetch_related("tariff")
    await redis.enqueue_job(
        "log_user_activity",
        user_id=current_user.id,
        action="profile_update"
    )

    # Return updated profile using serializer
    return ProfileSerializer.from_orm(updated_user)

@router.put(
    "/me/password/",
    status_code=status.HTTP_200_OK
)
async def update_password(
    data: ProfilePasswordUpdateSerializer,
    current_user = Depends(get_current_user),
    t: dict = Depends(get_translation),
    redis = Depends(get_arq_redis)
) -> dict:
    """
    Change the current user's password:
    1. Validate that the user is active.
    2. Verify the old password.
    3. Update to the new password in the DB.
    4. Enqueue an activity log job.
    5. Return a success message.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=t["inactive_user"]
        )

    if not current_user.check_password(data.old_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )

    await UserService.change_password(
        current_user.id,
        data.new_password,
        t
    )

    await redis.enqueue_job(
        "log_user_activity",
        user_id=current_user.id,
        action="password_update"
    )

    return {"message": t["password_updated"]}