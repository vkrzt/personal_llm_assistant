from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Iterable, Optional

import dateparser
from dateparser.search import search_dates

LOGGER = logging.getLogger(__name__)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_datetime(
    text: str, locales: Iterable[str], timezone_name: str
) -> Optional[str]:
    if not text:
        return None
    try:
        dt = dateparser.parse(
            text,
            languages=list(locales),
            settings={
                "RETURN_AS_TIMEZONE_AWARE": True,
                "TIMEZONE": timezone_name,
                "PREFER_DATES_FROM": "future",
            },
        )
    except (ValueError, TypeError):
        dt = None
    if dt is None:
        try:
            results = search_dates(
                text,
                languages=list(locales),
                settings={
                    "RETURN_AS_TIMEZONE_AWARE": True,
                    "TIMEZONE": timezone_name,
                    "PREFER_DATES_FROM": "future",
                },
            )
            if results:
                dt = results[0][1]
        except (ValueError, TypeError):
            dt = None
    if dt is None:
        return None
    return dt.isoformat()


def safe_json_dumps(payload: Any) -> str:
    try:
        return json.dumps(payload, ensure_ascii=True)
    except TypeError:
        LOGGER.warning("Failed to JSON serialize payload")
        return "{}"


def safe_json_loads(payload: str) -> Any:
    if not payload:
        return {}
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        LOGGER.warning("Failed to JSON parse payload")
        return {}
