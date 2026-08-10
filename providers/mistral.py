from openai import OpenAI

from config import Config
from providers.base import BaseProvider


class MistralProvider(BaseProvider):

    def __init__(self):
        self.client = OpenAI(
            api_key=Config.MISTRAL_API_KEY,
            base_url="https://router.bynara.id/v1",
            timeout=60,
        )

    def chat(self, messages: list[dict]) -> str:
        response = self.client.chat.completions.create(
            model=Config.MISTRAL_MODEL,
            messages=messages,
        )
        return response.choices[0].message.content

    def stream_chat(self, messages: list[dict]):
        stream = self.client.chat.completions.create(
            model=Config.MISTRAL_MODEL,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
