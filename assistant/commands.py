class CommandHandler:

    def __init__(self, manager):

        self.manager = manager

    def handle(self, user_message):

        if not user_message.startswith("/"):
            return None

        parts = user_message.split()
        command = parts[0].lower()

        if command == "/help":

            return """
Available Commands

/help
/provider groq
/status
/clear
/calc
/read
/ask
/edit
/project
/tree
/run
/askproject
/new
/load
/list
/delete
/memories
/remember <content>
/forget <id>
"""

        elif command == "/provider":

            if len(parts) != 2:
                return "Usage: /provider groq"

            provider = parts[1].lower()

            if self.manager.router.set_provider(provider):
                return f"✅ Switched to {provider.title()}"

            return "❌ Unknown provider."

        elif command == "/status":

            return (
                f"Provider : {self.manager.router.get_provider()}\n"
                f"Messages : {len(self.manager.conversation)}\n"
                f"Memories : {self.manager.memory.get_count()}"
            )

        elif command == "/clear":

            self.manager.conversation = [self.manager.system_prompt]

            provider = self.manager.router.get_provider()
            self.manager.chat_manager.save(
                self.manager.conversation,
                provider=provider
            )

            return "✅ Conversation cleared."
        
        elif command == "/new":

            if len(parts) != 2:
                return "Usage: /new chatname"

            name = parts[1]

            self.manager.chat_manager.new(name)

            self.manager.conversation = [
                self.manager.system_prompt
            ]

            provider = self.manager.router.get_provider()
            self.manager.chat_manager.save(
                self.manager.conversation,
                provider=provider
            )

            return f"✅ Created chat '{name}'"
        
        elif command == "/load":

            if len(parts) != 2:
                return "Usage: /load chatname"

            name = parts[1]

            conversation = self.manager.chat_manager.switch(name)

            if conversation:
                self.manager.conversation = conversation
            else:
                self.manager.conversation = [
                    self.manager.system_prompt
                ]

            # Restore the provider that was active when this chat was last saved.
            meta = self.manager.chat_manager.load_meta()
            saved_provider = meta.get("provider", "")
            if saved_provider:
                self.manager.router.set_provider(saved_provider)

            return f"✅ Loaded '{name}'"
        
        elif command == "/list":

            chats = self.manager.chat_manager.list()

            if not chats:
                return "No chats found."

            return "\n".join(chats)
        
        elif command == "/delete":

            if len(parts) != 2:
                return "Usage: /delete chatname"

            name = parts[1]

            self.manager.chat_manager.delete(name)

            return f"✅ Deleted '{name}'"

        elif command in {"/memories", "/memory"}:

            memories = self.manager.memory.recall(limit=None)
            count = self.manager.memory.get_count()

            if not memories:
                return f"🧠 Memory Subsystem (Total: {count})\n\nNo memories stored yet."

            lines = [f"🧠 Memory Subsystem (Total: {count}):\n"]
            for m in memories:
                lines.append(f"[{m['id']}] {m['content']}")

            return "\n".join(lines)

        elif command == "/remember":

            if len(parts) < 2:
                return "Usage: /remember <content>"

            content = user_message.replace("/remember", "", 1).strip()
            self.manager.memory.remember(content)

            return "✅ Memory stored."

        elif command == "/forget":

            if len(parts) != 2:
                return "Usage: /forget <id>"

            try:
                mem_id = int(parts[1])
            except ValueError:
                return "❌ Invalid ID. Please specify a numeric memory ID."

            self.manager.memory.forget(mem_id)

            return f"✅ Memory #{mem_id} forgotten."

        elif command == "/calc":

            expression = user_message.replace("/calc", "").strip()

            try:
                return str(self.manager.calculator.execute(expression))
            except Exception:
                return "Invalid expression."

        elif command == "/read":

            if len(parts) != 2:
                return "Usage: /read filename"

            return self.manager.filesystem.read(parts[1])

        elif command == "/project":

            return self.manager.filesystem.list_directory()
        
        elif command == "/tree":

            return self.manager.filesystem.tree()
        
        elif command == "/askproject":

            if len(parts) < 2:
                return "Usage: /askproject question"

            question = " ".join(parts[1:])

            project = self.manager.filesystem.read_project()

            prompt = f"""
        You are analyzing a Python project.

        Project:

        {project}

        Question:

        {question}
        """

            response = self.manager.router.chat(
                [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            return response
                
        elif command == "/run":

            if len(parts) != 2:
                return "Usage: /run filename.py"

            filename = parts[1]

            return self.manager.terminal.execute(f"python {filename}")

        elif command == "/ask":

            if len(parts) < 3:
                return "Usage: /ask filename question"

            filename = parts[1]
            question = " ".join(parts[2:])

            file_contents = self.manager.filesystem.read(filename)

            prompt = f"""
Here is a file.

Filename:
{filename}

Contents:
{file_contents}

User Question:
{question}
"""

            self.manager.conversation.append(
                {
                    "role": "user",
                    "content": prompt
                }
            )

            response = self.manager.router.chat(self.manager.conversation)

            self.manager.conversation.append(
                {
                    "role": "assistant",
                    "content": response
                }
            )

            return response

        elif command == "/edit":

            if len(parts) < 3:
                return "Usage: /edit filename instruction"

            filename = parts[1]
            instruction = " ".join(parts[2:])

            original_code = self.manager.filesystem.read(filename)

            prompt = f"""
You are an expert Python developer.

Modify the following file according to the user's request.

IMPORTANT:
Return ONLY the complete updated file.
Do not explain anything.
Do not use markdown.
Do not wrap the code in ```.

User Request:
{instruction}

Current File:

{original_code}
"""

            response = self.manager.router.chat(
                [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            self.manager.filesystem.write(filename, response)

            return "✅ File edited successfully."

        return "Unknown command. Type /help"