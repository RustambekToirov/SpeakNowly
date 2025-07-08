import os
from fastadmin import TortoiseModelAdmin, register, WidgetType
from tortoise.exceptions import ValidationError as TortoiseValidationError
from fastadmin.api.exceptions import AdminApiException
from models import (
    User, Listening, ListeningPart, ListeningSection,
    ListeningQuestion, ListeningSession, ListeningAnswer,
    ListeningQuestionType, ListeningPartNumber, ListeningSessionStatus
)
from aiofiles.os import listdir as aio_listdir
from aiofiles.os import wrap as aio_wrap


@register(Listening)
class ListeningAdmin(TortoiseModelAdmin):
    list_display     = ("id", "title", "created_at")
    search_fields    = ("title",)
    list_filter      = ()
    list_select_related = ()
    formfield_overrides = {
        "title"       : (WidgetType.Input, {}),
        "description" : (WidgetType.TextArea, {}),
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

@register(ListeningPart)
class ListeningPartAdmin(TortoiseModelAdmin):
    list_display = ("id", "listening", "part_number", "audio_file", "created_at")
    list_filter = ("listening", "part_number")
    list_select_related = ("listening",)
    search_fields = ()

    formfield_overrides = {
        "part_number": (WidgetType.Select, {
            "options": [
                {"label": f"Part {p.name[-1]}", "value": p.value}
                for p in ListeningPartNumber
            ]
        }),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "listening":
            items = await Listening.all().values("id", "title")
            return (
                WidgetType.Select,
                {"options": [{"label": i["title"], "value": i["id"]} for i in items]}
            )

        if field_name == "audio_file":
            dir_path = "media/audio"
            try:
                files = await aio_wrap(os.listdir)(dir_path)
                audio_files = [
                    f for f in files if f.endswith(".mp3") or f.endswith(".wav")
                ]
                options = [
                    {"label": f, "value": f"/media/audio/{f}"}
                    for f in audio_files
                ]
                return (WidgetType.Select, {"options": options})
            except FileNotFoundError:
                return (WidgetType.Select, {"options": []})

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

@register(ListeningSection)
class ListeningSectionAdmin(TortoiseModelAdmin):
    list_display     = ("id", "part", "section_number", "question_type", "start_index", "end_index")
    list_filter      = ("part", "question_type")
    list_select_related = ("part",)
    search_fields    = ()
    formfield_overrides = {
        "section_number": (WidgetType.InputNumber, {}),
        "start_index"   : (WidgetType.InputNumber, {}),
        "end_index"     : (WidgetType.InputNumber, {}),
        "question_text" : (WidgetType.TextArea, {}),
        "options"       : (WidgetType.TextArea, {}),
        "question_type" : (WidgetType.Select, {
            "options": [
                {"label": t.name.replace("_", " ").title(), "value": t.value}
                for t in ListeningQuestionType
            ]
        }),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "part":
            items = await ListeningPart.all().values("id")
            return (
                WidgetType.Select,
                {"options": [{"label": f"Part {p['id']}", "value": p["id"]} for p in items]}
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

@register(ListeningQuestion)
class ListeningQuestionAdmin(TortoiseModelAdmin):
    list_display     = ("id", "section", "index", "created_at")
    list_filter      = ("section",)
    list_select_related = ("section",)
    search_fields    = ()
    formfield_overrides = {
        "index"          : (WidgetType.InputNumber, {}),
        "question_text"  : (WidgetType.TextArea, {}),
        "options"        : (WidgetType.TextArea, {}),
        "correct_answer" : (WidgetType.TextArea, {}),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "section":
            items = await ListeningSection.all().values("id")
            return (
                WidgetType.Select,
                {"options": [{"label": f"Section {s['id']}", "value": s["id"]} for s in items]}
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

@register(ListeningSession)
class ListeningSessionAdmin(TortoiseModelAdmin):
    list_display       = ("id", "user", "exam", "status", "start_time", "end_time")
    list_filter        = ("user", "exam", "status")
    list_select_related = ("user", "exam")
    search_fields      = ("user.email",)
    formfield_overrides = {
        "start_time": (WidgetType.DateTimePicker, {}),
        "end_time"  : (WidgetType.DateTimePicker, {}),
        "status"    : (WidgetType.Select, {
            "options": [
                {"label": s.name.title(), "value": s.value}
                for s in ListeningSessionStatus
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
        if field_name == "exam":
            items = await Listening.all().values("id", "title")
            return (
                WidgetType.Select,
                {"options": [{"label": e["title"], "value": e["id"]} for e in items]}
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

@register(ListeningAnswer)
class ListeningAnswerAdmin(TortoiseModelAdmin):
    list_display        = ("id", "session", "question", "user", "is_correct", "score")
    list_filter         = ("session", "user", "question", "is_correct")
    list_select_related = ("session", "user", "question")
    search_fields       = ("user.email",)
    formfield_overrides = {
        "user_answer": (WidgetType.TextArea, {}),
        "is_correct" : (WidgetType.Switch, {}),
        "score"      : (WidgetType.InputNumber, {"step": 0.1}),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name == "user":
            users = await User.all().values("id", "email")
            return (
                WidgetType.Select,
                {"options": [{"label": u["email"], "value": u["id"]} for u in users]}
            )
        if field_name == "session":
            items = await ListeningSession.all().values("id")
            return (
                WidgetType.Select,
                {"options": [{"label": f"Session {s['id']}", "value": s["id"]} for s in items]}
            )
        if field_name == "question":
            items = await ListeningQuestion.all().values("id")
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
