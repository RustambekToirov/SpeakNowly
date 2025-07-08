from tortoise import fields
from passlib.hash import bcrypt  # For password hashing
from ..base import BaseModel
from ..tariffs import Tariff


class User(BaseModel):
    """Represents a user in the system."""
    telegram_id = fields.BigIntField(unique=True, null=True, description="Telegram ID")
    email = fields.CharField(max_length=255, unique=True, description="Email Address")
    first_name = fields.CharField(max_length=255, null=True, description="First Name")
    last_name = fields.CharField(max_length=255, null=True, description="Last Name")
    age = fields.IntField(null=True, description="Age")
    photo = fields.CharField(max_length=255, null=True, description="Photo")
    password = fields.CharField(max_length=128, description="Password")
    tariff = fields.ForeignKeyField('models.Tariff', related_name='users', null=True, description="Tariff")
    tokens = fields.IntField(default=0, description="Tokens")
    is_verified = fields.BooleanField(default=False, description="Verified")
    is_active = fields.BooleanField(default=True, description="Active")
    is_staff = fields.BooleanField(default=False, description="Staff")
    is_superuser = fields.BooleanField(default=False, description="Superuser")
    last_login = fields.DatetimeField(null=True, description="Last Login")

    class Meta:
        table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email
    
    async def __str__(self):
        return self.email

    def set_password(self, raw_password: str):
        """Hashes the password before saving."""
        self.password = bcrypt.hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """Verifies the password."""
        return bcrypt.verify(raw_password, self.password)

    @property
    def is_premium(self) -> bool:
        """Return True if the user has a non-default tariff."""
        return self.tariff is not None and not self.tariff.is_default

    async def add_tariff(self, tariff: Tariff):
        """Assign a tariff to the user and save."""
        self.tariff = tariff
        await self.save()


class UserActivityLog(BaseModel):
    """Logs user activities such as login, logout, and other actions."""
    user = fields.ForeignKeyField("models.User", related_name="activity_logs", description="User")
    action = fields.CharField(max_length=255, description="Action performed by the user")
    timestamp = fields.DatetimeField(auto_now_add=True, description="Timestamp of the action")

    class Meta:
        table = "user_activity_logs"
        verbose_name = "User Activity Log"
        verbose_name_plural = "User Activity Logs"

    def __str__(self):
        return f"{self.user.email} - {self.action}"
    
    async def __str__(self):
        await self.fetch_related('user')
        return f"{self.user.email} - {self.action}"