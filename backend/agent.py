"""Campus Customs agent: entry point and wiring.

The agent is four files: prompts/prompt.md (system prompt), agent.py (this file),
tools.py (database tools), and models.py (structured types).

This file loads the system prompt, connects a PydanticAI agent to the course model
through Portkey, registers the tools from tools.py, runs one chat turn for main.py's
/api/chat route (run_chat), and appends every turn to the audit trail
(output/audit_trail.json).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Literal
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

import tools
from models import (
    AuditEntry,
    AuditToolCall,
    ChatReply,
    ChatResponse,
    CustomerProfile,
    HistoryMessage,
    MAX_PAGE_RESULTS,
    PageContext,
    PageResultsOut,
    ProductDescription,
    ProductPrice,
    SearchResults,
    ShopDeps,
    StockReport,
)

BACKEND_DIR = Path(__file__).resolve().parent
PROMPT_PATH = BACKEND_DIR / "prompts" / "prompt.md"
DB_PATH = BACKEND_DIR.parent / "data" / "campus_customs.db"

# The API key lives in the workspace-root .env (AGENTS.md). A local .env, if any, wins.
for env_file in (BACKEND_DIR / ".env", BACKEND_DIR.parent / ".env", BACKEND_DIR.parent.parent / ".env"):
    load_dotenv(env_file)

PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
MODEL_NAME = os.getenv("CAMPUS_CUSTOMS_MODEL", "gpt-5.6-luna")
USAGE_LIMITS = UsageLimits(request_limit=8)  # max model calls per chat turn
# Problem 9 (B1): cheaper, faster turns on the same low-cost model.
MODEL_SETTINGS = OpenAIResponsesModelSettings(
    openai_reasoning_effort="low",  # shop Q&A needs lookups, not deep reasoning
    openai_text_verbosity="low",  # short replies, as the prompt asks
    max_tokens=1500,  # hard cap on output per call (a runaway reply can't run up the bill)
    openai_prompt_cache_key="campus-customs-agent-v1",  # same static prompt + tools every call -> cached input
)
MAX_CARDS = 4
MAX_SEARCH_RESULTS = MAX_PAGE_RESULTS
# Shown when the model gateway's content filter blocks a message (e.g. jailbreak attempts).
FILTERED_REPLY = (
    "Sorry, that's not something I can help with. I'm here for Campus Customs gear, though! "
    "Want help finding a hoodie, tee, or quarter-zip?"
)

log = logging.getLogger("campus_customs.agent")


def make_model() -> OpenAIResponsesModel:
    """gpt-5.6-luna through Portkey. Tools need the Responses API on this gateway."""
    api_key = os.environ.get("PORTKEY_API_KEY")
    if not api_key:
        raise RuntimeError("PORTKEY_API_KEY is not set (expected in the workspace .env).")
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=os.getenv("PORTKEY_BASE_URL", PORTKEY_BASE_URL),
        default_headers={"x-portkey-api-key": api_key},
        max_retries=3,
        timeout=60.0,
    )
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))


@lru_cache(maxsize=1)
def get_agent() -> Agent[ShopDeps, ChatReply]:
    """Built once on the first chat, so the shop still serves products without an API key."""
    agent = Agent(
        make_model(),
        deps_type=ShopDeps,
        output_type=ChatReply,
        instructions=PROMPT_PATH.read_text(encoding="utf-8"),
        model_settings=MODEL_SETTINGS,
        retries=2,
    )

    @agent.instructions
    def session_context(ctx: RunContext[ShopDeps]) -> str:
        """Per-request facts that come from the server (session cookie + DB), not from the shopper's text."""
        d = ctx.deps
        lines = ["## This session"]
        if d.user_id:
            lines.append(
                f"- The shopper is logged in as {d.user_name} (first name {d.user_first_name}, email {d.user_email}). "
                "Earlier messages in this conversation are their saved chat history from past visits."
            )
        else:
            lines.append("- The shopper is a guest (not logged in). You don't know their name or email.")
        lines.append(f"- Current page: `{d.page_path or '/'}`.")
        if d.viewing_product_id:
            product = tools.page_product(d.db_path, d.viewing_product_id)
            if product:
                lines.append(
                    f"- They have the product page for **{product.name}** open "
                    f"(product_id `{product.product_id}`, {product.garment_type}, colors: {', '.join(product.colors)}). "
                    "\"This\", \"it\", or \"this one\" means this product unless they say otherwise."
                )
        return "\n".join(lines)

    @agent.tool
    def get_customer_profile(ctx: RunContext[ShopDeps]) -> CustomerProfile:
        """Look up the logged-in shopper's own account: name, email, member-since date, saved chat count.

        Use when they ask "who am I logged in as?", "what email do you have for me?", etc.
        Returns logged_in=false for guests. Only ever describes the current shopper.
        """
        if not ctx.deps.user_id:
            return CustomerProfile(logged_in=False)
        return tools.customer_profile(ctx.deps.db_path, ctx.deps.user_id)

    @agent.tool
    def search_catalogue(
        ctx: RunContext[ShopDeps],
        query: str,
        limit: int = 8,
        min_price: float | None = None,
        max_price: float | None = None,
        category: Literal["hoodies", "crewnecks", "quarter-zips", "tees", "long-sleeve", "outerwear"] | None = None,
    ) -> SearchResults:
        """Search the Campus Customs catalogue by keywords, optionally within a category and/or price range.

        Matches product names, garment types, colors, tags, and descriptions.
        Use this before naming or recommending any product. For price limits
        ("under $60", "between $40 and $70") ALWAYS pass min_price / max_price:
        they filter the whole catalogue before the result limit is applied.
        For a whole apparel type ("what hoodies do you have?") pass `category` (query can be ''):
        it is exact, unlike keywords. Each hit includes its DB price, so no separate price call is
        needed for search results. If total_matches > len(results), more matched than were returned.

        Args:
            query: what the shopper wants, e.g. 'navy hoodie', 'Branford quarter-zip', 'Harvard Yale tee'.
            limit: max results to return (1-30). Use 30 when filling page_results for a browse request.
            min_price: lowest price in USD to include, if the shopper gave one.
            max_price: highest price in USD to include, if the shopper gave one.
            category: hoodies, crewnecks, quarter-zips, tees (T-shirts), long-sleeve, or outerwear (jackets & fleece).
        """
        found = tools.search_products(
            ctx.deps.db_path,
            query,
            limit=max(1, min(limit, MAX_SEARCH_RESULTS)),
            min_price=min_price,
            max_price=max_price,
            category=category,
        )
        ctx.deps.seen_product_ids.extend(h.product_id for h in found.results)
        return found

    @agent.tool
    def get_product_description(ctx: RunContext[ShopDeps], product_id: str) -> ProductDescription:
        """Look up a product's full description, garment type, and available colors.

        Use for "what does it look like", "what color is it", "is it a pullover or zip", etc.

        Args:
            product_id: exact product_id from search_catalogue (or the open product page).
        """
        with unknown_product_retry():
            info = tools.get_product_description(ctx.deps.db_path, product_id)
        ctx.deps.seen_product_ids.append(info.product_id)
        return info

    @agent.tool
    def get_product_price(ctx: RunContext[ShopDeps], product_ids: list[str]) -> list[ProductPrice]:
        """Look up the current price (USD) of one or more products from the database.

        Call this for EVERY price you mention: single prices, comparisons, "under $50", cheapest/most expensive.

        Args:
            product_ids: exact product_ids from search_catalogue, up to 12.
        """
        with unknown_product_retry():
            prices = tools.get_product_prices(ctx.deps.db_path, product_ids[:12])
        ctx.deps.seen_product_ids.extend(p.product_id for p in prices)
        return prices

    @agent.tool
    def check_stock(ctx: RunContext[ShopDeps], product_id: str, size: str | None = None) -> StockReport:
        """Look up live inventory for a product, by size.

        Call this for EVERY availability question ("is it in stock", "do you have a medium", "how many left").
        Pass `size` when the shopper names one (accepts XS, S, M, L, XL, XXL or words like 'medium');
        leave it out to get every size.

        Args:
            product_id: exact product_id from search_catalogue (or the open product page).
            size: the size the shopper asked about, if any.
        """
        with unknown_product_retry():
            report = tools.check_stock(ctx.deps.db_path, product_id, size)
        ctx.deps.seen_product_ids.append(report.product_id)
        return report

    return agent


