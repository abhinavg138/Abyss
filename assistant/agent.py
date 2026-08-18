import json
import time
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

    def _agent_providers(self):
        """Return configured OpenAI-compatible providers that can run tools."""
        providers = []
        for name in ("nvidia", "groq", "openrouter"):
            provider = self.router.providers.get(name)
            if provider is None or not hasattr(provider, "client"):
                continue
            providers.append((name, provider))
        return providers

    def available(self) -> bool:
        return bool(self._agent_providers())

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

    def _model_for(self, name: str, provider) -> str:
        from config import Config
        if name == "nvidia":
            return Config.NVIDIA_MODEL
        if name == "groq":
            return Config.GROQ_MODEL
        if name == "openrouter":
            return Config.OPENROUTER_MODEL
        return ""

    def _complete(self, name: str, provider, messages: list[dict]):
        model = self._model_for(name, provider)
        return provider.client.chat.completions.create(
            model=model,
            messages=messages,
            tools=self._tools(),
            tool_choice="auto",
        )

    def run(self, task: str) -> str:
        providers = self._agent_providers()
        if not providers:
            return "❌ Agent mode requires a configured tool-capable provider (NVIDIA, Groq, or OpenRouter)."

        messages = [
            {"role": "system", "content": "You are Abyss Agent, an autonomous software and computer-use agent. Work methodically. Inspect before modifying. Use tools for evidence instead of guessing. For coding tasks, inspect relevant files, make the smallest correct changes, run an appropriate test when possible, and report exactly what changed. Never claim a tool action succeeded unless its result confirms it. Stay inside the current workspace."},
            {"role": "user", "content": task},
        ]

        active_name, active_provider = providers[0]

        for _step in range(1, self.MAX_STEPS + 1):
            try:
                response = self._complete(active_name, active_provider, messages)
            except Exception as exc:
                # NVIDIA/NIM can return 429 when its short-term quota is exhausted.
                # Give it one brief retry, then fall through to another configured
                # OpenAI-compatible provider instead of crashing the FastAPI stream.
                if "429" in str(exc) or exc.__class__.__name__ == "RateLimitError":
                    time.sleep(2)
                    try:
                        response = self._complete(active_name, active_provider, messages)
                    except Exception as retry_exc:
                        remaining = [(n, p) for n, p in providers if n != active_name]
                        if not remaining:
                            return f"❌ Agent provider {active_name} is rate-limited (429). Try again shortly."
                        active_name, active_provider = remaining[0]
                        try:
                            response = self._complete(active_name, active_provider, messages)
                        except Exception as fallback_exc:
                            return f"❌ Agent providers failed. {active_name}: {fallback_exc}"
                else:
                    return f"❌ Agent provider {active_name} failed: {exc}"

            self.router.current_provider = active_name
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

        return f"❌ Agent stopped after reaching its maximum of {self.MAX_STEPS} tool steps."
