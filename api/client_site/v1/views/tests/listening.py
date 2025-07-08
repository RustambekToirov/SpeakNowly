import asyncio
import os
from fastapi import APIRouter, Depends, status, Request, HTTPException, UploadFile, File
from typing import Dict, Any, List
from aiofiles import open as aio_open

from models.transactions import TransactionType
from models.tests.listening import (
    Listening, ListeningPart, ListeningSection, ListeningQuestion,
    ListeningQuestionType, ListeningPartNumber
)
from models.users import User
from ...serializers.tests import (
    ListeningDataSlimSerializer,
    ListeningPartSerializer,
    ListeningAnswerSerializer,
    ListeningAnalyseResponseSerializer,
    ListeningSessionExamSerializer,
    ListeningTestCreate,
)
from services.tests import ListeningService
from utils.auth import active_user, admin_required
from utils import get_translation, check_user_tokens
from utils.arq_pool import get_arq_redis

router = APIRouter()


async def _serialize_listening_session(data):
    session_obj = type("SessionObj", (), {
        "id": data["session_id"],
        "status": data["status"],
        "start_time": data["start_time"],
        "end_time": data["end_time"],
    })()
    exam = await ListeningSessionExamSerializer.from_orm(data["exam"])
    parts = await asyncio.gather(*(ListeningPartSerializer.from_orm(p) for p in data["parts"]))
    return ListeningDataSlimSerializer(
        session_id=session_obj.id,
        status=session_obj.status,
        start_time=session_obj.start_time,
        end_time=session_obj.end_time,
        exam=exam,
        parts=parts,
    )


@router.post(
    "/start/",
    response_model=ListeningDataSlimSerializer,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new listening session"
)
async def start_listening_test(
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
    request: Request = None,
    redis=Depends(get_arq_redis),
):
    await check_user_tokens(user, TransactionType.TEST_LISTENING, request, t)
    session_data = await ListeningService.start_session(user, t)
    return await _serialize_listening_session(session_data)


@router.get(
    "/session/{session_id}/",
    response_model=ListeningDataSlimSerializer,
    status_code=status.HTTP_200_OK,
    summary="Get listening session details"
)
async def get_listening_session(
    session_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
):
    """
    Get details of a listening session.
    """
    data = await ListeningService.get_session_data(session_id, user.id, t)
    return await _serialize_listening_session(data)


@router.get(
    "/parts/{part_id}/",
    response_model=ListeningPartSerializer,
    status_code=status.HTTP_200_OK,
    summary="Get listening part"
)
async def get_listening_part(
    part_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
):
    """
    Get details of a listening part (sections and questions).
    """
    part = await ListeningService.get_part(part_id, t)
    return await ListeningPartSerializer.from_orm(part)


@router.post(
    "/session/{session_id}/submit/",
    status_code=status.HTTP_201_CREATED,
    summary="Submit answers for a listening session"
)
async def submit_listening_answers(
    session_id: int,
    payload: ListeningAnswerSerializer,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
    redis=Depends(get_arq_redis),
):
    result = await ListeningService.submit_answers(session_id, user.id, payload.answers, t)
    await redis.enqueue_job("analyse_listening", session_id=session_id)
    return result


@router.post(
    "/session/{session_id}/cancel/",
    status_code=status.HTTP_200_OK,
    summary="Cancel a listening session"
)
async def cancel_listening_session(
    session_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
):
    """
    Cancel a listening session.
    """
    result = await ListeningService.cancel_session(session_id, user.id, t)
    return result


@router.post(
    "/session/{session_id}/restart/",
    status_code=status.HTTP_200_OK,
    summary="Restart a listening session"
)
async def restart_listening_session(
    session_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
):
    """
    Restart a listening session.
    """
    result = await ListeningService.restart_session(session_id, user.id, t)
    return result


@router.get(
    "/session/{session_id}/analysis/",
    response_model=ListeningAnalyseResponseSerializer,
    status_code=status.HTTP_200_OK,
    summary="Get analysis for a completed listening session"
)
async def get_listening_analysis(
    session_id: int,
    user=Depends(active_user),
    t: Dict[str, str] = Depends(get_translation),
    request: Request = None,
):
    """
    Get analysis for a completed listening session.
    """
    result = await ListeningService.get_analysis(session_id, user.id, t, request)
    return result


# --- Upload Audio File ---
@router.post(
    "/upload-audio/",
    status_code=201,
    summary="Upload audio file for listening part"
)
async def upload_audio(
    file: UploadFile = File(...),
    user: User = Depends(admin_required)
):
    dir_path = "media/audio"
    os.makedirs(dir_path, exist_ok=True)
    file_location = f"{dir_path}/{file.filename}"
    async with aio_open(file_location, "wb") as f:
        content = await file.read()
        await f.write(content)
    return {"filename": file.filename, "url": f"/media/audio/{file.filename}"}

# --- Get Audio Links ---
@router.get(
    "/audio-links/",
    response_model=List[str],
    summary="Get all audio file links from media/audio directory"
)
async def get_audio_links(
    user: User = Depends(admin_required)
):
    dir_path = "media/audio"
    if not os.path.exists(dir_path):
        return []
    files = [
        f"/media/audio/{filename}"
        for filename in os.listdir(dir_path)
        if os.path.isfile(os.path.join(dir_path, filename))
    ]
    return files

