from tools.browser import BrowserTool
from assistant.agent import AgentEngine


class CommandHandler:
    def __init__(self, manager):
        self.manager = manager
        self.browser = BrowserTool()

    def handle(self, user_message):
        if not user_message.startswith("/"):
            return None

        parts = user_message.split()
        command = parts[0].lower()

        if command == "/help":
            return """Available Commands

/help
/provider groq
/status
/agent TASK
/clear
/calc EXPR
/read FILE
/write FILE CONTENT
/find PATTERN [PATH]
/grep QUERY [PATH]
/ask FILE QUESTION
/edit FILE INSTRUCTION
/project
/tree
/run FILE.py
/shell COMMAND
/web URL
/tools
/forge CAPABILITY
/forge-install NAME
/forge-run NAME [ARGS...]
/forge-upgrade NAME [IMPROVEMENT]
/skills
/askproject QUESTION
/new NAME
/load NAME
/list
/delete NAME
/memories
/remember CONTENT
/forget ID
"""

        if command == "/agent":
            task = user_message.replace("/agent", "", 1).strip()
            if not task:
                return "Usage: /agent <task>\nExample: /agent inspect this project and find why streaming is broken"
            agent = AgentEngine(
                self.manager.router,
                self.manager.filesystem,
                self.manager.terminal,
                self.manager.calculator,
                self.browser,
            )
            return agent.run(task)

        if command == "/tools":
            return """Abyss Tools 2.0

calculator  — safe arithmetic
read_file   — read text files
write_file  — create/update files
list_files  — list a directory
find_files  — find files by wildcard
grep        — search text across files
tree        — project tree
project     — read Python project source
terminal    — execute local commands (120s max)
browser     — fetch public HTTP/HTTPS URLs

Abyss Agent
agent       — autonomous multi-step tool-calling workflow using GLM-5.2

Abyss Forge
forge         — generate + test a new skill
forge-install — install a staged skill
forge-run     — execute an installed skill
forge-upgrade — generate, test and replace a skill with a newer version
skills        — list staged/installed skills
"""

        if command == "/forge":
            request = user_message.replace("/forge", "", 1).strip()
            if not request:
                return "Usage: /forge <capability>\nExample: /forge convert Roman numerals to integers"
            result = self.manager.forge.forge(request)
            if result.status == "staged":
                return f"🛠️ Forge completed\n\nSkill: {result.name}\nWhat it does: {result.description}\n\nTests: PASSED\n{result.tests}\n\nStatus: STAGED — not installed\nRun /forge-install {result.name} to install it."
            return f"❌ Forge failed: {result.error or result.tests}"

        if command == "/forge-install":
            if len(parts) != 2:
                return "Usage: /forge-install <skill_name>"
            result = self.manager.forge.install(parts[1])
            if result.status == "installed":
                return f"✅ Installed {result.name}\n{result.description}\nPath: {result.path}"
            return f"❌ Install failed: {result.error}"

        if command == "/forge-run":
            if len(parts) < 2:
                return "Usage: /forge-run <skill_name> [args...]"
            return self.manager.forge.run(parts[1], parts[2:])

        if command == "/forge-upgrade":
            if len(parts) < 2:
                return "Usage: /forge-upgrade <skill_name> [improvement request]"
            request = " ".join(parts[2:]) or "Improve reliability, edge-case handling and test coverage without changing the public interface."
            result = self.manager.forge.upgrade(parts[1], request)
            if result.status == "upgraded":
                return f"🧬 Evolution complete\n\nSkill: {result.name}\nVersion upgraded\nTests: PASSED\n{result.tests}\n\nPrevious version backed up in extensions/.backups/"
            return f"❌ Evolution failed: {result.error or result.tests}"

        if command == "/skills":
            staged = self.manager.forge.list_staged()
            installed = self.manager.forge.list_installed()
            lines = ["Abyss Forge Skills", "", "Staged:"]
            lines.extend(f"  • {name}" for name in staged) if staged else lines.append("  None")
            lines.extend(["", "Installed:"])
            lines.extend(f"  • {name}" for name in installed) if installed else lines.append("  None")
            return "\n".join(lines)

        if command == "/provider":
            if len(parts) != 2:
                return "Usage: /provider groq"
            provider = parts[1].lower()
            return f"✅ Switched to {provider.title()}" if self.manager.router.set_provider(provider) else "❌ Unknown provider."

        if command == "/status":
            return f"Provider : {self.manager.router.get_provider()}\nMessages : {len(self.manager.conversation)}\nMemories : {self.manager.memory.get_count()}\nSkills   : {len(self.manager.forge.list_installed())} installed"

        if command == "/clear":
            self.manager.conversation = [self.manager.system_prompt]
            self.manager.chat_manager.save(self.manager.conversation, provider=self.manager.router.get_provider())
            return "✅ Conversation cleared."

        if command == "/new":
            if len(parts) != 2:
                return "Usage: /new chatname"
            name = parts[1]
            self.manager.chat_manager.new(name)
            self.manager.conversation = [self.manager.system_prompt]
            self.manager.chat_manager.save(self.manager.conversation, provider=self.manager.router.get_provider())
            return f"✅ Created chat '{name}'"

        if command == "/load":
            if len(parts) != 2:
                return "Usage: /load chatname"
            name = parts[1]
            conversation = self.manager.chat_manager.switch(name)
            self.manager.conversation = conversation or [self.manager.system_prompt]
            meta = self.manager.chat_manager.load_meta()
            if meta.get("provider"):
                self.manager.router.set_provider(meta["provider"])
            return f"✅ Loaded '{name}'"

        if command == "/list":
            chats = self.manager.chat_manager.list()
            return "\n".join(chats) if chats else "No chats found."

        if command == "/delete":
            if len(parts) != 2:
                return "Usage: /delete chatname"
            self.manager.chat_manager.delete(parts[1])
            return f"✅ Deleted '{parts[1]}'"

        if command in {"/memories", "/memory"}:
            memories = self.manager.memory.recall(limit=None)
            lines = [f"🧠 Memory Subsystem (Total: {len(memories)}):\n"]
            lines.extend(f"[{m['id']}] {m['content']}" for m in memories)
            return "\n".join(lines) if memories else f"🧠 Memory Subsystem (Total: {len(memories)})\n\nNo memories stored yet."

        if command == "/remember":
            content = user_message.replace("/remember", "", 1).strip()
            if not content:
                return "Usage: /remember <content>"
            self.manager.memory.remember(content)
            return "✅ Memory stored."

        if command == "/forget":
            if len(parts) != 2:
                return "Usage: /forget <id>"
            try:
                mem_id = int(parts[1])
            except ValueError:
                return "❌ Invalid ID. Please specify a numeric memory ID."
            self.manager.memory.forget(mem_id)
            return f"✅ Memory #{mem_id} forgotten."

        if command == "/calc":
            expression = user_message.replace("/calc", "", 1).strip()
            try:
                return str(self.manager.calculator.execute(expression))
            except Exception as e:
                return f"Invalid expression: {e}"

        if command == "/read":
            if len(parts) != 2:
                return "Usage: /read filename"
            return self.manager.filesystem.read(parts[1])

        if command == "/write":
            if len(parts) < 3:
                return "Usage: /write filename content"
            filename = parts[1]
            content = user_message.split(None, 2)[2]
            return "✅ " + self.manager.filesystem.write(filename, content)

        if command == "/find":
            if len(parts) < 2:
                return "Usage: /find pattern [path]"
            pattern = parts[1]
            path = parts[2] if len(parts) > 2 else "."
            return self.manager.filesystem.find(pattern, path)

        if command == "/grep":
            if len(parts) < 2:
                return "Usage: /grep query [path]"
            query = parts[1]
            path = parts[2] if len(parts) > 2 else "."
            return self.manager.filesystem.grep(query, path)

        if command == "/project":
            return self.manager.filesystem.list_directory()

        if command == "/tree":
            return self.manager.filesystem.tree()

        if command == "/run":
            if len(parts) != 2:
                return "Usage: /run filename.py"
            return self.manager.terminal.execute(f"python {parts[1]}")

        if command == "/shell":
            command_text = user_message.replace("/shell", "", 1).strip()
            if not command_text:
                return "Usage: /shell command"
            return self.manager.terminal.execute(command_text)

        if command == "/web":
            if len(parts) != 2:
                return "Usage: /web URL"
            return self.browser.execute(parts[1])

        if command == "/askproject":
            if len(parts) < 2:
                return "Usage: /askproject question"
            project = self.manager.filesystem.read_project()
            question = " ".join(parts[1:])
            return self.manager.router.chat([{"role": "user", "content": f"You are analyzing a Python project.\n\nProject:\n{project}\n\nQuestion:\n{question}"}])

        if command == "/ask":
            if len(parts) < 3:
                return "Usage: /ask filename question"
            filename = parts[1]
            question = " ".join(parts[2:])
            file_contents = self.manager.filesystem.read(filename)
            prompt = f"Here is a file.\n\nFilename:\n{filename}\n\nContents:\n{file_contents}\n\nUser Question:\n{question}"
            return self.manager.router.chat([{"role": "user", "content": prompt}])

        if command == "/edit":
            if len(parts) < 3:
                return "Usage: /edit filename instruction"
            filename = parts[1]
            instruction = " ".join(parts[2:])
            original_code = self.manager.filesystem.read(filename)
            prompt = f"""You are an expert developer. Modify this file according to the request.
Return ONLY the complete updated file. No markdown. No explanation.

User Request:
{instruction}

Current File:
{original_code}"""
            response = self.manager.router.chat([{"role": "user", "content": prompt}])
            self.manager.filesystem.write(filename, response)
            return "✅ File edited successfully."

        return "Unknown command. Type /help"
