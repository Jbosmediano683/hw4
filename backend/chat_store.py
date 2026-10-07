"""Customer memory (Problem 8): logged-in shoppers' chat history in the chat_messages table.

One row per message:
  id, user_id -> users.id, role ('user' | 'assistant'), content,
  products_json      - chat product cards shown under an assistant reply (JSON list of ProductCard)
  page_results_json  - page results the reply put on the website (JSON PageResultsOut), added here
  created_at

Every query is scoped by user_id taken from the session cookie, so a shopper can
only ever read or clear their own history.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from models import ChatResponse, HistoryMessage, MAX_HISTORY_MESSAGES, PageResultsOut, ProductCard, StoredMessage

MAX_RELOAD_MESSAGES = 50  # shown in the widget when a shopper returns


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_chat_tables(db_path: Path) -> None:
    """chat_messages ships with the seed DB; add the page_results_json column once."""
    with connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                products_json TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        columns = {r["name"] for r in conn.execute("PRAGMA table_info(chat_messages)")}
        if "page_results_json" not in columns:
            conn.execute("ALTER TABLE chat_messages ADD COLUMN page_results_json TEXT")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages (user_id, id)")


def _rows(conn: sqlite3.Connection, user_id: int, limit: int) -> list[sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT role, content, products_json, page_results_json, created_at
        FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()
    return list(reversed(rows))


def _cards(raw: str | None) -> list[ProductCard]:
    # Seed rows store richer product dicts (tags, inventory); ProductCard keeps just the card fields.
    return [ProductCard.model_validate(p) for p in json.loads(raw)] if raw else []


def _page(raw: str | None) -> PageResultsOut | None:
    return PageResultsOut.model_validate_json(raw) if raw else None


def load_messages(db_path: Path, user_id: int, limit: int = MAX_RELOAD_MESSAGES) -> list[StoredMessage]:
    """What the widget shows when a logged-in shopper comes back."""
    with connect(db_path) as conn:
        rows = _rows(conn, user_id, limit)
    return [
        StoredMessage(
            role=r["role"],
            content=r["content"],
            products=_cards(r["products_json"]),
            page_results=_page(r["page_results_json"]),
            created_at=r["created_at"],
        )
        for r in rows
    ]


def recent_history(db_path: Path, user_id: int, limit: int = MAX_HISTORY_MESSAGES) -> list[HistoryMessage]:
    """The agent's memory for a logged-in shopper, read from the DB (not trusted from the browser)."""
    with connect(db_path) as conn:
        rows = _rows(conn, user_id, limit)
    history = []
    for r in rows:
        page = _page(r["page_results_json"])
        history.append(
            HistoryMessage(
                role=r["role"],
                content=r["content"][:4000],
                product_ids=[c.product_id for c in _cards(r["products_json"])][:8],
                page_product_ids=[c.product_id for c in page.products] if page else [],
            )
        )
    return history


def save_turn(db_path: Path, user_id: int, message: str, response: ChatResponse) -> None:
    """Store the shopper's message and the assistant's reply (with its cards) as two rows."""
    with connect(db_path) as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)",
            (user_id, message),
        )
        conn.execute(
            """
            INSERT INTO chat_messages (user_id, role, content, products_json, page_results_json)
            VALUES (?, 'assistant', ?, ?, ?)
            """,
            (
                user_id,
                response.reply,
                json.dumps([c.model_dump() for c in response.products]),
                response.page_results.model_dump_json() if response.page_results else None,
            ),
        )


def clear_history(db_path: Path, user_id: int) -> int:
    with connect(db_path) as conn:
        return conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,)).rowcount


def message_count(db_path: Path, user_id: int) -> int:
    with connect(db_path) as conn:
        return conn.execute("SELECT COUNT(*) FROM chat_messages WHERE user_id = ?", (user_id,)).fetchone()[0]
