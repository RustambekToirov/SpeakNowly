from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator
from enum import Enum
from ..base import BaseModel
import json


class SpeakingStatus(str, Enum):
    """Status of a speaking test."""
    STARTED = "started"
    PENDING = "pending"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    EXPIRED = "expired"


class SpeakingPart(str, Enum):
    """Parts of the speaking test."""
    PART_1 = "Part 1"
    PART_2 = "Part 2"
    PART_3 = "Part 3"


class Speaking(BaseModel):
    """Represents a speaking test instance for a user."""
    status = fields.CharEnumField(SpeakingStatus, null=True, default=SpeakingStatus.PENDING, description="Status of the speaking test")
    user = fields.ForeignKeyField("models.User", related_name="speaking_tests", on_delete=fields.CASCADE, description="User taking the speaking test")
    start_time = fields.DatetimeField(null=True, description="Start time of the test")
    end_time = fields.DatetimeField(null=True, description="End time of the test")

    class Meta:
        table = "speaking"
        verbose_name = "Speaking Test"
        verbose_name_plural = "Speaking Tests"

    def __str__(self):
        return f"Speaking test {self.id} for user {self.user_id}"


class SpeakingQuestion(BaseModel):
    """A question belonging to a speaking test."""
    speaking = fields.ForeignKeyField("models.Speaking", related_name="questions", on_delete=fields.CASCADE, description="Related speaking test")
    part = fields.CharEnumField(SpeakingPart, null=True, description="Part of the speaking test")
    title = fields.TextField(null=True, blank=True, description="Title of the question")
    content = fields.JSONField(description="Content of the question")

    class Meta:
        table = "speaking_questions"
        verbose_name = "Speaking Question"
        verbose_name_plural = "Speaking Questions"

    def __str__(self):
        snippet = (json.dumps(self.content) or "")[:50]
        return f"{self.part} for Speaking {self.speaking_id}: {snippet}"


class SpeakingAnswer(BaseModel):
    """The answer to a single speaking question."""
    question = fields.OneToOneField("models.SpeakingQuestion", related_name="answer", on_delete=fields.CASCADE, description="The question this answer refers to")
    text_answer = fields.TextField(null=True, description="Transcribed text of the audio answer")
    audio_answer = fields.CharField(max_length=255, null=True, description="File path to the stored audio answer")

    class Meta:
        table = "speaking_answers"
        verbose_name = "Speaking Answer"
        verbose_name_plural = "Speaking Answers"

    def __str__(self):
        return f"Answer to {self.question.part} (Speaking {self.question.speaking_id})"
