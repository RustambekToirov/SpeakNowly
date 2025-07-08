from typing import Dict, Any
from fastapi import HTTPException
from hashlib import sha256
from hmac import HMAC

from utils.auth.auth import create_access_token, create_refresh_token
from models.users.users import User
from config import TELEGRAM_BOT_TOKEN

async def telegram_sign_in(
    telegram_data: Dict[str, Any],
    email: str | None,
    phone: str | None = None
) -> Dict[str, str]:
    """
    Authenticate or link user via Telegram Login Widget and phone verification:
    - Validates Telegram-sent data with HMAC-SHA256
    - Finds or creates a User record by email
    - Associates Telegram ID and optional phone
    - Generates JWT access and refresh tokens
    """
    # Extract and verify hash
    received_hash = telegram_data.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=400, detail="Missing hash from Telegram data")

    # Prepare data check string
    data_check_items = sorted(telegram_data.items())
    data_check_string = "\n".join(f"{k}={v}" for k, v in data_check_items)

    # Calculate HMAC-SHA256
    secret_key = sha256(TELEGRAM_BOT_TOKEN.encode()).digest()
    calculated_hash = HMAC(secret_key, data_check_string.encode(), sha256).hexdigest()

    if calculated_hash != received_hash:
        raise HTTPException(status_code=400, detail="Invalid Telegram data signature")

    # Extract Telegram user ID
    tg_id = telegram_data.get("id")
    if tg_id is None:
        raise HTTPException(status_code=400, detail="Telegram ID not provided")

    if not email:
        email = f"telegram_{tg_id}@speaknowly.com"

    user = await User.get_or_none(email=email)
    if not user:
        user = User(
            email=email,
            first_name=telegram_data.get("first_name"),
            last_name=telegram_data.get("last_name"),
            photo=telegram_data.get("photo_url"),
            telegram_id=str(tg_id),
            is_verified=True,
            is_active=True
        )
        if phone:
            user.phone = phone
        await user.save()
    else:
        user.telegram_id = str(tg_id)
        if phone:
            user.phone = phone
        user.first_name = user.first_name or telegram_data.get("first_name")
        user.last_name = user.last_name or telegram_data.get("last_name")
        user.photo = user.photo or telegram_data.get("photo_url")
        await user.save()

    # Generate JWT tokens
    access_token = await create_access_token(subject=str(user.id), email=user.email)
    refresh_token = await create_refresh_token(subject=str(user.id), email=user.email)

    return {"access_token": access_token, "refresh_token": refresh_token}
