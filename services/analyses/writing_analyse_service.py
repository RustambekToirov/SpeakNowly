from fastapi import HTTPException, status
from datetime import timedelta
from services.chatgpt import ChatGPTWritingIntegration
from models.analyses import WritingAnalyse
from models.tests import Writing, WritingStatus

class WritingAnalyseService:
    @staticmethod
    async def analyse(test_id: int, lang_code: str, t: dict) -> WritingAnalyse:
        """
        Analyse a completed Writing test and save the result.
        """
        test = await Writing.get_or_none(id=test_id).prefetch_related("part1", "part2")
        if not test:
            raise HTTPException(status.HTTP_404_NOT_FOUND, t.get("writing_test_not_found", "Writing test not found"))
        
        if test.status != WritingStatus.COMPLETED:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, t.get("writing_test_not_completed", "Writing test is not completed"))
        
        existing = await WritingAnalyse.get_or_none(writing_id=test.id)
        if existing:
            return existing
        
        if not test.part1 or not test.part2:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, t.get("writing_parts_not_found", "Writing parts not found"))

        chatgpt = ChatGPTWritingIntegration()
        analysis = await chatgpt.analyse_writing(test.part1, test.part2, lang_code=lang_code)
        if not analysis:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, t.get("writing_analysis_failed", "Failed to analyse writing test"))

        if isinstance(analysis, list):
            analysis = analysis[0] if analysis else {}
        if not isinstance(analysis, dict):
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, t.get("writing_analysis_invalid_format", "Invalid analysis format"))

        duration = (test.end_time - test.start_time) if (test.start_time and test.end_time) else timedelta(0)

        def get_criteria(part, *keys, default=""):
            for key in keys:
                if key in part:
                    return part[key]
            return {}

        part1 = analysis.get("Task1") or analysis.get("part1") or {}
        part2 = analysis.get("Task2") or analysis.get("part2") or {}

        # Task 1 (part1)
        task_achievement = get_criteria(part1, "TaskAchievement", "Task Achievement")
        coherence = get_criteria(part1, "CoherenceAndCohesion", "Coherence and Cohesion")
        lexical = get_criteria(part1, "LexicalResource", "Lexical Resource")
        grammar = get_criteria(part1, "GrammaticalRangeAndAccuracy", "Grammatical Range and Accuracy")
        word_count = get_criteria(part1, "WordCount", "Word Count")
        timing = get_criteria(part1, "TimingFeedback", "Timing Feedback")

        # Task 2 (part2)
        task_response = get_criteria(part2, "TaskResponse", "Task Response")
        coherence2 = get_criteria(part2, "CoherenceAndCohesion", "Coherence and Cohesion")
        lexical2 = get_criteria(part2, "LexicalResource", "Lexical Resource")
        grammar2 = get_criteria(part2, "GrammaticalRangeAndAccuracy", "Grammatical Range and Accuracy")
        word_count2 = get_criteria(part2, "WordCount", "Word Count")
        timing2 = get_criteria(part2, "TimingFeedback", "Timing Feedback")

        # IELTS: average of 4 criteria for each task, then average of both tasks, rounded to nearest 0.5
        def get_score(crit):
            if isinstance(crit, dict):
                return crit.get("Score") or crit.get("score") or 0
            elif isinstance(crit, (int, float)):
                return crit
            return 0

        scores1 = [get_score(task_achievement), get_score(coherence), get_score(lexical), get_score(grammar)]
        scores2 = [get_score(task_response), get_score(coherence2), get_score(lexical2), get_score(grammar2)]

        avg1 = sum(scores1) / 4 if all(scores1) else 0
        avg2 = sum(scores2) / 4 if all(scores2) else 0

        overall_band_score = analysis.get("overall_band_score")
        if overall_band_score is None:
            # If both Tasks are present
            if avg1 and avg2:
                overall_band_score = round(((avg1 + avg2) / 2) * 2) / 2
            # If only one Task is present
            elif avg1:
                overall_band_score = round(avg1 * 2) / 2
            elif avg2:
                overall_band_score = round(avg2 * 2) / 2
            else:
                overall_band_score = 1
            if overall_band_score < 1:
                overall_band_score = 1

        part2_answer = test.part2.answer if test.part2 else None
        if not part2_answer or part2_answer.strip().lower() in ["", "string"]:
            overall_band_score = min(overall_band_score, 6.0)

        # Collect overall feedback (can be improved based on your prompt)
        total_feedback = ""
        if "overall_feedback" in analysis:
            total_feedback = analysis["overall_feedback"]
        elif "total_feedback" in analysis:
            total_feedback = analysis["total_feedback"]
        else:
            # Gather feedback from both parts
            def safe_feedback(crit):
                if isinstance(crit, dict):
                    return crit.get("Feedback") or crit.get("feedback") or ""
                return ""
            total_feedback = (
                safe_feedback(task_achievement) + "\n" +
                safe_feedback(task_response)
            ).strip()

        writing_analyse = await WritingAnalyse.create(
            writing=test,
            # Task 1
            task_achievement_score=task_achievement.get("Score", 0) or task_achievement.get("score", 0),
            task_achievement_feedback=task_achievement.get("Feedback", "") or task_achievement.get("feedback", ""),
            lexical_resource_score=lexical.get("Score", 0) or lexical.get("score", 0),
            lexical_resource_feedback=lexical.get("Feedback", "") or lexical.get("feedback", ""),
            coherence_and_cohesion_score=coherence.get("Score", 0) or coherence.get("score", 0),
            coherence_and_cohesion_feedback=coherence.get("Feedback", "") or coherence.get("feedback", ""),
            grammatical_range_and_accuracy_score=grammar.get("Score", 0) or grammar.get("score", 0),
            grammatical_range_and_accuracy_feedback=grammar.get("Feedback", "") or grammar.get("feedback", ""),
            word_count_score=word_count.get("Score", 0) or word_count.get("score", 0),
            word_count_feedback=word_count.get("Feedback", "") or word_count.get("feedback", ""),
            timing_feedback=timing.get("Feedback", "") or timing.get("feedback", ""),
            # General
            overall_band_score=overall_band_score,
            total_feedback=total_feedback,
            duration=duration,
        )
        return writing_analyse