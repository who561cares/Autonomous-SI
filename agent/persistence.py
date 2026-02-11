"""SQLite-backed persistence for state, memory, and reflections."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class SQLiteStore:
    """Simple SQLite persistence helper for agent runtime state and memory."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS kv_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    user TEXT NOT NULL,
                    assistant TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reflections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    turn INTEGER NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def load_state(self, default_state: dict[str, Any]) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM kv_state WHERE key = ?", ("runtime_state",)).fetchone()
        if not row:
            return default_state
        return json.loads(row["value"])

    def save_state(self, state: dict[str, Any]) -> None:
        payload = json.dumps(state, ensure_ascii=False)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO kv_state(key, value) VALUES(?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """,
                ("runtime_state", payload),
            )
            conn.commit()

    def load_memory(self, limit: int) -> list[dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT ts, user, assistant FROM memory ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        items = [dict(row) for row in rows]
        items.reverse()
        return items

    def append_memory(self, ts: str, user_message: str, reply: str, max_items: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO memory(ts, user, assistant) VALUES (?, ?, ?)",
                (ts, user_message, reply),
            )
            conn.execute(
                """
                DELETE FROM memory
                WHERE id NOT IN (
                    SELECT id FROM memory ORDER BY id DESC LIMIT ?
                )
                """,
                (max_items,),
            )
            conn.commit()

    def append_reflection(self, ts: str, turn: int, reflection: dict[str, Any]) -> None:
        payload = json.dumps(reflection, ensure_ascii=False)
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO reflections(ts, turn, payload) VALUES (?, ?, ?)",
                (ts, turn, payload),
            )
            conn.commit()

    def load_reflections(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT ts, turn, payload FROM reflections ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        result: list[dict[str, Any]] = []
        for row in reversed(rows):
            result.append({"ts": row["ts"], "turn": row["turn"], "reflection": json.loads(row["payload"])})
        return result
