from fastadmin import TortoiseModelAdmin, register, WidgetType
from models import User, Tariff
from models.payments import Payment, PaymentStatus


@register(Payment)
class PaymentAdmin(TortoiseModelAdmin):
    list_display = (
        "id", "user", "tariff", "amount", "status",
        "start_date", "end_date", "created_at",
    )
    list_filter = ("status", "user")
    list_select_related = ("user", "tariff")
    search_fields = ()

    formfield_overrides = {
        "uuid":             (WidgetType.Input, {"disabled": True}),
        "amount":           (WidgetType.InputNumber, {"disabled": True}),
        "status":           (WidgetType.Input, {"disabled": True}),
        "start_date":       (WidgetType.DateTimePicker, {"disabled": True}),
        "end_date":         (WidgetType.DateTimePicker, {"disabled": True}),
        "atmos_order_id":   (WidgetType.Input, {"disabled": True}),
        "atmos_invoice_id": (WidgetType.Input, {"disabled": True}),
        "atmos_status":     (WidgetType.Input, {"disabled": True}),
        "atmos_response":   (WidgetType.TextArea, {"disabled": True}),
    }

    async def get_formfield_override(self, field_name: str):
        if field_name in ["user", "tariff"]:
            return None
        return await super().get_formfield_override(field_name)

    async def can_create(self, request) -> bool:
        return False

    async def can_update(self, request, obj) -> bool:
        return False

    async def can_delete(self, request, obj) -> bool:
        return False
