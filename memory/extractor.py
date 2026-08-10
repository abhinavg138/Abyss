import json


class MemoryExtractor:

    @staticmethod
    def extract(router, user_message):

        system_prompt = {
            "role": "system",
            "content": """
You are a memory extraction AI.

Decide whether the USER MESSAGE contains long-term information worth remembering.

Remember:
- Name
- Age
- Location
- Preferences
- Hobbies
- Goals
- Ongoing projects
- Skills

Ignore:
- Greetings
- Questions
- Temporary requests
- Small talk

Return ONLY valid JSON.

Example:

{
    "remember": true,
    "memory": "User likes badminton."
}
"""
        }

        messages = [
            system_prompt,
            {
                "role": "user",
                "content": user_message
            }
        ]

        response = router.chat(messages)

        try:
            return json.loads(response)
        except Exception:
            return {
                "remember": False,
                "memory": ""
            }