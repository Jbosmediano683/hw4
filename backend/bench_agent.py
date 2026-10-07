"""Problem 9 benchmark: latency, model calls, tokens, and correctness per chat turn.

Run from backend/:  python bench_agent.py <label>
Results are appended to ../output/bench_agent.json so before/after runs can be compared.
The Portkey gateway caches identical requests, so each config must run on questions
it hasn't seen with the same settings, or the timings measure the cache.
"""

import asyncio
import json
import sqlite3
import sys
import time
from pathlib import Path

from pydantic_ai.messages import ModelResponse, ToolCallPart

import agent
from models import ShopDeps

sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(__file__).resolve().parent.parent / "output" / "bench_agent.json"


def db(sql, *args):
    with sqlite3.connect(agent.DB_PATH) as conn:
        return conn.execute(sql, args).fetchall()


def qty(pid, size):
    return db("SELECT quantity FROM inventory WHERE product_id=? AND size=?", pid, size)[0][0]


def price(pid):
    return f"${db('SELECT price FROM catalogue WHERE product_id=?', pid)[0][0]:.2f}"


def crewneck_count():
    return db("SELECT COUNT(*) FROM catalogue WHERE lower(garment_type) LIKE '%crew%' "
              "AND lower(garment_type) NOT LIKE '%t-shirt%'")[0][0]


# (question, product page open, check(reply, output) -> bool, what the check expects)
CASES = [
    ("How much is the Yale Dad Hoodie?", None,
     lambda r, o: price("yale-dad-hoodie") in r, f"mentions {price('yale-dad-hoodie')}"),
    ("Is the Berkeley quarter zip available in a small?", None,
     lambda r, o: (qty("berkeley-1-4-zip", "S") > 0) == ("sold out" not in r.lower()),
     f"S qty={qty('berkeley-1-4-zip', 'S')}"),
    ("How many XL are left of the Squash Left Chest Hoodie?", None,
     lambda r, o: str(qty("squash-left-chest-hoodie", "XL")) in r or
     (qty("squash-left-chest-hoodie", "XL") == 0 and "sold out" in r.lower()),
     f"XL qty={qty('squash-left-chest-hoodie', 'XL')}"),
    ("What colors does this come in?", "champion-full-zip-hood",
     lambda r, o: all(c.lower() in r.lower() for c in json.loads(
         db("SELECT colors FROM catalogue WHERE product_id='champion-full-zip-hood'")[0][0])),
     "lists every color"),
    ("What crewnecks do you have?", None,
     lambda r, o: o.page_results is not None and len(o.page_results.product_ids) >= crewneck_count() - 2,
     f"page_results with ~{crewneck_count()} crewnecks"),
    ("Show me tees under $35", None,
     lambda r, o: o.page_results is not None and len(o.page_results.product_ids) > 0,
     "page_results with tees <= $35"),
]


async def main(label: str) -> None:
    rows = []
    ag = agent.get_agent()
    for question, page, check, expect in CASES:
        deps = ShopDeps(db_path=agent.DB_PATH, viewing_product_id=page, page_path=f"/products/{page}" if page else "/")
        start = time.perf_counter()
        result = await ag.run(question, deps=deps, usage_limits=agent.USAGE_LIMITS,
                              model_settings=agent.MODEL_SETTINGS)
        secs = time.perf_counter() - start
        u = result.usage
        u = u() if callable(u) else u
        tools_called = [p.tool_name for m in result.all_messages() if isinstance(m, ModelResponse)
                        for p in m.parts if isinstance(p, ToolCallPart) and p.tool_name != "final_result"]
        ok = bool(check(result.output.reply, result.output))
        rows.append({"q": question, "secs": round(secs, 2), "requests": u.requests,
                     "input_tokens": u.input_tokens, "output_tokens": u.output_tokens,
                     "tools": tools_called, "correct": ok, "expect": expect,
                     "reply": result.output.reply[:160]})
        print(f"{'OK ' if ok else 'BAD'} {secs:5.1f}s  req={u.requests} in={u.input_tokens:>6} "
              f"out={u.output_tokens:>5}  {question}  tools={tools_called}")
        if not ok:
            print(f"      expected {expect}; got: {result.output.reply[:200]}")

    n = len(rows)
    summary = {
        "label": label, "model": agent.MODEL_NAME, "settings": {k: v for k, v in (agent.MODEL_SETTINGS or {}).items()},
        "avg_secs": round(sum(r["secs"] for r in rows) / n, 2),
        "avg_requests": round(sum(r["requests"] for r in rows) / n, 2),
        "avg_input_tokens": round(sum(r["input_tokens"] for r in rows) / n),
        "avg_output_tokens": round(sum(r["output_tokens"] for r in rows) / n),
        "correct": f"{sum(r['correct'] for r in rows)}/{n}",
        "rows": rows,
    }
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=1))
    runs = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
    runs.append(summary)
    OUT.write_text(json.dumps(runs, indent=1), encoding="utf-8")


asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "run"))
