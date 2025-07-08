from tortoise import fields
from ..base import BaseModel
from .constants import Constants

class Reading(BaseModel):
    """Reading session: links a user to a set of texts (passages), stores time, result, and test status."""
    status = fields.CharEnumField(
        enum_type=Constants.ReadingStatus, default=Constants.ReadingStatus.PENDING, description="Status of the test"
    )
    user = fields.ForeignKeyField('models.User', related_name='reading_sessions', on_delete=fields.CASCADE, description="Related user")
    passages = fields.ManyToManyField('models.ReadingPassage', related_name='readings', description="Related passages")
    start_time = fields.DatetimeField(description="Start time of the test")
    end_time = fields.DatetimeField(null=True, description="End time of the test")
    score = fields.DecimalField(max_digits=3, decimal_places=1, default=0, description="Score of the test")
    duration = fields.IntField(default=60, description="Duration in minutes")

    class Meta:
        table = "readings"
        verbose_name = "Reading"
        verbose_name_plural = "Readings"

    def __str__(self) -> str:
        passages_titles = ", ".join([p.title for p in self.passages.all()[:3]])
        return f"{self.user.get_full_name()} - {self.status} - {passages_titles}"

class ReadingAnswer(BaseModel):
    """User's answer to a question: stores the selected option or answer text, correctness, and link to the reading session."""
    ANSWERED = "answered"
    NOT_ANSWERED = "not_answered"

    status = fields.CharField(max_length=12, default=NOT_ANSWERED, description="Status of the answer")
    user = fields.ForeignKeyField('models.User', related_name='user_answers', on_delete=fields.CASCADE, description="Related user")
    reading = fields.ForeignKeyField('models.Reading', related_name='user_answers', null=True, on_delete=fields.CASCADE, description="Related reading")
    question = fields.ForeignKeyField('models.ReadingQuestion', related_name='user_answers', on_delete=fields.CASCADE, description="Related question")
    variant = fields.ForeignKeyField('models.ReadingVariant', related_name='user_answers', null=True, on_delete=fields.CASCADE, description="Selected variant")
    text = fields.TextField(null=True, description="Answer text")
    explanation = fields.TextField(null=True, description="Explanation for the answer")
    is_correct = fields.BooleanField(null=True, description="Whether the answer is correct")
    correct_answer = fields.TextField(null=True, default="default", description="Correct answer text")

    class Meta:
        table = "reading_answers"
        verbose_name = "Answer"
        verbose_name_plural = "Answers"
        unique_together = ("reading_id", "user_id", "question_id")

    def __str__(self) -> str:
        return f"Answer to {self.question.text}"
    
class ReadingPassage(BaseModel):
    """Text (passage) for reading: contains text, difficulty level, number, and related questions."""
    level = fields.CharEnumField(
        enum_type=Constants.PassageLevel, default=Constants.PassageLevel.EASY, description="Difficulty level of the passage"
    )
    number = fields.IntField(null=True, description="Number of the passage")
    title = fields.CharField(max_length=255, description="Title of the passage")
    text = fields.TextField(description="Text content of the passage")
    skills = fields.TextField(null=True, description="Skills associated with the passage")

    class Meta:
        table = "reading_passages"
        verbose_name = "Passage"
        verbose_name_plural = "Passages"

    def __str__(self) -> str:
        return self.title
    
class ReadingQuestion(BaseModel):
    """Question for a passage: contains question text, type (text/multiple choice), and score for a correct answer."""
    passage = fields.ForeignKeyField('models.ReadingPassage', related_name='questions', null=True, on_delete=fields.CASCADE, description="Related passage")
    text = fields.TextField(description="Text of the question")
    type = fields.CharEnumField(enum_type=Constants.QuestionType, description="Type of the question")
    score = fields.IntField(description="Score for the question")

    class Meta:
        table = "reading_questions"
        verbose_name = "Question"
        verbose_name_plural = "Questions"

    def __str__(self) -> str:
        return self.text
    
class ReadingVariant(BaseModel):
    """Answer option for Multiple Choice: text and correctness flag."""
    question = fields.ForeignKeyField('models.ReadingQuestion', related_name='variants', on_delete=fields.CASCADE, description="Related question")
    text = fields.TextField(description="Text of the variant")
    is_correct = fields.BooleanField(default=False, description="Whether the variant is correct")

    class Meta:
        table = "reading_variants"
        verbose_name = "Variant"
        verbose_name_plural = "Variants"

    def __str__(self) -> str:
        return f"Variant for {self.question.text}"
