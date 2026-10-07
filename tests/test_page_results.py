"""Problem 7 check: browse questions should fill page_results; specific questions should not.

Run from hw4/:  python tests/test_page_results.py
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))  # import the backend modules

import tools
from agent import DB_PATH, run_chat

sys.stdout.reconfigure(encoding="utf-8")

CASES = [
    # (question, expected search for DB truth or None if page_results should stay empty)
    ("What hoodies do you have?", ("hoodies", None)),
    ("Show me navy hoodies under $70", ("navy hoodies", 70)),
    ("Anything for Branford college?", ("Branford", None)),
    ("Do you have pink hoodies?", None),
    ("How much is the Boola Boola T Shirt?", None),
]


async def main() -> None:
    for question, truth in CASES:
        start = time.time()
        r = await run_chat(question, [])
        page = r.page_results
        print(f"\n> {question}  ({time.time() - start:.1f}s)")
        print(f"   reply: {r.reply}")
        print(f"   chat cards: {[c.product_id for c in r.products]}")
        print(f"   page_results: {page and (page.title, page.total)}")
        if truth:
            query, max_price = truth
            expected = {h.product_id for h in tools.search_products(DB_PATH, query, 30, max_price=max_price).results}
            got = {c.product_id for c in page.products} if page else set()
            print(f"   DB check: {len(got & expected)}/{len(expected)} expected on page, {len(got - expected)} extra")
        else:
            print(f"   DB check: page_results should be empty -> {'OK' if page is None else 'NOT EMPTY'}")


asyncio.run(main())
