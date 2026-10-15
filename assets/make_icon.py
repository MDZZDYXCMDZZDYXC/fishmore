#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the fishmore plugin icon.

The icon states the gameplay rather than an abstract motif:

* **a fishing rod cast over water** -- the plugin is nothing but the vanilla
  fishing loop, unchanged: cast, wait, reel in.
* **what comes out of the water** -- a fish (the vanilla catch) rising together
  with a diamond, an apple and a few sparkles (the "extra" catches this plugin
  adds). That is literally the feature: the same rod now also pulls up items
  that vanilla fishing never gives you.
* **the wordmark FISHMORE** -- this project's own name.

Two outputs come from one geometry definition, shared by both backends as a
small primitive list (so the SVG and the PNG can never drift apart):

* ``icon.svg``  -- vector source, built with plain string concatenation, no
  third-party dependency (same approach as the reference project `two048`).
* ``icon-64/128/256/512.png`` -- rasterised with Pillow when available, drawn at
  4x and downsampled, which is what keeps the edges clean.
"""

import os

# ---------------------------------------------------------------------------
# Palette (Minecraft named colours where they apply)
# ---------------------------------------------------------------------------
WATER_DEEP = "#2E5FB0"
WATER_SURF = "#4FA3E3"
WATER_WAVE = "#8FD0F5"
FOAM = "#EAF9FF"

ROD_WOOD = "#7A5230"
ROD_GRIP = "#3A2712"
REEL = "#8F8F8F"
REEL_RING = "#565656"
REEL_HUB = "#D2D2D2"
LINE = "#D9D9D9"

BOB_TOP = "#E23B3B"
BOB_BOT = "#F4F4F4"

FISH = "#F0A03C"
FISH_DARK = "#C77A20"
FISH_BELLY = "#FBD9A0"

DIAMOND = "#48E0CC"
DIAMOND_HI = "#A9F3E8"

APPLE = "#E33B3B"
APPLE_HI = "#FF8A8A"
LEAF = "#5FBF3F"
STEM = "#6B4A2B"

GOLD = "#FFD84D"
SLIME = "#55FF55"

BADGE_TOP = (26, 26, 37)
BADGE_MID = (18, 18, 25)
BADGE_BOTTOM = (10, 10, 16)

# ---------------------------------------------------------------------------
# Geometry (512x512 design space)
# ---------------------------------------------------------------------------
W = H = 512
BADGE_RADIUS = 112.0

# water: a band across the bottom, with the surface line at its top
WATER_Y = 392.0
WATER_H = H - WATER_Y
WAVE_1 = [(0.0, 398.0), (128.0, 384.0), (256.0, 398.0)]
WAVE_2 = [(256.0, 398.0), (384.0, 412.0), (512.0, 398.0)]
WAVE_3 = [(0.0, 424.0), (150.0, 412.0), (300.0, 424.0)]

# rod: from the grip in the water up to the tip in the upper right
ROD_A = (96.0, 392.0)      # handle end
ROD_M = (234.0, 255.0)     # joint between the two tapered segments
ROD_B = (372.0, 118.0)     # tip
ROD_W_LOW = 18.0
ROD_W_HIGH = 12.0
GRIP_END = (140.0, 348.0)  # where the dark grip stops
GRIP_W = 23.0

REEL_C = (146.0, 343.0)
REEL_R = 17.0

# line: a slack curve from the rod tip down to the bobber
LINE_CTRL = (330.0, 250.0)
BOBBER = (322.0, 392.0)

# the catch: a fish flanked by "extra" items that vanilla fishing never gives
FISH_C = (262.0, 300.0)
FISH_RX, FISH_RY = 48.0, 26.0
DIAMOND_C = (168.0, 236.0)
DIAMOND_R = 34.0
APPLE_C = (312.0, 240.0)
APPLE_R = 27.0

SPARKLES = [
    (188.0, 150.0, 13.0, GOLD, 0.92),
    (430.0, 244.0, 10.0, GOLD, 0.80),
    (88.0, 244.0, 9.0, GOLD, 0.72),
]

DROPS = [
    (272.0, 366.0, 7.0),
    (334.0, 362.0, 6.0),
    (302.0, 344.0, 5.0),
    (286.0, 380.0, 5.0),
    (352.0, 380.0, 4.0),
]

WORDMARK_BASELINE, WORDMARK_SIZE = 472.0, 24.0
WORDMARK_TRACKING = 4.0

FONT_UI = "'Segoe UI Semibold', 'Segoe UI', 'DejaVu Sans', Arial, sans-serif"


# ---------------------------------------------------------------------------
# Primitive list (shared by the SVG and PNG backends)
#
# Each primitive is a dict; the two renderers below translate the same list, so
# there is exactly one geometry definition.
# ---------------------------------------------------------------------------
def _star(cx, cy, size):
    inner = size * 0.28
    return [
        (cx, cy - size), (cx + inner, cy - inner), (cx + size, cy),
        (cx + inner, cy + inner), (cx, cy + size), (cx - inner, cy + inner),
        (cx - size, cy), (cx - inner, cy - inner),
    ]


def build_primitives():
    p = []
    add = p.append

    # ---- water + waves (clipped to the badge by the backends) ----
    add({"t": "rect", "x": 0.0, "y": WATER_Y, "w": W, "h": WATER_H,
         "fill": WATER_DEEP, "alpha": 1.0})
    add({"t": "rect", "x": 0.0, "y": WATER_Y, "w": W, "h": 36.0,
         "fill": WATER_SURF, "alpha": 1.0})
    for wave in (WAVE_1, WAVE_2, WAVE_3):
        add({"t": "poly", "pts": wave, "stroke": WATER_WAVE,
             "width": 5.0, "alpha": 0.75})

    # ---- splash ripples around the bobber ----
    add({"t": "ring", "cx": BOBBER[0], "cy": BOBBER[1], "rx": 82.0, "ry": 16.0,
         "stroke": FOAM, "width": 3.0, "alpha": 0.45})
    add({"t": "ring", "cx": BOBBER[0], "cy": BOBBER[1], "rx": 50.0, "ry": 9.0,
         "stroke": FOAM, "width": 2.5, "alpha": 0.30})
    for dx, dy, r in DROPS:
        add({"t": "dot", "cx": dx, "cy": dy, "r": r, "fill": FOAM, "alpha": 0.90})

    # ---- the catch: fish + extra items, all lifted off the water ----
    # fish (body facing left, tail on the right)
    add({"t": "poly", "pts": [
        (FISH_C[0] + FISH_RX, FISH_C[1]),
        (FISH_C[0] + FISH_RX + 42.0, FISH_C[1] - 24.0),
        (FISH_C[0] + FISH_RX + 42.0, FISH_C[1] + 24.0),
    ], "fill": FISH, "alpha": 1.0})
    add({"t": "poly", "pts": [
        (FISH_C[0] - 4.0, FISH_C[1] - FISH_RY + 4.0),
        (FISH_C[0] + 18.0, FISH_C[1] - FISH_RY - 24.0),
        (FISH_C[0] + 34.0, FISH_C[1] - FISH_RY + 2.0),
    ], "fill": FISH_DARK, "alpha": 0.95})
    add({"t": "dot", "cx": FISH_C[0], "cy": FISH_C[1], "rx": FISH_RX, "ry": FISH_RY,
         "fill": FISH, "alpha": 1.0})
    add({"t": "dot", "cx": FISH_C[0] - 10.0, "cy": FISH_C[1] + 10.0, "rx": 24.0, "ry": 9.0,
         "fill": FISH_BELLY, "alpha": 0.55})
    add({"t": "dot", "cx": FISH_C[0] - FISH_RX + 16.0, "cy": FISH_C[1] - 6.0, "r": 5.0,
         "fill": "#20120A", "alpha": 1.0})

    # diamond (an isometric rhombus with light facets)
    dcx, dcy = DIAMOND_C
    dr = DIAMOND_R
    add({"t": "poly", "pts": [
        (dcx, dcy - dr), (dcx + dr, dcy), (dcx, dcy + dr), (dcx - dr, dcy),
    ], "fill": DIAMOND, "alpha": 1.0})
    add({"t": "poly", "pts": [
        (dcx, dcy - dr), (dcx + dr * 0.30, dcy - dr * 0.10),
        (dcx, dcy + dr * 0.10), (dcx - dr * 0.30, dcy - dr * 0.10),
    ], "fill": DIAMOND_HI, "alpha": 0.55})
    for vx, vy in ((dcx, dcy - dr), (dcx + dr, dcy), (dcx, dcy + dr), (dcx - dr, dcy)):
        add({"t": "poly", "pts": [(vx, vy), (dcx, dcy)], "stroke": DIAMOND_HI,
             "width": 2.0, "alpha": 0.55})

    # apple (a red fruit with a stem and a leaf)
    add({"t": "dot", "cx": APPLE_C[0], "cy": APPLE_C[1], "r": APPLE_R,
         "fill": APPLE, "alpha": 1.0})
    add({"t": "dot", "cx": APPLE_C[0] - APPLE_R * 0.30, "cy": APPLE_C[1] - APPLE_R * 0.34,
         "rx": APPLE_R * 0.42, "ry": APPLE_R * 0.24, "fill": APPLE_HI, "alpha": 0.75})
    add({"t": "poly", "pts": [
        (APPLE_C[0], APPLE_C[1] - APPLE_R + 2.0),
        (APPLE_C[0] + 3.0, APPLE_C[1] - APPLE_R - 12.0),
    ], "stroke": STEM, "width": 4.0, "alpha": 1.0})
    add({"t": "poly", "pts": [
        (APPLE_C[0] + 3.0, APPLE_C[1] - APPLE_R - 12.0),
        (APPLE_C[0] + 20.0, APPLE_C[1] - APPLE_R - 16.0),
        (APPLE_C[0] + 8.0, APPLE_C[1] - APPLE_R - 2.0),
    ], "fill": LEAF, "alpha": 1.0})

    # sparkles: "there is more where that came from"
    for cx, cy, size, color, alpha in SPARKLES:
        add({"t": "poly", "pts": _star(cx, cy, size), "fill": color, "alpha": alpha})

    # ---- rod ----
    add({"t": "poly", "pts": [ROD_A, ROD_M], "stroke": ROD_WOOD,
         "width": ROD_W_LOW, "alpha": 1.0})
    add({"t": "poly", "pts": [ROD_M, ROD_B], "stroke": ROD_WOOD,
         "width": ROD_W_HIGH, "alpha": 1.0})
    add({"t": "poly", "pts": [ROD_A, GRIP_END], "stroke": ROD_GRIP,
         "width": GRIP_W, "alpha": 1.0})
    add({"t": "dot", "cx": REEL_C[0], "cy": REEL_C[1], "r": REEL_R + 6.0,
         "fill": REEL_RING, "alpha": 1.0})
    add({"t": "dot", "cx": REEL_C[0], "cy": REEL_C[1], "r": REEL_R,
         "fill": REEL, "alpha": 1.0})
    add({"t": "dot", "cx": REEL_C[0], "cy": REEL_C[1], "r": 6.0,
         "fill": REEL_HUB, "alpha": 1.0})

    # ---- line + bobber ----
    add({"t": "quad", "p0": ROD_B, "ctrl": LINE_CTRL, "p1": BOBBER,
         "stroke": LINE, "width": 3.2, "alpha": 0.95})
    add({"t": "rect", "x": BOBBER[0] - 9.0, "y": BOBBER[1] - 26.0, "w": 18.0, "h": 26.0,
         "r": 4.0, "fill": BOB_TOP, "alpha": 1.0})
    add({"t": "rect", "x": BOBBER[0] - 9.0, "y": BOBBER[1] - 6.0, "w": 18.0, "h": 18.0,
         "r": 4.0, "fill": BOB_BOT, "alpha": 1.0})

    # ---- wordmark ----
    add({"t": "text", "x": W / 2, "y": WORDMARK_BASELINE, "s": WORDMARK_SIZE,
         "anchor": "middle", "fill": FOAM, "alpha": 0.98, "tracking": WORDMARK_TRACKING,
         "content": "FISHMORE"})

    return p


# ---------------------------------------------------------------------------
# SVG backend
# ---------------------------------------------------------------------------
def _svg_prim(pr):
    t = pr["t"]
    if t == "rect":
        return (f'<rect x="{pr["x"]}" y="{pr["y"]}" width="{pr["w"]}" '
                f'height="{pr["h"]}" fill="{pr["fill"]}" fill-opacity="{pr["alpha"]}"/>')
    if t == "dot":
        rx = pr.get("rx", pr.get("r"))
        ry = pr.get("ry", pr.get("r"))
        return (f'<ellipse cx="{pr["cx"]}" cy="{pr["cy"]}" rx="{rx}" ry="{ry}" '
                f'fill="{pr["fill"]}" fill-opacity="{pr["alpha"]}"/>')
    if t == "ring":
        return (f'<ellipse cx="{pr["cx"]}" cy="{pr["cy"]}" rx="{pr["rx"]}" ry="{pr["ry"]}" '
                f'fill="none" stroke="{pr["stroke"]}" stroke-width="{pr["width"]}" '
                f'stroke-opacity="{pr["alpha"]}"/>')
    if t == "poly":
        pts = " ".join(f"{x},{y}" for x, y in pr["pts"])
        if "stroke" in pr:
            return (f'<polyline points="{pts}" fill="none" stroke="{pr["stroke"]}" '
                    f'stroke-width="{pr["width"]}" stroke-opacity="{pr["alpha"]}" '
                    'stroke-linecap="round" stroke-linejoin="round"/>')
        return f'<polygon points="{pts}" fill="{pr["fill"]}" fill-opacity="{pr["alpha"]}"/>'
    if t == "quad":
        (x0, y0), (cx, cy), (x1, y1) = pr["p0"], pr["ctrl"], pr["p1"]
        return (f'<path d="M{x0} {y0} Q{cx} {cy} {x1} {y1}" fill="none" '
                f'stroke="{pr["stroke"]}" stroke-width="{pr["width"]}" '
                f'stroke-opacity="{pr["alpha"]}" stroke-linecap="round"/>')
    if t == "text":
        stroke = ""
        if pr.get("stroke"):
            stroke = (f' stroke="{pr["stroke"]}" stroke-width="{pr["stroke_w"]}" '
                      'paint-order="stroke"')
        return (f'<text x="{pr["x"]}" y="{pr["y"]}" text-anchor="{pr["anchor"]}" '
                f'font-family="{FONT_UI}" font-size="{pr["s"]}" font-weight="700" '
                f'letter-spacing="{pr["tracking"]}" fill="{pr["fill"]}" '
                f'fill-opacity="{pr["alpha"]}"{stroke}>{pr["content"]}</text>')
    raise ValueError(t)


def build_svg():
    a = []
    add = a.append
    add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="fishmore plugin icon">')
    add("<title>fishmore</title>")
    add("<desc>A fishing rod cast over water, pulling up a fish together with a "
        "diamond, an apple and sparkles - the extra items this plugin adds to "
        "vanilla fishing.</desc>")
    add("<defs>")
    add('<linearGradient id="badge" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#1A1A25"/>'
        '<stop offset="0.55" stop-color="#121219"/>'
        '<stop offset="1" stop-color="#0A0A10"/></linearGradient>')
    add('<radialGradient id="warm" cx="0.20" cy="0.10" r="0.66">'
        '<stop offset="0" stop-color="#FF8A3D" stop-opacity="0.16"/>'
        '<stop offset="1" stop-color="#FF8A3D" stop-opacity="0"/></radialGradient>')
    add('<radialGradient id="cool" cx="0.86" cy="0.98" r="0.64">'
        '<stop offset="0" stop-color="#55FFFF" stop-opacity="0.12"/>'
        '<stop offset="1" stop-color="#55FFFF" stop-opacity="0"/></radialGradient>')
    add(f'<clipPath id="badgeclip"><rect width="{W}" height="{H}" '
        f'rx="{BADGE_RADIUS}"/></clipPath>')
    add("</defs>")

    add(f'<rect width="{W}" height="{H}" rx="{BADGE_RADIUS}" fill="url(#badge)"/>')
    add(f'<rect width="{W}" height="{H}" rx="{BADGE_RADIUS}" fill="url(#warm)"/>')
    add(f'<rect width="{W}" height="{H}" rx="{BADGE_RADIUS}" fill="url(#cool)"/>')

    add('<g clip-path="url(#badgeclip)">')
    for pr in build_primitives():
        add(_svg_prim(pr))
    add("</g>")

    add(f'<rect x="1.5" y="1.5" width="{W - 3}" height="{H - 3}" rx="{BADGE_RADIUS - 1.5}" '
        'fill="none" stroke="#FFFFFF" stroke-opacity="0.10" stroke-width="3"/>')
    add("</svg>")
    return "\n".join(a)


# ---------------------------------------------------------------------------
# PNG backend (Pillow), drawn at 4x then downsampled
# ---------------------------------------------------------------------------
S = 4


def _hex(value):
    return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))


def _font(paths, size):
    from PIL import ImageFont
    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def _diagonal_gradient(size):
    from PIL import Image
    tiny = Image.new("RGB", (2, 2))
    tiny.putpixel((0, 0), (30, 30, 42))
    tiny.putpixel((1, 0), BADGE_TOP)
    tiny.putpixel((0, 1), BADGE_MID)
    tiny.putpixel((1, 1), BADGE_BOTTOM)
    return tiny.resize((size, size), Image.BICUBIC).convert("RGBA")


def _radial_glow(size, cx, cy, radius, color, max_alpha):
    from PIL import Image, ImageDraw
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    steps = 72
    for step in range(steps, 0, -1):
        t = step / steps
        r = radius * t
        alpha = int(max_alpha * (1.0 - t) ** 1.7)
        if alpha > 0:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*color, alpha))
    return layer


def _draw_tracking(draw, text, x, y, font, tracking, fill, stroke_w=0, stroke_fill=None):
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * max(0, len(text) - 1)
    cur = x - total / 2
    for ch, w in zip(text, widths):
        kwargs = {"font": font, "fill": fill, "anchor": "ls"}
        if stroke_w:
            kwargs["stroke_width"] = stroke_w
            kwargs["stroke_fill"] = stroke_fill
        draw.text((cur, y), ch, **kwargs)
        cur += w + tracking


def _quad_points(p0, ctrl, p1, steps=40):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        mt = 1 - t
        x = mt * mt * p0[0] + 2 * mt * t * ctrl[0] + t * t * p1[0]
        y = mt * mt * p0[1] + 2 * mt * t * ctrl[1] + t * t * p1[1]
        pts.append((x, y))
    return pts


def render_pngs(out_dir):
    from PIL import Image, ImageChops, ImageDraw

    size = W * S

    def sx(v):
        return v * S

    img = _diagonal_gradient(size)
    img = Image.alpha_composite(img, _radial_glow(size, sx(112), sx(62), sx(240), (255, 138, 61), 30))
    img = Image.alpha_composite(img, _radial_glow(size, sx(430), sx(500), sx(228), (85, 255, 255), 26))

    shapes = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(shapes, "RGBA")

    ui = _font(
        ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/segoeui.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
        int(sx(WORDMARK_SIZE)),
    )

    for pr in build_primitives():
        t = pr["t"]
        a = int(pr.get("alpha", 1.0) * 255)
        if t == "rect":
            col = (*_hex(pr["fill"]), a)
            r = int(sx(pr.get("r", 0.0)))
            if r > 0:
                d.rounded_rectangle([sx(pr["x"]), sx(pr["y"]),
                                     sx(pr["x"] + pr["w"]), sx(pr["y"] + pr["h"])],
                                    radius=r, fill=col)
            else:
                d.rectangle([sx(pr["x"]), sx(pr["y"]),
                             sx(pr["x"] + pr["w"]), sx(pr["y"] + pr["h"])], fill=col)
        elif t == "dot":
            rx = pr.get("rx", pr.get("r"))
            ry = pr.get("ry", pr.get("r"))
            d.ellipse([sx(pr["cx"] - rx), sx(pr["cy"] - ry),
                       sx(pr["cx"] + rx), sx(pr["cy"] + ry)], fill=(*_hex(pr["fill"]), a))
        elif t == "ring":
            d.ellipse([sx(pr["cx"] - pr["rx"]), sx(pr["cy"] - pr["ry"]),
                       sx(pr["cx"] + pr["rx"]), sx(pr["cy"] + pr["ry"])],
                      outline=(*_hex(pr["stroke"]), a), width=int(sx(pr["width"])))
        elif t == "poly":
            pts = [(sx(x), sx(y)) for x, y in pr["pts"]]
            if "stroke" in pr:
                d.line(pts, fill=(*_hex(pr["stroke"]), a), width=int(sx(pr["width"])),
                       joint="curve")
                # round the endpoints to match SVG's stroke-linecap
                rad = sx(pr["width"]) / 2
                for x, y in (pts[0], pts[-1]):
                    d.ellipse([x - rad, y - rad, x + rad, y + rad],
                              fill=(*_hex(pr["stroke"]), a))
            else:
                d.polygon(pts, fill=(*_hex(pr["fill"]), a))
        elif t == "quad":
            pts = [(sx(x), sx(y)) for x, y in _quad_points(pr["p0"], pr["ctrl"], pr["p1"])]
            d.line(pts, fill=(*_hex(pr["stroke"]), a), width=int(sx(pr["width"])),
                   joint="curve")
        elif t == "text":
            _draw_tracking(
                d, pr["content"], sx(pr["x"]), sx(pr["y"]), ui, sx(pr["tracking"]),
                (*_hex(pr["fill"]), a),
                stroke_w=int(sx(pr["stroke_w"])) if pr.get("stroke") else 0,
                stroke_fill=(*_hex(pr["stroke"]), a) if pr.get("stroke") else None,
            )
        else:
            raise ValueError(t)

    img = Image.alpha_composite(img, shapes)

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=int(sx(BADGE_RADIUS)), fill=255)
    img.putalpha(ImageChops.multiply(img.getchannel("A"), mask))

    written = []
    for px in (512, 256, 128, 64):
        path = os.path.join(out_dir, f"icon-{px}.png")
        img.resize((px, px), Image.LANCZOS).save(path, "PNG", optimize=True)
        written.append(path)
    return written


def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    svg_path = os.path.join(out_dir, "icon.svg")
    with open(svg_path, "w", encoding="utf-8") as fh:
        fh.write(build_svg())
    print(svg_path)
    try:
        for path in render_pngs(out_dir):
            print(path)
    except ImportError:
        print("Pillow not installed; skipped PNG rendering (icon.svg is still written).")


if __name__ == "__main__":
    main()
