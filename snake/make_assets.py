"""
Generates the PNG sprites in ./assets (needs Pillow, only for this script).
The game itself only needs tkinter + the PNG files.

    python make_assets.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

CELL = 36           # final sprite size in px (must match CELL in snake.py)
S = 4               # supersampling factor for smooth edges
C = CELL * S
OUT = Path(__file__).parent / "assets"

PALETTES = {        # main, outline, belly/highlight
    "turquoise": ((64, 200, 190), (24, 110, 105), (150, 235, 228)),
    "orange":    ((245, 150, 40), (165, 85, 10),  (255, 205, 130)),
    "dead":      ((150, 150, 150), (90, 90, 90),  (195, 195, 195)),
}
VEC = {"U": (0, -1), "D": (0, 1), "L": (-1, 0), "R": (1, 0)}
ORDER = "UDLR"


def canvas():
    return Image.new("RGBA", (C, C), (0, 0, 0, 0))


def save(img, name):
    img.resize((CELL, CELL), Image.LANCZOS).save(OUT / f"{name}.png")


def tube(d, dirs, width, color):
    """Disc in the centre + bars to every connected edge -> seamless joints."""
    c, r = C / 2, width / 2
    d.ellipse((c - r, c - r, c + r, c + r), fill=color)
    for k in dirs:
        dx, dy = VEC[k]
        x0, x1 = sorted((c, c + dx * C))
        y0, y1 = sorted((c, c + dy * C))
        if dx:
            d.rectangle((x0, c - r, x1, c + r), fill=color)
        else:
            d.rectangle((c - r, y0, c + r, y1), fill=color)


def body(pal, dirs):
    img = canvas(); d = ImageDraw.Draw(img)
    main, outline, light = pal
    tube(d, dirs, C * 0.80, outline)
    tube(d, dirs, C * 0.64, main)
    r = C * 0.12
    d.ellipse((C/2 - r, C/2 - r, C/2 + r, C/2 + r), fill=light)   # scale dot
    return img


def tail(pal, toward):
    """Tapers from the edge it connects to into a rounded tip."""
    img = canvas(); d = ImageDraw.Draw(img)
    main, outline, _ = pal
    dx, dy = VEC[toward]
    c = C / 2
    for w, col in ((C * 0.80, outline), (C * 0.64, main)):
        edge = (c + dx * c, c + dy * c)
        tip = (c - dx * C * 0.18, c - dy * C * 0.18)
        r_tip = w * 0.22
        px, py = -dy, dx                          # perpendicular
        poly = [(edge[0] + px * w / 2, edge[1] + py * w / 2),
                (edge[0] - px * w / 2, edge[1] - py * w / 2),
                (tip[0] - px * r_tip, tip[1] - py * r_tip),
                (tip[0] + px * r_tip, tip[1] + py * r_tip)]
        d.polygon(poly, fill=col)
        d.ellipse((tip[0] - r_tip, tip[1] - r_tip, tip[0] + r_tip, tip[1] + r_tip), fill=col)
    return img


def head_right(pal, dead=False):
    """Head facing right; other directions are rotations of this one."""
    img = canvas(); d = ImageDraw.Draw(img)
    main, outline, _ = pal
    c = C / 2
    for w, col in ((C * 0.92, outline), (C * 0.78, main)):
        r = w / 2
        d.rectangle((0, c - r * 0.87, c, c + r * 0.87), fill=col)   # neck to left edge
        d.ellipse((c - r, c - r, c + r, c + r), fill=col)
    if not dead:  # tongue
        d.line((c + C * 0.38, c, C * 0.98, c), fill=(220, 30, 50), width=S * 2)
    for ey in (c - C * 0.19, c + C * 0.19):
        ex, er = c + C * 0.1, C * 0.12
        if dead:
            k = er * 0.8
            d.line((ex - k, ey - k, ex + k, ey + k), fill=(40, 40, 40), width=S * 3)
            d.line((ex - k, ey + k, ex + k, ey - k), fill=(40, 40, 40), width=S * 3)
        else:
            d.ellipse((ex - er, ey - er, ex + er, ey + er), fill="white", outline=outline, width=S)
            pr = er * 0.5
            d.ellipse((ex + er * 0.2 - pr, ey - pr, ex + er * 0.2 + pr, ey + pr), fill=(20, 20, 20))
    return img


ROT = {"R": None, "U": Image.ROTATE_90, "L": Image.ROTATE_180, "D": Image.ROTATE_270}


def apple():
    img = canvas(); d = ImageDraw.Draw(img)
    c = C / 2
    # shadow
    sh = canvas(); ImageDraw.Draw(sh).ellipse((C*.2, C*.78, C*.85, C*.93), fill=(0, 0, 0, 70))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(S * 2)))
    d.ellipse((C*.14, C*.24, C*.56, C*.84), fill=(205, 30, 35))
    d.ellipse((C*.44, C*.24, C*.86, C*.84), fill=(205, 30, 35))
    d.ellipse((C*.22, C*.30, C*.78, C*.86), fill=(230, 45, 45))
    d.ellipse((C*.28, C*.36, C*.40, C*.52), fill=(255, 170, 170))        # shine
    d.line((c, C*.30, c + C*.04, C*.10), fill=(100, 60, 20), width=S * 3)  # stem
    d.ellipse((c + C*.04, C*.08, c + C*.30, C*.22), fill=(70, 160, 60))   # leaf
    return img


def grass(color, blade):
    img = Image.new("RGBA", (C, C), color); d = ImageDraw.Draw(img)
    for x, y in ((.2, .3), (.7, .2), (.5, .7), (.15, .8), (.85, .65)):
        d.line((C*x, C*y, C*x + C*.03, C*y - C*.08), fill=blade, width=S * 2)
    return img


def brick():
    img = Image.new("RGBA", (C, C), (120, 110, 105)); d = ImageDraw.Draw(img)  # mortar
    m = S * 2
    rows = [(0, C/2, [(-C/2, C/2), (C/2, C*1.5)]), (C/2, C, [(0, C)])]
    for y0, y1, bricks in rows:
        for x0, x1 in bricks:
            d.rectangle((x0 + m, y0 + m, x1 - m, y1 - m), fill=(165, 75, 55))
            d.rectangle((x0 + m, y0 + m, x1 - m, y0 + m * 3), fill=(195, 105, 80))  # top light
            d.rectangle((x0 + m, y1 - m * 3, x1 - m, y1 - m), fill=(125, 50, 38))   # bottom shade
    return img


def panel(w, h):
    img = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle((0, 0, w * S - 1, h * S - 1), radius=24 * S,
                                          fill=(20, 40, 20, 205), outline=(255, 255, 255, 230),
                                          width=3 * S)
    img.resize((w, h), Image.LANCZOS).save(OUT / "panel.png")


def main():
    OUT.mkdir(exist_ok=True)
    for name, pal in PALETTES.items():
        dead = name == "dead"
        h = head_right(pal, dead)
        for k, rot in ROT.items():
            save(h if rot is None else h.transpose(rot), f"{name}_head_{k}")
            save(tail(pal, k), f"{name}_tail_{k}")
        for i, a in enumerate(ORDER):
            for b in ORDER[i + 1:]:
                save(body(pal, a + b), f"{name}_body_{a}{b}")
    save(apple(), "apple")
    save(grass((170, 215, 81, 255), (150, 195, 65)), "grass_light")
    save(grass((162, 209, 73, 255), (140, 185, 58)), "grass_dark")
    save(brick(), "wall")
    panel(560, 300)
    print(f"Assets written to {OUT}")


if __name__ == "__main__":
    main()
