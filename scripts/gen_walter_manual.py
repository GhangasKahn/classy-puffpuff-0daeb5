#!/usr/bin/env python3
"""WALTER Rev C — LEGO-style step-by-step build manual (WOODWRIGHT PLANFORGE).

Numbered steps, bag callouts, insertion arrows, progressive assembly.
Generated from walter_project.build_project() — same IDs as the guidebook.

Run:  python3 scripts/gen_walter_manual.py
"""

from __future__ import annotations

import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAD = os.path.join(ROOT, "sander", "walter", "cad")
sys.path.insert(0, CAD)

from walter_kernel import REV, assembly  # noqa: E402
from walter_project import BAGS, build_project  # noqa: E402

OUT = os.path.join(ROOT, "sander", "walter", "manual")
os.makedirs(OUT, exist_ok=True)

PROJ = build_project()
PARTS = {p["PART_ID"]: p for p in PROJ["parts"]}
STEPS = PROJ["steps"]
TOTAL = len(STEPS)

INK, DIM, ACC, PAPER = "#1c1914", "#6b5340", "#b4532a", "#f4efe6"
HL, LIGHT, STEEL = "#b4532a", "#d4cbb8", "#5c656c"
DRUM, BELT, SAFE = "#7a5a3a", "#2a2a2c", "#3d5a4c"
W, Hpx = 1680, 1188
MONO = "font-family='IBM Plex Mono, Menlo, monospace'"
SER = "font-family='Georgia, serif'"
PAGES = []

