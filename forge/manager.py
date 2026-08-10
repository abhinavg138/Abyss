from __future__ import annotations

import ast
import difflib
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
    """Controlled runtime skill creation, testing and self-repair."""

    BLOCKED_IMPORTS = {
        "os", "subprocess", "socket", "shutil", "ctypes", "multiprocessing",
        "sys", "importlib", "requests", "httpx", "urllib", "ftplib",
    }
    BLOCKED_CALLS = {"eval", "exec", "__import__", "compile", "open"}
    NAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,31}$")

    def __init__(self, router, root: str | Path = "extensions"):
        self.router = router
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.staging = self.root / ".staging"
        self.backups = self.root / ".backups"
        self.staging.mkdir(parents=True, exist_ok=True)
        self.backups.mkdir(parents=True, exist_ok=True)

    def forge(self, request: str) -> ForgeResult:
        request = request.strip()
        if not request:
            return ForgeResult("unknown", "", "failed", error="No capability request supplied.")
        prompt = f"""
You are Abyss Forge, a conservative Python skill generator.
Create ONE small reusable skill for this request:
{request}
Return ONLY valid JSON with exactly: name, description, code, tests.
The code/tests fields are JSON strings. Escape newlines, quotes and backslashes correctly. No markdown fences.
Rules: lowercase snake_case name; class Skill with execute(self,*args,**kwargs); unittest tests importing Skill from tool.py; standard library only; no os, subprocess, socket, shutil, ctypes, multiprocessing, sys, importlib, requests, httpx, urllib, ftplib; no eval, exec, __import__, compile or open; no arbitrary filesystem/network access; deterministic tests.
"""
        try:
            payload = self._validated_generation(prompt)
            return self._stage_and_test(payload)
        except Exception as exc:
            return ForgeResult("unknown", "", "failed", error=str(exc))

    def upgrade(self, name: str, request: str = "Improve reliability, edge-case handling and test coverage without changing the public interface.") -> ForgeResult:
        """Generate, test and atomically install a new version of an installed skill."""
        name = self.resolve_name(name, staged=False) or name
        if not self.NAME_RE.fullmatch(name):
            return ForgeResult(name, "", "failed", error="Invalid skill name.")
        target = self.root / name
        tool = target / "tool.py"
        tests = target / "tests.py"
        manifest = target / "manifest.json"
        if not tool.exists() or not tests.exists():
            return ForgeResult(name, "", "failed", error=f"Installed skill '{name}' not found.")

        old_code = tool.read_text(encoding="utf-8")
        old_tests = tests.read_text(encoding="utf-8")
        old_manifest = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else {"version": 1, "description": name}
        version = int(old_manifest.get("version", 1)) + 1
        prompt = f"""
You are Abyss Forge Evolution.
Improve the installed skill below.
Reason for improvement: {request}

Current skill name: {name}
Current code:
{old_code}

Current tests:
{old_tests}

Return ONLY valid JSON with exactly: name, description, code, tests.
Keep name exactly {name}. Preserve execute() and existing behavior.
Add regression tests for the requested improvement. Standard library only.
No os, subprocess, socket, shutil, ctypes, multiprocessing, sys, importlib,
requests, httpx, urllib, ftplib, eval, exec, __import__, compile or open.
No markdown fences.
"""
        try:
            payload = self._validated_generation(prompt)
            if payload["name"] != name:
                raise ValueError("Evolution must preserve the skill name.")
            result = self._stage_and_test(payload, version=version)
            if result.status != "staged":
                return result
            return self._promote_staged(name, payload["description"], result.tests, old_manifest.get("version", 1), "upgraded")
        except Exception as exc:
            return ForgeResult(name, "", "failed", error=str(exc))

    def repair(self, name: str, failure: str, args: list[str] | None = None) -> ForgeResult:
        """Diagnose a failed skill run, generate a repair, regression-test it and promote it."""
        name = self.resolve_name(name, staged=False) or name
        if not self.NAME_RE.fullmatch(name):
            return ForgeResult(name, "", "failed", error="Invalid skill name.")
        target = self.root / name
        tool = target / "tool.py"
        tests = target / "tests.py"
        manifest_path = target / "manifest.json"
        if not tool.exists() or not tests.exists():
            return ForgeResult(name, "", "failed", error=f"Installed skill '{name}' not found.")

        old_code = tool.read_text(encoding="utf-8")
        old_tests = tests.read_text(encoding="utf-8")
        old_manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"version": 1, "description": name}
        old_version = int(old_manifest.get("version", 1))
        prompt = f"""
You are Abyss Forge Repair.
An installed skill failed during execution. Diagnose the failure and produce a minimal repair.

Skill: {name}
Arguments: {json.dumps(args or [])}
Observed failure:
{failure[:6000]}

Current code:
{old_code}

Current tests:
{old_tests}

Return ONLY valid JSON with exactly: name, description, code, tests.
Keep name exactly {name}. Preserve the execute() interface and all working behavior.
Add a regression test reproducing the failure and tests for the repair.
Do not merely weaken validation to make the test pass.
Standard library only. No os, subprocess, socket, shutil, ctypes, multiprocessing,
sys, importlib, requests, httpx, urllib, ftplib, eval, exec, __import__, compile or open.
No markdown fences.
"""
        try:
            payload = self._validated_generation(prompt)
            if payload["name"] != name:
                raise ValueError("Repair must preserve the skill name.")
            result = self._stage_and_test(payload, version=old_version + 1)
            if result.status != "staged":
                return result
            return self._promote_staged(name, payload["description"], result.tests, old_version, "repaired")
        except Exception as exc:
            return ForgeResult(name, "", "failed", error=str(exc))

    def install(self, name: str) -> ForgeResult:
        requested = name
        name = self.resolve_name(name, staged=True) or name
        if not self.NAME_RE.fullmatch(name):
            return ForgeResult(name, "", "failed", error="Invalid skill name.")
        staged = self.staging / name
        if not staged.exists():
            suggestions = self.suggestions(requested, staged=True)
            hint = f" Did you mean: {', '.join(suggestions[:3])}?" if suggestions else ""
            return ForgeResult(name, "", "failed", error=f"No staged skill found. Forge it first.{hint}")
        target = self.root / name
        if target.exists():
            return ForgeResult(name, "", "failed", error="Skill already exists; use /forge-upgrade to evolve it.")
        shutil.copytree(staged, target)
        manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
        return ForgeResult(name, manifest["description"], "installed", str(target), manifest.get("tests", ""))

    def run(self, name: str, args: list[str] | None = None, auto_repair: bool = True) -> str:
        requested = name
        name = self.resolve_name(name, staged=False) or name
        if not self.NAME_RE.fullmatch(name):
            return "Invalid skill name."
        target = self.root / name
        if not (target / "tool.py").exists():
            suggestions = self.suggestions(requested)
            if suggestions:
                return f"Installed skill '{requested}' not found. Did you mean: {', '.join(suggestions[:3])}?"
            return f"Installed skill '{requested}' not found. Use /skills to see installed skills."

        result = self._execute(name, args)
        if result[0]:
            return result[1]

        failure = result[1]
        if not auto_repair:
            return f"Skill '{name}' failed.\n{failure}"

        repair_result = self.repair(name, failure, args)
        if repair_result.status != "repaired":
            return (
                f"Skill '{name}' failed.\n{failure}\n\n"
                f"🛠️ Automatic repair failed: {repair_result.error or repair_result.tests}"
            )

        retry = self._execute(name, args)
        if retry[0]:
            return (
                f"🛠️ Skill '{name}' failed, Forge repaired it, regression tests passed, "
                f"and the retry succeeded.\n\n{retry[1]}"
            )
        return (
            f"Skill '{name}' failed. Forge produced a repair and tests passed, "
            f"but the retry still failed.\n\n{retry[1]}"
        )

    def _execute(self, name: str, args: list[str] | None = None) -> tuple[bool, str]:
        target = self.root / name
        runner = "import json, sys\nfrom tool import Skill\nvalue = Skill().execute(*json.loads(sys.argv[1]))\nprint(value if isinstance(value, str) else json.dumps(value, default=str))\n"
        try:
            result = subprocess.run([sys.executable, "-c", runner, json.dumps(args or [])], cwd=target, capture_output=True, text=True, timeout=20)
        except subprocess.TimeoutExpired:
            return False, "Execution timed out after 20s."
        output = ((result.stdout or "") + (result.stderr or "")).strip()
        if result.returncode != 0:
            return False, f"Exit code {result.returncode}\n{output}"
        return True, output or f"Skill '{name}' returned no output."

    def _promote_staged(self, name: str, description: str, tests: str, old_version: int, status: str) -> ForgeResult:
        staged = self.staging / name
        target = self.root / name
        backup = self.backups / f"{name}_v{old_version}"
        if backup.exists():
            shutil.rmtree(backup)
        shutil.copytree(target, backup)
        shutil.rmtree(target)
        shutil.copytree(staged, target)
        return ForgeResult(name, description, status, str(target), tests)

    def list_staged(self) -> list[str]:
        return sorted(p.name for p in self.staging.iterdir() if p.is_dir())

    def list_installed(self) -> list[str]:
        return sorted(p.name for p in self.root.iterdir() if p.is_dir() and p.name not in {".staging", ".backups"} and (p / "tool.py").exists())

    def suggestions(self, name: str, staged: bool = False) -> list[str]:
        pool = self.list_staged() if staged else self.list_installed()
        query = name.lower().replace("-", "_").strip()
        scored = []
        for candidate in pool:
            score = difflib.SequenceMatcher(None, query, candidate).ratio()
            if query in candidate or candidate in query:
                score += 0.25
            scored.append((score, candidate))
        return [candidate for score, candidate in sorted(scored, reverse=True) if score >= 0.35]

    def resolve_name(self, name: str, staged: bool = False) -> str | None:
        pool = self.list_staged() if staged else self.list_installed()
        normalized = name.lower().replace("-", "_").strip()
        if normalized in pool:
            return normalized
        suggestions = self.suggestions(normalized, staged=staged)
        if suggestions and difflib.SequenceMatcher(None, normalized, suggestions[0]).ratio() >= 0.82:
            return suggestions[0]
        return None

    def _validated_generation(self, prompt: str) -> dict:
        raw = self.router.chat([{"role": "user", "content": prompt}]).strip()
        payload = self._parse_json(raw)
        self._validate_payload(payload)
        return payload

    def _stage_and_test(self, payload: dict, version: int = 1) -> ForgeResult:
        name = payload["name"]
        stage = self.staging / name
        if stage.exists():
            shutil.rmtree(stage)
        stage.mkdir(parents=True)
        (stage / "tool.py").write_text(payload["code"], encoding="utf-8")
        (stage / "tests.py").write_text(payload["tests"], encoding="utf-8")
        (stage / "manifest.json").write_text(json.dumps({"name": name, "description": payload["description"], "tests": "tests.py", "generated_by": "Abyss Forge", "version": version}, indent=2), encoding="utf-8")
        try:
            result = subprocess.run([sys.executable, "tests.py"], cwd=stage, capture_output=True, text=True, timeout=20)
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
            elif isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] in self.BLOCKED_IMPORTS:
                raise ValueError(f"Blocked import: {node.module}")
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in self.BLOCKED_CALLS:
                raise ValueError(f"Blocked builtin: {node.func.id}")
        if not test_file:
            classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Skill"]
            if not classes:
                raise ValueError("Generated skill must define class Skill.")
            methods = {n.name for n in classes[0].body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
            if "execute" not in methods:
                raise ValueError("Skill must define execute().")

    def _parse_json(self, raw: str) -> dict:
        candidates = [raw]
        if "```" in raw:
            candidates.insert(0, re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", raw.strip(), flags=re.IGNORECASE))
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
