"""Tools the Campus Customs agent can call. Plain functions over campus_customs.db.

agent.py registers these with PydanticAI. Each one reads the database with a
parameterized query and returns typed results from models.py, so the agent only
ever sees real catalogue data.

Problem 5: catalogue search. Problem 6: description, price, and stock lookups.
"""

from __future__ import annotations

import json
import re
import sqlite3
import time
from pathlib import Path

from models import (
    CustomerProfile,
    ProductCard,
    ProductDescription,
    ProductHit,
    ProductPrice,
    SearchResults,
    SizeStock,
    StockReport,
)

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
LOW_STOCK = 5  # same threshold the product page uses for "Only N left"
SIZE_ALIASES = {
    "xs": "XS", "x-small": "XS", "xsmall": "XS", "extra small": "XS", "extra-small": "XS",
    "s": "S", "sm": "S", "small": "S",
    "m": "M", "med": "M", "medium": "M",
    "l": "L", "lg": "L", "large": "L",
    "xl": "XL", "x-large": "XL", "xlarge": "XL", "extra large": "XL", "extra-large": "XL",
    "xxl": "XXL", "2xl": "XXL", "xx-large": "XXL", "xxlarge": "XXL", "2x": "XXL",
    "extra extra large": "XXL", "double xl": "XXL",
}


# Shop categories (Problem 9). garment_type has 22 messy variants; these are the six aisles.
CATEGORIES = {
    "hoodies": "Hoodies",
    "crewnecks": "Crewnecks",
    "quarter-zips": "Quarter-Zips",
    "tees": "T-Shirts",
    "long-sleeve": "Long Sleeve",
    "outerwear": "Jackets & Fleece",
}
CATALOGUE_TTL_SECONDS = 300


def category_for(garment_type: str) -> str:
    """Map a raw garment_type to a category slug. Order matters: 'full-zip hooded sweatshirt' is a hoodie."""
    g = garment_type.lower()
    if "hood" in g:
        return "hoodies"
    if "quarter-zip" in g:
        return "quarter-zips"
    if "t-shirt" in g:
        return "tees"
    if "jacket" in g or "fleece" in g:
        return "outerwear"
    if "long-sleeve" in g:
        return "long-sleeve"
    return "crewnecks"


_catalogue_cache: tuple[float, list[dict]] | None = None


def catalogue(db_path: Path) -> list[dict]:
    """Catalogue rows (product info, not stock) cached in memory for 5 minutes.

    Product info rarely changes; stock is always read live from inventory.
    """
    global _catalogue_cache
    if _catalogue_cache and time.monotonic() - _catalogue_cache[0] < CATALOGUE_TTL_SECONDS:
        return _catalogue_cache[1]
    with connect(db_path) as conn:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
    products = []
    for r in rows:
        p = dict(r)
        p["colors"] = json.loads(p["colors"])
        p["search_tags"] = json.loads(p["search_tags"])
        p["category"] = category_for(p["garment_type"])
        p["image_url"] = f"/media/{p['image_file_path']}"
        products.append(p)
    _catalogue_cache = (time.monotonic(), products)
    return products


class UnknownProduct(LookupError):
    """Raised when a product_id isn't in the catalogue. agent.py turns this into a retry hint."""

# Shopper words mapped to how the catalogue phrases them.
SYNONYMS = {
    "hoodie": ["hoodie", "hooded", "hood"],
    "hoodies": ["hoodie", "hooded", "hood"],
    "tee": ["t-shirt", "tee"],
    "tees": ["t-shirt", "tee"],
    "tshirt": ["t-shirt"],
    "shirt": ["shirt", "t-shirt"],
    "crew": ["crewneck"],
    "sweater": ["sweatshirt", "sweater", "crewneck"],
    "quarterzip": ["quarter-zip", "1/4 zip"],
    "fleece": ["fleece"],
    "jacket": ["jacket"],
    "grey": ["gray", "grey"],
    "gray": ["gray", "grey"],
}
STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "with", "in", "of", "do", "you", "have",
    "any", "some", "me", "show", "i", "want", "looking", "need", "is", "are", "my", "your",
    "under", "below", "over", "above", "than", "less", "more", "cheap", "price", "dollars",
}


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _terms(text: str) -> list[list[str]]:
    """Split a query into terms; each term is a list of acceptable spellings."""
    words = re.findall(r"[a-z0-9/'-]+", text.lower().replace("t shirt", "tshirt").replace("quarter zip", "quarterzip"))
    return [SYNONYMS.get(w, [w.rstrip("s") if len(w) > 3 else w]) for w in words if w not in STOPWORDS]


