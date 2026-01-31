import tempfile

from assistant.db import Database
from assistant.models import Clarification, Item
from assistant.utils import utc_now_iso


def _sample_item(item_id: str, user_id: str, summary: str, due_at: str | None):
    return Item(
        id=item_id,
        user_id=user_id,
        type="task",
        text=summary,
        summary=summary,
        context="home",
        project=None,
        priority="high",
        urgency="high",
        due_at=due_at,
        created_at=utc_now_iso(),
        source="text",
        references=["builder"],
        status="open",
        raw_json={"type": "task"},
    )


def test_db_insert_and_search():
    with tempfile.NamedTemporaryFile() as tmp:
        db = Database(tmp.name)
        item = _sample_item("item-1", "user-1", "Call the builder", None)
        db.add_items([item])
        rows = db.search_items("user-1", "builder")
        assert len(rows) == 1
        assert rows[0]["summary"] == "Call the builder"


def test_db_clarifications_roundtrip():
    with tempfile.NamedTemporaryFile() as tmp:
        db = Database(tmp.name)
        item = _sample_item("item-1", "user-1", "Fix window", None)
        db.add_items([item])
        clar = Clarification(
            id="clar-1",
            user_id="user-1",
            item_id="item-1",
            field="priority",
            question="Priority?",
            options=["low", "high"],
            status="open",
            created_at=utc_now_iso(),
        )
        db.add_clarifications([clar])
        pending = db.get_pending_clarifications("user-1")
        assert len(pending) == 1
        assert pending[0].field == "priority"
