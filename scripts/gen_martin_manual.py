#!/usr/bin/env python3
"""MARTIN Rev F.2 — LEGO-style step-by-step build manual.

Numbered steps, parts callout boxes, insertion arrows, progressive
assembly drawings. Every page is generated from
martin_kernel.build_project() — the same single source of truth as the
CAD model, the plan sheets, and the fabrication package.

Run:  python3 scripts/gen_martin_manual.py
"""

from __future__ import annotations

import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "fence", "martin"))

from martin_kernel import PROJECT, build_project, v as kv  # noqa: E402
from martin_elevation import (  # noqa: E402
    paint_front_elevation,
    paint_motif,
    paint_pier_bricks,
    EARTH, BELT, EAVE, CASS, PIER, BRICK, PLANTER,
    PAPER, INK, ACC, DIM,
)

OUT = os.path.join(ROOT, "fence", "martin", "manual")
os.makedirs(OUT, exist_ok=True)

PROJ = build_project()
LY = PROJ["layout"]
PARTS = {p["PART_ID"]: p for p in PROJ["parts"]}
SLATS = {s["id"]: s for s in LY["slats"]}

HL = "#b3541e"       # this-step highlight
OAK = "#8a6a3d"
LIGHT = "#c5c8c2"
GATEBG = "#e4e0d6"

W, Hpx = 1680, 1188
MONO = "font-family='IBM Plex Mono, Menlo, monospace'"
SER = "font-family='Georgia, serif'"

TOTAL_STEPS = 24
PAGES = []  # (filename, caption)


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
        self.add(f"<polygon points='{p}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}'/>")

    def circle(self, cx, cy, r, fill="none", stroke=INK, sw=2):
        self.add(f"<circle cx='{cx:.1f}' cy='{cy:.1f}' r='{r:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}'/>")

    def text(self, x, y, s, size=16, color=INK, anchor="start", bold=False, mono=True):
        f = MONO if mono else SER
        wgt = " font-weight='600'" if bold else ""
        self.add(f"<text x='{x:.1f}' y='{y:.1f}' {f} font-size='{size}' fill='{color}' text-anchor='{anchor}'{wgt}>{esc(s)}</text>")

    def arrow(self, x1, y1, x2, y2, color=HL, w=7):
        ang = math.atan2(y2 - y1, x2 - x1)
        hx, hy = x2, y2
        L, Wd = 22, 11
        p1 = (hx - L * math.cos(ang) + Wd * math.sin(ang), hy - L * math.sin(ang) - Wd * math.cos(ang))
        p2 = (hx - L * math.cos(ang) - Wd * math.sin(ang), hy - L * math.sin(ang) + Wd * math.cos(ang))
        self.line(x1, y1, x2 - 14 * math.cos(ang), y2 - 14 * math.sin(ang), w, color)
        self.poly([(hx, hy), p1, p2], fill=color, stroke=color, sw=1)

    def no_icon(self, cx, cy, word, label):
        self.circle(cx, cy, 30, fill=PAPER, stroke=INK, sw=3)
        self.text(cx, cy + 5, word, 12, INK, "middle", bold=True)
        self.line(cx - 21, cy - 21, cx + 21, cy + 21, 5, HL)
        self.text(cx, cy + 52, label, 11, DIM, "middle")

    def frame(self):
        self.b.insert(0, f"<rect x='0' y='0' width='{W}' height='{Hpx}' fill='{PAPER}' stroke='{INK}' stroke-width='3'/>")
        self.b.insert(1, f"<rect x='24' y='24' width='{W - 48}' height='{Hpx - 48}' fill='none' stroke='{INK}' stroke-width='1.2'/>")
        self.line(24, Hpx - 88, W - 24, Hpx - 88, 1.4)
        self.text(40, Hpx - 56, "MARTIN", 26, ACC, bold=True, mono=False)
        self.text(172, Hpx - 58, self.fl, 15, INK, bold=True)
        self.text(40, Hpx - 34, "Buffalo NY · Darwin Martin Tree of Life · no nails, no glue on locking faces, no concrete", 12, DIM)
        self.text(W - 40, Hpx - 56, self.fr, 14, DIM, "end")
        self.text(W - 40, Hpx - 34, "Generated from martin_kernel.py — do not scale", 12, DIM, "end")

    def save(self, filename, caption):
        self.frame()
        svg = (
            f"<?xml version='1.0' encoding='UTF-8'?>\n"
            f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{Hpx}' viewBox='0 0 {W} {Hpx}'>\n"
            + "\n".join(self.b) + "\n</svg>\n"
        )
        path = os.path.join(OUT, filename)
        with open(path, "w") as f:
            f.write(svg)
        PAGES.append((filename, caption))
        print("wrote", os.path.relpath(path, ROOT))


# ---------------------------------------------------------------- transforms
S_E = 7.0
OXE, OYE = 430, 845


def XE(x):
    return OXE + x * S_E


def YE(z):
    return OYE - z * S_E


SP = 6.5
OXP, OYP = 430, 480


def XP(x):
    return OXP + x * SP


def YP(y):
    return OYP - y * SP


H = LY["overall_height"]
L = LY["overall_length"]
FX = kv("post_x")
CAP_T = kv("cap_t")
GX0 = FX + kv("gate_gap")
GW = LY["gate_leaf_w"]
GH = LY["gate_h"]
GZ0 = kv("gate_bottom_clear")


# ---------------------------------------------------------------- page chrome
def step_sheet(n, bag, title, note=""):
    s = Sheet(f"BUILD MANUAL · STEP {n} OF {TOTAL_STEPS}", f"BAG {bag} · Rev {PROJECT['REVISION']}")
    s.rect(40, 46, 150, 118, fill=PAPER, stroke=INK, sw=4, rx=16)
    s.text(115, 136, str(n), 84, INK, "middle", bold=True)
    s.rect(206, 46, 128, 40, fill=ACC, stroke=INK, sw=2, rx=10)
    s.text(270, 72, f"BAG {bag}", 16, PAPER, "middle", bold=True)
    s.text(206, 122, title, 21, ACC, bold=True)
    if note:
        s.text(206, 150, note, 13, DIM)
    return s


def part_fill(pid):
    for pre, col in (("K", EARTH), ("R", BELT), ("Q", CASS), ("C", EAVE), ("L", PIER),
                     ("F", LIGHT), ("G", GATEBG), ("W", OAK), ("T", BRICK), ("H", "#aeb6ba")):
        if pid.startswith(pre):
            return col
    return LIGHT


def parts_box(s, items, x=40, y=200, title="PARTS THIS STEP"):
    """items: list of (qty, pid, label). Chip size from finished dims."""
    hgt = 46 + 58 * len(items)
    s.rect(x, y, 330, hgt, fill="#eceae2", stroke=INK, sw=2.5, rx=14)
    s.text(x + 16, y + 30, title, 13, ACC, bold=True)
    yy = y + 52
    for qty, pid, label in items:
        p = PARTS.get(pid, {})
        li = float(p.get("FINISHED_LENGTH") or 24)
        wi = float(p.get("FINISHED_WIDTH") or 4)
        cw = max(26, min(170, li * 1.1))
        ch = max(9, min(30, wi * 2.4))
        s.rect(x + 16, yy + (30 - ch) / 2, cw, ch, fill=part_fill(pid), stroke=INK, sw=1.4)
        s.text(x + 16 + cw + 12, yy + 14, f"{qty}×", 17, HL, bold=True)
        s.text(x + 16, yy + 46, f"{pid}  {label}", 11.5, INK)
        yy += 58
    return y + hgt


