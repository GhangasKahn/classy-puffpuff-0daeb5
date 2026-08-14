#!/usr/bin/env python3
"""Generate MARTIN marketing plan SVG sheets (A3 landscape, printable).

Dimensions come from martin_kernel.build_project() — do not hard-code.
Run:  python3 scripts/gen_martin_plans.py
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "fence", "martin"))
from martin_kernel import build_project, v as kv  # noqa: E402

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
        self.text(W - 40, Hpx - 34, "Sit-on-grade · No nails in timber · Rev D", 13, DIM, "end")

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
    s = Sheet("M-1", "General arrangement", "Scale 1:16 approx · dimensions in inches")
    s.titleblock()
    s.text(40, 70, "FRONT ELEVATION — garden face", 16, ACC, bold=True)
    s.text(40, 94, "143\" overall · 65\" high · 36\" gate · four 4×6 posts · three 2×8 Prairie bands", 14, DIM)

    # dodai sill (elevation)
    s.rect(X(-P["sill_overhang"]), Y(0), (L + 2 * P["sill_overhang"]) * S, P["sill_h"] * S,
           fill=LIGHT, stroke=INK, sw=1.5)
    s.text(X(L / 2), Y(-P["sill_h"] / 2) + 5, "DODAI SILL — SIT ON GRADE", 12, DIM, "middle")

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
    s.text(40, 980, "PLAN (ladder)", 14, ACC, bold=True)
    py = 1040
    ps = 4.5
    for cx in POSTS:
        s.rect(80 + cx * ps - fx * ps / 2, py - P["post_y"] * ps / 2,
               fx * ps, P["post_y"] * ps, fill="#d9dcde", stroke=INK, sw=1.2)
    s.rect(80 - P["sill_overhang"] * ps, py - P["base_width"] * ps / 2,
           (L + 2 * P["sill_overhang"]) * ps, P["base_width"] * ps,
           fill="none", stroke=DIM, sw=1, dash="4 3")
    s.text(80 + L * ps / 2, py + P["base_width"] * ps / 2 + 22,
           f'LADDER {P["base_width"]:g}" WIDE · CROSS-TIES AT POSTS · NO DIGGING', 12, DIM, "middle")

    # notes
    notes = [
        "DESIGN: Prairie horizontals (Darwin Martin / FLW) + Japanese nuki / hozo / kama-tsugi.",
        "JOINERY: No nails or screws in timber. Wedge-locked through-rails. Drawbored gate M&T.",
        "WINTER: Knock wedges → withdraw nuki → lift gate → lift posts → empty sandbags → carry ladder.",
        "FINISH: Exterior primer + owner gray. Mask wedge faces, tenons, and sill laps.",
        "ENGINEERING NOTE: Planning design — wind ballast is a calc, not a PE stamp. No foundations.",
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
        ("POST", "4×6", "3.5×5.5", "full height", "Nuki posts + 3.5\" tenon into F-003"),
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
    s.text(520, 144, "Ladder sills + sandbag boxes resist overturning", 13, INK)

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

    # driveway grade
    s.line(sx(-28), sy(-sh - pad_t), sx(-2), sy(-sh - pad_t), 2, "#5a5854")
    s.text(sx(-26), sy(-sh - pad_t) + 18, "DRIVEWAY (EXISTING)", 11, DIM)
    # garden grade
    s.line(sx(2), sy(-sh - pack), sx(28), sy(-sh - pack), 2, "#5a6a4a")
    s.text(sx(8), sy(-sh - pack) + 18, "GARDEN GRADE (LOWER)", 11, DIM)

    # rubber pads under driveway sill
    s.rect(sx(drive_cy - st / 2), sy(-sh), st * S4, pad_t * S4, fill="#3d3530", stroke=INK, sw=1)
    s.text(sx(drive_cy), sy(-sh - pad_t) - 6, "H-001 PADS", 10, DIM, "middle")

    # packing cribs under garden sill
    s.rect(sx(garden_cy - st / 2 - 1), sy(-sh), (st + 2) * S4, pack * S4, fill="#9a9890", stroke=INK, sw=1.5)
    s.text(sx(garden_cy), sy(-sh - pack / 2) + 4, f'F-004 PACK {pack:g}" TBM', 11, INK, "middle", bold=True)

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

    # ballast box on driveway side
    s.rect(sx(drive_cy - 5), sy(10), 10 * S4, 10 * S4, fill="#b8b6b0", stroke=INK, sw=1.5)
    s.text(sx(drive_cy), sy(5), "F-005 + H-007", 10, INK, "middle")

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
           f'SILLS {LY["sill_len"]:.0f}" × 4×6  ·  BASE {P["base_width"]:g}" WIDE  ·  DROP {P["drop_off"]:g}" PACKING TBM',
           13, INK)

    s.text(780, 420, "WINTER REMOVAL SEQUENCE", 16, ACC, bold=True)
    steps = [
        "1. Open gate · remove oak latch peg / padlock.",
        "2. Knock out rail wedges (kusabi) — save in labeled bag.",
        "3. Slide nuki rails out of posts (two-person).",
        "4. Lift vertical boards out of grooves; bundle flat.",
        "5. Lift gate leaf off wooden pintles.",
        "6. Lift each post straight up out of F-003.",
        "7. Empty sandbags; store dry. Lift ladder or leave sills.",
        "8. Nothing is poured. Nothing is buried. No post holes.",
    ]
    for i, t in enumerate(steps):
        s.text(780, 455 + i * 24, t, 13, INK)

    s.text(40, 780, "NOTES", 14, ACC, bold=True)
    s.text(40, 808, "• Entirely freestanding furniture fence. NO post holes. NO cement. NO gravel or stone pads.", 13, INK)
    s.text(40, 832, "• Field-measure driveway→garden drop; stack F-004 2×6 cribs to match. Default shown: 5\".", 13, INK)
    s.text(40, 856, "• H-001 rubber furniture pads under F-001 protect the driveway — no fasteners into pavement.", 13, INK)
    s.text(40, 880, "• Wind ballast: removable 50 lb bags in F-005 (planning count from kernel — not a PE stamp).", 13, INK)
    s.text(40, 904, "• Latch B default (mortise in P0). Do not epoxy into the house.", 13, INK)

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

    gw = LY["gate_leaf_w"]
    gh = LY["gate_h"]
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
        "LATCH B — DEFAULT (fully freestanding):",
        "  — 1.5\" × 3.5\" × 18\" sliding oak bar through latch stile.",
        "  — Bar enters mortise in P0 latch post; gravity catch.",
        "  — Cross-peg + optional keyed padlock hasp on bar.",
        "  — NO epoxy, NO house receiver, NO fasteners into the wall.",
        "LATCH A — OPTIONAL ONLY (if you later choose a house strike):",
        "  — Oak strike block on the wall you own — not in this default kit.",
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

    fam_meta = {
        "4x6x8": ("4×6", "8'", "Posts + cross-ties nested"),
        "4x6x16": ("4×6", "16'", "Dodai sills F-001 / F-002"),
        "2x8x10": ("2×8", "10'", "Nuki rails R-001…003 (104.50″)"),
        "2x8x12": ("2×8", "12'", "Cap C-001 + stub C-002 nested"),
        "2x6x8": ("2×6", "8'", "Gate G-001…008 nested"),
        "1x6x8": ("1×6", "8'", "Privacy + gate boards nested"),
        "2x4x8": ("2×4", "8'", "Kusabi W-001 blanks"),
        "oak_1x4x4": ("1×4 oak", "4'", "Pegs / latch / pintles"),
    }
    bf_by = {}
    for b in NEST["boards"]:
        bf_by[b["PURCHASE"]] = bf_by.get(b["PURCHASE"], 0) + b["BF"]
    rows = [("Qty", "Nominal", "Length", "Use", "Board feet")]
    for fam in ("4x6x8", "4x6x16", "2x8x10", "2x8x12", "2x6x8", "1x6x8", "2x4x8", "oak_1x4x4"):
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
        "Sandbags 50 lb: see kernel ballast.n_bags — removable wind ballast, NOT a pad",
        "Optional: stainless pintle hinges, keyed padlock hasp (only metal parts)",
        "NO concrete. NO gravel bed. NO post-hole digger. NO epoxy into the house.",
    ]
    for i, t in enumerate(misc):
        s.text(40, yy + 85 + i * 24, "•  " + t, 13, INK)

    s.text(40, 980, "CUT ORDER: sills/ties → posts → mortises → rails → dry assemble → boards → cap scarf → gate → paint → set ladder → drop in.", 13, DIM)
    s.save()


if __name__ == "__main__":
    sheet_m1()
    sheet_m2()
    sheet_m3()
    sheet_m4()
    sheet_m5()
    sheet_m6()
    print("MARTIN plans done →", OUT)
