#!/usr/bin/env python3
"""Generate MARTIN marketing plan SVG sheets (A3 landscape, printable).

Dimensions come from martin_kernel.build_project() — do not hard-code.
Run:  python3 scripts/gen_martin_plans.py
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "fence", "martin"))
from martin_kernel import build_project, v as kv  # noqa: E402
from martin_elevation import paint_front_elevation, paint_motif, paint_pier_bricks, CASS, BELT, EARTH, EAVE, MUNTIN, PIER  # noqa: E402

OUT = os.path.join(ROOT, "fence", "martin", "plans")
os.makedirs(OUT, exist_ok=True)

IN = 25.4
PROJ = build_project()
LY = PROJ["layout"]
NEST = PROJ["nest"]

# Derived from martin_kernel — do not hard-code controlling dims here.
P = dict(
    length=kv("overall_length"),
    height=kv("overall_height"),
    post_x=kv("post_x"),
    post_y=kv("post_y"),
    post_tenon_x=kv("post_tenon_x"),
    post_tenon_y=kv("post_tenon_y"),
    post_tenon_h=kv("post_tenon_h"),
    gate_clear=kv("gate_clear"),
    gate_gap=kv("gate_gap"),
    rail_t=kv("rail_t"),
    rail_h=kv("rail_h"),
    rail_z_cl=LY["rail_cls"],
    cap_t=kv("cap_t"),
    cap_w=kv("cap_w"),
    board_t=kv("board_t"),
    board_w=kv("board_w"),
    board_gap=kv("board_gap"),
    sill_overhang=kv("sill_overhang"),
    base_width=LY["base_width"],
    sill_h=kv("sill_h"),
    sill_t=kv("sill_t"),
    drop_off=kv("drop_off"),
    tie_len=LY["tie_len"],
    pack_h=LY["pack_h"],
    furniture_pad_t=kv("furniture_pad_t"),
    base_spread_cl=LY["base_spread_cl"],
    latch_bar=kv("latch_bar_l"),
    planter_x=kv("planter_x"),
    planter_y=kv("planter_y"),
    planter_h=kv("planter_h"),
)

fx = P["post_x"]
L = P["length"]
gate = P["gate_clear"]
POSTS = tuple(p["cx"] for p in LY["posts"])
P0, P1, P2, P3 = POSTS
bay_clear = LY["bay_clear"]
H = P["height"]

# ---- sheet primitives --------------------------------------------------------
W, Hpx = 1680, 1188  # A3 landscape @ ~4 px/mm
INK, DIM, ACC, PAPER, LIGHT = "#1a1f24", "#5a6a4a", "#3d5a4c", "#f3f1ec", "#c5c8c2"
GRAY = "#6e7578"
MONO = "font-family='IBM Plex Mono, Menlo, monospace'"
SER = "font-family='Georgia, serif'"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Sheet:
    def __init__(self, code, title, scale_note):
        self.code, self.title, self.scale_note = code, title, scale_note
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
        self.add(
            f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' "
            f"fill='{fill}' stroke='{stroke}' stroke-width='{sw}'{d}/>"
        )

    def poly(self, pts, fill="none", stroke=INK, sw=2, close=True):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        tag = "polygon" if close else "polyline"
        self.add(
            f"<{tag} points='{p}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}'/>"
        )

    def text(
        self,
        x,
        y,
        s,
        size=20,
        color=INK,
        anchor="start",
        mono=True,
        bold=False,
        rot=None,
        bg=False,
    ):
        f = MONO if mono else SER
        wgt = " font-weight='600'" if bold else ""
        r = f" transform='rotate({rot} {x:.1f} {y:.1f})'" if rot is not None else ""
        if bg and rot is None:
            w = len(s) * size * 0.58
            bx = {"start": x - 4, "middle": x - w / 2 - 4, "end": x - w - 4}[anchor]
            self.add(
                f"<rect x='{bx:.1f}' y='{y - size:.1f}' width='{w + 8:.1f}' "
                f"height='{size + 6:.1f}' fill='{PAPER}'/>"
            )
        self.add(
            f"<text x='{x:.1f}' y='{y:.1f}' {f} font-size='{size}' fill='{color}' "
            f"text-anchor='{anchor}'{wgt}{r}>{esc(s)}</text>"
        )

    def dim_h(self, x1, x2, y, label, offset=0, size=16):
        yy = y + offset
        for x in (x1, x2):
            self.line(x, y, x, yy + 8, 1, DIM)
        self.line(x1, yy, x2, yy, 1.4, DIM)
        for x, s in ((x1, 1), (x2, -1)):
            self.poly(
                [(x, yy), (x + s * 10, yy - 4), (x + s * 10, yy + 4)],
                fill=DIM,
                stroke=DIM,
                sw=0.5,
            )
        self.text((x1 + x2) / 2, yy - 6, label, size, DIM, "middle", bg=True)

    def dim_v(self, y1, y2, x, label, offset=0, size=16):
        xx = x + offset
        for y in (y1, y2):
            self.line(x, y, xx + (8 if offset >= 0 else -8), y, 1, DIM)
        self.line(xx, y1, xx, y2, 1.4, DIM)
        for y, s in ((y1, 1), (y2, -1)):
            self.poly(
                [(xx, y), (xx - 4, y + s * 10), (xx + 4, y + s * 10)],
                fill=DIM,
                stroke=DIM,
                sw=0.5,
            )
        self.text(xx + (12 if offset >= 0 else -12), (y1 + y2) / 2 + 5, label, size, DIM,
                  "start" if offset >= 0 else "end", bg=True, rot=-90)

    def titleblock(self):
        self.rect(0, 0, W, Hpx, fill=PAPER, stroke=INK, sw=3)
        self.rect(24, 24, W - 48, Hpx - 48, fill="none", stroke=INK, sw=1.2)
        self.line(24, Hpx - 90, W - 24, Hpx - 90, 1.5, INK)
        self.text(40, Hpx - 58, "MARTIN", 28, ACC, bold=True, mono=False)
        self.text(160, Hpx - 62, f"{self.code}  ·  {self.title}", 18, INK, bold=True)
        self.text(40, Hpx - 34, self.scale_note, 13, DIM)
        self.text(W - 40, Hpx - 58, "Buffalo NY · Prairie + Japanese joinery", 14, DIM, "end")
        self.text(W - 40, Hpx - 34, f"Sit-on-grade · No nails in timber · Rev {PROJ['project']['REVISION']}", 13, DIM, "end")

    def save(self):
        path = os.path.join(OUT, f"{self.code}_{self.title.split()[0].lower()}.svg")
        # safer filenames
        names = {
            "M-1": "M1_general.svg",
            "M-2": "M2_elevation.svg",
            "M-3": "M3_joinery.svg",
            "M-4": "M4_pad_piers.svg",
            "M-5": "M5_gate_latch.svg",
            "M-6": "M6_cutlist.svg",
        }
        path = os.path.join(OUT, names[self.code])
        svg = (
            f"<?xml version='1.0' encoding='UTF-8'?>\n"
            f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{Hpx}' "
            f"viewBox='0 0 {W} {Hpx}'>\n"
            + "\n".join(self.b)
            + "\n</svg>\n"
        )
        with open(path, "w") as f:
            f.write(svg)
        print("wrote", path)
        return path


# ---- drawing helpers in inches → px -----------------------------------------
# elevation scale: 143" fits in ~1200 px → ~8.4 px/in
S = 8.2
OX, OY = 80, 820  # origin at sill top, left outer face


def X(xin):
    return OX + xin * S


def Y(zin):
    """z up from sill top; SVG y down."""
    return OY - zin * S


def sheet_m1():
    s = Sheet("M-1", "General arrangement", f"Scale 1:16 approx · dimensions in inches · Rev {PROJ['project']['REVISION']} Tree of Life")
    s.titleblock()
    s.text(40, 70, "FRONT ELEVATION — garden face", 16, ACC, bold=True)
    s.text(40, 94, '143" overall · 65" high · Darwin Martin Tree of Life · cantilevered eave · 2×4 Prairie ribbons · live planters', 13, DIM)

    paint_front_elevation(s, LY, X, Y, S, kv, gate=True, labels=True, planters=True)

    # dimensions
    s.dim_h(X(0), X(L), Y(0), '143" OVERALL', offset=48)
    s.dim_h(X(fx), X(fx + gate), Y(0), '36" GATE', offset=78)
    s.dim_h(X(P1 + fx / 2), X(P2 - fx / 2), Y(H), f'{bay_clear:.2f}" BAY', offset=-36)
    s.dim_h(X(P2 + fx / 2), X(P3 - fx / 2), Y(H), f'{bay_clear:.2f}" BAY', offset=-36)
    s.dim_v(Y(0), Y(H), X(L), '65"', offset=40)

    # plan mini
    s.text(40, 980, "PLAN (ladder)", 14, ACC, bold=True)
    py = 1040
    ps = 4.5
    for i, cx in enumerate(POSTS):
        s.rect(80 + cx * ps - fx * ps / 2, py - P["post_y"] * ps / 2,
               fx * ps, P["post_y"] * ps, fill="#d9dcde", stroke=INK, sw=1.2)
        if i > 0:
            s.rect(80 + cx * ps - (fx + 1.4) * ps / 2, py - (P["post_y"] + 1.2) * ps / 2,
                   (fx + 1.4) * ps, (P["post_y"] + 1.2) * ps, fill="none", stroke=DIM, sw=0.6)
    s.rect(80 - P["sill_overhang"] * ps, py - P["base_width"] * ps / 2,
           (L + 2 * P["sill_overhang"]) * ps, P["base_width"] * ps,
           fill="none", stroke=DIM, sw=1, dash="4 3")
    # planters as troughs garden-side of P1–P3
    for la, rb in ((1, 2), (2, 3)):
        x0 = 80 + POSTS[la] * ps
        x1 = 80 + POSTS[rb] * ps
        s.rect(x0 + 4, py + P["post_y"] * ps / 2 + 4, x1 - x0 - 8, 18 * ps * 0.35,
               fill="#6a6e66", stroke=INK, sw=0.8)
    s.text(80 + L * ps / 2, py + P["base_width"] * ps / 2 + 22,
           f'LADDER {P["base_width"]:g}" WIDE · PLANTER TROUGHS GARDEN-SIDE OF P1–P3 · NO PLANTER AT HOUSE', 12, DIM, "middle")

    notes = [
        "DESIGN: Darwin Martin House Tree of Life — original wood muntins, not licensed glass.",
        "MACRO: deep eave + fascia shadow, belts that stick past the piers, Roman-brick piers, recessed lights.",
        "LIGHTS: ¾″ dog-grid nested gold squares / three trees / nested squares. Solid 2×12 water table.",
        "GATE: Tree of Life portal flush to the house. Oak pivots at P1. No Z-brace on the garden face.",
        "BALLAST: Live planters P1–P2 and P2–P3. Stone inside boxes only — not a pad.",
        "WINTER: Knock wedges → withdraw cassettes → lift gate off oak pivots → lift posts → empty troughs.",
        "FINISH: Ease 1/16″, end-grain sealer, PT dry then prime, two owner-gray coats. Buffalo 4-season.",
    ]
    for i, n in enumerate(notes):
        s.text(40, 118 + i * 18, n, 11, INK)

    s.save()


def sheet_m2():
    s = Sheet("M-2", "Elevation & light-screen", "Scale ~1:12 · one privacy bay · Tree of Life")
    s.titleblock()
    s.text(40, 70, "PRIVACY BAY — TREE OF LIFE BETWEEN PROJECTING BELTS", 16, ACC, bold=True)

    S2 = 12.0
    ox, oy = 80, 900

    def x(vin):
        return ox + vin * S2

    def y(vin):
        return oy - vin * S2

    bay = bay_clear
    # local coords: post left at 0, bay, post right
    # Shift motifs from actual P1 bay into this frame
    x_shift = P1 + fx / 2  # world x of left bay inner face

    def Xx(xin):
        return x(xin - x_shift + fx)

    def Yy(zin):
        return y(zin)

    # cassette field
    for sl in LY["slats"]:
        if sl["id"].startswith("Q-"):
            s.rect(x(fx), y(sl["z1"]), bay * S2, sl["h"] * S2, fill=CASS, stroke="none", sw=0)
    for m in LY["motifs"]:
        if m.get("bay") == 0:
            paint_motif(s, m, Xx, Yy, S2)

    # water table + belts spanning past piers
    for sl in LY["slats"]:
        if sl["id"] == "K-001":
            s.rect(x(-1.5), y(sl["z1"]), (fx + bay + fx + 3) * S2, sl["h"] * S2, fill=EARTH, stroke=INK, sw=1.4)
        elif sl["id"].startswith("R-"):
            s.rect(x(-1.5), y(sl["z1"]), (fx + bay + fx + 3) * S2, sl["h"] * S2, fill=BELT, stroke=INK, sw=1.3)

    # piers
    s.rect(x(0), y(H - P["cap_t"]), fx * S2, (H - P["cap_t"]) * S2, fill=PIER, stroke=INK)
    s.rect(x(fx + bay), y(H - P["cap_t"]), fx * S2, (H - P["cap_t"]) * S2, fill=PIER, stroke=INK)
    paint_pier_bricks(s, x, y, S2, fx / 2, fx, 1.5, H - P["cap_t"] - 1)
    paint_pier_bricks(s, x, y, S2, fx + bay + fx / 2, fx, 1.5, H - P["cap_t"] - 1)

    # eave + fascia
    s.rect(x(-2.0), y(H), (fx + bay + fx + 4) * S2, P["cap_t"] * S2, fill=EAVE, stroke=INK)
    s.rect(x(-2.0), y(H - P["cap_t"]), (fx + bay + fx + 4) * S2, kv("fascia_h") * S2, fill="#1a1f24", stroke=INK, sw=1)

    s.dim_v(y(0), y(H), x(fx + bay + fx), '65"', offset=36)
    for sl in LY["slats"]:
        if sl["nuki"]:
            s.dim_v(y(0), y(sl["cl"]), x(-1.5), f'{sl["cl"]:g}" CL', offset=-46)
    s.dim_h(x(fx), x(fx + bay), y(0), f'{bay:.2f}" CLEAR', offset=40)

    s.text(x(fx + bay / 2), y(LY["slats"][2]["cl"]) + 4, "BELT", 11, PAPER, "middle", bold=True)

    # schedule
    s.text(980, 70, "LAYER SCHEDULE (bottom → top)", 16, ACC, bold=True)
    rows = [("Mark", "Stock", "Joinery", "CL AFF", "Role")]
    for sl in LY["slats"]:
        j = "nuki + kusabi" if sl["nuki"] else "cassette groove"
        rows.append((sl["id"], sl["stock"], j, f'{sl["cl"]:g}"', sl["role"][:32]))
    rows.append(("C-001", "2×12", "kama-tsugi + light dado", '65" top', "Wright eave (cantilever)"))
    rows.append(("C-003", "1×4", "housed under eave", "soffit", "Fascia / shadow line"))
    rows.append(("POST", "4×6 + 2×2 wrap", "3.5×5.5 + Roman brick", "full height", "Piers P1–P3"))
    yy = 110
    for r in rows:
        xx = 980
        widths = (70, 90, 130, 80, 200)
        for i, cell in enumerate(r):
            s.text(xx, yy, cell, 12, INK if r[0] != "Mark" else DIM, bold=(r[0] == "Mark"))
            xx += widths[i]
        yy += 22
        s.line(980, yy - 16, 1620, yy - 16, 0.6, LIGHT)

    s.text(980, 430, "WHY THIS IS NOT A RANCH FENCE", 16, ACC, bold=True)
    bullets = [
        "Deep 2×12 eave + 1×4 fascia — Wright plane, not a 2× lid.",
        "2×4 Prairie ribbons cantilever 3″ past the piers (rail_reveal).",
        "Piers wrapped in Roman-brick 2×2 (Darwin Martin texture).",
        "Three recessed lights: nested squares / Tree of Life / nested squares.",
        f"Solid 2×12 PT water table — dog crawl stop. Q-001 max {kv('pattern_gap_dog'):g}″; upper lights {kv('pattern_gap'):g}″.",
        f"φ sizes the cassette pair ({LY['light_minor']:g} / {LY['light_major']:g}). Do not substitute 2×10 ranch rails.",
        "Through-nuki only K-001 + R-001 + R-002. Cassettes withdraw for winter.",
        "Original wood interpretation of Darwin Martin Tree of Life — not licensed glass.",
    ]
    for i, b in enumerate(bullets):
        s.text(980, 465 + i * 26, "•  " + b, 13, INK)

    s.save()


def sheet_m3():
    s = Sheet("M-3", "Joinery details", "Details @ 1:4 · cut from dimensional lumber")
    s.titleblock()

    # Nuki detail
    s.text(40, 70, "DETAIL 1 — NUKI THROUGH-RIBBON (2×4 IN 4×6)", 16, ACC, bold=True)
    sx, sy = 80, 420
    # post section
    s.rect(sx, sy - 120, 90, 240, fill="#d9dcde", stroke=INK, sw=2)  # post
    nh = 28  # schematic 2×4 ribbon (thin Wright plane, not a 2×10 ranch rail)
    s.rect(sx - 80, sy - nh / 2, 250, nh, fill=GRAY, stroke=INK, sw=2)
    s.poly([(sx + 70, sy - 10), (sx + 95, sy), (sx + 70, sy + 10)], fill=ACC, stroke=ACC)  # wedge
    s.text(sx + 45, sy + 150, "4×6 POST", 13, DIM, "middle")
    s.text(sx + 170, sy - 28, "2×4 RIBBON NUKI", 13, DIM)
    s.text(sx + 110, sy + 5, "WEDGE", 12, ACC, bold=True)
    s.text(sx - 10, 70 + 40, f'Mortise: 1.50" × {kv("belt_h"):.2f}" through · cheeks 2.00" of 5.50" post each side of 1.50" rail', 13, INK)
    s.text(sx - 10, 70 + 62, 'Through-nuki only water table + two 2×4 ribbons. Cassettes groove in — keep the post web.', 13, INK)

    # Foot tenon
    s.text(520, 70, "DETAIL 2 — FOOT TENON INTO CROSS-TIE", 16, ACC, bold=True)
    tx, ty = 560, 380
    s.rect(tx, ty - 160, 70, 160, fill="#d9dcde", stroke=INK, sw=2)
    s.rect(tx + 10, ty, 50, 80, fill="#d9dcde", stroke=INK, sw=2)
    s.rect(tx - 50, ty, 170, 90, fill=LIGHT, stroke=INK, sw=2)
    s.text(tx + 35, ty - 175, "POST", 13, DIM, "middle")
    s.text(tx + 35, ty + 40, "TENON", 12, ACC, "middle", bold=True)
    s.text(tx + 35, ty + 78, "F-003 TIE", 12, DIM, "middle")
    s.text(520, 100, 'Shouldered tenon 2.5" × 4.5" × 3.5" into F-003 (sit-on-grade)', 13, INK)
    s.text(520, 122, "No sleeve, no pour, no post hole. Lift post +Z for winter.", 13, INK)
    s.text(520, 144, "Ladder sills + live planters (garden side) resist overturning", 13, INK)

    # Scarf
    s.text(40, 560, "DETAIL 3 — KAMA-TSUGI CAP SCARF AT P2", 16, ACC, bold=True)
    s.poly([(80, 720), (200, 720), (230, 700), (200, 680), (80, 680)], fill=GRAY, stroke=INK, sw=2)
    s.poly([(230, 700), (200, 680), (320, 680), (350, 700), (320, 720), (200, 720)],
           fill="#8a9094", stroke=INK, sw=2)
    s.line(215, 675, 215, 725, 2, ACC)
    s.text(215, 745, "OAK PEG (drawbore)", 12, ACC, "middle")
    s.text(40, 590, "Cut sickle scarf in 2×12 eave · dry fit · drawbore ⅛\" offset · oak peg ⅜\"", 13, INK)

    # Light-screen gaps
    s.text(520, 560, "DETAIL 4 — TREE OF LIFE APERTURE (DOG SEAL)", 16, ACC, bold=True)
    s.rect(560, 620, 200, 40, fill=BELT, stroke=INK, sw=2)
    s.rect(560, 668, 200, 48, fill=CASS, stroke=INK, sw=1)
    s.rect(590, 678, 8, 28, fill=MUNTIN, stroke=INK, sw=0.6)
    s.rect(720, 678, 8, 28, fill=MUNTIN, stroke=INK, sw=0.6)
    s.rect(560, 724, 200, 40, fill=EARTH, stroke=INK, sw=2)
    s.text(520, 590, f'Q-001 {kv("pattern_gap_dog"):g}" dog grid. Upper lights {kv("pattern_gap"):g}". Water table is the crawl stop.', 13, INK)
    s.text(520, 612, "Do not through-mortise cassettes — three nuki keep the post continuous.", 13, INK)

    s.text(40, 820, "JOINT VOCABULARY USED", 14, ACC, bold=True)
    s.text(40, 848, "Nuki 貫 · Kusabi wedge · Hozo ほぞ (gate) · Kama-tsugi 鎌継ぎ (cap) · Ari-kake optional at corners", 13, INK)

    s.save()


def sheet_m4():
    s = Sheet("M-4", "Sit-on-grade ladder base", "No digging · no cement · no stone pad · Buffalo")
    s.titleblock()
    s.text(40, 70, "SECTION — LOOKING ALONG RUN (driveway −Y / garden +Y)", 16, ACC, bold=True)

    S4 = 8.0
    ox, oy = 80, 430  # oy = sill top

    def sx(yin):
        return ox + 240 + yin * S4

    def sy(zin):
        return oy - zin * S4

    sh = P["sill_h"]
    st = P["sill_t"]
    spread = P["base_spread_cl"]
    pad_t = P["furniture_pad_t"]
    pack = P["pack_h"]
    drive_cy = -spread / 2.0
    garden_cy = spread / 2.0
    tie_half = P["tie_len"] / 2.0

    # driveway grade (run sits on slab)
    s.line(sx(-28), sy(-sh - pad_t), sx(28), sy(-sh - pad_t), 2, "#5a5854")
    s.text(sx(-26), sy(-sh - pad_t) + 18, "DRIVEWAY SLAB (EXISTING)", 11, DIM)

    # rubber pads under driveway sill
    s.rect(sx(drive_cy - st / 2), sy(-sh), st * S4, pad_t * S4, fill="#3d3530", stroke=INK, sw=1)
    s.text(sx(drive_cy), sy(-sh - pad_t) - 6, "H-001 PADS", 10, DIM, "middle")

    # cross-tie (behind sills, shown as long beam)
    s.rect(sx(-tie_half), sy(0), P["tie_len"] * S4, sh * S4, fill="#c5c8c2", stroke=INK, sw=2)
    s.text(sx(0), sy(-sh / 2) + 5, "F-003 CROSS-TIE", 12, INK, "middle", bold=True)

    # two sills on edge
    s.rect(sx(drive_cy - st / 2), sy(0), st * S4, sh * S4, fill=LIGHT, stroke=INK, sw=2)
    s.rect(sx(garden_cy - st / 2), sy(0), st * S4, sh * S4, fill=LIGHT, stroke=INK, sw=2)
    s.text(sx(drive_cy), sy(0) - 8, "F-001", 11, ACC, "middle", bold=True)
    s.text(sx(garden_cy), sy(0) - 8, "F-002", 11, ACC, "middle", bold=True)

    # tenon into tie
    s.rect(sx(-P["post_tenon_y"] / 2), sy(0), P["post_tenon_y"] * S4, P["post_tenon_h"] * S4,
           fill="#d9dcde", stroke=INK, sw=2)
    # post above
    s.rect(sx(-P["post_y"] / 2), sy(36), P["post_y"] * S4, 36 * S4, fill="#d9dcde", stroke=INK, sw=2)
    s.text(sx(0), sy(28), "POST", 12, ACC, "middle", bold=True)

    # live planter on garden side (not at house)
    s.rect(sx(garden_cy + st / 2 + 1), sy(P["planter_h"]), P["planter_y"] * S4 * 0.55, P["planter_h"] * S4,
           fill="#8a9094", stroke=INK, sw=1.5)
    s.text(sx(garden_cy + 10), sy(P["planter_h"] / 2), "F-005 PLANTER", 10, INK, "middle")
    s.text(sx(garden_cy + 10), sy(P["planter_h"] / 2) + 14, "LIVE + STONE IN-BOX", 9, DIM, "middle")

    s.dim_v(sy(0), sy(-P["post_tenon_h"]), sx(P["post_y"] / 2), '3.5" TENON', offset=36)
    s.dim_h(sx(-tie_half), sx(tie_half), sy(-sh - pack) + 40, f'{P["tie_len"]:g}" TIE', offset=8)
    s.dim_h(sx(drive_cy), sx(garden_cy), sy(0), f'{spread:g}" SILL CL', offset=-28)

    # plan of ladder
    s.text(780, 70, "LADDER PLAN", 16, ACC, bold=True)
    px0, py0 = 800, 160
    scale = 4.0
    oh = P["sill_overhang"]
    s.rect(px0, py0, LY["sill_len"] * scale, P["base_width"] * scale, fill="none", stroke=DIM, sw=1, dash="4 3")
    # two sills
    s.rect(px0, py0, LY["sill_len"] * scale, P["sill_t"] * scale, fill=LIGHT, stroke=INK, sw=1.5)
    s.rect(px0, py0 + (P["base_width"] - P["sill_t"]) * scale, LY["sill_len"] * scale, P["sill_t"] * scale,
           fill=LIGHT, stroke=INK, sw=1.5)
    for i, cx in enumerate(POSTS):
        tx = px0 + (oh + cx - fx / 2) * scale
        s.rect(tx, py0 - 1, fx * scale, P["tie_len"] * scale * 0.95, fill="#c5c8c2", stroke=INK, sw=1.2)
        s.rect(tx, py0 + (P["base_width"] / 2 - P["post_y"] / 2) * scale,
               fx * scale, P["post_y"] * scale, fill="#d9dcde", stroke=INK, sw=1.5)
        s.text(px0 + (oh + cx) * scale, py0 - 14, f"P{i}", 12, ACC, "middle", bold=True)
    s.text(px0, py0 + P["base_width"] * scale + 28,
           f'SILLS {LY["sill_len"]:.0f}" × 4×6  ·  BASE {P["base_width"]:g}" WIDE  ·  DROP {P["drop_off"]:g}" (0 = slab)',
           13, INK)

    s.text(780, 420, "WINTER REMOVAL SEQUENCE", 16, ACC, bold=True)
    steps = [
        "1. Open gate · remove oak latch peg / padlock.",
        "2. Knock out rail wedges (kusabi) — save in labeled bag.",
        "3. Slide nuki bands out of posts (two-person).",
        "4. Withdraw light cassettes toward P3.",
        "5. Lift gate leaf off oak pivots (W-003).",
        "6. Lift each post straight up out of F-003.",
        "7. Empty planters (or lift troughs); store dry. Lift ladder or leave sills.",
        "8. Nothing is poured. Nothing is buried. No post holes. No pad.",
    ]
    for i, t in enumerate(steps):
        s.text(780, 455 + i * 24, t, 13, INK)

    s.text(40, 780, "NOTES", 14, ACC, bold=True)
    s.text(40, 808, "• Entirely freestanding furniture fence. NO post holes. NO cement. NO gravel or stone pads.", 13, INK)
    s.text(40, 832, "• Run sits on the driveway slab (photos). F-004 packing only if outriggers leave the slab.", 13, INK)
    s.text(40, 856, "• H-001 rubber furniture pads under F-001 protect the driveway — no fasteners into pavement.", 13, INK)
    s.text(40, 880, "• Wind ballast: two live planters (P1–P2, P2–P3). Optional stone IN the boxes. Not a pad.", 13, INK)
    s.text(40, 904, "• Latch B default (mortise in P0). Gate against the house. Do not epoxy. No planter at P0.", 13, INK)

    s.save()


def sheet_m5():
    s = Sheet("M-5", "Gate & latch", "Tree of Life portal · oak pivots · Latch B into P0 · against the house")
    s.titleblock()
    s.text(40, 70, "GATE LEAF — DARWIN MARTIN TREE OF LIFE · FLUSH TO THE HOUSE (NO PLANTER AT P0)", 15, ACC, bold=True)

    S5 = 11
    ox, oy = 90, 900

    def x(vin):
        return ox + vin * S5

    def y(vin):
        return oy - vin * S5

    gw = LY["gate_leaf_w"]
    gh = LY["gate_h"]
    stile = 3.5
    s.rect(x(0), y(gh), gw * S5, gh * S5, fill="#e4e0d6", stroke=INK, sw=2)
    s.rect(x(0), y(gh), stile * S5, gh * S5, fill=PIER, stroke=INK)
    s.rect(x(gw - stile), y(gh), stile * S5, gh * S5, fill=PIER, stroke=INK)

    # cassette fields + motifs (gate bay) — world x already in motif
    gx0 = kv("post_x") + kv("gate_gap")

    def Xx(xin):
        return x(xin - gx0)

    for m in LY["motifs"]:
        if m.get("bay") == "gate":
            s.rect(Xx(m["x0"]), y(m["z0"] + m["h"]), m["w"] * S5, m["h"] * S5, fill=CASS, stroke="none", sw=0)
            paint_motif(s, m, Xx, y, S5)

    # projecting belts across the leaf (align to screen)
    for sl in LY["slats"]:
        if sl["id"].startswith("R-"):
            s.rect(x(stile), y(sl["z1"]), (gw - 2 * stile) * S5, sl["h"] * S5, fill=BELT, stroke=INK, sw=1.0)
        elif sl["id"] == "K-001":
            s.rect(x(stile), y(min(sl["z1"], gh)), (gw - 2 * stile) * S5, min(sl["h"], gh) * S5, fill=EARTH, stroke=INK, sw=1.0)

    s.dim_h(x(0), x(gw), y(0), f'{gw:.1f}" LEAF WIDTH', offset=40)
    s.dim_v(y(0), y(gh), x(gw), f'{gh:.1f}"', offset=36)
    s.text(x(gw / 2), y(3.2), "TREE OF LIFE", 11, PAPER, "middle", bold=True)

    s.text(620, 70, "HARDWARE (WOOD-FIRST)", 16, ACC, bold=True)
    lines = [
        "FACE: Tree of Life (middle light) + nested squares. Not a Z-brace ranch gate.",
        "  Shop brace G-008 lives on the driveway face — not the garden elevation.",
        "HINGE: 1.25\" oak pivots W-003 (structurally best on a freestanding P1).",
        "  — Bottom socket in the sill/threshold at P1; top in the cap soffit.",
        "  — Leaf weight in compression to the driveway — not a cantilever pintle.",
        "  — Gate lifts straight up (+Z) for winter. Optional stainless pintle is backup only.",
        "LATCH B — DEFAULT (fully freestanding, against the house):",
        "  — 1.5\" × 3.5\" × 18\" sliding oak bar through latch stile.",
        "  — Bar enters mortise in P0 latch post; gravity catch. CL on R-002 belt.",
        "  — Cross-peg + optional keyed padlock hasp on bar.",
        "  — NO epoxy, NO house receiver, NO planter at P0.",
        "SWING: Into garden (confirm site). Clear arc 36\".",
        "JOINERY: Drawbored mortise & tenon at every stile/rail (hozo).",
        f"DOG: Solid water-table rail + {kv('pattern_gap_dog'):g}″ Q-001 grid + 0.375″ bottom clear.",
    ]
    for i, t in enumerate(lines):
        s.text(620, 100 + i * 22, t, 13, INK)

    s.text(40, 980, "Garden face is Wright. Shop brace is hidden. Bottom clear 0.375\" (dog). Top clear 0.50\" under the eave.", 13, DIM)

    s.save()


def sheet_m6():
    s = Sheet("M-6", "Cut list & board feet", "Buy list for one hardware-store run · Buffalo")
    s.titleblock()
    s.text(40, 70, "LUMBER BUY LIST — DIMENSIONAL STOCK (paint-grade OK)", 16, ACC, bold=True)

    fam_meta = {
        "4x6x8": ("4×6", "8'", "Posts + cross-ties nested"),
        "4x6x16": ("4×6", "16'", "Dodai sills F-001 / F-002"),
        "2x4x10": ("2×4", "10'", "Prairie ribbons R-001 / R-002"),
        "2x12x10": ("2×12 PT", "10'", "Water table K-001"),
        "2x12x12": ("2×12", "12'", "Eave C-001 + stub C-002"),
        "1x4x8": ("1×4", "8'", "Tree of Life / nested-rect muntins + Q-010 stock"),
        "1x4x12": ("1×4", "12'", "Eave fascia C-003"),
        "2x6x8": ("2×6", "8'", "Gate stiles + planters + braces"),
        "2x2x8": ("2×2", "8'", "Roman-brick T-001 pier wrap"),
        "2x4x8": ("2×4", "8'", "Kusabi + gate ribbon rails G-003..005"),
        "oak_1x4x4": ("1×4 oak", "4'", "Pegs / latch / oak pivots"),
    }
    bf_by = {}
    for b in NEST["boards"]:
        bf_by[b["PURCHASE"]] = bf_by.get(b["PURCHASE"], 0) + b["BF"]
    rows = [("Qty", "Nominal", "Length", "Use", "Board feet")]
    fams = ("4x6x8", "4x6x16", "2x4x10", "2x12x10", "2x12x12", "1x4x8", "1x4x12", "2x6x8", "2x2x8", "2x4x8", "oak_1x4x4")
    for fam in fams:
        nom, length, use = fam_meta[fam]
        rows.append((str(NEST["buy_counts"].get(fam, 0)), nom, length, use, f"{bf_by.get(fam, 0):.1f}"))
    yy = 110
    cols = [40, 120, 250, 360, 1180]
    for r in rows:
        for i, cell in enumerate(r):
            s.text(cols[i], yy, cell, 14, DIM if r[0] == "Qty" else INK, bold=(r[0] == "Qty" or i == 0))
        yy += 30
        s.line(40, yy - 20, 1400, yy - 20, 0.7, LIGHT)

    s.text(
        40,
        yy + 10,
        f"NET {NEST['net_bf']:.0f} bf  ·  waste {NEST['waste_factor']:.0%}  ·  PROCUREMENT {NEST['procurement_bf']:.0f} bf  ·  counts from kernel nest (not a hand list)",
        14,
        ACC,
        bold=True,
    )

    s.text(40, yy + 55, "NON-TIMBER", 16, ACC, bold=True)
    misc = [
        "Rubber furniture pads: 8 pcs under driveway sill (protect pavement)",
        "Live planter mix + optional pea gravel IN two F-005 troughs (drainage + mass — not a pad)",
        "12V IP65 LED tape + driver (cap soffit). Driver in P3 planter niche — not at the house.",
        "Optional: stainless pintle backup, keyed padlock hasp. Allowed metal: lighting + latch.",
        "NO concrete. NO gravel bed. NO post-hole digger. NO epoxy into the house. NO planter at the gate.",
    ]
    for i, t in enumerate(misc):
        s.text(40, yy + 85 + i * 24, "•  " + t, 13, INK)

    s.text(40, 980, "CUT ORDER: sills/ties → posts → nuki + cassette grooves → belts/water table → Tree of Life cassettes → eave scarf → gate → paint → set → plant.", 13, DIM)
    s.save()


if __name__ == "__main__":
    sheet_m1()
    sheet_m2()
    sheet_m3()
    sheet_m4()
    sheet_m5()
    sheet_m6()
    from martin_elevation import write_hero_svg
    write_hero_svg(os.path.join(OUT, "hero_elevation.svg"), LY, kv, dark=False)
    write_hero_svg(os.path.join(ROOT, "fence", "martin", "renders", "hero_elevation.svg"), LY, kv, dark=True)
    print("MARTIN plans done →", OUT)
