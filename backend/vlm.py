import json
import httpx

import config

EXTRACT_SYSTEM_PROMPT = """You are an expert exam paper reader. You will be shown an image of a student's exam paper.

Extract ALL visible questions and the student's answers. If the student left a question blank, note that.

You MUST respond with valid JSON in this exact format:
{
  "questions": [
    {
      "question_number": 1,
      "question_text": "The question as written on the paper",
      "student_answer": "What the student wrote as their answer",
      "max_score": 10
    }
  ]
}

If you can see the student's name, include "student_name" at the top level.
If a max score is visible per question, use it. Otherwise estimate based on question complexity (default 10).
Read carefully — handwriting may be messy. If a word is unclear, give your best guess with [?] marker."""

GRADE_SYSTEM_PROMPT = """You are a strict but fair university exam grader for a Deep Learning course.

You will receive:
1. A question from the exam
2. The student's answer
3. Relevant course content from lecture materials

Grade the student's answer based ONLY on the course content provided. Assess:
- Correctness of concepts
- Completeness of the answer
- Use of proper terminology from the course

You MUST respond with valid JSON:
{
  "score": 7,
  "max_score": 10,
  "feedback": "Clear explanation of what was correct and what was missing or wrong",
  "key_concepts_expected": ["concept1", "concept2"],
  "concepts_demonstrated": ["concept1"]
}

Be specific in feedback. Reference the course content when explaining what was missing."""


async def _call_openrouter(messages: list[dict], max_tokens: int = 2000) -> dict:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{config.OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": config.VLM_MODEL,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.1,
            },
        )
        if response.status_code != 200:
            error_body = response.text[:500]
            raise RuntimeError(f"OpenRouter {response.status_code}: {error_body}")
        data = response.json()
        content = data["choices"][0]["message"]["content"]

        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        return json.loads(content.strip())


async def extract_answers(base64_image: str) -> dict:
    if base64_image.startswith("data:"):
        image_url = base64_image
    else:
        image_url = f"data:image/jpeg;base64,{base64_image}"

    messages = [
        {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Read this exam paper and extract all questions and student answers."},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        },
    ]
    return await _call_openrouter(messages, max_tokens=4000)


async def grade_answer(
    question_text: str,
    student_answer: str,
    course_context: str,
    image_b64: str | None = None,
) -> dict:
    user_content = f"""## Question
{question_text}

## Student's Answer
{student_answer}

## Relevant Course Content
{course_context}"""

    user_parts: list[dict] = [{"type": "text", "text": user_content}]

    if image_b64:
        image_url = image_b64 if image_b64.startswith("data:") else f"data:image/jpeg;base64,{image_b64}"
        user_parts.append({"type": "image_url", "image_url": {"url": image_url}})

    messages = [
        {"role": "system", "content": GRADE_SYSTEM_PROMPT},
        {"role": "user", "content": user_parts},
    ]
    return await _call_openrouter(messages, max_tokens=1500)
