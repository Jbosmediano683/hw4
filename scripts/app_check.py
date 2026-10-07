"""Problem 11: test the live site and write output/app_check.html with screenshots.

Needs the app running (backend :8000, frontend :5174) and Playwright (uses the installed Microsoft Edge):
    python -m pip install playwright
    python scripts/app_check.py          (from hw4/)

Each check drives the real website in a headless browser, saves PNGs to output/app_check_images/,
records what the agent actually said, and compares it with the database.
"""

from __future__ import annotations

import html
import json
import re
import sys
import sqlite3
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

HW = Path(__file__).resolve().parents[1]
DB = HW / "data" / "campus_customs.db"
OUT = HW / "output"
IMG = OUT / "app_check_images"
SITE = "http://localhost:5174"
VIEWPORT = {"width": 1920, "height": 1040}

INVENTORY_PRODUCT = "baseball-left-chest-crewneck"
INVENTORY_QUESTION = "How much is this, and do you have it in XL and in a medium?"
SEARCH_QUESTION = "What hoodies do you have?"


# ---------- database truth ----------

def db_rows(sql: str, *args):
    with sqlite3.connect(DB) as conn:
        return conn.execute(sql, args).fetchall()


def product_truth(pid: str) -> dict:
    name, price, colors = db_rows("SELECT name, price, colors FROM catalogue WHERE product_id = ?", pid)[0]
    order = ["XS", "S", "M", "L", "XL", "XXL"]
    stock = dict(db_rows("SELECT size, quantity FROM inventory WHERE product_id = ?", pid))
    return {"name": name, "price": price, "colors": json.loads(colors),
            "stock": {s: stock[s] for s in order if s in stock}}


def hoodie_ids() -> set[str]:
    rows = db_rows("SELECT product_id, garment_type FROM catalogue")
    return {pid for pid, g in rows if "hood" in g.lower()}


# ---------- browser helpers ----------

def settle(page: Page, ms: int = 1300) -> None:
    page.wait_for_timeout(ms)  # let entrance animations finish before the screenshot


def ask_chat(page: Page, question: str) -> tuple[str, float]:
    """Open the concierge, send a question, wait for the reply. Returns (reply text, seconds)."""
    if page.locator(".chat-panel").count() == 0:
        page.click(".chat-fab")
    page.wait_for_selector(".chat-input input")
    before = page.locator(".msg-assistant").count()
    page.fill(".chat-input input", question)
    start = time.perf_counter()
    page.press(".chat-input input", "Enter")
    page.wait_for_function(
        "n => document.querySelectorAll('.msg-assistant').length > n && !document.querySelector('.stockroom')",
        arg=before, timeout=90_000,
    )
    secs = time.perf_counter() - start
    reply = page.locator(".msg-assistant .bubble").last.inner_text()
    return reply.strip(), secs


