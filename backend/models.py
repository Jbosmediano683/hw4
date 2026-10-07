"""Pydantic / PydanticAI structured types for the Campus Customs chatbot."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

MAX_MESSAGE_CHARS = 1000
MAX_HISTORY_MESSAGES = 12  # Problem 9: was 20; older turns cost tokens on every call
MAX_PAGE_RESULTS = 30  # most product cards the chat can put on the page at once


# ---------- agent dependencies ----------

@dataclass
class ShopDeps:
    """Passed to every tool call. The shopper comes from the session cookie, never from chat text."""

    db_path: Path
    # who is chatting (all None for guests) - from auth.public_user(), never password_hash
    user_id: int | None = None
    user_first_name: str | None = None
    user_name: str | None = None
    user_email: str | None = None
    # where they are on the site, from the widget's page_context
    page_path: str | None = None
    viewing_product_id: str | None = None
    # product_ids that tools returned during this run, used to vet the agent's product cards
    seen_product_ids: list[str] = field(default_factory=list)


# ---------- tool return types ----------

class CustomerProfile(BaseModel):
    """get_customer_profile: the logged-in shopper's own account details (never the password hash)."""

    logged_in: bool
    first_name: str | None = None
    last_name: str | None = None
    name: str | None = None
    email: str | None = None
    member_since: str | None = Field(default=None, description="Account creation date, YYYY-MM-DD.")
    saved_messages: int = Field(default=0, description="How many chat messages we have stored for them.")


class ProductHit(BaseModel):
    """One catalogue search result.

    Colors let browse results be narrowed ("just the navy ones"); price (straight from the DB) lets the agent
    answer price questions and price filters without a second round trip (Problem 9).
    """

    product_id: str
    name: str
    category: str
    garment_type: str
    colors: list[str]
    price: float


class SearchResults(BaseModel):
    """search_catalogue: ranked hits plus how many matched in total, so the agent knows if the list was cut short."""

    total_matches: int
    results: list[ProductHit]


class ProductDescription(BaseModel):
    """get_product_description: what the item looks like. No price or stock, so each fact has one source."""

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]


class ProductPrice(BaseModel):
    """get_product_price: the catalogue price, exactly as stored."""

    product_id: str
    name: str
    price: float
    currency: Literal["USD"] = "USD"


SizeStatus = Literal["in_stock", "low_stock", "sold_out"]


class SizeStock(BaseModel):
    size: str
    quantity: int
    status: SizeStatus  # low_stock means 1-5 left, matching the product page


class StockReport(BaseModel):
    """check_stock: live inventory for one product, either all sizes or the one the shopper asked about."""

    product_id: str
    name: str
    requested_size: str | None = Field(
        default=None, description="Normalized size the shopper asked about (XS, S, M, L, XL, XXL), if any."
    )
    requested_size_offered: bool | None = Field(
        default=None, description="False if the shop doesn't make this product in the requested size at all."
    )
    sizes: list[SizeStock] = Field(description="The requested size only, or every size from XS to XXL.")
    sizes_in_stock: list[str]
    sold_out_sizes: list[str]
    total_in_stock: int


# ---------- agent output ----------

class PageResults(BaseModel):
    """Search results the agent wants rendered on the website itself (Problem 7)."""

    title: str = Field(
        max_length=60,
        description="Short heading for the results, e.g. 'Hoodies', 'Branford College gear', 'Tees under $40'.",
    )
    product_ids: list[str] = Field(
        description=f"Every matching product_id from search_catalogue, best first, up to {MAX_PAGE_RESULTS}.",
    )


class ChatReply(BaseModel):
    """What the agent must return each turn."""

    reply: str = Field(
        description=(
            "The message shown to the shopper, in the Campus Customs voice. Plain text; "
            "**bold** and '- ' bullet lists are allowed. Keep it short."
        )
    )
    product_ids: list[str] = Field(
        default_factory=list,
        description=(
            "product_ids to show as product cards under the reply, most relevant first, max 4. "
            "Only use ids a tool returned. Leave empty if no product is relevant, "
            "and leave empty when page_results is set (the page already shows them)."
        ),
    )
    page_results: PageResults | None = Field(
        default=None,
        description=(
            "Set when the shopper is browsing a type or group of items ('what hoodies do you have?', "
            "'show me Branford stuff', 'tees under $40'): the website shows these as product cards on the page. "
            "Leave null for questions about one specific product, price, or stock."
        ),
    )


# ---------- HTTP API types ----------

class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)
    product_ids: list[str] = Field(default_factory=list, max_length=8)
    page_product_ids: list[str] = Field(default_factory=list, max_length=MAX_PAGE_RESULTS)


class PageContext(BaseModel):
    """Where the shopper is on the site when they send a message."""

    path: str = Field(default="/", max_length=200)
    product_id: str | None = Field(default=None, max_length=200, description="Set on /products/:id pages.")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    # Only used for guests; logged-in history is read from the database.
    history: list[HistoryMessage] = Field(default_factory=list, max_length=MAX_HISTORY_MESSAGES)
    page_context: PageContext = Field(default_factory=PageContext)


class ProductCard(BaseModel):
    """A product card (in the chat or on the page). Built from the database, never from model text."""

    product_id: str
    name: str
    garment_type: str
    price: float
    image_url: str
    description: str
    colors: list[str]


class PageResultsOut(BaseModel):
    """The page_results half of the API contract: what the front end renders on the Products page."""

    title: str
    total: int
    products: list[ProductCard]


class ChatResponse(BaseModel):
    reply: str
    products: list[ProductCard] = Field(default_factory=list)
    page_results: PageResultsOut | None = None


class StoredMessage(BaseModel):
    """One saved chat message, as GET /api/chat/history returns it to the widget."""

    role: Literal["user", "assistant"]
    content: str
    products: list[ProductCard] = Field(default_factory=list)
    page_results: PageResultsOut | None = None
    created_at: str


class ChatHistoryResponse(BaseModel):
    messages: list[StoredMessage]


# ---------- audit trail (Problem 12) ----------

StopReason = Literal["final_result", "content_filter", "usage_limit", "rate_limited", "error"]


class AuditToolCall(BaseModel):
    """One tool call inside an agent run: what was asked and a short summary of what came back."""

    tool: str
    args: str = Field(description="Arguments as compact JSON, truncated.")
    result: str = Field(default="", description="Short summary of the tool's return value, truncated.")
    retried: bool = Field(default=False, description="True if the tool raised ModelRetry (e.g. unknown product_id).")


class AuditEntry(BaseModel):
    """One line of output/audit_trail.json: a single chat turn through the agent loop."""

    id: str
    time: str = Field(description="UTC ISO-8601 timestamp when the turn started.")
    user: str = Field(description="'user:<id>' or 'guest'. Never an email or name.")
    page: str = Field(description="Page path the shopper was on, plus the product_id if any.")
    message: str = Field(description="The shopper's message, card-like numbers redacted, truncated.")
    model: str
    history_messages: int
    tool_calls: list[AuditToolCall] = Field(default_factory=list)
    stop_reason: StopReason
    finish_reason: str | None = Field(default=None, description="Provider finish reason on the last model response.")
    reply: str = Field(default="", description="The agent's reply, truncated.")
    product_cards: int = 0
    page_results: str | None = Field(default=None, description="'<title> (<n>)' when results were put on the page.")
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    duration_ms: int = 0
    error: str | None = None
