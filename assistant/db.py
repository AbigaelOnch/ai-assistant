"""Local SQLite store for tasks, pending approvals and a run log."""
import json
import sqlite3
from datetime import datetime

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    notes TEXT,
    source TEXT,
    due TEXT,
    priority TEXT DEFAULT 'normal',
    status TEXT DEFAULT 'open',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool TEXT NOT NULL,
    args TEXT NOT NULL,
    reason TEXT,
    status TEXT DEFAULT 'pending',
    result TEXT,
    created_at TEXT NOT NULL,
    decided_at TEXT
);
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    summary TEXT
);
"""


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


# --- approvals -------------------------------------------------------------

def queue_approval(tool: str, args: dict, reason: str) -> int:
    with connect() as c:
        cur = c.execute(
            "INSERT INTO approvals (tool, args, reason, created_at) VALUES (?,?,?,?)",
            (tool, json.dumps(args), reason, now()))
        return cur.lastrowid


def pending_approvals() -> list[sqlite3.Row]:
    with connect() as c:
        return c.execute(
            "SELECT * FROM approvals WHERE status='pending' ORDER BY id").fetchall()


def decide_approval(approval_id: int, status: str, result: str = "") -> None:
    with connect() as c:
        c.execute("UPDATE approvals SET status=?, result=?, decided_at=? WHERE id=?",
                  (status, result, now(), approval_id))


def log_run(summary: str) -> None:
    with connect() as c:
        c.execute("INSERT INTO runs (started_at, summary) VALUES (?,?)", (now(), summary))


def last_run_time() -> str | None:
    with connect() as c:
        row = c.execute("SELECT started_at FROM runs ORDER BY id DESC LIMIT 1").fetchone()
        return row["started_at"] if row else None
