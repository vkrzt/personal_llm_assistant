import tempfile

from assistant.db import Database
from assistant.service import AssistantService


class FakeLLM:
    def __init__(self, payload):
        self._payload = payload

    def extract(self, message: str):
        return self._payload

    def transcribe(self, file_path: str) -> str:
        return "transcript"


def test_capture_fallback_creates_note():
    with tempfile.NamedTemporaryFile() as tmp:
        db = Database(tmp.name)
        llm = FakeLLM({"summary": "", "items": [], "questions": []})
        service = AssistantService(
            db=db, llm_client=llm, locales=["en"], timezone_name="UTC"
        )
        result = service.capture("user-1", "Just a thought", "text")
        assert len(result.items) == 1
        rows = db.search_items("user-1", "Just a thought")
        assert rows


def test_capture_uses_llm_items():
    with tempfile.NamedTemporaryFile() as tmp:
        db = Database(tmp.name)
        llm = FakeLLM(
            {
                "summary": "Call builder",
                "items": [
                    {
                        "type": "task",
                        "text": "Call builder tomorrow",
                        "summary": "Call builder",
                        "context": "home",
                        "project": None,
                        "priority": "high",
                        "urgency": "high",
                        "due_at": None,
                        "people": [],
                    }
                ],
                "questions": [],
            }
        )
        service = AssistantService(
            db=db, llm_client=llm, locales=["en"], timezone_name="UTC"
        )
        result = service.capture("user-1", "Call builder tomorrow", "text")
        assert result.items[0].type == "task"
        rows = db.list_tasks("user-1")
        assert len(rows) == 1
