import json
from pathlib import Path
from typing import Any


class AgentEngine:
    """Bounded native tool-calling agent for Abyss."""

    MAX_STEPS = 8

    def __init__(self, router, filesystem, terminal, calculator, browser):
        self.router = router
        self.filesystem = filesystem
        self.terminal = terminal
        self.calculator = calculator
        self.browser = browser

    @property
    def nvidia(self):
        return self.router.providers.get("nvidia")

    def available(self) -> bool:
        return self.nvidia is not None and hasattr(self.nvidia, "client")

    def _tools(self) -> list[dict]:
        return [
            {"type": "function", "function": {"name": "read_file", "description": "Read a text file from the current Abyss workspace.", "parameters": {"type": "object", "properties": {"filename": {"type": "string"}}, "required": ["filename"]}}},
            {"type": "function", "function": {"name": "find_files", "description": "Find files by wildcard pattern, optionally under a path.", "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}}, "required": ["pattern"]}}},
            {"type": "function", "function": {"name": "grep", "description": "Search file contents for a text query.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "path": {"type": "string"}}, "required": ["query"]}}},
            {"type": "function", "function": {"name": "tree", "description": "Show the project directory tree.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": []}}},
            {"type": "function", "function": {"name": "calculate", "description": "Calculate a safe arithmetic expression.", "parameters": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}}},
            {"type": "function", "function": {"name": "run_command", "description": "Run a local terminal command in the Abyss workspace. Use only when the task requires execution or testing.", "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
            {"type": "function", "function": {"name": "write_file", "description": "Create or replace a text file. Only use when the user explicitly asks to create, edit, fix, or modify files.", "parameters": {"type": "object", "properties": {"filename": {"type": "string"}, "content": {"type": "string"}}, "required": ["filename", "content"]}}},
            {"type": "function", "function": {"name": "open_url", "description": "Fetch a public HTTP or HTTPS URL.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
        ]

    def _execute(self, name: str, arguments: dict[str, Any]) -> str:
        try:
            if name == "read_file":
                return self.filesystem.read(arguments["filename"])
            if name == "find_files":
                return self.filesystem.find(arguments["pattern"], arguments.get("path", "."))
            if name == "grep":
                return self.filesystem.grep(arguments["query"], arguments.get("path", "."))
            if name == "tree":
                return self.filesystem.tree(arguments.get("path", "."))
            if name == "calculate":
                return str(self.calculator.execute(arguments["expression"]))
            if name == "run_command":
                return self._safe_run(arguments["command"])
            if name == "write_file":
                filename = arguments["filename"]
                if Path(filename).is_absolute():
                    return "Denied: agent may only modify relative workspace paths."
                return self.filesystem.write(filename, arguments["content"])
            if name == "open_url":
                return self.browser.execute(arguments["url"])
            return f"Unknown tool: {name}"
        except Exception as exc:
            return f"Tool error: {exc}"

    def _safe_run(self, command: str) -> str:
        command = str(command).strip()
        lowered = command.lower()
        blocked = ("format ", "format /", "del /s", "rmdir /s", "rm -rf", "shutdown", "restart-computer", "remove-item", "diskpart", "reg delete")
        if any(token in lowered for token in blocked):
            return "Denied: potentially destructive command."
        return self.terminal.execute(command, timeout=120)

    def run(self, task: str) -> str:
        if not self.available():
            return "❌ Agent mode requires the NVIDIA provider (GLM-5.2) to be configured."

        messages = [
            {"role": "system", "content": "You are Abyss Agent, an autonomous software and computer-use agent. Work methodically. Inspect before modifying. Use tools for evidence instead of guessing. For coding tasks, inspect relevant files, make the smallest correct changes, run an appropriate test when possible, and report exactly what changed. Never claim a tool action succeeded unless its result confirms it. Stay inside the current workspace."},
            {"role": "user", "content": task},
        ]
        client = self.nvidia.client
        from config import Config

        for _step in range(1, self.MAX_STEPS + 1):
            response = client.chat.completions.create(model=Config.NVIDIA_MODEL, messages=messages, tools=self._tools(), tool_choice="auto")
            message = response.choices[0].message
            tool_calls = getattr(message, "tool_calls", None) or []

            if not tool_calls:
                return message.content or "Agent completed without a final response."

            assistant_message = {"role": "assistant", "content": message.content or "", "tool_calls": []}
            for call in tool_calls:
                assistant_message["tool_calls"].append({"id": call.id, "type": "function", "function": {"name": call.function.name, "arguments": call.function.arguments}})
            messages.append(assistant_message)

            for call in tool_calls:
                try:
                    arguments = json.loads(call.function.arguments or "{}")
                except json.JSONDecodeError:
                    arguments = {}
                result = self._execute(call.function.name, arguments)
                messages.append({"role": "tool", "tool_call_id": call.id, "content": result[:30000]})

        return "❌ Agent stopped after reaching its maximum of 8 tool steps."
