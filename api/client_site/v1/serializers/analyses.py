from typing import Optional
from pydantic import BaseModel

class ListeningAnalyseSerializer(BaseModel):
    session_id: int
    user_id: Optional[int]
    correct_answers: int
    overall_score: float
    duration: Optional[str]
    status: Optional[str]

class ReadingAnalyseSerializer(BaseModel):
    passage_id: int
    user_id: int
    correct_answers: int
    overall_score: float
    duration: Optional[str]

class SpeakingAnalyseSerializer(BaseModel):
    speaking_id: int
    feedback: Optional[str]
    overall_band_score: Optional[float]
    fluency_and_coherence_score: Optional[float]
    fluency_and_coherence_feedback: Optional[str]
    lexical_resource_score: Optional[float]
    lexical_resource_feedback: Optional[str]
    grammatical_range_and_accuracy_score: Optional[float]
    grammatical_range_and_accuracy_feedback: Optional[str]
    pronunciation_score: Optional[float]
    pronunciation_feedback: Optional[str]
    duration: Optional[str]

class WritingAnalyseSerializer(BaseModel):
    writing_id: int
    task_achievement_feedback: Optional[str]
    task_achievement_score: Optional[float]
    lexical_resource_feedback: Optional[str]
    lexical_resource_score: Optional[float]
    coherence_and_cohesion_feedback: Optional[str]
    coherence_and_cohesion_score: Optional[float]
    grammatical_range_and_accuracy_feedback: Optional[str]
    grammatical_range_and_accuracy_score: Optional[float]
    word_count_feedback: Optional[str]
    word_count_score: Optional[float]
    timing_feedback: Optional[str]
    overall_band_score: Optional[float]
    total_feedback: Optional[str]
    duration: Optional[str]