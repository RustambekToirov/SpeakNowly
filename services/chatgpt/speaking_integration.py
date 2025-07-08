from fastapi import HTTPException, status, UploadFile
import json
import re
from openai import AuthenticationError, BadRequestError, OpenAIError, RateLimitError
from .base_integration import BaseChatGPTIntegration
from io import BytesIO
import random
from datetime import datetime

QUESTIONS_PROMPT = """
Generate a set of IELTS Speaking test questions in 3 parts.

Part 1: Always start with questions about full name, address, and work/education. Then add 2 different topics, each with 2-3 personal questions (likes/dislikes, free time, favorite things, etc).
Part 2: Give a descriptive question and three follow-up points. The topic should not overlap with Part 1.
Part 3: Give argumentative questions related to Part 2. Total 3-6 questions.

All "question" fields must be arrays of strings.

IMPORTANT:
- You MUST use the provided seed, user_id, and date to generate questions that are unique for each combination.
- Do NOT repeat questions or topics from previous generations, even if only the seed changes.
- The questions must be different every time, even for the same user, if the seed or date changes.
- Use the seed to randomize topics, wording, and order.
- Never generate the same set of questions twice.
- If the seed changes even by 1, all questions must be new.

Return ONLY a valid JSON object. Do not include explanations, markdown, or text outside the JSON.

{
  "part1": {"title": "...", "question": ["...", "..."]},
  "part2": {"title": "...", "question": ["...", "..."]},
  "part3": {"title": "...", "question": ["...", "..."]}
}
"""

ANALYSE_PROMPT = """
You are an experienced IELTS examiner. Evaluate the following candidate's speaking responses based on the IELTS Speaking criteria:

Fluency and Coherence: Assess the flow of speech, logical structuring, and absence of unnatural pauses or repetition.
Lexical Resource: Evaluate the range and precision of vocabulary, including idiomatic language and collocations.
Grammatical Range and Accuracy: Consider the variety and correctness of grammatical structures and sentence complexity.
Pronunciation: Assess clarity, word stress, intonation, and overall intelligibility.

STRICTNESS INSTRUCTIONS:
- Be as strict and objective as a real IELTS examiner.
- Do NOT award a band of 5.0 or higher for short, hesitant, repetitive, or simplistic answers with frequent errors.
- Only award 5.0 or above if responses are well-developed, coherent, use complex structures accurately, and display a wide range of vocabulary.
- Responses with noticeable mistakes, limited development, or basic language should receive 4.0 or below.
- If an answer is missing or completely off-topic, assign 0.
- Avoid sympathy scoring; most scores will fall between 3.0 and 6.0.

IMPORTANT:
- There may be fewer than three answers (some parts missing or empty). For any missing part, assign 0 for all criteria and feedback “No answer”.
- The overall band score is the average of each criterion score (including zeros for missing parts), rounded to the nearest half-band.

Please provide:
- Individual band scores (1.0–9.0) for each criterion.
- Detailed feedback for each criterion.
- A final overall band score (1.0–9.0) based on the average of the four criteria (including zeros).

Return ONLY a valid JSON object in this format. Do not include any extra text:

{
  "fluency_and_coherence_score": ...,
  "fluency_and_coherence_feedback": "...",
  "lexical_resource_score": ...,
  "lexical_resource_feedback": "...",
  "grammatical_range_and_accuracy_score": ...,
  "grammatical_range_and_accuracy_feedback": "...",
  "pronunciation_score": ...,
  "pronunciation_feedback": "...",
  "overall_band_score": ...,
  "feedback": "...",
  "part1_score": ...,
  "part1_feedback": "...",
  "part2_score": ...,
  "part2_feedback": "...",
  "part3_score": ...,
  "part3_feedback": "..."
}
"""

class ChatGPTSpeakingIntegration(BaseChatGPTIntegration):
    """
    Asynchronous integration with OpenAI for generating and analyzing IELTS Speaking.
    """

    async def generate_ielts_speaking_questions(self, user_id=None) -> dict:
        """
        Generate IELTS Speaking questions using OpenAI.

        Args:
            user_id (int): Unique identifier for the user.

        Returns:
            dict: Generated questions in JSON format.
        """
        seed = random.randint(1, 1_000_000)
        now = datetime.now().isoformat()
        prompt = QUESTIONS_PROMPT
        user_content = json.dumps({
            "seed": seed,
            "user_id": user_id,
            "date": now
        })
        response = await self.async_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.9,
        )
        return json.loads(response.choices[0].message.content)

    async def generate_ielts_speaking_analyse(self, part1, part2, part3, lang_code: str = "en") -> dict:
        """
        Analyse a completed Speaking test using OpenAI.

        Args:
            part1, part2, part3: SpeakingAnswers objects with .question.title, .question.content, .text_answer

        Returns:
            dict: Analysis result in JSON format.
        """
        lang_map = {
            "uz": "Uzbek",
            "ru": "Russian",
            "en": "English",
        }
        language_name = lang_map.get(lang_code, "English")
        data = [
            {"title": part1.question.title, "question": part1.question.content, "user_answer": part1.text_answer},
            {"title": part2.question.title, "question": part2.question.content, "user_answer": part2.text_answer},
            {"title": part3.question.title, "question": part3.question.content, "user_answer": part3.text_answer},
        ]
        prompt_with_lang = f"""
{ANALYSE_PROMPT.strip()}

🗣 IMPORTANT: Please return ALL feedback, scores, and explanations in this language: {language_name.upper()}.
Only use {language_name} language. Do NOT include English explanations.
Return ONLY a valid JSON object. Do not include any explanations, markdown, or text outside the JSON. If you understand, reply only with the JSON object.
"""
        response = await self.async_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt_with_lang},
                {"role": "user", "content": json.dumps(data, ensure_ascii=False)},
            ],
            temperature=0.0,
            max_tokens=6000
        )
        raw = response.choices[0].message.content
        if not raw or not raw.strip():
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "OpenAI returned an empty response for analysis.")

        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not match:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                f"OpenAI returned invalid JSON:\n{raw}"
            )
        json_str = match.group(0)
        try:
            return json.loads(json_str)
        except Exception as e:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                f"Error parsing OpenAI response: {e}\nRAW: {json_str}"
            )

    async def transcribe_audio_file_async(self, audio: UploadFile, lang="en") -> str:
        """
        Asynchronously transcribe audio using OpenAI Whisper.
        """
        try:
            content = await audio.read()
            file_like = BytesIO(content)
            file_like.name = audio.filename

            transcript = await self.async_client.audio.transcriptions.create(
                file=file_like,
                model="whisper-1",
                response_format="text",
                language=lang
            )
            return transcript
        except AuthenticationError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication with OpenAI failed. Check your API key.")
        except BadRequestError as e:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
        except RateLimitError as e:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, f"Rate limit exceeded. {str(e)}")
        except OpenAIError as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"OpenAI API error: {str(e)}")