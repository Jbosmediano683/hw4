"""Cut each residential college's crest out of its own Campus Customs product photo.

Run once (needs Pillow, a dev-only tool):  python frontend/scripts/extract_crests.py   (from hw4/, after placing the data pack)
Writes frontend/public/crests/<slug>.png (transparent, shield-masked) and a contact sheet for review.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageStat

HW = Path(__file__).resolve().parents[2]
PRODUCTS = HW / "data" / "products"
OUT = HW / "frontend" / "public" / "crests"
SIZE = 112  # output height in px (2x the ~56px display size for crisp retina rendering)

# slug: (product photo, rough box around the shield only: left, top, right, bottom)
CRESTS = {
    "benjamin-franklin": ("benjamin-franklin-t-shirt", (372, 200, 534, 390)),
    "berkeley": ("berkeley-1-4-zip", (350, 144, 402, 200)),
    "branford": ("branford-1-4-zip", (346, 136, 408, 199)),
    "davenport": ("davenport-college-crewneck", (514, 206, 576, 264)),
    "grace-hopper": ("grace-hopper-logo-t-shirt", (370, 200, 532, 396)),
    "jonathan-edwards": ("jonathan-edwards-college-crewneck", (520, 208, 580, 274)),
    "morse": ("morse-logo-t-shirt", (362, 208, 544, 424)),
    "pierson": ("pierson-logo-t-shirt", (372, 200, 534, 396)),
    "saybrook": ("saybrook-logo-t-shirt", (374, 206, 536, 400)),
    "timothy-dwight": ("timothy-dwight-college-crewneck", (514, 200, 570, 264)),
    "trumbull": ("trumbull-1-4-zip", (348, 130, 398, 192)),
}


def tight_box(img: Image.Image, box: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    """Shrink the rough box to the shield: pixels that clearly differ from the heather-gray fabric.

    The fabric is textured, so blur first and only keep rows/columns with a real run of "ink".
    """
    region = img.crop(box).convert("RGB").filter(ImageFilter.GaussianBlur(1.2))
    w, h = region.size
    border = [region.getpixel((x, y)) for x in range(w) for y in (0, 1, h - 2, h - 1)] + [
        region.getpixel((x, y)) for y in range(h) for x in (0, 1, w - 2, w - 1)
    ]
    fabric = tuple(sorted(c[i] for c in border)[len(border) // 2] for i in range(3))
    px = region.load()
    ink = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            diff = abs(r - fabric[0]) + abs(g - fabric[1]) + abs(b - fabric[2])
            ink[y][x] = diff > 60 or (max(r, g, b) - min(r, g, b)) > 45
    min_run = max(2, round(0.12 * min(w, h)))
    cols = [x for x in range(w) if sum(ink[y][x] for y in range(h)) >= min_run]
    rows = [y for y in range(h) if sum(ink[y][x] for x in range(w)) >= min_run]
    if not cols or not rows:
        return box
    return (box[0] + cols[0], box[1] + rows[0], box[0] + cols[-1] + 1, box[1] + rows[-1] + 1)


def shield_mask(w: int, h: int) -> Image.Image:
    """Heater-shield silhouette: flat top, straight sides to 55%, then smooth curves meeting at a point."""
    s = 4
    W, H = w * s, h * s
    shoulder = H * 0.55

    def bez(p0, c, p1, t):
        return ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0],
                (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1])

    # Inset a few percent so no sliver of shirt fabric survives along the edges.
    ix, iy = W * 0.045, H * 0.02
    L, R, T, B = ix, W - ix, iy, H - iy
    tip = (W / 2, B)
    right = [bez((R, shoulder), (R, H * 0.86), tip, i / 30) for i in range(31)]
    left = [bez(tip, (L, H * 0.86), (L, shoulder), i / 30) for i in range(1, 31)]
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon([(L, T), (R, T), *right, *left], fill=255)
    return m.resize((w, h), Image.LANCZOS)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGBA", (len(CRESTS) * (SIZE + 20) + 20, SIZE + 40), (8, 32, 64, 255))
    for i, (slug, (photo, rough)) in enumerate(CRESTS.items()):
        img = Image.open(PRODUCTS / f"{photo}.jpg").convert("RGB")
        box = tight_box(img, rough)
        crest = img.crop(box)
        w = round(SIZE * crest.width / crest.height)
        crest = crest.resize((w, SIZE), Image.LANCZOS).convert("RGBA")
        crest.putalpha(shield_mask(w, SIZE))
        crest.save(OUT / f"{slug}.png", optimize=True)
        sheet.alpha_composite(crest, (20 + i * (SIZE + 20), 20))
        print(f"{slug:18} {photo:36} rough={rough} tight={box} -> {w}x{SIZE}")
    sheet.save(HW / "frontend" / "scripts" / "crests_contact_sheet.png")


if __name__ == "__main__":
    main()
