# Campus Customs — Usability Improvements (Problem 9)

Four improvements, two on the front end and two in the agent/backend. Each
one says **what was added**, **why it helps** a Campus Customs shopper or the
business, and **where to see it** in the running app (site
http://localhost:5174, API http://localhost:8000).

| # | Improvement | Where to see it |
|---|---|---|
| F1 | Ivy-League "preppy" redesign | Every page: ribbon, crest, serif headlines, card hover, footer |
| F2 | Shop by apparel type | Nav **Shop ▾** menu, Home "Find your fit" tiles, Products tabs + sort, breadcrumbs, "More Hoodies" row |
| B1 | Cheaper, leaner agent turns | Chat replies; `backend/agent.py` `MODEL_SETTINGS`; `output/bench_agent.json` |
| B2 | Faster page loads | `GET /api/categories`; gzip + cache headers in DevTools/curl; one catalogue fetch per visit |

---

## Front end

### F1. Ivy-League "preppy" redesign

**What I added**
- **Classic serif typography.** Headlines, product names, prices, and the
  brand use *Cormorant Garamond* (an old-style serif in the spirit of
  collegiate engraving), paired with *Inter* for body text. The hero reads
  "Classic Yale style, made for *…*", with the italic accent in light Yale blue.
- **A crest monogram.** An SVG shield with a "CC" monogram (`components/Crest.tsx`)
  appears in the nav and footer. It is drawn in code, so it costs no image download.
- **An announcement ribbon** above the nav, in small caps: "New Haven,
  Connecticut ✦ Bulldog apparel for every generation ✦ Ask our assistant anytime".
- **Ornaments.** ✦ rule ornaments between sections. (In Problem 10 the hero's
  pinstripes were replaced by the fall-on-campus backdrop.)
- **Refined product cards.** Photos zoom gently on hover, and a frosted
  "View details →" pill slides up so it's obvious the card opens the full page.
- **An elegant footer.** Crest, a Shop column listing every apparel type, an
  account column, and an italic serif sign-off ("Made for Bulldogs, worn for life").
- It stays inside the course style rules (AGENTS.md): dark background,
  white/ivory text. *Problem 10 update: the pink accents
  were replaced with Yale blue & white; see `output/design.md`.*

**Why it helps**
- Campus Customs sells to Yale students, alumni, and parents. A storefront
  that looks like a heritage collegiate outfitter, rather than a generic demo,
  builds trust and justifies $58–$98 price points.
- The hover pill and crest-led branding make the site easier to read at a
  glance: what's clickable, where you are, and whose shop this is.

**See it:** any page. The ribbon, crest, and serif type are on every
page. Hover a product card on `/products` to see the "View details →" pill.
The footer is at the bottom of every page.

### F2. Shop by apparel type (category navigation)

**What I added**
- **Six clean aisles.** The database's 22 messy `garment_type` values
  ("short-sleeve T-shirt", "short-sleeve t-shirt", "hooded pullover
  sweatshirt", …) are mapped to **Hoodies (27), Crewnecks (29), Quarter-Zips
  (11), T-Shirts (25), Long Sleeve (2), Jackets & Fleece (8)**
  (`tools.category_for`).
- **"Shop ▾" menu in the nav.** A dropdown with each apparel type's photo
  and style count, plus "View all 102". It opens on hover or click and closes
  on Escape, an outside click, or navigation.
- **"Find your fit" tiles on Home.** Six photo tiles, each linking straight
  to its aisle.
- **Category tabs and sorting on Products.**
  - Tabs: All · Hoodies · Crewnecks · … with counts.
  - Sort: Featured / Price low→high / Price high→low / Most in stock.
  - Both are kept in the URL (`/products?category=hoodies&sort=price-asc`),
    so views are shareable and work with Back.
- **Breadcrumbs.** `Home / Shop / Hoodies / Yale Sports Hoodie Tennis` on
  product pages, and `Home / Shop / Quarter-Zips` on aisle pages.
- **"More Hoodies" row** on every product page: four more items from the
  same aisle (best-stocked first), plus "All 27 hoodies →".
- The footer's Shop column links to each aisle too.

**Why it helps**
- Shoppers think in garment types ("I want a quarter-zip"), not in 102
  unsorted products. Any aisle is now **one click from any page**, and
  sorting by price answers "what's the cheapest hoodie?" without the chat.
- Breadcrumbs and the "More …" row keep shoppers moving between related
  items instead of bouncing back to the full grid. More items viewed means
  more chances to buy.

**See it:**
- Hover **Shop ▾** in the nav, then pick Quarter-Zips. You'll see 11 styles,
  the breadcrumb, and the active tab.
- Switch to the **Hoodies** tab and choose **Price: low to high**. The two
  $45.00 hoodies come first.
- Open any product to see the breadcrumb and the **More Hoodies** row at the bottom.

---

## Agent / backend

### B1. Cheaper, leaner agent turns (same low-cost model, fewer and smaller calls)

**What I added**
- **Kept the cost-efficient model.** The agent stays on `gpt-5.6-luna`, the
  low-cost model this course standardizes on (AGENTS.md). I didn't switch to
  a model whose pricing I couldn't verify. Instead, every turn now uses that
  model more efficiently.
- **Lean model settings** (`agent.MODEL_SETTINGS`):
  - `openai_reasoning_effort="low"`: shop Q&A needs lookups, not deep reasoning.
  - `openai_text_verbosity="low"`: matches the prompt's short-reply voice.
  - `max_tokens=1500`: a hard cap so no reply can run away with output tokens.
  - `openai_prompt_cache_key`: the ~6k-token system prompt and tool
    definitions are identical on every call, so the provider serves them from
    its prompt cache (cached input is billed at a discount).
- **Fewer round trips.** `search_catalogue` hits now include each product's
  database **price** and **category**. The agent no longer needs a separate
  `get_product_price` call after a search; that was 1 to 3 extra model calls
  per browse or price question. It also gets an exact `category` filter, so
  "what crewnecks do you have?" is a single precise call instead of fuzzy keywords.
- **Shorter memory window.** History sent to the model was cut from 20 to 12
  messages. Older turns cost tokens on every call but rarely matter.
- **A cost guard.** `/api/chat` is rate-limited to 20 messages per minute
  per logged-in shopper (or per IP for guests), with a friendly 429. A script
  or stuck client can't run up the model bill.
- The prompt was updated to match: quote `price` from search hits, use
  `category` for browsing, and don't repeat lookups.

**Measured** with `backend/bench_agent.py`: 6 fresh questions (price, stock
by size, stock count, colors on a product page, a whole category, and a
price-filtered category), each checked against the database. Full rows are in
`output/bench_agent.json`.

| Per chat turn (average) | Before (Problem 8) | After (Problem 9) | Change |
|---|---|---|---|
| Response time | 6.34 s | **4.23 s** | **−33%** |
| Model calls | 3.00 | **2.33** | −22% |
| Input tokens | 10,143 | **7,929** | −22% |
| …of which served from prompt cache | n/a | **~94%** (≈5,970 of 6,330 per call) | cheaper input |
| Output tokens | 315 | **201** | −36% |
| Correct vs. database | 6/6 | **6/6** | no accuracy loss |

The biggest single win: "Show me tees under $35" went from **5 model calls /
21,830 input tokens / 12.7 s** to **2 calls / 7,583 tokens / 3.6 s**.
The Problem 6 (price and stock) and Problem 7 (page results) test suites were
rerun after the change, and every check still matches the database.

**Why it helps**
- **Business:** about a fifth fewer tokens, most of the input billed at the
  cached rate, a third fewer output tokens, and a rate limit. Each
  conversation costs less, and the cost can't spike.
- **Shopper:** answers arrive about a third faster, with the same accuracy.

**See it:** ask the chat "What crewnecks do you have?" or "Show me tees
under $35". Results land on the page in a few seconds. The settings are in
`backend/agent.py` (`MODEL_SETTINGS`), and the numbers are in `output/bench_agent.json`.

### B2. Faster page loads

**What I added**
- **An in-memory catalogue cache** (`tools.catalogue()`, 5-minute TTL).
  Product info is parsed once instead of on every request and every agent
  search. **Stock is never cached**; it is still read live from `inventory`.
- **Gzip compression** on API responses (`GZipMiddleware`).
- **Browser caching for product photos.** `/media/...` now sends
  `Cache-Control: public, max-age=86400`, so returning visitors don't
  re-download the 3.6 MB of product images.
- **One catalogue download per visit.** The front end shares a single
  `fetchProducts()` / `fetchCategories()` request across Home, Products,
  product pages, the nav menu, and the footer, instead of re-fetching on every page.
- **A new `GET /api/categories` endpoint** returning the six aisles with
  counts and a cover image (it powers the Shop menu and tiles in F2).

**Measured**

| | Before | After |
|---|---|---|
| `/api/products` bytes on the wire | 62,543 | **8,598 (−86%)** |
| Server work per `/api/products` call | 3.66 ms | **1.96 ms (−46%)** |
| Agent `search_catalogue` work | 3.68 ms | **0.97 ms (−74%)** |
| Product photo `Cache-Control` | none (re-validated every visit) | **public, max-age=86400** |
| Catalogue requests while browsing Home → Shop menu → Quarter-Zips → Hoodies → product page | one per page | **1 total** (verified in the browser's network log) |

(Over localhost the total request time stays in the single-digit to
low-double-digit milliseconds either way. The byte savings and caching are
what matter on a phone over campus Wi-Fi or cellular.)

**Why it helps**
- **Shopper:** product grids appear faster, especially on mobile. Moving
  between pages feels instant because the catalogue and photos are already loaded.
- **Business:** less bandwidth and server work per visitor, and faster agent
  searches.

**See it:**
- Run `curl -s -D - -o NUL http://localhost:8000/media/products/boola-boola-t-shirt.jpg`.
  The response shows `cache-control: public, max-age=86400`.
- Run `curl -s http://localhost:8000/api/categories` to see the six aisles.
- In browser DevTools → Network, `/api/products` is fetched once while you browse.
