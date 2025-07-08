from fastapi import HTTPException, status, UploadFile
from typing import Dict, Any, Optional
from tortoise.transactions import in_transaction
from datetime import datetime, timezone
import json
import os
from uuid import uuid4
from pathlib import Path
import aiofiles

from models.tests import (
    Speaking,
    SpeakingAnswer,
    SpeakingQuestion,
    SpeakingStatus,
    TestTypeEnum,
    SpeakingPart,
)
from services.analyses import SpeakingAnalyseService
from services.chatgpt.speaking_integration import ChatGPTSpeakingIntegration
from utils.get_actual_price import get_user_actual_test_price
from models import TokenTransaction, TransactionType, User
from config import BASE_DIR

MEDIA_ROOT = BASE_DIR / "media" / "user_audios"
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

PART_MAP = {
    "part1": SpeakingPart.PART_1.value,
    "part2": SpeakingPart.PART_2.value,
    "part3": SpeakingPart.PART_3.value,
}

async def save_upload_file_async(upload_file: UploadFile, folder: Path = MEDIA_ROOT) -> str:
    """
    Save uploaded audio file with unique name.
    """
    ext = os.path.splitext(upload_file.filename)[1]
    filename = f"{uuid4().hex}{ext}"
    file_path = folder / filename
    async with aiofiles.open(file_path, "wb") as out_file:
        while True:
            chunk = await upload_file.read(1024 * 1024)
            if not chunk:
                break
            await out_file.write(chunk)
    await upload_file.seek(0)
    return str(file_path.relative_to(BASE_DIR))

