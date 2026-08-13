#!/usr/bin/env python3
"""Generate MARTIN build-plan SVG sheets (A3 landscape, printable).

Dimensions mirror fence/martin/cad/martin_fence.py.
Run:  python3 scripts/gen_martin_plans.py
"""

from __future__ import annotations

import os
import sys

OUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "fence", "martin", "plans"
)
os.makedirs(OUT, exist_ok=True)

IN = 25.4

# ---- parameters from fabrication SSOT (do not duplicate) --------------------
_FAB = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "fence", "martin", "fab"
)
sys.path.insert(0, _FAB)
from martin_ssot import PARAMS, PROJECT, layout as ssot_layout, pv  # noqa: E402

LY = ssot_layout()
P = dict(
    length=pv("overall_length"),
    height=pv("overall_height"),
    post_x=pv("post_x"),
    post_y=pv("post_y"),
    post_tenon_x=pv("post_tenon_x"),
    post_tenon_y=pv("post_tenon_y"),
    post_tenon_h=pv("post_tenon_h"),
    gate_clear=pv("gate_clear"),
    gate_gap=pv("gate_gap"),
    rail_t=pv("rail_t"),
    rail_h=pv("rail_h"),
    rail_z_cl=tuple(PARAMS["rail_z_cl"]["value"]),
    cap_t=pv("cap_t"),
    cap_w=pv("cap_w"),
    board_t=pv("board_t"),
    board_w=pv("board_w"),
    board_gap=pv("board_gap"),
    pad_overhang=pv("pad_overhang"),
    pad_width=pv("pad_width"),
    pad_thick=pv("pad_thick"),
    drop_off=pv("drop_off"),
    pier_xy=pv("pier_xy"),
    pier_h=pv("pier_h"),
    gravel_h=pv("gravel_h"),
    latch_bar=pv("latch_bar_x"),
)

fx = P["post_x"]
L = P["length"]
gate = P["gate_clear"]
P0, P1, P2, P3 = LY["post_centers"]
bay_clear = LY["bay_clear"]
POSTS = LY["post_centers"]
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
        self.text(W - 40, Hpx - 34, f"Removable · No nails in timber · Rev {PROJECT['REVISION']}", 13, DIM, "end")

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
            "M-7": "M7_shop.svg",
            "M-8": "M8_mill.svg",
            "G-000": "G000_cover.svg",
            "S-402": "S402_cutlist.svg",
            "QA-700": "QA700_inspection.svg",
            "P-301": "P301_post.svg",
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
OX, OY = 80, 820  # origin at pad top, left outer face


def X(xin):
    return OX + xin * S


def Y(zin):
    """z up from pad; SVG y down."""
    return OY - zin * S


def sheet_m1():
    s = Sheet("M-1", "General arrangement", "Scale 1:16 approx · dimensions in inches")
    s.titleblock()
    s.text(40, 70, "FRONT ELEVATION — garden face", 16, ACC, bold=True)
    s.text(40, 94, "143\" overall · 65\" high · 36\" gate · four 4×6 posts · three 2×8 Prairie bands", 14, DIM)

    # pad
    s.rect(X(-P["pad_overhang"]), Y(0), (L + 2 * P["pad_overhang"]) * S, P["pad_thick"] * S,
           fill=LIGHT, stroke=INK, sw=1.5)
    s.text(X(L / 2), Y(-P["pad_thick"] / 2) + 5, "LEVELING PAD", 12, DIM, "middle")

    # posts
    for i, cx in enumerate(POSTS):
        s.rect(X(cx - fx / 2), Y(H - P["cap_t"]), fx * S, (H - P["cap_t"]) * S,
               fill="#d9dcde", stroke=INK, sw=1.8)
        s.text(X(cx), Y(H) - 18, f"P{i}", 14, ACC, "middle", bold=True)

    # rails privacy
    for zc in P["rail_z_cl"]:
        s.rect(X(P1 - fx / 2 - 0.5), Y(zc + P["rail_h"] / 2),
               (P3 - P1 + fx + 1) * S, P["rail_h"] * S, fill=GRAY, stroke=INK, sw=1.2)

    # cap
    s.rect(X(P1 - fx / 2 - 0.75), Y(H), (P3 - P1 + fx + 1.5) * S, P["cap_t"] * S,
           fill="#8a9094", stroke=INK, sw=1.2)
    s.rect(X(P0 - fx / 2 - 0.5), Y(H), (fx + 1) * S, P["cap_t"] * S,
           fill="#8a9094", stroke=INK, sw=1.2)

    # gate leaf outline
    s.rect(X(fx + 0.5), Y(H - 0.5), (gate - 1) * S, (H - 1.5) * S,
           fill="#e8eaeb", stroke=ACC, sw=2, dash="6 4")
    s.text(X(fx + gate / 2), Y(H / 2), "GATE", 16, ACC, "middle", bold=True)
    s.text(X(fx + gate / 2), Y(H / 2) + 22, '36" CLEAR', 12, DIM, "middle")

    # boards hint
    for bay in ((P1 + fx / 2, P2 - fx / 2), (P2 + fx / 2, P3 - fx / 2)):
        x0, x1 = bay
        n = 6
        pitch = (x1 - x0) / n
        for i in range(n):
            s.rect(X(x0 + i * pitch + 0.15), Y(P["rail_z_cl"][0] - P["rail_h"] / 2 - 0.2),
                   (pitch - 0.35) * S,
                   (P["rail_z_cl"][0] - P["rail_h"] / 2 - 1.5) * S,
                   fill="#cfd3d5", stroke=LIGHT, sw=0.8)

    # dimensions
    s.dim_h(X(0), X(L), Y(0), '143" OVERALL', offset=48)
    s.dim_h(X(fx), X(fx + gate), Y(0), '36" GATE', offset=78)
    s.dim_h(X(P1 + fx / 2), X(P2 - fx / 2), Y(H), f'{bay_clear:.2f}" BAY', offset=-36)
    s.dim_h(X(P2 + fx / 2), X(P3 - fx / 2), Y(H), f'{bay_clear:.2f}" BAY', offset=-36)
    s.dim_v(Y(0), Y(H), X(L), '65"', offset=40)

    # plan mini
    s.text(40, 980, "PLAN (pad top)", 14, ACC, bold=True)
    py = 1040
    ps = 4.5
    for cx in POSTS:
        s.rect(80 + cx * ps - fx * ps / 2, py - P["post_y"] * ps / 2,
               fx * ps, P["post_y"] * ps, fill="#d9dcde", stroke=INK, sw=1.2)
    s.rect(80 - P["pad_overhang"] * ps, py - P["pad_width"] * ps / 2,
           (L + 2 * P["pad_overhang"]) * ps, P["pad_width"] * ps,
           fill="none", stroke=DIM, sw=1, dash="4 3")
    s.text(80 + L * ps / 2, py + P["pad_width"] * ps / 2 + 22,
           'PAD 28" WIDE · SOCKET PIERS AT POSTS', 12, DIM, "middle")

    # notes
    notes = [
        "DESIGN: Prairie horizontals (Darwin Martin / FLW) + Japanese nuki / hozo / kama-tsugi.",
        "STOCK: Select DF mill billets (6×6 / 2×12 / 1×12) — owner re-dimensions for VG / low warp.",
        "JOINERY: 100% Japanese wood joinery. No nails or screws in timber. Drawbored / wedged only.",
        "WINTER: Knock wedges → withdraw nuki rails → lift gate off pintles → lift posts → tip piers.",
        "FINISH: Exterior primer + owner gray. Mask wedge faces, tenons, and sleeve contact.",
        "ENGINEERING NOTE: Planning design — have a NY PE review foundations if required by permit.",
    ]
    for i, n in enumerate(notes):
        s.text(780, 70 + i * 22, n, 12, INK)

    s.save()


