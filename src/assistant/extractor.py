from __future__ import annotations

import uuid
from typing import Any, Dict, Iterable, List, Optional, Tuple

from assistant.models import CaptureResult, Clarification, Item
from assistant.utils import parse_datetime, utc_now_iso

ALLOWED_TYPES = {"task", "event", "note", "idea", "decision", "contact"}
ALLOWED_CONTEXTS = {"work", "personal", "home", "health", "project", "other"}
ALLOWED_PRIORITY = {"low", "medium", "high", "critical"}
ALLOWED_URGENCY = {"low", "medium", "high"}


def build_capture_result(
    user_id: str,
    source: str,
    raw: Dict[str, Any],
    locales: Iterable[str],
    timezone_name: str,
) -> CaptureResult:
    summary = str(raw.get("summary") or "").strip()
    items_raw = raw.get("items") or []
    questions_raw = raw.get("questions") or []

    items: List[Item] = []
    now_iso = utc_now_iso()

    for item_raw in items_raw:
        item = _normalize_item(
            user_id=user_id,
            source=source,
            item_raw=item_raw,
            locales=locales,
            timezone_name=timezone_name,
            created_at=now_iso,
        )
        items.append(item)

    clarifications = _build_clarifications(
        user_id=user_id,
        items=items,
        questions_raw=questions_raw,
        created_at=now_iso,
    )

    if not summary:
        summary = _build_summary(items)

    return CaptureResult(summary=summary, items=items, clarifications=clarifications)


def _normalize_item(
    user_id: str,
    source: str,
    item_raw: Dict[str, Any],
    locales: Iterable[str],
    timezone_name: str,
    created_at: str,
) -> Item:
    item_type = _normalize_choice(item_raw.get("type"), ALLOWED_TYPES, "note")
    text = str(item_raw.get("text") or "").strip()
    summary = str(item_raw.get("summary") or "").strip() or text
    context = _normalize_choice(item_raw.get("context"), ALLOWED_CONTEXTS, "other")
    project = _normalize_optional_text(item_raw.get("project"))
    priority = _normalize_choice(item_raw.get("priority"), ALLOWED_PRIORITY, None)
    urgency = _normalize_choice(item_raw.get("urgency"), ALLOWED_URGENCY, None)

    due_at = _normalize_due_at(
        item_raw.get("due_at"), text, locales=locales, timezone_name=timezone_name
    )

    references = _normalize_references(item_raw.get("people"))

    return Item(
        id=str(uuid.uuid4()),
        user_id=user_id,
        type=item_type,
        text=text,
        summary=summary,
        context=context,
        project=project,
        priority=priority,
        urgency=urgency,
        due_at=due_at,
        created_at=created_at,
        source=source,
        references=references,
        raw_json=item_raw,
    )


def _normalize_due_at(
    due_value: Optional[str],
    fallback_text: str,
    locales: Iterable[str],
    timezone_name: str,
) -> Optional[str]:
    if due_value:
        parsed = parse_datetime(str(due_value), locales, timezone_name)
        if parsed:
            return parsed
    if fallback_text:
        return parse_datetime(fallback_text, locales, timezone_name)
    return None


def _normalize_choice(
    value: Optional[str], allowed: set, default: Optional[str]
) -> Optional[str]:
    if not value:
        return default
    value_str = str(value).strip().lower()
    if value_str in allowed:
        return value_str
    return default


def _normalize_optional_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    value_str = str(value).strip()
    return value_str if value_str else None


def _normalize_references(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _build_clarifications(
    user_id: str,
    items: List[Item],
    questions_raw: Iterable[Dict[str, Any]],
    created_at: str,
) -> List[Clarification]:
    clarifications: List[Clarification] = []
    for question in questions_raw:
        item_index = question.get("item_index")
        if item_index is None:
            continue
        try:
            item = items[int(item_index)]
        except (ValueError, IndexError, TypeError):
            continue
        field = str(question.get("field") or "").strip()
        if not field:
            continue
        text = str(question.get("question") or "").strip()
        if not text:
            continue
        options = question.get("options") or []
        if not isinstance(options, list):
            options = []
        option_values = [str(opt).strip() for opt in options if str(opt).strip()]
        clarifications.append(
            Clarification(
                id=str(uuid.uuid4()),
                user_id=user_id,
                item_id=item.id,
                field=field,
                question=text,
                options=option_values,
                status="open",
                created_at=created_at,
            )
        )
    return clarifications


def _build_summary(items: List[Item]) -> str:
    if not items:
        return ""
    summaries = [item.summary for item in items if item.summary]
    if not summaries:
        return ""
    if len(summaries) == 1:
        return summaries[0]
    return "; ".join(summaries[:3])
