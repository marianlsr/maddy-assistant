from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator


class MemoryStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._init_db()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Commit or rollback each operation and always release the SQLite file.

        ``with sqlite3.connect(...)`` handles transactions but does not close the
        connection on exit. On Windows that can lock a temporary database file.
        """
        conn = sqlite3.connect(self.path)
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS message_details (
                    message_id INTEGER PRIMARY KEY REFERENCES messages(id),
                    reply_to INTEGER,
                    receipt TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL UNIQUE,
                    value TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    remind_at TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    message TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    source TEXT NOT NULL,
                    payload TEXT NOT NULL DEFAULT '{}',
                    dedupe_key TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    delivered_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_events_pending
                ON events(status, created_at)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS timers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    label TEXT NOT NULL,
                    due_at TEXT NOT NULL,
                    kind TEXT NOT NULL DEFAULT 'timer',
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    finished_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS contextual_reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    conditions TEXT NOT NULL DEFAULT '{}',
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    triggered_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runtime_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS automations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    trigger_type TEXT NOT NULL,
                    trigger_config TEXT NOT NULL DEFAULT '{}',
                    conditions TEXT NOT NULL DEFAULT '{}',
                    actions TEXT NOT NULL DEFAULT '[]',
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tool_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT NOT NULL,
                    arguments TEXT NOT NULL DEFAULT '{}',
                    result TEXT NOT NULL DEFAULT '{}',
                    risk_level TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    record_key TEXT,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    confidence REAL NOT NULL DEFAULT 1.0,
                    explicitness TEXT NOT NULL DEFAULT 'explicit',
                    scope TEXT NOT NULL DEFAULT 'personal',
                    expires_at TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memory_records_kind
                ON memory_records(kind, created_at)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    entities TEXT NOT NULL DEFAULT '[]',
                    significance REAL NOT NULL DEFAULT 0.5,
                    provenance TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_type TEXT NOT NULL,
                    input_facts TEXT NOT NULL DEFAULT '[]',
                    scores TEXT NOT NULL DEFAULT '{}',
                    outcome TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS work_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    objective TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    plan TEXT NOT NULL DEFAULT '[]',
                    current_step INTEGER NOT NULL DEFAULT 0,
                    result TEXT,
                    authorized_scope TEXT NOT NULL DEFAULT 'user-authorized',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    trigger_phrase TEXT NOT NULL,
                    actions TEXT NOT NULL DEFAULT '[]',
                    status TEXT NOT NULL DEFAULT 'draft',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS study_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    topic TEXT,
                    duration_minutes INTEGER NOT NULL DEFAULT 0,
                    score REAL,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS calendar_events (
                    external_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    starts_at TEXT NOT NULL,
                    ends_at TEXT,
                    location TEXT,
                    source TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def add_message(
        self, role: str, content: str, *, reply_to: int | None = None, receipt: dict | None = None,
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute("INSERT INTO messages (role, content) VALUES (?, ?)", (role, content))
            message_id = int(cursor.lastrowid)
            if reply_to is not None or receipt is not None:
                conn.execute(
                    "INSERT INTO message_details (message_id, reply_to, receipt) VALUES (?, ?, ?)",
                    (message_id, reply_to, json.dumps(receipt) if receipt else None),
                )
        return message_id

    def message_history(self, limit: int = 40, before: int | None = None) -> dict:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("El limite debe estar entre 1 y 100")
        if before is not None and (isinstance(before, bool) or not isinstance(before, int) or before < 1):
            raise ValueError("Cursor no valido")
        where = "AND m.id < ?" if before is not None else ""
        params = (before, limit + 1) if before is not None else (limit + 1,)
        with self._connect() as conn:
            rows = conn.execute(
                f"""SELECT m.id, m.role, m.content, m.created_at, d.reply_to, d.receipt
                FROM messages m LEFT JOIN message_details d ON d.message_id = m.id
                WHERE m.role IN ('user', 'assistant') AND length(trim(m.content)) > 0 {where}
                ORDER BY m.id DESC LIMIT ?""",
                params,
            ).fetchall()
        has_more = len(rows) > limit
        messages = []
        for row in reversed(rows[:limit]):
            timestamp = datetime.fromisoformat(row[3])
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=UTC)
            messages.append({
                "id": row[0], "role": row[1], "content": row[2],
                "created_at": timestamp.astimezone(UTC).isoformat(),
                "reply_to": row[4], "receipt": json.loads(row[5]) if row[5] else None,
            })
        return {
            "messages": messages,
            "has_more": has_more,
            "next_before": messages[0]["id"] if messages and has_more else None,
        }

    def recent_messages(self, limit: int = 10) -> list[tuple[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return list(reversed(rows))

    def set_fact(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO facts (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
                """,
                (key, value),
            )

    def get_fact(self, key: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM facts WHERE key = ?", (key,)).fetchone()
        return row[0] if row else None

    def all_facts(self) -> dict[str, str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT key, value FROM facts ORDER BY key").fetchall()
        return {key: value for key, value in rows}

    def add_reminder(self, text: str, remind_at: str | None = None) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO reminders (text, remind_at) VALUES (?, ?)",
                (text, remind_at),
            )
            return int(cursor.lastrowid)

    def list_reminders(self, status: str = "pending") -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, text, remind_at, status, created_at
                FROM reminders
                WHERE status = ?
                ORDER BY id DESC
                """,
                (status,),
            ).fetchall()
        return [
            {
                "id": row[0],
                "text": row[1],
                "remind_at": row[2],
                "status": row[3],
                "created_at": row[4],
            }
            for row in rows
        ]

    def update_reminder(self, reminder_id: int, changes: dict) -> dict | None:
        allowed = {key: value for key, value in changes.items()
                   if key in {"text", "remind_at", "status"}}
        if "status" in allowed and allowed["status"] not in {"pending", "completed"}:
            raise ValueError("Estado de recordatorio no valido")
        with self._connect() as conn:
            if allowed:
                assignments = ", ".join(f"{key} = ?" for key in allowed)
                conn.execute(
                    f"UPDATE reminders SET {assignments} WHERE id = ?",
                    (*allowed.values(), reminder_id),
                )
            row = conn.execute(
                "SELECT id, text, remind_at, status, created_at FROM reminders WHERE id = ?",
                (reminder_id,),
            ).fetchone()
        if not row:
            return None
        return dict(zip(("id", "text", "remind_at", "status", "created_at"), row))

    def add_notification(
        self,
        channel: str,
        recipient: str,
        message: str,
        status: str,
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO notifications (channel, recipient, message, status)
                VALUES (?, ?, ?, ?)
                """,
                (channel, recipient, message, status),
            )
            return int(cursor.lastrowid)

    def list_notifications(self, limit: int = 20) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, channel, recipient, message, status, created_at
                FROM notifications
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "id": row[0],
                "channel": row[1],
                "recipient": row[2],
                "message": row[3],
                "status": row[4],
                "created_at": row[5],
            }
            for row in rows
        ]

    def add_event(
        self,
        event_type: str,
        priority: str,
        source: str,
        payload: dict[str, Any],
        dedupe_key: str | None = None,
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO events (event_type, priority, source, payload, dedupe_key)
                VALUES (?, ?, ?, ?, ?)
                """,
                (event_type, priority, source, json.dumps(payload), dedupe_key),
            )
            conn.execute(
                """
                DELETE FROM events
                WHERE status = 'delivered' AND id NOT IN
                    (SELECT id FROM events ORDER BY id DESC LIMIT 5000)
                """
            )
            return int(cursor.lastrowid)

    def recent_event_for_key(self, dedupe_key: str, since: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, event_type, priority, source, payload, status, created_at
                FROM events
                WHERE dedupe_key = ? AND created_at >= ?
                ORDER BY id DESC LIMIT 1
                """,
                (dedupe_key, since),
            ).fetchone()
        return _event_row(row) if row else None

    def list_events(self, status: str | None = None, limit: int = 50) -> list[dict]:
        query = """
            SELECT id, event_type, priority, source, payload, status, created_at
            FROM events
        """
        parameters: tuple[Any, ...]
        if status:
            query += " WHERE status = ?"
            parameters = (status, limit)
        else:
            parameters = (limit,)
        query += " ORDER BY id DESC LIMIT ?"
        with self._connect() as conn:
            rows = conn.execute(query, parameters).fetchall()
        return [_event_row(row) for row in rows]

    def acknowledge_event(self, event_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE events
                SET status = 'delivered', delivered_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'pending'
                """,
                (event_id,),
            )
            return cursor.rowcount > 0

    def add_timer(self, label: str, due_at: str, kind: str = "timer") -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO timers (label, due_at, kind) VALUES (?, ?, ?)",
                (label, due_at, kind),
            )
            return int(cursor.lastrowid)

    def list_timers(self, status: str = "pending") -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, label, due_at, kind, status, created_at, finished_at
                FROM timers WHERE status = ? ORDER BY due_at
                """,
                (status,),
            ).fetchall()
        return [
            {
                "id": row[0],
                "label": row[1],
                "due_at": row[2],
                "kind": row[3],
                "status": row[4],
                "created_at": row[5],
                "finished_at": row[6],
            }
            for row in rows
        ]

    def finish_timer(self, timer_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE timers SET status = 'finished', finished_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'pending'
                """,
                (timer_id,),
            )
            return cursor.rowcount > 0

    def cancel_timer(self, timer_id: int | None = None) -> int:
        with self._connect() as conn:
            if timer_id is None:
                row = conn.execute(
                    "SELECT id FROM timers WHERE status = 'pending' ORDER BY id DESC LIMIT 1"
                ).fetchone()
                timer_id = int(row[0]) if row else None
            if timer_id is None:
                return 0
            cursor = conn.execute(
                "UPDATE timers SET status = 'cancelled' WHERE id = ? AND status = 'pending'",
                (timer_id,),
            )
            return cursor.rowcount

    def add_contextual_reminder(
        self,
        text: str,
        event_type: str,
        conditions: dict[str, Any] | None = None,
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO contextual_reminders (text, event_type, conditions)
                VALUES (?, ?, ?)
                """,
                (text, event_type, json.dumps(conditions or {})),
            )
            return int(cursor.lastrowid)

    def list_contextual_reminders(self, status: str = "pending") -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, text, event_type, conditions, status, created_at, triggered_at
                FROM contextual_reminders WHERE status = ? ORDER BY id DESC
                """,
                (status,),
            ).fetchall()
        return [
            {
                "id": row[0],
                "text": row[1],
                "event_type": row[2],
                "conditions": json.loads(row[3]),
                "status": row[4],
                "created_at": row[5],
                "triggered_at": row[6],
            }
            for row in rows
        ]

    def trigger_contextual_reminder(self, reminder_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE contextual_reminders
                SET status = 'triggered', triggered_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'pending'
                """,
                (reminder_id,),
            )
            return cursor.rowcount > 0

    def set_runtime_state(self, key: str, value: Any) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runtime_state (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE
                SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
                """,
                (key, json.dumps(value)),
            )

    def get_runtime_state(self, key: str, default: Any = None) -> Any:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM runtime_state WHERE key = ?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def add_automation(
        self,
        name: str,
        trigger_type: str,
        trigger_config: dict,
        conditions: dict,
        actions: list[dict],
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO automations
                (name, trigger_type, trigger_config, conditions, actions)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    name,
                    trigger_type,
                    json.dumps(trigger_config),
                    json.dumps(conditions),
                    json.dumps(actions),
                ),
            )
            conn.execute(
                """
                DELETE FROM tool_runs
                WHERE id NOT IN (SELECT id FROM tool_runs ORDER BY id DESC LIMIT 2000)
                """
            )
            return int(cursor.lastrowid)

    def list_automations(self, enabled_only: bool = False) -> list[dict]:
        query = """
            SELECT id, name, trigger_type, trigger_config, conditions,
                   actions, enabled, created_at
            FROM automations
        """
        if enabled_only:
            query += " WHERE enabled = 1"
        query += " ORDER BY id DESC"
        with self._connect() as conn:
            rows = conn.execute(query).fetchall()
        return [
            {
                "id": row[0],
                "name": row[1],
                "trigger_type": row[2],
                "trigger_config": json.loads(row[3]),
                "conditions": json.loads(row[4]),
                "actions": json.loads(row[5]),
                "enabled": bool(row[6]),
                "created_at": row[7],
            }
            for row in rows
        ]

    def set_automation_enabled(self, automation_id: int, enabled: bool) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE automations SET enabled = ? WHERE id = ?",
                (int(enabled), automation_id),
            )
            return cursor.rowcount > 0

    def add_tool_run(
        self,
        tool_name: str,
        arguments: dict,
        result: dict,
        risk_level: str,
        status: str,
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tool_runs
                (tool_name, arguments, result, risk_level, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    tool_name,
                    json.dumps(arguments),
                    json.dumps(result),
                    risk_level,
                    status,
                ),
            )
            return int(cursor.lastrowid)

    def list_tool_runs(self, limit: int = 50) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, tool_name, arguments, result, risk_level, status, created_at
                FROM tool_runs ORDER BY id DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "id": row[0],
                "tool_name": row[1],
                "arguments": json.loads(row[2]),
                "result": json.loads(row[3]),
                "risk_level": row[4],
                "status": row[5],
                "created_at": row[6],
            }
            for row in rows
        ]

    def add_memory_record(
        self,
        kind: str,
        content: str,
        *,
        record_key: str | None = None,
        metadata: dict | None = None,
        confidence: float = 1.0,
        explicitness: str = "explicit",
        scope: str = "personal",
        expires_at: str | None = None,
    ) -> int:
        with self._connect() as conn:
            if record_key:
                conn.execute(
                    "DELETE FROM memory_records WHERE kind = ? AND record_key = ?",
                    (kind, record_key),
                )
            cursor = conn.execute(
                """
                INSERT INTO memory_records
                (kind, record_key, content, metadata, confidence, explicitness, scope, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    kind,
                    record_key,
                    content,
                    json.dumps(metadata or {}),
                    max(0.0, min(1.0, confidence)),
                    explicitness,
                    scope,
                    expires_at,
                ),
            )
            return int(cursor.lastrowid)

    def list_memory_records(self, kind: str | None = None, limit: int = 100) -> list[dict]:
        query = """
            SELECT id, kind, record_key, content, metadata, confidence, explicitness,
                   scope, expires_at, created_at, updated_at
            FROM memory_records
        """
        parameters: tuple[Any, ...]
        if kind:
            query += " WHERE kind = ? AND (expires_at IS NULL OR julianday(expires_at) > julianday('now'))"
            parameters = (kind, limit)
        else:
            query += " WHERE expires_at IS NULL OR julianday(expires_at) > julianday('now')"
            parameters = (limit,)
        query += " ORDER BY id DESC LIMIT ?"
        with self._connect() as conn:
            rows = conn.execute(query, parameters).fetchall()
        return [
            {
                "id": row[0],
                "kind": row[1],
                "key": row[2],
                "content": row[3],
                "metadata": json.loads(row[4]),
                "confidence": row[5],
                "explicitness": row[6],
                "scope": row[7],
                "expires_at": row[8],
                "created_at": row[9],
                "updated_at": row[10],
            }
            for row in rows
        ]

    def search_memory_records(
        self,
        query: str = "",
        *,
        kind: str | None = None,
        scope: str | None = None,
        min_confidence: float = 0.0,
        include_expired: bool = False,
        limit: int = 100,
    ) -> list[dict]:
        clauses: list[str] = []
        parameters: list[Any] = []
        if not include_expired:
            clauses.append("(expires_at IS NULL OR julianday(expires_at) > julianday('now'))")
        if kind:
            clauses.append("kind = ?")
            parameters.append(kind)
        if scope:
            clauses.append("scope = ?")
            parameters.append(scope)
        clauses.append("confidence >= ?")
        parameters.append(max(0.0, min(1.0, min_confidence)))
        if query.strip():
            escaped = (
                query.strip()
                .replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            clauses.append(
                "(content LIKE ? ESCAPE '\\' OR COALESCE(record_key, '') LIKE ? ESCAPE '\\')"
            )
            parameters.extend([f"%{escaped}%", f"%{escaped}%"])
        statement = """
            SELECT id, kind, record_key, content, metadata, confidence, explicitness,
                   scope, expires_at, created_at, updated_at
            FROM memory_records
        """
        if clauses:
            statement += " WHERE " + " AND ".join(clauses)
        statement += " ORDER BY updated_at DESC, id DESC LIMIT ?"
        parameters.append(max(1, min(1000, limit)))
        with self._connect() as conn:
            rows = conn.execute(statement, tuple(parameters)).fetchall()
        return [_memory_record(row) for row in rows]

    def memory_quality(self) -> dict[str, Any]:
        records = self.search_memory_records(include_expired=True, limit=1000)
        groups: dict[tuple[str, str], list[dict]] = {}
        for record in records:
            normalized = re.sub(r"\s+", " ", record["content"].casefold()).strip()
            groups.setdefault((record["kind"], normalized), []).append(record)
        duplicates = [
            {
                "kind": key[0],
                "content": items[0]["content"],
                "record_ids": [item["id"] for item in items],
            }
            for key, items in groups.items()
            if key[1] and len(items) > 1
        ]
        uncertain = [
            {"id": item["id"], "kind": item["kind"], "confidence": item["confidence"]}
            for item in records
            if item["confidence"] < 0.6 or item["explicitness"] == "inference"
        ]
        return {
            "record_count": len(records),
            "duplicate_groups": duplicates[:50],
            "uncertain_records": uncertain[:100],
            "healthy": not duplicates,
        }

    def update_memory_record(
        self,
        record_id: int,
        *,
        content: str | None = None,
        metadata: dict | None = None,
        confidence: float | None = None,
        scope: str | None = None,
    ) -> dict:
        changes: list[str] = []
        values: list[Any] = []
        if content is not None:
            changes.append("content = ?")
            values.append(content.strip())
        if metadata is not None:
            changes.append("metadata = ?")
            values.append(json.dumps(metadata))
        if confidence is not None:
            changes.append("confidence = ?")
            values.append(max(0.0, min(1.0, confidence)))
        if scope is not None:
            changes.append("scope = ?")
            values.append(scope.strip())
        if not changes:
            raise ValueError("No hay cambios para guardar")
        changes.append("updated_at = CURRENT_TIMESTAMP")
        values.append(record_id)
        with self._connect() as conn:
            cursor = conn.execute(
                f"UPDATE memory_records SET {', '.join(changes)} WHERE id = ?",
                values,
            )
            if cursor.rowcount != 1:
                raise KeyError(f"Memoria no encontrada: {record_id}")
        return next(item for item in self.list_memory_records(limit=1000) if item["id"] == record_id)

    def delete_memory_record(self, record_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM memory_records WHERE id = ?", (record_id,))
            return cursor.rowcount == 1

    def delete_skill(self, name: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM skills WHERE name = ?", (name,))
            return cursor.rowcount == 1

    def add_episode(
        self,
        event_type: str,
        summary: str,
        *,
        entities: list[str] | None = None,
        significance: float = 0.5,
        provenance: dict | None = None,
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO episodes
                (event_type, summary, entities, significance, provenance)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    event_type,
                    summary,
                    json.dumps(entities or []),
                    max(0.0, min(1.0, significance)),
                    json.dumps(provenance or {}),
                ),
            )
            return int(cursor.lastrowid)

    def list_episodes(self, *, since: str | None = None, limit: int = 100) -> list[dict]:
        query = """
            SELECT id, event_type, summary, entities, significance, provenance, created_at
            FROM episodes
        """
        parameters: tuple[Any, ...]
        if since:
            query += " WHERE created_at >= ?"
            parameters = (since, limit)
        else:
            parameters = (limit,)
        query += " ORDER BY id DESC LIMIT ?"
        with self._connect() as conn:
            rows = conn.execute(query, parameters).fetchall()
        return [
            {
                "id": row[0],
                "event_type": row[1],
                "summary": row[2],
                "entities": json.loads(row[3]),
                "significance": row[4],
                "provenance": json.loads(row[5]),
                "created_at": row[6],
            }
            for row in rows
        ]

    def add_decision(
        self,
        decision_type: str,
        input_facts: list[dict],
        scores: dict,
        outcome: str,
        rationale: str,
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO decisions (decision_type, input_facts, scores, outcome, rationale)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    decision_type,
                    json.dumps(input_facts),
                    json.dumps(scores),
                    outcome,
                    rationale,
                ),
            )
            return int(cursor.lastrowid)

    def list_decisions(self, limit: int = 50) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, decision_type, input_facts, scores, outcome, rationale, created_at
                FROM decisions ORDER BY id DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "id": row[0],
                "decision_type": row[1],
                "input_facts": json.loads(row[2]),
                "scores": json.loads(row[3]),
                "outcome": row[4],
                "rationale": row[5],
                "created_at": row[6],
            }
            for row in rows
        ]

    def create_work_item(
        self,
        objective: str,
        plan: list[dict],
        authorized_scope: str = "user-authorized",
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO work_items (objective, plan, authorized_scope)
                VALUES (?, ?, ?)
                """,
                (objective, json.dumps(plan), authorized_scope),
            )
            return int(cursor.lastrowid)

    def update_work_item(
        self,
        work_id: int,
        *,
        status: str | None = None,
        current_step: int | None = None,
        result: str | None = None,
    ) -> bool:
        updates: list[str] = []
        values: list[Any] = []
        if status is not None:
            updates.append("status = ?")
            values.append(status)
        if current_step is not None:
            updates.append("current_step = ?")
            values.append(current_step)
        if result is not None:
            updates.append("result = ?")
            values.append(result)
        if not updates:
            return False
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(work_id)
        with self._connect() as conn:
            cursor = conn.execute(
                f"UPDATE work_items SET {', '.join(updates)} WHERE id = ?",
                tuple(values),
            )
            return cursor.rowcount > 0

    def list_work_items(self, status: str | None = None, limit: int = 100) -> list[dict]:
        query = """
            SELECT id, objective, status, plan, current_step, result, authorized_scope,
                   created_at, updated_at FROM work_items
        """
        parameters: tuple[Any, ...]
        if status:
            query += " WHERE status = ?"
            parameters = (status, limit)
        else:
            parameters = (limit,)
        query += " ORDER BY id DESC LIMIT ?"
        with self._connect() as conn:
            rows = conn.execute(query, parameters).fetchall()
        return [
            {
                "id": row[0],
                "objective": row[1],
                "status": row[2],
                "plan": json.loads(row[3]),
                "current_step": row[4],
                "result": row[5],
                "authorized_scope": row[6],
                "created_at": row[7],
                "updated_at": row[8],
            }
            for row in rows
        ]

    def save_skill(
        self,
        name: str,
        trigger_phrase: str,
        actions: list[dict],
        status: str = "draft",
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO skills (name, trigger_phrase, actions, status)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    trigger_phrase = excluded.trigger_phrase,
                    actions = excluded.actions,
                    status = excluded.status,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (name, trigger_phrase, json.dumps(actions), status),
            )

    def list_skills(self, status: str | None = None) -> list[dict]:
        query = "SELECT id, name, trigger_phrase, actions, status, created_at, updated_at FROM skills"
        parameters: tuple[Any, ...] = ()
        if status:
            query += " WHERE status = ?"
            parameters = (status,)
        query += " ORDER BY name"
        with self._connect() as conn:
            rows = conn.execute(query, parameters).fetchall()
        return [
            {
                "id": row[0],
                "name": row[1],
                "trigger_phrase": row[2],
                "actions": json.loads(row[3]),
                "status": row[4],
                "created_at": row[5],
                "updated_at": row[6],
            }
            for row in rows
        ]

    def add_study_session(
        self,
        subject: str,
        *,
        topic: str = "",
        duration_minutes: int = 0,
        score: float | None = None,
        metadata: dict | None = None,
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO study_sessions
                (subject, topic, duration_minutes, score, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (subject, topic, max(0, duration_minutes), score, json.dumps(metadata or {})),
            )
            return int(cursor.lastrowid)

    def list_study_sessions(self, subject: str | None = None, limit: int = 200) -> list[dict]:
        query = """
            SELECT id, subject, topic, duration_minutes, score, metadata, created_at
            FROM study_sessions
        """
        parameters: tuple[Any, ...]
        if subject:
            query += " WHERE subject = ?"
            parameters = (subject, limit)
        else:
            parameters = (limit,)
        query += " ORDER BY id DESC LIMIT ?"
        with self._connect() as conn:
            rows = conn.execute(query, parameters).fetchall()
        return [
            {
                "id": row[0],
                "subject": row[1],
                "topic": row[2],
                "duration_minutes": row[3],
                "score": row[4],
                "metadata": json.loads(row[5]),
                "created_at": row[6],
            }
            for row in rows
        ]

    def upsert_calendar_event(
        self,
        external_id: str,
        title: str,
        starts_at: str,
        *,
        ends_at: str | None = None,
        location: str | None = None,
        source: str = "manual",
        metadata: dict | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO calendar_events
                (external_id, title, starts_at, ends_at, location, source, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(external_id) DO UPDATE SET
                    title = excluded.title,
                    starts_at = excluded.starts_at,
                    ends_at = excluded.ends_at,
                    location = excluded.location,
                    source = excluded.source,
                    metadata = excluded.metadata,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    external_id,
                    title,
                    starts_at,
                    ends_at,
                    location,
                    source,
                    json.dumps(metadata or {}),
                ),
            )

    def list_calendar_events(self, start: str, end: str, limit: int = 100) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT external_id, title, starts_at, ends_at, location, source, metadata,
                       updated_at
                FROM calendar_events
                WHERE starts_at >= ? AND starts_at <= ?
                ORDER BY starts_at LIMIT ?
                """,
                (start, end, limit),
            ).fetchall()
        return [
            {
                "id": row[0],
                "title": row[1],
                "starts_at": row[2],
                "ends_at": row[3],
                "location": row[4],
                "source": row[5],
                "metadata": json.loads(row[6]),
                "updated_at": row[7],
            }
            for row in rows
        ]


def _event_row(row: tuple) -> dict:
    return {
        "id": row[0],
        "event_type": row[1],
        "priority": row[2],
        "source": row[3],
        "payload": json.loads(row[4]),
        "status": row[5],
        "created_at": row[6],
    }


def _memory_record(row: tuple) -> dict:
    return {
        "id": row[0],
        "kind": row[1],
        "key": row[2],
        "content": row[3],
        "metadata": json.loads(row[4]),
        "confidence": row[5],
        "explicitness": row[6],
        "scope": row[7],
        "expires_at": row[8],
        "created_at": row[9],
        "updated_at": row[10],
    }
