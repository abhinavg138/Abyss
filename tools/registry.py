from dataclasses import dataclass
from typing import Callable, Dict, Any


@dataclass
class ToolSpec:
    name: str
    description: str
    handler: Callable[..., Any]


class ToolRegistry:
    """Single registry for every executable Abyss tool."""

    def __init__(self, calculator, filesystem, terminal, browser):
        self.tools: Dict[str, ToolSpec] = {
            "calculator": ToolSpec("calculator", "Evaluate safe arithmetic", calculator.execute),
            "read_file": ToolSpec("read_file", "Read a local text file", filesystem.read),
            "write_file": ToolSpec("write_file", "Write a local text file", filesystem.write),
            "list_files": ToolSpec("list_files", "List a directory", filesystem.list_directory),
            "tree": ToolSpec("tree", "Show project tree", filesystem.tree),
            "find_files": ToolSpec("find_files", "Find files by wildcard", filesystem.find),
            "grep": ToolSpec("grep", "Search text inside project files", filesystem.grep),
            "project": ToolSpec("project", "Read Python project source", filesystem.read_project),
            "terminal": ToolSpec("terminal", "Run a local shell command", terminal.execute),
            "browser": ToolSpec("browser", "Fetch a public HTTP/HTTPS URL", browser.execute),
        }

    def get(self, name):
        return self.tools.get(name)

    def execute(self, name, *args, **kwargs):
        tool = self.get(name)
        if not tool:
            return f"Unknown tool: {name}"
        try:
            return tool.handler(*args, **kwargs)
        except Exception as e:
            return f"Tool '{name}' failed: {e}"

    def describe(self):
        return "\n".join(f"{tool.name}: {tool.description}" for tool in self.tools.values())
