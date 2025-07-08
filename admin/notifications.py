from fastadmin import TortoiseModelAdmin, register, WidgetType
from tortoise.exceptions import ValidationError as TortoiseValidationError
from fastadmin.api.exceptions import AdminApiException
from models import User
from models.notifications import Message, ReadStatus, MessageType
from services.users.email_service import EmailService
from datetime import datetime


@register(Message)
class MessageAdmin(TortoiseModelAdmin):
    list_display = ("id", "user", "type", "title", "created_at")
    list_filter = ("user",)
    list_select_related = ("user",)
    search_fields = ("title",)

    formfield_overrides = {
        "type": (WidgetType.Select, {
            "options": [
                {"label": "Mail",        "value": MessageType.MAIL.value},
                {"label": "Site",        "value": MessageType.SITE.value},
                {"label": "Mail & Site", "value": MessageType.MAIL_SITE.value},
            ]
        }),
        "title":       (WidgetType.Input, {}),
        "description": (WidgetType.TextArea, {}),
        "content":     (WidgetType.TextArea, {}),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "user":
            users = await User.all().values("id", "email")
            return (
                WidgetType.Select,
                {"options": [{"label": u["email"], "value": u["id"]} for u in users]}
            )
        return await super().get_formfield_override(field_name)

    async def save_model(self, id: int | None, payload: dict) -> dict:
        try:
            result = await super().save_model(id, payload)
            message = await Message.get(id=result["id"]).prefetch_related("user")

            if (
                message.type in (MessageType.MAIL, MessageType.MAIL_SITE)
                and message.user and message.user.email
            ):
                subject = message.title
                body = message.description or message.content or ""
                html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
  <style>
    body {{font-family:Helvetica,Arial,sans-serif;margin:0;padding:0;background:#f9f9f9;color:#333}}
    .container {{max-width:600px;margin:2rem auto;background:#fff;border-radius:8px;
      box-shadow:0 4px 8px rgba(0,0,0,0.1);overflow:hidden}}
    .header {{background:#4F6AFC;text-align:center;padding:20px;color:#fff}}
    .header h1 {{margin:0;font-size:24px;letter-spacing:2px}}
    .content {{padding:20px 30px}}
    .content h2 {{margin-top:0}}
    .content p {{line-height:1.6;margin-bottom:16px}}
    .footer {{text-align:center;padding:10px;font-size:12px;color:#888;
      background:#f9f9f9;border-top:1px solid #ddd}}
  </style>
</head>
<body>
  <div class="container">
    <div class="header"><h1>SPEAKNOWLY</h1></div>
    <div class="content">
      <h2>{message.title}</h2>
      <p>{message.description or ""}</p>
      <div>{message.content or ""}</div>
    </div>
    <div class="footer">
      &copy; {datetime.now().year} Speaknowly. All rights reserved.
    </div>
  </div>
</body>
</html>
"""
                try:
                    await EmailService.send_email(
                        subject=subject,
                        recipients=[message.user.email],
                        body=body,
                        html_body=html_body
                    )
                except Exception as e:
                    print("❌ Ошибка при отправке email:", e)

            return result
        except TortoiseValidationError as e:
            errors: dict[str, str] = {}
            for msg in e.args:
                if isinstance(msg, str) and ":" in msg:
                    fld, text = msg.split(":", 1)
                    errors[fld.strip()] = text.strip()
            detail = "; ".join(f"{k}: {v}" for k, v in errors.items())
            raise AdminApiException(status_code=400, detail=detail)


@register(ReadStatus)
class ReadStatusAdmin(TortoiseModelAdmin):
    list_display = ("id", "user", "message", "read_at")
    list_select_related = ("user", "message")
    search_fields = ("user__email", "message__title")

    formfield_overrides = {
        "read_at": (WidgetType.DateTimePicker, {}),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "user":
            users = await User.all().values("id", "email")
            return (
                WidgetType.Select,
                {"options": [{"label": u["email"], "value": u["id"]} for u in users]}
            )
        if field_name == "message":
            msgs = await Message.all().values("id", "title")
            return (
                WidgetType.Select,
                {"options": [{"label": m["title"], "value": m["id"]} for m in msgs]}
            )
        return await super().get_formfield_override(field_name)

    async def save_model(self, id: int | None, payload: dict) -> dict:
        try:
            return await super().save_model(id, payload)
        except TortoiseValidationError as e:
            errors: dict[str, str] = {}
            for msg in e.args:
                if isinstance(msg, str) and ":" in msg:
                    fld, text = msg.split(":", 1)
                    errors[fld.strip()] = text.strip()
            detail = "; ".join(f"{k}: {v}" for k, v in errors.items())
            raise AdminApiException(status_code=400, detail=detail)
