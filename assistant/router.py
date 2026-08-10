from config import Config

from providers.groq import GroqProvider
from providers.gemini import GeminiProvider
from providers.nvidia import NvidiaProvider
from providers.openai import OpenAIProvider
from providers.mistral import MistralProvider


class Router:

    def __init__(self):

        self.providers = {

            "groq": GroqProvider(),

            "gemini": GeminiProvider(),

            "nvidia": NvidiaProvider(),

            "openai": OpenAIProvider(),

            "mistral": MistralProvider(),

        }

        self.current_provider = Config.DEFAULT_PROVIDER

    def set_provider(self, provider_name):

        if provider_name in self.providers:
            self.current_provider = provider_name
            return True

        return False

    def get_provider(self):
        return self.current_provider

    def chat(self, messages):

        last_exception = None

        for provider_name in self._provider_order():

            provider = self.providers[provider_name]

            try:

                print(f"Trying {provider_name}...")

                response = provider.chat(messages)

                self.current_provider = provider_name

                return response

            except Exception as e:

                print(f"{provider_name} failed: {e}")

                last_exception = e

        raise last_exception

    def stream(self, messages):

        last_exception = None

        for provider_name in self._provider_order():

            provider = self.providers[provider_name]

            try:

                print(f"Streaming with {provider_name}")

                if hasattr(provider, "stream_chat"):

                    for token in provider.stream_chat(messages):

                        yield token

                else:

                    response = provider.chat(messages)

                    yield response

                self.current_provider = provider_name

                return

            except Exception as e:

                print(f"{provider_name} failed: {e}")

                last_exception = e

        raise last_exception
    
    def _provider_order(self):

        order = [self.current_provider]

        for provider in Config.FALLBACK_ORDER:

            if provider not in order:

                order.append(provider)

        return order