def never_glue(s, x, y):
    s.rect(x, y, 200, 44, fill="#f7e8de", stroke=HL, sw=2.5, rx=10)
    s.text(x + 100, y + 20, "NEVER GLUE", 14, HL, "middle", bold=True)
    s.text(x + 100, y + 36, "winter knock-down", 10, DIM, "middle")


# ---------------------------------------------------------------- elevation state
def elev_state(s, posts=(), layers=(), wedges=False, bricks=False, eave=False,
               fascia=False, stub=False, gate=False, latch=False, planters=False,
               labels=True):
    """Progressive garden-face elevation."""
    # sill
    s.rect(XE(-kv("sill_overhang")), YE(0), (L + 2 * kv("sill_overhang")) * S_E,
           kv("sill_h") * S_E, fill="#9a9890", stroke=INK, sw=1.4)
    # ties visible as blocks in the sill at each post
    for p in LY["posts"]:
        s.rect(XE(p["cx"] - FX / 2), YE(0) + 2, FX * S_E, kv("sill_h") * S_E - 4,
               fill="#b8b6b0", stroke=INK, sw=0.8)
    # cassette fields + motifs
    for lid in layers:
        if not lid.startswith("Q-"):
            continue
        sl = SLATS[lid]
        s.rect(XE(LY["nuki_x0"] + 0.4), YE(sl["z1"]), (LY["nuki_len"] - 0.8) * S_E,
               sl["h"] * S_E, fill=CASS, stroke="none", sw=0)
        for m in LY["motifs"]:
            if m.get("part") == lid and m.get("bay") in (0, 1):
                paint_motif(s, m, XE, YE, S_E)
    # water table + belts
    for lid in layers:
        if lid.startswith("Q-"):
            continue
        sl = SLATS[lid]
        fill = EARTH if lid == "K-001" else BELT
        s.rect(XE(LY["nuki_x0"]), YE(sl["z1"]), LY["nuki_len"] * S_E, sl["h"] * S_E,
               fill=fill, stroke=INK, sw=1.3)
    # piers
    for p in LY["posts"]:
        if p["mark"] not in posts:
            continue
        s.rect(XE(p["cx"] - FX / 2), YE(H - CAP_T), FX * S_E, (H - CAP_T) * S_E,
               fill=PIER, stroke=INK, sw=1.6)
        if bricks and p["mark"] != "P0":
            paint_pier_bricks(s, XE, YE, S_E, p["cx"], FX, 2.0, H - CAP_T - 1.0)
        if labels:
            s.text(XE(p["cx"]), YE(H) - 16, p["mark"], 12, ACC, "middle", bold=True)
    # kusabi wedges at nuki posts
    if wedges:
        for p in LY["posts"]:
            if p["mark"] not in ("P1", "P2", "P3") or p["mark"] not in posts:
                continue
            for lid in layers:
                if lid.startswith("Q-"):
                    continue
                cl = SLATS[lid]["cl"]
                x = XE(p["cx"] + FX / 2)
                s.poly([(x, YE(cl) - 6), (x + 13, YE(cl)), (x, YE(cl) + 6)], fill=OAK, stroke=INK, sw=1)
    # eave + fascia + stub
    if eave:
        s.rect(XE(LY["cap_x0"]), YE(H), LY["cap_len"] * S_E, CAP_T * S_E, fill=EAVE, stroke=INK, sw=1.4)
    if fascia:
        s.rect(XE(LY["cap_x0"]), YE(H - CAP_T), LY["cap_len"] * S_E, kv("fascia_h") * S_E,
               fill="#1a1f24", stroke=INK, sw=1.0)
    if stub:
        p0 = LY["posts"][0]["cx"]
        s.rect(XE(p0 - FX / 2 - 0.5), YE(H), (FX + 1.0) * S_E, CAP_T * S_E, fill=EAVE, stroke=INK, sw=1.2)
    # planters
    if planters:
        for la, rb in ((1, 2), (2, 3)):
            x0 = LY["posts"][la]["cx"] + FX / 2 + 0.4
            x1 = LY["posts"][rb]["cx"] - FX / 2 - 0.4
            s.rect(XE(x0), YE(7.5), (x1 - x0) * S_E, 7.5 * S_E, fill=PLANTER, stroke=INK, sw=1.1)
    # gate
    if gate:
        s.rect(XE(GX0), YE(GZ0 + GH), GW * S_E, GH * S_E, fill=GATEBG, stroke=ACC, sw=2)
        stile = kv("stile_w")
        s.rect(XE(GX0), YE(GZ0 + GH), stile * S_E, GH * S_E, fill=PIER, stroke=INK, sw=1.1)
        s.rect(XE(GX0 + GW - stile), YE(GZ0 + GH), stile * S_E, GH * S_E, fill=PIER, stroke=INK, sw=1.1)
        for m in LY["motifs"]:
            if m.get("bay") == "gate":
                paint_motif(s, m, XE, YE, S_E)
        for bid in ("R-001", "R-002"):
            b = SLATS[bid]
            s.rect(XE(GX0 + stile), YE(b["z1"]), (GW - 2 * stile) * S_E, b["h"] * S_E, fill=BELT, stroke=INK, sw=0.8)
    if latch:
        cl = LY["latch_cl"]
        s.rect(XE(GX0) - 46, YE(cl + 1.75), 60, 3.5 * S_E, fill=OAK, stroke=INK, sw=1.4)


def hl_box(s, x, z, w, h):
    s.rect(XE(x) - 5, YE(z + h) - 5, w * S_E + 10, h * S_E + 10, fill="none", stroke=HL, sw=4, dash="12 7")


