"""Problem 6 check: ask price / stock / description questions and show which tools the agent called.

Run from backend/:  python test_tools_agent.py
"""

import asyncio
import sys
import time

from pydantic_ai.messages import ModelResponse, ToolCallPart

from agent import DB_PATH, USAGE_LIMITS, get_agent
from models import ShopDeps

sys.stdout.reconfigure(encoding="utf-8")

CASES = [
    ("How much is the Boola Boola T Shirt?", None),
    ("Do you have the Baseball Left Chest Crewneck in XL?", None),
    ("How many mediums are left?", "baseball-left-chest-crewneck"),
    ("What sizes is this available in?", "baseball-left-chest-crewneck"),
    ("Do you have it in 3XL?", "baseball-left-chest-crewneck"),
    ("What does the Branford 1/4 zip look like and what does it cost?", None),
    ("Which hoodies do you have under $60?", None),
]


async def main() -> None:
    agent = get_agent()
    for question, viewing in CASES:
        deps = ShopDeps(db_path=DB_PATH, user_first_name="Test", viewing_product_id=viewing)
        start = time.time()
        result = await agent.run(question, deps=deps, usage_limits=USAGE_LIMITS)
        calls = [
            f"{p.tool_name}({p.args_as_dict()})"
            for m in result.all_messages()
            if isinstance(m, ModelResponse)
            for p in m.parts
            if isinstance(p, ToolCallPart) and p.tool_name != "final_result"
        ]
        where = f" [viewing {viewing}]" if viewing else ""
        print(f"\n> {question}{where}  ({time.time() - start:.1f}s)")
        for c in calls:
            print(f"   tool: {c}")
        print(f"   reply: {result.output.reply}")
        print(f"   cards: {result.output.product_ids}")


asyncio.run(main())
