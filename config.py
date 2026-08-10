from dotenv import load_dotenv
import os

# Load variables from .env
load_dotenv()

class Config:
    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

    # Default AI Provider
    DEFAULT_PROVIDER = "mistral"

    # Default Model Names
    GROQ_MODEL = "llama-3.3-70b-versatile"
    GEMINI_MODEL = "gemini-2.5-flash"
    OPENAI_MODEL = "gpt-5"
    NVIDIA_MODEL = "moonshotai/kimi-k2.6"
    MISTRAL_MODEL = "mimo-v2.5-pro-free"
    OPENROUTER_MODEL = "openai/gpt-4o-mini"

    FALLBACK_ORDER = [
        "mistral",
        "nvidia",
        "groq",
        "gemini",
    ]