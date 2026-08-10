from openai import OpenAI

from config import Config
from providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    supports_vision = True

    def __init__(self):
        self.client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            timeout=60,
        )

    def chat(self, messages: list[dict]) -> str:
        response = self.client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=messages,
        )
        return response.choices[0].message.content

    def stream_chat(self, messages: list[dict]):
        stream = self.client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
