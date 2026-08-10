import google.generativeai as genai

from config import Config
from providers.base import BaseProvider


def _to_gemini_messages(messages: list[dict]) -> tuple[str, list, list]:
    """
    Convert OpenAI-style message list into a Gemini system prompt +
    history list that the GenerativeModel.start_chat() API expects.

    Gemini format:
        history = [{"role": "user"|"model", "parts": ["text"|PIL.Image]}]
    The last user message is sent separately via chat.send_message().
    """
    system_parts = []
    history = []
    last_user_parts = []

    for msg in messages:
        role = msg["role"]
        content = msg["content"] or ""

        # Convert content to parts (list of strings/images)
        parts = []
        if isinstance(content, list):
            for part in content:
                if part.get("type") == "text":
                    parts.append(part.get("text", ""))
                elif part.get("type") == "image_url":
                    url = part.get("image_url", {}).get("url", "")
                    if url.startswith("data:image/"):
                        try:
                            import base64
                            import io
                            from PIL import Image
                            header, encoded = url.split(",", 1)
                            img_data = base64.b64decode(encoded)
                            img = Image.open(io.BytesIO(img_data))
                            parts.append(img)
                        except Exception as e:
                            parts.append(f"\n[Error parsing image: {str(e)}]")
        else:
            parts = [content]

        if role == "system":
            system_parts.extend([p for p in parts if isinstance(p, str)])
        elif role == "user":
            if last_user_parts:
                history.append({"role": "user", "parts": last_user_parts})
            last_user_parts = parts
        elif role == "assistant":
            if last_user_parts:
                history.append({"role": "user",  "parts": last_user_parts})
                last_user_parts = []
            history.append({"role": "model", "parts": parts})

    if not last_user_parts:
        last_user_parts = [""]

    system_instruction = "\n\n".join(system_parts) if system_parts else None
    return system_instruction, history, last_user_parts


class GeminiProvider(BaseProvider):
    supports_vision = True

    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self._model_name = Config.GEMINI_MODEL

    def _build_chat(self, messages: list[dict]):
        system_instruction, history, last_user_msg = _to_gemini_messages(messages)

        model = genai.GenerativeModel(
            model_name=self._model_name,
            system_instruction=system_instruction,
        )
        chat = model.start_chat(history=history)
        return chat, last_user_msg

    def chat(self, messages: list[dict]) -> str:
        chat, last_user_msg = self._build_chat(messages)
        response = chat.send_message(last_user_msg)
        return response.text

    def stream_chat(self, messages: list[dict]):
        chat, last_user_msg = self._build_chat(messages)
        # stream=True makes send_message return an iterable of chunks
        for chunk in chat.send_message(last_user_msg, stream=True):
            text = chunk.text
            if text:
                yield text
