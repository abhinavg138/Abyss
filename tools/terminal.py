from tools.base import BaseTool
import subprocess


class TerminalTool(BaseTool):
    """Run local commands with bounded execution time and captured output."""

    def execute(self, command, timeout=30):
        command = str(command).strip()
        if not command:
            return "No command provided."

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=max(1, min(int(timeout), 120)),
                cwd=None,
            )
        except subprocess.TimeoutExpired:
            return f"Command timed out after {timeout}s."
        except Exception as e:
            return f"Terminal error: {e}"

        output = (result.stdout or "") + (result.stderr or "")
        output = output.strip()
        if not output:
            return f"Command finished with exit code {result.returncode}."

        if result.returncode != 0:
            return f"Exit code {result.returncode}\n{output}"
        return output