def sheet_m2():
    s = Sheet("M-2", "Elevation & rail schedule", "Scale ~1:12 · rail centerlines AFF")
    s.titleblock()
    s.text(40, 70, "PRIVACY BAY ELEVATION — typical", 16, ACC, bold=True)

    # larger scale detail of one bay + post
    S2 = 12.0
    ox, oy = 120, 880

    def x(v):
        return ox + v * S2

    def y(v):
        return oy - v * S2

    bay = bay_clear
    # posts left/right
    s.rect(x(0), y(H - P["cap_t"]), fx * S2, (H - P["cap_t"]) * S2, fill="#d9dcde", stroke=INK)
    s.rect(x(fx + bay), y(H - P["cap_t"]), fx * S2, (H - P["cap_t"]) * S2, fill="#d9dcde", stroke=INK)
    # rails
    for zc in P["rail_z_cl"]:
        s.rect(x(-0.5), y(zc + P["rail_h"] / 2),
               (fx + bay + fx + 1) * S2, P["rail_h"] * S2, fill=GRAY, stroke=INK)
        s.text(x(fx + bay / 2), y(zc) + 5, f'2×8 NUKI  CL {zc:g}"', 13, PAPER, "middle", bold=True)
    # cap
    s.rect(x(-0.75), y(H), (fx + bay + fx + 1.5) * S2, P["cap_t"] * S2, fill="#8a9094", stroke=INK)
    # boards
    pitch = P["board_w"] + P["board_gap"]
    n = int((bay + P["board_gap"]) // pitch)
    used = n * P["board_w"] + (n - 1) * P["board_gap"]
    x0 = fx + (bay - used) / 2
    for i in range(n):
        s.rect(x(x0 + i * pitch), y(P["rail_z_cl"][0] - P["rail_h"] / 2 - 0.15),
               P["board_w"] * S2,
               (P["rail_z_cl"][0] - P["rail_h"] / 2 - 1.5) * S2,
               fill="#cfd3d5", stroke=INK, sw=1)

    s.dim_v(y(0), y(H), x(fx + bay + fx), '65"', offset=36)
    for zc in P["rail_z_cl"]:
        s.dim_v(y(0), y(zc), x(-0.5), f'{zc:g}" CL', offset=-50)
    s.dim_h(x(fx), x(fx + bay), y(0), f'{bay:.2f}" CLEAR', offset=40)
    s.dim_h(x(0), x(fx), y(H), '3.5"', offset=-28)

    # schedule table
    s.text(980, 70, "RAIL / BAND SCHEDULE", 16, ACC, bold=True)
    rows = [
        ("Mark", "Stock", "Orientation", "CL AFF", "Role"),
        ("R1", "2×8", "on edge", '10"', "Bottom Prairie band / splash rail"),
        ("R2", "2×8", "on edge", '28"', "Mid band / latch alignment"),
        ("R3", "2×8", "on edge", '46"', "Upper Prairie band"),
        ("CAP", "2×8", "flat", '65" top', "Continuous weather cap"),
        ("B", "1×6", "vertical", "between rails", "Privacy — floats in grooves"),
        ("POST", "4×6", "3.5×5.5", "full height", "Nuki posts + 12\" foot tenon"),
    ]
    yy = 110
    for r in rows:
        xx = 980
        for cell in r:
            s.text(xx, yy, cell, 13, INK if r[0] != "Mark" else DIM, bold=(r[0] == "Mark"))
            xx += 110
        yy += 28
        s.line(980, yy - 18, 1580, yy - 18, 0.6, LIGHT)

    s.text(980, 360, "JOINERY AT EACH RAIL", 16, ACC, bold=True)
    bullets = [
        "Nuki (貫): rail from 2×12 outer third through post mortise.",
        "Wedge (kusabi): white oak from cheek slot — reverse to release.",
        "Board grooves: ⅜\" deep plow — boards float, zero fasteners.",
        "Cap scarf (kama-tsugi) at P2, drawbored oak peg.",
        "Japanese joinery only — no nails/screws in timber.",
    ]
    for i, b in enumerate(bullets):
        s.text(980, 395 + i * 26, "•  " + b, 14, INK)

    s.save()


def sheet_m3():
    s = Sheet("M-3", "Joinery details", "Details @ 1:4 · cut from dimensional lumber")
    s.titleblock()

    # Nuki detail
    s.text(40, 70, "DETAIL 1 — NUKI THROUGH-RAIL (2×8 in 4×6)", 16, ACC, bold=True)
    sx, sy = 80, 420
    # post section
    s.rect(sx, sy - 120, 90, 240, fill="#d9dcde", stroke=INK, sw=2)  # post
    s.rect(sx - 80, sy - 40, 250, 50, fill=GRAY, stroke=INK, sw=2)  # rail
    s.poly([(sx + 70, sy - 10), (sx + 95, sy), (sx + 70, sy + 10)], fill=ACC, stroke=ACC)  # wedge
    s.text(sx + 45, sy + 150, "4×6 POST", 13, DIM, "middle")
    s.text(sx + 170, sy - 55, "2×8 RAIL", 13, DIM)
    s.text(sx + 110, sy + 5, "WEDGE", 12, ACC, bold=True)
    s.text(sx - 10, 70 + 40, 'Mortise: rail thickness (≈1.5") × (7.25" + 1/16" seasonal ease) through', 13, INK)
    s.text(sx - 10, 70 + 62, 'Cheeks ~1" each side · Zenwu walls + Temple flush trim; sliding fit, no side rattle', 13, INK)
    s.text(sx - 10, 70 + 84, 'Wedge: hardwood ⅝" × 1⅛" × 5.5" — tap to lock, reverse to release', 13, INK)

    # Foot tenon
    s.text(520, 70, "DETAIL 2 — FOOT TENON INTO SLEEVE", 16, ACC, bold=True)
    tx, ty = 560, 380
    s.rect(tx, ty - 160, 70, 160, fill="#d9dcde", stroke=INK, sw=2)
    s.rect(tx + 10, ty, 50, 130, fill="#d9dcde", stroke=INK, sw=2)
    s.rect(tx - 20, ty - 10, 110, 160, fill="none", stroke=DIM, sw=1.5, dash="5 3")
    s.rect(tx - 40, ty + 150, 150, 40, fill=LIGHT, stroke=INK)
    s.text(tx + 35, ty - 175, "POST", 13, DIM, "middle")
    s.text(tx + 35, ty + 70, "TENON", 12, ACC, "middle", bold=True)
    s.text(tx + 35, ty + 200, "PIER", 12, DIM, "middle")
    s.text(520, 100, 'Shouldered tenon 2.5" × 4.5" × 12" into sleeved pier', 13, INK)
    s.text(520, 122, "Shoulders: TS + Festool LS 36 · cheeks: #5 / Bridge City plane to sleeve", 13, INK)
    s.text(520, 144, "Sleeve = tenon + ¼\" clear (winter pull) · ⌀½\" drain at bottom", 13, INK)
    s.text(520, 166, "Cross-wedge optional through pier cheeks for storm lock", 13, INK)

    # Scarf
    s.text(40, 560, "DETAIL 3 — KAMA-TSUGI CAP SCARF AT P2", 16, ACC, bold=True)
    s.poly([(80, 720), (200, 720), (230, 700), (200, 680), (80, 680)], fill=GRAY, stroke=INK, sw=2)
    s.poly([(230, 700), (200, 680), (320, 680), (350, 700), (320, 720), (200, 720)],
           fill="#8a9094", stroke=INK, sw=2)
    s.line(215, 675, 215, 725, 2, ACC)
    s.text(215, 745, "OAK PEG (drawbore)", 12, ACC, "middle")
    s.text(40, 590, "Sickle scarf · Universal V2 protractor · shoot faces on Preda board", 13, INK)
    s.text(40, 612, "Dry fit · drawbore ⅛\" offset · oak peg ⅜\" · MFT stop for peg holes", 13, INK)

    # Board groove
    s.text(520, 560, "DETAIL 4 — FLOATING 1×6 IN RAIL GROOVES", 16, ACC, bold=True)
    s.rect(560, 650, 200, 40, fill=GRAY, stroke=INK, sw=2)
    s.rect(600, 620, 30, 100, fill="#cfd3d5", stroke=INK, sw=1.5)
    s.rect(640, 620, 30, 100, fill="#cfd3d5", stroke=INK, sw=1.5)
    s.rect(680, 620, 30, 100, fill="#cfd3d5", stroke=INK, sw=1.5)
    s.text(520, 590, '⅜" deep × ⅞" wide plow on table saw (LS 36 fence) · ¼" board gaps', 13, INK)
    s.text(520, 612, "Boards drop in from top before cap is set — zero fasteners", 13, INK)

    s.text(40, 820, "JOINT VOCABULARY USED", 14, ACC, bold=True)
    s.text(40, 848, "Nuki 貫 · Kusabi wedge · Hozo ほぞ (gate) · Kama-tsugi 鎌継ぎ (cap) · Ari-kake optional at corners", 13, INK)
    s.text(40, 876, "Shop method sheet M-7 maps every joint to the owner Festool / Bridge City / Zenwu kit.", 13, DIM)

    s.save()


def sheet_m4():
    s = Sheet("M-4", "Pad & socket piers", "Scale ~1:20 · Buffalo frost / removable winter system")
    s.titleblock()
    s.text(40, 70, "SECTION — LEVELING PAD + TIP-OUT SOCKET PIER", 16, ACC, bold=True)

    S4 = 9.0
    ox, oy = 200, 520

    def x(v):
        return ox + v * S4

    def y(v):
        return oy - v * S4

    # gravel
    s.rect(ox - 80, oy + (P["pad_thick"] + P["drop_off"]) * S4,
           420, P["gravel_h"] * S4, fill="#6a6864", stroke=INK)
    s.text(ox + 130, oy + (P["pad_thick"] + P["drop_off"] + P["gravel_h"] / 2) * S4 + 5,
           '6" COMPACTED #57 GRAVEL', 12, PAPER, "middle", bold=True)

    # makeup / drop
    s.rect(ox - 40, oy + P["pad_thick"] * S4, 360, P["drop_off"] * S4, fill="#9a9890", stroke=INK)
    s.text(ox + 140, oy + (P["pad_thick"] + P["drop_off"] / 2) * S4 + 5,
           f'DROP-OFF MAKEUP ({P["drop_off"]:g}") — FIELD VERIFY', 12, INK, "middle")

    # pad
    s.rect(ox - 60, oy, 400, P["pad_thick"] * S4, fill=LIGHT, stroke=INK, sw=2)
    s.text(ox + 140, oy + P["pad_thick"] * S4 / 2 + 5, '6" LEVELING PAD (TOP LEVEL)', 13, INK, "middle", bold=True)

    # pier
    s.rect(ox + 120, oy, 14 * S4, P["pier_h"] * S4, fill="#b8b6b0", stroke=INK, sw=2)
    # sleeve
    s.rect(ox + 120 + 3.5 * S4, oy, 5 * S4, 13 * S4, fill="none", stroke=ACC, sw=2, dash="4 3")
    # tenon
    s.rect(ox + 120 + 4 * S4, oy - 8 * S4, 4 * S4, 12 * S4, fill="#d9dcde", stroke=INK, sw=2)
    # post above
    s.rect(ox + 120 + 3 * S4, oy - 40 * S4, 5.5 * S4, 40 * S4, fill="#d9dcde", stroke=INK, sw=2)

    s.dim_v(oy, oy + P["pier_h"] * S4, ox + 120 + 14 * S4, '18" PIER', offset=28)
    s.dim_v(oy - 12 * S4, oy, ox + 100, '12" TENON', offset=-30)
    s.dim_h(ox + 120, ox + 120 + 14 * S4, oy + P["pier_h"] * S4, '14" SQ', offset=36)

    # plan of pad
    s.text(780, 70, "PAD PLAN", 16, ACC, bold=True)
    px0, py0 = 800, 200
    # simplify: draw proportional
    scale = 4.2
    s.rect(px0, py0, (L + 12) * scale, P["pad_width"] * scale, fill=LIGHT, stroke=INK, sw=2)
    for i, cx in enumerate(POSTS):
        s.rect(px0 + (6 + cx - 7) * scale, py0 + (P["pad_width"] - P["pier_xy"]) / 2 * scale,
               P["pier_xy"] * scale, P["pier_xy"] * scale, fill="#b8b6b0", stroke=INK, sw=1.5)
        s.text(px0 + (6 + cx) * scale, py0 - 12, f"P{i}", 12, ACC, "middle", bold=True)
    s.text(px0, py0 + P["pad_width"] * scale + 30,
           f'PAD: {L + 2*P["pad_overhang"]:.0f}" × {P["pad_width"]:g}" × {P["pad_thick"]:g}" (+ {P["drop_off"]:g}" makeup)',
           13, INK)

    s.text(780, 420, "WINTER REMOVAL SEQUENCE", 16, ACC, bold=True)
    steps = [
        "1. Open gate · remove oak latch peg / padlock.",
        "2. Knock out rail wedges (kusabi) — save in labeled bag.",
        "3. Slide nuki rails out of posts (two-person).",
        "4. Lift vertical boards out of grooves; bundle flat.",
        "5. Lift gate leaf off wooden pintles.",
        "6. Lift each post straight up out of sleeve.",
        "7. Tip socket piers onto dolly; store dry.",
        "8. Leave leveling pad in place (or cover); mark sleeve holes.",
    ]
    for i, t in enumerate(steps):
        s.text(780, 455 + i * 24, t, 13, INK)

    s.text(40, 900, "NOTES", 14, ACC, bold=True)
    s.text(40, 928, "• Field-measure driveway→garden drop; adjust makeup thickness. Default shown: 5\".", 13, INK)
    s.text(40, 952, "• Sleeve: Schedule 40 PVC or galv. tube sized to 2.5\"×4.5\" tenon + ¼\" clearance; drill ⌀½\" drain at bottom.", 13, INK)
    s.text(40, 976, "• Concrete: 4000 psi air-entrained. Piers may be precast for true tip-out removal.", 13, INK)
    s.text(40, 1000, "• For permanent frost piers instead: extend stems to 48\" bearing — see STELE report method.", 13, INK)

    s.save()


def sheet_m5():
    s = Sheet("M-5", "Gate & latch", "Gate leaf · wooden pintles · house or post latch")
    s.titleblock()
    s.text(40, 70, "GATE LEAF — 36\" CLEAR OPENING", 16, ACC, bold=True)

    S5 = 11
    ox, oy = 100, 860

    def x(v):
        return ox + v * S5

    def y(v):
        return oy - v * S5

    gw = gate - 1.0
    gh = H - 2.0
    s.rect(x(0), y(gh), gw * S5, gh * S5, fill="#e8eaeb", stroke=INK, sw=2)
    # stiles
    s.rect(x(0), y(gh), 3.5 * S5, gh * S5, fill="#d9dcde", stroke=INK)
    s.rect(x(gw - 3.5), y(gh), 3.5 * S5, gh * S5, fill="#d9dcde", stroke=INK)
    for zc in P["rail_z_cl"]:
        s.rect(x(3.5), y(zc + 2.75), (gw - 7) * S5, 5.5 * S5, fill=GRAY, stroke=INK)
    # brace
    s.line(x(3.5), y(8), x(gw - 3.5), y(gh - 8), 6, ACC)
    s.dim_h(x(0), x(gw), y(0), f'{gw:.1f}" LEAF WIDTH', offset=40)
    s.dim_v(y(0), y(gh), x(gw), f'{gh:.1f}"', offset=36)

    s.text(620, 70, "HARDWARE (WOOD-FIRST)", 16, ACC, bold=True)
    lines = [
        "HINGE: Wooden pintle + gudgeon (hard maple / white oak).",
        "  — Two pintles on P1; gate lifts straight up to remove.",
        "  — Optional upgrade: stainless pintle set (only metal on fence).",
        "LATCH A — HOUSE RECEIVER (preferred if wall available):",
        "  — 1.5\" × 3.5\" × 18\" sliding oak bar through latch stile.",
        "  — Bar enters 4\" deep hardwood sleeve epoxied into house",
        "    concrete (or lag-bolted receiver block on foundation).",
        "  — Cross-peg + optional keyed padlock hasp on bar.",
        "LATCH B — SELF-CONTAINED:",
        "  — Same bar into mortise in P0 latch post; gravity catch.",
        "SWING: Into garden (or driveway — confirm site). Clear arc 36\".",
        "JOINERY: Drawbored mortise & tenon at every stile/rail (hozo).",
        "  — Bridge City tenon + kerf tools · Temple rip/crosscut · Zenwu cleanup.",
        "  — Drawbore ⅛\" offset; brad-point from MFT dog/stop · ⅜\" oak peg.",
        "  Diagonal brace half-lapped into rails — no fasteners.",
        "  — Protractor sets brace angle; shoot half-lap faces on Preda board.",
    ]
    for i, t in enumerate(lines):
        s.text(620, 100 + i * 22, t, 13, INK)

    s.text(40, 980, "PRIVACY: Gate boards match fence 1×6 language; rails align with Prairie bands R1–R3.", 13, DIM)

    s.save()


def sheet_m6():
    s = Sheet("M-6", "Mill BOM & finished cuts", "Select DF + white oak · owner re-dimensions · Buffalo")
    s.titleblock()
    s.text(40, 70, "A — MILL BUY LIST (oversized select stock — reject pith / twist / crook)", 16, ACC, bold=True)

    rows = [
        ("Qty", "Nominal", "Length", "Grade / species", "Primary yield", "BF"),
        ("4", "6×6", "8'", "DF Select / #1", "Posts → mill 3½×5½×75.5\" fin. (rough 77\")", "96.0"),
        ("5", "2×12", "12'", "DF Select / #1", "Nuki R1–R3 + cap + gate frame", "120.0"),
        ("2", "2×12", "10'", "DF Select / #1", "Gate / brace / spare rail cheeks", "40.0"),
        ("6", "1×12", "10'", "DF Select / VG-ish", "Privacy + gate boards → ¾×5½", "60.0"),
        ("1", "8/4×6\"", "6'", "White oak", "Kusabi, pegs, pintles, latch bar", "6.0"),
    ]
    yy = 100
    cols = [40, 100, 200, 300, 620, 1280]
    for r in rows:
        for i, cell in enumerate(r):
            s.text(cols[i], yy, cell, 13, DIM if r[0] == "Qty" else INK, bold=(r[0] == "Qty" or i == 0))
        yy += 26
        s.line(40, yy - 18, 1400, yy - 18, 0.6, LIGHT)

    s.text(40, yy + 6, "BUY TOTAL ≈ 322 bf  ·  Mill waste ~20–25% expected  ·  Finished timber still paints owner gray", 14, ACC, bold=True)
    s.text(40, yy + 28, "Why 2×12 / 6×6: outer thirds give straighter grain; pith stays in waste; you control final thickness / faces.", 13, DIM)

    s.text(40, yy + 58, "B — FINISHED PARTS (after re-dimension · Japanese joinery stock)", 16, ACC, bold=True)
    finished = [
        ("4", "Posts P0–P3", '3½×5½×75.5"', "Foot tenon 2½×4½×12\" · D-001 derived length"),
        ("3", "Nuki rails R1–R3", '1½×7¼×~105"', "Through P1–P3 · plow ⅜×⅞ grooves"),
        ("2", "Cap (scarf pair)", '1½×7¼×~53" ea', "Kama-tsugi at P2 · + latch stub at P0"),
        ("2", "Gate stiles", '1½×3½×~62"', "Hozo mortises · wooden pintle gudgeons"),
        ("5", "Gate rails / brace", '1½×3½–5½×~29"', "Drawbored M&T · half-lap brace"),
        ("~40", "Privacy/gate boards", '¾×5½× course', "Float in grooves · ¼\" gaps · no fasteners"),
        ("12+", "Kusabi wedges", '⅝×1⅛×5½"', "White oak · one per nuki cheek seat"),
        ("8+", "Drawbore pegs", '⌀⅜×~3"', "White oak · gate + cap scarf"),
        ("2", "Pintles + latch bar", "oak as fit", "Lift-off hinges · sliding bar Latch A/B"),
    ]
    yy2 = yy + 88
    s.text(40, yy2, "Qty", 12, DIM, bold=True)
    s.text(100, yy2, "Part", 12, DIM, bold=True)
    s.text(360, yy2, "Finished size", 12, DIM, bold=True)
    s.text(620, yy2, "Joinery note", 12, DIM, bold=True)
    yy2 += 22
    for r in finished:
        s.text(40, yy2, r[0], 12, INK, bold=True)
        s.text(100, yy2, r[1], 12, INK)
        s.text(360, yy2, r[2], 12, INK)
        s.text(620, yy2, r[3], 12, INK)
        yy2 += 20

    s.text(40, 900, "NON-TIMBER", 14, ACC, bold=True)
    misc = [
        "Concrete 4000 psi AE ~0.35 yd³ · #57 stone ~0.4 yd³ · 4 drained sleeves (tenon + ¼\" clear)",
        "Primer + owner gray ×2 · end-grain sealer · epoxy for Latch A house sleeve only",
        "Optional stainless pintles/hasp — only allowed metal; timber frame stays nail-free",
    ]
    for i, t in enumerate(misc):
        s.text(40, 926 + i * 20, "•  " + t, 12, INK)

    s.text(40, 1000, "See M-8 for grain selection / sticker schedule / 2×12 yield map. See M-7 for tool stations.", 13, DIM)
    s.save()


def sheet_m7():
    s = Sheet("M-7", "Shop method — owner tooling", "Mill → Japanese joinery · Festool + Bridge City kit")
    s.titleblock()

    s.text(40, 70, "OWNER KIT (THIS BUILD)", 16, ACC, bold=True)
    kit_l = [
        "Festool track saw + MFT (Hongdui dogs / track hinge) — breakdown, stops, story work",
        "Table saw + Festool TS LS 36 + Woodpeckers Fence Guide V2 — rip / shoulder / plow",
        "Miter / Ryobi rough crosscut · Temple rip + crosscut + flush trim · Zenwu Y2 + Ti hammer",
        "Stanley #5 + Bridge City plane + Preda LW bench / shooting board — true faces & fit",
        "Bridge City Universal V2 protractor · tenon tool · both kerf tools · Multi-Tool M1",
        "Incra 12″ · Kuratoga · drill/impact · Taylor countersink (peg mouths only — not fasteners)",
    ]
    for i, t in enumerate(kit_l):
        s.text(40, 96 + i * 20, "•  " + t, 13, INK)

    s.text(40, 230, "TOLERANCES (HOLD THESE)", 16, ACC, bold=True)
    tol = [
        ("Layout", "1/64″ on joinery faces. Story-stick mortise CL at 10 / 28 / 46″."),
        ("Nuki width", "Mortise = measured rail thickness. Sliding fit — plane cheeks; no side rattle."),
        ("Nuki height", "7.25″ + 1/16″ seasonal ease only. Parallel Zenwu walls."),
        ("Foot tenon", "2.5×4.5×12. Shoulders ±1/32″. Sleeve +¼″ clear for winter pull."),
        ("Board plow", "⅜″ deep × ⅞″ wide on TS (LS 36). ~⅛″ total float on ¾″ boards."),
        ("Drawbore", "⅛″ offset · ⌀⅜″ oak peg from MFT stop. No metal fasteners in frame."),
        ("Moisture", "Mill final faces after sticker MC stabilizes (shop-dry). Reject moving sticks."),
        ("Plumb", "Posts ≤⅛″ over 65″. Cap scarf shoot-fit before peg."),
    ]
    yy = 256
    for label, body in tol:
        s.text(40, yy, label.upper(), 12, ACC, bold=True)
        s.text(170, yy, body, 12, INK)
        yy += 20

    s.text(40, 430, "STATION SEQUENCE (END-TO-END)", 16, ACC, bold=True)
    seq = [
        "0. SELECT / STICKER — Buy M-6 stock. Mark pith side. Sticker 14+ days (see M-8) while pad cures.",
        "1. LAYOUT — M1 + Incra + Kuratoga. Story-stick rail CL; dog work on MFT.",
        "2. RE-DIMENSION — TS + LS 36: 6×6→3½×5½ posts; 2×12→1½×7¼ rails/cap; 1×12→¾×5½ boards (VG edges).",
        "3. FOOT TENONS — Shoulder 2½×4½×12. Plane cheeks; dry-fit every sleeve.",
        "4. NUKI MORTISES — Bore waste; Zenwu + Ti hammer; Temple/flush trim exits; kerf-tool kusabi slots.",
        "5. RAIL GROOVES — Plow ⅜×⅞ one locked TS setup for all R1–R3. No router. No nails.",
        "6. DRY ASSEMBLE — Rails through P1–P3; drop boards; wedges snug. Cap kama-tsugi (protractor + Preda).",
        "7. GATE — Bridge City tenon tooling; half-lap brace; drawbore pegs; wooden pintles only.",
        "8. FINISH / SET — Paint (mask locks). Drop posts; re-wedge; hang gate. Zero nails in timber.",
    ]
    for i, t in enumerate(seq):
        s.text(40, 456 + i * 22, t, 13, INK)

    s.text(40, 670, "JAPANESE JOINERY ONLY — FASTENER BAN", 16, ACC, bold=True)
    bans = [
        "Allowed in timber: nuki + kusabi · hozo + drawbore peg · kama-tsugi peg · foot tenon · floating grooves · half-lap brace.",
        "Forbidden in timber: nails, screws, plates, biscuits, pocket screws, construction adhesive on locking faces.",
        "Metal allowed only as optional stainless pintles / padlock hasp — never as structural frame fasteners.",
        "Boards float and drain; wedges reverse for winter knock-down — that is the fastening system.",
    ]
    for i, t in enumerate(bans):
        s.text(40, 698 + i * 22, "•  " + t, 13, INK)

    s.text(40, 800, "QUALITY GATES (DO NOT SKIP)", 16, ACC, bold=True)
    gates = [
        "A. Stock rejected if pith in finished section, ring shake, or twist >1/8″ in 8′ after sticker period.",
        "B. Every foot tenon drops/lifts free in its sleeve — no twist bind.",
        "C. All three nuki slide a post dry before final wedge fit.",
        "D. Cap scarf closes to light from shooting board; peg after paint plan is set.",
        "E. Gate hangs plumb on wooden pintles and lifts straight up for winter.",
    ]
    for i, t in enumerate(gates):
        s.text(40, 828 + i * 22, t, 13, INK)

    s.text(40, 970, "No router required — grooves/shoulders are table-saw work. Hand tools own the fit.", 13, DIM)
    s.save()


def sheet_m8():
    s = Sheet("M-8", "Mill stock · grain · warpage", "Select DF strategy · 2×12 yield · sticker · Japanese stock prep")
    s.titleblock()

    s.text(40, 70, "SPECIES STRATEGY (BUFFALO · PAINTED · LOW WARP)", 16, ACC, bold=True)
    sp = [
        "Structure: Douglas fir Select / #1 (or Select Structural) in 6×6 and 2×12 — stiff, straight, common mill sizes.",
        "Boards: DF 1×12 select — rip VG/rift-leaning edge strips to ¾×5½ (no bandsaw resaw required).",
        "Hardware wood: white oak 8/4 — kusabi, ⌀⅜ pegs, pintles, latch bar (hard, outdoor-durable).",
        "Paint seals DF end grain; Japanese joints leave play only where seasonal movement needs it (nuki height).",
    ]
    for i, t in enumerate(sp):
        s.text(40, 98 + i * 22, "•  " + t, 13, INK)

    s.text(40, 200, "GRAIN RULES (LEAST WARPAGE)", 16, ACC, bold=True)
    grain = [
        "1. REJECT: pith-centered sticks, ring shake, spiral grain, crook/bow >1/8″ in 8′, wet pockets, huge knots on joinery faces.",
        "2. 2×12 RAILS: rip the finished 7¼\" width from an OUTER third of the 11¼\" face — leave pith/center as waste or stakes.",
        "3. RING ORIENTATION: for posts, put more vertical grain on the 5½\" face (garden/drive exposure). Avoid flat-sawn cups on tenons.",
        "4. BOARDS: choose edge strips with rings closer to 45–90° to the face (rift/VG). Heart side rules: cup toward heart → orient consistently.",
        "5. BALANCE RIPS: mill matching faces the same day; sticker again overnight before joinery if shop RH swings.",
        "6. SEAL ENDS: wax or end-sealer on fresh crosscuts during sticker period to slow check.",
    ]
    for i, t in enumerate(grain):
        s.text(40, 228 + i * 22, t, 13, INK)

    # simple 2x12 yield diagram
    s.text(40, 380, "2×12 YIELD MAP (1½\" × 11¼\" face)", 16, ACC, bold=True)
    s.rect(40, 400, 520, 90, fill="#d9dcde", stroke=INK, sw=2)
    s.rect(40, 400, 160, 90, fill="#c5c8c2", stroke=INK, sw=1.5)
    s.rect(200, 400, 200, 90, fill="#e8eaeb", stroke=ACC, sw=2, dash="5 3")
    s.rect(400, 400, 160, 90, fill="#6e7578", stroke=INK, sw=1.5)
    s.text(120, 450, "OUTER", 14, DIM, "middle", bold=True)
    s.text(120, 470, "RAIL / CAP", 12, ACC, "middle", bold=True)
    s.text(300, 450, "PITH ZONE", 14, DIM, "middle", bold=True)
    s.text(300, 470, "WASTE / STAKES", 12, DIM, "middle")
    s.text(480, 450, "OUTER", 14, PAPER, "middle", bold=True)
    s.text(480, 470, "GATE / SPARE", 12, PAPER, "middle", bold=True)
    s.text(580, 430, "Per 12′ 2×12: prefer one clean 7¼\" nuki/cap blank", 13, INK)
    s.text(580, 454, "from the straighter outer third. Second outer strip →", 13, INK)
    s.text(580, 478, "gate stile/rail stock or brace. Center scrap ≠ joinery.", 13, INK)

    s.text(40, 520, "STICKER SCHEDULE", 16, ACC, bold=True)
    stick = [
        "Stack on flat sleepers · ¾\" stickers every 12–16\" · aligned vertically · weight the top.",
        "Shop or covered porch airflow; not on concrete without vapor break. Target: stabilize to shop RH.",
        "Minimum 14 days after delivery before final face milling; longer if stock arrived damp.",
        "Re-check with winding sticks before joinery. Re-sticker any board that moved >1/16″ in 4′.",
    ]
    for i, t in enumerate(stick):
        s.text(40, 548 + i * 22, "•  " + t, 13, INK)

    s.text(40, 650, "RE-DIMENSION SEQUENCE (YOUR SAWS)", 16, ACC, bold=True)
    red = [
        "POSTS: joint/rip 6×6 → 3½×5½ (LS 36 + Fence Guide). Rough 77″ then finish 75.5″ (H − cap + tenon). Mark tenon end.",
        "RAILS/CAP: rip 2×12 outer third → 7¼\" wide × 1½\" thick. Plane reference faces. Crosscut ~105″ privacy rails.",
        "BOARDS: rip 1×12 edge strips → 5½\" wide; plane faces to true ¾\". Cut course lengths after dry-fit rails.",
        "OAK: rip kusabi blanks; turn/rasp ⌀⅜ pegs; shape pintles + latch bar. Never substitute softwood pegs outdoors.",
    ]
    for i, t in enumerate(red):
        s.text(40, 678 + i * 22, t, 13, INK)

    s.text(40, 780, "JOINERY PREP AFTER MILLING", 16, ACC, bold=True)
    prep = [
        "True reference faces with #5 / Bridge City plane before any mortise layout — layout from the good face.",
        "Keep each post’s grain map: which face is garden, which cheek gets kusabi (consistent around the run).",
        "Nuki: mill full length, dry-slide through posts, then mark wedge seats from the assembled position.",
        "All locking faces stay bare wood (no paint/glue). Paint after dry-fit; mask tenons, wedges, peg holes, sleeve zones.",
    ]
    for i, t in enumerate(prep):
        s.text(40, 808 + i * 22, "•  " + t, 13, INK)

    s.text(40, 920, "FINISHED ENVELOPE UNCHANGED: 143″ × 65″ · 36″ gate · 3½×5½ posts · 1½×7¼ Prairie bands · ¾×5½ boards.", 13, DIM)
    s.text(40, 944, "Only the source stock and grain strategy change — CAD geometry and Japanese joint sizes stay Rev A/B compatible.", 13, DIM)
    s.text(40, 980, "BOM counts on M-6 / S-402. Tool stations on M-7. Joinery on M-3 / M-5. SSOT: fab/martin.json.", 13, DIM)
    s.save()


def sheet_g000():
    s = Sheet("G-000", "Cover · drawing index", "Rev D parametric fabrication model · inches")
    s.titleblock()
    s.text(40, 70, "MARTIN — DIGITAL MANUFACTURING DEFINITION", 18, ACC, bold=True)
    s.text(40, 100, "Parameter → geometry → metadata → drawings → BOM → cut list → build / QA", 14, DIM)
    s.text(40, 140, "GATES M0–M8: PASS (see fab/martin.json). CAD solids still grouped; Part IDs live in SSOT.", 13, INK)
    s.text(40, 180, "DRAWING INDEX", 16, ACC, bold=True)
    idx = [
        ("G-000", "This cover"),
        ("GA-100 / M-1", "General arrangement"),
        ("GA-110 / M-2", "Elevation & rail schedule"),
        ("J-400 / M-3", "Joinery details"),
        ("GA-140 / M-4", "Pad & socket piers"),
        ("P-350 / M-5", "Gate & latch"),
        ("S-401 / M-6", "Mill BOM & finished parts"),
        ("S-410 / M-7", "Shop method · stops · owner tools"),
        ("S-420 / M-8", "Grain · warpage · 2×12 yield"),
        ("S-402", "Rough + finished cut list (this package)"),
        ("P-301", "Post L-001…L-004 — datums & tenon"),
        ("QA-700", "Inspection plan"),
        ("EX-200", "Exploded / Walk app at /build"),
    ]
    yy = 210
    for code, title in idx:
        s.text(40, yy, code, 13, ACC, bold=True)
        s.text(220, yy, title, 13, INK)
        yy += 22
    s.text(40, 520, "CONTROLLING EQUATIONS", 16, ACC, bold=True)
    for i, (k, eq) in enumerate(LY["equations"].items()):
        s.text(40, 548 + i * 20, f"{k} = {eq}", 13, INK)
    s.text(40, 760, "D-001: post finished length = overall_height − cap_t + post_tenon_h = "
           f"{LY['post_finished_length']}\" (not height+tenon).", 13, INK)
    s.text(40, 784, "drop_off is class M — field-verify before pour. Fastener ban in timber.", 13, INK)
    s.text(40, 820, "Machine-readable: fence/martin/fab/martin.json + CSV schedules.", 13, DIM)
    s.text(40, 860, "Completeness: a craftsperson can fabricate from Part IDs, datums, and schedules without inferring critical sizes.", 13, DIM)
    s.save()


def sheet_s402():
    s = Sheet("S-402", "Rough & finished cut list", "Generated from SSOT · do not hand-edit numbers")
    s.titleblock()
    s.text(40, 70, "FINISHED DIMENSION LIST (after milling)", 16, ACC, bold=True)
    rows = [
        ("ID", "Qty", "T", "W", "L", "Material", "Notes"),
        ("L-001…004", "4", "3.5", "5.5", f"{LY['post_finished_length']}", "DF", "Shoulder = pad-top datum"),
        ("R-001…003", "3", "1.5", "7.25", f"{LY['nuki_length']}", "DF", "Outer-zone rip from 2×12"),
        ("R-004/005", "2", "1.5", "7.25", f"{round(LY['cap_length']/2, 2)}", "DF", "Kama-tsugi pair"),
        ("R-006", "1", "1.5", "7.25", f"{round(P['post_x']+1, 2)}", "DF", "P0 stub — no gate span"),
        ("G-001", "2", "1.5", "3.5", f"{LY['leaf_height']}", "DF", "LH/RH stiles"),
        ("G-010", "5", "1.5", "5.5", f"{round(LY['leaf_width']-2*P.get('post_x', 3.5)+3.5, 2)}"[:6], "DF",
         f"inner = leaf − 2×stile = {round(LY['leaf_width']-7, 2)}\""),
        ("K-001", "12", "0.625", "1.125", "5.5", "W. oak", "Fit to slot · never glue"),
        ("H-001", "12", "⌀0.375", "—", "3.0", "W. oak", "Drawbore pegs"),
        ("H-003", "1", "1.5", "3.5", "18", "W. oak", "Sliding latch"),
    ]
    # fix G-010 length properly
    rows[6] = ("G-010", "5", "1.5", "5.5", f"{round(LY['leaf_width']-7, 2)}", "DF", "Tenon extra not in finished L")
    yy = 100
    cols = [40, 160, 230, 300, 380, 500, 640]
    for r in rows:
        for i, cell in enumerate(r):
            s.text(cols[i], yy, str(cell), 12, DIM if r[0] == "ID" else INK, bold=(r[0] == "ID"))
        yy += 22
        s.line(40, yy - 16, 1600, yy - 16, 0.5, LIGHT)

    s.text(40, 360, "ROUGH / BREAKDOWN", 16, ACC, bold=True)
    s.text(40, 388, "Posts: 6×6×8′ → rough 5.5×5.5×77″ → finish 3.5×5.5×75.5″. Rails: 2×12×12′ → rip 7.25″ outer zone → nuki 104.5″.", 13, INK)
    s.text(40, 412, "Boards: cut COURSE HEIGHTS after rails exist (U-004). C1–C4 derived from rail CL ± rail_h/2 ± 0.125″.", 13, INK)
    yy = 448
    s.text(40, yy, "Course", 12, DIM, bold=True)
    s.text(200, yy, "Finished L", 12, DIM, bold=True)
    s.text(320, yy, "Qty (2 bays)", 12, DIM, bold=True)
    yy += 22
    n = LY["boards_per_bay"] * LY["bays"]
    for cid, h, z0, z1 in LY["course_heights"]:
        s.text(40, yy, cid, 13, INK)
        s.text(200, yy, f"{h:.3f}\"", 13, INK)
        s.text(320, yy, str(n), 13, INK)
        s.text(420, yy, f"z {z0:.2f}–{z1:.2f} AFF", 13, DIM)
        yy += 22
    s.text(40, 640, f"Privacy boards total {LY['privacy_board_qty']}  ·  Gate infill {LY['boards_gate']}  ·  Procurement {322} bf  ·  waste_factor 0.22 explicit", 13, ACC, bold=True)
    s.text(40, 680, "STOCK NESTS (2×12 × 12′): one nuki per board + remainder to gate. Do not nest pith zone into joinery. See fab/08_CUT_LISTS/stock_nests.csv", 13, INK)
    s.text(40, 720, "STOP S-011: MFT length stop for all four posts. STOP S-021: TS fence locked for all grooves. STOP S-040: peg from MFT.", 13, INK)
    s.text(40, 980, "Source: fence/martin/fab/martin_ssot.py  ·  Change overall_length and regenerate.", 13, DIM)
    s.save()


def sheet_p301():
    s = Sheet("P-301", "Posts L-001…L-004", "Datums · foot tenon · nuki CL · Rev D")
    s.titleblock()
    s.text(40, 70, "DATUMS — ALL POSTS", 16, ACC, bold=True)
    s.text(40, 100, "Datum End A: tenon shoulder = pad top. Measure nuki CL up from A, not from tenon tip.", 13, INK)
    s.text(40, 124, "Reference Face B: garden face (against fence when ripping). Reference Edge C: run-left arris.", 13, INK)
    s.text(40, 148, f"Finished: 3.5 × 5.5 × {LY['post_finished_length']}\"  ·  Tenon 2.5 × 4.5 × 12\"  ·  Shoulders ±1/32\" (T2)", 13, INK)

    # simple post elevation
    sc = 8.0
    x0, y0 = 80, 980
    body_h = LY["post_above_pad"] * sc
    ten = P["post_tenon_h"] * sc
    s.rect(x0, y0 - body_h, 3.5 * sc, body_h, fill="#d9dcde", stroke=INK, sw=2)
    s.rect(x0 + 0.5 * sc, y0, 2.5 * sc, ten, fill="#d9dcde", stroke=INK, sw=2)
    s.line(x0 - 20, y0, x0 + 80, y0, 1, ACC, dash="4 3")
    s.text(x0 + 90, y0 + 4, "DATUM A · PAD TOP / SHOULDER", 12, ACC)
    for cl, label in zip(P["rail_z_cl"], ("R1", "R2", "R3")):
        yy = y0 - cl * sc
        s.line(x0 - 8, yy, x0 + 3.5 * sc + 8, yy, 1, DIM, dash="3 2")
        s.text(x0 + 3.5 * sc + 16, yy + 4, f"{label} CL {cl}\"", 12, DIM)
    s.dim_v(y0 - body_h, y0, x0, f'{LY["post_above_pad"]}" ABOVE', offset=-40)
    s.dim_v(y0, y0 + ten, x0 + 3.5 * sc, '12" TENON', offset=50)

    s.text(420, 70, "HANDED / UNIQUE", 16, ACC, bold=True)
    notes = [
        "L-001 P0 Latch — nuki mortises; NO kusabi slots; Latch B mortise optional.",
        "L-002 P1 Hinge — nuki + kusabi; wooden pintle gudgeons on gate side.",
        "L-003 P2 Mid — nuki + kusabi; bears kama-tsugi.",
        "L-004 P3 End — nuki + kusabi; run terminus.",
        "Mortise: width = measured rail_t (sliding). Height = 7.25 + 1/16 ease.",
        "Cheeks ~1″ each side of rail (post_y − rail_t)/2.",
        "OP040: one MFT stop for all four rough/finish lengths. DO NOT MOVE.",
        "Grain: more vertical grain on 5.5″ exposed faces. No pith in tenon.",
    ]
    for i, t in enumerate(notes):
        s.text(420, 100 + i * 24, "•  " + t, 13, INK)
    s.text(420, 360, "QTY 4  ·  MAKE  ·  DF Select  ·  Purchase 6×6×8′", 14, ACC, bold=True)
    s.save()


def sheet_qa700():
    s = Sheet("QA-700", "Inspection plan", "QC checkpoints · tolerance class · gates")
    s.titleblock()
    s.text(40, 70, "DO NOT SKIP — SIGN OFF ON THE STICKER / DRY-FIT / SET", 16, ACC, bold=True)
    from martin_ssot import inspection
    yy = 110
    s.text(40, yy, "QC", 12, DIM, bold=True)
    s.text(120, yy, "Gate", 12, DIM, bold=True)
    s.text(200, yy, "Check", 12, DIM, bold=True)
    s.text(980, yy, "Criteria", 12, DIM, bold=True)
    yy += 24
    for q in inspection():
        s.text(40, yy, q["QC"], 12, ACC, bold=True)
        s.text(120, yy, q["GATE"], 12, INK)
        s.text(200, yy, q["CHECK"][:70], 12, INK)
        s.text(980, yy, q["CRITERIA"][:55], 12, DIM)
        yy += 22
    s.text(40, 430, "FIT CLASSES USED: SLIDING (nuki width) · CLEARANCE (foot tenon) · DRAWBORED (hozo/kama) · FLOATING (boards) · SNUG (brace lap)", 13, INK)
    s.text(40, 460, "FAILURE MODES: cupping if pith in nuki; locked mortise if ease omitted; winter bind if sleeve clearance lost; racking if brace omitted.", 13, INK)
    s.text(40, 500, "STRUCTURAL NOTE: Planning design — not a stamped PE document. Wind path: nuki compression + pier mass. No nail withdrawal.", 13, DIM)
    s.save()


if __name__ == "__main__":
    sheet_m1()
    sheet_m2()
    sheet_m3()
    sheet_m4()
    sheet_m5()
    sheet_m6()
    sheet_m7()
    sheet_m8()
    sheet_g000()
    sheet_s402()
    sheet_p301()
    sheet_qa700()
    print("MARTIN plans done →", OUT)
