import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str
    openai_api_key: str
    openai_model: str
    openai_transcribe_model: str
    db_path: str
    timezone: str
    locales: List[str]


def load_config() -> Config:
    load_dotenv()
    locales = os.getenv("LOCALES", "en").split(",")
    locales = [loc.strip() for loc in locales if loc.strip()]
    return Config(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        openai_transcribe_model=os.getenv("OPENAI_TRANSCRIBE_MODEL", "whisper-1"),
        db_path=os.getenv("DB_PATH", "./assistant.db"),
        timezone=os.getenv("TIMEZONE", "UTC"),
        locales=locales or ["en"],
    )
