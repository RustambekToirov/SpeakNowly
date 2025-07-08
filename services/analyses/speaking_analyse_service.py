from fastapi import HTTPException, status
from tortoise.transactions import in_transaction
from datetime import timedelta
from services.chatgpt import ChatGPTSpeakingIntegration
from models.analyses import SpeakingAnalyse
from models.tests import Speaking, SpeakingAnswer, SpeakingStatus

def analyse_to_dict(analyse: SpeakingAnalyse) -> dict:
    return {
        "feedback": analyse.feedback,
        "overall_band_score": float(analyse.overall_band_score) if analyse.overall_band_score is not None else None,
        "fluency_and_coherence_score": float(analyse.fluency_and_coherence_score) if analyse.fluency_and_coherence_score is not None else None,
        "fluency_and_coherence_feedback": analyse.fluency_and_coherence_feedback,
        "lexical_resource_score": float(analyse.lexical_resource_score) if analyse.lexical_resource_score is not None else None,
        "lexical_resource_feedback": analyse.lexical_resource_feedback,
        "grammatical_range_and_accuracy_score": float(analyse.grammatical_range_and_accuracy_score) if analyse.grammatical_range_and_accuracy_score is not None else None,
        "grammatical_range_and_accuracy_feedback": analyse.grammatical_range_and_accuracy_feedback,
        "pronunciation_score": float(analyse.pronunciation_score) if analyse.pronunciation_score is not None else None,
        "pronunciation_feedback": analyse.pronunciation_feedback,
        "timing": analyse.duration.total_seconds() if analyse.duration else None,
    }

class SpeakingAnalyseService:
    @staticmethod
    async def analyse(test_id: int, lang_code: str, t: dict) -> dict:
        test = await Speaking.get_or_none(id=test_id)
        if not test:
            raise HTTPException(status.HTTP_404_NOT_FOUND, t.get("speaking_test_not_found", "Speaking test not found"))
        if test.status != SpeakingStatus.COMPLETED.value:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, t.get("speaking_test_not_completed", "Speaking test is not completed"))

        existing = await SpeakingAnalyse.get_or_none(speaking_id=test.id)
        if existing:
            return analyse_to_dict(existing)

        answers = await SpeakingAnswer.filter(question__speaking_id=test_id).order_by("question__part").select_related("question")
        # Always prepare part1, part2, part3 (use fake if missing)
        fake_answer = type("FakeAnswer", (), {"question": type("Q", (), {"title": "", "content": ""})(), "text_answer": ""})
        part1 = answers[0] if len(answers) > 0 else fake_answer
        part2 = answers[1] if len(answers) > 1 else fake_answer
        part3 = answers[2] if len(answers) > 2 else fake_answer

        chatgpt = ChatGPTSpeakingIntegration()
        analysis = await chatgpt.generate_ielts_speaking_analyse(part1, part2, part3, lang_code=lang_code)

        # For missing parts, set 0 and feedback
        if not getattr(part1, "text_answer", None):
            analysis["part1_score"] = 0
            analysis["part1_feedback"] = t.get("no_answer_feedback", "No answer")
        if not getattr(part2, "text_answer", None):
            analysis["part2_score"] = 0
            analysis["part2_feedback"] = t.get("no_answer_feedback", "No answer")
        if not getattr(part3, "text_answer", None):
            analysis["part3_score"] = 0
            analysis["part3_feedback"] = t.get("no_answer_feedback", "No answer")

        criteria_scores = [
            float(v) for k, v in analysis.items()
            if k.endswith("_score")
            and not k.startswith("part")
            and k != "overall_band_score"
            and isinstance(v, (int, float))
        ]

        if not criteria_scores:
            overall = 1
        else:
            overall = round((sum(criteria_scores) / len(criteria_scores)) * 2) / 2

        analysis["overall_band_score"] = overall

        duration = (test.end_time - test.start_time) if (test.start_time and test.end_time) else timedelta(0)
        analysis["timing"] = duration.total_seconds()

        # Save analysis to DB if not exists
        speaking_analyse = await SpeakingAnalyse.create(
            speaking_id=test.id,
            feedback=analysis.get("feedback"),
            overall_band_score=analysis.get("overall_band_score"),
            fluency_and_coherence_score=analysis.get("fluency_and_coherence_score"),
            fluency_and_coherence_feedback=analysis.get("fluency_and_coherence_feedback"),
            lexical_resource_score=analysis.get("lexical_resource_score"),
            lexical_resource_feedback=analysis.get("lexical_resource_feedback"),
            grammatical_range_and_accuracy_score=analysis.get("grammatical_range_and_accuracy_score"),
            grammatical_range_and_accuracy_feedback=analysis.get("grammatical_range_and_accuracy_feedback"),
            pronunciation_score=analysis.get("pronunciation_score"),
            pronunciation_feedback=analysis.get("pronunciation_feedback"),
            duration=duration,
        )

        return analyse_to_dict(speaking_analyse)