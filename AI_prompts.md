# AI Prompt Log — Homework 4: Campus Customs

Log of the prompts I typed to my vibe coder (Claude Code) while building this
assignment. One section per problem, in the order I worked them.

---

## Problem 1 — Data

**Prompt 1**

> We're working out of HW 4 today. Please look at the Zip file and do the
> following

(Attached a screenshot of the assignment's Data section: unzip `data.zip` so
there is `data/campus_customs.db` with tables `catalogue`, `inventory`, and
`users`, plus `data/products/` with images whose paths match the `catalogue`
table.)

**Follow-up prompt**

> Create "AI_prompts.md" at the start of the assignment and keep it updated as
> you work. This file is the log of what you type to the vibe coder.

*What was lacking after the first prompt:* the data was unzipped and checked,
but there was no prompt log yet, and the assignment requires one from the
start.

---

## Problem 2 — Analyze the database

**Prompt 1**

> FYI that was problem 1. Now onto Problem 2: Analyze the database. Look at the
> database "data/campus_customs.db" and understand the fields of each table. At
> a minimum you should understand "catalogue", "inventory", and "users". Start
> the file "output/harness.md". Write down each table and its fields, and one
> short line on why each field matters for the shop or the chatbot. You will
> keep growing this harness file in later problems (models, tools, safety,
> specs).

**Follow-up prompt**

None needed. The first prompt produced `output/harness.md` covering all four
tables (`catalogue`, `inventory`, `users`, plus the extra `chat_messages`), with
a reason for every field.

---

## Problem 3 — Build the Campus Customs website

**Prompt 1**

> Problem 3: Build the Campus Customs website. Scaffold a REACT + VITE +
> TypeScript front end for Campus Customs. Put a nav bar at the top that links
> to the main pages: Home, Products, About Us, Log In, Create account. Pull
> Campus Customs-style wording from yalebulldogblue.com for Home and About Us,
> but write these pages in your own voice (do not copy the original site
> text). On the products page, show product images from the catalogue (use the
> image paths in the database) with basic product info (name, price, short
> description). Make each product open a single-item page (large image on one
> side, full product text on the other — description, price, sizes/stock when
> you have them). Clicking a card on products should take the shopper there.
> Add a chat interface in the BOTTOM RIGHT of the site (a floating chat panel
> is fine). It does NOT need to talk to an agent yet — a stub that will call
> your backend later is enough for this problem. You will need a small API
> soon to read the database. It is fine to start a simple FastAPI app in
> "backend/main.py" just to serve products and images, then grow it into the
> agent backend in Problem 5.

**Follow-up prompt**

None needed. The first prompt produced the running site: nav bar, all five
pages, a 102-product grid with database images, single-item pages with live
per-size stock, a FastAPI backend, and a bottom-right chat panel wired to a
stub `/api/chat` endpoint.

---

## Problem 4 — Create account and login

**Prompt 1**

> Problem 4: Create account and login. Build a normal create-account / login
> flow. Create account: first name, last name, email, password (confirm
> password is a nice touch). Log in: email and password. New accounts go into
> the "users" table. Make sure to store passwords securely so hackers (human or
> AI) cannot access them. The seed database already has a test user you can use
> while building: Email: test@campuscustoms.yale.edu, Password: password.
> Confirm you can log in as that user, and that a brand-new account you create
> also works. Update "output/harness.md" with how auth works (what you store for
> a user and how passwords are protected).

**Follow-up prompt**

None needed. The first prompt produced working signup, login, and logout:
salted PBKDF2 hashes at 600,000 iterations in `users`, HttpOnly session
cookies, and a brute-force throttle. The test user and a new account (Handsome
Dan) were both verified in the browser, and `output/harness.md` section 3
documents it.

---

## Problem 5 — PydanticAI Agent backend

**Prompt 1**

> Problem 5: PydanticAI Agent backend. Build the shop chatbot as a PydanticAI
> agent behind FastAPI, plugged into your front-end chat widget. Put the API
> app in "backend/main.py" — that is the file you run with Uvicorn. Keep the
> agent as these four files next to it (same idea as Homework 3):
> "backend/prompts/prompt.md" (system prompt), "backend/agent.py" (agent entry
> / wiring), "backend/tools.py" (tools the agent can call), "backend/models.py"
> (Pydantic / PydanticAI structured types). In "main.py", expose a chat route
> so a message from the website returns a reply from the agent. Put Campus
> Customs voice and safety basics into "prompts/prompt.md". Start or update
> types in "models.py" for chat replies / product cards as needed. In
> "output/harness.md", note how the front end talks to FastAPI and how the
> agent is loaded (prompt file + model). Make sure the backend runs from the
> "backend/" folder like this: uvicorn main:app --reload --port 8000

