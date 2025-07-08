from fastapi import HTTPException

import logging
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    EMAIL_FROM
)

logger = logging.getLogger("email_service")


class EmailService:
    """
    Provides asynchronous email sending capabilities with support for 
    plain text and HTML content via SMTP.
    """

    @staticmethod
    async def send_email(
        subject: str,
        recipients: list[str],
        body: str = None,
        html_body: str = None,
    ) -> dict:
        """
        Send an email:
        1. Validate input parameters.
        2. Prepare MIME multipart message.
        3. Attach plain text and/or HTML content.
        4. Connect to SMTP server with TLS.
        5. Send email and return status.
        6. Handle errors and log failures.
        """
        # 1. Validate input
        if not body and not html_body:
            raise HTTPException(status_code=400, detail="Email body is required")

        # 2. Prepare message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = ", ".join(recipients)

        # 3. Attach content
        if body:
            msg.attach(MIMEText(body, "plain"))
        if html_body:
            msg.attach(MIMEText(html_body, "html"))

        # 4-5. Send email via SMTP
        try:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, recipients, msg.as_string())
            server.quit()
            return {"status": "sent"}
        # 6. Handle errors
        except Exception as e:
            logger.error(f"SMTP send error: {e}")
            raise HTTPException(status_code=503, detail="Failed to send email")
