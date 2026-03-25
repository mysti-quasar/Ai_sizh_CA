import json
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class LocalCache:
    def __init__(self, db_path: str = "./connector_cache.sqlite3"):
        self.db_path = str(Path(db_path).resolve())
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sync_state (
                    entity TEXT PRIMARY KEY,
                    last_sync_at TEXT,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sync_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity TEXT,
                    sync_type TEXT,
                    status TEXT,
                    message TEXT,
                    payload_json TEXT,
                    started_at TEXT,
                    ended_at TEXT
                );

                CREATE TABLE IF NOT EXISTS pending_tasks (
                    id TEXT PRIMARY KEY,
                    task_type TEXT NOT NULL,
                    entity TEXT,
                    payload_json TEXT NOT NULL,
                    dedupe_key TEXT,
                    status TEXT NOT NULL,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    next_attempt_at TEXT,
                    last_error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_pending_tasks_dedupe
                ON pending_tasks(dedupe_key)
                WHERE dedupe_key IS NOT NULL;

                CREATE TABLE IF NOT EXISTS fingerprints (
                    entity TEXT NOT NULL,
                    external_id TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (entity, external_id)
                );
                """
            )

    def get_or_create_device_id(self) -> str:
        existing = self.get_setting("device_id")
        if existing:
            return existing
        device_id = str(uuid.uuid4())
        self.set_setting("device_id", device_id)
        return device_id

    def set_setting(self, key: str, value: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO settings(key, value)
                VALUES(?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """,
                (key, value),
            )

    def get_setting(self, key: str, default: str = "") -> str:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set_last_sync(self, entity: str, last_sync_at: str) -> None:
        now = datetime.utcnow().isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sync_state(entity, last_sync_at, updated_at)
                VALUES(?, ?, ?)
                ON CONFLICT(entity) DO UPDATE SET
                    last_sync_at=excluded.last_sync_at,
                    updated_at=excluded.updated_at
                """,
                (entity, last_sync_at, now),
            )

    def get_last_sync(self, entity: str) -> str:
        with self._connect() as conn:
            row = conn.execute("SELECT last_sync_at FROM sync_state WHERE entity=?", (entity,)).fetchone()
        return row["last_sync_at"] if row and row["last_sync_at"] else ""

    def add_sync_log(
        self,
        entity: str,
        sync_type: str,
        status: str,
        message: str,
        payload: dict[str, Any] | None = None,
        started_at: str = "",
        ended_at: str = "",
    ) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sync_logs(entity, sync_type, status, message, payload_json, started_at, ended_at)
                VALUES(?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entity,
                    sync_type,
                    status,
                    message,
                    json.dumps(payload or {}),
                    started_at,
                    ended_at,
                ),
            )

    def enqueue_task(
        self,
        task_type: str,
        payload: dict[str, Any],
        entity: str = "",
        dedupe_key: str | None = None,
    ) -> tuple[bool, str]:
        now = datetime.utcnow().isoformat()
        task_id = str(uuid.uuid4())

        try:
            with self._lock, self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO pending_tasks(
                        id, task_type, entity, payload_json, dedupe_key, status,
                        retry_count, next_attempt_at, last_error, created_at, updated_at
                    )
                    VALUES(?, ?, ?, ?, ?, 'queued', 0, ?, '', ?, ?)
                    """,
                    (
                        task_id,
                        task_type,
                        entity,
                        json.dumps(payload),
                        dedupe_key,
                        now,
                        now,
                        now,
                    ),
                )
            return True, task_id
        except sqlite3.IntegrityError:
            return False, "duplicate"

    def claim_tasks(self, limit: int = 20) -> list[dict[str, Any]]:
        now = datetime.utcnow().isoformat()
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM pending_tasks
                WHERE status IN ('queued', 'retry')
                  AND (next_attempt_at IS NULL OR next_attempt_at <= ?)
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (now, limit),
            ).fetchall()

            task_ids = [row["id"] for row in rows]
            if task_ids:
                conn.executemany(
                    "UPDATE pending_tasks SET status='processing', updated_at=? WHERE id=?",
                    [(now, task_id) for task_id in task_ids],
                )

        tasks = []
        for row in rows:
            tasks.append(
                {
                    "id": row["id"],
                    "task_type": row["task_type"],
                    "entity": row["entity"],
                    "payload": json.loads(row["payload_json"]),
                    "dedupe_key": row["dedupe_key"],
                    "retry_count": row["retry_count"],
                }
            )
        return tasks

    def complete_task(self, task_id: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM pending_tasks WHERE id=?", (task_id,))

    def fail_task(self, task_id: str, error: str, retry_count: int, max_retries: int = 5) -> None:
        now = datetime.utcnow()
        with self._lock, self._connect() as conn:
            if retry_count >= max_retries:
                conn.execute(
                    """
                    UPDATE pending_tasks
                    SET status='failed', retry_count=?, last_error=?, updated_at=?
                    WHERE id=?
                    """,
                    (retry_count, error[:500], now.isoformat(), task_id),
                )
                return

            # Exponential retry delay: 2, 4, 8, 16, ... seconds
            next_attempt = now + timedelta(seconds=2 ** max(1, retry_count))
            conn.execute(
                """
                UPDATE pending_tasks
                SET status='retry', retry_count=?, last_error=?, next_attempt_at=?, updated_at=?
                WHERE id=?
                """,
                (retry_count, error[:500], next_attempt.isoformat(), now.isoformat(), task_id),
            )

    def pending_summary(self) -> dict[str, int]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) AS count FROM pending_tasks GROUP BY status"
            ).fetchall()
        summary = {"queued": 0, "retry": 0, "processing": 0, "failed": 0}
        for row in rows:
            summary[row["status"]] = int(row["count"])
        return summary

    def filter_new_or_modified(
        self,
        entity: str,
        records: list[dict[str, Any]],
        id_field: str = "guid",
        fingerprint_field: str = "fingerprint",
    ) -> list[dict[str, Any]]:
        changed: list[dict[str, Any]] = []
        now = datetime.utcnow().isoformat()

        with self._lock, self._connect() as conn:
            for record in records:
                external_id = str(record.get(id_field) or record.get("name") or "")
                if not external_id:
                    continue
                fingerprint = str(record.get(fingerprint_field, ""))
                row = conn.execute(
                    "SELECT fingerprint FROM fingerprints WHERE entity=? AND external_id=?",
                    (entity, external_id),
                ).fetchone()
                if not row or row["fingerprint"] != fingerprint:
                    changed.append(record)
                    conn.execute(
                        """
                        INSERT INTO fingerprints(entity, external_id, fingerprint, updated_at)
                        VALUES(?, ?, ?, ?)
                        ON CONFLICT(entity, external_id)
                        DO UPDATE SET fingerprint=excluded.fingerprint, updated_at=excluded.updated_at
                        """,
                        (entity, external_id, fingerprint, now),
                    )

        return changed