**Follow-up prompt**

> Yes, finish Problem 5 first, then I will give you instructions for problem 6

*What was lacking after the first prompt:* I interrupted the build halfway
(while `models.py` was being written) to start Problem 6, so the agent files
didn't exist yet. The follow-up told the vibe coder to finish Problem 5 first
and keep Problem 6's lookup tools for later.

---

## Problem 6 — Tools: product info and stock

**Prompt 1**

> Problem 6: Tools: product info and stock. Give the agent tools that look up
> real information from "campus_customs.db": product description, price, how
> many are in stock (by size when the customer asks). The agent must use the
> database — it should not invent prices or quantities. If a size is out of
> stock, say so clearly. Expand "prompts/prompt.md" so the agent knows to call
> these tools for price and stock questions. Add or update return types in
> "models.py". In "output/harness.md", list each tool and explain which model
> fields you chose for lookup results and why.

**Follow-up prompt**

None needed. (I had first sent a cut-off version of this prompt in the middle
of Problem 5, so the vibe coder asked me to resend it in full; the prompt above
is the complete one.) During testing the vibe coder caught that "hoodies under
$60" wrongly returned none, because the search only priced the first 12 of 27
hoodies. It added `min_price` / `max_price` filters to `search_catalogue` and
reran the tests, and all 8 checks now match the database.

---

## Problem 7 — Chat search that updates the page

**Prompt 1**

> Problem 7: Chat search that updates the page. Now we will add a neat feature
> to the site. When a customer asks about a type of item — for example "what
> hoodies do you have?" — the agent should search the catalogue and the website
> should dynamically show those matching items as product cards (image, name,
> price, short info). This is an API contract: the agent returns structured
> product matches and then the front end renders them on the website. It looks
> really cool.

**Follow-up prompt**

> After the dynamic product cards are loaded by your new feature, make sure
> that the same single-item page behavior you built in Problem 3 still works:
> each product card — including the ones the chat just put on the page — should
> still open that detail view (large image + full info) when clicked. Update
> "prompts/prompt.md" and "output/harness.md" so it is clear how search results
> reach the page.

*What was lacking after the first prompt:* it described the feature but didn't
say the chat-placed cards must keep the Problem 3 click-through to the detail
page, or that the prompt and harness had to document how results reach the
page. (I interrupted and resent the first prompt with these additions.)

---

## Problem 8 — Customer memory

**Prompt 1**

> Problem 8: Customer memory. When a shopper is logged in, save their chat
> history in the database in an appropriate table and reload it when they
> return. The agent should know who is chatting (name, email) — put that in
> agent deps (or an equivalent clear pattern) and/or tools the agent can call.
> Also pass enough page context that if someone is on a product page and asks
> "do you have this in pink?", the agent knows which item they mean. Hint: you
> can put code into the agent context. Guests can still chat, but history only
> needs to persist for logged-in users. Document in "output/harness.md": how
> user chat history is stored, what customer fields the agent sees, and how
> page context is passed.

**Follow-up prompt**

None needed. The first prompt produced persistent history in `chat_messages`
(one new column for page results). History reloads on login with a "Welcome
back" message, and the agent gets name and email through `ShopDeps`, the
session instructions, and a `get_customer_profile` tool. The product page
context is resolved into the agent's instructions. All of it was verified in
the browser and against the database.

---

## Problem 9 — Usability improvements

**Prompt 1**

> Problem 9: Usability improvements. Now that the core shop works, improve
> it. Choose and implement: 2 front-end usability improvements (maybe make the
> page looks easy to navigate, I want a sleek environment that is worth of an
> Ivy League brand. Make it preppy and look fancy. Also include easy
> navigation between each type of apparel). 2 agent / backend usability
> improvements (use a cost efficient learning model, and work on make the page
> load faster responding. I'll let you AI decide on the backend improvments
> however).
> Write "output/usability.md" before or as you build. For each of the
> improvements, say what you added and why it helps a Campus Customs shopper
> or the business. Then make sure all improvements actually show up in the
> running app.

**Follow-up prompt**

None needed. The first prompt produced all four improvements in the running
app: the Ivy-League redesign, shop-by-apparel navigation, leaner and cheaper
agent turns (measured 33% faster with 22% fewer input tokens and still 6/6
correct), and faster page loads (86% smaller catalogue payload, cached
photos). Each is described in `output/usability.md` with what was added, why
it helps, and where to see it.