# ---------------------------------------------------------------- plan state
def plan_state(s, pads=False, sills=False, ties=False, planters=False):
    st = kv("sill_t")
    spread = kv("base_spread_cl")
    tie_half = LY["tie_len"] / 2.0
    # house
    s.rect(XP(-24), YP(26), 16 * SP, 52 * SP, fill="#d9d5ca", stroke=INK, sw=1.4)
    s.text(XP(-16), YP(0) + 5, "HOUSE", 13, DIM, "middle", bold=True)
    # base footprint ghost
    s.rect(XP(-kv("sill_overhang")), YP(LY["base_width"] / 2), LY["sill_len"] * SP,
           LY["base_width"] * SP, fill="none", stroke=DIM, sw=1, dash="5 4")
    if pads:
        for i in range(8):
            px = -2 + i * (L + 4) / 7.0
            s.rect(XP(px) - 8, YP(-spread / 2) - 8, 16, 16, fill="#3d3530", stroke=INK, sw=1)
    if sills:
        s.rect(XP(-kv("sill_overhang")), YP(-spread / 2 + st / 2), LY["sill_len"] * SP, st * SP, fill=LIGHT, stroke=INK, sw=1.6)
        s.rect(XP(-kv("sill_overhang")), YP(spread / 2 + st / 2), LY["sill_len"] * SP, st * SP, fill=LIGHT, stroke=INK, sw=1.6)
        s.text(XP(L / 2), YP(-spread / 2) + 28, "F-001 DRIVEWAY SILL", 12, DIM, "middle")
        s.text(XP(L / 2), YP(spread / 2) - 18, "F-002 GARDEN SILL", 12, DIM, "middle")
    if ties:
        for p in LY["posts"]:
            s.rect(XP(p["cx"] - FX / 2), YP(tie_half), FX * SP, LY["tie_len"] * SP, fill="#c5c8c2", stroke=INK, sw=1.5)
            s.text(XP(p["cx"]), YP(tie_half) - 10, p["mark"], 12, ACC, "middle", bold=True)
    if planters:
        for la, rb in ((1, 2), (2, 3)):
            x0 = LY["posts"][la]["cx"] + FX / 2 + 1
            x1 = LY["posts"][rb]["cx"] - FX / 2 - 1
            s.rect(XP(x0), YP(spread / 2 + st / 2 + kv("planter_y") + 1), (x1 - x0) * SP,
                   kv("planter_y") * SP, fill=PLANTER, stroke=INK, sw=1.4)
    s.text(XP(L / 2), YP(-spread / 2 - 9), "DRIVEWAY (EXISTING SLAB — DO NOT DRILL, DO NOT POUR)", 12, DIM, "middle")
    s.text(XP(L / 2), YP(spread / 2 + st + 22), "GARDEN", 12, DIM, "middle")


# ---------------------------------------------------------------- gate bench
GS = 8.5
GBX, GBY = 700, 970


def GXb(x):
    return GBX + (x - GX0) * GS


def GYb(z):
    return GBY - (z - GZ0) * GS


def gate_bench(s, frame=True, cassettes=False):
    stile = kv("stile_w")
    s.rect(GXb(GX0), GYb(GZ0 + GH), GW * GS, GH * GS, fill="#f0ede4", stroke=DIM, sw=1, dash="4 3")
    if frame:
        s.rect(GXb(GX0), GYb(GZ0 + GH), stile * GS, GH * GS, fill=PIER, stroke=INK, sw=1.6)
        s.rect(GXb(GX0 + GW - stile), GYb(GZ0 + GH), stile * GS, GH * GS, fill=PIER, stroke=INK, sw=1.6)
        rails = [(GZ0, 3.5), (GZ0 + GH - 3.5, 3.5)]
        for bid in ("R-001", "R-002"):
            b = SLATS[bid]
            rails.append((b["cl"] - 2.75, 5.5))
        q3 = SLATS["Q-003"]
        rails.append((q3["cl"] - 2.75, 5.5))
        for z0r, hr in rails:
            s.rect(GXb(GX0 + stile), GYb(z0r + hr), (GW - 2 * stile) * GS, hr * GS, fill=BELT, stroke=INK, sw=1.2)
    if cassettes:
        k = SLATS["K-001"]
        s.rect(GXb(GX0 + stile), GYb(k["z1"]), (GW - 2 * stile) * GS, (k["z1"] - GZ0) * GS, fill=EARTH, stroke=INK, sw=1.2)
        for m in LY["motifs"]:
            if m.get("bay") == "gate":
                s.rect(GXb(m["x0"]), GYb(m["z0"] + m["h"]), m["w"] * GS, m["h"] * GS, fill=CASS, stroke="none", sw=0)
                paint_motif(s, m, GXb, GYb, GS)


# ================================================================ pages
def page_cover():
    s = Sheet("BUILD MANUAL · COVER", f"Rev {PROJECT['REVISION']}")
    s.text(40, 96, "MARTIN", 64, INK, bold=True, mono=False)
    s.text(44, 132, "BUILD MANUAL — DARWIN MARTIN TREE OF LIFE FENCE", 20, ACC, bold=True)
    s.text(44, 160, f"143″ × 65″ · {TOTAL_STEPS} steps · 6 bags · no post holes · no cement · winter-removable", 14, DIM)
    SC, ox, oy = 7.6, 320, 720

    def Xc(x):
        return ox + x * SC

    def Yc(z):
        return oy - z * SC

    paint_front_elevation(s, LY, Xc, Yc, SC, kv, gate=True, labels=True, planters=True)
    bags = [
        ("1", "FOUNDATION", "pads · sills · ties · troughs"),
        ("2", "PIERS", "4×6 posts drop in"),
        ("3", "LIGHT-SCREEN", "water table · 2×4 ribbons · Tree of Life"),
        ("4", "EAVE", "2×12 cantilever + fascia + light"),
        ("5", "GATE", "Tree of Life portal"),
        ("6", "FINISH", "paint · plant · done"),
    ]
    for i, (n, t, d) in enumerate(bags):
        x = 60 + i * 262
        s.rect(x, 800, 240, 96, fill="#eceae2", stroke=INK, sw=2, rx=14)
        s.circle(x + 34, 838, 22, fill=ACC, stroke=INK, sw=2)
        s.text(x + 34, 845, n, 20, PAPER, "middle", bold=True)
        s.text(x + 68, 834, t, 14, INK, bold=True)
        s.text(x + 68, 856, d, 10.5, DIM)
    s.no_icon(1330, 120, "GLUE", "wedges & pegs only")
    s.no_icon(1440, 120, "NAILS", "no metal in timber")
    s.no_icon(1550, 120, "POUR", "sits on the slab")
    s.text(60, 960, "READ FIRST: mill all parts to the cut lists (fab/08_CUT_LISTS) before step 1. Saw stops S-014 (posts) and S-021 (nuki) — do not move a stop mid-family.", 13, INK)
    s.text(60, 986, "Datum: sill top = z 0. Latch face at the house = x 0. Every step keys off these two lines.", 13, DIM)
    s.save("00-cover.svg", "Cover — the finished fence and the six bags")


