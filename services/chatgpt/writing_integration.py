from fastapi import HTTPException
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
import re
import random

from .base_integration import BaseChatGPTIntegration

ANALYSE_PROMPT = """
You are an official IELTS examiner. Your task is to evaluate IELTS Writing Task 1 and Task 2 responses provided by a candidate.

IMPORTANT STRICTNESS INSTRUCTIONS:
- Be extremely strict and objective, as a real IELTS examiner.
- Do NOT award band 8.0 or higher unless the writing is truly exceptional, nearly native-like, with almost no errors, highly sophisticated vocabulary, and complex structures.
- If there are any noticeable errors, repetition, lack of complexity, or awkward phrasing, do NOT give more than 7.0.
- Use the official IELTS band descriptors for each criterion.
- Most responses should receive scores between 5.0 and 7.0. Only outstanding, rare responses should get higher.

Task 1 Evaluation Criteria:
- Task Achievement: Does the response address the key points from the provided diagram accurately and completely?
- Coherence and Cohesion: Are ideas logically organized and connected effectively with appropriate linking words?
- Lexical Resource: Is a wide range of vocabulary used accurately and appropriately?
- Grammatical Range and Accuracy: Are sentence structures varied and grammatical errors minimal?

Task 2 Evaluation Criteria:
- Task Response: Does the essay fully address the task, presenting a clear position with well-supported ideas?
- Coherence and Cohesion: Are the ideas logically sequenced and effectively linked?
- Lexical Resource: Is the vocabulary diverse and appropriate for an academic essay?
- Grammatical Range and Accuracy: Is the grammar accurate and varied?

Evaluation Criteria for Both Tasks:
1. Task Achievement/Response:
    - Does the response fully address the task requirements, providing relevant, well-supported ideas?
    - Are key points covered accurately and completely?
    - Assign a score (0-9) and provide specific feedback on strengths and areas for improvement.

2. Coherence and Cohesion:
    - Are ideas logically organized and effectively linked using appropriate cohesive devices?
    - Is there a clear progression of ideas throughout the response?
    - Assign a score (0-9) with feedback on logical sequencing and cohesion.

3. Lexical Resource:
    - Is a wide range of vocabulary used accurately and appropriately?
    - Does the response demonstrate lexical variety and precision?
    - Provide feedback on vocabulary diversity and appropriacy, with a score (0-9).

4. Grammatical Range and Accuracy:
    - Are sentence structures varied and grammatical errors minimal?
    - Is punctuation used correctly and effectively?
    - Assign a score (0-9) with feedback on grammar accuracy and sentence complexity.

5. Word Count:
    - Does the response meet the required word count for the task (150 words for Task 1, 250 words for Task 2)?
    - Provide feedback on whether the response is underlength or overlength and suggest improvements for better word count management.
    - Assign a score (0-9) based on adherence to the word count requirements.

6. Timing Feedback:
    - Provide insights on whether the response was completed within the given time constraints.
    - Suggest improvements for better time management.

Instructions for Evaluation:
1. Assess the provided responses based on the above criteria.
2. Provide structured, constructive feedback tailored to IELTS band descriptors.
3. Assign individual band scores (0-9) for each criterion and an overall band score.
4. Ensure feedback is specific, actionable, and designed to help the candidate improve.
5. Be especially strict when awarding scores above 7.0—such scores are only for truly outstanding work.
6. If only one task is answered, the overall band score must not exceed 6.0, regardless of the quality of the answer.
"""

PART1_PROMPT = """
Create a line or bar or pie chart based on an IELTS Writing Task 1 question comparing five categories in two different years on a given topic.
The data for the chart is in JSON format with the keys question, chart_type, categories, years, and:
Return ONLY a valid JSON object with the following structure, no explanations, markdown, or code. Do not include any text outside the JSON.

{
  "question": "...",
  "chart_type": "bar" | "line" | "pie",
  "categories": [...],
  "year1": ...,
  "year2": ...,
  "data_year1": [...],
  "data_year2": [...]
}
"""

PART2_PROMPT = """
Create an IELTS Writing Task 2 question. The question should be based on common essay topics such as education,
technology, the environment, healthcare and many other social issues. Make a clear, thought-provoking statement that
requires the test taker to discuss both sides of an argument and express their opinion.
"""

