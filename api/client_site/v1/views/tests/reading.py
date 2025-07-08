from fastapi import APIRouter, Depends, status, Request, HTTPException
from typing import Dict, Any

from models.transactions import TransactionType
from ...serializers.tests.reading import (
    ReadingSessionSerializer,
    PassageSerializer,
    SubmitPassageAnswerSerializer,
)
from services.tests import ReadingService
from utils.auth import active_user
from utils import get_translation, check_user_tokens
from utils.arq_pool import get_arq_redis

router = APIRouter()

@router.post(
    "/start/",
    response_model=ReadingSessionSerializer,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new reading session"
)
async def start_reading_test(
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
    request: Request = None,
):
    """
    Start a new reading test session.
    """
    await check_user_tokens(user, TransactionType.TEST_READING, request, t)
    session_data = await ReadingService.start_session(user.id, t)
    from models.tests import Reading
    session = await Reading.get_or_none(id=session_data["id"], user_id=user.id)
    if not session:
        raise HTTPException(status_code=404, detail=t["session_not_found"])
    return await ReadingSessionSerializer.from_orm(session)

@router.get(
    "/{session_id}/",
    response_model=ReadingSessionSerializer,
    status_code=status.HTTP_200_OK,
    summary="Get reading session details"
)
async def get_reading_session(
    session_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
):
    """
    Get details of a reading session.
    """
    from models.tests import Reading
    session = await Reading.get_or_none(id=session_id, user_id=user.id)
    if not session:
        raise HTTPException(status_code=404, detail=t["session_not_found"])
    return await ReadingSessionSerializer.from_orm(session)

@router.post(
    "/{session_id}/submit/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Submit answers for a passage in session"
)
async def submit_passage_answers(
    session_id: int,
    payload: SubmitPassageAnswerSerializer,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
):
    """
    Save answers for a passage in a reading session (no analysis here).
    """
    answers = await ReadingService.submit_answers(
        session_id=session_id,
        user_id=user.id,
        passage_id=payload.passage_id,
        answers=[a.dict() for a in payload.answers],
        t=t
    )
    return {"message": t["answers_submitted"]}

@router.post(
    "/{session_id}/finish/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Finish reading session"
)
async def finish_reading(
    session_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
):
    """
    Finish a reading session.
    """
    result = await ReadingService.finish_session(session_id, user.id, t)
    return result

@router.post(
    "/{session_id}/cancel/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Cancel reading session"
)
async def cancel_reading(
    session_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
):
    """
    Cancel a reading session.
    """
    return await ReadingService.cancel_session(session_id, user.id, t)

@router.post(
    "/{session_id}/restart/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Restart reading session"
)
async def restart_reading(
    session_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
):
    """
    Restart a reading session.
    """
    return await ReadingService.restart_session(session_id, user.id, t)

@router.get(
    "/{session_id}/analysis/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get reading analysis"
)
async def analyse_reading(
    session_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
):
    """
    Get analysis for a completed reading session.
    """
    result = await ReadingService.get_analysis(session_id, user.id, t)
    return result