"""Append-only audit trail of agent-loop activity (Problem 12).

output/audit_trail.json is a JSON array. Every chat turn appends one AuditEntry; entries are never
removed or rewritten, and the file is never reset between runs. Writes are serialized with a lock and
done atomically (temp file + replace), so the file stays valid JSON even if the server is stopped mid-write.

Privacy: entries hold the user id only (no email/name), redacted message text, and short summaries,
never full tool payloads or secrets.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel
from pydantic_ai.messages import ModelMessage, ModelResponse, RetryPromptPart, ToolCallPart, ToolReturnPart

from models import AuditEntry, AuditToolCall

AUDIT_PATH = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"
SHORT = 160  # max characters for args / results / messages in the log
_lock = threading.Lock()

# 12-19 digits, optionally separated by spaces or dashes: looks like a payment card number.
CARD_RE = re.compile(r"\b\d(?:[ -]?\d){11,18}\b")


def redact(text: str) -> str:
    """Mask anything that looks like a payment card number (used for the model, chat history, and the log)."""
    return CARD_RE.sub("[redacted number]", text)


def short(value, limit: int = SHORT) -> str:
    if isinstance(value, BaseModel):
        text = value.model_dump_json()
    elif isinstance(value, (list, tuple)) and value and isinstance(value[0], BaseModel):
        text = json.dumps([v.model_dump(mode="json") for v in value], ensure_ascii=False)
    elif isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, default=str)
    else:
        text = str(value)
    text = redact(" ".join(text.split()))
    return text if len(text) <= limit else text[: limit - 1] + "…"


def summarize_result(content) -> str:
    """A human-readable one-liner for common tool results, else truncated JSON."""
    name = type(content).__name__
    if name == "SearchResults":
        ids = [h.product_id for h in content.results]
        return short(f"{content.total_matches} matches, {len(ids)} returned: {', '.join(ids)}")
    if name == "StockReport":
        sizes = ", ".join(f"{s.size}={s.quantity}" for s in content.sizes)
        return short(f"{content.product_id}: {sizes} (requested {content.requested_size or 'all'})")
    if isinstance(content, list) and content and type(content[0]).__name__ == "ProductPrice":
        return short(", ".join(f"{p.product_id}=${p.price:.2f}" for p in content))
    return short(content)


def tool_calls_from(messages: list[ModelMessage]) -> tuple[list[AuditToolCall], str | None]:
    """Pair each ToolCallPart with its ToolReturnPart / RetryPromptPart by tool_call_id."""
    calls: dict[str, AuditToolCall] = {}
    order: list[str] = []
    finish_reason = None
    for m in messages:
        if isinstance(m, ModelResponse):
            finish_reason = getattr(m, "finish_reason", None) or finish_reason
        for part in m.parts:
            if isinstance(part, ToolCallPart):
                calls[part.tool_call_id] = AuditToolCall(tool=part.tool_name, args=short(part.args_as_dict()))
                order.append(part.tool_call_id)
            elif isinstance(part, ToolReturnPart) and part.tool_call_id in calls:
                calls[part.tool_call_id].result = summarize_result(part.content)
            elif isinstance(part, RetryPromptPart) and part.tool_call_id in calls:
                calls[part.tool_call_id].retried = True
                calls[part.tool_call_id].result = short(part.content)
    return [calls[i] for i in order], (str(finish_reason) if finish_reason else None)


def new_entry(*, user_id: int | None, page_path: str, product_id: str | None, message: str,
              model: str, history_messages: int, stop_reason: str = "final_result") -> AuditEntry:
    return AuditEntry(
        id=uuid.uuid4().hex[:12],
        time=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        user=f"user:{user_id}" if user_id else "guest",
        page=page_path + (f" [{product_id}]" if product_id else ""),
        message=short(message, 200),
        model=model,
        history_messages=history_messages,
        stop_reason=stop_reason,
    )


def append(entry: AuditEntry) -> None:
    """Append one entry. Never truncates: existing entries are read back and kept."""
    with _lock:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        entries: list = []
        if AUDIT_PATH.exists():
            try:
                entries = json.loads(AUDIT_PATH.read_text(encoding="utf-8") or "[]")
            except json.JSONDecodeError:
                # Never wipe history: keep the unreadable file aside and start a new array.
                AUDIT_PATH.replace(AUDIT_PATH.with_suffix(f".corrupt-{int(time.time())}.json"))
                entries = []
        entries.append(entry.model_dump(mode="json"))
        tmp = AUDIT_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(entries, indent=1, ensure_ascii=False), encoding="utf-8")
        for attempt in range(5):  # OneDrive can hold the file briefly while syncing
            try:
                os.replace(tmp, AUDIT_PATH)
                return
            except PermissionError:
                time.sleep(0.1 * (attempt + 1))
        os.replace(tmp, AUDIT_PATH)
