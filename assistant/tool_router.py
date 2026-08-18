import re


class ToolRouter:
    """Turn natural-language requests into deterministic commands."""

    def __init__(self, router):
        self.router = router

    def route(self, user_message):
        msg = user_message.lower().strip()

        if msg.startswith("/"):
            return user_message.strip()

        forge_markers = (
            "create a tool", "make a tool", "build a tool", "forge a tool",
            "create a skill", "make a skill", "build a skill", "teach yourself",
            "add a capability", "learn how to", "you don't have a tool",
        )
        if any(marker in msg for marker in forge_markers):
            return "/forge " + user_message

        if re.fullmatch(r"[0-9+\-*/().%\s]+", msg):
            return "/calc " + msg
        if msg.startswith("what is"):
            expr = msg.replace("what is", "", 1).strip()
            if re.fullmatch(r"[0-9+\-*/().%\s]+", expr):
                return "/calc " + expr

        if msg.startswith(("read ", "open ")):
            filename = user_message.split(maxsplit=1)[1]
            return "/read " + filename
        if msg.startswith(("run ", "execute ")):
            return "/run " + user_message.split(maxsplit=1)[1]
        if msg.startswith("edit "):
            return "/edit " + user_message[5:].strip()
        if msg.startswith(("write ", "create file ")):
            return "/write " + user_message.split(maxsplit=1)[1]
        if msg.startswith(("find files ", "find file ", "search files ")):
            return "/find " + user_message.split(maxsplit=2)[-1]
        if msg.startswith(("grep ", "search for ")):
            return "/grep " + user_message.split(maxsplit=1)[1]
        if "project structure" in msg or "folder structure" in msg:
            return "/tree"
        if "list files" in msg or "show project" in msg:
            return "/project"

        if msg.startswith(("run command ", "execute command ", "shell ", "terminal ")):
            return "/shell " + user_message.split(maxsplit=2)[-1]

        url_match = re.search(r"https?://\S+", user_message)
        if url_match and any(word in msg for word in ("open", "read", "fetch", "visit", "look at")):
            return "/web " + url_match.group(0).rstrip(".,)")

        # Ordinary chat should go straight to the model. Only spend a second
        # model request on intent classification when the user strongly signals
        # that they want Abyss to inspect or operate on something.
        tool_signals = (
            "inspect", "look through", "look at my", "check my file",
            "check the file", "search my", "search the project", "find in",
            "find all", "grep", "read my", "open my", "open the file",
            "run the command", "use the terminal", "execute the command",
            "run this", "edit my", "modify my file", "change the file",
            "write to", "create a file", "project files", "project folder",
            "show me the files", "what files", "browse", "visit the site",
        )
        if not any(signal in msg for signal in tool_signals):
            return "NONE"

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
/forge CAPABILITY

Use /forge only when the user clearly asks Abyss to create/learn a new reusable capability.
Use tools only when the user clearly wants Abyss to perform an action.
Do not use tools for normal explanations, coding requests, brainstorming, or questions answerable from model knowledge.
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
"create a tool that converts Roman numerals" -> /forge create a tool that converts Roman numerals

User:
{user_message}
"""

        try:
            response = self.router.chat([{"role": "user", "content": prompt}]).strip()
            allowed = (
                "/calc ", "/read ", "/run ", "/project", "/tree", "/find ",
                "/grep ", "/write ", "/shell ", "/web ", "/ask ", "/edit ",
                "/tools", "/forge ",
            )
            if response.startswith(allowed):
                return response
        except Exception:
            pass

        return "NONE"
