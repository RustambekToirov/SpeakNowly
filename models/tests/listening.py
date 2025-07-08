from tortoise import fields
from ..base import BaseModel
from enum import Enum


class ListeningQuestionType(str, Enum):
    """Types of questions that can be asked in a Listening test."""
    FORM_COMPLETION = "form_completion"
    CHOICE = "choice"
    MULTIPLE_ANSWERS = "multiple_answers"
    MATCHING = "matching"
    SENTENCE_COMPLETION = "sentence_completion"
    CLOZE_TEST = "cloze_test"


class ListeningPartNumber(int, Enum):
    """Enumeration for the parts of a Listening test."""
    PART_1 = 1
    PART_2 = 2
    PART_3 = 3
    PART_4 = 4


class ListeningSessionStatus(str, Enum):
    """Status of a Listening test session."""
    STARTED = "started"
    PENDING = "pending"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    EXPIRED = "expired"


class Listening(BaseModel):
    """Listening test metadata."""
    title = fields.CharField(max_length=255, description="Title of the listening test")
    description = fields.TextField(description="Description of the listening test")

    class Meta:
        table = "listenings"
        verbose_name = "Listening Test"
        verbose_name_plural = "Listening Tests"

    def __str__(self):
        return self.title


class ListeningPart(BaseModel):
    """One part of a Listening test (e.g., Part 1, Part 2)."""
    listening = fields.ForeignKeyField(
        "models.Listening",
        on_delete=fields.CASCADE,
        related_name="parts",
        description="Related listening test"
    )
    part_number = fields.IntEnumField(ListeningPartNumber, description="Part number of the test")
    audio_file = fields.CharField(max_length=255, description="Path or URL of the audio file for this part")

    class Meta:
        table = "listening_parts"
        verbose_name = "Listening Part"
        verbose_name_plural = "Listening Parts"

    def __str__(self):
        return f"Part {self.part_number} of Listening {self.listening_id}"


class ListeningSection(BaseModel):
    """One section within a ListeningPart."""
    part = fields.ForeignKeyField(
        "models.ListeningPart",
        on_delete=fields.CASCADE,
        related_name="sections",
        description="Related listening part"
    )
    section_number = fields.IntField(description="Section number within the part")
    start_index = fields.IntField(description="Start index/timestamp of this section")
    end_index = fields.IntField(description="End index/timestamp of this section")
    question_type = fields.CharEnumField(ListeningQuestionType, description="Type of questions in this section")
    question_text = fields.TextField(null=True, description="Prompt text for the section (if applicable)")
    options = fields.JSONField(null=True, description="Options shared among questions in this section")

    class Meta:
        table = "listening_sections"
        verbose_name = "Listening Section"
        verbose_name_plural = "Listening Sections"

    def __str__(self):
        return f"Section {self.section_number} of Part {self.part_id}"


class ListeningQuestion(BaseModel):
    """A single question inside a ListeningSection."""
    section = fields.ForeignKeyField(
        "models.ListeningSection",
        on_delete=fields.CASCADE,
        related_name="questions",
        description="Related listening section"
    )
    index = fields.IntField(description="Index of the question within the section")
    question_text = fields.TextField(null=True, description="Text of the question")
    options = fields.JSONField(null=True, description="Options for this question (if any)")
    correct_answer = fields.JSONField(description="Correct answer(s) for the question")

    class Meta:
        table = "listening_questions"
        verbose_name = "Listening Question"
        verbose_name_plural = "Listening Questions"

    def __str__(self):
        return f"Question {self.index} in Section {self.section_id}"


class ListeningSession(BaseModel):
    """Tracks a user’s attempt at a Listening test."""
    status = fields.CharEnumField(
        ListeningSessionStatus,
        default=ListeningSessionStatus.STARTED,
        description="Current status of the session"
    )
    user = fields.ForeignKeyField(
        "models.User",
        on_delete=fields.CASCADE,
        related_name="listening_sessions",
        description="User who started this session"
    )
    exam = fields.ForeignKeyField(
        "models.Listening",
        on_delete=fields.CASCADE,
        related_name="user_sessions",
        description="Listening test associated with this session"
    )
    start_time = fields.DatetimeField(auto_now_add=True, description="When the session started")
    end_time = fields.DatetimeField(null=True, description="When the session ended")

    class Meta:
        table = "user_listening_sessions"
        verbose_name = "User Listening Session"
        verbose_name_plural = "User Listening Sessions"

    def __str__(self):
        return f"Session {self.id} for User {self.user_id}"


class ListeningAnswer(BaseModel):
    """Stores a user’s answer to a ListeningQuestion within a session."""
    session = fields.ForeignKeyField(
        "models.ListeningSession",
        on_delete=fields.CASCADE,
        related_name="responses",
        description="Related listening session"
    )
    user = fields.ForeignKeyField(
        "models.User",
        on_delete=fields.CASCADE,
        description="User who provided this response"
    )
    question = fields.ForeignKeyField(
        "models.ListeningQuestion",
        on_delete=fields.CASCADE,
        description="The question this response belongs to"
    )
    user_answer = fields.JSONField(null=True, description="User’s submitted answer")
    is_correct = fields.BooleanField(default=False, description="Whether the user’s answer was correct")
    score = fields.DecimalField(max_digits=5, decimal_places=2, default=0.0, description="Score awarded for this response")

    class Meta:
        table = "user_responses"
        verbose_name = "User Response"
        verbose_name_plural = "User Responses"

    async def save(self, *args, **kwargs):
        """
        Convert non-(str,int,float,list,dict) answers to string before saving.
        """
        if self.user_answer is not None and not isinstance(self.user_answer, (str, int, float, list, dict)):
            self.user_answer = str(self.user_answer)
        await super().save(*args, **kwargs)

    def __str__(self):
        return f"Response {self.id} (Session {self.session_id}, Question {self.question_id})"
