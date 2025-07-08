from fastapi import APIRouter, Depends, Query
from typing import List, Any, Optional, Dict
from itertools import chain

from ...serializers.tests import (
    ListeningHistorySerializer,
    ReadingHistorySerializer,
    SpeakingHistorySerializer,
    WritingHistorySerializer,
    UserProgressSerializer,
    MainStatsSerializer,
)
from services import UserProgressService
from models.tests import ListeningSession, Reading, Speaking, Writing
from models.analyses import ListeningAnalyse, SpeakingAnalyse, WritingAnalyse
from utils.auth import active_user

router = APIRouter()


@router.get("/", response_model=List[Any], summary="Get user test history")
async def get_history(
    user=Depends(active_user),
    type: Optional[str] = Query(None, description="Filter by test type"),
    show: Optional[str] = Query(None, description="Show last N results"),
):
    """
    Get combined test history for the current user.
    """
    reading = await Reading.filter(user_id=user.id).all()
    listening = await ListeningSession.filter(user_id=user.id).all()
    speaking = await Speaking.filter(user_id=user.id).all()
    writing = await Writing.filter(user_id=user.id).all()

    queryset = sorted(
        chain(reading, listening, speaking, writing),
        key=lambda obj: getattr(obj, "created_at", getattr(obj, "start_time", None)),
        reverse=True,
    )

    if type == "reading":
        queryset = [item for item in queryset if isinstance(item, Reading)]
    elif type == "listening":
        queryset = [item for item in queryset if isinstance(item, ListeningSession)]
    elif type == "speaking":
        queryset = [item for item in queryset if isinstance(item, Speaking)]
    elif type == "writing":
        queryset = [item for item in queryset if isinstance(item, Writing)]

    if show == "last":
        queryset = queryset[:5]

    results = []
    for item in queryset:
        if isinstance(item, Reading):
            results.append(await ReadingHistorySerializer.from_orm_async(item))
        elif isinstance(item, ListeningSession):
            results.append(await ListeningHistorySerializer.from_orm_async(item))
        elif isinstance(item, Speaking):
            results.append(await SpeakingHistorySerializer.from_orm_async(item))
        elif isinstance(item, Writing):
            results.append(await WritingHistorySerializer.from_orm_async(item))

    return results


@router.get("/progress/", response_model=UserProgressSerializer, summary="Get user progress")
async def get_user_progress(user=Depends(active_user)):
    """
    Get progress statistics for the current user.
    """
    latest_analysis = await UserProgressService.get_latest_analysis(user.id)
    highest_score = await UserProgressService.get_highest_score(user.id)
    return UserProgressSerializer(
        latest_analysis=latest_analysis,
        highest_score=highest_score
    )


@router.get("/stats/", response_model=MainStatsSerializer, summary="Get main statistics")
async def get_main_stats(user=Depends(active_user)):
    """
    Get main statistics for the current user.
    """
    speaking = await SpeakingAnalyse.filter(speaking__user_id=user.id).order_by("-speaking__start_time").first()
    speaking_score = speaking.overall_band_score if speaking else 0

    reading = await Reading.filter(user_id=user.id).order_by("-start_time").first()
    reading_score = reading.score if reading else 0

    writing = await WritingAnalyse.filter(writing__user_id=user.id).order_by("-writing__start_time").first()
    writing_score = writing.overall_band_score if writing else 0

    listening = await ListeningAnalyse.filter(user_id=user.id).order_by("-session__start_time").first()
    listening_score = listening.overall_score if listening else 0

    return MainStatsSerializer(
        speaking=speaking_score,
        reading=reading_score,
        writing=writing_score,
        listening=listening_score,
    )