@contextmanager
def unknown_product_retry():
    """A bad product_id becomes a ModelRetry so the agent searches again instead of guessing."""
    try:
        yield
    except tools.UnknownProduct as e:
        raise ModelRetry(
            f"No product with product_id '{e}'. Use search_catalogue to find the exact product_id."
        ) from None


def to_model_history(history: list[HistoryMessage]) -> list[ModelMessage]:
    """Turn the widget's recent messages into PydanticAI message history."""
    messages: list[ModelMessage] = []
    for m in history:
        if m.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=m.content)]))
        else:
            text = m.content
            if m.product_ids:
                text += f"\n[Product cards shown: {', '.join(m.product_ids)}]"
            if m.page_product_ids:
                text += f"\n[Products put on the page: {', '.join(m.page_product_ids)}]"
            messages.append(ModelResponse(parts=[TextPart(content=text)]))
    return messages


async def run_chat(
    message: str,
    history: list[HistoryMessage],
    user: dict | None = None,
    page: PageContext | None = None,
) -> ChatResponse:
    """One chat turn. `user` is auth.public_user() from the session cookie (None for guests)."""
    page = page or PageContext()
    viewing_product_id = page.product_id
    deps = ShopDeps(
        db_path=DB_PATH,
        user_id=user["id"] if user else None,
        user_first_name=user["first_name"] if user else None,
        user_name=user["name"] if user else None,
        user_email=user["email"] if user else None,
        page_path=page.path,
        viewing_product_id=viewing_product_id,
    )
    # Problem 12: every turn appends one entry to output/audit_trail.json, whatever the outcome.
    entry = new_audit_entry(
        user_id=deps.user_id, page_path=page.path, product_id=viewing_product_id,
        message=message, model=MODEL_NAME, history_messages=len(history),
    )
    started = time.perf_counter()
    try:
        result = await get_agent().run(
            message,
            deps=deps,
            message_history=to_model_history(history),
            usage_limits=USAGE_LIMITS,
        )
    except ModelHTTPError as e:
        if e.status_code == 400 and "content_filter" in str(e.body):
            log.warning("Message blocked by the provider content filter")
            entry.stop_reason, entry.reply = "content_filter", _short(FILTERED_REPLY, 200)
            _finish_audit(entry, started)
            return ChatResponse(reply=FILTERED_REPLY)
        entry.stop_reason, entry.error = "error", _short(f"ModelHTTPError {e.status_code}")
        _finish_audit(entry, started)
        raise
    except UsageLimitExceeded as e:
        entry.stop_reason, entry.error = "usage_limit", _short(str(e))
        _finish_audit(entry, started)
        raise
    except (Exception, asyncio.CancelledError) as e:  # cancelled = client left or server reloading
        entry.stop_reason, entry.error = "error", _short(f"{type(e).__name__}: {e}")
        _finish_audit(entry, started)
        raise
    reply = result.output

    # Only show cards for products the agent actually looked up (this turn, earlier
    # turns, or the open page). product_cards() then drops any id not in the DB.
    allowed = set(deps.seen_product_ids) | {
        pid for m in history for pid in (*m.product_ids, *m.page_product_ids)
    }
    if viewing_product_id:
        allowed.add(viewing_product_id)

    def vetted(product_ids: list[str], cap: int) -> list[str]:
        return list(dict.fromkeys(pid for pid in product_ids if pid in allowed))[:cap]

    # Page results: the API contract that updates the website (Problem 7).
    page_results = None
    if reply.page_results:
        cards = tools.product_cards(DB_PATH, vetted(reply.page_results.product_ids, MAX_PAGE_RESULTS))
        if cards:
            page_results = PageResultsOut(title=reply.page_results.title, total=len(cards), products=cards)

    chat_ids = [] if page_results else vetted(reply.product_ids, MAX_CARDS)
    response = ChatResponse(
        reply=reply.reply,
        products=tools.product_cards(DB_PATH, chat_ids),
        page_results=page_results,
    )

    entry.tool_calls, entry.finish_reason = _tool_calls_from(result.new_messages())
    entry.tool_calls = [c for c in entry.tool_calls if c.tool != "final_result"]
    entry.reply = _short(response.reply, 200)
    entry.product_cards = len(response.products)
    if page_results:
        entry.page_results = f"{page_results.title} ({page_results.total})"
    usage = result.usage() if callable(result.usage) else result.usage
    entry.requests = usage.requests
    entry.input_tokens = usage.input_tokens or 0
    entry.output_tokens = usage.output_tokens or 0
    entry.cache_read_tokens = getattr(usage, "cache_read_tokens", 0) or 0
    _finish_audit(entry, started)
    return response


