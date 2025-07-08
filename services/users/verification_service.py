import asyncio
from fastapi import HTTPException
from random import randint
from datetime import datetime, timezone, timedelta
from arq import create_pool
from arq.connections import RedisSettings

from services.users import UserService
from models.users import VerificationCode, VerificationType, User
from utils.arq_pool import get_redis_settings

CODE_TTL = timedelta(minutes=10)

class VerificationService:
    """
    Handles email verification for registration, password reset, and email update flows using ARQ.
    Enforces code TTL and resend limits, and sends emails via Redis queue.
    """

    @staticmethod
    async def send_verification_code(email: str, verification_type: str, t: dict) -> str:
        """
        Generate and send a verification code:
        1. Validate verification_type.
        2. Enforce resend limit.
        3. Prevent sending if user already verified (REGISTER).
        4. Delete old unused codes.
        5. Generate 5-digit code.
        6. Prepare plain and HTML email bodies with localization.
        7. Enqueue send_email task via ARQ.
        8. Persist the code in the database.
        9. Return the generated code.
        """
        # 1. Validate verification type
        try:
            otp_type = VerificationType(verification_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=t.get("invalid_verification_type", "Invalid verification type"))

        # 2. Resend limiter check
        if await VerificationCode.is_resend_blocked(email, otp_type):
            raise HTTPException(status_code=429, detail=t.get("too_many_attempts", "Too many attempts, please try again later"))

        # 3. Prevent sending if already verified during registration
        user = await UserService.get_by_email(email)
        if otp_type == VerificationType.REGISTER and user and user.is_verified:
            raise HTTPException(status_code=400, detail=t.get("user_already_registered", "Email already registered"))

        # 4. Delete old unused codes
        await VerificationCode.filter(
            email=email,
            verification_type=otp_type,
            is_used=False,
            is_expired=False
        ).delete()

        # 5. Generate code
        code = f"{randint(10000, 99999)}"

        # 6. Prepare email content
        subject = "Your Verification Code"
        body = f"Your verification code is: {code}\n\nThis code is valid for 10 minutes."
        html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Verify Your Email</title>
  <style>
    body {{
      font-family: Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 0;
      background-color: #f9f9f9;
      color: #333333;
    }}
    .container {{
      max-width: 600px;
      margin: 2rem auto;
      background-color: #ffffff;
      border-radius: 8px;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
      overflow: hidden;
    }}
    .header {{
      background-color: #4F6AFC;
      text-align: center;
      padding: 20px;
      color: #ffffff;
    }}
    .header .website {{
      font-size: 16px;
      margin-top: 10px;
      font-weight: bold;
    }}
    .content {{
      padding: 20px 30px;
      text-align: center;
    }}
    .content h1 {{
      color: #4F6AFC;
      font-size: 24px;
      margin-bottom: 16px;
    }}
    .content p {{
      margin: 0 0 16px;
      line-height: 1.6;
    }}
    .content .code {{
      font-size: 24px;
      font-weight: bold;
      color: #333333;
      padding: 10px 20px;
      background-color: #f4f4f4;
      border-radius: 4px;
      display: inline-block;
      margin: 20px 0;
    }}
    .footer {{
      text-align: center;
      padding: 10px;
      font-size: 12px;
      color: #888888;
      background-color: #f9f9f9;
      border-top: 1px solid #dddddd;
    }}
    .footer a {{
      color: #4F6AFC;
      text-decoration: none;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="website">
        <h1 style="color: #ffffff; font-size: 32px; font-weight: bold; margin: 0; letter-spacing: 3px; text-transform: uppercase;">
          <a href="https://speaknowly.com" style="color: #ffffff; text-decoration: none; display: block;">SPEAKNOWLY</a>
        </h1>
      </div>
    </div>
    <div class="content">
      <h1>{otp_type.name.replace('_', ' ').capitalize()}</h1>
      <p>Please use the following verification code. This code is valid for 10 minutes:</p>
      <p class="code">{code}</p>
      <p>If you did not request this code, you can safely ignore this email.</p>
      <p>Thank you,<br />The Speaknowly Team</p>
    </div>
    <div class="footer">
      &copy; {datetime.now().year} Speaknowly. All rights reserved.
    </div>
  </div>
</body>
</html>
"""

        # 7. Enqueue email
        redis_settings = get_redis_settings()
        redis = await create_pool(redis_settings)
        await redis.enqueue_job(
            "send_email",
            subject=subject,
            recipients=[email],
            body=body,
            html_body=html_body
        )
        await redis.close()

        # 8. Persist code record
        now = datetime.now(timezone.utc)
        await VerificationCode.create(
            email=email,
            verification_type=otp_type,
            code=int(code),
            is_used=False,
            is_expired=False,
            created_at=now,
            updated_at=now
        )

        # 9. Return generated code
        return code

    @staticmethod
    async def verify_code(
        email: str,
        code: str,
        verification_type: str,
        t: dict,
        user_id: int = None
    ) -> User:
        """
        Verify the code and return the User:
        1. Validate verification type.
        2. Fetch latest unused/unexpired code.
        3. Check if code has expired based on TTL.
        4. Validate code matches.
        5. Mark code as used.
        6. Retrieve and return user.
        """
        # 1. Validate verification type
        try:
            otp_type = VerificationType(verification_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=t.get("invalid_verification_type", "Invalid verification type"))

        # 2. Fetch the latest unused code
        record = await VerificationCode.filter(
            email=email,
            verification_type=otp_type,
            is_used=False,
            is_expired=False
        ).order_by("-updated_at").first()
        if not record:
            raise HTTPException(status_code=400, detail=t.get("code_not_found", "Code not found or used"))

        # 3. Check if code has expired based on TTL
        if datetime.now(timezone.utc) - record.updated_at > CODE_TTL:
            record.is_expired = True
            await record.save()
            raise HTTPException(status_code=400, detail=t.get("code_expired", "Verification code expired"))

        # 4. Validate code matches
        if str(record.code) != str(code):
            raise HTTPException(status_code=400, detail=t.get("invalid_code", "Invalid verification code"))

        # 5. Mark code as used
        record.is_used = True
        await record.save()

        # 6. Retrieve and return user
        if otp_type == VerificationType.UPDATE_EMAIL and user_id:
            user = await UserService.get_by_id(user_id)
        else:
            user = await UserService.get_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail=t.get("user_not_found", "User not found"))
        return user

    @staticmethod
    async def delete_unused_codes(email: str, verification_type: str) -> None:
        """
        Delete unused verification codes:
        1. Validate verification type.
        2. Remove all unused and unexpired codes for the email.
        """
        # 1. Validate verification type
        try:
            otp_type = VerificationType(verification_type)
        except ValueError:
            return
            
        # 2. Remove all unused and unexpired codes
        await VerificationCode.filter(
            email=email,
            verification_type=otp_type,
            is_used=False,
            is_expired=False
        ).delete()
