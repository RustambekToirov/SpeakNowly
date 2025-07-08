from tortoise import fields
from .base import BaseModel

class ListeningAnalyse(BaseModel):
    """Stores analysis results for a listening test."""
    session = fields.OneToOneField(
        "models.ListeningSession", related_name="analysis", description="Related listening session"
    )
    user = fields.ForeignKeyField("models.User", related_name="listening_analyses", description="User who took the test")
    correct_answers = fields.IntField(default=0, description="Number of correct answers")
    overall_score = fields.DecimalField(max_digits=3, decimal_places=1, description="Overall score")
    status = fields.CharField(max_length=32, default="pending", description="Status of analysis")
    duration = fields.TimeDeltaField(description="Time taken for the test")

    class Meta:
        table = "listening_analyses"
        verbose_name = "Listening Analyse"
        verbose_name_plural = "Listening Analyses"

    def __str__(self):
        return f"Listening Analyse - Score: {self.overall_score}"


class WritingAnalyse(BaseModel):
    """Stores analysis results for a writing test."""
    writing = fields.OneToOneField(
        "models.Writing", related_name="analyse", description="Related writing test"
    )
    task_achievement_feedback = fields.TextField(description="Feedback on task achievement")
    task_achievement_score = fields.DecimalField(max_digits=3, decimal_places=1, description="Score for task achievement")
    lexical_resource_feedback = fields.TextField(description="Feedback on lexical resource")
    lexical_resource_score = fields.DecimalField(max_digits=3, decimal_places=1, description="Score for lexical resource")
    coherence_and_cohesion_feedback = fields.TextField(description="Feedback on coherence and cohesion")
    coherence_and_cohesion_score = fields.DecimalField(max_digits=3, decimal_places=1, description="Score for coherence and cohesion")
    grammatical_range_and_accuracy_feedback = fields.TextField(description="Feedback on grammar")
    grammatical_range_and_accuracy_score = fields.DecimalField(max_digits=3, decimal_places=1, description="Score for grammar")
    word_count_feedback = fields.TextField(description="Feedback on word count")
    word_count_score = fields.DecimalField(max_digits=3, decimal_places=1, description="Score for word count")
    timing_feedback = fields.TextField(description="Feedback on timing")
    overall_band_score = fields.DecimalField(max_digits=3, decimal_places=1, description="Overall band score")
    total_feedback = fields.TextField(description="Overall feedback")
    duration = fields.TimeDeltaField(null=True, description="Time taken for the test")

    class Meta:
        table = "writing_analyses"
        verbose_name = "Writing Analyse"
        verbose_name_plural = "Writing Analyses"

    def __str__(self):
        return f"Writing Analyse - Score: {self.overall_band_score}"


class SpeakingAnalyse(BaseModel):
    """Stores analysis results for a speaking test."""
    speaking = fields.OneToOneField("models.Speaking", related_name="analyse", on_delete=fields.CASCADE, description="Analysis of the speaking test")
    feedback = fields.TextField(null=True, description="Feedback for the user")
    overall_band_score = fields.DecimalField(max_digits=3, decimal_places=1, null=True, description="Overall band score")
    fluency_and_coherence_score = fields.DecimalField(max_digits=3, decimal_places=1, null=True, description="Fluency and coherence score")
    fluency_and_coherence_feedback = fields.TextField(null=True, description="Feedback on fluency and coherence")
    lexical_resource_score = fields.DecimalField(max_digits=3, decimal_places=1, null=True, description="Lexical resource score")
    lexical_resource_feedback = fields.TextField(null=True, description="Feedback on lexical resource")
    grammatical_range_and_accuracy_score = fields.DecimalField(max_digits=3, decimal_places=1, null=True, description="Grammatical range and accuracy score")
    grammatical_range_and_accuracy_feedback = fields.TextField(null=True, description="Feedback on grammatical range and accuracy")
    pronunciation_score = fields.DecimalField(max_digits=3, decimal_places=1, null=True, description="Pronunciation score")
    pronunciation_feedback = fields.TextField(null=True, description="Feedback on pronunciation")
    duration = fields.TimeDeltaField(null=True, description="Duration of the speaking test")

    class Meta:
        table = "speaking_analyses"
        verbose_name = "Speaking Analyse"
        verbose_name_plural = "Speaking Analyses"

    def __str__(self):
        return f"Speaking Analyse - Score: {self.overall_band_score}"


class ReadingAnalyse(BaseModel):
    """Stores analysis results for a reading test."""
    user = fields.ForeignKeyField("models.User", related_name="reading_analyses", description="User who took the test")
    passage = fields.ForeignKeyField("models.ReadingPassage", related_name="analyses", description="Related reading passage")
    correct_answers = fields.IntField(default=0, description="Number of correct answers")
    overall_score = fields.DecimalField(max_digits=5, decimal_places=2, description="Overall score")
    duration = fields.TimeDeltaField(null=True, description="Time taken for the test")

    class Meta:
        table = "reading_analyses"
        verbose_name = "Reading Analyse"
        verbose_name_plural = "Reading Analyses"

    def __str__(self):
        passage_title = getattr(self.passage, "title", self.passage_id)
        user_email = getattr(self.user, "email", self.user_id)
        return f"Analysis for {passage_title} by {user_email}"
