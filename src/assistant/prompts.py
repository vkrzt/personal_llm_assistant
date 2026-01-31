SYSTEM_PROMPT = (
    "You are a personal assistant that extracts structured information from "
    "user messages. Return JSON only. Do not include Markdown."
)

USER_PROMPT_TEMPLATE = """\
Extract structured items from the message. Use the schema below and output JSON:

Schema:
{{
  "summary": string,
  "items": [
    {{
      "type": "task" | "event" | "note" | "idea" | "decision" | "contact",
      "text": string,
      "summary": string,
      "context": "work" | "personal" | "home" | "health" | "project" | "other",
      "project": string | null,
      "priority": "low" | "medium" | "high" | "critical" | null,
      "urgency": "low" | "medium" | "high" | null,
      "due_at": string | null,
      "people": [string]
    }}
  ],
  "questions": [
    {{
      "item_index": number,
      "field": "context" | "priority" | "urgency" | "due_at" | "project",
      "question": string,
      "options": [string]
    }}
  ]
}}

Rules:
- Identify multiple items if present.
- Use short summaries.
- Leave unknown values as null.
- If unsure about context/priority/urgency/due date/project, add a question.
- questions.item_index refers to the index in items.
- due_at should be an ISO 8601 string when known; otherwise null.

Message:
{message}
"""
