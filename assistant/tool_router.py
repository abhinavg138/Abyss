import re


class ToolRouter:
    """Turn natural-language tool requests into deterministic commands."""

    def __init__(self, router):
        self.router = router

    def route(self, user_message):
        msg = user_message.lower().strip()

        # Explicit commands always pass through unchanged.
        if msg.startswith("/"):
            return user_message.strip()

        # Calculator
        if re.fullmatch(r"[0-9+\-*/().%\s]+", msg):
            return "/calc " + msg
        if msg.startswith("what is"):
            expr = msg.replace("what is", "", 1).strip()
            if re.fullmatch(r"[0-9+\-*/().%\s]+", expr):
                return "/calc " + expr

        # Filesystem / project tools
        if msg.startswith(("read ", "open ")):
            filename = user_message.split(maxsplit=1)[1]
            return "/read " + filename
        if msg.startswith(("run ", "execute ")):
            filename = user_message.split(maxsplit=1)[1]
            return "/run " + filename
        if msg.startswith("edit "):
            return "/edit " + user_message[5:].strip()
        if msg.startswith(("write ", "create file ")):
            payload = user_message.split(maxsplit=1)[1]
            return "/write " + payload
        if msg.startswith(("find files ", "find file ", "search files ")):
            payload = user_message.split(maxsplit=2)[-1]
            return "/find " + payload
        if msg.startswith(("grep ", "search for ")):
            payload = user_message.split(maxsplit=1)[1]
            return "/grep " + payload
        if "project structure" in msg or "folder structure" in msg:
            return "/tree"
        if "list files" in msg or "show project" in msg:
            return "/project"

        # Terminal
        if msg.startswith(("run command ", "execute command ", "shell ", "terminal ")):
            payload = user_message.split(maxsplit=2)[-1]
            return "/shell " + payload

        # Web fetch. This is deliberately URL-oriented rather than pretending
        # to be a full search engine.
        url_match = re.search(r"https?://\S+", user_message)
        if url_match and any(word in msg for word in ("open", "read", "fetch", "visit", "look at")):
            return "/web " + url_match.group(0).rstrip(".,)")

        # Let the model classify less obvious tool requests.
        prompt = f"""
You are Abyss's tool intent classifier.

Return ONE command only, or NONE.

Available commands:
/calc EXPRESSION
/read FILE
/run FILE
/project
/tree
/find PATTERN [PATH]
/grep QUERY [PATH]
/write FILE CONTENT
/shell COMMAND
/web URL
/ask FILE QUESTION
/edit FILE INSTRUCTION
/tools

Use a tool only when the user clearly wants Abyss to perform that action.
Do not use tools for normal explanations, coding requests, brainstorming, or questions that can be answered from model knowledge.
Never invent a filename, URL, command, or path.

Examples:
"calculate 55*32" -> /calc 55*32
"read config.py" -> /read config.py
"run test.py" -> /run test.py
"show project structure" -> /tree
"find all python files" -> /find *.py
"search files for DEFAULT_PROVIDER" -> /grep DEFAULT_PROVIDER
"open https://example.com" -> /web https://example.com
"run command git status" -> /shell git status

User:
{user_message}
"""

        try:
            response = self.router.chat([{"role": "user", "content": prompt}])
            response = response.strip()
            if response.startswith(("/calc ", "/read ", "/run ", "/project", "/tree", "/find ", "/grep ", "/write ", "/shell ", "/web ", "/ask ", "/edit ", "/tools")):
                return response
        except Exception:
            pass

        return "NONE"
