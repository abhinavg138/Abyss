from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ForgeResult:
    name: str
    description: str
    status: str
    path: str | None = None
    tests: str = ""
    error: str = ""


class ForgeManager:
    """Controlled runtime skill creation and execution.

    Forge never edits Abyss core files. New skills are generated into
    extensions/.staging, tested, and require an explicit install command.
    """

    BLOCKED_IMPORTS = {
        "os", "subprocess", "socket", "shutil", "ctypes", "multiprocessing",
        "sys", "importlib", "requests", "httpx", "urllib", "ftplib",
    }
    NAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,31}$")

    def __init__(self, router, root: str | Path = "extensions"):
        self.router = router
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.staging = self.root / ".staging"
        self.staging.mkdir(parents=True, exist_ok=True)

    def forge(self, request: str) -> ForgeResult:
        request = request.strip()
        if not request:
            return ForgeResult("unknown", "", "failed", error="No capability request supplied.")

        prompt = f"""
You are Abyss Forge, a conservative Python skill generator.

Create ONE small reusable skill for this capability request:
{request}

Return ONLY valid JSON with exactly these fields:
name, description, code, tests

IMPORTANT JSON RULE:
The code and tests fields are JSON strings. Escape every newline as \\n,
escape every embedded double quote as \\" and escape backslashes as needed.
Do not put markdown fences around the JSON.

Rules:
- name must be lowercase snake_case, 3-32 chars.
- code must define a class named Skill with an execute(self, *args, **kwargs) method.
- tests must be a standalone unittest script that imports Skill from tool.py.
- Use Python standard-library functionality only.
- Do NOT import or use os, subprocess, socket, shutil, ctypes, multiprocessing,
  sys, importlib, requests, httpx, urllib, ftplib, eval, exec, or __import__.
- Do not read/write arbitrary files or access the network.
- Keep the skill focused on the requested capability.
- Do not modify Abyss core files.
- Make the tests deterministic and runnable with `python tests.py`.
"""
        try:
            raw = self.router.chat([{"role": "user", "content": prompt}]).strip()
            payload = self._parse_json(raw)
            self._validate_payload(payload)
            return self._stage_and_test(payload)
        except Exception as exc:
            return ForgeResult("unknown", "", "failed", error=str(exc))

    def install(self, name: str) -> ForgeResult:
        if not self.NAME_RE.fullmatch(name):
            return ForgeResult(name, "", "failed", error="Invalid skill name.")
        staged = self.staging / name
        if not staged.exists():
            return ForgeResult(name, "", "failed", error="No staged skill found. Forge it first.")
        target = self.root / name
        if target.exists():
            return ForgeResult(name, "", "failed", error="Skill already exists; refusing to overwrite it.")
        shutil.copytree(staged, target)
        manifest = target / "manifest.json"
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        return ForgeResult(name, payload["description"], "installed", str(target), payload.get("tests", ""))

    def run(self, name: str, args: list[str] | None = None) -> str:
        if not self.NAME_RE.fullmatch(name):
            return "Invalid skill name."
        target = self.root / name
        tool_file = target / "tool.py"
        if not tool_file.exists():
            return "Installed skill not found."

        runner = (
            "import json, sys\n"
            "from tool import Skill\n"
            "value = Skill().execute(*json.loads(sys.argv[1]))\n"
            "print(value if isinstance(value, str) else json.dumps(value, default=str))\n"
        )
        try:
            result = subprocess.run(
                [sys.executable, "-c", runner, json.dumps(args or [])],
                cwd=target,
                capture_output=True,
                text=True,
                timeout=20,
            )
        except subprocess.TimeoutExpired:
            return "Skill timed out after 20s."
        output = ((result.stdout or "") + (result.stderr or "")).strip()
        return output or f"Skill exited with code {result.returncode}."

    def list_staged(self) -> list[str]:
        return sorted(p.name for p in self.staging.iterdir() if p.is_dir())

    def list_installed(self) -> list[str]:
        return sorted(
            p.name for p in self.root.iterdir()
            if p.is_dir() and p.name != ".staging" and (p / "tool.py").exists()
        )

    def _stage_and_test(self, payload: dict) -> ForgeResult:
        name = payload["name"]
        stage = self.staging / name
        if stage.exists():
            shutil.rmtree(stage)
        stage.mkdir(parents=True)
        (stage / "tool.py").write_text(payload["code"], encoding="utf-8")
        (stage / "tests.py").write_text(payload["tests"], encoding="utf-8")
        (stage / "manifest.json").write_text(json.dumps({
            "name": name,
            "description": payload["description"],
            "tests": "tests.py",
            "generated_by": "Abyss Forge",
        }, indent=2), encoding="utf-8")
        try:
            result = subprocess.run(
                [sys.executable, "tests.py"], cwd=stage, capture_output=True,
                text=True, timeout=20,
            )
        except subprocess.TimeoutExpired:
            shutil.rmtree(stage, ignore_errors=True)
            return ForgeResult(name, payload["description"], "failed_tests", error="Tests timed out after 20s.")
        output = ((result.stdout or "") + (result.stderr or "")).strip()
        if result.returncode != 0:
            shutil.rmtree(stage, ignore_errors=True)
            return ForgeResult(name, payload["description"], "failed_tests", tests=output, error=output)
        return ForgeResult(name, payload["description"], "staged", str(stage), output)

    def _validate_payload(self, payload: dict):
        if set(payload) != {"name", "description", "code", "tests"}:
            raise ValueError("Forge response must contain name, description, code, and tests.")
        if not isinstance(payload["name"], str) or not self.NAME_RE.fullmatch(payload["name"]):
            raise ValueError("Invalid skill name.")
        for field in ("description", "code", "tests"):
            if not isinstance(payload[field], str) or not payload[field].strip():
                raise ValueError(f"Missing {field}.")
        self._validate_code(payload["code"])
        self._validate_code(payload["tests"], test_file=True)

    def _validate_code(self, source: str, test_file: bool = False):
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in self.BLOCKED_IMPORTS:
                        raise ValueError(f"Blocked import: {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if (node.module or "").split(".")[0] in self.BLOCKED_IMPORTS:
                    raise ValueError(f"Blocked import: {node.module}")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec", "__import__"}:
                    raise ValueError(f"Blocked builtin: {node.func.id}")
        if not test_file:
            classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Skill"]
            if not classes:
                raise ValueError("Generated skill must define class Skill.")
            methods = {n.name for n in classes[0].body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
            if "execute" not in methods:
                raise ValueError("Skill must define execute().")

    def _parse_json(self, raw: str) -> dict:
        """Parse model JSON, including common LLM formatting mistakes.

        Models sometimes return literal newlines/tabs inside JSON string values
        even after being asked for escaped JSON. strict=False lets the JSON
        decoder accept those control characters so Python code can reach the
        normal AST validation stage instead of failing at the transport layer.
        """
        candidates = [raw]
        if "```" in raw:
            fenced = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", raw.strip(), flags=re.IGNORECASE)
            candidates.insert(0, fenced)

        for candidate in candidates:
            try:
                return json.loads(candidate, strict=False)
            except json.JSONDecodeError:
                start, end = candidate.find("{"), candidate.rfind("}")
                if start >= 0 and end > start:
                    try:
                        return json.loads(candidate[start:end + 1], strict=False)
                    except json.JSONDecodeError:
                        pass

        raise ValueError("Forge model did not return valid JSON.")