def page_inventory():
    s = Sheet("BUILD MANUAL · PART INVENTORY", "mill first, then build")
    s.text(40, 80, "PART INVENTORY — TIMBER (MAKE)", 22, ACC, bold=True)
    s.text(40, 106, "Finished sizes in inches. Mill everything before step 1 — like opening the box and sorting bricks.", 13, DIM)
    columns = [
        (40, [("BAG 1 — FOUNDATION", ["F-001", "F-002", "F-003", "F-005", "F-006"]),
              ("BAG 2 — PIERS", ["L-001", "L-002", "L-003", "L-004"])]),
        (590, [("BAG 3 — LIGHT-SCREEN", ["K-001", "R-001", "R-002", "Q-001", "Q-002", "Q-003", "T-001", "W-001"]),
               ("BAG 4 — EAVE", ["C-001", "C-002", "C-003"])]),
        (1140, [("BAG 5 — GATE", ["G-001", "G-002", "G-003", "G-004", "G-005", "G-006", "G-007", "G-009", "G-010", "W-002", "W-003"])]),
    ]
    for x, groups in columns:
        y = 130
        for gname, ids in groups:
            s.text(x, y + 20, gname, 15, INK, bold=True)
            y += 34
            for pid in ids:
                p = PARTS.get(pid)
                if not p:
                    continue
                li = float(p.get("FINISHED_LENGTH") or 12)
                wi = float(p.get("FINISHED_WIDTH") or 3.5)
                cw = max(24, min(150, li * 0.95))
                ch = max(8, min(24, wi * 2.1))
                s.rect(x, y + (24 - ch) / 2, cw, ch, fill=part_fill(pid), stroke=INK, sw=1.2)
                s.text(x + 162, y + 12, f'{int(p["QUANTITY"])}×', 14, HL, bold=True)
                s.text(x + 200, y + 12, f'{pid}', 12.5, INK, bold=True)
                s.text(x + 200, y + 28, f'{float(p["FINISHED_THICKNESS"]):g}×{float(p["FINISHED_WIDTH"]):g}×{float(p["FINISHED_LENGTH"]):g}″  {p["PART_NAME"][:34]}', 10.5, DIM)
                y += 44
            y += 18
    # hardware strip
    s.text(40, 1010, "NOT TIMBER:  H-001 rubber pads ×8 · H-006 12V IP65 tape + driver · H-007 in-box stone · H-005 primer + owner-gray paint · optional H-003 pintles / H-004 hasp", 12.5, INK)
    s.text(40, 1034, "Oak parts (W-001 wedges, W-002 pegs, W-003 pivots, G-010 latch) are the LEGO 'technic pins' of this build — they are the only fasteners.", 12.5, DIM)
    s.save("01-inventory.svg", "Part inventory — every brick in the box")


# ---------- BAG 1 ----------
def page_step1():
    s = step_sheet(1, 1, "Place 8 rubber pads on the driveway", "Protect the slab. No fasteners into pavement — ever.")
    parts_box(s, [(8, "H-001", 'rubber pad 4×4×0.5″')])
    plan_state(s, pads=True)
    for i in range(8):
        px = -2 + i * (L + 4) / 7.0
        if i in (0, 3, 7):
            s.arrow(XP(px), YP(-kv("base_spread_cl") / 2) - 66, XP(px), YP(-kv("base_spread_cl") / 2) - 20)
    s.text(430, 700, "Pads sit where the DRIVEWAY sill will land (dashed footprint). Sweep the slab first. Dry slab, dry pads.", 13, INK)
    s.save("step-01.svg", "Step 1 — pads on the driveway")


def page_step2():
    s = step_sheet(2, 1, "Lay the two dodai sills", "F-001 on the pads (driveway) · F-002 on grade (garden)")
    parts_box(s, [(1, "F-001", 'driveway sill 4×6 × 155″'), (1, "F-002", 'garden sill 4×6 × 155″')])
    plan_state(s, pads=True, sills=True)
    s.arrow(XP(L / 2), YP(-kv("base_spread_cl") / 2) - 80, XP(L / 2), YP(-kv("base_spread_cl") / 2) - 26)
    s.arrow(XP(L / 2), YP(kv("base_spread_cl") / 2) + 92, XP(L / 2), YP(kv("base_spread_cl") / 2) + 38)
    s.text(430, 700, f'Sill centerlines {kv("base_spread_cl"):g}″ apart — this spread is the wind lever. Overhang {kv("sill_overhang"):g}″ past each end post.', 13, INK)
    s.text(430, 724, "Check both sills for straight. Pack F-004 crib ONLY if the garden sill leaves the slab (default 0).", 13, DIM)
    s.save("step-02.svg", "Step 2 — dodai sills")


def page_step3():
    s = step_sheet(3, 1, "Half-lap the four cross-ties", "One tie per pier station · pegged, not glued")
    parts_box(s, [(4, "F-003", 'cross-tie 4×6 × 41.5″'), (8, "W-002", "oak peg Ø0.375″")])
    plan_state(s, pads=True, sills=True, ties=True)
    for p in LY["posts"]:
        s.arrow(XP(p["cx"]), YP(LY["tie_len"] / 2) - 74, XP(p["cx"]), YP(LY["tie_len"] / 2) - 22)
    # half-lap inset — below the plan, clear of the P3 tie
    ix, iy = 1330, 680
    s.rect(ix, iy, 280, 190, fill="#eceae2", stroke=INK, sw=2, rx=12)
    s.text(ix + 14, iy + 26, "DETAIL — HALF-LAP", 12, ACC, bold=True)
    s.rect(ix + 40, iy + 70, 200, 34, fill=LIGHT, stroke=INK, sw=1.6)
    s.rect(ix + 110, iy + 52, 52, 70, fill="#c5c8c2", stroke=INK, sw=1.6)
    s.line(ix + 136, iy + 44, ix + 136, iy + 130, 2, HL)
    s.text(ix + 14, iy + 156, "Cut half the depth from each,", 11, INK)
    s.text(ix + 14, iy + 172, "peg through. Flush top face.", 11, INK)
    never_glue(s, 1330, 890)
    s.save("step-03.svg", "Step 3 — cross-ties")


def page_step4():
    s = step_sheet(4, 1, "Build the two planter troughs", "Sub-assembly — set aside until step 23")
    parts_box(s, [(2, "F-005", 'trough 44×18×18″ PT')])
    bx, by = 640, 840
    sc = 9
    s.rect(bx, by - 18 * sc, 44 * sc, 18 * sc, fill=PLANTER, stroke=INK, sw=2)
    s.rect(bx + 8, by - 18 * sc + 8, 44 * sc - 16, 18 * sc - 16, fill="#5a5e56", stroke=INK, sw=1)
    for i in range(5):
        s.line(bx + 40 + i * 80, by - 6, bx + 60 + i * 80, by - 6, 5, INK)
    s.text(bx + 22 * sc, by - 18 * sc - 16, 'F-005 — 44″ × 18″ × 18″ (×2)', 14, ACC, "middle", bold=True)
    s.text(bx + 22 * sc, by + 30, "Drainage slots in the base · extra paint inside · ½″ air gap from posts when placed", 12.5, INK, "middle")
    s.text(bx + 22 * sc, by + 54, "These are the wind ballast: wet soil + optional in-box stone ≈ 1522 lb across two troughs.", 12.5, DIM, "middle")
    s.rect(1350, 220, 250, 60, fill="#eceae2", stroke=INK, sw=2, rx=12)
    s.text(1475, 246, "SET ASIDE", 15, HL, "middle", bold=True)
    s.text(1475, 266, "used again in step 23", 11, DIM, "middle")
    s.save("step-04.svg", "Step 4 — planter troughs (sub-assembly)")


