import sqlite3
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "call_analytics.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_analytics_database():
    conn = get_connection()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id TEXT UNIQUE NOT NULL,
            user_id TEXT,
            outcome TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


def record_call(
    call_id: str,
    user_id: str,
    outcome: str,
):
    init_analytics_database()

    conn = get_connection()

    conn.execute(
        """
        INSERT OR REPLACE INTO calls (
            call_id,
            user_id,
            outcome,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            call_id,
            user_id,
            outcome,
            datetime.now(timezone.utc).isoformat(),
        ),
    )

    conn.commit()
    conn.close()


def get_call_counts():
    init_analytics_database()

    conn = get_connection()

    total = conn.execute(
        "SELECT COUNT(*) FROM calls"
    ).fetchone()[0]

    successful = conn.execute(
        "SELECT COUNT(*) FROM calls WHERE outcome = 'success'"
    ).fetchone()[0]

    failed = conn.execute(
        "SELECT COUNT(*) FROM calls WHERE outcome = 'failed'"
    ).fetchone()[0]

    conn.close()

    return {
        "total": total,
        "successful": successful,
        "failed": failed,
    }
