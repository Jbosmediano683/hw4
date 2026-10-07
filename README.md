# Campus Customs — HW 4

A Yale-blue, fall-on-campus storefront for **Campus Customs** (57 Broadway, New Haven) with a
**PydanticAI shopping agent**, the *Bulldog Concierge*, that answers from the live product database.

- `frontend/`: React + Vite + TypeScript site (Home, Shop/Products, product pages, About, Log In, Create account, and the chat widget)
- `backend/main.py`: FastAPI app (run with `uvicorn main:app --reload --port 8000` from `backend/`)
- The agent is four files in `backend/`:
  - `prompts/prompt.md`: system prompt, voice, tool rules, and safety rules
  - `agent.py`: agent wiring and run loop (model, tools, card vetting, audit)
  - `tools.py`: database tools (search, description, price, stock, customer profile)
  - `models.py`: Pydantic / PydanticAI structured types
- `agent.py` also writes the append-only audit trail (`output/audit_trail.json`).
- Two FastAPI app modules (used by `main.py`, not part of the agent): `auth.py` (accounts and sessions) and `chat_store.py` (customer chat history)
- `tests/`: agent checks, safety probes, and a benchmark
- `output/`: harness, design, usability, app check, and `audit_trail.json`

**How the system works** (architecture, model fields, tools, safety, specs): see **`output/harness.md`, Part A**.

---

## 1. Requirements

- **Python 3.11+** (tested on 3.13)
- **Node.js 20.19+** (tested on 24.20) with npm
- A **Portkey API key** for the course model gateway (model `gpt-5.6-luna`)

## 2. Place the data pack (not in git)

The database and product photos are **not** in this repository. Unzip the course `data.zip` so that it sits inside `hw4/`:

```
hw4/
└── data/
    ├── campus_customs.db
    └── products/          # images referenced by the catalogue
```

On first start, the backend adds what it needs to the database itself: a `sessions` table, and a `page_results_json` column plus an index on `chat_messages`. Nothing has to be prepared by hand.

## 3. Add your API key

```bash
cp .env.example .env        # Windows PowerShell: Copy-Item .env.example .env
```

Then edit `.env` and set `PORTKEY_API_KEY=...`. The `.env` file is gitignored. The products, login, and shop pages work without a key; only the chat needs it.

## 4. Run the backend (terminal 1)

From `hw4/`, create and activate a virtual environment, then install the requirements:

**Windows (PowerShell)**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

Check it: http://localhost:8000/api/health → `{"status":"ok"}`

## 5. Run the frontend (terminal 2)

From `hw4/`:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5174**. Vite proxies `/api` and `/media` to the backend on port 8000.

- **Test login:** `test@campuscustoms.yale.edu` / `password`. You can also create your own account from **Create account**.
- **Try in the chat** (bottom right, *Ask the Concierge*):
  - "What hoodies do you have?" puts the results on the page as product cards.
  - "How much is this, and do you have it in XL?" on a product page.

## 6. Optional extras

- **College crests in the "Shop your college" strip** are cut from the data pack's product photos, so they aren't committed. Until you build them, the strip shows plain shields. To build them (needs Pillow):
  ```bash
  python -m pip install pillow
  python frontend/scripts/extract_crests.py      # writes frontend/public/crests/*.png
  ```
- **About-page photos:** drop `storefront.jpg`, `interior-1.jpg`, and `interior-2.jpg` into `frontend/public/about/`. They replace the labelled illustrations automatically.
- **Tests and evidence scripts** (run from `hw4/` with the venv active):

  | Command | What it does |
  |---|---|
  | `python tests/test_tools_agent.py` | Price, stock, and description answers checked against the DB |
  | `python tests/test_page_results.py` | Category questions put the right cards on the page |
  | `python tests/test_safety.py` (server running) | Safety probes through `/api/chat`; each turn appends to `output/audit_trail.json` |
  | `python tests/bench_agent.py <label>` | Latency, tokens, and correctness benchmark |
  | `python scripts/app_check.py` (from `hw4/`, app running) | Re-captures `output/app_check.html` (needs `pip install playwright` and Microsoft Edge) |

## 7. API

| Method | Path | Returns |
|---|---|---|
| GET | `/api/health` | `{"status": "ok"}` |
| GET | `/api/products` | All catalogue rows, with JSON fields parsed, plus `image_url`, `category`, live `stock` by size, and `total_stock` |
| GET | `/api/categories` | The six apparel aisles with counts and a cover image |
| GET | `/api/products/{product_id}` | One product plus `inventory` (size → quantity, XS to XXL) |
| POST | `/api/auth/signup` | Create account (`first_name, last_name, email, password`), sets session cookie |
| POST | `/api/auth/login` | Log in (`email, password`), sets session cookie |
| POST | `/api/auth/logout` | Ends the session |
| GET | `/api/auth/me` | Current user or `null` |
| POST | `/api/chat` | One agent turn: `{message, history (guests only), page_context: {path, product_id}}` returns `{reply, products, page_results}`. Saved to `chat_messages` when logged in |
| GET | `/api/chat/history` | Logged-in shopper's saved chat (last 50 messages) |
| DELETE | `/api/chat/history` | Clear the logged-in shopper's saved chat |
| GET | `/media/products/<file>.jpg` | Product images (served from `data/`) |

## 8. Write-ups

- `output/harness.md`: **Part A** shows how the system works (architecture, model fields, tools, safety, audit trail, specs, how to run); **Part B** is the build log by problem
- `output/audit_trail.json`: append-only log of every agent turn (tool calls, stop reason, tokens)
- `output/usability.md`: the four usability improvements (Problem 9) and their measurements
- `output/design.md`: the storefront design (Problem 10) and why it helps customers stay and buy
- `output/app_check.html`: live-site test report with screenshots (Problem 11); open it in a browser
- `AI_prompts.md`: the prompts I typed to the vibe coder, one section per problem