# ---------- BAG 2 ----------
def page_step5():
    s = step_sheet(5, 2, "Drop P0 + P1 into their ties", "Foot tenon straight down, gravity only. P1 carries the oak pivot sockets.")
    parts_box(s, [(1, "L-001", "P0 latch post"), (1, "L-002", "P1 hinge post")])
    elev_state(s, posts=("P0", "P1"))
    for mark in ("P0", "P1"):
        cx = next(p["cx"] for p in LY["posts"] if p["mark"] == mark)
        s.arrow(XE(cx), YE(H) - 90, XE(cx), YE(H) - 24)
        hl_box(s, cx - FX / 2, 0, FX, H - CAP_T)
    ix, iy = 1350, 210
    s.rect(ix, iy, 270, 170, fill="#eceae2", stroke=INK, sw=2, rx=12)
    s.text(ix + 14, iy + 26, "P1 — OAK PIVOT SOCKETS", 12, ACC, bold=True)
    s.circle(ix + 70, iy + 80, 16, fill=PAPER, stroke=INK, sw=2)
    s.circle(ix + 70, iy + 80, 7, fill=OAK, stroke=INK, sw=1)
    s.text(ix + 100, iy + 76, "Ø1.25″ socket in the sill", 11, INK)
    s.text(ix + 100, iy + 94, "and later in the eave soffit.", 11, INK)
    s.text(ix + 14, iy + 130, "Gate weight goes into the ground", 11, DIM)
    s.text(ix + 14, iy + 146, "through P1 — not off P0.", 11, DIM)
    s.save("step-05.svg", "Step 5 — P0 and P1")


def page_step6():
    s = step_sheet(6, 2, "Drop P2 + P3", "Same move. Shoulder lands on the sill top — that is your datum.")
    parts_box(s, [(1, "L-003", "P2 mid post"), (1, "L-004", "P3 end post")])
    elev_state(s, posts=("P0", "P1", "P2", "P3"))
    for mark in ("P2", "P3"):
        cx = next(p["cx"] for p in LY["posts"] if p["mark"] == mark)
        s.arrow(XE(cx), YE(H) - 90, XE(cx), YE(H) - 24)
        hl_box(s, cx - FX / 2, 0, FX, H - CAP_T)
    s.text(430, 1000, "Check: all four posts plumb (1/8″ in 65″ max), shoulders seated, tenons fully home. Lift straight up +Z to remove — that is the winter move.", 13, INK)
    s.save("step-06.svg", "Step 6 — P2 and P3")


def page_step7():
    s = step_sheet(7, 2, "Peg the sujikai braces", "Diagonals from sill to post at P0 and P3 — rack stiffness")
    parts_box(s, [(4, "F-006", "sujikai brace"), (4, "W-002", "oak peg")])
    elev_state(s, posts=("P0", "P1", "P2", "P3"))
    for cx in (LY["posts"][0]["cx"], LY["posts"][3]["cx"]):
        s.line(XE(cx - 10), YE(0), XE(cx), YE(18), 8, "#b8b6b0")
        s.line(XE(cx + 10), YE(0), XE(cx), YE(18), 8, "#b8b6b0")
        hl_box(s, cx - 11, 0, 22, 19)
    s.text(430, 1000, "Housed half-laps, pegged. They live below the water table line — invisible once the screen is on.", 13, INK)
    s.save("step-07.svg", "Step 7 — braces")


# ---------- BAG 3 ----------
def _slide_step(n, pid, title, note, layers, extra=None):
    s = step_sheet(n, 3, title, note)
    p = PARTS[pid]
    parts_box(s, [(int(p["QUANTITY"]), pid, p["PART_NAME"][:34])])
    elev_state(s, posts=("P0", "P1", "P2", "P3"), layers=layers)
    sl = SLATS[pid]
    s.arrow(XE(157), YE(sl["cl"]), XE(147), YE(sl["cl"]))
    hl_box(s, LY["nuki_x0"], sl["z0"], LY["nuki_len"], sl["h"])
    s.text(XE(152), YE(sl["cl"]) - 18, "SLIDE IN FROM P3 END", 11, HL, "middle", bold=True)
    if extra:
        extra(s)
    return s


def page_step8():
    def extra(s):
        s.text(430, 1000, 'Through-mortise in P1/P2/P3, 1.50″ × 11.25″. The 2×12 PT water table is the earth line AND the dog seal — solid to the ground.', 13, INK)
    s = _slide_step(8, "K-001", "Slide the water table through", "2×12 PT · earth line · dog crawl stop", ["K-001"], extra)
    s.save("step-08.svg", "Step 8 — water table K-001")


def page_step9():
    s = step_sheet(9, 3, "Drop the first light cassettes", "Q-001 nested squares — one per bay, into the K-001 groove")
    parts_box(s, [(2, "Q-001", "nested-rects cassette (roots)")])
    elev_state(s, posts=("P0", "P1", "P2", "P3"), layers=["K-001", "Q-001"])
    sl = SLATS["Q-001"]
    for la, rb in ((1, 2), (2, 3)):
        cx = (LY["posts"][la]["cx"] + LY["posts"][rb]["cx"]) / 2
        s.arrow(XE(cx), YE(sl["z1"]) - 80, XE(cx), YE(sl["z1"]) - 16)
        hl_box(s, LY["posts"][la]["cx"] + FX / 2, sl["z0"], LY["bay_clear"], sl["h"])
    s.text(430, 1000, "Cassette bottom edge stands in the groove on top of K-001. It leans until the next belt captures it — support it.", 13, INK)
    s.save("step-09.svg", "Step 9 — Q-001 cassettes")


def page_step10():
    def extra(s):
        s.text(430, 1000, "R-001 slides through the piers and its underside groove captures the Q-001 top edge. Ribbon projects 3″ past each pier face — check both ends.", 13, INK)
    s = _slide_step(10, "R-001", "Slide Prairie ribbon 1 through", "2×4 · locks Q-001 · projects past the piers", ["K-001", "Q-001", "R-001"], extra)
    s.save("step-10.svg", "Step 10 — ribbon R-001")


def page_step11():
    s = step_sheet(11, 3, "Drop the TREE OF LIFE cassettes", "The hero. Three trees per bay, recessed behind the belts.")
    parts_box(s, [(2, "Q-002", "Tree of Life cassette")])
    elev_state(s, posts=("P0", "P1", "P2", "P3"), layers=["K-001", "Q-001", "R-001", "Q-002"])
    sl = SLATS["Q-002"]
    for la, rb in ((1, 2), (2, 3)):
        cx = (LY["posts"][la]["cx"] + LY["posts"][rb]["cx"]) / 2
        s.arrow(XE(cx), YE(sl["z1"]) - 80, XE(cx), YE(sl["z1"]) - 16)
        hl_box(s, LY["posts"][la]["cx"] + FX / 2, sl["z0"], LY["bay_clear"], sl["h"])
    # enlarged motif inset — first tree of the first bay only
    ix, iy = 1300, 100
    s.rect(ix, iy, 330, 258, fill="#eceae2", stroke=INK, sw=2, rx=12)
    s.text(ix + 14, iy + 26, "ONE TREE — ENLARGED", 12, ACC, bold=True)
    m = next(m for m in LY["motifs"] if m["part"] == "Q-002" and m.get("bay") == 0)
    cw = m["w"] / 3.0
    xmax = m["x0"] + cw + 0.6
    one = {
        "rects": [r for r in m["rects"] if r["x"] + r["w"] <= xmax],
        "lines": [ln for ln in m["lines"] if max(ln["x1"], ln["x2"]) <= xmax],
    }
    scz = min(288.0 / cw, 196.0 / m["h"])

    def Xi(x, _m=m):
        return ix + 20 + (x - _m["x0"]) * scz

    def Yi(z, _m=m):
        return iy + 240 - (z - _m["z0"]) * scz

    s.rect(ix + 20, iy + 240 - m["h"] * scz, cw * scz, m["h"] * scz, fill=CASS, stroke="none", sw=0)
    paint_motif(s, one, Xi, Yi, scz)
    s.text(430, 1000, "Pots at the base, three trunks, chevron branches pointing up, square leaves. Max aperture 1.50″ — run the gauge.", 13, INK)
    s.save("step-11.svg", "Step 11 — Tree of Life Q-002")


