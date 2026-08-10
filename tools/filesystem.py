from tools.base import BaseTool
from pathlib import Path
import fnmatch
import os


class FilesystemTool(BaseTool):
    """Local project filesystem operations used by Abyss tools."""

    def execute(self, filename):
        return self.read(filename)

    def read(self, filename):
        path = Path(filename)
        if not path.exists():
            return "File not found."
        if not path.is_file():
            return "Path is not a file."
        return path.read_text(encoding="utf-8", errors="ignore")

    def write(self, filename, content):
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return "File updated."

    def list_directory(self, path="."):
        target = Path(path)
        if not target.exists():
            return "Directory not found."
        if not target.is_dir():
            return "Path is not a directory."
        items = sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        return "\n".join(("[DIR] " if item.is_dir() else "      ") + item.name for item in items)

    def find(self, pattern, path="."):
        root = Path(path)
        if not root.exists():
            return "Directory not found."
        matches = []
        for item in root.rglob("*"):
            if item.is_file() and fnmatch.fnmatch(item.name.lower(), pattern.lower()):
                matches.append(str(item))
                if len(matches) >= 200:
                    break
        return "\n".join(matches) if matches else "No matching files found."

    def grep(self, query, path="."):
        root = Path(path)
        if not root.exists():
            return "Path not found."
        results = []
        for item in root.rglob("*"):
            if not item.is_file() or item.stat().st_size > 2_000_000:
                continue
            try:
                for line_no, line in enumerate(item.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                    if query.lower() in line.lower():
                        results.append(f"{item}:{line_no}: {line.strip()[:300]}")
                        if len(results) >= 200:
                            return "\n".join(results)
            except OSError:
                continue
        return "\n".join(results) if results else "No matches found."

    def tree(self, path=".", prefix="", depth=3):
        root = Path(path)
        if not root.exists():
            return "Path not found."
        if depth < 0:
            return ""
        output = []
        try:
            items = sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError as e:
            return f"Filesystem error: {e}"
        for index, item in enumerate(items):
            connector = "└── " if index == len(items) - 1 else "├── "
            output.append(prefix + connector + item.name)
            if item.is_dir() and depth > 0:
                extension = "    " if index == len(items) - 1 else "│   "
                child = self.tree(item, prefix + extension, depth - 1)
                if child:
                    output.append(child)
        return "\n".join(output)

    def read_project(self, path="."):
        project = []
        root = Path(path)
        for file in root.rglob("*.py"):
            if any(part in {".venv", "__pycache__", ".git"} for part in file.parts):
                continue
            try:
                project.append(f"\n\n===== {file} =====\n{file.read_text(encoding='utf-8', errors='ignore')}")
            except OSError:
                pass
        return "".join(project)
