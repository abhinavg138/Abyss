from abc import ABC, abstractmethod


class BaseProvider(ABC):
    supports_vision = False

    @abstractmethod
    def chat(self, messages: list[dict]) -> str:
        """Send messages and return full response string."""
        pass

    def stream_chat(self, messages: list[dict]):
        """
        Yield response tokens one at a time.
        Default fallback: call chat() and yield the whole response at once.
        Providers should override this with real streaming.
        """
        yield self.chat(messages)
