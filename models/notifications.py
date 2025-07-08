from tortoise import fields
from .base import BaseModel
from enum import Enum

class MessageType(str, Enum):
    MAIL = "mail"
    SITE = "site"
    MAIL_SITE = "mail_site"

class Message(BaseModel):
    user = fields.ForeignKeyField("models.User", related_name="messages", null=True, description="User")
    type = fields.CharEnumField(MessageType, default=MessageType.SITE, description="Type")
    title = fields.CharField(max_length=255, description="Title")
    description = fields.TextField(null=True, description="Description")
    content = fields.TextField(null=True, description="Content")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "messages"
        verbose_name = "Message"
        verbose_name_plural = "Messages"

class ReadStatus(BaseModel):
    message = fields.ForeignKeyField("models.Message", related_name="read_statuses", description="Message")
    user = fields.ForeignKeyField("models.User", related_name="read_statuses", description="User")

    class Meta:
        table = "read_statuses"
        verbose_name = "Read Status"
        verbose_name_plural = "Read Statuses"
