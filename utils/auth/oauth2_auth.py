from typing import Literal
from fastapi import HTTPException, Request
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from services.users import UserService
from utils.auth.apple_auth import decode_apple_id_token
from utils.auth.auth import create_access_token, create_refresh_token
from models.users.users import User
from config import GOOGLE_CLIENT_ID
from models.notifications import Message, MessageType
import asyncio
import json

async def oauth2_sign_in(
    token: str,
    auth_type: Literal["google", "apple"],
    request: Request = None,
    client_id: str = None,
    lang: str = "en"
) -> dict:
    """
    Authenticates user via OAuth2 and returns tokens.
    """
    email = None
    first_name = None
    last_name = None
    photo = None

    if auth_type == "google":
        try:
            payload = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: google_id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID)
            )
            email = payload.get("email")
            first_name = payload.get("given_name")
            last_name = payload.get("family_name")
            photo = payload.get("picture")
            if not email:
                raise HTTPException(status_code=403, detail="Email not provided by Google token")
        except ValueError:
            raise HTTPException(status_code=403, detail="Invalid Google ID token")

    elif auth_type == "apple":
        if request is None:
            raise HTTPException(status_code=400, detail="Require request to parse Apple 'user' field")
        try:
            payload = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: decode_apple_id_token(token, client_id)
            )
            email = payload.get("email")
            if not email:
                raise HTTPException(status_code=403, detail="Email not provided by Apple token")

            form = await request.form()
            user_json = form.get("user")
            if user_json:
                try:
                    user_data = json.loads(user_json)
                    name = user_data.get("name", {})
                    first_name = name.get("firstName")
                    last_name = name.get("lastName")
                except json.JSONDecodeError:
                    pass

        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=403, detail="Invalid Apple ID token")

    else:
        raise HTTPException(status_code=400, detail="Unsupported authentication provider")

    user = await User.get_or_none(email=email)
    created = False
    if not user:
        user = User(
            email=email,
            is_verified=True,
            is_active=True,
            first_name=first_name,
            last_name=last_name,
            photo=photo,
        )
        user.set_password("")  # Empty password for OAuth users
        await user.save()
        created = True

        await UserService.assign_default_tariff(user)

    # Welcome message
    if created:
        titles = {"en": "Welcome", "ru": "Добро пожаловать", "uz": "Xush kelibsiz"}
        descriptions = {
            "en": "Please update your email and password in your profile.",
            "ru": "Пожалуйста, обновите email и пароль в профиле.",
            "uz": "Profilingizda email va parolni yangilang."
        }
        contents = {
            "en": (
                "<div>"
                "<p>🇬🇧 Welcome to SpeakNowly! Please set your email and password in your profile for full access.</p>"
                "</div>"
            ),
            "ru": (
                "<div>"
                "<p>🇷🇺 Добро пожаловать в SpeakNowly! Пожалуйста, задайте email и пароль в профиле для полного доступа.</p>"
                "</div>"
            ),
            "uz": (
                "<div>"
                "<p>🇺🇿 SpeakNowly'ga xush kelibsiz! To'liq kirish uchun profilingizda email va parolni belgilang.</p>"
                "</div>"
            ),
        }
        title = titles.get(lang, titles["en"])
        description = descriptions.get(lang, descriptions["en"])
        content = contents.get(lang, contents["en"])

        await Message.create(
            user=user,
            type=MessageType.SITE,
            title=title,
            description=description,
            content=content,
        )

    access_token = await create_access_token(subject=str(user.id), email=user.email)
    refresh_token = await create_refresh_token(subject=str(user.id), email=user.email)
    return {"access_token": access_token, "refresh_token": refresh_token}