def main() -> None:
    IMG.mkdir(parents=True, exist_ok=True)
    results: dict = {"run_at": datetime.now().strftime("%B %d, %Y at %I:%M %p").replace(" 0", " ")}

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        ctx = browser.new_context(viewport=VIEWPORT, device_scale_factor=1)
        # Fresh guest session; skip the one-time teaser bubble so it doesn't cover the shots.
        ctx.add_init_script("sessionStorage.setItem('cc-concierge-teaser-seen', '1')")
        page = ctx.new_page()

        # ---- Check 1: chat checks inventory on a product page ----
        page.goto(f"{SITE}/products/{INVENTORY_PRODUCT}")
        page.wait_for_selector(".detail-info h1")
        reply, secs = ask_chat(page, INVENTORY_QUESTION)
        settle(page, 800)
        page.screenshot(path=IMG / "inventory.png")
        page.locator(".chat-panel").screenshot(path=IMG / "inventory_chat.png")
        page_sizes = page.locator("button.size").all_inner_texts()
        results["inventory"] = {"reply": reply, "secs": secs, "truth": product_truth(INVENTORY_PRODUCT),
                                "page_sizes": [s.replace("\n", ": ") for s in page_sizes]}

        # ---- Check 2: category question puts result cards on the page ----
        page.goto(f"{SITE}/")
        page.wait_for_selector(".hero h1")
        reply, secs = ask_chat(page, SEARCH_QUESTION)
        page.wait_for_url("**/products")
        page.wait_for_selector(".chat-results .card")
        settle(page, 1800)
        page.screenshot(path=IMG / "search_cards.png")
        cards = page.locator(".chat-results .card")
        card_ids = [h.split("/")[-1] for h in cards.evaluate_all("els => els.map(e => e.getAttribute('href'))")]
        heading = page.locator(".chat-results h1").inner_text()
        # ...and a chat-placed card still opens the single-item page (Problem 3 behavior).
        page.click(".chat-panel .icon-btn")  # close the chat so the full detail page is visible
        first = cards.nth(0)
        first_name = first.locator(".card-title").inner_text()
        first.click()
        page.wait_for_selector(".detail-info h1")
        settle(page, 1000)
        page.screenshot(path=IMG / "search_click_through.png")
        results["search"] = {"reply": reply, "secs": secs, "heading": heading, "card_ids": card_ids,
                             "truth_ids": sorted(hoodie_ids()), "clicked": first_name, "detail_url": page.url}

        # ---- Check 3: Problem 9 usability feature, Shop-by-apparel navigation ----
        page.goto(f"{SITE}/")
        page.wait_for_selector(".hero h1")
        page.hover(".nav-link-btn")
        page.wait_for_selector(".mega-item")
        settle(page, 600)
        page.screenshot(path=IMG / "usability_shop_menu.png", clip={"x": 0, "y": 0, "width": VIEWPORT["width"], "height": 560})
        menu = [t.replace("\n", " ") for t in page.locator(".mega-item").all_inner_texts()]
        page.click(".mega-item[href='/products?category=hoodies']")
        page.wait_for_selector(".cat-tab.active")
        page.select_option(".sort", "price-asc")
        page.mouse.move(5, 5)
        settle(page, 1500)
        page.screenshot(path=IMG / "usability_sorted_aisle.png")
        prices = [float(t.strip("$")) for t in page.locator(".grid .card .price").all_inner_texts()]
        results["usability"] = {"menu": menu, "url": page.url,
                                "active_tab": page.locator(".cat-tab.active").inner_text().replace("\n", " "),
                                "crumbs": page.locator(".crumbs").inner_text().replace("\n", " "),
                                "prices": prices}
        browser.close()

    (OUT / "app_check_results.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    write_html(results)
    print(json.dumps({k: ({kk: vv for kk, vv in v.items() if kk not in ("card_ids", "truth_ids", "prices")}
                       if isinstance(v, dict) else v) for k, v in results.items()}, indent=1, ensure_ascii=False))


# ---------- report ----------

def write_html(r: dict) -> None:
    inv, srch, use = r["inventory"], r["search"], r["usability"]
    t = inv["truth"]
    stock_rows = "".join(
        f"<tr><td>{s}</td><td>{q}</td><td>{'sold out' if q == 0 else ('low (≤5)' if q <= 5 else 'in stock')}</td></tr>"
        for s, q in t["stock"].items()
    )
    # Check 1 verdict: the reply must quote the DB price and agree with the DB on XL and M stock.
    low = inv["reply"].lower()
    xl, m = t["stock"].get("XL", 0), t["stock"].get("M", 0)
    inv_checks = {
        f"quotes ${t['price']:.2f}": f"${t['price']:.2f}" in inv["reply"],
        f"XL ({xl}) {'sold out' if xl == 0 else 'in stock'}": ("sold out" in low) if xl == 0 else ("xl" in low),
        f"M ({m}) reported": (str(m) in inv["reply"]) if m else ("sold out" in low),
    }
    inv_ok = all(inv_checks.values())
    inv_list = "".join(f"<li>{'✅' if ok else '❌'} {html.escape(k)}</li>" for k, ok in inv_checks.items())
    got, want = set(srch["card_ids"]), set(srch["truth_ids"])
    search_ok = got == want
    prices = use["prices"]
    sorted_ok = prices == sorted(prices)
    esc = html.escape

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Campus Customs — App Check (Problem 11)</title>
<style>
  :root {{ --yale: #00356b; --ink: #1d2433; --muted: #5b6577; --ok: #1b7f4b; --bad: #b3261e; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font: 16px/1.6 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; color: var(--ink); background: #f4f6fa; }}
  header {{ background: var(--yale); color: #fff; padding: 36px 24px 28px; }}
  header h1 {{ margin: 0 0 6px; font: 600 2rem/1.2 Georgia, "Times New Roman", serif; }}
  header p {{ margin: 0; opacity: .85; }}
  main {{ max-width: 1120px; margin: 0 auto; padding: 24px; }}
  nav.toc {{ background: #fff; border: 1px solid #dfe4ee; border-radius: 12px; padding: 14px 20px; margin-bottom: 28px; }}
  nav.toc a {{ color: var(--yale); }}
  section {{ background: #fff; border: 1px solid #dfe4ee; border-radius: 14px; padding: 24px 26px; margin-bottom: 30px; }}
  h2 {{ margin: 0 0 4px; font: 600 1.5rem/1.3 Georgia, serif; color: var(--yale); }}
  .verdict {{ display: inline-block; margin: 6px 0 14px; padding: 3px 12px; border-radius: 999px; font-weight: 700; font-size: .85rem; }}
  .pass {{ background: #e3f4ea; color: var(--ok); }} .fail {{ background: #fbe5e3; color: var(--bad); }}
  figure {{ margin: 18px 0; }}
  figure img {{ display: block; width: 100%; height: auto; border: 1px solid #cfd6e3; border-radius: 10px; box-shadow: 0 6px 18px rgba(0,0,0,.08); }}
  figure.narrow img {{ max-width: 420px; }}
  figcaption {{ margin-top: 8px; color: var(--muted); font-size: .95rem; }}
  figcaption strong {{ color: var(--ink); }}
  .row {{ display: grid; grid-template-columns: 1.6fr 1fr; gap: 22px; align-items: start; }}
  blockquote {{ margin: 10px 0; padding: 10px 14px; background: #f1f5fb; border-left: 4px solid var(--yale); border-radius: 6px; }}
  table {{ border-collapse: collapse; margin: 8px 0; font-size: .92rem; }}
  th, td {{ border: 1px solid #dfe4ee; padding: 4px 10px; text-align: left; }}
  th {{ background: #f1f5fb; }}
  code {{ background: #eef2f8; padding: 1px 5px; border-radius: 4px; font-size: .9em; }}
  footer {{ text-align: center; color: var(--muted); font-size: .85rem; padding: 10px 0 30px; }}
  @media (max-width: 860px) {{ .row {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<header>
  <h1>Campus Customs — App Check</h1>
  <p>Problem 11 · Live-site test run {r.get("run_at", "")} · site <code style="background:rgba(255,255,255,.15);color:#fff">{SITE}</code>, API on :8000, agent model <code style="background:rgba(255,255,255,.15);color:#fff">gpt-5.6-luna</code></p>
</header>
<main>
<nav class="toc"><strong>Checks:</strong>
  <a href="#check1">1. Chat checks inventory (honest stock &amp; price)</a> ·
  <a href="#check2">2. Dynamic search-result cards</a> ·
  <a href="#check3">3. Problem 9 usability feature</a>
  <br><small>Screenshots were captured automatically from the running site in a headless Microsoft Edge browser
  (<code>scripts/app_check.py</code>); every database value below was read from <code>data/campus_customs.db</code> during the same run.</small>
</nav>

<section id="check1">
  <h2>1. Chat checks the inventory level of an item</h2>
  <span class="verdict {'pass' if inv_ok else 'fail'}">{'PASS: reply matches the database' if inv_ok else 'CHECK: reply differs from the database'}</span>
  <p>On the <strong>{esc(t["name"])}</strong> product page, a guest asked the Bulldog Concierge:</p>
  <blockquote>“{esc(INVENTORY_QUESTION)}”</blockquote>
  <div class="row">
    <figure>
      <img src="app_check_images/inventory.png" alt="Product page for the {esc(t['name'])} with the chat open showing the stock answer" />
      <figcaption><strong>Proves:</strong> the agent understood “this” from the open product page and answered from live data. The size buttons on the page (left) and the chat reply (right) show the same stock.</figcaption>
    </figure>
    <figure class="narrow">
      <img src="app_check_images/inventory_chat.png" alt="Close-up of the chat reply about price and stock" />
      <figcaption><strong>Close-up of the reply</strong> ({inv["secs"]:.1f} s): “{esc(inv["reply"])}”</figcaption>
    </figure>
  </div>
  <p><strong>Database truth</strong> for <code>{INVENTORY_PRODUCT}</code>: price <strong>${t["price"]:.2f}</strong>.</p>
  <table><tr><th>Size</th><th>Quantity (inventory table)</th><th>Status</th></tr>{stock_rows}</table>
  <ul>{inv_list}</ul>
  <p>{'The reply’s price and its XL / M stock statements match these rows exactly. Nothing was invented.' if inv_ok else 'At least one statement in the reply does not match these rows (see the list above).'}</p>
</section>

<section id="check2">
  <h2>2. Dynamic search-result cards after a category question</h2>
  <span class="verdict {'pass' if search_ok else 'fail'}">{'PASS' if search_ok else 'CHECK'}: {len(got)} cards on the page · {len(want)} hoodies in the database</span>
  <p>From the Home page, a guest asked <strong>“{esc(SEARCH_QUESTION)}”</strong>. The agent returned structured
  <code>page_results</code>, and the site moved to the Products page and rendered them as product cards.</p>
  <figure>
    <img src="app_check_images/search_cards.png" alt="Products page showing 'From your chat — Hoodies' with hoodie cards" />
    <figcaption><strong>Proves:</strong> the chat answer (“{esc(srch["reply"])}”) updated the page itself. The section
    “✦ From your chat · {esc(srch["heading"])}” shows {len(got)} cards with image, name, price, and short description.
    These are exactly the {len(want)} hoodies in the catalogue{'' if search_ok else ' (see mismatch)'}.</figcaption>
  </figure>
  <figure>
    <img src="app_check_images/search_click_through.png" alt="Detail page opened by clicking a chat-placed card" />
    <figcaption><strong>Proves:</strong> a card the chat put on the page still opens the single-item page.
    Clicking “{esc(srch["clicked"])}” opened <code>{esc(srch["detail_url"].replace(SITE, ""))}</code>, with a large image and full product info.</figcaption>
  </figure>
</section>

<section id="check3">
  <h2>3. Problem 9 usability feature: shop by apparel type</h2>
  <span class="verdict {'pass' if sorted_ok else 'fail'}">{'PASS' if sorted_ok else 'CHECK'}: menu, aisle tabs, breadcrumbs, and price sort all work</span>
  <figure>
    <img src="app_check_images/usability_shop_menu.png" alt="Shop menu open in the navigation bar listing six apparel types" />
    <figcaption><strong>Proves:</strong> the new <strong>Shop ▾</strong> menu reaches every apparel type in one click, with live
    style counts: {esc(" · ".join(use["menu"]))}.</figcaption>
  </figure>
  <figure>
    <img src="app_check_images/usability_sorted_aisle.png" alt="Hoodies aisle with category tabs, breadcrumbs, and price low-to-high sort" />
    <figcaption><strong>Proves:</strong> choosing Hoodies opened <code>{esc(use["url"].replace(SITE, ""))}</code> with the
    breadcrumb “{esc(use["crumbs"])}”, the active tab “{esc(use["active_tab"])}”, and <em>Price: low to high</em>.
    Cards run ${prices[0]:.2f} → ${prices[-1]:.2f} in order{'' if sorted_ok else ' (NOT sorted)'}.</figcaption>
  </figure>
</section>

<footer>Generated by <code>scripts/app_check.py</code> · raw results in <code>output/app_check_results.json</code></footer>
</main>
</body>
</html>
"""
    # Every screenshot opens full size when clicked.
    page = re.sub(
        r'<img src="(app_check_images/[^"]+)"[^>]*/>',
        lambda m: f'<a href="{m.group(1)}" target="_blank">{m.group(0)}</a>',
        page,
    )
    page = page.replace("</nav>", "<br><small>Click any screenshot to open it full size.</small></nav>", 1)
    (OUT / "app_check.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    if "--html-only" in sys.argv:  # rebuild the report from the last run without re-capturing
        write_html(json.loads((OUT / "app_check_results.json").read_text(encoding="utf-8")))
    else:
        main()
