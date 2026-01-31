from __future__ import annotations

from typing import Iterable, List

from assistant.models import Item


def format_capture_response(summary: str, items: List[Item]) -> str:
    counts = _count_items(items)
    lines = ["Captured: " + ", ".join(counts) if counts else "Captured."]
    if summary:
        lines.append(f"Summary: {summary}")
    for item in items[:5]:
        lines.append(_format_item_line(item))
    if len(items) > 5:
        lines.append(f"...and {len(items) - 5} more.")
    return "\n".join(lines)


def format_items(title: str, rows: Iterable[dict]) -> str:
    lines = [title]
    rows_list = list(rows)
    if not rows_list:
        lines.append("No items found.")
        return "\n".join(lines)
    for row in rows_list:
        lines.append(_format_row(row))
    return "\n".join(lines)


def format_questions(questions: List[str]) -> str:
    if not questions:
        return ""
    return "\n".join(questions)


def _count_items(items: List[Item]) -> List[str]:
    counts = {}
    for item in items:
        counts[item.type] = counts.get(item.type, 0) + 1
    order = ["task", "event", "note", "idea", "decision", "contact"]
    results = []
    for item_type in order:
        if item_type in counts:
            results.append(f"{counts[item_type]} {item_type}")
    return results


def _format_item_line(item: Item) -> str:
    pieces = [f"- {item.summary or item.text}"]
    meta = []
    if item.context:
        meta.append(item.context)
    if item.project:
        meta.append(f"project: {item.project}")
    if item.due_at:
        meta.append(f"due: {item.due_at}")
    if meta:
        pieces.append(f"({', '.join(meta)})")
    return " ".join(pieces)


def _format_row(row: dict) -> str:
    summary = row["summary"] or row["text"]
    meta = []
    if row["context"]:
        meta.append(row["context"])
    if row["project"]:
        meta.append(f"project: {row['project']}")
    if row["due_at"]:
        meta.append(f"due: {row['due_at']}")
    return f"- {summary} ({', '.join(meta)})" if meta else f"- {summary}"
