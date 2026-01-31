import logging
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from assistant.config import load_config
from assistant.db import Database
from assistant.llm import LLMClient
from assistant.service import AssistantService
from assistant.telegram_bot import build_application


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    config = load_config()
    if not config.telegram_bot_token:
        print("Missing TELEGRAM_BOT_TOKEN", file=sys.stderr)
        return 1
    if not config.openai_api_key:
        print("Missing OPENAI_API_KEY", file=sys.stderr)
        return 1

    db = Database(config.db_path)
    llm = LLMClient(
        api_key=config.openai_api_key,
        model=config.openai_model,
        transcribe_model=config.openai_transcribe_model,
    )
    service = AssistantService(
        db=db, llm_client=llm, locales=config.locales, timezone_name=config.timezone
    )
    application = build_application(config.telegram_bot_token, service)
    application.run_polling()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
