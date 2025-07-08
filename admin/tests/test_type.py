from fastadmin import TortoiseModelAdmin, register, WidgetType
from tortoise.exceptions import ValidationError as TortoiseValidationError
from fastadmin.api.exceptions import AdminApiException
from models import TestType


@register(TestType)
class TestTypeAdmin(TortoiseModelAdmin):
    list_display   = ("id", "type", "price", "trial_price")
    list_filter    = ()
    search_fields  = ()

    formfield_overrides = {
        "type": (WidgetType.Select, {
            "options": [
                {"label": t.name.replace("_ENG", "").title(), "value": t.value}
                for t in TestType._meta.fields_map["type"].enum_type
            ]
        }),
        "price":       (WidgetType.InputNumber, {}),
        "trial_price": (WidgetType.InputNumber, {}),
    }

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
