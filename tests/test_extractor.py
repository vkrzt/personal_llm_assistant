from assistant.extractor import build_capture_result


def test_build_capture_result_parses_items_and_questions():
    raw = {
        "summary": "",
        "items": [
            {
                "type": "task",
                "text": "Call the window contractor tomorrow morning",
                "summary": "",
                "context": "home",
                "project": None,
                "priority": "high",
                "urgency": "high",
                "due_at": None,
                "people": ["contractor"],
            }
        ],
        "questions": [
            {
                "item_index": 0,
                "field": "priority",
                "question": "How urgent is this?",
                "options": ["low", "medium", "high"],
            }
        ],
    }
    result = build_capture_result(
        user_id="user-1",
        source="text",
        raw=raw,
        locales=["en"],
        timezone_name="UTC",
    )

    assert result.items
    assert result.items[0].type == "task"
    assert result.items[0].context == "home"
    assert result.items[0].due_at is not None
    assert result.clarifications
    assert result.summary
