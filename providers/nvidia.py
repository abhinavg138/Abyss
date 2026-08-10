import json

from openai import OpenAI

from config import Config
from providers.base import BaseProvider


class NvidiaProvider(BaseProvider):

    def __init__(self):
        self.client = OpenAI(
            api_key=Config.NVIDIA_API_KEY,
            base_url="https://integrate.api.nvidia.com/v1",
            timeout=60,
        )

    def _prepare_messages(self, messages: list[dict]) -> list[dict]:
        prepared = []
        for message in messages:
            clean_message = message.copy()
            if (
                prepared
                and prepared[-1].get("role") == clean_message.get("role")
                and isinstance(prepared[-1].get("content"), str)
                and isinstance(clean_message.get("content"), str)
            ):
                prepared[-1]["content"] = (
                    prepared[-1]["content"].rstrip()
                    + "\n\n"
                    + clean_message["content"].lstrip()
                )
            else:
                prepared.append(clean_message)
        return prepared

    def chat(self, messages: list[dict]) -> str:
        payload = {
            "model": Config.NVIDIA_MODEL,
            "messages": self._prepare_messages(messages),
        }
        print("[NVIDIA] request payload:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))

        response = self.client.chat.completions.create(
            **payload,
        )
        text = response.choices[0].message.content
        print("[NVIDIA] final assistant text:")
        print(text)
        return text

    def stream_chat(self, messages: list[dict]):
        payload = {
            "model": Config.NVIDIA_MODEL,
            "messages": self._prepare_messages(messages),
            "stream": True,
        }
        print("[NVIDIA] request payload:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))

        stream = self.client.chat.completions.create(
            **payload,
        )
        full_response = ""
        try:
            for chunk in stream:
                raw_chunk = (
                    chunk.model_dump_json()
                    if hasattr(chunk, "model_dump_json")
                    else repr(chunk)
                )
                print("[NVIDIA] raw stream chunk:")
                print(raw_chunk)

                if chunk.choices:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        full_response += delta
                        yield delta
        finally:
            print("[NVIDIA] final assistant text:")
            print(full_response)