def search_products(
    db_path: Path,
    query: str,
    limit: int = 8,
    min_price: float | None = None,
    max_price: float | None = None,
    category: str | None = None,
) -> SearchResults:
    """Rank catalogue items by how many query terms appear in their name, type, colors, tags, or description.

    Products matching every term win; partial matches are a fallback when nothing matches them all.
    Price and category filters are applied over the whole catalogue *before* ranking and the limit,
    so "hoodies under $60" can't miss a match that would have ranked below the cut-off.
    """
    terms = _terms(query)
    rows = [
        p for p in catalogue(db_path)
        if (min_price is None or p["price"] >= min_price)
        and (max_price is None or p["price"] <= max_price)
        and (category is None or p["category"] == category)
    ]

    scored = []
    for r in rows:
        title = f"{r['name']} {r['garment_type']}".lower()
        body = " ".join([r["description"], *r["colors"], *r["search_tags"]]).lower()
        score = matched = 0
        for spellings in terms:
            if any(s in title for s in spellings):
                score += 3
                matched += 1
            elif any(s in body for s in spellings):
                score += 1
                matched += 1
        if score or not terms:
            scored.append((matched == len(terms), score, r["name"], r))

    # "navy hoodies" should mean navy AND hoodie: keep only products matching every
    # term when any exist, and fall back to partial matches only when none do.
    if any(full for full, *_ in scored):
        scored = [t for t in scored if t[0]]
    scored.sort(key=lambda t: (-t[1], t[2]))
    return SearchResults(
        total_matches=len(scored),
        results=[
            ProductHit(
                product_id=r["product_id"],
                name=r["name"],
                category=r["category"],
                garment_type=r["garment_type"],
                colors=r["colors"],
                price=r["price"],
            )
            for *_, r in scored[:limit]
        ],
    )


def _catalogue_row(conn: sqlite3.Connection, product_id: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
    if row is None:
        raise UnknownProduct(product_id)
    return row


def get_product_description(db_path: Path, product_id: str) -> ProductDescription:
    with connect(db_path) as conn:
        row = _catalogue_row(conn, product_id)
    return ProductDescription(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        colors=json.loads(row["colors"]),
    )


def get_product_prices(db_path: Path, product_ids: list[str]) -> list[ProductPrice]:
    """Prices for one or more products, in the order asked. Unknown ids raise UnknownProduct."""
    with connect(db_path) as conn:
        rows = [_catalogue_row(conn, pid) for pid in product_ids]
    return [ProductPrice(product_id=r["product_id"], name=r["name"], price=r["price"]) for r in rows]


def normalize_size(size: str) -> str | None:
    """'medium' -> 'M', '2XL' -> 'XXL'. Returns the cleaned input upper-cased if it isn't a known alias."""
    key = size.strip().lower().replace("size", "").strip()
    return SIZE_ALIASES.get(key) or (key.upper() or None)


def _status(quantity: int) -> str:
    if quantity <= 0:
        return "sold_out"
    return "low_stock" if quantity <= LOW_STOCK else "in_stock"


def check_stock(db_path: Path, product_id: str, size: str | None = None) -> StockReport:
    """Live inventory for a product: one size if asked, otherwise every size."""
    with connect(db_path) as conn:
        row = _catalogue_row(conn, product_id)
        inv = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchall()
    stock = sorted(
        (SizeStock(size=r["size"], quantity=r["quantity"], status=_status(r["quantity"])) for r in inv),
        key=lambda s: SIZE_ORDER.index(s.size) if s.size in SIZE_ORDER else 99,
    )
    requested = normalize_size(size) if size else None
    shown = [s for s in stock if s.size == requested] if requested else stock
    return StockReport(
        product_id=row["product_id"],
        name=row["name"],
        requested_size=requested,
        requested_size_offered=(bool(shown) if requested else None),
        sizes=shown,
        sizes_in_stock=[s.size for s in stock if s.quantity > 0],
        sold_out_sizes=[s.size for s in stock if s.quantity <= 0],
        total_in_stock=sum(s.quantity for s in stock),
    )


def page_product(db_path: Path, product_id: str) -> ProductDescription | None:
    """The product on the page the shopper has open, for the agent's context (None if the id is bogus)."""
    try:
        return get_product_description(db_path, product_id)
    except UnknownProduct:
        return None


def customer_profile(db_path: Path, user_id: int) -> CustomerProfile:
    """The current shopper's own profile. Selects named columns only; password_hash is never read."""
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT first_name, last_name, name, email, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        saved = conn.execute("SELECT COUNT(*) FROM chat_messages WHERE user_id = ?", (user_id,)).fetchone()[0]
    if row is None:
        return CustomerProfile(logged_in=False)
    return CustomerProfile(
        logged_in=True,
        first_name=row["first_name"],
        last_name=row["last_name"],
        name=row["name"],
        email=row["email"],
        member_since=row["created_at"][:10],
        saved_messages=saved,
    )


def product_cards(db_path: Path, product_ids: list[str]) -> list[ProductCard]:
    """Build product cards for ids that really exist, keeping the given order (not an agent tool)."""
    if not product_ids:
        return []
    with connect(db_path) as conn:
        placeholders = ",".join("?" * len(product_ids))
        rows = conn.execute(
            f"SELECT product_id, name, garment_type, price, image_file_path, description, colors FROM catalogue "
            f"WHERE product_id IN ({placeholders})",
            product_ids,
        ).fetchall()
    by_id = {r["product_id"]: r for r in rows}
    return [
        ProductCard(
            product_id=pid,
            name=by_id[pid]["name"],
            garment_type=by_id[pid]["garment_type"],
            price=by_id[pid]["price"],
            image_url=f"/media/{by_id[pid]['image_file_path']}",
            description=by_id[pid]["description"],
            colors=json.loads(by_id[pid]["colors"]),
        )
        for pid in product_ids
        if pid in by_id
    ]
