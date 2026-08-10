import json
import re


class MemoryExtractor:
    """Extract structured, updateable long-term memories from user messages."""

    MEMORY_CUES = re.compile(
        r"\b(remember|don't forget|do not forget|my name is|i am|i'm|i like|i love|"
        r"i prefer|i use|i'm using|my preferred|my goal|i want to|i'm working on|"
        r"i am working on|i study|i'm studying|i play|i live|i hate)\b",
        re.IGNORECASE,
    )

    @classmethod
    def should_extract(cls, user_message: str) -> bool:
        """Avoid an extra LLM call for obviously transient messages."""
        return bool(user_message and cls.MEMORY_CUES.search(user_message))

    @staticmethod
    def extract(router, user_message):
        system_prompt = {
            "role": "system",
            "content": """
You are Abyss's long-term memory extractor.

Determine whether the USER MESSAGE contains stable information worth remembering.
Only remember facts that are likely to remain useful across future conversations.

Good memories:
- name, location, education
- preferences and dislikes
- hobbies and recurring interests
- goals
- ongoing projects
- skills, tools and technologies the user regularly uses

Do NOT remember:
- greetings, questions, temporary requests
- one-off purchases or short-lived plans
- information about someone else unless it is a stable part of the user's context

If the user explicitly says "remember" or "don't forget", strongly prefer remember=true.

Return ONLY valid JSON with exactly these fields:
{
  "remember": true,
  "category": "Personal|Preferences|Projects|Goals|Skills|Other",
  "key": "stable_snake_case_key",
  "value": "short normalized value",
  "memory": "natural one-sentence fact about the user",
  "confidence": 0.0
}

Use a stable key for facts that should be updated later. Examples:
- preferred_ide
- favorite_sport
- current_project
- education_program
- location

If there is nothing worth remembering:
{
  "remember": false,
  "category": "Other",
  "key": "",
  "value": "",
  "memory": "",
  "confidence": 0.0
}
"""
        }

        messages = [
            system_prompt,
            {"role": "user", "content": user_message},
        ]

        response = router.chat(messages)

        try:
            result = json.loads(response)
            return {
                "remember": bool(result.get("remember")),
                "category": result.get("category", "Other"),
                "key": str(result.get("key", "")).strip() or None,
                "value": str(result.get("value", "")).strip() or None,
                "memory": str(result.get("memory", "")).strip(),
                "confidence": float(result.get("confidence", 1.0)),
            }
        except Exception:
            return {
                "remember": False,
                "category": "Other",
                "key": None,
                "value": None,
                "memory": "",
                "confidence": 0.0,
            }
