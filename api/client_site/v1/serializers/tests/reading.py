from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class VariantSerializer(BaseModel):
    id: int = Field(..., description="ID of the variant")
    text: str = Field(..., description="Text content of the variant")
    is_correct: Optional[bool] = Field(None, description="Is this variant correct?")

    @classmethod
    async def from_orm(cls, obj) -> "VariantSerializer":
        return cls(
            id=obj.id,
            text=obj.text,
            is_correct=getattr(obj, "is_correct", None),
        )

class QuestionListSerializer(BaseModel):
    id: int = Field(..., description="ID of the question")
    text: str = Field(..., description="Text content of the question")
    type: Optional[str] = Field(None, description="Type of the question")
    answers: List[VariantSerializer] = Field(..., description="List of related answer variants")

    @classmethod
    async def from_orm(cls, obj) -> "QuestionListSerializer":
        variants = await obj.variants.all()
        answers = [await VariantSerializer.from_orm(v) for v in variants]
        return cls(
            id=obj.id,
            text=obj.text,
            type=getattr(obj, "type", None),
            answers=answers,
        )

class PassageSerializer(BaseModel):
    id: int = Field(..., description="ID of the passage")
    title: str = Field(..., description="Title of the passage")
    text: str = Field(..., description="Full text content of the passage")
    skills: Optional[str] = Field(None, description="Skills associated with this passage")  # Добавляем поле
    questions: List[QuestionListSerializer] = Field(..., description="List of questions for this passage")

    @classmethod
    async def from_orm(cls, obj) -> "PassageSerializer":
        questions_qs = await obj.questions.all()
        questions = [await QuestionListSerializer.from_orm(q) for q in questions_qs]
        return cls(
            id=obj.id,
            title=obj.title,
            text=obj.text,
            skills=obj.skills,
            questions=questions,
        )

class SubmitQuestionAnswerSerializer(BaseModel):
    question_id: int = Field(..., description="ID of the question being answered")
    answer: str = Field(..., description="User's submitted answer text or variant ID as string")

class SubmitPassageAnswerSerializer(BaseModel):
    passage_id: int = Field(..., description="ID of the passage being answered")
    answers: List[SubmitQuestionAnswerSerializer] = Field(..., description="List of question-answer pairs")

class FinishReadingSerializer(BaseModel):
    reading_id: int = Field(..., description="ID of the reading session to finish")

class QuestionAnalysisSerializer(BaseModel):
    id: int = Field(..., description="ID of the question")
    text: str = Field(..., description="Text content of the question")
    type: Optional[str] = Field(None, description="Type of the question")
    answers: List[Dict[str, Any]] = Field(..., description="List of answer variants with correctness information")

    @classmethod
    async def from_orm(cls, obj) -> "QuestionAnalysisSerializer":
        variants = await obj.variants.all()
        answers = [
            {"id": v.id, "text": v.text, "is_correct": v.is_correct}
            for v in variants
        ]
        return cls(
            id=obj.id,
            text=obj.text,
            type=getattr(obj, "type", None),
            answers=answers,
        )

class StartReadingSerializer(BaseModel):
    level: Optional[str] = Field('easy', description="Level of the reading test (easy, medium, hard)")

class VariantAnalysisSerializer(BaseModel):
    id: int = Field(..., description="ID of the variant")
    text: str = Field(..., description="Text content of the variant")
    is_correct: Optional[bool] = Field(None, description="Is this variant correct?")

class QuestionAnalysisFullSerializer(BaseModel):
    id: int = Field(..., description="ID of the question")
    text: str = Field(..., description="Text content of the question")
    type: Optional[str] = Field(None, description="Type of the question")
    answers: List[VariantAnalysisSerializer] = Field(..., description="List of answer variants")
    user_answer: Optional[str] = Field(None, description="User's submitted answer")
    correct_answer: Optional[str] = Field(None, description="Correct answer text")
    is_correct: Optional[bool] = Field(None, description="Was the user's answer correct?")

class PassageAnalysisFullSerializer(BaseModel):
    id: int = Field(..., description="ID of the passage")
    title: str = Field(..., description="Title of the passage")
    text: str = Field(..., description="Full text of the passage")
    questions: List[QuestionAnalysisFullSerializer] = Field(..., description="Questions with analysis")
    overall_score: Optional[float] = Field(None, description="IELTS score for this passage")
    timing: Optional[float] = Field(None, description="Time spent on this passage (seconds)")

class ReadingAnalysisFullResponseSerializer(BaseModel):
    score: float = Field(..., description="Overall IELTS score for the session")
    correct: str = Field(..., description="Correct answers out of total, e.g. 36/40")
    time: float = Field(..., description="Total time spent (minutes)")
    passages: List[PassageAnalysisFullSerializer] = Field(..., description="Detailed analysis for each passage")

class ReadingSessionSerializer(BaseModel):
    id: int
    user_id: int
    status: str
    score: float
    start_time: datetime
    end_time: Optional[datetime]
    passages: List[PassageSerializer]

    @classmethod
    async def from_orm(cls, obj) -> "ReadingSessionSerializer":
        passages = await obj.passages.all().prefetch_related("questions__variants")
        passages_serialized = [await PassageSerializer.from_orm(p) for p in passages]
        return cls(
            id=obj.id,
            user_id=obj.user_id,
            status=obj.status,
            score=obj.score,
            start_time=obj.start_time,
            end_time=obj.end_time,
            passages=passages_serialized
        )