def _finish_audit(entry, started: float) -> None:
    entry.duration_ms = round((time.perf_counter() - started) * 1000)
    try:
        append_audit(entry)
    except Exception:  # the audit log must never break a shopper's chat
        log.exception("Could not write audit entry")


# ---------- audit trail (Problem 12) ----------
# output/audit_trail.json is a JSON array. Every chat turn appends one AuditEntry; entries are never
# removed or rewritten, and the file is never reset between runs. Writes are serialized with a lock and
# done atomically (temp file + replace), so the file stays valid JSON even if the server stops mid-write.
# Privacy: entries hold the user id only (no email/name), redacted message text, and short summaries.

AUDIT_PATH = BACKEND_DIR.parent / "output" / "audit_trail.json"
AUDIT_SHORT = 160  # max characters for args / results in the log
_audit_lock = threading.Lock()

# 12-19 digits, optionally separated by spaces or dashes: looks like a payment card number.
CARD_RE = re.compile(r"\b\d(?:[ -]?\d){11,18}\b")


def redact(text: str) -> str:
    """Mask anything that looks like a payment card number (used for the model, chat history, and the log)."""
    return CARD_RE.sub("[redacted number]", text)


def _short(value, limit: int = AUDIT_SHORT) -> str:
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


def _summarize_result(content) -> str:
    """A readable one-liner for common tool results, else truncated JSON."""
    if isinstance(content, SearchResults):
        ids = [h.product_id for h in content.results]
        return _short(f"{content.total_matches} matches, {len(ids)} returned: {', '.join(ids)}")
    if isinstance(content, StockReport):
        sizes = ", ".join(f"{s.size}={s.quantity}" for s in content.sizes)
        return _short(f"{content.product_id}: {sizes} (requested {content.requested_size or 'all'})")
    if isinstance(content, list) and content and isinstance(content[0], ProductPrice):
        return _short(", ".join(f"{p.product_id}=${p.price:.2f}" for p in content))
    return _short(content)


