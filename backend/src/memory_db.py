import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("anisha-memory")

DB_PATH = Path(__file__).resolve().parent.parent / "memory.db"


def _get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_database() -> None:
    """Create the caller memory table if it does not already exist."""
    with _get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS caller_memory (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                language_preference TEXT,
                facts TEXT NOT NULL DEFAULT '{}',
                last_interaction TEXT NOT NULL
            )
            """
        )
        connection.commit()

    logger.info("Memory database initialized at %s", DB_PATH)


def lookup_caller(user_id: str) -> dict[str, Any] | None:
    """Return stored caller memory, or None if the caller is unknown."""
    if not user_id:
        return None

    with _get_connection() as connection:
        row = connection.execute(
            """
            SELECT user_id, name, language_preference, facts, last_interaction
            FROM caller_memory
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

    if row is None:
        return None

    try:
        facts = json.loads(row["facts"])
    except (TypeError, json.JSONDecodeError):
        facts = {}

    return {
        "user_id": row["user_id"],
        "name": row["name"],
        "language_preference": row["language_preference"],
        "facts": facts,
        "last_interaction": row["last_interaction"],
    }


def save_caller(
    user_id: str,
    name: str | None = None,
    language_preference: str | None = None,
    facts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create or update a caller's persistent memory."""
    if not user_id:
        raise ValueError("user_id is required")

    existing = lookup_caller(user_id)

    existing_facts = existing.get("facts", {}) if existing else {}
    merged_facts = {**existing_facts, **(facts or {})}

    final_name = (
        name if name is not None else (existing.get("name") if existing else None)
    )

    final_language = (
        language_preference
        if language_preference is not None
        else (
            existing.get("language_preference")
            if existing
            else None
        )
    )

    timestamp = datetime.now(timezone.utc).isoformat()

    with _get_connection() as connection:
        connection.execute(
            """
            INSERT INTO caller_memory (
                user_id,
                name,
                language_preference,
                facts,
                last_interaction
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name = excluded.name,
                language_preference = excluded.language_preference,
                facts = excluded.facts,
                last_interaction = excluded.last_interaction
            """,
            (
                user_id,
                final_name,
                final_language,
                json.dumps(merged_facts, ensure_ascii=False),
                timestamp,
            ),
        )
        connection.commit()

    return lookup_caller(user_id) or {
        "user_id": user_id,
        "name": final_name,
        "language_preference": final_language,
        "facts": merged_facts,
        "last_interaction": timestamp,
    }