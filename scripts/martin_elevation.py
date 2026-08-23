"""Prairie elevation painter — Tree of Life, belts, eave, piers.

Used by gen_martin_plans.py and export_martin_fab.py so M-1 / GA-110
cannot accidentally draw a stacked ranch fence again.
"""

from __future__ import annotations

EARTH = "#3a3d38"      # water table
BELT = "#4a4e48"       # thin Prairie ribbons
EAVE = "#2a2e2c"       # cap
FASCIA = "#1a1f24"
CASS = "#ebe4cc"       # opalescent glass field
MUNTIN = "#1c2018"     # Wright came
PIER = "#c4c2ba"
BRICK = "#a8aaa4"
PLANTER = "#6a6e66"
LEAF = "#c9a227"       # Darwin Martin gold squares
GOLD = "#c9a227"
PAPER = "#f3f1ec"
INK = "#1a1f24"
ACC = "#3d5a4c"
DIM = "#5a6a4a"


def paint_motif(s, m, X, Y, S, fill=MUNTIN, stroke=INK, sw=0.7):
    """Paint kernel motif (rects + chevron lines) in sheet space."""
    for r in m.get("rects") or []:
        role = r.get("role", "")
        col = fill
        if role in ("leaf", "jewel", "pot"):
            col = GOLD
        elif role in ("frame", "inner", "ribbon"):
            col = "#2a322c"
        elif role == "trunk":
            col = "#141610"
        elif role == "mullion":
            col = "#1c2018"
        s.rect(X(r["x"]), Y(r["z"] + r["h"]), r["w"] * S, r["h"] * S,
               fill=col, stroke=stroke, sw=sw)
    for ln in m.get("lines") or []:
        t = float(ln.get("t") or 0.75)
        s.line(X(ln["x1"]), Y(ln["z1"]), X(ln["x2"]), Y(ln["z2"]),
               w=max(1.8, t * S * 0.65), color=stroke)


def paint_pier_bricks(s, X, Y, S, cx, fx, z0, z1, faces=1):
    """Roman-brick 2×2 wrapping hint on a pier (front elevation)."""
    bs = 1.5
    gap = 0.18
    x0 = cx - fx / 2.0 - 0.35
    w = fx + 0.7
    z = z0 + 0.2
    row = 0
    while z + bs <= z1 - 0.2:
        offset = (bs / 2.0) if row % 2 else 0.0
        x = x0 + offset
        while x + bs <= x0 + w + 0.01:
            s.rect(X(x), Y(z + bs), bs * S, bs * S, fill=BRICK, stroke="#8a8c86", sw=0.4)
            x += bs + gap
        z += bs + gap
        row += 1