---

## Problem 10 — Style the website

**Prompt 1**

> Problem 10: Style the website. Add creative design so the site feels like a
> real Campus Customs Storefront - fonts, color, hierarchy, motion, product
> presentation, chat feel. You will get more points for imaginative and
> innovative design. Write "output/design.md": what you changed and why it
> should help customers stick around and buy. Keep it concrete and short

**Follow-up prompt**

> Why did you choose a pink font? It doesn't match Yale's blue and white color
> palette at all. Also, I want the background to reflect the vibrant,
> beautiful scenery of campus during the Fall semester. When the leaves start
> to turn, when long sleeves start being the norm. I want customers to feel
> comfy reflecting back on the campus during the Fall season.

*What was lacking after the first prompt:* the design used pink accents
(taken from the generic workspace style rules) instead of Yale's blue and
white, and the plain dark background didn't evoke campus in the fall. The
follow-up switched the palette to Yale blue and white and added an animated
fall-on-campus backdrop with a Gothic skyline, autumn elms, and drifting
leaves.

**Follow-up prompt 2**

> For the "shop your college" section, can you please put the college
> insignia's either behind or underneath each name? It will look so much
> better.

(Attached a screenshot of the college marquee.)

*What was lacking:* the marquee showed the college names as plain text, with
no crests. The vibe coder cut the real crests out of each college's own
product photos and placed them behind the names. On hover, each crest comes
forward and the name moves underneath it.

**Follow-up prompt 3**

> On the "about us" page, please put some photos on the right of the actual
> Campus Customs storefront located in the shops at New Haven and maybe some
> photos of inside the store. I'm trying to make alumnus' feel nostalgic for
> the simpler times when they went to school.

(Attached a screenshot of the About page.)

*What was lacking:* the About page was text only, with nothing visual of the
shop itself. The vibe coder added a nostalgic polaroid photo wall on the
right that loads real store photos from `frontend/public/about/`. Since it
had no rights-cleared photos of the real store, it shows labelled
illustrations until photos are added. It also added the shop's real history
(57 Broadway, since the 1970s) to the copy.

**What the first prompt produced** (all verified in the browser):
- The Bulldog Concierge chat, with suggestion chips that change with the page.
- A residential-college marquee and Curated Edits that ask the concierge and
  fill the page with results.
- Product cards with swatches, a size strip, honest low-stock badges, and a
  3D tilt.
- A zoom lens and size picker on product pages.
- A rotating headline, scroll reveals, and page fades.

`output/design.md` explains each change and why it should help customers
stick around and buy.

---

## Problem 11 — Site testing (app check)

**Prompt 1**

> Ok looks good. Let's move to Problem 11: Site testing (app check). Test the
> live site and document it in "output/app_check.html" (a page you can
> double-click open). Include clear screenshots and short captions for: 1.
> Chat checking the inventory level of an item (honest stock/price from the
> DB) 2. The dynamic search-result cards appearing after a category question
> (e.g. hoodies) 3. One of the usability features you added in Problem 9.
> Make the HTML easy to grade: heading for each check, screenshot, one or two
> sentences on what the screenshot proves. Put the screenshot image files in
> "output/app_check_images/" and link them from "app_check.html" with
> relative paths (for example "app_check_images/inventory.png")

**Follow-up prompt**

None needed. The first prompt produced `output/app_check.html`, with three
PASS checks and six full-resolution screenshots captured from the live site
by a headless-browser script. Each check is compared against the database
(price $58.00, XL sold out, M = 5; 27/27 hoodie cards; prices sorted low to
high).

---

## Problem 12 — Audit trail, safety, and finish harness

**Prompt 1**

> Problem 12: Audit trail, safety, and finish harness. Keep an append-only
> "output/audit_trail.json" of agent-loop activity (time, tool name, short
> args/result, stop reason). Do not wipe it between runs. Also think of some
> safety rules to give the agent and put them in "prompts/prompt.md". Finish
> "output/harness.md" so it is clear how the system works: model fields in
> "models.py" and why you chose them; tools and abilities; safety rules; specs
> (loop limits, result caps, models, how to run front + back).

**Follow-up prompt**

None needed. The first prompt produced:
- The append-only `output/audit_trail.json` (one entry per turn, with tool
  calls, stop reason, and tokens), which logs every outcome including rate
  limits.
- Five groups of safety rules in the prompt, plus server-side guards such as
  card-number redaction.
- A finished harness: Part A, "How the system works", covers architecture,
  model fields, tools, safety, audit, specs, and run commands.

All of it was verified by `test_safety.py` against the live API.

---
