"""Campus Customs API.

Problem 3: serves the catalogue, per-size stock, and product images from
data/campus_customs.db. Problem 4: accounts and sessions (see auth.py).
Problem 5: /api/chat runs the PydanticAI agent (agent.py, tools.py, models.py,
prompts/prompt.md).

Run from the backend/ folder:  uvicorn main:app --reload --port 8000
"""

import json
import logging
import sqlite3
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from agent import append_audit, new_audit_entry, redact, run_chat
import chat_store
import tools
from auth import build_router, init_auth_tables
from models import ChatHistoryResponse, ChatRequest, ChatResponse

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "campus_customs.db"
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

app = FastAPI(title="Campus Customs API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
# Problem 9 (B2): compress JSON responses (the 102-product catalogue is ~70% smaller gzipped).
app.add_middleware(GZipMiddleware, minimum_size=1000)


class CachedStaticFiles(StaticFiles):
    """Product photos don't change, so let browsers keep them for a day instead of re-asking."""

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        if response.status_code in (200, 304):
            response.headers["Cache-Control"] = "public, max-age=86400"
        return response


# catalogue.image_file_path is "products/<id>.jpg", relative to data/,
# so /media/products/<id>.jpg maps straight onto it.
app.mount("/media", CachedStaticFiles(directory=DATA_DIR), name="media")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


with get_db() as _conn:
    init_auth_tables(_conn)
chat_store.init_chat_tables(DB_PATH)
auth_router = build_router(get_db)
app.include_router(auth_router)


def product_from_row(row: sqlite3.Row) -> dict:
    product = dict(row)
    product["colors"] = json.loads(product["colors"])
    product["search_tags"] = json.loads(product["search_tags"])
    product["image_url"] = f"/media/{product['image_file_path']}"
    return product


def stock_for(conn: sqlite3.Connection, product_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
    ).fetchall()
    stock = [dict(r) for r in rows]
    stock.sort(key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else 99)
    return stock


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/products")
def list_products() -> list[dict]:
    """Cached catalogue (tools.catalogue) + live stock: one small inventory query per request.

    `stock` (size -> quantity, XS..XXL) lets product cards show which sizes are available (Problem 10).
    """
    with get_db() as conn:
        rows = conn.execute("SELECT product_id, size, quantity FROM inventory").fetchall()
    stock: dict[str, dict[str, int]] = {}
    for r in rows:
        stock.setdefault(r["product_id"], {})[r["size"]] = r["quantity"]
    out = []
    for p in tools.catalogue(DB_PATH):
        sizes = stock.get(p["product_id"], {})
        ordered = {s: sizes[s] for s in SIZE_ORDER if s in sizes}
        out.append({**p, "stock": ordered, "total_stock": sum(ordered.values())})
    return out


@app.get("/api/categories")
def list_categories() -> list[dict]:
    """The shop's aisles with counts and a cover image, for the nav menu and category tiles."""
    products = tools.catalogue(DB_PATH)
    out = []
    for slug, label in tools.CATEGORIES.items():
        items = [p for p in products if p["category"] == slug]
        if items:
            out.append({"slug": slug, "label": label, "count": len(items), "image_url": items[0]["image_url"]})
    return out


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        product = product_from_row(row)
        product["category"] = tools.category_for(product["garment_type"])
        product["inventory"] = stock_for(conn, product_id)
    return product


log = logging.getLogger("campus_customs")

# Problem 9 (B1): cap chat turns per shopper so a script or a stuck client can't run up model costs.
CHAT_LIMIT, CHAT_WINDOW_SECONDS = 20, 60
_chat_calls: dict[str, deque[float]] = defaultdict(deque)


def check_chat_rate(key: str) -> None:
    calls, now = _chat_calls[key], time.monotonic()
    while calls and now - calls[0] > CHAT_WINDOW_SECONDS:
        calls.popleft()
    if len(calls) >= CHAT_LIMIT:
        raise HTTPException(status_code=429, detail="You're sending messages quickly. Give it a few seconds and try again.")
    calls.append(now)


@app.post("/api/chat")
async def chat(
    req: ChatRequest, request: Request, user: dict | None = Depends(auth_router.current_user)
) -> ChatResponse:
    """One chat turn: message + page context in, the agent's reply + product cards out.

    Logged in: history comes from chat_messages and the turn is saved there.
    Guest: history comes from the browser and nothing is stored.
    """
    try:
        check_chat_rate(f"user:{user['id']}" if user else f"ip:{request.client.host if request.client else '?'}")
    except HTTPException:
        blocked = new_audit_entry(
            user_id=user["id"] if user else None, page_path=req.page_context.path,
            product_id=req.page_context.product_id, message=req.message, model="(not called)",
            history_messages=0, stop_reason="rate_limited",
        )
        append_audit(blocked)
        raise
    # Safety: card-like numbers never reach the model, the chat history table, or the audit log.
    message = redact(req.message)
    history = (
        chat_store.recent_history(DB_PATH, user["id"])
        if user
        else [h.model_copy(update={"content": redact(h.content)}) for h in req.history[-12:]]
    )
    try:
        response = await run_chat(message, history, user=user, page=req.page_context)
    except Exception:
        log.exception("Agent run failed")
        raise HTTPException(
            status_code=502,
            detail="Sorry, our assistant is having trouble right now. Please try again in a moment.",
        )
    if user:
        chat_store.save_turn(DB_PATH, user["id"], message, response)
    return response


@app.get("/api/chat/history")
def chat_history(user: dict = Depends(auth_router.require_user)) -> ChatHistoryResponse:
    """The logged-in shopper's saved conversation, so the widget can reload it when they return."""
    return ChatHistoryResponse(messages=chat_store.load_messages(DB_PATH, user["id"]))


@app.delete("/api/chat/history")
def clear_chat_history(user: dict = Depends(auth_router.require_user)) -> dict:
    """Let a shopper wipe their own saved chat."""
    return {"deleted": chat_store.clear_history(DB_PATH, user["id"])}
