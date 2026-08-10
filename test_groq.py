from providers.groq import GroqProvider

provider = GroqProvider()

messages = [
    {
        "role": "user",
        "content": "Say hello in one sentence."
    }
]

response = provider.chat(messages)

print(response)