from openai import OpenAI

from config import Config
from providers.base import BaseProvider


class OpenRouterProvider(BaseProvider):
    """
    OpenRouter exposes an OpenAI-compatible API, so streaming
    works exactly the same way as the other OpenAI-style providers.
    """
    supports_vision = True

    def __init__(self):
        self.client = OpenAI(
            api_key=Config.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            timeout=60,
        )
        self.model = Config.OPENROUTER_MODEL

    def chat(self, messages: list[dict]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content

    def stream_chat(self, messages: list[dict]):
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
