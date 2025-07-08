from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

class ListeningPartShortSerializer(BaseModel):
    """Short serializer for a listening part (for session/parts list)."""
    part_number: int
    audio_file: str

    class Config:
        from_attributes = True

    @classmethod
    async def from_orm(cls, obj):
        return cls(
            part_number=obj.part_number,
            audio_file=obj.audio_file,
        )

class ListeningSessionExamSerializer(BaseModel):
    """Serializer for exam info in session."""
    id: int = Field(..., description="ID of the listening test")
    title: str = Field(..., description="Title of the listening test")
    description: str = Field(..., description="Description of the listening test")

    @classmethod
    async def from_orm(cls, obj) -> "ListeningSessionExamSerializer":
        return cls(
            id=obj.id,
            title=obj.title,
            description=obj.description,
        )

class ListeningDataSlimSerializer(BaseModel):
    """Serializer for listening session start/detail."""
    session_id: int = Field(..., description="ID of the session")
    status: str = Field(..., description="Session status")
    start_time: Optional[datetime] = Field(None, description="Session start time")
    end_time: Optional[datetime] = Field(None, description="Session end time")
    exam: ListeningSessionExamSerializer = Field(..., description="Listening test info")
    parts: List["ListeningPartSerializer"] = Field(..., description="List of parts for this session")

    @classmethod
    async def from_orm(cls, session_obj, exam_obj, parts_qs) -> "ListeningDataSlimSerializer":
        exam = await ListeningSessionExamSerializer.from_orm(exam_obj)
        parts = [await ListeningPartSerializer.from_orm(p) for p in parts_qs]
        return cls(
            session_id=session_obj.id,
            status=session_obj.status,
            start_time=session_obj.start_time,
            end_time=session_obj.end_time,
            exam=exam,
            parts=parts,
        )

class ListeningQuestionSerializer(BaseModel):
    """Serializer for a listening question."""
    id: int = Field(..., description="ID of the question")
    section_id: int = Field(..., description="ID of the section")
    index: int = Field(..., description="Index of the question in section")
    options: Optional[Union[List[str], Dict[str, str], List[Dict[str, str]]]] = Field(None, description="Options for the question")
    correct_answer: Any = Field(..., description="Correct answer for the question")
    question_text: Optional[str] = Field(None, description="Text of the question")

    @classmethod
    async def from_orm(cls, obj) -> "ListeningQuestionSerializer":
        cleaned_options = None
        if obj.options:
            if isinstance(obj.options, list):
                tmp_list = []
                for item in obj.options:
                    if isinstance(item, dict) or isinstance(item, str):
                        tmp_list.append(item or "")
                    else:
                        tmp_list.append("")
                cleaned_options = tmp_list
            else:
                cleaned_options = obj.options

        return cls(
            id=obj.id,
            section_id=obj.section_id,
            index=obj.index,
            options=cleaned_options,
            correct_answer=obj.correct_answer,
            question_text=obj.question_text,
        )

class ListeningSectionSerializer(BaseModel):
    """Serializer for a listening section with its questions."""
    id: int = Field(..., description="ID of the section")
    section_number: int = Field(..., description="Section number in the part")
    start_index: int = Field(..., description="Start index of questions")
    end_index: int = Field(..., description="End index of questions")
    question_type: str = Field(..., description="Type of questions in section")
    question_text: Optional[str] = Field(None, description="Text for the section")
    options: Optional[Union[List[str], Dict[str, str], List[Dict[str, str]]]] = Field(None, description="Options for the section")
    questions: List[ListeningQuestionSerializer] = Field(..., description="List of questions in this section")

    @classmethod
    async def from_orm(cls, obj) -> "ListeningSectionSerializer":
        # подтягиваем и сериализуем вопросы
        questions_qs = await obj.questions.order_by("index").all()
        questions = [await ListeningQuestionSerializer.from_orm(q) for q in questions_qs]

        # нормализуем options в простой список строк
        raw_opts = obj.options or []
        if isinstance(raw_opts, list):
            opts: List[str] = []
            for item in raw_opts:
                if isinstance(item, dict):
                    # если dict, берём поле value (или label, если нужно)
                    opts.append(str(item.get("value", "") or ""))
                elif isinstance(item, str):
                    opts.append(item)
                else:
                    opts.append("")
            options = opts
        else:
            # если не список, оставляем как есть
            options = raw_opts

        return cls(
            id=obj.id,
            section_number=obj.section_number,
            start_index=obj.start_index,
            end_index=obj.end_index,
            question_type=obj.question_type,
            question_text=obj.question_text,
            options=options,
            questions=questions,
        )

class ListeningPartSerializer(BaseModel):
    """Serializer for a listening part with its sections."""
    id: int = Field(..., description="ID of the part")
    part_number: int = Field(..., description="Part number")
    audio_file: str = Field(..., description="Audio file path")
    sections: List[ListeningSectionSerializer] = Field(..., description="List of sections in this part")

    @classmethod
    async def from_orm(cls, obj) -> "ListeningPartSerializer":
        sections_qs = await obj.sections.order_by("section_number").all()
        sections = [await ListeningSectionSerializer.from_orm(s) for s in sections_qs]
        return cls(
            id=obj.id,
            part_number=obj.part_number,
            audio_file=obj.audio_file,
            sections=sections,
        )

class ListeningAnswerItemSerializer(BaseModel):
    """Serializer for a user's answer to a single listening question."""
    question_id: int = Field(..., description="ID of the question being answered")
    user_answer: Any = Field(..., description="User's answer")

class ListeningAnswerSerializer(BaseModel):
    """Serializer for submitting answers to all questions in a listening session."""
    answers: List[ListeningAnswerItemSerializer] = Field(..., description="List of answers")

class ListeningResponseDetailSerializer(BaseModel):
    """Serializer for detailed response analysis of a listening question."""
    id: int
    user_answer: Any
    is_correct: bool
    score: float
    correct_answer: Any
    question_index: int

class ListeningAnalyseResponseSerializer(BaseModel):
    """Serializer for summarizing analysis results of a listening session."""
    session_id: int
    analysis: Dict[str, Any]
    responses: List[ListeningResponseDetailSerializer]
    listening_parts: List[ListeningPartShortSerializer]

# Listening Test Creation Serializers
class ListeningQuestionCreate(BaseModel):
    index: int
    question_text: str
    options: List[str]
    correct_answer: List[str]

class ListeningSectionCreate(BaseModel):
    section_number: int
    start_index: int
    end_index: int
    question_type: str
    question_text: str
    options: List[str]
    questions: List[ListeningQuestionCreate]

class ListeningPartCreate(BaseModel):
    part_number: int
    audio_file: str
    sections: List[ListeningSectionCreate]

class ListeningTestCreate(BaseModel):
    title: str
    description: str
    parts: List[ListeningPartCreate]

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Test Title",
                "description": "Test description",
                "parts": [
                    {
                        "part_number": 1,
                        "audio_file": "audio1.mp3",
                        "sections": [
                            {
                                "section_number": 1,
                                "start_index": 0,
                                "end_index": 60,
                                "question_type": "multiple_answers",
                                "question_text": "Which 2 apply?",
                                "options": ["option1", "option2", "option3"],
                                "questions": [
                                    {
                                        "index": 1,
                                        "question_text": "Which two letters are consonants?",
                                        "options": ["A", "B", "C", "D"],
                                        "correct_answer": ["A", "C"]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }