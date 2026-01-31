from __future__ import annotations

import uuid
from typing import List, Optional

from assistant.clarifications import apply_clarification_answer
from assistant.db import Database
from assistant.extractor import build_capture_result
from assistant.models import CaptureResult, Clarification, Item
from assistant.planning import day_range_iso, week_range_iso
from assistant.utils import utc_now_iso


class AssistantService:
    def __init__(
        self, db: Database, llm_client, locales: List[str], timezone_name: str
    ) -> None:
        self._db = db
        self._llm = llm_client
        self._locales = locales
        self._timezone = timezone_name

    def capture(self, user_id: str, message: str, source: str) -> CaptureResult:
        try:
            raw = self._llm.extract(message)
        except Exception:  # noqa: BLE001
            raw = {"summary": "", "items": [], "questions": []}
        result = build_capture_result(
            user_id=user_id,
            source=source,
            raw=raw,
            locales=self._locales,
            timezone_name=self._timezone,
        )
        if not result.items:
            result = CaptureResult(
                summary=message.strip()[:140],
                items=[
                    Item(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        type="note",
                        text=message.strip(),
                        summary=message.strip()[:140],
                        context="other",
                        project=None,
                        priority=None,
                        urgency=None,
                        due_at=None,
                        created_at=utc_now_iso(),
                        source=source,
                        references=[],
                        raw_json={"fallback": True},
                    )
                ],
                clarifications=[],
            )

        self._db.add_items(result.items)
        if result.clarifications:
            self._db.add_clarifications(result.clarifications)
        return result

    def transcribe_voice(self, file_path: str) -> str:
        return self._llm.transcribe(file_path)

    def list_tasks(self, user_id: str, context: Optional[str] = None):
        return self._db.list_tasks(user_id, context=context)

    def search(self, user_id: str, query: str):
        return self._db.search_items(user_id, query)

    def plan_today(self, user_id: str):
        start, end = day_range_iso(self._timezone)
        return self._db.items_due_between(user_id, start, end)

    def plan_week(self, user_id: str):
        start, end = week_range_iso(self._timezone)
        return self._db.items_due_between(user_id, start, end)

    def pending_clarifications(self, user_id: str) -> List[Clarification]:
        return self._db.get_pending_clarifications(user_id)

    def answer_clarification(
        self, clarification: Clarification, answer: str
    ) -> tuple[bool, str]:
        return apply_clarification_answer(
            db=self._db,
            clarification=clarification,
            answer=answer,
            locales=self._locales,
            timezone_name=self._timezone,
        )
