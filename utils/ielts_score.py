from models.analyses import ListeningAnalyse, SpeakingAnalyse, WritingAnalyse
from models.tests import Reading

class IELTSScoreCalculator:
    """
    Calculates average IELTS scores for users.
    """

    @classmethod
    async def get_average_score(cls, queryset, field: str) -> float:
        """
        Calculates average score for specified field in queryset.
        """
        values = [getattr(obj, field, 0) for obj in queryset if getattr(obj, field, None) is not None]
        return sum(values) / len(values) if values else 0

    @classmethod
    async def calculate(cls, user) -> float:
        """
        Calculates overall IELTS score from all test components.
        """
        listening = await ListeningAnalyse.filter(user_id=user.id).all()
        listening_avg = await cls.get_average_score(listening, "overall_score")

        speaking = await SpeakingAnalyse.filter(speaking__user_id=user.id).all()
        speaking_avg = await cls.get_average_score(speaking, "overall_band_score")

        writing = await WritingAnalyse.filter(writing__user_id=user.id).all()
        writing_avg = await cls.get_average_score(writing, "overall_band_score")

        reading = await Reading.filter(user_id=user.id).all()
        reading_avg = await cls.get_average_score(reading, "score")

        total_score = (listening_avg + speaking_avg + writing_avg + reading_avg) / 4
        return round(total_score * 2) / 2