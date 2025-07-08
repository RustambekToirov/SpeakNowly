from tortoise import fields
from enum import Enum

from .base import BaseModel


class CommentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Comment(BaseModel):
    """
    Tortoise ORM model for storing user comments.
    """
    text = fields.TextField(description="Comment text")
    user = fields.ForeignKeyField("models.User", on_delete=fields.CASCADE, related_name="comments", description="Author of the comment")
    rate = fields.FloatField(default=1.0, description="Rating (1 to 5)")
    status = fields.CharEnumField(CommentStatus, default=CommentStatus.ACTIVE, description="Current status of the comment (active/inactive)")

    class Meta:
        table = "comments"
        verbose_name = "Comment"
        verbose_name_plural = "Comments"

    def __str__(self) -> str:
        return self.text[:20]
