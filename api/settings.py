import os

from dotenv import load_dotenv

load_dotenv(".env.local")


def get_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


DATABASE_URL = get_env("DATABASE_URL", "sqlite:///./local.db")
LIVEKIT_URL = get_env("LIVEKIT_URL")
LIVEKIT_API_KEY = get_env("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = get_env("LIVEKIT_API_SECRET")
EMAIL_FROM = get_env("EMAIL_FROM")
RESEND_API_KEY = get_env("RESEND_API_KEY")
MAGIC_LINK_BASE_URL = get_env("MAGIC_LINK_BASE_URL", "http://localhost:3000")
N8N_EMAIL_WEBHOOK_URL = get_env("N8N_EMAIL_WEBHOOK_URL")
OPENAI_EVALUATOR_MODEL = get_env("OPENAI_EVALUATOR_MODEL", "gpt-4o-mini")
OPENAI_SUMMARY_MODEL = get_env("OPENAI_SUMMARY_MODEL", "gpt-4o-mini")
LLM_REQUEST_TIMEOUT_SECONDS = float(get_env("LLM_REQUEST_TIMEOUT_SECONDS", "12"))
