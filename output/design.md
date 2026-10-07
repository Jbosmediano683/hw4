# Campus Customs — Design (Problem 10)

**Direction:** a New Haven heritage outfitter in the fall semester, with a concierge at the counter.
Yale blue and white, a fall-on-campus backdrop, products that show the facts before you click, and a chat that feels like staff helping you shop.

| Area | What changed | Why it helps customers stay and buy |
|---|---|---|
| **Color** | Yale Blue `#00356B` surfaces, white/ivory text, light Yale blue `#7FB8FF` accents. White primary buttons with Yale-blue text. Amber appears **only** on low-stock warnings. | Looks like Yale at a glance, which builds trust for $58–$98 apparel. One action color plus one urgency color makes the next step obvious. |
| **Fall backdrop** | `CampusBackdrop.tsx`: a dusk sky fading to an October glow, a Gothic skyline (Harkness-style tower, lit windows, lamp posts), maple-red, pumpkin, and gold elms, and leaves drifting down the page. Pure SVG/CSS, no image downloads. | Puts alumni back on campus when the leaves turn and long sleeves come out. That nostalgia is what sells hoodies, crewnecks, and quarter-zips. |
| **Type & hierarchy** | Cormorant Garamond serif headlines with Inter body text. Lookbook numbering ("No. 01 · Shop by apparel"). A blue/white letterman stripe under the nav. Fall copy ("Long-sleeve season is here", "When the elms on Old Campus turn gold…"). | Reads like a printed catalogue, so there's a clear order to scroll through and the brand voice feels premium. |
| **Motion** | The hero rotates its audience ("made for *crisp fall days / sweater weather / students / alumni / parents / game day*"). Sections rise in on scroll, pages fade in, and the hero collage fans out on hover. All of it is off under `prefers-reduced-motion`. | Every visitor sees themselves in the first line. The site feels alive without getting in the way. |
| **Product cards** | Color swatches (all 22 catalogue colors mapped), a size strip (XS–XXL, sold-out sizes struck through), an honest "Only 2 left in XL" badge from live stock (only when a size has 5 or fewer), and a 3D tilt with a cursor glare. | Shoppers can rule items in or out without a click. Real scarcity nudges a purchase with no fake countdowns. |
| **Product page** | A 2.2× zoom lens on the photo, named swatches, and a size picker that answers immediately ("Good news: L is in stock, but only 2 left" / "XXL is sold out"). | Answers the two questions that stop a purchase: *will it look right?* and *is my size there?* |
| **Chat feel** | The **Bulldog Concierge**: crest avatar, timestamps, a "🐾 Checking the stockroom…" typing state, suggestion chips that change with the page ("Do you have this in pink?" on a product page), and a pill launcher with a one-time teaser. | Feels like a person at the counter, and shoppers never face a blank box. |
| **The site asks for you** | The concierge can be triggered from anywhere on the site (`chatUI.ask`): the **"Shop your college"** strip (click *Saybrook* → its gear lands on the page), three **Curated Edits** (The Game, Sweater Weather, The Family Collection), and "Ask the Concierge" chips on product pages. | The AI becomes part of the storefront, not a widget in the corner. Browsing turns into a conversation that ends in clickable product cards. |
| **College crests** | Each college name in the strip sits over its real crest, cut from that college's own product photo (`frontend/scripts/extract_crests.py`). On hover the crest comes forward and the name slides beneath it. Colleges with no products get a plain Yale-blue shield, not invented arms. | Students and alumni spot their own college instantly. Identity is a strong reason to click. |
| **About page** | A polaroid wall of the shop at 57 Broadway with a warm faded-film look, the shop's real history (family-run, on Broadway since the 1970s), and a nostalgic pull quote. The frames load real photos from `frontend/public/about/` and show labelled illustrations until photos are added. | Seeing the shop they walked past as students is the strongest nostalgia trigger for alumni buyers. |

**Note for a fresh clone:** the crest images are derived from the product photos, so they're kept out of git like the data pack. Until you run `python frontend/scripts/extract_crests.py` after placing `data/`, the strip shows plain shields.

**Verified in the running app:**
- The low-stock badges match the DB. For example, Basic Hoodie shows "Only 2 left in XL", and the DB has XL = 2.
- Clicking *Saybrook* put its 3 items on the page.
- On the Saybrook crewneck, the "How many L are left?" chip got "There are 2… left in L", which matches the DB.
- The Sweater Weather edit returned 11 quarter-zips at $72.00 and 7 fleece at $98.00, which matches the DB.
- No console errors.
