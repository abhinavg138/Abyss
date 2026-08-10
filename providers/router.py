from config import Config

from providers.groq import GroqProvider
from providers.gemini import GeminiProvider
from providers.nvidia import NvidiaProvider
from providers.openai import OpenAIProvider
from providers.mistral import MistralProvider
from providers.openrouter import OpenRouterProvider


class Router:

    def __init__(self):
        self.providers = {
            "groq":       GroqProvider(),
            "gemini":     GeminiProvider(),
            "nvidia":     NvidiaProvider(),
            "openai":     OpenAIProvider(),
            "mistral":    MistralProvider(),
            "openrouter": OpenRouterProvider(),
        }
        self.current_provider = Config.DEFAULT_PROVIDER

    def set_provider(self, name: str) -> bool:
        if name in self.providers:
            self.current_provider = name
            return True
        return False

    def get_provider(self) -> str:
        return self.current_provider

    def _provider_order(self, requires_vision: bool = False) -> list[str]:
        order = []
        # Check current provider
        if not requires_vision or self.providers[self.current_provider].supports_vision:
            order.append(self.current_provider)

        # Check fallback order
        for p in Config.FALLBACK_ORDER:
            if p not in order:
                if not requires_vision or self.providers[p].supports_vision:
                    order.append(p)

        # Append any provider that supports vision if requires_vision and order is empty
        if requires_vision and not order:
            for name, provider in self.providers.items():
                if provider.supports_vision:
                    order.append(name)

        # Fallback to general order if no vision providers are found (safety fallback)
        if not order:
            order.append(self.current_provider)
            for p in Config.FALLBACK_ORDER:
                if p not in order:
                    order.append(p)

        return order

    # ── Non-streaming ─────────────────────────────────────────────
    def chat(self, messages: list[dict]) -> str:
        requires_vision = False
        for msg in messages:
            if isinstance(msg.get("content"), list):
                requires_vision = True
                break

        last_exc = None
        for name in self._provider_order(requires_vision=requires_vision):
            try:
                print(f"[Router] chat → {name} (vision: {requires_vision})")
                result = self.providers[name].chat(messages)
                self.current_provider = name
                return result
            except Exception as e:
                print(f"[Router] {name} failed: {e}")
                last_exc = e
        raise last_exc

    # ── Streaming ─────────────────────────────────────────────────
    def stream(self, messages: list[dict]):
        requires_vision = False
        for msg in messages:
            if isinstance(msg.get("content"), list):
                requires_vision = True
                break

        last_exc = None
        for name in self._provider_order(requires_vision=requires_vision):
            try:
                print(f"[Router] stream → {name} (vision: {requires_vision})")
                for token in self.providers[name].stream_chat(messages):
                    yield token
                self.current_provider = name
                return   # success — don't fall through to next provider
            except Exception as e:
                print(f"[Router] {name} stream failed: {e}")
                last_exc = e
        raise last_exc
