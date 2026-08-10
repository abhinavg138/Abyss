from config import Config

print("Groq Key Found:", Config.GROQ_API_KEY is not None)
print("Gemini Key Found:", Config.GEMINI_API_KEY is not None)

print("Default Provider:", Config.DEFAULT_PROVIDER)
print("Groq Model:", Config.GROQ_MODEL)
print("Gemini Model:", Config.GEMINI_MODEL)