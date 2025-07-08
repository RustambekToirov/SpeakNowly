from fastadmin import TortoiseModelAdmin, register, WidgetType
from tortoise.exceptions import ValidationError as TortoiseValidationError
from fastadmin.api.exceptions import AdminApiException
from models import User
from models.tests import Writing, WritingPart1, WritingPart2, WritingStatus

@register(Writing)
class WritingAdmin(TortoiseModelAdmin):
    list_display = ("id", "user", "status", "start_time", "end_time")
    list_filter = ("status", "user")
    list_select_related = ("user",)
    search_fields = ()

    formfield_overrides = {
        "status":     (WidgetType.Select, {
            "options": [
                {"label": s.name.title(), "value": s.value}
                for s in WritingStatus
            ]
        }),
        "start_time": (WidgetType.DateTimePicker, {}),
        "end_time":   (WidgetType.DateTimePicker, {}),
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
            return await super().save_model(id, payload)
        except TortoiseValidationError as e:
            errors = {}
            for msg in e.args:
                if isinstance(msg, str) and ":" in msg:
                    fld, txt = msg.split(":", 1)
                    errors[fld.strip()] = txt.strip()
            detail = "; ".join(f"{k}: {v}" for k, v in errors.items())
            raise AdminApiException(status_code=400, detail=detail)

@register(WritingPart1)
class WritingPart1Admin(TortoiseModelAdmin):
    list_display = ("id", "writing")
    list_filter = ("writing",)
    list_select_related = ("writing",)
    search_fields = ()

    formfield_overrides = {
        "content":      (WidgetType.TextArea, {}),
        "diagram":      (WidgetType.Input, {}),
        "diagram_data": (WidgetType.TextArea, {}),
        "answer":       (WidgetType.TextArea, {}),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "writing":
            items = await Writing.all().values("id", "id")
            return (
                WidgetType.Select,
                {"options": [{"label": str(i["id"]), "value": i["id"]} for i in items]}
            )
        return await super().get_formfield_override(field_name)

    async def save_model(self, id: int | None, payload: dict) -> dict:
        try:
            return await super().save_model(id, payload)
        except TortoiseValidationError as e:
            errors = {}
            for msg in e.args:
                if isinstance(msg, str) and ":" in msg:
                    fld, txt = msg.split(":", 1)
                    errors[fld.strip()] = txt.strip()
            detail = "; ".join(f"{k}: {v}" for k, v in errors.items())
            raise AdminApiException(status_code=400, detail=detail)

@register(WritingPart2)
class WritingPart2Admin(TortoiseModelAdmin):
    list_display = ("id", "writing")
    list_filter = ("writing",)
    list_select_related = ("writing",)
    search_fields = ()

    formfield_overrides = {
        "content": (WidgetType.TextArea, {}),
        "answer":  (WidgetType.TextArea, {}),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "writing":
            items = await Writing.all().values("id", "id")
            return (
                WidgetType.Select,
                {"options": [{"label": str(i["id"]), "value": i["id"]} for i in items]}
            )
        return await super().get_formfield_override(field_name)

    async def save_model(self, id: int | None, payload: dict) -> dict:
        try:
            return await super().save_model(id, payload)
        except TortoiseValidationError as e:
            errors = {}
            for msg in e.args:
                if isinstance(msg, str) and ":" in msg:
                    fld, txt = msg.split(":", 1)
                    errors[fld.strip()] = txt.strip()
            detail = "; ".join(f"{k}: {v}" for k, v in errors.items())
            raise AdminApiException(status_code=400, detail=detail)