class SpeakingService:
    """
    Service for managing speaking tests and sessions.
    """

    @staticmethod
    async def start_session(user, t: dict) -> Dict[str, Any]:
        """
        Start a new speaking session with AI-generated questions.
        """
        # Check if user has enough tokens
        price = await get_user_actual_test_price(user, TestTypeEnum.SPEAKING_ENG)
        if user.tokens < price:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=t.get("insufficient_tokens", "Insufficient tokens")
            )

        # Generate questions using ChatGPT
        chatgpt = ChatGPTSpeakingIntegration()
        try:
            questions_data = await chatgpt.generate_ielts_speaking_questions(user_id=user.id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=t.get("question_generation_failed", "Failed to generate questions")
            )

        # Create session transaction
        async with in_transaction():
            # Deduct tokens
            user.tokens -= price
            await user.save()
            await TokenTransaction.create(
                user_id=user.id,
                transaction_type=TransactionType.TEST_SPEAKING,
                amount=price,
                balance_after_transaction=user.tokens,
                description=t.get("transaction_description", f"Speaking test (-{price} tokens)"),
            )

            # Create session
            session = await Speaking.create(
                user_id=user.id,
                start_time=datetime.now(timezone.utc),
                status=SpeakingStatus.STARTED.value,
            )

            # Create questions for each part
            for part_key in ["part1", "part2", "part3"]:
                q = questions_data.get(part_key)
                if not q:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=t.get("question_parsing_failed", "Failed parsing questions")
                    )
                content = q["question"]
                if isinstance(content, str):
                    try:
                        content = json.loads(content)
                    except Exception:
                        content = [content]
                await SpeakingQuestion.create(
                    speaking=session,
                    part=PART_MAP[part_key],
                    title=q["title"],
                    content=content,
                )

        return await SpeakingService.get_session(session.id, user.id, t)

    @staticmethod
    async def get_session(session_id: int, user_id: int, t: dict) -> Dict[str, Any]:
        """
        Retrieve speaking session with questions.
        """
        session = await Speaking.get_or_none(id=session_id, user_id=user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t.get("session_not_found", "Session not found")
            )
            
        questions = await SpeakingQuestion.filter(speaking=session).order_by("part")
        part_map = {q.part: q for q in questions}
        
        return {
            "id": session.id,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "status": session.status,
            "questions": {
                "part1": {
                    "id": part_map[SpeakingPart.PART_1.value].id,
                    "title": part_map[SpeakingPart.PART_1.value].title,
                    "content": part_map[SpeakingPart.PART_1.value].content,
                },
                "part2": {
                    "id": part_map[SpeakingPart.PART_2.value].id,
                    "title": part_map[SpeakingPart.PART_2.value].title,
                    "content": part_map[SpeakingPart.PART_2.value].content,
                },
                "part3": {
                    "id": part_map[SpeakingPart.PART_3.value].id,
                    "title": part_map[SpeakingPart.PART_3.value].title,
                    "content": part_map[SpeakingPart.PART_3.value].content,
                },
            },
            "analyse": None,
        }

    @staticmethod
    async def submit_answers(
        session_id: int, user_id: int, audio_files: Dict[str, Optional[UploadFile]], t: dict, lang_code: str = "en"
    ) -> Dict[str, Any]:
        """
        Submit audio answers and perform analysis.
        """
        # Validate session exists
        session = await Speaking.get_or_none(id=session_id, user_id=user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t.get("session_not_found", "Session not found")
            )

        # Check if already completed
        if session.status in [SpeakingStatus.COMPLETED.value, SpeakingStatus.CANCELLED.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=t.get("session_already_completed_or_cancelled", "Session already completed or cancelled")
            )

        # Validate questions
        questions = await SpeakingQuestion.filter(speaking=session).order_by("part")
        if len(questions) != 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=t.get("invalid_question_count", "Invalid question count")
            )

        part_map = {q.part: q for q in questions}
        chatgpt = ChatGPTSpeakingIntegration()

        # Process audio files and save answers
        async with in_transaction():
            # Part 1 is required
            if not audio_files.get("part1"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=t.get("part1_audio_required", "Part 1 audio is required")
                )
                
            answers = {}
            for part_key in ["part1", "part2", "part3"]:
                audio = audio_files.get(part_key)
                if not audio:
                    continue
                    
                question = part_map.get(PART_MAP[part_key])
                if not question:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=t.get("question_not_found", f"Question for {part_key} not found")
                    )
                    
                # Save audio and transcribe
                audio_path = await save_upload_file_async(audio)
                text = await chatgpt.transcribe_audio_file_async(audio)
                
                # Save answer
                answer = await SpeakingAnswer.create(
                    question=question,
                    audio_answer=audio_path,
                    text_answer=text,
                )
                answers[part_key] = answer

            # Mark session as completed
            session.status = SpeakingStatus.COMPLETED.value
            session.end_time = datetime.now(timezone.utc)
            await session.save(update_fields=["status", "end_time"])

            # Get analysis
            analyse = await SpeakingAnalyseService.analyse(session.id, lang_code=lang_code, t=t)
            if not analyse:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=t.get("analysis_not_found", "Failed to generate analysis")
                )

        return {
            "message": t.get("answers_submitted", "Answers submitted successfully"),
            "analysis": analyse,
        }

    @staticmethod
    async def cancel_session(session_id: int, user_id: int, t: dict) -> dict:
        """
        Cancel a speaking session.
        """
        session = await Speaking.get_or_none(id=session_id, user_id=user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t.get("session_not_found", "Session not found")
            )

        if session.status in [SpeakingStatus.COMPLETED.value, SpeakingStatus.CANCELLED.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=t.get("cannot_cancel_session", "Cannot cancel completed or already cancelled session")
            )

        session.status = SpeakingStatus.CANCELLED.value
        await session.save(update_fields=["status"])
        return {"message": t.get("session_cancelled", "Session cancelled")}

    @staticmethod
    async def restart_session(session_id: int, user_id: int, t: dict) -> dict:
        """
        Restart a speaking session.
        """
        session = await Speaking.get_or_none(id=session_id, user_id=user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t.get("session_not_found", "Session not found")
            )

        if session.status not in [SpeakingStatus.COMPLETED.value, SpeakingStatus.CANCELLED.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=t.get("cannot_restart_session", "Cannot restart active session")
            )

        # Delete existing answers
        await SpeakingAnswer.filter(question__speaking=session).delete()
        
        # Reset session
        session.status = SpeakingStatus.STARTED.value
        session.start_time = datetime.now(timezone.utc)
        session.end_time = None
        await session.save(update_fields=["status", "start_time", "end_time"])
        return {"message": t.get("session_restarted", "Session restarted")}
    
    @staticmethod
    async def get_analysis(session_id: int, user_id: int, t: dict, request=None) -> Dict[str, Any]:
        """
        Get analysis for a completed session.
        """
        session = await Speaking.get_or_none(id=session_id, user_id=user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t.get("session_not_found", "Session not found")
            )
        if session.status != SpeakingStatus.COMPLETED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=t.get("session_not_completed", "Session not completed")
            )
        lang_code = "en"
        if request:
            lang_code = request.headers.get("Accept-Language", "en").split(",")[0].lower()
        analyse = await SpeakingAnalyseService.analyse(session.id, lang_code=lang_code, t=t)
        
        return {
            "analysis": {
                "feedback": analyse["feedback"],
                "overall_band_score": analyse["overall_band_score"],
                
                "fluency_and_coherence_score": analyse["fluency_and_coherence_score"],
                "fluency_and_coherence_feedback": analyse["fluency_and_coherence_feedback"],
                
                "lexical_resource_score": analyse["lexical_resource_score"],
                "lexical_resource_feedback": analyse["lexical_resource_feedback"],
                
                "grammatical_range_and_accuracy_score": analyse["grammatical_range_and_accuracy_score"],
                "grammatical_range_and_accuracy_feedback": analyse["grammatical_range_and_accuracy_feedback"],
                
                "pronunciation_score": analyse["pronunciation_score"],
                "pronunciation_feedback": analyse["pronunciation_feedback"],
                
                "timing": analyse["timing"],
            }
        }