def page_step12():
    def extra(s):
        cl = LY["latch_cl"]
        s.line(XE(-4), YE(cl), XE(10), YE(cl), 2, HL, dash="6 4")
        s.text(XE(-4), YE(cl) - 8, f'LATCH CL {cl:.2f}″ AFF', 11, HL, bold=True)
        s.text(430, 1000, "This ribbon carries the latch centerline into P0. Same slide as before — capture Q-002's top edge.", 13, INK)
    s = _slide_step(12, "R-002", "Slide Prairie ribbon 2 through", "2×4 · latch centerline · locks the Tree of Life", ["K-001", "Q-001", "R-001", "Q-002", "R-002"], extra)
    s.save("step-12.svg", "Step 12 — ribbon R-002")


def page_step13():
    s = step_sheet(13, 3, "Drop the top light cassettes", "Q-003 nested squares — foliage row under the eave")
    parts_box(s, [(2, "Q-003", "nested-rects cassette (foliage)")])
    elev_state(s, posts=("P0", "P1", "P2", "P3"), layers=["K-001", "Q-001", "R-001", "Q-002", "R-002", "Q-003"])
    sl = SLATS["Q-003"]
    for la, rb in ((1, 2), (2, 3)):
        cx = (LY["posts"][la]["cx"] + LY["posts"][rb]["cx"]) / 2
        s.arrow(XE(cx), YE(sl["z1"]) - 80, XE(cx), YE(sl["z1"]) - 16)
        hl_box(s, LY["posts"][la]["cx"] + FX / 2, sl["z0"], LY["bay_clear"], sl["h"])
    s.text(430, 1000, f"Top edge grooves into the eave soffit later. The φ pair is now visible: {LY['light_minor']:g}″ / {LY['light_major']:g}″ / {LY['light_minor']:g}″ lights.", 13, INK)
    s.save("step-13.svg", "Step 13 — Q-003 cassettes")


def page_step14():
    s = step_sheet(14, 3, "Drive the kusabi wedges", "Lock every nuki at P1 / P2 / P3 — friction, not glue")
    parts_box(s, [(12, "W-001", "kusabi wedge (9 + 3 spare)")])
    elev_state(s, posts=("P0", "P1", "P2", "P3"),
               layers=["K-001", "Q-001", "R-001", "Q-002", "R-002", "Q-003"], wedges=True)
    for p in LY["posts"][1:]:
        hl_box(s, p["cx"] + FX / 2 - 0.5, SLATS["K-001"]["cl"] - 2, 3, SLATS["R-002"]["cl"] - SLATS["K-001"]["cl"] + 4)
    ix, iy = 1330, 120
    s.rect(ix, iy, 290, 200, fill="#eceae2", stroke=INK, sw=2, rx=12)
    s.text(ix + 14, iy + 26, "DETAIL — KUSABI", 12, ACC, bold=True)
    s.rect(ix + 40, iy + 60, 60, 110, fill=PIER, stroke=INK, sw=1.6)
    s.rect(ix + 10, iy + 95, 240, 34, fill=BELT, stroke=INK, sw=1.6)
    s.poly([(ix + 104, iy + 100), (ix + 150, iy + 112), (ix + 104, iy + 124)], fill=OAK, stroke=INK, sw=1.2)
    s.arrow(ix + 200, iy + 112, ix + 158, iy + 112)
    s.text(ix + 14, iy + 186, "Tap until snug. Reverse to strip in winter.", 10.5, INK)
    never_glue(s, 1360, 900)
    s.save("step-14.svg", "Step 14 — kusabi wedges")


def page_step15():
    s = step_sheet(15, 3, "Peg the Roman-brick pier wrap", "36 blocks · P1 / P2 / P3 · Darwin Martin texture")
    parts_box(s, [(36, "T-001", '2×2 block 1.5×1.5×7″ · ¼″ pegs')])
    elev_state(s, posts=("P0", "P1", "P2", "P3"),
               layers=["K-001", "Q-001", "R-001", "Q-002", "R-002", "Q-003"], wedges=True, bricks=True)
    for p in LY["posts"][1:]:
        hl_box(s, p["cx"] - FX / 2 - 0.6, 1.5, FX + 1.2, H - CAP_T - 3)
    s.text(430, 1000, "Stacked running bond with ⅜″ raked joints — shadow, not structure. ¼″ pegs only; ½″ splits the 2×2.", 13, INK)
    s.save("step-15.svg", "Step 15 — pier wrap T-001")


# ---------- BAG 4 ----------
def page_step16():
    s = step_sheet(16, 4, "Set the eave — kama-tsugi at P2", "Two 2×12 halves scarf over the mid pier · drawbore peg")
    parts_box(s, [(1, "C-001", '2×12 eave (2 halves)'), (1, "W-002", "oak peg — scarf")])
    elev_state(s, posts=("P0", "P1", "P2", "P3"),
               layers=["K-001", "Q-001", "R-001", "Q-002", "R-002", "Q-003"], wedges=True, bricks=True, eave=True)
    s.arrow(XE(LY["posts"][2]["cx"]), YE(H) - 96, XE(LY["posts"][2]["cx"]), YE(H) - 26)
    hl_box(s, LY["cap_x0"], H - CAP_T, LY["cap_len"], CAP_T)
    ix, iy = 1330, 200
    s.rect(ix, iy, 290, 170, fill="#eceae2", stroke=INK, sw=2, rx=12)
    s.text(ix + 14, iy + 26, "DETAIL — KAMA-TSUGI", 12, ACC, bold=True)
    s.poly([(ix + 30, iy + 100), (ix + 120, iy + 100), (ix + 142, iy + 84), (ix + 120, iy + 68), (ix + 30, iy + 68)], fill=BELT, stroke=INK, sw=1.6)
    s.poly([(ix + 142, iy + 84), (ix + 120, iy + 68), (ix + 250, iy + 68), (ix + 250, iy + 100), (ix + 120, iy + 100)], fill="#8a9094", stroke=INK, sw=1.6)
    s.line(ix + 131, iy + 60, ix + 131, iy + 108, 2.4, HL)
    s.text(ix + 14, iy + 140, "Sickle scarf · drawbore 1/8″ · peg Ø 3/8″", 10.5, INK)
    s.text(430, 1000, f'Eave cantilevers {kv("cap_overhang"):g}″ past the end piers and ~2.9″ front and back. It should look like it floats.', 13, INK)
    s.save("step-16.svg", "Step 16 — eave C-001")


