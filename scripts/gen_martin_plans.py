#!/usr/bin/env python3
"""Generate MARTIN build-plan SVG sheets (A3 landscape, printable).

Dimensions mirror fence/martin/cad/martin_fence.py.
Run:  python3 scripts/gen_martin_plans.py
"""

from __future__ import annotations

import os

OUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "fence", "martin", "plans"
)
os.makedirs(OUT, exist_ok=True)

IN = 25.4

# ---- parameters (must mirror martin_fence.py) --------------------------------
P = dict(
    length=143.0,
    height=65.0,
    post_x=3.5,
    post_y=5.5,
    post_tenon_x=2.5,
    post_tenon_y=4.5,
    post_tenon_h=12.0,
    gate_clear=36.0,
    gate_gap=0.5,
    rail_t=1.5,
    rail_h=7.25,
    rail_z_cl=(10.0, 28.0, 46.0),
    cap_t=1.5,
    cap_w=7.25,
    board_t=0.75,
    board_w=5.5,
    board_gap=0.25,
    pad_overhang=6.0,
    pad_width=28.0,
    pad_thick=6.0,
    drop_off=5.0,
    pier_xy=14.0,
    pier_h=18.0,
    gravel_h=6.0,
    latch_bar=18.0,
)

fx = P["post_x"]
L = P["length"]
gate = P["gate_clear"]
P0 = fx / 2.0
P1 = fx + gate + fx / 2.0
p1_right = P1 + fx / 2.0
p3_left = L - fx
clear_span = p3_left - p1_right
bay_clear = (clear_span - fx) / 2.0
P2 = p1_right + bay_clear + fx / 2.0
P3 = L - fx / 2.0
POSTS = (P0, P1, P2, P3)
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
        self.text(W - 40, Hpx - 34, "Removable · No nails in timber · Rev A", 13, DIM, "end")

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
        "JOINERY: No nails or screws in timber. Wedge-locked through-rails. Drawbored gate M&T.",
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
        "Nuki (貫): rail passes through post mortise.",
        "Wedge (kusabi): hardwood wedge from cheek slot.",
        "Board grooves: ⅜\" deep dado in rail edges — boards float.",
        "Cap scarf (kama-tsugi) centered on P2, drawbored oak peg.",
        "All joins cut dry, fit, then paint; never glue locking faces.",
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
    s.text(sx - 10, 70 + 40, 'Mortise: 1.5" × 7.25" through · cheeks ~1" each side of rail', 13, INK)
    s.text(sx - 10, 70 + 62, 'Wedge: hardwood ⅝" × 1⅛" × 5.5" — tap to lock, reverse to release', 13, INK)

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
    s.text(520, 122, "Drain hole at sleeve bottom · never trap water", 13, INK)
    s.text(520, 144, "Cross-wedge optional through pier cheeks for storm lock", 13, INK)

    # Scarf
    s.text(40, 560, "DETAIL 3 — KAMA-TSUGI CAP SCARF AT P2", 16, ACC, bold=True)
    s.poly([(80, 720), (200, 720), (230, 700), (200, 680), (80, 680)], fill=GRAY, stroke=INK, sw=2)
    s.poly([(230, 700), (200, 680), (320, 680), (350, 700), (320, 720), (200, 720)],
           fill="#8a9094", stroke=INK, sw=2)
    s.line(215, 675, 215, 725, 2, ACC)
    s.text(215, 745, "OAK PEG (drawbore)", 12, ACC, "middle")
    s.text(40, 590, "Cut sickle scarf in 2×8 cap · dry fit · drawbore ⅛\" offset · oak peg ⅜\"", 13, INK)

    # Board groove
    s.text(520, 560, "DETAIL 4 — FLOATING 1×6 IN RAIL GROOVES", 16, ACC, bold=True)
    s.rect(560, 650, 200, 40, fill=GRAY, stroke=INK, sw=2)
    s.rect(600, 620, 30, 100, fill="#cfd3d5", stroke=INK, sw=1.5)
    s.rect(640, 620, 30, 100, fill="#cfd3d5", stroke=INK, sw=1.5)
    s.rect(680, 620, 30, 100, fill="#cfd3d5", stroke=INK, sw=1.5)
    s.text(520, 590, '⅜" deep × ⅞" wide dado in rail edges · ¼" board gaps for drainage', 13, INK)
    s.text(520, 612, "Boards drop in from top before cap is set — zero fasteners", 13, INK)

    s.text(40, 820, "JOINT VOCABULARY USED", 14, ACC, bold=True)
    s.text(40, 848, "Nuki 貫 · Kusabi wedge · Hozo ほぞ (gate) · Kama-tsugi 鎌継ぎ (cap) · Ari-kake optional at corners", 13, INK)

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
        "  Diagonal brace half-lapped into rails — no fasteners.",
    ]
    for i, t in enumerate(lines):
        s.text(620, 100 + i * 22, t, 13, INK)

    s.text(40, 980, "PRIVACY: Gate boards match fence 1×6 language; rails align with Prairie bands R1–R3.", 13, DIM)

    s.save()


