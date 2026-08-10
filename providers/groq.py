from groq import Groq

from config import Config
from providers.base import BaseProvider


class GroqProvider(BaseProvider):

    def __init__(self):
        self.client = Groq(api_key=Config.GROQ_API_KEY)

    def chat(self, messages: list[dict]) -> str:
        response = self.client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=messages,
        )
        return response.choices[0].message.content

    def stream_chat(self, messages: list[dict]):
        stream = self.client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
