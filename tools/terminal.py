from tools.base import BaseTool
import subprocess


class TerminalTool(BaseTool):

    def execute(self, command):

        try:

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )

            if result.stdout:
                return result.stdout

            if result.stderr:
                return result.stderr

            return "Command executed."

        except Exception as e:
            return str(e)