def sheet_m6():
    s = Sheet("M-6", "Cut list & board feet", "Buy list for one hardware-store run · Buffalo")
    s.titleblock()
    s.text(40, 70, "LUMBER BUY LIST — DIMENSIONAL STOCK (paint-grade OK)", 16, ACC, bold=True)

    rows = [
        ("Qty", "Nominal", "Length", "Use", "Board feet"),
        ("4", "4×6", "8'", "Posts P0–P3 (cut to 65\" + 12\" tenon from same blank)", "64.0"),
        ("6", "2×8", "10'", "Prairie nuki rails R1–R3 (cut to fit; extras for gate rails/brace scrap)", "80.0"),
        ("3", "2×8", "12'", "Cap rails + latch bar stock + sill scraps", "48.0"),
        ("4", "2×6", "8'", "Gate stiles/rails / secondary bands", "32.0"),
        ("18", "1×6", "8'", "Privacy + gate vertical boards (¾\" — matches existing fence)", "72.0"),
        ("1", "2×4", "8'", "Wedge stock (rip to kusabi blanks) + stakes", "5.3"),
        ("1", "1×4 Oak", "4'", "Drawbore pegs, pintle blanks (hardwood)", "1.3"),
    ]
    yy = 110
    cols = [40, 120, 250, 360, 1180]
    for r in rows:
        for i, cell in enumerate(r):
            s.text(cols[i], yy, cell, 14, DIM if r[0] == "Qty" else INK, bold=(r[0] == "Qty" or i == 0))
        yy += 30
        s.line(40, yy - 20, 1400, yy - 20, 0.7, LIGHT)

    s.text(40, yy + 10, "TOTAL LUMBER ≈ 303 board feet  ·  Buy +15% waste on joinery stock → order ~350 bf equivalent as above counts", 14, ACC, bold=True)

    s.text(40, yy + 55, "NON-TIMBER", 16, ACC, bold=True)
    misc = [
        "Concrete 4000 psi air-entrained: ~0.35 yd³ (pad + 4 piers) — or 12–14 bags 80 lb + pier precast option",
        "#57 crushed stone: ~0.4 yd³ under pad",
        "Sleeve liners: 4 pcs — PVC Sch40 or galv. sized to tenon (or form sleeves and remove)",
        "Exterior primer + owner gray paint (2 coats); end-grain sealer",
        "Optional: stainless pintle hinges, keyed padlock hasp (only metal parts)",
        "Epoxy anchoring adhesive for house receiver sleeve (Latch A)",
        "Plastic shim pack / construction adhesive — NOT for joinery (pad leveling only)",
    ]
    for i, t in enumerate(misc):
        s.text(40, yy + 85 + i * 24, "•  " + t, 13, INK)

    s.text(40, 980, "CUT ORDER: posts → mortises → rails → dry assemble → boards → cap scarf → gate → paint → set piers/pad → drop in.", 13, DIM)
    s.save()


if __name__ == "__main__":
    sheet_m1()
    sheet_m2()
    sheet_m3()
    sheet_m4()
    sheet_m5()
    sheet_m6()
    print("MARTIN plans done →", OUT)
