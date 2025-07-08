from fastapi import HTTPException, status
from typing import Dict, Any
from tortoise.transactions import in_transaction
from datetime import datetime, timezone

from models.tests import (
    Writing,
    WritingPart1,
    WritingPart2,
    WritingStatus,
    TestTypeEnum,
)
from services.analyses.writing_analyse_service import WritingAnalyseService
from services.chatgpt.writing_integration import ChatGPTWritingIntegration
from utils.get_actual_price import get_user_actual_test_price
from models import TokenTransaction, TransactionType, User

class WritingService:
    """
    Service for managing writing tests and sessions.
    """

    @staticmethod
    async def start_session(user, t: dict) -> Dict[str, Any]:
        """
        Start a new writing session for a user with questions and diagrams.
        """
        # Check if user has enough tokens
        price = await get_user_actual_test_price(user, TestTypeEnum.WRITING_ENG)
        if user.tokens < price:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=t.get("insufficient_tokens", "Insufficient tokens")
            )

        # Generate questions using ChatGPT
        chatgpt = ChatGPTWritingIntegration()
        part1_data = await chatgpt.generate_writing_part1_question(user_id=user.id)
        part2_data = await chatgpt.generate_writing_part2_question(user_id=user.id)

        # Extract part 1 data
        part1_question = part1_data["question"]
        chart_type = part1_data["chart_type"]
        categories = part1_data["categories"]
        year1 = part1_data["year1"]
        year2 = part1_data["year2"]
        data_year1 = part1_data["data_year1"]
        data_year2 = part1_data["data_year2"]

        # Validate chart type
        if chart_type not in ["bar", "line", "pie"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=t.get("unknown_chart_type", "Unknown chart type")
            )

        # Generate diagram
        if chart_type == "bar":
            diagram_path = chatgpt.create_bar_chart(categories, year1, year2, data_year1, data_year2)
        elif chart_type == "line":
            diagram_path = chatgpt.create_line_chart(categories, year1, year2, data_year1, data_year2)
        elif chart_type == "pie":
            diagram_path = chatgpt.create_pie_chart(categories, year1, year2, data_year1, data_year2)
        diagram_path = diagram_path.replace("media/", "")

        part2_question = part2_data["question"]

        # Create test session transaction
        async with in_transaction():
            # Deduct tokens
            user.tokens -= price
            await user.save()
            await TokenTransaction.create(
                user_id=user.id,
                transaction_type=TransactionType.TEST_WRITING,
                amount=price,
                balance_after_transaction=user.tokens,
                description=t.get("transaction_description", f"Writing test (-{price} tokens)").format(price=price),
            )

            # Create writing session
            writing = await Writing.create(
                user_id=user.id,
                status=WritingStatus.STARTED.value,
                start_time=datetime.now(timezone.utc),
            )

            # Create writing parts
            diagram_data = {
                "categories": categories,
                "year1": year1,
                "year2": year2,
                "data_year1": data_year1,
                "data_year2": data_year2,
            }
            await WritingPart1.create(
                writing=writing,
                content=part1_question,
                diagram=diagram_path,
                diagram_data=diagram_data,
                answer="",
            )
            await WritingPart2.create(
                writing=writing,
                content=part2_question,
                answer="",
            )

        return await WritingService.get_session(writing.id, user.id, t)

    @staticmethod
    async def get_session(session_id: int, user_id: int, t: dict) -> "Writing":
        """
        Retrieve a writing session and its questions.
        """
        writing = await Writing.get_or_none(id=session_id, user_id=user_id)
        if not writing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t.get("session_not_found", "Session not found")
            )
        return writing

    @staticmethod
    async def submit_answers(
        session_id: int, user_id: int, part1_answer: str, part2_answer: str, t: dict, lang_code: str = "en"
    ) -> Dict[str, Any]:
        """
        Submit answers and perform analysis.
        """
        # Validate session exists
        writing = await Writing.get_or_none(id=session_id, user_id=user_id).prefetch_related("part1", "part2")
        if not writing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t.get("session_not_found", "Session not found")
            )

        # Check if already completed
        if writing.status in [WritingStatus.COMPLETED.value, WritingStatus.CANCELLED.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=t.get("session_already_completed_or_cancelled", "Session already completed or cancelled")
            )

        # Save answers and complete session
        async with in_transaction():
            if part1_answer:
                writing.part1.answer = part1_answer
                await writing.part1.save()
            if part2_answer:
                writing.part2.answer = part2_answer
                await writing.part2.save()

            writing.status = WritingStatus.COMPLETED.value
            writing.end_time = datetime.now(timezone.utc)
            await writing.save(update_fields=["status", "end_time"])

        # Get analysis
        writing_analyse = await WritingAnalyseService.analyse(writing.id, lang_code=lang_code, t=t)

        # Return results
        return {
            "message": t.get("answers_submitted", "Answers submitted successfully"),
            "analysis": {
                "task_achievement_feedback": writing_analyse.task_achievement_feedback,
                "task_achievement_score": float(writing_analyse.task_achievement_score) 
                    if writing_analyse.task_achievement_score is not None else None,
                
                "lexical_resource_feedback": writing_analyse.lexical_resource_feedback,
                "lexical_resource_score": float(writing_analyse.lexical_resource_score) 
                    if writing_analyse.lexical_resource_score is not None else None,
                
                "coherence_and_cohesion_feedback": writing_analyse.coherence_and_cohesion_feedback,
                "coherence_and_cohesion_score": float(writing_analyse.coherence_and_cohesion_score) 
                    if writing_analyse.coherence_and_cohesion_score is not None else None,
                
                "grammatical_range_and_accuracy_feedback": writing_analyse.grammatical_range_and_accuracy_feedback,
                "grammatical_range_and_accuracy_score": float(writing_analyse.grammatical_range_and_accuracy_score) 
                    if writing_analyse.grammatical_range_and_accuracy_score is not None else None,
                
                "word_count_feedback": writing_analyse.word_count_feedback,
                "word_count_score": float(writing_analyse.word_count_score) 
                    if writing_analyse.word_count_score is not None else None,
                
                "overall_band_score": float(writing_analyse.overall_band_score) 
                    if writing_analyse.overall_band_score is not None else None,
                
                "total_feedback": writing_analyse.total_feedback,
                "timing": writing_analyse.duration.total_seconds() if writing_analyse.duration else None,
            },
        }

    @staticmethod
    async def cancel_session(session_id: int, user_id: int, t: dict) -> dict:
        """
        Cancel a writing session.
        """
        writing = await Writing.get_or_none(id=session_id, user_id=user_id)
        if not writing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t.get("session_not_found", "Session not found")
            )

        if writing.status in [WritingStatus.COMPLETED.value, WritingStatus.CANCELLED.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=t.get("cannot_cancel_session", "Cannot cancel completed or already cancelled session")
            )

        writing.status = WritingStatus.CANCELLED.value
        await writing.save(update_fields=["status"])
        return {"message": t.get("session_cancelled", "Session cancelled")}

    @staticmethod
    async def restart_session(session_id: int, user_id: int, t: dict) -> dict:
        """
        Restart a writing session.
        """
        writing = await Writing.get_or_none(id=session_id, user_id=user_id)
        if not writing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t.get("session_not_found", "Session not found")
            )

        if writing.status not in [WritingStatus.COMPLETED.value, WritingStatus.CANCELLED.value, WritingStatus.EXPIRED.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=t.get("cannot_restart_session", "Cannot restart active session")
            )

        # Reset answers
        part1 = await WritingPart1.get_or_none(writing=writing)
        part2 = await WritingPart2.get_or_none(writing=writing)
        if part1:
            part1.answer = ""
            await part1.save(update_fields=["answer"])
        if part2:
            part2.answer = ""
            await part2.save(update_fields=["answer"])

        # Reset session
        writing.status = WritingStatus.STARTED.value
        writing.start_time = datetime.now(timezone.utc)
        writing.end_time = None
        await writing.save(update_fields=["status", "start_time", "end_time"])
        return {"message": t.get("session_restarted", "Session restarted")}

    @staticmethod
    async def get_analysis(session_id: int, user_id: int, t: dict, request=None) -> Dict[str, Any]:
        """
        Get analysis for a completed session.
        """
        writing = await Writing.get_or_none(id=session_id, user_id=user_id)
        if not writing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t.get("session_not_found", "Session not found")
            )
        if writing.status != WritingStatus.COMPLETED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=t.get("session_not_completed", "Session not completed")
            )
        
        lang_code = "en"
        if request:
            lang_code = request.headers.get("Accept-Language", "en").split(",")[0].lower()
        analyse = await WritingAnalyseService.analyse(writing.id, lang_code=lang_code, t=t)
        
        return {
            "analysis": {
                "task_achievement_feedback": analyse.task_achievement_feedback,
                "task_achievement_score": float(analyse.task_achievement_score) 
                    if analyse.task_achievement_score is not None else None,
                
                "lexical_resource_feedback": analyse.lexical_resource_feedback,
                "lexical_resource_score": float(analyse.lexical_resource_score) 
                    if analyse.lexical_resource_score is not None else None,
                
                "coherence_and_cohesion_feedback": analyse.coherence_and_cohesion_feedback,
                "coherence_and_cohesion_score": float(analyse.coherence_and_cohesion_score) 
                    if analyse.coherence_and_cohesion_score is not None else None,
                
                "grammatical_range_and_accuracy_feedback": analyse.grammatical_range_and_accuracy_feedback,
                "grammatical_range_and_accuracy_score": float(analyse.grammatical_range_and_accuracy_score) 
                    if analyse.grammatical_range_and_accuracy_score is not None else None,
                
                "word_count_feedback": analyse.word_count_feedback,
                "word_count_score": float(analyse.word_count_score) 
                    if analyse.word_count_score is not None else None,
                
                "overall_band_score": float(analyse.overall_band_score) 
                    if analyse.overall_band_score is not None else None,
                
                "total_feedback": analyse.total_feedback,
                "timing": analyse.duration.total_seconds() if analyse.duration else None,
            }
        }
