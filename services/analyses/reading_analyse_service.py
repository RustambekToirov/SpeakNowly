from fastapi import HTTPException, status
from datetime import timedelta
import asyncio
from models.tests.constants import Constants
from services.chatgpt import ChatGPTReadingIntegration
from models.analyses import ReadingAnalyse
from models.tests import Reading, ReadingAnswer

class ReadingAnalyseService:
    @staticmethod
    async def analyse(reading_id: int, user_id: int) -> list[ReadingAnalyse]:
        reading = await Reading.get_or_none(id=reading_id).prefetch_related("passages")
        if not reading:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Reading session not found")
        
        if reading.status != Constants.ReadingStatus.COMPLETED.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Reading session not completed")

        # Get all user answers for this session
        all_answers = await ReadingAnswer.filter(
            reading_id=reading_id, user_id=user_id
        ).select_related("question")
        
        # Group answers by passage_id
        answers_by_passage = {}
        for a in all_answers:
            if a.status == ReadingAnswer.ANSWERED:
                answers_by_passage.setdefault(a.question.passage_id, []).append(a)

        chatgpt = ChatGPTReadingIntegration()

        def normalize(text):
            return (text or "").strip().lower()
        
        # Get ALL passages from session - not just those with answers
        passages = await reading.passages.all().prefetch_related("questions")
        text_map = {p.id: p.text for p in passages}
        
        async def analyse_passage(passage_id: int, passage_text: str):
            # Check if already analyzed
            if await ReadingAnalyse.get_or_none(passage_id=passage_id, user_id=user_id):
                return None

            # Get answers if any
            submitted = answers_by_passage.get(passage_id, [])
            
            # If no submit for this passage, mark all questions as incorrect
            if not submitted:                
                # Get all questions for this passage
                passage = next((p for p in passages if p.id == passage_id), None)
                if not passage:
                    return None
                    
                questions = await passage.questions.all()
                
                # Create/update answers as "not answered and incorrect"
                for q in questions:
                    ans = next((a for a in all_answers if a.question_id == q.id), None)
                    if ans:
                        await ReadingAnswer.filter(id=ans.id).update(
                            is_correct=False, 
                            status=ReadingAnswer.NOT_ANSWERED,
                            correct_answer="", 
                            explanation="Not answered"
                        )
                    else:
                        # If no answer record exists - create a new one
                        await ReadingAnswer.create(
                            reading_id=reading_id,
                            user_id=user_id,
                            question_id=q.id,
                            status=ReadingAnswer.NOT_ANSWERED,
                            is_correct=False,
                            correct_answer="",
                            explanation="Not answered"
                        )
                
                # Create analysis record with score 0
                await ReadingAnalyse.create(
                    passage_id=passage_id,
                    user_id=user_id,
                    correct_answers=0,
                    overall_score=1,  # Minimum IELTS score
                    duration=(reading.end_time - reading.start_time) if (reading.start_time and reading.end_time) else timedelta(0)
                )
                
                # Form response structure for skipped passage
                questions_data = []
                for q in questions:
                    # Get options for MULTIPLE_CHOICE
                    if q.type == "MULTIPLE_CHOICE":
                        variants = await q.variants.all()
                        correct_var = next((v for v in variants if v.is_correct), None)
                        correct_answer = correct_var.text if correct_var else ""
                    else:
                        correct_answer = ""
                    
                    questions_data.append({
                        "question_id": q.id,
                        "user_answer": "",
                        "correct_answer": correct_answer,
                        "explanation": "Not answered",
                        "is_correct": False
                    })
                
                return [{
                    "passages": {
                        "passage_id": passage_id,
                        "analysis": questions_data
                    },
                    "stats": {
                        "total_correct": 0,
                        "total_questions": len(questions),
                        "accuracy": 0,
                        "overall_score": 1
                    }
                }]
            
            # Handling passages with answers
            # Sort answers
            non_empty = [ans for ans in submitted if (ans.text or "").strip()]
            empty_qs = [ans for ans in submitted if not (ans.text or "").strip()]
            
            # Mark empty answers as incorrect
            for ans in empty_qs:
                await ReadingAnswer.filter(
                    reading_id=reading_id, user_id=user_id,
                    question_id=ans.question.id
                ).update(is_correct=False, correct_answer="", explanation="No answer provided.")
            
            # Separate questions by type
            multiple_choice_answers = [a for a in non_empty if a.question.type == "MULTIPLE_CHOICE"]
            text_answers = [a for a in non_empty if a.question.type == "TEXT"]
            
            # 1. Check MULTIPLE_CHOICE on backend
            mc_analysis = []
            correct_mc = 0
            for ans in multiple_choice_answers:
                variants = await ans.question.variants.all()
                correct_var = next((v for v in variants if v.is_correct), None)
                correct_answer = correct_var.text if correct_var else ""
                is_corr = normalize(ans.text) == normalize(correct_answer)
                explanation = "" if is_corr else "Incorrect option."
                
                await ReadingAnswer.filter(
                    reading_id=reading_id, user_id=user_id,
                    question_id=ans.question.id
                ).update(
                    is_correct=is_corr,
                    correct_answer=correct_answer,
                    explanation=explanation
                )
                
                mc_analysis.append({
                    "question_id": ans.question.id,
                    "user_answer": ans.text,
                    "correct_answer": correct_answer,
                    "explanation": explanation,
                    "is_correct": is_corr
                })
                
                if is_corr:
                    correct_mc += 1
            
            # 2. Check TEXT questions via ChatGPT
            text_analysis = []
            correct_text = 0
            
            if text_answers:
                try:
                    # Prepare data for ChatGPT
                    questions_payload = [
                        {
                            "question_id": a.question.id,
                            "question": a.question.text,
                            "type": a.question.type,
                            "user_answer": a.text or ""
                        }
                        for a in text_answers
                    ]
                    
                    # Call ChatGPT for TEXT questions check
                    result = await chatgpt.check_passage_answers(
                        text=passage_text,
                        questions=questions_payload,
                        passage_id=passage_id
                    )
                    
                    # Process results from ChatGPT
                    text_analysis = result["analysis"]
                    
                    # Save scores to database
                    for item in text_analysis:
                        qid = item["question_id"]
                        is_corr = bool(item.get("is_correct", False))
                        
                        await ReadingAnswer.filter(
                            reading_id=reading_id, user_id=user_id,
                            question_id=qid
                        ).update(
                            is_correct=is_corr,
                            correct_answer=item.get("correct_answer", ""),
                            explanation=item.get("explanation", "")
                        )
                        
                        if is_corr:
                            correct_text += 1
                            
                except Exception as e:
                    # In case of ChatGPT error, mark all TEXT questions as incorrect
                    for ans in text_answers:
                        await ReadingAnswer.filter(
                            reading_id=reading_id, user_id=user_id,
                            question_id=ans.question.id
                        ).update(
                            is_correct=False,
                            correct_answer="",
                            explanation=f"Error processing answer: {str(e)}"
                        )
                        
                        text_analysis.append({
                            "question_id": ans.question.id,
                            "user_answer": ans.text,
                            "correct_answer": "",
                            "explanation": "Error processing answer",
                            "is_correct": False
                        })
            
            # 3. Combine results
            combined_analysis = mc_analysis + text_analysis
            
            # 4. Calculate overall statistics
            total_correct = correct_mc + correct_text
            total_questions = len(multiple_choice_answers) + len(text_answers) + len(empty_qs)
            accuracy = int((total_correct / total_questions) * 100) if total_questions else 0
            
            # 5. IELTS band calculation (official table, rounded to nearest 0.5)
            def calculate_ielts_band(correct):
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

            overall_score = calculate_ielts_band(total_correct)
            
            # 6. Save analysis result
            await ReadingAnalyse.create(
                passage_id=passage_id,
                user_id=user_id,
                correct_answers=total_correct,
                overall_score=overall_score,
                duration=(reading.end_time - reading.start_time) if (reading.start_time and reading.end_time) else timedelta(0)
            )
            
            # 7. Return data in the same format
            return [{
                "passages": {
                    "passage_id": passage_id,
                    "analysis": combined_analysis
                },
                "stats": {
                    "total_correct": total_correct,
                    "total_questions": total_questions,
                    "accuracy": accuracy,
                    "overall_score": overall_score
                }
            }]

        # Create tasks for all passages (even those without answers)
        tasks = [analyse_passage(p.id, text_map[p.id]) for p in passages]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r]

    @staticmethod
    async def get_passage_analysis(passage_id: int, user_id: int):
        return await ReadingAnalyse.get_or_none(passage_id=passage_id, user_id=user_id)

    @staticmethod
    async def get_all_analyses(reading_id: int, user_id: int):
        reading = await Reading.get_or_none(id=reading_id).prefetch_related("passages")
        if not reading:
            return []
        pids = [p.id for p in await reading.passages.all()]
        return await ReadingAnalyse.filter(passage_id__in=pids, user_id=user_id)
