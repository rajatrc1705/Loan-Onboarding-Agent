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
AGENT_SERVICE_URL = get_env("AGENT_SERVICE_URL")
EMAIL_FROM = get_env("EMAIL_FROM")
RESEND_API_KEY = get_env("RESEND_API_KEY")