# --- Create Listening Test ---
@router.post(
    "/create/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new listening test"
)
async def create_listening_test(
    data: ListeningTestCreate,
    user: User = Depends(admin_required),
    t: Dict[str, str] = Depends(get_translation)
):
    """
    Create a new listening test with parts, sections, and questions.
    """
    data = data.dict()
    listening = await Listening.create(
        title=data["title"],
        description=data.get("description", "")
    )
    # Create parts
    for part_data in data.get("parts", []):
        audio_file = part_data["audio_file"]
        if not audio_file.startswith("/media/audio/"):
            audio_file = f"/media/audio/{audio_file}"
        part = await ListeningPart.create(
            listening=listening,
            part_number=ListeningPartNumber(part_data["part_number"]),
            audio_file=audio_file
        )
        # Create sections
        for section_data in part_data.get("sections", []):
            # Ensure options is a list
            options = section_data.get("options", [])
            if not isinstance(options, list):
                options = [options]
            section = await ListeningSection.create(
                part=part,
                section_number=section_data["section_number"],
                start_index=section_data["start_index"],
                end_index=section_data["end_index"],
                question_type=ListeningQuestionType(section_data["question_type"]),
                question_text=section_data.get("question_text"),
                options=options
            )
            # Create questions
            for q_data in section_data.get("questions", []):
                q_options = q_data.get("options", [])
                if not isinstance(q_options, list):
                    q_options = [q_options]
                await ListeningQuestion.create(
                    section=section,
                    index=q_data["index"],
                    question_text=q_data.get("question_text"),
                    options=q_options,
                    correct_answer=q_data["correct_answer"]
                )
    return {"id": listening.id, "message": "Listening test created"}

# --- Read (list all) Listening Tests ---
@router.get(
    "/all/",
    status_code=status.HTTP_200_OK,
    summary="List all listening tests"
)
async def list_listening_tests(
    user: User = Depends(admin_required),
    t: Dict[str, str] = Depends(get_translation)
):
    tests = await Listening.all().prefetch_related("parts")
    return [
        {
            "id": test.id,
            "title": test.title,
            "description": test.description,
            "parts": [
                {
                    "id": part.id,
                    "part_number": part.part_number,
                    "audio_file": part.audio_file
                }
                for part in await test.parts.all()
            ]
        }
        for test in tests
    ]

# --- Read (get one) Listening Test ---
@router.get(
    "/{test_id}/",
    status_code=status.HTTP_200_OK,
    summary="Get listening test by ID"
)
async def get_listening_test(
    test_id: int,
    user: User = Depends(admin_required),
    t: Dict[str, str] = Depends(get_translation)
):
    test = await Listening.get_or_none(id=test_id)
    if not test:
        raise HTTPException(status_code=404, detail=t.get("test_not_found", "Listening test not found"))
    parts = await test.parts.all().prefetch_related("sections")
    return {
        "id": test.id,
        "title": test.title,
        "description": test.description,
        "parts": [
            {
                "id": part.id,
                "part_number": part.part_number,
                "audio_file": part.audio_file,
                "sections": [
                    {
                        "id": section.id,
                        "section_number": section.section_number,
                        "question_type": section.question_type,
                        "question_text": section.question_text,
                        "options": section.options,
                        "questions": [
                            {
                                "id": q.id,
                                "index": q.index,
                                "question_text": q.question_text,
                                "options": q.options,
                                "correct_answer": q.correct_answer
                            }
                            for q in await section.questions.all()
                        ]
                    }
                    for section in await part.sections.all()
                ]
            }
            for part in parts
        ]
    }

# --- Update Listening Test ---
@router.put(
    "/{test_id}/",
    status_code=status.HTTP_200_OK,
    summary="Update listening test"
)
async def update_listening_test(
    test_id: int,
    data: Dict[str, Any],
    user: User = Depends(admin_required),
    t: Dict[str, str] = Depends(get_translation)
):
    test = await Listening.get_or_none(id=test_id)
    if not test:
        raise HTTPException(status_code=404, detail=t.get("test_not_found", "Listening test not found"))
    test.title = data.get("title", test.title)
    test.description = data.get("description", test.description)
    if "parts" in data:
        for part_data in data["parts"]:
            audio_file = part_data.get("audio_file")
            if audio_file and not audio_file.startswith("/media/audio/"):
                part_data["audio_file"] = f"/media/audio/{audio_file}"

    await test.save()
    return {"id": test.id, "message": "Listening test updated"}

# --- Delete Listening Test ---
@router.delete(
    "/{test_id}/",
    status_code=status.HTTP_200_OK,
    summary="Delete listening test"
)
async def delete_listening_test(
    test_id: int,
    user: User = Depends(admin_required),
    t: Dict[str, str] = Depends(get_translation)
):
    test = await Listening.get_or_none(id=test_id)
    if not test:
        raise HTTPException(status_code=404, detail=t.get("test_not_found", "Listening test not found"))
    await test.delete()
    return {"message": "Listening test deleted"}
