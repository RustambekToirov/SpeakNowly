from fastapi import APIRouter, Depends, status, HTTPException, Request
from typing import Dict, Any, Optional

from models.transactions import TransactionType

from ...serializers.tests.writing import WritingSerializer, WritingSubmitRequest
from services.tests import WritingService
from models.tests import TestTypeEnum
from utils.auth import active_user
from utils import get_translation, check_user_tokens

router = APIRouter()


@router.post(
    "/start/",
    response_model=WritingSerializer,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new writing session"
)
async def start_writing_test(
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
    request: Request = None,
):
    """
    Start a new writing test session.
    """
    await check_user_tokens(user, TransactionType.TEST_WRITING, request, t)
    session_data = await WritingService.start_session(user, t)
    return await WritingSerializer.from_orm(session_data)


@router.get(
    "/{session_id}/",
    response_model=WritingSerializer,
    status_code=status.HTTP_200_OK,
    summary="Get writing session details"
)
async def get_writing_session(
    session_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
):
    """
    Get details of a writing session.
    """
    session_data = await WritingService.get_session(session_id, user.id, t)
    return await WritingSerializer.from_orm(session_data)


@router.post(
    "/session/{session_id}/submit/",
    status_code=status.HTTP_201_CREATED,
    summary="Submit answers for a writing session"
)
async def submit_writing_answers(
    session_id: int,
    payload: WritingSubmitRequest,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
    request: Request = None,
):
    lang_code = "en"
    if request:
        lang_code = request.headers.get("accept-language", "en").split(",")[0].lower()

    result = await WritingService.submit_answers(
        session_id=session_id,
        user_id=user.id,
        part1_answer=payload.part1_answer,
        part2_answer=payload.part2_answer,
        t=t,
        lang_code=lang_code,
    )
    return result


@router.post(
    "/session/{session_id}/cancel/",
    status_code=status.HTTP_200_OK,
    summary="Cancel a writing session"
)
async def cancel_writing_session(
    session_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
):
    """
    Cancel a writing session.
    """
    result = await WritingService.cancel_session(session_id, user.id, t)
    return result


@router.post(
    "/session/{session_id}/restart/",
    status_code=status.HTTP_200_OK,
    summary="Restart a writing session"
)
async def restart_writing_session(
    session_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
):
    result = await WritingService.restart_session(session_id, user.id, t)
    return result


@router.get(
    "/session/{session_id}/analysis/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get analysis for a completed writing session"
)
async def get_writing_analysis(
    session_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
    request: Request = None,
):
    """
    Get analysis for a completed writing session.
    """
    result = await WritingService.get_analysis(session_id, user.id, t, request)
    return result