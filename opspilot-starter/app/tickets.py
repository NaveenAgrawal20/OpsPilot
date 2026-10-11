"""SQLite ticket drafts with explicit approval and idempotent creation."""

import os
import sqlite3
import uuid
from pathlib import Path


def database_path() -> Path:
    root = Path(__file__).resolve().parents[1]
    return Path(os.getenv("OPSPILOT_DB", str(root / "data" / "opspilot.db"))).resolve()


def connect() -> sqlite3.Connection:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("""CREATE TABLE IF NOT EXISTS drafts (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        summary TEXT NOT NULL,
        approved INTEGER NOT NULL DEFAULT 0
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS tickets (
        id TEXT PRIMARY KEY,
        draft_id TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        summary TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'open'
    )""")
    connection.commit()
    return connection


def prepare_draft(title: str, summary: str) -> dict:
    draft_id = str(uuid.uuid4())
    with connect() as db:
        db.execute("INSERT INTO drafts (id, title, summary) VALUES (?, ?, ?)",
                   (draft_id, title, summary))
    return {"draft_id": draft_id, "approved": False}


def approve_draft(draft_id: str) -> None:
    with connect() as db:
        cursor = db.execute("UPDATE drafts SET approved = 1 WHERE id = ?", (draft_id,))
        if cursor.rowcount == 0:
            raise ValueError("Draft does not exist")


def create_approved_ticket(draft_id: str) -> dict:
    """The MCP server calls this; repeat calls return the same ticket."""
    with connect() as db:
        draft = db.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
        if draft is None:
            raise ValueError("Draft does not exist")
        if not draft["approved"]:
            raise PermissionError("Human approval required")
        previous = db.execute("SELECT * FROM tickets WHERE draft_id = ?", (draft_id,)).fetchone()
        if previous is not None:
            return dict(previous)
        ticket_id = "INC-" + uuid.uuid4().hex[:8].upper()
        db.execute(
            "INSERT INTO tickets (id, draft_id, title, summary) VALUES (?, ?, ?, ?)",
            (ticket_id, draft_id, draft["title"], draft["summary"]),
        )
        return {"id": ticket_id, "draft_id": draft_id, "title": draft["title"],
                "summary": draft["summary"], "status": "open"}


def list_tickets() -> list[dict]:
    with connect() as db:
        return [dict(row) for row in db.execute("SELECT * FROM tickets ORDER BY rowid DESC")]
