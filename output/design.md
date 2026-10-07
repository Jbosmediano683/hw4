# Campus Customs — Design (Problem 10)

**Direction: a New Haven heritage outfitter in the fall semester, with a concierge at the counter.**
Problem 9 laid the Ivy-League base (serif type, crest). Problem 10 makes the
store *feel alive*: **Yale blue and white**, a **fall-on-campus backdrop**,
products that show real detail before you click, motion that guides the eye,
and a chat that behaves like a person helping you shop.

## What changed, and why it helps customers stay and buy

### 0. Yale blue & white, and fall on campus
- **Palette:** Yale Blue (`#00356B`) and deep navies for every surface, white/ivory text, and light Yale blue (`#7FB8FF`) for accents. Primary buttons and the concierge launcher are **white with Yale-blue text**; the shopper's chat bubbles are Yale medium blue (`#286DC0`); the crest and favicon are white on Yale blue. The earlier pink accent is gone. *Why:* the store should look like Yale at a glance. Brand-true color reads as authentic and trustworthy for $58–$98 apparel.
- **The fall backdrop** (`CampusBackdrop.tsx`, fixed behind every page):
  - A dusk sky that deepens from Yale blue to a warm October glow at the horizon.
  - A Gothic campus skyline: a Harkness-style tower with pinnacles, crenellated college walls, a library nave, and a chapel spire, with **warm lit leaded windows** (a few gently flicker) and glowing lamp posts.
  - **Elms in maple red, pumpkin, and gold**, and **autumn leaves drifting down the page** with a soft sway.

  It is all SVG and CSS, so it costs no image downloads. The leaves stop under reduced-motion.

  *Why:* it puts shoppers back on campus when the leaves turn and long sleeves come out. That cozy, nostalgic feeling is exactly what sells hoodies, crewnecks, and quarter-zips, and it gives returning alumni a reason to linger.
- **Fall copy:**
  - Ribbon: "Fall semester on campus ✦ Long-sleeve season is here".
  - Hero: "The Fall Semester Collection", with "made for *crisp fall days. / sweater weather. / students. / alumni. …*".
  - Body: "When the elms on Old Campus turn gold and long sleeves become the norm…".
  - A new **Sweater Weather** edit (quarter-zips & fleece).
  - Footer: "Made for Bulldogs, worn every fall".
- **Autumn amber is used in only one place outside the scenery: scarcity** (the "Only 2 left" badge and low-stock sizes), so urgency stands out against the blue.

### 1. Fonts, color, hierarchy
- **Editorial numbering**: "No. 01 · Shop by apparel", "No. 02 · Curated edits", and so on, plus italic serif numerals on the pillars. *Why:* it reads like a printed lookbook, so the page has a clear order and shoppers scroll further.
- **Letterman stripe** (blue / white / blue) under the nav, like a varsity sweater trim. *Why:* brand recognition on every page at almost no visual cost.
- **Clear roles for color:** white is for the main action (buttons, launcher), light Yale blue for prices, labels, and concierge chips, and amber only for low stock. Everything else is ivory or blue-gray. *Why:* the eye lands on what to do next.
- **Mobile:** the ribbon collapses to one line and the launcher becomes a crest button, so the hero fits on a phone screen.

### 2. Motion (respectful, never in the way)
- **A headline that rotates its audience:** "Classic Yale style, made for *students. / alumni. / parents. / game day.*", with a soft 3D roll. *Why:* every visitor sees themselves in the first line.
- **Scroll reveal**: sections rise in as they enter view. **Page fade**: each route fades in. **The hero collage fans out** on hover.
- Everything turns off under `prefers-reduced-motion`. *Why:* it feels polished without making anyone queasy.

### 3. Product presentation
- **Cards show the decision-making facts up front**: color **swatches** (all 22 catalogue colors mapped to real tones), a **size strip** (XS to XXL, with sold-out sizes struck through), and an **honest urgency badge** from live stock ("Only 2 left in XL"; shown only when a size is truly at 5 or fewer). *Why:* shoppers can rule items in or out without a click, and real scarcity nudges a purchase without fake countdowns.
- **3D tilt with a light glare** that follows the cursor. *Why:* it gives products a tactile, physical feel and invites a click.
- **The product page has a zoom lens** (2.2× magnifier that follows the cursor) to inspect crests and lettering, **named swatches**, and a **size picker** that immediately says "Good news: L is in stock, but only 2 left" or "XXL is sold out right now." *Why:* it answers "will it look right, and is my size there?", the two questions that stop a purchase.

