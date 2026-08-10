from providers.gemini import GeminiProvider

provider = GeminiProvider()

messages = [
    {
        "role": "user",
        "content": "Say hello in one sentence."
    }
]

response = provider.chat(messages)

print(response)