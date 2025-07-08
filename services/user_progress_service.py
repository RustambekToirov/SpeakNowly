from tortoise.functions import Max
from models.analyses import ListeningAnalyse, SpeakingAnalyse, WritingAnalyse
from models.tests import Reading

class UserProgressService:
    """
    Tracks and calculates user progress across different test types.
    Provides methods to retrieve latest scores and highest achievements.
    """

    @staticmethod
    async def get_latest_analysis(user_id: int):
        """
        Get user's latest test scores:
        1. Query latest listening analysis by session start time.
        2. Query latest speaking analysis by start time.
        3. Query latest writing analysis by start time.
        4. Query latest reading test by start time.
        5. Return dictionary with scores from each test type.
        """
        # 1. Query latest listening analysis
        latest_listening = await ListeningAnalyse.filter(user_id=user_id).order_by("-session__start_time").first()
        
        # 2. Query latest speaking analysis
        latest_speaking = await SpeakingAnalyse.filter(speaking__user_id=user_id).order_by("-speaking__start_time").first()
        
        # 3. Query latest writing analysis
        latest_writing = await WritingAnalyse.filter(writing__user_id=user_id).order_by("-writing__start_time").first()
        
        # 4. Query latest reading test
        latest_reading = await Reading.filter(user_id=user_id).order_by("-start_time").first()

        # 5. Return scores dictionary
        return {
            "listening": latest_listening.overall_score if latest_listening else None,
            "speaking": latest_speaking.overall_band_score if latest_speaking else None,
            "writing": latest_writing.overall_band_score if latest_writing else None,
            "reading": latest_reading.score if latest_reading else None,
        }

    @staticmethod
    async def get_highest_score(user_id: int):
        """
        Calculate user's highest overall IELTS score:
        1. Query all listening scores and find maximum.
        2. Query all speaking scores and find maximum.
        3. Query all writing scores and find maximum.
        4. Query all reading scores and find maximum.
        5. Calculate average of highest scores.
        6. Round to nearest 0.5 (IELTS standard).
        """
        # 1. Listening highest score
        listening_scores = await ListeningAnalyse.filter(user_id=user_id).values_list("overall_score", flat=True)
        max_listening = max(listening_scores) if listening_scores else 0

        # 2. Speaking highest score
        speaking_scores = await SpeakingAnalyse.filter(speaking__user_id=user_id).values_list("overall_band_score", flat=True)
        max_speaking = max(speaking_scores) if speaking_scores else 0

        # 3. Writing highest score
        writing_scores = await WritingAnalyse.filter(writing__user_id=user_id).values_list("overall_band_score", flat=True)
        max_writing = max(writing_scores) if writing_scores else 0

        # 4. Reading highest score
        reading_scores = await Reading.filter(user_id=user_id).values_list("score", flat=True)
        max_reading = max(reading_scores) if reading_scores else 0

        # 5. Calculate average
        max_scores = [
            max_listening or 0,
            max_speaking or 0,
            max_writing or 0,
            max_reading or 0,
        ]
        total = sum(max_scores) / 4
        
        # 6. Round to nearest 0.5 (IELTS standard)
        return round(total * 2) / 2
