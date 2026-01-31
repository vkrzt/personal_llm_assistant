import tempfile

from assistant.clarifications import apply_clarification_answer
from assistant.db import Database
from assistant.models import Clarification, Item
from assistant.utils import utc_now_iso


def test_apply_clarification_updates_item():
    with tempfile.NamedTemporaryFile() as tmp:
        db = Database(tmp.name)
        item = Item(
            id="item-1",
            user_id="user-1",
            type="task",
            text="Call builder",
            summary="Call builder",
            context="home",
            project=None,
            priority=None,
            urgency=None,
            due_at=None,
            created_at=utc_now_iso(),
            source="text",
            references=[],
            status="open",
            raw_json={},
        )
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
        ok, _ = apply_clarification_answer(
            db,
            clar,
            "high",
            locales=["en"],
            timezone_name="UTC",
        )
        assert ok
        updated = db.fetch_item("item-1")
        assert updated["priority"] == "high"