def page_step17():
    s = step_sheet(17, 4, "Hang the fascia · cap the latch post · light", "The shadow line that makes it read as Wright")
    parts_box(s, [(1, "C-003", "1×4 fascia"), (1, "C-002", "latch cap stub"), (1, "H-006", "12V IP65 tape + driver")])
    elev_state(s, posts=("P0", "P1", "P2", "P3"),
               layers=["K-001", "Q-001", "R-001", "Q-002", "R-002", "Q-003"], wedges=True, bricks=True,
               eave=True, fascia=True, stub=True)
    hl_box(s, LY["cap_x0"], H - CAP_T - kv("fascia_h"), LY["cap_len"], kv("fascia_h"))
    p0 = LY["posts"][0]["cx"]
    hl_box(s, p0 - FX / 2 - 0.5, H - CAP_T, FX + 1.0, CAP_T)
    s.text(430, 976, "C-003 hangs under the garden edge of the eave — housed, pegged. C-002 stub caps P0 without bridging the gate.", 13, INK)
    s.text(430, 1000, "H-006 LED tape lies in the soffit dado with its wood cover slat. Driver goes in the P3 planter niche — never at the house.", 13, DIM)
    s.save("step-17.svg", "Step 17 — fascia, stub, light")


# ---------- BAG 5 ----------
def page_step18():
    s = step_sheet(18, 5, "Assemble the gate frame", "Bench sub-assembly · hozo mortise & tenon, drawbored")
    parts_box(s, [(1, "G-001", "hinge stile"), (1, "G-002", "latch stile"),
                  (1, "G-003", "rail @ belt 1"), (1, "G-004", "rail @ belt 2"),
                  (1, "G-005", "top belt rail"), (1, "G-006", "bottom rail"),
                  (1, "G-007", "top rail"), (10, "W-002", "oak pegs")])
    gate_bench(s, frame=True, cassettes=False)
    s.text(GXb(GX0 + GW / 2), GYb(GZ0 + GH) - 24, f'LEAF {GW:g}″ × {GH:g}″ — RAILS ALIGN TO THE SCREEN BELTS', 13, ACC, "middle", bold=True)
    s.text(GXb(GX0 + GW / 2), GYb(GZ0) + 40, "Tenon = ⅓ of the 1.5″ stock. Drawbore ⅛″ toward the shoulder. Dry-fit before pegging.", 12, INK, "middle")
    s.text(GXb(GX0 + GW / 2), GYb(GZ0) + 64, "Shop brace G-008 (if you add one) goes on the DRIVEWAY face — the garden face stays pure.", 12, DIM, "middle")
    s.save("step-18.svg", "Step 18 — gate frame (bench)")


def page_step19():
    s = step_sheet(19, 5, "Slide in the gate Tree of Life", "Cassettes float in stile grooves — same pattern as the screen")
    parts_box(s, [(3, "G-009", "Tree of Life / nested cassettes")])
    gate_bench(s, frame=True, cassettes=True)
    s.arrow(GXb(GX0 + GW / 2), GYb(GZ0 + GH) - 92, GXb(GX0 + GW / 2), GYb(GZ0 + GH) - 22)
    s.text(GXb(GX0 + GW / 2), GYb(GZ0) + 40, "Solid water-table panel at the bottom (dog), then nested squares / three trees / nested squares.", 12, INK, "middle")
    s.text(GXb(GX0 + GW / 2), GYb(GZ0) + 64, "The gate lights line up in z with the screen lights — the pattern runs across the whole fence.", 12, DIM, "middle")
    s.save("step-19.svg", "Step 19 — gate cassettes")


def page_step20():
    s = step_sheet(20, 5, "Hang the gate on its oak pivots", "Lower onto the sill pivot at P1 · top pin into the eave soffit")
    parts_box(s, [(2, "W-003", "oak pivot Ø1.25″")])
    elev_state(s, posts=("P0", "P1", "P2", "P3"),
               layers=["K-001", "Q-001", "R-001", "Q-002", "R-002", "Q-003"], wedges=True, bricks=True,
               eave=True, fascia=True, stub=True, gate=True)
    s.arrow(XE(GX0 + GW / 2), YE(H) - 100, XE(GX0 + GW / 2), YE(H) - 30)
    hl_box(s, GX0, GZ0, GW, GH)
    s.circle(XE(LY["posts"][1]["cx"] - FX / 2 - 1), YE(1), 9, fill=OAK, stroke=INK, sw=1.6)
    s.circle(XE(LY["posts"][1]["cx"] - FX / 2 - 1), YE(H - CAP_T - 1), 9, fill=OAK, stroke=INK, sw=1.6)
    s.text(430, 976, "Leaf weight rides the bottom pivot in compression to the driveway sill. Lift straight up +Z to remove.", 13, INK)
    s.text(430, 1000, f'Clearances: {kv("gate_bottom_clear"):g}″ under the leaf (dog), {kv("gate_top_clear"):g}″ under the eave. Two-person lift.', 13, DIM)
    s.save("step-20.svg", "Step 20 — hang the gate")


def page_step21():
    s = step_sheet(21, 5, "Fit the sliding latch bar", "Oak bar through the latch stile into the P0 mortise — Latch B")
    parts_box(s, [(1, "G-010", 'oak latch bar 1.5×3.5×18″'), (1, "W-002", "cross-peg")])
    elev_state(s, posts=("P0", "P1", "P2", "P3"),
               layers=["K-001", "Q-001", "R-001", "Q-002", "R-002", "Q-003"], wedges=True, bricks=True,
               eave=True, fascia=True, stub=True, gate=True, latch=True)
    cl = LY["latch_cl"]
    s.arrow(XE(GX0) - 120, YE(cl + 1.75) + 12, XE(GX0) - 54, YE(cl + 1.75) + 12)
    hl_box(s, GX0 - 8, cl - 2.5, 10, 5)
    s.text(430, 976, f'Bar slides at CL {cl:.2f}″ AFF (the R-002 belt line) into the mortise in P0. Gravity catch + cross-peg. Optional padlock hasp.', 13, INK)
    s.text(430, 1000, "Swing test: full 90° into the garden, no rub at the water table, latch throws home smooth. No epoxy, no house strike.", 13, DIM)
    s.save("step-21.svg", "Step 21 — latch bar")


