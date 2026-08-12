import sqlite3
import uuid
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "escalation.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_escalation_database():
    conn = get_connection()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS escalations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference_id TEXT UNIQUE NOT NULL,
            who_needs_help TEXT NOT NULL,
            problem TEXT NOT NULL,
            already_checked TEXT,
            urgency TEXT NOT NULL,
            language TEXT,
            preferred_followup TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def create_escalation(
    who_needs_help: str,
    problem: str,
    already_checked: str,
    urgency: str,
    language: str,
    preferred_followup: str,
):
    init_escalation_database()

    reference_id = (
        f"ESC-{datetime.now().strftime('%Y%m%d')}-"
        f"{uuid.uuid4().hex[:6].upper()}"
    )

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO escalations (
            reference_id,
            who_needs_help,
            problem,
            already_checked,
            urgency,
            language,
            preferred_followup,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?)
        """,
        (
            reference_id,
            who_needs_help,
            problem,
            already_checked,
            urgency,
            language,
            preferred_followup,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )

    conn.commit()
    conn.close()

    return reference_id


def get_all_escalations():
    init_escalation_database()

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT *
        FROM escalations
        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]