### 3b. About page: the shop at 57 Broadway, for nostalgic alumni
- **Text on the left, a photo wall on the right**: three taped polaroids (the storefront at 57 Broadway, the sweatshirt wall, and pennants by the register), slightly rotated, with handwritten-style serif captions. They straighten and lift on hover. A **warm, faded-film treatment** (light sepia, vignette, grain) makes every photo feel like a memory of a fall afternoon.
- **Real history in the copy:** a family-run shop at 57 Broadway, across from campus, selling Yale gear on Broadway since the 1970s. There's also a pull quote: *"Remember the first cold morning of the fall semester…"*, and an invitation to stop by during reunions or The Game.
- **Honest photos:** the frames load real photos from `frontend/public/about/` (`storefront.jpg`, `interior-1.jpg`, `interior-2.jpg`). Until those files are added, each frame shows an original illustration labelled "illustration", so nothing pretends to be a photo of the real store.
- *Why:* alumni buy for the feeling of being back on campus. Seeing the shop they walked past as students is the strongest nostalgia trigger the site can offer.

### 4. Shopping that talks back (chat feel)
- **The Bulldog Concierge**: a named persona with a crest avatar and an online dot, avatars on its messages, timestamps, and a "🐾🐾🐾 *Checking the stockroom…*" typing state. *Why:* it feels like staff at a shop counter, not a chatbot form.
- **Suggestion chips that change with the page**:
  - Home: "Gift ideas for a Yale parent"
  - A product page: "Do you have this in pink?" / "Is this in stock in a medium?"
  - An aisle: "Which crewnecks are under $60?"

  *Why:* shoppers never face a blank box.
- **The launcher is a pill**: "Ask the Concierge", with a soft pulsing ring, plus a one-time teaser bubble ("Looking for your college's quarter-zip? I can check sizes and stock in seconds."). *Why:* it signals that help exists, without nagging (once per session).
- **The site itself asks the concierge for you** (new `chatUI` context):
  - **Residential-college marquee**: the 14 college names scroll by in italic serif, **each over its own college crest**, like a wax seal. On hover the crest comes forward at full color and the name slides beneath it. Clicking "Saybrook" asks *"Do you have anything for Saybrook College?"*, and the concierge lays the 3 Saybrook items on the page.
    - The crests are the **real shields, cut from each college's own Campus Customs product photo** (11 colleges, `frontend/scripts/extract_crests.py` → `public/crests/*.png`, shield-masked and transparent).
    - Ezra Stiles, Pauli Murray, and Silliman have no products yet, so they get a plain Yale-blue shield rather than invented arms.
    - *Why:* students and alumni spot their own college's arms instantly. Identity is a strong reason to click and buy.
  - **Curated Edits**: "The Game Edit", "Sweater Weather", and "The Family Collection" are editorial collages. Their button hands a real question to the concierge, and the results fill the page.
  - **Product page "Ask the Concierge" card**: one tap on "How many L are left?" gets "There are 2 … left in L".

  *Why:* the AI becomes part of the storefront, not a widget in the corner. Browsing turns into a conversation, and every answer lands as clickable product cards.

## Verified in the running app
- After the Yale-blue/fall revision: the backdrop renders behind every page (skyline, lit windows, red/orange/gold elms, 22 drifting leaves), all text stays readable over it, and there are no console errors. The "Sweater Weather" edit's question returned "Fall quarter-zips and fleece" (18 = 11 quarter-zips at $72.00 + 7 fleece at $98.00, matching the DB).
- Home: rotating headline, college marquee, 3 edit collages, reveal-on-scroll, a teaser after ~3.5 s, and the pill launcher. No console errors.
- Featured card badges match the database exactly: Basic Hoodie "Only 2 left in XL" (XL=2); Harvard–Yale tee "Only 2 left in L" (L=2); Boola tee "Only 2 left in XL" (XL=2). The bomber shows no badge because no in-stock size is ≤5.
- Clicking **Saybrook** in the marquee opened the concierge, showed the stockroom state, and put the "Saybrook College gear" page up with 3 cards (6.4 s). Those chat-placed cards carry swatches, size strips, and badges too.
- Saybrook College Crewneck page: the zoom lens tracked the cursor, picking **L** showed "only 2 left", and the "How many L are left?" chip got "There are 2 … left in L" from the agent.