class ChatGPTWritingIntegration(BaseChatGPTIntegration):
    """
    Async integration with OpenAI for IELTS Writing generation and analysis.
    """

    async def generate_writing_part1_question(self, user_id=None) -> dict:
        """
        Generate IELTS Writing Task 1 question and chart data using OpenAI.
        """
        seed = random.randint(1, 1_000_000)
        now = datetime.now().isoformat()
        prompt = (
            PART1_PROMPT
            + f"\n\n# Seed: {seed}\n"
            + f"# User ID: {user_id}\n"
            + f"# Date: {now}\n"
            + "Please use the above seed, user ID, and date to make the chart and question unique."
            + "Please make sure the topic and chart data are different from previous generations, and use the seed, user ID, and date for uniqueness."
        )
        response = await self.async_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7,
        )
        raw = response.choices[0].message.content
        if not raw or not raw.strip():
            raise HTTPException(status_code=500, detail="OpenAI вернул пустой ответ для Task 1 question.")
        # Ищем JSON в ответе
        match = re.search(r'\{[\s\S]*\}', raw)
        if not match:
            raise HTTPException(status_code=500, detail=f"Failed to find JSON in GPT response: {raw}")
        json_str = match.group(0)
        try:
            return json.loads(json_str)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse Task 1 question: {e}\nRAW: {json_str}")

    async def generate_writing_part2_question(self, user_id=None) -> dict:
        """
        Generate IELTS Writing Task 2 question using OpenAI.
        """
        seed = random.randint(1, 1_000_000)
        now = datetime.now().isoformat()
        prompt = (
            PART2_PROMPT
            + f"\n\n# Seed: {seed}\n"
            + f"# User ID: {user_id}\n"
            + f"# Date: {now}\n"
            + "Please use the above seed, user ID, and date to make the question unique."
        )
        response = await self.async_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7,
        )
        raw = response.choices[0].message.content
        if not raw or not raw.strip():
            raise HTTPException(status_code=500, detail="OpenAI вернул пустой ответ для Task 2 question.")
        # Ищем JSON в ответе
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            json_str = match.group(0)
            try:
                return json.loads(json_str)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to parse Task 2 question: {e}\nRAW: {json_str}")
        return {"question": raw.strip()}

    def create_bar_chart(self, categories, year1, year2, data_year1, data_year2) -> str:
        output_dir = "media/writing/diagrams"
        os.makedirs(output_dir, exist_ok=True)
        fig, ax = plt.subplots(figsize=(8, 6))
        bar_width = 0.35
        x = range(len(categories))
        ax.bar(x, data_year1, width=bar_width, label=str(year1), alpha=0.7)
        ax.bar([i + bar_width for i in x], data_year2, width=bar_width, label=str(year2), alpha=0.7)
        ax.set_xlabel("Categories", fontsize=12)
        ax.set_ylabel("Percentage of Expenditure", fontsize=12)
        ax.set_title(f"Comparison of Household Expenditure by Category ({year1} vs {year2})", fontsize=14)
        ax.set_xticks([i + bar_width / 2 for i in x])
        ax.set_xticklabels(categories, fontsize=10)
        ax.legend()
        filename = os.path.join(output_dir, f"{datetime.now().isoformat()}.png")
        plt.savefig(filename)
        plt.close()
        return filename

    def create_line_chart(self, categories, year1, year2, data_year1, data_year2) -> str:
        output_dir = "media/writing/diagrams"
        os.makedirs(output_dir, exist_ok=True)
        plt.figure(figsize=(8, 6))
        plt.plot(categories, data_year1, marker="o", label=str(year1))
        plt.plot(categories, data_year2, marker="o", label=str(year2))
        plt.xlabel("Categories")
        plt.ylabel("Percentage of Expenditure")
        plt.title(f"Trend of Household Expenditure ({year1} vs {year2})")
        plt.legend()
        filename = os.path.join(output_dir, f"{datetime.now().isoformat()}.png")
        plt.savefig(filename)
        plt.close()
        return filename

    def create_pie_chart(self, categories, year1, year2, data_year1, data_year2) -> str:
        output_dir = "media/writing/diagrams"
        os.makedirs(output_dir, exist_ok=True)
        fig, axs = plt.subplots(1, 2, figsize=(12, 6))
        axs[0].pie(data_year1, labels=categories, autopct="%1.1f%%", startangle=140)
        axs[0].set_title(f"Distribution of Household Expenditure ({year1})")
        axs[1].pie(data_year2, labels=categories, autopct="%1.1f%%", startangle=140)
        axs[1].set_title(f"Distribution of Household Expenditure ({year2})")
        filename = os.path.join(output_dir, f"{datetime.now().isoformat()}.png")
        plt.savefig(filename)
        plt.close()
        return filename

    async def analyse_writing(self, part1, part2, lang_code: str = "en") -> dict:
        lang_map = {
            "uz": "Uzbek",
            "ru": "Russian",
            "en": "English",
        }
        language_name = lang_map.get(lang_code, "English")
        data = [
            {
                "part1": {
                    "question": part1.content,
                    "diagram_data": part1.diagram_data,
                    "user_answer": part1.answer,
                },
                "part2": {
                    "question": part2.content,
                    "user_answer": part2.answer,
                },
            }
        ]
        prompt_with_lang = f"""
{ANALYSE_PROMPT.strip()}

🗣 IMPORTANT: Please return ALL feedback, scores, and explanations in this language: {language_name.upper()}.
Only use {language_name} language. Do NOT include English explanations.
Return ONLY a valid JSON object. Do not include any explanations, markdown, or text outside the JSON. If you understand, reply only with the JSON object.
"""
        response = await self._generate_response(
            prompt=prompt_with_lang,
            user_content=json.dumps(data, ensure_ascii=False)
        )
        match = re.search(r'```(?:json)?\s*([\s\S]+?)\s*```', response)
        if match:
            json_str = match.group(1)
        else:
            json_str = response
        try:
            return json.loads(json_str)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse ChatGPT response: {e}\nRAW: {response}")

    async def _generate_response(self, prompt: str, user_content: str) -> str:
        response = await self.async_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.0,
        )
        return response.choices[0].message.content