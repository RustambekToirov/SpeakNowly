from fastadmin import TortoiseModelAdmin, register, WidgetType, action
from tortoise.exceptions import ValidationError as TortoiseValidationError
from fastadmin.api.exceptions import AdminApiException
from models.users.users import User, UserActivityLog


@register(User)
class UserAdmin(TortoiseModelAdmin):
    list_display = (
        "id", "telegram_id", "email", "first_name", "last_name",
        "age", "tokens", "tariff", "is_verified", "is_active",
        "is_staff", "is_superuser", "last_login", "created_at",
    )
    list_select_related = ("tariff",)
    list_display_links = ("email",)
    list_filter = (
        "tariff", "is_verified", "is_active", "is_staff", "is_superuser",
    )
    search_fields = ("email", "telegram_id", "first_name", "last_name")

    formfield_overrides = {
        "telegram_id": (WidgetType.InputNumber, {}),
        "email":       (WidgetType.EmailInput, {}),
        "first_name":  (WidgetType.Input, {}),
        "last_name":   (WidgetType.Input, {}),
        "age":         (WidgetType.InputNumber, {}),
        "photo":       (WidgetType.Input, {}),
        "password":    (WidgetType.PasswordInput, {"passwordModalForm": True}),
        "tokens":      (WidgetType.InputNumber, {}),
        "last_login":  (WidgetType.DateTimePicker, {}),
        "is_verified": (WidgetType.Switch, {}),
        "is_active":   (WidgetType.Switch, {}),
        "is_staff":    (WidgetType.Switch, {}),
        "is_superuser":(WidgetType.Switch, {}),
    }

    actions = (*TortoiseModelAdmin.actions, "activate", "deactivate")

    async def authenticate(self, email: str, password: str) -> int | None:
        user = await self.model_cls.filter(
            email=email, is_active=True, is_superuser=True
        ).first()
        if not user or not user.check_password(password):
            return None
        return user.id

    async def change_password(self, id: int, password: str) -> None:
        user = await self.model_cls.filter(id=id).first()
        if not user:
            return
        user.set_password(password)
        await user.save(update_fields=("password",))

    async def tariff_name(self, obj):
        tariff = await obj.tariff
        return tariff.name if tariff else "-"

    @action(description="Activate selected users")
    async def activate(self, ids: list[int]) -> None:
        await self.model_cls.filter(id__in=ids).update(is_active=True)

    @action(description="Deactivate selected users")
    async def deactivate(self, ids: list[int]) -> None:
        await self.model_cls.filter(id__in=ids).update(is_active=False)

    async def save_model(self, id: int | None, payload: dict) -> dict:
        try:
            return await super(UserAdmin, self).save_model(id, payload)
        except TortoiseValidationError as e:
            errors: dict[str, str] = {}
            for msg in e.args:
                if isinstance(msg, str) and ':' in msg:
                    fld, text = msg.split(':', 1)
                    errors[fld.strip()] = text.strip()
            msg = "; ".join([f"{k}: {v}" for k, v in errors.items()])
            raise AdminApiException(status_code=400, detail=msg)


@register(UserActivityLog)
class UserActivityLogAdmin(TortoiseModelAdmin):
    list_display = (
        "id", "user", "action", "timestamp", "created_at"
    )
    list_select_related = ("user",)
    list_display_links = ("id",)
    list_filter = ("action", "timestamp", "user")
    search_fields = ("action",)

    formfield_overrides = {
        "action": (WidgetType.Input, {}),
        "timestamp": (WidgetType.DateTimePicker, {}),
    }

    can_create = True
    can_edit = False
    can_delete = False

    async def save_model(self, id: int | None, payload: dict) -> dict:
        try:
            return await super(UserActivityLogAdmin, self).save_model(id, payload)
        except TortoiseValidationError as e:
            errors: dict[str, str] = {}
            for msg in e.args:
                if isinstance(msg, str) and ':' in msg:
                    fld, text = msg.split(':', 1)
                    errors[fld.strip()] = text.strip()
            msg = "; ".join([f"{k}: {v}" for k, v in errors.items()])
            raise AdminApiException(status_code=400, detail=msg)