GROUP_FILL = {
    "frame": "#c4a574",
    "steel": "#6a7278",
    "drum": "#b4532a",
    "table": "#e8eef0",
    "conveyor": "#2a2a2c",
    "motor": "#161616",
    "hood": "#3d4a46",
    "guard": "#8a6a42",
    "stand": "#6e5638",
}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Sheet:
    def __init__(self, footer_left, footer_right):
        self.fl, self.fr = footer_left, footer_right
        self.b = []

    def add(self, s):
        self.b.append(s)

    def line(self, x1, y1, x2, y2, w=2, color=INK, dash=None):
        d = f" stroke-dasharray='{dash}'" if dash else ""
        self.add(f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' stroke='{color}' stroke-width='{w}'{d}/>")

    def rect(self, x, y, w, h, fill="none", stroke=INK, sw=2, dash=None, rx=None):
        d = f" stroke-dasharray='{dash}'" if dash else ""
        r = f" rx='{rx}'" if rx else ""
        self.add(f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}'{d}{r}/>")

    def poly(self, pts, fill="none", stroke=INK, sw=2):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.add(f"<polygon points='{p}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}' stroke-linejoin='round'/>")

    def circle(self, cx, cy, r, fill="none", stroke=INK, sw=2):
        self.add(f"<circle cx='{cx:.1f}' cy='{cy:.1f}' r='{r:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}'/>")

    def ellipse(self, cx, cy, rx, ry, fill="none", stroke=INK, sw=2):
        self.add(f"<ellipse cx='{cx:.1f}' cy='{cy:.1f}' rx='{rx:.1f}' ry='{ry:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}'/>")

    def text(self, x, y, s, size=16, color=INK, anchor="start", bold=False, mono=True):
        f = MONO if mono else SER
        wgt = " font-weight='600'" if bold else ""
        self.add(f"<text x='{x:.1f}' y='{y:.1f}' {f} font-size='{size}' fill='{color}' text-anchor='{anchor}'{wgt}>{esc(s)}</text>")

    def arrow(self, x1, y1, x2, y2, color=HL, w=7):
        ang = math.atan2(y2 - y1, x2 - x1)
        L, Wd = 22, 11
        p1 = (x2 - L * math.cos(ang) + Wd * math.sin(ang), y2 - L * math.sin(ang) - Wd * math.cos(ang))
        p2 = (x2 - L * math.cos(ang) - Wd * math.sin(ang), y2 - L * math.sin(ang) + Wd * math.cos(ang))
        self.line(x1, y1, x2 - 14 * math.cos(ang), y2 - 14 * math.sin(ang), w, color)
        self.poly([(x2, y2), p1, p2], fill=color, stroke=color, sw=1)

    def no_icon(self, cx, cy, word, label):
        self.circle(cx, cy, 30, fill=PAPER, stroke=INK, sw=3)
        self.text(cx, cy + 5, word, 11, INK, "middle", bold=True)
        self.line(cx - 21, cy - 21, cx + 21, cy + 21, 5, HL)
        self.text(cx, cy + 52, label, 11, DIM, "middle")

    def balloon(self, x, y, n):
        self.circle(x, y, 14, fill=PAPER, stroke=INK, sw=2)
        self.text(x, y + 5, str(n), 14, INK, "middle", bold=True)

    def frame(self):
        self.b.insert(0, f"<rect x='0' y='0' width='{W}' height='{Hpx}' fill='{PAPER}' stroke='{INK}' stroke-width='3'/>")
        self.b.insert(1, f"<rect x='24' y='24' width='{W - 48}' height='{Hpx - 48}' fill='none' stroke='{INK}' stroke-width='1.2'/>")
        self.line(24, Hpx - 88, W - 24, Hpx - 88, 1.4)
        self.text(40, Hpx - 56, "WALTER", 26, ACC, bold=True, mono=False)
        self.text(185, Hpx - 58, self.fl, 15, INK, bold=True)
        self.text(40, Hpx - 34, "16″ drum sander · PLANFORGE v1.0 · NOT a ShopNotes reprint · do not scale this page", 12, DIM)
        self.text(W - 40, Hpx - 56, self.fr, 14, DIM, "end")
        self.text(W - 40, Hpx - 34, f"Generated from walter_kernel.py · Rev {REV}", 12, DIM, "end")

    def save(self, filename, caption):
        self.frame()
        svg = (
            f"<?xml version='1.0' encoding='UTF-8'?>\n"
            f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{Hpx}' viewBox='0 0 {W} {Hpx}'>\n"
            + "\n".join(self.b)
            + "\n</svg>\n"
        )
        path = os.path.join(OUT, filename)
        with open(path, "w") as f:
            f.write(svg)
        PAGES.append((filename, caption))
        print("wrote", os.path.relpath(path, ROOT))


def step_sheet(n, bag, title, note=""):
    s = Sheet(f"BUILD MANUAL · STEP {n} OF {TOTAL}", f"BAG {bag} · Rev {REV}")
    s.rect(40, 46, 150, 118, fill=PAPER, stroke=INK, sw=4, rx=16)
    s.text(115, 136, str(n), 84, INK, "middle", bold=True)
    s.rect(206, 46, 128, 40, fill=ACC, stroke=INK, sw=2, rx=10)
    s.text(270, 72, f"BAG {bag}", 16, PAPER, "middle", bold=True)
    s.text(206, 122, title, 21, ACC, bold=True)
    if note:
        s.text(206, 150, note, 13, DIM)
    return s


def parts_box(s, items, x=40, y=188):
    if not items:
        s.rect(x, y, 330, 70, fill="#eceae2", stroke=INK, sw=2.5, rx=14)
        s.text(x + 16, y + 30, "NO NEW PARTS THIS STEP", 13, ACC, bold=True)
        s.text(x + 16, y + 52, "Inspection / tune only.", 12, DIM)
        return y + 80
    hgt = 46 + 52 * len(items)
    s.rect(x, y, 330, hgt, fill="#eceae2", stroke=INK, sw=2.5, rx=14)
    s.text(x + 16, y + 30, "PARTS THIS STEP", 13, ACC, bold=True)
    yy = y + 50
    for qty, pid, label in items:
        p = PARTS.get(pid, {})
        fill = GROUP_FILL.get(p.get("GROUP", "frame"), LIGHT)
        s.rect(x + 16, yy, 36, 22, fill=fill, stroke=INK, sw=1.3)
        s.text(x + 60, yy + 17, f"{qty}×  {pid}", 15, HL, bold=True)
        s.text(x + 16, yy + 40, label, 12, INK)
        yy += 52
    return y + hgt


def warn(s, x, y, w, lines):
    s.rect(x, y, w, 22 + 18 * len(lines), fill="#f7e8de", stroke=HL, sw=2, rx=8)
    for i, ln in enumerate(lines):
        s.text(x + 14, y + 22 + i * 18, ln, 13, INK if i else HL, bold=(i == 0))


# ---- isometric from kernel -------------------------------------------------
def iso(x, y, z):
    return (x - y) * 0.86602540378, -z + (x + y) * 0.5


def paint_machine(s, ox, oy, scale, highlight=(), explode=0.0, discs=False, stand=False, ghost=()):
    """Painter's-algorithm isometric of kernel solids."""
    hl = set(highlight)
    gh = set(ghost)
    parts = assembly(opening=1.5, explode=explode, cutaway=False, discs=discs, stand=stand)
    faces = []
    from walter_kernel import Box, Cyl

    def quads(p):
        if isinstance(p, Box):
            x, y, z, dx, dy, dz = p.x, p.y, p.z, p.dx, p.dy, p.dz
            v = [
                (x, y, z), (x + dx, y, z), (x + dx, y + dy, z), (x, y + dy, z),
                (x, y, z + dz), (x + dx, y, z + dz), (x + dx, y + dy, z + dz), (x, y + dy, z + dz),
            ]
            return [(v[0], v[1], v[2], v[3]), (v[4], v[5], v[6], v[7]),
                    (v[0], v[1], v[5], v[4]), (v[1], v[2], v[6], v[5]),
                    (v[2], v[3], v[7], v[6]), (v[3], v[0], v[4], v[7])]
        r, h, ax = p.d / 2.0, p.h, p.axis
        out = []
        segs = 12

        def pt(i, along):
            a = 2 * math.pi * i / segs
            c, sn = math.cos(a), math.sin(a)
            if ax == "x":
                return (p.x + along, p.y + r * c, p.z + r * sn)
            if ax == "y":
                return (p.x + r * c, p.y + along, p.z + r * sn)
            return (p.x + r * c, p.y + r * sn, p.z + along)

        for i in range(segs):
            j = (i + 1) % segs
            out.append((pt(i, 0), pt(j, 0), pt(j, h), pt(i, h)))
        return out

    vis = [p for p in parts if (not gh or p.group in gh or p.group in hl)]
    if gh:
        vis = [p for p in vis if p.group in gh or p.group in hl]
    for p in vis:
        for q in quads(p):
            depth = sum(q[i][0] + q[i][1] + q[i][2] for i in range(4)) / 4
            faces.append((depth, p.group, p.color, q, p.group in hl))
    faces.sort(key=lambda t: t[0])
    xs, ys = [], []
    proj = []
    for depth, g, color, q, hot in faces:
        xy = [iso(*pt) for pt in q]
        xs += [p[0] for p in xy]
        ys += [p[1] for p in xy]
        proj.append((g, color, xy, hot))
    if not xs:
        return
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    sx = scale / max(maxx - minx, 0.01)
    sy = scale / max(maxy - miny, 0.01)
    sc = min(sx, sy) * 0.92
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2

    def T(x, y):
        return ox + (x - cx) * sc, oy + (y - cy) * sc

    for g, color, xy, hot in proj:
        pts = [(T(x, y)) for x, y in xy]
        fill = color if (not hl or hot) else "#efe8dc"
        sw = 1.6 if hot else 0.6
        stroke = HL if hot else "#3a3228"
        if hl and not hot:
            fill = "#efe8dc"
            stroke = LIGHT
        s.poly(pts, fill=fill, stroke=stroke, sw=sw)


def disc_detail(s, ox, oy, r=210):
    s.circle(ox, oy, r, fill="#c4b49a", stroke=INK, sw=3)
    s.circle(ox, oy, r * 0.748 / 5.125, fill=PAPER, stroke=INK, sw=2)
    kw = r * 0.1875 / 2.5625
    s.rect(ox - kw / 2, oy - r * 0.748 / 5.125 - 10, kw, 18, fill=ACC, stroke=INK, sw=1.4)
    s.text(ox, oy + r + 28, "D-001  Ø 5.125  BORE 0.748  KEY 3/16", 14, ACC, "middle", bold=True)


# ================================================================ pages
def page_cover():
    s = Sheet("BUILD MANUAL · COVER", f"Rev {REV}")
    s.text(40, 96, "WALTER", 64, INK, bold=True, mono=False)
    s.text(44, 132, "BUILD MANUAL — 16″ CLOSED-FRAME DRUM THICKNESS SANDER", 20, ACC, bold=True)
    s.text(44, 160, f"22 × 36 × 20″ · {TOTAL} steps · 6 bags · PLANFORGE v1.0 · original engineering", 14, DIM)
    paint_machine(s, 980, 560, 520, highlight=(), explode=0, discs=False)
    for i, b in enumerate(BAGS):
        x = 48 + (i % 3) * 420
        y = 780 + (i // 3) * 110
        s.rect(x, y, 400, 96, fill="#eceae2", stroke=INK, sw=2, rx=14)
        s.circle(x + 36, y + 38, 22, fill=ACC, stroke=INK, sw=2)
        s.text(x + 36, y + 45, str(b["id"]), 20, PAPER, "middle", bold=True)
        s.text(x + 72, y + 34, b["name"], 16, INK, bold=True)
        s.text(x + 72, y + 58, b["blurb"], 12, DIM)
    s.no_icon(1480, 100, "MDF", "drum or walls")
    s.no_icon(1588, 100, "BELT", "sanding as conveyor")
    s.text(48, 1020, "READ FIRST: mill parts to fab/08_CUT_LISTS before Bag 1. Print T-DISC and T-PLATE at 100% and check both scale bars.", 13, INK)
    s.text(48, 1044, "Datums: D1 base top = Z0. D2 drum axis Z 13.50 / Y 18.00. Orange arrows = this step. Do not scale a perspective.", 13, DIM)
    s.save("00-cover.svg", "Cover — finished machine and six bags")


def page_inventory():
    s = Sheet("BUILD MANUAL · PART INVENTORY", f"Rev {REV}")
    s.text(40, 70, "EVERY BRICK IN THE BOX", 22, ACC, bold=True)
    s.text(40, 96, "Make parts first. Buy parts second. Do not open Bag 1 until D-001 blanks exist.", 14, DIM)
    cols = 4
    items = PROJ["parts"]
    col_w = 390
    for i, p in enumerate(items):
        col, row = i % cols, i // cols
        x, y = 40 + col * col_w, 120 + row * 46
        fill = GROUP_FILL.get(p["GROUP"], LIGHT)
        s.rect(x, y, 34, 16, fill=fill, stroke=INK, sw=1)
        s.text(x + 42, y + 14, f"{p['QTY']}× {p['PART_ID']}", 13, HL, bold=True)
        s.text(x + 160, y + 14, p["DESC"][:34], 12, INK)
    s.text(40, 1040, f"{len(items)} unique IDs  ·  bags 1–6  ·  N-001 stand is optional  ·  hardware H-001… in planforge/MCMASTER_SCHEDULE.csv", 13, DIM)
    s.save("01-inventory.svg", "Part inventory — every brick in the box")


def page_step(st):
    s = step_sheet(st["n"], st["bag"], st["title"], st["note"])
    bottom = parts_box(s, st["parts"])
    key = st["key"]
    groups = st["groups"]

    # stage
    ox, oy, sc = 980, 620, 480
    explode = 0.35 if key in ("STACK", "PLATES", "MOTOR", "HOOD") else 0.0
    discs = key in ("CUT", "BORE", "STACK", "GLUE", "TRUE", "WRAP")
    paint_machine(s, ox, oy, sc, highlight=groups, explode=explode, discs=discs, ghost=())

    if key == "CUT":
        disc_detail(s, 560, 520, 170)
        s.arrow(560, 330, 560, 360)
        s.text(560, 318, "BANDSAW OUTSIDE THE LINE", 13, HL, "middle", bold=True)
    elif key == "BORE":
        disc_detail(s, 560, 500, 160)
        s.arrow(560, 500, 720, 500)
        s.text(740, 505, "FENCE ON THE DRILL PRESS", 13, HL, bold=True)
    elif key == "STACK":
        s.text(420, 420, "0.5 mm GAP EVERY 4", 14, HL, bold=True)
        s.arrow(520, 480, 700, 560)
    elif key == "GLUE":
        warn(s, 40, bottom + 16, 330, ["NO GLUE IN THE KEYWAY", "Clamp as a column, not a vise."])
    elif key == "TRUE":
        s.text(420, 400, "Ø 5.000 ±0.010  Q02", 16, HL, bold=True)
    elif key == "WALLS":
        warn(s, 40, bottom + 16, 330, ["GRAIN CROSSED", "Glue on a flat door."])
    elif key == "PLATES":
        s.rect(430, 360, 220, 220, fill=STEEL, stroke=INK, sw=2)
        s.circle(540, 470, 28, fill=PAPER, stroke=INK, sw=2)
        s.text(540, 610, "ST-001 IDLE — SLOT THESE TWO", 13, HL, "middle", bold=True)
    elif key == "BOX":
        s.text(420, 380, "DATUM D1  ·  WINDING STICKS", 15, HL, bold=True)
        warn(s, 40, bottom + 16, 330, ["THIS IS THE MACHINE'S ACCURACY", "Glue does not forgive wind."])
    elif key == "JACK":
        s.text(420, 400, "D3 ZERO = PLATES COPLANAR", 15, HL, bold=True)
    elif key == "WAYS":
        warn(s, 40, bottom + 16, 330, ["OIL THE WAYS", "Never paint the sliding faces."])
    elif key == "ACME":
        s.text(420, 390, "DATUM D4  ·  CLOCK THE NUTS", 15, HL, bold=True)
        warn(s, 40, bottom + 16, 330, ["FOUR INDEPENDENT SCREWS RACK", "HTD (or #25) only after clocking."])
    elif key == "ROLL":
        s.text(420, 390, "0.030″ BARREL ON BOTH", 15, HL, bold=True)
    elif key == "BELT":
        warn(s, 40, bottom + 16, 330, ["NOT A SANDING BELT", "Track empty 60 s, then loaded."])
    elif key == "MOTOR":
        s.arrow(1180, 520, 1280, 520)
        s.text(1290, 525, "HINGE + TURNBUCKLE", 13, HL, bold=True)
    elif key == "GUARD":
        warn(s, 40, bottom + 16, 330, ["NO FINGER SLOT AT THE PINCH", "Starter is not a light switch."])
    elif key == "HOOD":
        s.text(420, 390, "400 CFM AT 4″  ·  BRUSH ON", 15, HL, bold=True)
    elif key == "WRAP":
        s.text(420, 390, "START IN THE IDLE-END SLOT", 15, HL, bold=True)
        s.arrow(700, 480, 880, 560)
    elif key == "PARA":
        s.text(420, 390, "16″ TEST BOARD KISSES BOTH ENDS", 15, HL, bold=True)
    elif key == "QA":
        qs = ["Q01 square", "Q02 OD", "Q03 parallel", "Q04 track", "Q05 witness", "Q06 E-stop", "Q07 hood", "Q08 guard", "Q09 poplar", "Q10 jack zero"]
        yy = 360
        for q in qs:
            s.rect(420, yy, 220, 28, fill="#efe8dc", stroke=INK, sw=1)
            s.text(432, yy + 20, q, 13, INK)
            yy += 32
    elif key == "CARD":
        warn(s, 40, bottom + 16, 330, ["STARTUP ORDER", "Collector → hood → lock → drum → feed"])
        s.text(420, 400, "NEVER START WITH A BOARD UNDER THE DRUM", 14, HL, bold=True)
    elif key == "FIRST":
        s.text(420, 390, "0.010″ POPLAR  ·  THEN OAK", 16, HL, bold=True)
        warn(s, 40, bottom + 16, 330, ["THIS IS NOT A PLANER", "Nothing shorter than 12″ unless on a carrier."])

    s.rect(40, 980, 1600, 36, fill="#efe8dc", stroke="none", sw=0)
    s.text(52, 1004, f"Bag {st['bag']}  ·  highlight = this step  ·  full solids in cad/exports  ·  next: step {st['n'] + 1 if st['n'] < TOTAL else 'done'}", 13, DIM)
    s.save(f"step-{st['n']:02d}.svg", f"Step {st['n']} — {st['title']}")


def write_index():
    figs = []
    for i, (fn, cap) in enumerate(PAGES):
        figs.append(
            f"<figure id='p{i}'><img src='{fn}' alt='{esc(cap)}' loading='lazy'/>"
            f"<figcaption><b>{i:02d}</b> {esc(cap)}</figcaption></figure>"
        )
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>WALTER Build Manual — Rev {REV} · LEGO steps</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Newsreader:opsz,wght@6..72,500;6..72,600&display=swap" rel="stylesheet"/>
<style>
:root{{--ink:#1c1914;--paper:#f4efe6;--copper:#b4532a;--copper-hi:#d47248;--dim:#8a7a68}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--ink);color:var(--paper);font-family:"IBM Plex Mono",monospace;line-height:1.5}}
header{{padding:48px 24px 20px;max-width:1200px;margin:0 auto}}
.k{{font:500 11px/1 "IBM Plex Mono",monospace;letter-spacing:.28em;color:var(--copper-hi);text-transform:uppercase}}
h1{{font-family:"Newsreader",Georgia,serif;font-weight:600;font-size:clamp(34px,6vw,64px);margin:10px 0 8px}}
.sub{{color:var(--dim);font-size:14px;max-width:70ch}}
nav{{padding:10px 24px 20px;max-width:1200px;margin:0 auto;display:flex;gap:10px;flex-wrap:wrap}}
nav a{{color:var(--dim);text-decoration:none;font-size:11px;border:1px solid rgba(244,239,230,.2);padding:7px 10px;letter-spacing:.08em}}
nav a:hover{{color:var(--paper);border-color:var(--paper)}}
main{{max-width:1200px;margin:0 auto;padding:0 24px 80px}}
figure{{margin:26px 0}}
img{{width:100%;display:block;border:1px solid rgba(244,239,230,.18);background:#f4efe6}}
figcaption{{padding:10px 2px;color:var(--dim);font-size:12px}}
figcaption b{{color:var(--copper-hi);margin-right:8px}}
@media print{{body{{background:#fff}}header,nav{{display:none}}img{{border:none;page-break-after:always}}}}
</style></head><body>
<header>
<p class="k">WALTER · Rev {REV} · WOODWRIGHT PLANFORGE v1.0</p>
<h1>Build Manual</h1>
<p class="sub">{TOTAL} steps · 6 bags · generated from the kernel. Print at 100% on A3 (~71% on Letter). Orange arrows are this step. Release: FABRICATION-READY WITH CONDITIONS — not a PE stamp, not a ShopNotes reprint.</p>
</header>
<nav>
<a href="../">← Design</a><a href="../app/">Build app</a><a href="../planforge/">Planforge</a><a href="../fab/">Fab</a><a href="../report/">Report</a>
<a href="#p0">Cover</a><a href="#p1">Parts</a><a href="#p2">Bag 1</a><a href="#p7">Bag 2</a><a href="#p11">Bag 3</a><a href="#p14">Bag 4</a><a href="#p16">Bag 5</a><a href="#p18">Bag 6</a>
</nav>
<main>
{''.join(figs)}
</main>
</body></html>
"""
    path = os.path.join(OUT, "index.html")
    with open(path, "w") as f:
        f.write(html)
    print("wrote", os.path.relpath(path, ROOT))


def main():
    page_cover()
    page_inventory()
    for st in STEPS:
        page_step(st)
    write_index()
    print(f"WALTER LEGO manual Rev {REV}: {len(PAGES)} pages")


if __name__ == "__main__":
    main()