# ---------- BAG 6 ----------
def page_step22():
    s = step_sheet(22, 6, "Knock down and paint", "The paint IS the weather system — Buffalo four-season prep")
    parts_box(s, [(1, "H-005", "primer + owner-gray enamel")], title="MATERIALS THIS STEP")
    stages = [
        ("1", "EASE", 'break every arris 1/16″ — paint dies on sharp corners'),
        ("2", "SEAL", "end-grain sealer on every cut end"),
        ("3", "DRY", "PT water table + troughs must be dry first"),
        ("4", "PRIME", "exterior primer, all faces"),
        ("5", "GRAY ×2", "two finish coats owner gray · extra inside troughs"),
    ]
    for i, (n, t, d) in enumerate(stages):
        x = 430 + (i % 3) * 400
        y = 260 + (i // 3) * 210
        s.rect(x, y, 370, 160, fill="#eceae2", stroke=INK, sw=2.5, rx=14)
        s.circle(x + 44, y + 50, 26, fill=ACC, stroke=INK, sw=2)
        s.text(x + 44, y + 58, n, 22, PAPER, "middle", bold=True)
        s.text(x + 86, y + 44, t, 18, INK, bold=True)
        s.text(x + 24, y + 100, d, 12, DIM)
    s.rect(430, 700, 1170, 90, fill="#f7e8de", stroke=HL, sw=2.5, rx=14)
    s.text(450, 736, "MASK: every locking face — tenon cheeks, nuki bearing faces, kusabi slots, pivot sockets. Paint on a locking face = a stuck joint in February.", 13, HL, bold=True)
    s.text(450, 762, "Dry-fit first (steps 1–21), knock down in reverse, paint the parts flat, then rebuild. Label every wedge and cassette as it comes out.", 13, INK)
    s.save("step-22.svg", "Step 22 — paint")


def page_step23():
    s = step_sheet(23, 6, "Place the troughs · stone · soil · plant", "The planters from step 4 become the wind ballast")
    parts_box(s, [(2, "F-005", "trough (from step 4)"), (1, "H-007", '4″ in-box drainage stone')])
    plan_state(s, pads=True, sills=True, ties=True, planters=True)
    for la, rb in ((1, 2), (2, 3)):
        cx = (LY["posts"][la]["cx"] + LY["posts"][rb]["cx"]) / 2
        s.arrow(XP(cx), YP(kv("base_spread_cl") / 2 + kv("planter_y") + 14), XP(cx), YP(kv("base_spread_cl") / 2 + kv("planter_y") - 4))
    b = PROJ["ballast"]
    s.text(430, 700, f'Garden side of bays P1–P2 and P2–P3 ONLY. Never at the house / gate. ½″ air gap from the posts.', 13, INK)
    s.text(430, 724, f'Stone 4″ in the box, wet soil on top: {b["provided_lb"]:g} lb provided vs {b["required_lb"]:g} lb required (planning FS {b["fs"]:g}).', 13, INK)
    s.text(430, 748, "Water regularly — a dry planter is missing ballast. LED driver lives in a dry niche of the P3 trough.", 13, DIM)
    s.save("step-23.svg", "Step 23 — plant the ballast")


def page_step24():
    s = step_sheet(24, 6, "Done — and the winter reverse", "You built the thing that otherwise never exists")
    SC, ox, oy = 7.2, 400, 700

    def Xc(x):
        return ox + x * SC

    def Yc(z):
        return oy - z * SC

    paint_front_elevation(s, LY, Xc, Yc, SC, kv, gate=True, labels=True, planters=True)
    s.text(ox + L * SC / 2, 160, "COMPLETE", 42, ACC, "middle", bold=True)
    rev = [
        "WINTER (reverse order):",
        "24-23  empty / lift the troughs",
        "21-20  latch peg out · lift gate off pivots +Z",
        "17-16  light, fascia, eave halves off",
        "15-14  brick wrap stays on posts · knock wedges out — bag & label",
        "13-8   withdraw cassettes and belts toward P3",
        "7-5    lift posts straight up",
        "4-1    ladder can stay on the slab or come in",
    ]
    for i, t in enumerate(rev):
        s.text(60, 800 + i * 26, t, 13, INK if i else ACC, bold=(i == 0))
    s.text(900, 800, "SPRING: run this manual forward again.", 13, ACC, bold=True)
    s.text(900, 826, "Wedges snug, not brutal. Replant. Re-check plumb.", 13, INK)
    s.text(900, 852, "Nothing is buried. Nothing is poured. Nothing rusts.", 13, DIM)
    s.save("step-24.svg", "Step 24 — complete + winter reverse")


# ---------------------------------------------------------------- viewer page
def write_viewer():
    figs = "\n".join(
        f"<figure id='p{i}'><img src='{fn}' alt='{esc(cap)}' loading='lazy'/><figcaption><b>{i:02d}</b> {esc(cap)}</figcaption></figure>"
        for i, (fn, cap) in enumerate(PAGES)
    )
    html = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>MARTIN Build Manual — Rev __REV__ · step by step</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Newsreader:opsz,wght@6..72,500;6..72,600&display=swap" rel="stylesheet"/>
<style>
:root{--ink:#1a1f24;--paper:#f3f1ec;--sage:#5a6a4a;--sage-hi:#8fad78;--dim:#9aa3a6}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--ink);color:var(--paper);font-family:"IBM Plex Mono",monospace;line-height:1.5}
header{padding:48px 24px 20px;max-width:1200px;margin:0 auto}
.k{font:500 11px/1 "IBM Plex Mono",monospace;letter-spacing:.28em;color:var(--sage-hi);text-transform:uppercase}
h1{font-family:"Newsreader",Georgia,serif;font-weight:600;font-size:clamp(34px,6vw,64px);margin:10px 0 8px}
.sub{color:var(--dim);font-size:14px;max-width:70ch}
nav{padding:10px 24px 20px;max-width:1200px;margin:0 auto;display:flex;gap:10px;flex-wrap:wrap}
nav a{color:var(--dim);text-decoration:none;font-size:11px;border:1px solid rgba(243,241,236,.2);padding:7px 10px;letter-spacing:.08em}
nav a:hover{color:var(--paper);border-color:var(--paper)}
main{max-width:1200px;margin:0 auto;padding:0 24px 80px}
figure{margin:26px 0}
img{width:100%;display:block;border:1px solid rgba(243,241,236,.18)}
figcaption{padding:10px 2px;color:var(--dim);font-size:12px}
figcaption b{color:var(--sage-hi);margin-right:8px}
@media print{body{background:#fff}header,nav{display:none}img{border:none;page-break-after:always}}
</style></head><body>
<header>
<p class="k">MARTIN · Rev __REV__ · step-by-step</p>
<h1>Build Manual</h1>
<p class="sub">__NSTEPS__ steps · 6 bags · generated from the fabrication kernel. Print at 100% on A3 (~71% on Letter). Numbered parts callouts on every step; orange arrows are this step's move. No glue, no nails, no concrete.</p>
</header>
<nav>
<a href="../">← Design</a><a href="../app/">Build app</a><a href="../planforge/">Planforge</a><a href="../fab/">Fab package</a>
<a href="#p0">Cover</a><a href="#p1">Parts</a><a href="#p2">Bag 1</a><a href="#p6">Bag 2</a><a href="#p9">Bag 3</a><a href="#p17">Bag 4</a><a href="#p19">Bag 5</a><a href="#p23">Bag 6</a>
</nav>
<main>
__FIGS__
</main>
</body></html>
"""
    html = html.replace("__NSTEPS__", str(TOTAL_STEPS)).replace("__FIGS__", figs).replace("__REV__", PROJECT["REVISION"])
    path = os.path.join(OUT, "index.html")
    with open(path, "w") as f:
        f.write(html)
    print("wrote", os.path.relpath(path, ROOT))


def main():
    page_cover()
    page_inventory()
    page_step1()
    page_step2()
    page_step3()
    page_step4()
    page_step5()
    page_step6()
    page_step7()
    page_step8()
    page_step9()
    page_step10()
    page_step11()
    page_step12()
    page_step13()
    page_step14()
    page_step15()
    page_step16()
    page_step17()
    page_step18()
    page_step19()
    page_step20()
    page_step21()
    page_step22()
    page_step23()
    page_step24()
    write_viewer()
    print(f"MARTIN build manual done → {OUT}  ({len(PAGES)} pages)")


if __name__ == "__main__":
    main()
