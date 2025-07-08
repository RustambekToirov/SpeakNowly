from fastapi import HTTPException, status
from datetime import timedelta
from models.analyses import ListeningAnalyse
from models.tests import ListeningSession, ListeningAnswer, ListeningSessionStatus

class ListeningAnalyseService:
    @staticmethod
    async def analyse(session_id: int) -> ListeningAnalyse:
        """
        Analyse a completed Listening session and save the result.
        """
        session = await ListeningSession.get_or_none(id=session_id)
        if not session:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Listening session not found")
        
        if session.status != ListeningSessionStatus.COMPLETED:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Listening session is not completed")
        
        existing = await ListeningAnalyse.get_or_none(session_id=session_id)
        if existing:
            return existing
        
        responses = await ListeningAnswer.filter(session_id=session_id)
        correct_count = sum(1 for r in responses if r.is_correct)

        # IELTS Listening band conversion table (Academic/General Training)
        def calculate_score(correct):
            mapping = {
                range(39, 41): 9.0,
                range(37, 39): 8.5,
                range(35, 37): 8.0,
                range(32, 35): 7.5,
                range(30, 32): 7.0,
                range(26, 30): 6.5,
                range(23, 26): 6.0,
                range(18, 23): 5.5,
                range(16, 18): 5.0,
                range(13, 16): 4.5,
                range(10, 13): 4.0,
                range(7, 10): 3.5,
                range(5, 7): 3.0,
                range(3, 5): 2.5,
                range(1, 3): 2.0,
                range(0, 1): 0.0,
            }
            for score_range, band in mapping.items():
                if correct in score_range:
                    return band
            return 0.0

        band_score = calculate_score(correct_count)
        duration = (session.end_time - session.start_time) if (session.start_time and session.end_time) else timedelta(0)

        analyse_obj = await ListeningAnalyse.create(
            session_id=session_id,
            user_id=session.user_id,
            correct_answers=correct_count,
            overall_score=band_score,
            duration=duration,
        )
        
        return analyse_obj