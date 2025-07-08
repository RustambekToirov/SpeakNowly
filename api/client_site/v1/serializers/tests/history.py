from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal
from datetime import datetime

class ReadingHistorySerializer(BaseModel):
    """Serializer for reading history."""
    type: Literal["Reading"] = "Reading"
    score: float
    created_at: datetime
    duration: Optional[int]
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    async def from_orm_async(cls, obj):
        score = getattr(obj, "score", 0)
        duration = None
        if getattr(obj, "start_time", None) and getattr(obj, "end_time", None):
            duration = int((obj.end_time - obj.start_time).total_seconds())
        return cls(
            score=score,
            created_at=getattr(obj, "start_time", None),
            duration=duration,
        )

class ListeningHistorySerializer(BaseModel):
    """Serializer for listening history."""
    type: Literal["Listening"] = "Listening"
    score: float
    created_at: datetime
    duration: Optional[int]
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    async def from_orm_async(cls, obj):
        from models.analyses import ListeningAnalyse
        analyse = await ListeningAnalyse.get_or_none(session_id=obj.id)
        score = float(analyse.overall_score) if analyse else 0
        duration = None
        if getattr(obj, "start_time", None) and getattr(obj, "end_time", None):
            duration = int((obj.end_time - obj.start_time).total_seconds())
        return cls(
            score=score,
            created_at=getattr(obj, "start_time", None),
            duration=duration,
        )

class WritingHistorySerializer(BaseModel):
    """Serializer for writing history."""
    type: Literal["Writing"] = "Writing"
    score: float
    created_at: datetime
    duration: Optional[int]
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    async def from_orm_async(cls, obj):
        from models.analyses import WritingAnalyse
        analyse = await WritingAnalyse.get_or_none(writing_id=obj.id)
        score = float(analyse.overall_band_score) if analyse else 0
        duration = None
        if getattr(obj, "start_time", None) and getattr(obj, "end_time", None):
            duration = int((obj.end_time - obj.start_time).total_seconds())
        return cls(
            score=score,
            created_at=getattr(obj, "start_time", None),
            duration=duration,
        )

class SpeakingHistorySerializer(BaseModel):
    """Serializer for speaking history."""
    type: Literal["Speaking"] = "Speaking"
    score: float
    created_at: datetime
    duration: Optional[int]
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    async def from_orm_async(cls, obj):
        from models.analyses import SpeakingAnalyse
        analyse = await SpeakingAnalyse.get_or_none(speaking_id=obj.id)
        score = float(analyse.overall_band_score) if analyse else 0
        duration = None
        if getattr(obj, "start_time", None) and getattr(obj, "end_time", None):
            duration = int((obj.end_time - obj.start_time).total_seconds())
        return cls(
            score=score,
            created_at=getattr(obj, "start_time", None),
            duration=duration,
        )

HistoryItem = (
    ReadingHistorySerializer
    | ListeningHistorySerializer
    | WritingHistorySerializer
    | SpeakingHistorySerializer
)

class LatestAnalysis(BaseModel):
    """Serializer for the latest analysis of a user."""
    listening: Optional[float]
    speaking: Optional[float]
    writing: Optional[float]
    reading: Optional[float]
    model_config = ConfigDict(from_attributes=True)

class UserProgressSerializer(BaseModel):
    """Serializer for user progress."""
    latest_analysis: LatestAnalysis
    highest_score: float
    model_config = ConfigDict(from_attributes=True)

class MainStatsSerializer(BaseModel):
    """Serializer for main stats of a user."""
    speaking: float
    reading: float
    writing: float
    listening: float
    model_config = ConfigDict(from_attributes=True)

