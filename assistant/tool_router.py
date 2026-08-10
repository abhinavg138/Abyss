import re


class ToolRouter:

    def __init__(self, router):

        self.router = router

    def route(self, user_message):

        msg = user_message.lower().strip()

        # Calculator
        if re.fullmatch(r"[0-9\+\-\*\/\(\)\.\s]+", msg):
            return "/calc " + msg

        if msg.startswith("what is"):
            expr = msg.replace("what is", "").strip()

            if re.fullmatch(r"[0-9\+\-\*\/\(\)\.\s]+", expr):
                return "/calc " + expr

        # Read file
        if msg.startswith("read "):
            return "/read " + user_message[5:].strip()

        # Run file
        if msg.startswith("run "):
            return "/run " + user_message[4:].strip()

        # Tree
        if "project structure" in msg or "folder structure" in msg:
            return "/tree"

        # Project
        if "list files" in msg or "show project" in msg:
            return "/project"
        
        # Open file
        if msg.startswith("open "):
            return "/read " + user_message[5:].strip()

        # Execute file
        if msg.startswith("execute "):
            return "/run " + user_message[8:].strip()

        # Edit file
        if msg.startswith("edit "):
            return "/edit " + user_message[5:].strip()

        prompt = f"""
You are an intent classifier.

Your ONLY job is deciding whether the user's message should become one of these commands.

Available commands:

/calc EXPRESSION
/read FILE
/run FILE
/project
/tree
/ask FILE QUESTION
/edit FILE INSTRUCTION

Only use commands when the user is clearly asking to USE a tool.

Examples:

"What is 5+8?" -> /calc 5+8
"Calculate 55*32" -> /calc 55*32
"Read config.py" -> /read config.py
"Open main.py" -> /read main.py
"Run app.py" -> /run app.py
"Execute test.py" -> /run test.py
"Show project structure" -> /tree
"Show folder structure" -> /tree
"List project files" -> /project
"Edit router.py to add logging" -> /edit router.py add logging

DO NOT convert these:

"Write a Python quicksort function"
"Write HTML"
"Write Java"
"Explain recursion"
"What is recursion?"
"How do I use FastAPI?"
"Create a login page"
"Generate code"
"Help me debug this"

For every request above return:

NONE

Rules:

- Return ONLY ONE command.
- Return ONLY NONE if a command is not absolutely necessary.
- Never guess.
- Never invent filenames.

User:
{user_message}
"""

        response = self.router.chat(
            [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.strip()