def _tool_calls_from(messages: list[ModelMessage]) -> tuple[list[AuditToolCall], str | None]:
    """Pair each ToolCallPart with its ToolReturnPart / RetryPromptPart by tool_call_id."""
    calls: dict[str, AuditToolCall] = {}
    order: list[str] = []
    finish_reason = None
    for m in messages:
        if isinstance(m, ModelResponse):
            finish_reason = getattr(m, "finish_reason", None) or finish_reason
        for part in m.parts:
            if isinstance(part, ToolCallPart):
                calls[part.tool_call_id] = AuditToolCall(tool=part.tool_name, args=_short(part.args_as_dict()))
                order.append(part.tool_call_id)
            elif isinstance(part, ToolReturnPart) and part.tool_call_id in calls:
                calls[part.tool_call_id].result = _summarize_result(part.content)
            elif isinstance(part, RetryPromptPart) and part.tool_call_id in calls:
                calls[part.tool_call_id].retried = True
                calls[part.tool_call_id].result = _short(part.content)
    return [calls[i] for i in order], (str(finish_reason) if finish_reason else None)


def new_audit_entry(*, user_id: int | None, page_path: str, product_id: str | None, message: str,
                    model: str, history_messages: int, stop_reason: str = "final_result") -> AuditEntry:
    return AuditEntry(
        id=uuid.uuid4().hex[:12],
        time=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        user=f"user:{user_id}" if user_id else "guest",
        page=page_path + (f" [{product_id}]" if product_id else ""),
        message=_short(message, 200),
        model=model,
        history_messages=history_messages,
        stop_reason=stop_reason,
    )


def append_audit(entry: AuditEntry) -> None:
    """Append one entry. Never truncates: existing entries are read back and kept."""
    with _audit_lock:
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
