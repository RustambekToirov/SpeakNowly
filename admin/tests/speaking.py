from fastadmin import TortoiseModelAdmin, register, WidgetType
from tortoise.exceptions import ValidationError as TortoiseValidationError
from fastadmin.api.exceptions import AdminApiException
from models import User
from models.tests import Speaking, SpeakingQuestion, SpeakingAnswer, SpeakingPart, SpeakingStatus

@register(Speaking)
class SpeakingAdmin(TortoiseModelAdmin):
    list_display = ("id", "user", "status", "start_time", "end_time")
    list_filter = ("status", "user")
    list_select_related = ("user",)
    search_fields = ()

    formfield_overrides = {
        "status": (WidgetType.Select, {
            "options": [
                {"label": s.name.title(), "value": s.value}
                for s in SpeakingStatus
            ]
        }),
        "start_time": (WidgetType.DateTimePicker, {}),
        "end_time": (WidgetType.DateTimePicker, {}),
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

@register(SpeakingQuestion)
class SpeakingQuestionAdmin(TortoiseModelAdmin):
    list_display = ("id", "speaking", "part", "title")
    list_filter = ("part",)
    list_select_related = ("speaking",)
    search_fields = ("title",)

    formfield_overrides = {
        "part": (WidgetType.Select, {
            "options": [
                {"label": p.name.replace("_", " ").title(), "value": p.value}
                for p in SpeakingPart
            ]
        }),
        "title": (WidgetType.Input, {}),
        "content": (WidgetType.TextArea, {}),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "speaking":
            items = await Speaking.all().values("id", "id")
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
