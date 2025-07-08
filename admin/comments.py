from fastadmin import TortoiseModelAdmin, register, WidgetType
from tortoise.exceptions import ValidationError as TortoiseValidationError
from fastadmin.api.exceptions import AdminApiException
from models import User
from models.comments import Comment, CommentStatus


@register(Comment)
class CommentAdmin(TortoiseModelAdmin):
    list_display = (
        "id", "user", "rate", "status", "text", "created_at",
    )
    list_filter = ("status", "user")
    list_select_related = ("user",)
    search_fields = ("text",)

    formfield_overrides = {
        "rate":   (WidgetType.InputNumber, {"min": 1, "max": 5, "step": 0.5}),
        "status": (WidgetType.Select, {
            "options": [
                {"label": "Active",   "value": CommentStatus.ACTIVE.value},
                {"label": "Inactive", "value": CommentStatus.INACTIVE.value},
            ]
        }),
        "text":   (WidgetType.TextArea, {}),
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
        # Custom rate validation
        rate = payload.get("rate")
        if rate is not None and not (1 <= rate <= 5):
            raise AdminApiException(status_code=400, detail="Rate must be between 1 and 5")

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
