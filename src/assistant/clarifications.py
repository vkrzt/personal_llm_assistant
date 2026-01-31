from __future__ import annotations

from typing import Iterable, Optional, Tuple

from assistant.db import Database
from assistant.extractor import ALLOWED_CONTEXTS, ALLOWED_PRIORITY, ALLOWED_URGENCY
from assistant.models import Clarification
from assistant.utils import parse_datetime, utc_now_iso


def apply_clarification_answer(
    db: Database,
    clarification: Clarification,
    answer: str,
    locales: Iterable[str],
    timezone_name: str,
) -> Tuple[bool, str]:
    normalized = _normalize_answer(
        clarification.field, answer, locales=locales, timezone_name=timezone_name
    )
    if normalized is None:
        return False, f"Could not parse answer for {clarification.field}."

    db.update_item_field(clarification.item_id, clarification.field, normalized)
    db.resolve_clarification(clarification.id, answer, utc_now_iso())
    return True, f"Updated {clarification.field}: {normalized}"


def _normalize_answer(
    field: str,
    answer: str,
    locales: Iterable[str],
    timezone_name: str,
) -> Optional[str]:
    answer = answer.strip()
    if not answer:
        return None
    if field == "context":
        normalized = answer.lower()
        return normalized if normalized in ALLOWED_CONTEXTS else "other"
    if field == "priority":
        normalized = answer.lower()
        return normalized if normalized in ALLOWED_PRIORITY else None
    if field == "urgency":
        normalized = answer.lower()
        return normalized if normalized in ALLOWED_URGENCY else None
    if field == "due_at":
        return parse_datetime(answer, locales, timezone_name)
    if field == "project":
        return answer
    return None
