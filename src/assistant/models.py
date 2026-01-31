from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Item:
    id: str
    user_id: str
    type: str
    text: str
    summary: str
    context: str
    project: Optional[str]
    priority: Optional[str]
    urgency: Optional[str]
    due_at: Optional[str]
    created_at: str
    source: str
    references: List[str] = field(default_factory=list)
    status: str = "open"
    raw_json: Optional[dict] = None


@dataclass
class Clarification:
    id: str
    user_id: str
    item_id: str
    field: str
    question: str
    options: List[str]
    status: str
    created_at: str


@dataclass
class CaptureResult:
    summary: str
    items: List[Item]
    clarifications: List[Clarification]
