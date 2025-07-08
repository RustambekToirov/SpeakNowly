from fastadmin import TortoiseModelAdmin, register, WidgetType
from tortoise.exceptions import ValidationError as TortoiseValidationError
from fastadmin.api.exceptions import AdminApiException
from models import User, Reading, ReadingPassage, ReadingQuestion, ReadingVariant, ReadingAnswer
from models.tests.constants import Constants

@register(ReadingPassage)
class ReadingPassageAdmin(TortoiseModelAdmin):
    list_display    = ("id", "title", "level", "number")
    list_filter     = ("level",)
    search_fields   = ("title",)
    formfield_overrides = {
        "title"  : (WidgetType.Input, {}),
        "text"   : (WidgetType.TextArea, {}),
        "skills" : (WidgetType.TextArea, {}),
        "level"  : (WidgetType.Select, {
            "options": [
                {"label": l.name.title(), "value": l.value}
                for l in Constants.PassageLevel
            ]
        }),
    }

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
from fastadmin import TortoiseModelAdmin, register, WidgetType
from tortoise.exceptions import ValidationError as TortoiseValidationError
from fastadmin.api.exceptions import AdminApiException
from models import ReadingQuestion, ReadingPassage
from models.tests.constants import Constants

@register(ReadingQuestion)
class ReadingQuestionAdmin(TortoiseModelAdmin):
    list_display        = ("id", "passage", "text", "type", "score")
    list_filter         = ("passage", "type")
    list_select_related = ("passage",)
    search_fields       = ()

    formfield_overrides = {
        "text":  (WidgetType.TextArea, {}),
        "score": (WidgetType.InputNumber, {}),
        "type":  (WidgetType.Select, {
            "options": [
                {"label": t.name.replace("_", " ").title(), "value": t.value}
                for t in Constants.QuestionType
            ]
        }),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "passage":
            items = await ReadingPassage.all().values("id", "title")
            return (
                WidgetType.Select,
                {"options": [{"label": p["title"], "value": p["id"]} for p in items]}
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

@register(ReadingVariant)
class ReadingVariantAdmin(TortoiseModelAdmin):
    list_display        = ("id", "question", "text", "is_correct")
    list_filter         = ("question", "is_correct")
    list_select_related = ("question",)
    search_fields       = ()

    formfield_overrides = {
        "text"      : (WidgetType.TextArea, {}),
        "is_correct": (WidgetType.Switch, {}),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "question":
            items = await ReadingQuestion.all().values("id")
            return (
                WidgetType.Select,
                {"options": [{"label": f"Question {q['id']}", "value": q["id"]} for q in items]}
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

@register(Reading)
class ReadingAdmin(TortoiseModelAdmin):
    list_display        = ("id", "user", "status", "score", "start_time", "end_time")
    list_filter         = ("status", "user")
    list_select_related = ("user",)
    search_fields       = ()

    formfield_overrides = {
        "start_time": (WidgetType.DateTimePicker, {}),
        "end_time"  : (WidgetType.DateTimePicker, {}),
        "duration"  : (WidgetType.InputNumber, {}),
        "score"     : (WidgetType.InputNumber, {"step": 0.1}),
        "status"    : (WidgetType.Select, {
            "options": [
                {"label": s.name.title(), "value": s.value}
                for s in Constants.ReadingStatus
            ]
        }),
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

@register(ReadingAnswer)
class ReadingAnswerAdmin(TortoiseModelAdmin):
    list_display        = ("id", "user", "reading", "question", "variant", "is_correct")
    list_filter         = ("user", "reading", "question", "variant", "is_correct")
    list_select_related = ("user", "reading", "question", "variant")
    search_fields       = ()

    formfield_overrides = {
        "status"         : (WidgetType.Select, {
            "options": [
                {"label": "Answered",     "value": "answered"},
                {"label": "Not Answered", "value": "not_answered"},
            ]
        }),
        "text"           : (WidgetType.TextArea, {}),
        "explanation"    : (WidgetType.TextArea, {}),
        "correct_answer" : (WidgetType.TextArea, {}),
        "is_correct"     : (WidgetType.Switch, {}),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "user":
            users = await User.all().values("id", "email")
            return (
                WidgetType.Select,
                {"options": [{"label": u["email"], "value": u["id"]} for u in users]}
            )
        if field_name == "reading":
            items = await Reading.all().values("id")
            return (
                WidgetType.Select,
                {"options": [{"label": f"Reading {r['id']}", "value": r["id"]} for r in items]}
            )
        if field_name == "question":
            items = await ReadingQuestion.all().values("id")
            return (
                WidgetType.Select,
                {"options": [{"label": f"Question {q['id']}", "value": q["id"]} for q in items]}
            )
        if field_name == "variant":
            items = await ReadingVariant.all().values("id")
            return (
                WidgetType.Select,
                {"options": [{"label": f"Variant {v['id']}", "value": v["id"]} for v in items]}
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