def paint_front_elevation(s, ly, X, Y, S, v, *, gate=True, labels=True, planters=True, posts_on_top=True):
    """Garden-face elevation. Order: sill → water table → cassettes → belts → piers → eave → gate."""
    fx = v("post_x")
    H = ly["overall_height"]
    L = ly["overall_length"]
    posts = ly["posts"]
    cap_t = v("cap_t")
    fascia_h = v("fascia_h")
    cap_x0 = ly["cap_x0"]
    cap_len = ly["cap_len"]
    nuki_x0 = ly["nuki_x0"]
    nuki_len = ly["nuki_len"]
    slats = {s0["id"]: s0 for s0 in ly["slats"]}

    # dodai sill
    s.rect(X(-v("sill_overhang")), Y(0),
           (L + 2 * v("sill_overhang")) * S, v("sill_h") * S,
           fill="#9a9890", stroke=INK, sw=1.4)

    # recessed cassette fields first (behind belts)
    for sl in ly["slats"]:
        if not sl["id"].startswith("Q-"):
            continue
        s.rect(X(nuki_x0 + 0.4), Y(sl["z1"]),
               (nuki_len - 0.8) * S, sl["h"] * S,
               fill=CASS, stroke="none", sw=0)

    # motifs in privacy bays + gate
    for m in ly["motifs"]:
        if m.get("bay") == "gate" and not gate:
            continue
        if m.get("bay") == "gate":
            continue  # gate painted with leaf below
        paint_motif(s, m, X, Y, S)

    # water table + belts — project past piers
    kick = slats["K-001"]
    s.rect(X(nuki_x0), Y(kick["z1"]), nuki_len * S, kick["h"] * S,
           fill=EARTH, stroke=INK, sw=1.4)
    for bid in ("R-001", "R-002"):
        b = slats[bid]
        s.rect(X(nuki_x0), Y(b["z1"]), nuki_len * S, b["h"] * S,
               fill=BELT, stroke=INK, sw=1.3)

    # piers P0–P3 (P1–P3 get brick wrap)
    for i, p in enumerate(posts):
        cx, mark = p["cx"], p["mark"]
        s.rect(X(cx - fx / 2), Y(H - cap_t), fx * S, (H - cap_t) * S,
               fill=PIER, stroke=INK, sw=1.6)
        if mark != "P0":
            paint_pier_bricks(s, X, Y, S, cx, fx, 2.0, H - cap_t - 1.0)
        if labels:
            s.text(X(cx), Y(H) - 20, mark, 13, ACC, "middle", bold=True)

    # cantilevered eave + hanging fascia (the Wright move)
    s.rect(X(cap_x0), Y(H), cap_len * S, cap_t * S, fill=EAVE, stroke=INK, sw=1.4)
    s.rect(X(cap_x0), Y(H - cap_t), cap_len * S, fascia_h * S,
           fill=FASCIA, stroke=INK, sw=1.0)
    # latch-post stub
    p0 = posts[0]["cx"]
    s.rect(X(p0 - fx / 2 - 0.5), Y(H), (fx + 1.0) * S, cap_t * S,
           fill=EAVE, stroke=INK, sw=1.2)

    # live planters as architectural troughs aligned with water table (garden face, privacy bays)
    if planters:
        for left, right in ((1, 2), (2, 3)):
            x0 = posts[left]["cx"] + fx / 2.0 + 0.4
            x1 = posts[right]["cx"] - fx / 2.0 - 0.4
            ph = min(v("planter_h"), kick["h"] + 6.0)
            s.rect(X(x0), Y(ph * 0.42), (x1 - x0) * S, ph * 0.42 * S,
                   fill=PLANTER, stroke=INK, sw=1.1)
            if labels:
                s.text(X((x0 + x1) / 2), Y(ph * 0.21) + 4, "PLANTER", 9, PAPER, "middle", bold=True)

    # gate — Tree of Life portal, no Z-brace
    if gate:
        gx0 = fx + v("gate_gap")
        gw = ly["gate_leaf_w"]
        gh = ly["gate_h"]
        gz0 = v("gate_bottom_clear")
        s.rect(X(gx0), Y(gz0 + gh), gw * S, gh * S, fill=CASS, stroke=ACC, sw=2)
        stile = v("stile_w")
        s.rect(X(gx0), Y(gz0 + gh), stile * S, gh * S, fill=PIER, stroke=INK, sw=1.2)
        s.rect(X(gx0 + gw - stile), Y(gz0 + gh), stile * S, gh * S, fill=PIER, stroke=INK, sw=1.2)
        # gate motifs
        for m in ly["motifs"]:
            if m.get("bay") == "gate":
                paint_motif(s, m, X, Y, S)
        # belts continue across the gate as thin projecting rails
        for bid in ("R-001", "R-002"):
            b = slats[bid]
            s.rect(X(gx0 + stile), Y(b["z1"]), (gw - 2 * stile) * S, b["h"] * S,
                   fill=BELT, stroke=INK, sw=0.8)
        if labels:
            s.text(X(gx0 + gw / 2), Y(2.4), "GATE · TREE OF LIFE", 11, PAPER, "middle", bold=True)

    if labels:
        s.text(X(L / 2), Y(-v("sill_h") / 2) + 5, "DODAI — SIT ON DRIVEWAY", 11, DIM, "middle")


class _HeroSheet:
    """Minimal painter target for the landing/app hero SVG."""

    def __init__(self):
        self.b = []

    def add(self, s):
        self.b.append(s)

    def line(self, x1, y1, x2, y2, w=2, color=INK, dash=None):
        d = f" stroke-dasharray='{dash}'" if dash else ""
        self.add(
            f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' "
            f"stroke='{color}' stroke-width='{w}'{d}/>"
        )

    def rect(self, x, y, w, h, fill="none", stroke=INK, sw=2, dash=None):
        d = f" stroke-dasharray='{dash}'" if dash else ""
        st = "none" if stroke == "none" else stroke
        self.add(
            f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' "
            f"fill='{fill}' stroke='{st}' stroke-width='{sw}'{d}/>"
        )

    def text(self, x, y, s, size=16, color=INK, anchor="start", bold=False, *args, **kwargs):
        wgt = " font-weight='600'" if bold else ""
        self.add(
            f"<text x='{x:.1f}' y='{y:.1f}' font-family='IBM Plex Mono,monospace' "
            f"font-size='{size}' fill='{color}' text-anchor='{anchor}'{wgt}>{s}</text>"
        )


def write_hero_svg(path, ly, v, *, dark=True):
    """Garden-face hero for landing / app — generated from kernel motifs, not a screenshot."""
    import os
    W, Hpx = 1600, 720
    S = 8.4
    OX, OY = 70, 580
    bg = "#14181c" if dark else PAPER
    s = _HeroSheet()
    s.rect(0, 0, W, Hpx, fill=bg, stroke="none", sw=0)

    def X(xin):
        return OX + xin * S

    def Y(zin):
        return OY - zin * S

    paint_front_elevation(s, ly, X, Y, S, v, gate=True, labels=False, planters=True)
    ink = "#e8e0c8" if dark else INK
    s.text(40, 40, "MARTIN  ·  DARWIN MARTIN TREE OF LIFE  ·  143″ × 65″  ·  BUFFALO", 14, ink, "start", True)
    s.text(40, Hpx - 28, "NOT A RANCH FENCE  ·  2×4 PRAIRIE RIBBONS  ·  GOLD SQUARES  ·  NO Z-BRACE", 12, GOLD, "start", True)
    svg = (
        f"<?xml version='1.0' encoding='UTF-8'?>\n"
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{Hpx}' "
        f"viewBox='0 0 {W} {Hpx}' role='img' aria-label='MARTIN Tree of Life fence'>\n"
        + "\n".join(s.b)
        + "\n</svg>\n"
    )
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return path

