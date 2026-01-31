from __future__ import annotations

import sqlite3
from typing import Iterable, List, Optional

from assistant.models import Clarification, Item
from assistant.utils import safe_json_dumps, safe_json_loads


class Database:
    def __init__(self, path: str) -> None:
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self.ensure_schema()

    def ensure_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                text TEXT,
                summary TEXT,
                context TEXT,
                project TEXT,
                priority TEXT,
                urgency TEXT,
                due_at TEXT,
                created_at TEXT,
                source TEXT,
                references TEXT,
                status TEXT,
                raw_json TEXT
            );
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS clarifications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                field TEXT NOT NULL,
                question TEXT NOT NULL,
                options TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                resolved_at TEXT,
                answer TEXT
            );
            """
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_items_user ON items(user_id);"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_items_due ON items(due_at);"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_items_type ON items(type);"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_clarifications_user ON clarifications(user_id);"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_clarifications_status ON clarifications(status);"
        )
        self._conn.commit()

    def add_items(self, items: Iterable[Item]) -> None:
        payload = [
            (
                item.id,
                item.user_id,
                item.type,
                item.text,
                item.summary,
                item.context,
                item.project,
                item.priority,
                item.urgency,
                item.due_at,
                item.created_at,
                item.source,
                safe_json_dumps(item.references),
                item.status,
                safe_json_dumps(item.raw_json or {}),
            )
            for item in items
        ]
        self._conn.executemany(
            """
            INSERT INTO items (
                id, user_id, type, text, summary, context, project,
                priority, urgency, due_at, created_at, source,
                references, status, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            payload,
        )
        self._conn.commit()

    def add_clarifications(self, clarifications: Iterable[Clarification]) -> None:
        payload = [
            (
                clar.id,
                clar.user_id,
                clar.item_id,
                clar.field,
                clar.question,
                safe_json_dumps(clar.options),
                clar.status,
                clar.created_at,
                None,
                None,
            )
            for clar in clarifications
        ]
        if not payload:
            return
        self._conn.executemany(
            """
            INSERT INTO clarifications (
                id, user_id, item_id, field, question, options, status,
                created_at, resolved_at, answer
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            payload,
        )
        self._conn.commit()

    def get_pending_clarifications(self, user_id: str) -> List[Clarification]:
        cursor = self._conn.execute(
            """
            SELECT * FROM clarifications
            WHERE user_id = ? AND status = 'open'
            ORDER BY created_at ASC;
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        return [
            Clarification(
                id=row["id"],
                user_id=row["user_id"],
                item_id=row["item_id"],
                field=row["field"],
                question=row["question"],
                options=safe_json_loads(row["options"]) or [],
                status=row["status"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def resolve_clarification(
        self, clarification_id: str, answer: str, resolved_at: str
    ) -> None:
        self._conn.execute(
            """
            UPDATE clarifications
            SET status = 'resolved', resolved_at = ?, answer = ?
            WHERE id = ?;
            """,
            (resolved_at, answer, clarification_id),
        )
        self._conn.commit()

    def update_item_field(self, item_id: str, field: str, value: Optional[str]) -> None:
        if field not in {"context", "priority", "urgency", "due_at", "project", "status"}:
            raise ValueError("Unsupported field update")
        self._conn.execute(
            f"UPDATE items SET {field} = ? WHERE id = ?;",
            (value, item_id),
        )
        self._conn.commit()

    def fetch_item(self, item_id: str) -> Optional[sqlite3.Row]:
        cursor = self._conn.execute(
            "SELECT * FROM items WHERE id = ?;", (item_id,)
        )
        return cursor.fetchone()

    def search_items(self, user_id: str, query: str, limit: int = 20) -> List[sqlite3.Row]:
        like = f"%{query}%"
        cursor = self._conn.execute(
            """
            SELECT * FROM items
            WHERE user_id = ?
              AND (summary LIKE ? OR text LIKE ? OR project LIKE ?)
            ORDER BY created_at DESC
            LIMIT ?;
            """,
            (user_id, like, like, like, limit),
        )
        return cursor.fetchall()

    def list_tasks(self, user_id: str, context: Optional[str] = None) -> List[sqlite3.Row]:
        if context:
            cursor = self._conn.execute(
                """
                SELECT * FROM items
                WHERE user_id = ? AND type = 'task' AND status = 'open'
                  AND context = ?
                ORDER BY due_at IS NULL, due_at ASC, created_at DESC;
                """,
                (user_id, context),
            )
        else:
            cursor = self._conn.execute(
                """
                SELECT * FROM items
                WHERE user_id = ? AND type = 'task' AND status = 'open'
                ORDER BY due_at IS NULL, due_at ASC, created_at DESC;
                """,
                (user_id,),
            )
        return cursor.fetchall()

    def items_due_between(
        self, user_id: str, start_iso: str, end_iso: str
    ) -> List[sqlite3.Row]:
        cursor = self._conn.execute(
            """
            SELECT * FROM items
            WHERE user_id = ?
              AND due_at IS NOT NULL
              AND due_at >= ?
              AND due_at <= ?
            ORDER BY due_at ASC;
            """,
            (user_id, start_iso, end_iso),
        )
        return cursor.fetchall()

    def close(self) -> None:
        self._conn.close()
