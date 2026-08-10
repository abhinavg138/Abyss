from providers.router import Router
from assistant.commands import CommandHandler

from tools.calculator import CalculatorTool
from tools.filesystem import FilesystemTool
from tools.terminal import TerminalTool
from assistant.tool_router import ToolRouter
from memory.manager import MemoryManager
from memory.extractor import MemoryExtractor
from chat.manager import ChatManager

import os
import base64
from pathlib import Path


def extract_text_from_file(file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()

    if suffix == ".pdf":
        import pypdf
        reader = pypdf.PdfReader(file_path)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        return text

    elif suffix == ".docx":
        import docx
        doc = docx.Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])

    else:
        # txt, md, csv, json, py, cpp, java, js, html, css
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()


def chunk_text(text: str, chunk_size: int = 50000) -> list[str]:
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks


def is_image_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}


def file_to_base64_data_url(file_path: str) -> str:
    suffix = Path(file_path).suffix.lower().strip(".")
    if suffix == "jpg":
        suffix = "jpeg"
    with open(file_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    return f"data:image/{suffix};base64,{encoded_string}"


class AssistantManager:

    def __init__(self):

        self.calculator = CalculatorTool()
        self.filesystem = FilesystemTool()
        self.terminal = TerminalTool()

        self.router = Router()
        self.tool_router = ToolRouter(self.router)
        self.memory = MemoryManager()
        self.chat_manager = ChatManager()

        self.system_prompt = {
            "role": "system",
            "content": (
                "You are Abyss, a personal AI assistant created by "
                "Abhinav Gupta. "
                "Never introduce yourself as ChatGPT or Llama."
            )
        }

        saved = self.chat_manager.load()

        if saved:
            self.conversation = saved
        else:
            self.conversation = [self.system_prompt]
            provider = self.router.get_provider()
            self.chat_manager.save(self.conversation, provider=provider)

        # Restore the provider that was active when this chat was last saved.
        meta = self.chat_manager.load_meta()
        saved_provider = meta.get("provider", "")
        if saved_provider:
            self.router.set_provider(saved_provider)

        self.command_handler = CommandHandler(self)

    # ── public API ────────────────────────────────────────────────

    def chat(self, user_message: str, attachments: list = None):

        before_command = len(self.conversation)
        tool_command = self.tool_router.route(user_message)

        if tool_command != "NONE":
            command_result = self.command_handler.handle(tool_command)
        else:
            command_result = self.command_handler.handle(user_message)

        if command_result is not None:
            self._save_command_response(user_message, command_result, before_command)
            return command_result

        self.conversation.append({
            "role": "user",
            "content": user_message,
            "attachments": attachments or []
        })

        messages = self._build_messages_with_memory()

        response = self.router.chat(messages)

        self._extract_and_store_memory(user_message)

        self.conversation.append({"role": "assistant", "content": response})

        provider = self.router.get_provider()
        self.chat_manager.save(self.conversation, provider=provider)

        # Generate AI title after the FIRST assistant response only
        self._maybe_generate_title(user_message)

        return response

    def stream(self, user_message: str, attachments: list = None):

        before_command = len(self.conversation)
        tool_command = self.tool_router.route(user_message)

        if tool_command != "NONE":
            command_result = self.command_handler.handle(tool_command)
        else:
            command_result = self.command_handler.handle(user_message)

        if command_result is not None:
            self._save_command_response(user_message, command_result, before_command)
            yield command_result
            return

        self.conversation.append({
            "role": "user",
            "content": user_message,
            "attachments": attachments or []
        })

        messages = self._build_messages_with_memory()

        full_response = ""

        for token in self.router.stream(messages):
            full_response += token
            yield token

        self._extract_and_store_memory(user_message)

        self.conversation.append({"role": "assistant", "content": full_response})

        provider = self.router.get_provider()
        self.chat_manager.save(self.conversation, provider=provider)

        # Generate AI title after the FIRST assistant response only
        self._maybe_generate_title(user_message)

    # ── title generation ──────────────────────────────────────────

    def _maybe_generate_title(self, user_message: str):
        """
        Called after the first assistant response.
        If this chat has never been titled, ask the AI for a 2-5 word title
        and rename the file accordingly. Never renames again after that.
        """
        meta = self.chat_manager.load_meta()
        if meta.get("auto_named") or not self.chat_manager.is_auto_name_candidate():
            return

        # Only title on the first real exchange (system + user + assistant = 3 messages)
        non_system = [m for m in self.conversation if m.get("role") != "system"]
        if len(non_system) != 2:  # exactly 1 user + 1 assistant
            return

        try:
            title_prompt = [
                {
                    "role": "system",
                    "content": (
                        "You are a chat title generator. "
                        "Given the user's first message, reply with ONLY a short title "
                        "of 2 to 5 words that captures the topic. "
                        "No punctuation at the end. No quotes. No explanation."
                    )
                },
                {
                    "role": "user",
                    "content": user_message[:500]  # cap length
                }
            ]

            title = self.router.chat(title_prompt).strip().strip('"\'')

            # Sanity-check: must be 1-8 words and not absurdly long
            word_count = len(title.split())
            if 1 <= word_count <= 8 and len(title) <= 60:
                provider = self.router.get_provider()
                self.chat_manager.set_title(title, provider=provider, auto_named=True)

        except Exception:
            # Title generation is best-effort; never crash the chat
            pass

    # ── private helpers ───────────────────────────────────────────

    def _build_messages_with_memory(self) -> list:
        messages = []
        for msg in self.conversation:
            msg_copy = msg.copy()
            attachments = msg.get("attachments", [])
            
            text_attachments = []
            image_attachments = []
            for attachment in attachments:
                filename = attachment.get("filename", "")
                if is_image_file(filename):
                    image_attachments.append(attachment)
                else:
                    text_attachments.append(attachment)
            
            # Process text attachments
            text_context = ""
            if text_attachments:
                for attachment in text_attachments:
                    temp_path = attachment.get("temp_path")
                    filename = attachment.get("filename")
                    if temp_path and os.path.exists(temp_path):
                        try:
                            content = extract_text_from_file(temp_path)
                            chunks = chunk_text(content)
                            for idx, chunk in enumerate(chunks):
                                if len(chunks) > 1:
                                    text_context += f"\n\n--- Start of File: {filename} (Part {idx+1}/{len(chunks)}) ---\n{chunk}\n--- End of Part {idx+1} ---"
                                else:
                                    text_context += f"\n\n--- Start of File: {filename} ---\n{chunk}\n--- End of File ---"
                        except Exception as e:
                            text_context += f"\n\n[Error reading file {filename}: {str(e)}]"

            base_content = msg_copy.get("content") or ""
            if text_context:
                base_content = base_content + "\n" + text_context

            # Process image attachments
            if image_attachments:
                content_list = [{"type": "text", "text": base_content}]
                for attachment in image_attachments:
                    temp_path = attachment.get("temp_path")
                    if temp_path and os.path.exists(temp_path):
                        try:
                            data_url = file_to_base64_data_url(temp_path)
                            content_list.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": data_url
                                }
                            })
                        except Exception as e:
                            content_list.append({
                                "type": "text",
                                "text": f"\n[Error loading image {attachment.get('filename')}: {str(e)}]"
                            })
                msg_copy["content"] = content_list
            else:
                msg_copy["content"] = base_content

            if "attachments" in msg_copy:
                del msg_copy["attachments"]
            messages.append(msg_copy)

        memory_context = self.memory.get_context()

        if memory_context:
            messages.insert(0, {"role": "system", "content": memory_context})

        return messages

    def _extract_and_store_memory(self, user_message: str):
        result = MemoryExtractor.extract(self.router, user_message)

        if result.get("remember"):
            self.memory.remember(result["memory"])

    def _save_command_response(self, user_message: str, response: str, before_command: int):

        command = user_message.split(maxsplit=1)[0].lower() if user_message.startswith("/") else ""

        # Lifecycle commands handle their own persistence (or need none).
        if command in {"/clear", "/new", "/load", "/delete"}:
            return

        # If the command already appended messages to the conversation
        # (e.g. /ask, /edit), don't duplicate them.
        if not self._last_assistant_response_is(response) and len(self.conversation) == before_command:
            self.conversation.append({"role": "user",      "content": user_message})
            self.conversation.append({"role": "assistant", "content": response})

        provider = self.router.get_provider()
        self.chat_manager.save(self.conversation, provider=provider)

    def _last_assistant_response_is(self, response: str) -> bool:
        if not self.conversation:
            return False

        last_message = self.conversation[-1]

        return (
            last_message.get("role") == "assistant"
            and last_message.get("content") == response
        )
