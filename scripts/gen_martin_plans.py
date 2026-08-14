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
    s.text(40, 94, '143" overall · 65" high · 36" gate against house · φ Prairie 2×10/2×6 bands · ¾" dog gaps', 14, DIM)

    # dodai sill (elevation)
    s.rect(X(-P["sill_overhang"]), Y(0), (L + 2 * P["sill_overhang"]) * S, P["sill_h"] * S,
           fill=LIGHT, stroke=INK, sw=1.5)
    s.text(X(L / 2), Y(-P["sill_h"] / 2) + 5, "DODAI SILL — SIT ON DRIVEWAY", 12, DIM, "middle")

    # posts
    for i, cx in enumerate(POSTS):
        s.rect(X(cx - fx / 2), Y(H - P["cap_t"]), fx * S, (H - P["cap_t"]) * S,
               fill="#d9dcde", stroke=INK, sw=1.8)
        s.text(X(cx), Y(H) - 18, f"P{i}", 14, ACC, "middle", bold=True)

    # Prairie horizontal bands (privacy run P1–P3)
    for sl in LY["slats"]:
        fill = GRAY if sl["nuki"] else "#c5c8c2"
        s.rect(X(P1 - fx / 2 - 0.5), Y(sl["z1"]),
               (P3 - P1 + fx + 1) * S, sl["h"] * S, fill=fill, stroke=INK, sw=1.0)

    # cap
    s.rect(X(P1 - fx / 2 - 0.75), Y(H), (P3 - P1 + fx + 1.5) * S, P["cap_t"] * S,
           fill="#8a9094", stroke=INK, sw=1.2)
    s.rect(X(P0 - fx / 2 - 0.5), Y(H), (fx + 1) * S, P["cap_t"] * S,
           fill="#8a9094", stroke=INK, sw=1.2)

    # gate leaf outline + matching bands
    s.rect(X(fx + 0.5), Y(H - 0.5), (gate - 1) * S, (H - 1.5) * S,
           fill="#e8eaeb", stroke=ACC, sw=2, dash="6 4")
    for sl in LY["slats"]:
        s.rect(X(fx + 1.2), Y(sl["z1"]), (gate - 2.4) * S, sl["h"] * S,
               fill="#d0d3d5", stroke=LIGHT, sw=0.6)
    s.text(X(fx + gate / 2), Y(H / 2), "GATE", 16, ACC, "middle", bold=True)
    s.text(X(fx + gate / 2), Y(H / 2) + 22, 'AT HOUSE · 36" CLEAR', 11, DIM, "middle")

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
           f'LADDER {P["base_width"]:g}" WIDE · PLANTERS GARDEN-SIDE OF P1–P3 · NO PLANTER AT HOUSE', 12, DIM, "middle")

    # notes
    notes = [
        "DESIGN: Darwin Martin / FLW Prairie horizontals + Japanese nuki / hozo / kama-tsugi.",
        "SCREEN: 2×10 / 2×6 bands, ¾″ gaps, PT kick — beautiful and 100% dog containment.",
        "GATE: Flush to the house (P0). Oak pivots at P1. Latch B into P0. No planter at the gate.",
        "BALLAST: Live planters P1–P2 and P2–P3. Stone inside boxes only — not a pad.",
        "WINTER: Knock wedges → withdraw bands → lift gate off oak pivots → lift posts → empty troughs.",
        "FINISH: Ease 1/16″, end-grain sealer, PT dry then prime, two owner-gray coats. Buffalo 4-season.",
        "ENGINEERING NOTE: Planning design — planter mass is a calc, not a PE stamp. No foundations.",
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
    # Prairie bands
    for sl in LY["slats"]:
        fill = GRAY if sl["nuki"] else "#c5c8c2"
        s.rect(x(-0.5), y(sl["z1"]),
               (fx + bay + fx + 1) * S2, sl["h"] * S2, fill=fill, stroke=INK)
        label = f'{sl["stock"].upper()}  {sl["id"]}  {"NUKI" if sl["nuki"] else "HOUSED"}'
        s.text(x(fx + bay / 2), y(sl["cl"]) + 4, label, 11, PAPER if sl["nuki"] else INK, "middle", bold=True)
    # cap
    s.rect(x(-0.75), y(H), (fx + bay + fx + 1.5) * S2, P["cap_t"] * S2, fill="#8a9094", stroke=INK)

    s.dim_v(y(0), y(H), x(fx + bay + fx), '65"', offset=36)
    for sl in LY["slats"]:
        if sl["nuki"]:
            s.dim_v(y(0), y(sl["cl"]), x(-0.5), f'{sl["cl"]:g}" CL', offset=-50)
    s.dim_h(x(fx), x(fx + bay), y(0), f'{bay:.2f}" CLEAR', offset=40)
    s.dim_h(x(0), x(fx), y(H), '3.5"', offset=-28)

    # schedule table
    s.text(980, 70, "SLAT / BAND SCHEDULE", 16, ACC, bold=True)
    rows = [("Mark", "Stock", "Joinery", "CL AFF", "Role")]
    for sl in LY["slats"]:
        rows.append((sl["id"], sl["stock"], "nuki" if sl["nuki"] else "housed 0.75\"", f'{sl["cl"]:g}"', sl["role"][:28]))
    rows.append(("CAP", "2×8", "kama-tsugi + light dado", '65" top', "Weather cap / Wright light screen"))
    rows.append(("POST", "4×6", "3.5×5.5", "full height", "Nuki posts + 3.5\" tenon"))
    yy = 110
    for r in rows:
        xx = 980
        widths = (70, 70, 130, 80, 200)
        for i, cell in enumerate(r):
            s.text(xx, yy, cell, 12, INK if r[0] != "Mark" else DIM, bold=(r[0] == "Mark"))
            xx += widths[i]
        yy += 22
        s.line(980, yy - 16, 1620, yy - 16, 0.6, LIGHT)

    s.text(980, 430, "JOINERY RULE (STRENGTH)", 16, ACC, bold=True)
    bullets = [
        "Through-nuki + kusabi: K-001, R-001, R-003, R-005 only.",
        "Housed 0.75″ dado: remaining bands — keep the post web.",
        "Do not rip 2×10 to force φ. 9.25/5.5 = 1.682 ≈ φ.",
        "¾″ gaps + PT kick = dog seal. Do not caulk the light-screen.",
        "Cap scarf (kama-tsugi) on P2, drawbored. IP65 tape in soffit.",
        "Never glue locking faces. Paint after dry-fit; mask joinery.",
    ]
    for i, b in enumerate(bullets):
        s.text(980, 465 + i * 26, "•  " + b, 14, INK)

    s.save()


def sheet_m3():
    s = Sheet("M-3", "Joinery details", "Details @ 1:4 · cut from dimensional lumber")
    s.titleblock()

    # Nuki detail
    s.text(40, 70, "DETAIL 1 — NUKI THROUGH-BAND (2×10 IN 4×6)", 16, ACC, bold=True)
    sx, sy = 80, 420
    # post section
    s.rect(sx, sy - 120, 90, 240, fill="#d9dcde", stroke=INK, sw=2)  # post
    s.rect(sx - 80, sy - 50, 250, 70, fill=GRAY, stroke=INK, sw=2)  # 2x10
    s.poly([(sx + 70, sy - 10), (sx + 95, sy), (sx + 70, sy + 10)], fill=ACC, stroke=ACC)  # wedge
    s.text(sx + 45, sy + 150, "4×6 POST", 13, DIM, "middle")
    s.text(sx + 170, sy - 65, "2×10 NUKI", 13, DIM)
    s.text(sx + 110, sy + 5, "WEDGE", 12, ACC, bold=True)
    s.text(sx - 10, 70 + 40, 'Mortise: 1.5" × 9.25" through · cheeks 2" each side of slat', 13, INK)
    s.text(sx - 10, 70 + 62, 'Through-nuki only 4 bands. House the rest 0.75" — keep the post web.', 13, INK)

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
    s.text(40, 590, "Cut sickle scarf in 2×8 cap · dry fit · drawbore ⅛\" offset · oak peg ⅜\"", 13, INK)

    # Light-screen gaps
    s.text(520, 560, "DETAIL 4 — ¾″ PRAIRIE LIGHT-SCREEN (DOG SEAL)", 16, ACC, bold=True)
    s.rect(560, 620, 200, 40, fill=GRAY, stroke=INK, sw=2)
    s.rect(560, 668, 200, 12, fill="none", stroke=DIM, sw=1, dash="3 2")
    s.rect(560, 688, 200, 28, fill="#c5c8c2", stroke=INK, sw=1.5)
    s.text(520, 590, '0.75" gaps between 2×10 / 2×6 bands. Kick nuki at grade. Gauge must not pass.', 13, INK)
    s.text(520, 612, "Do not through-mortise every band — ¾″ web would split the post.", 13, INK)

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
        "4. Withdraw housed slats toward P3.",
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
    s = Sheet("M-5", "Gate & latch", "Gate leaf · oak pivots · Latch B into P0 · against the house")
    s.titleblock()
    s.text(40, 70, "GATE LEAF — 36\" CLEAR · FLUSH TO THE HOUSE (NO PLANTER AT P0)", 16, ACC, bold=True)

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
    for sl in LY["slats"]:
        s.rect(x(3.5), y(sl["z1"]), (gw - 7) * S5, sl["h"] * S5, fill="#c5c8c2", stroke=INK, sw=0.8)
    for zc in P["rail_z_cl"]:
        s.rect(x(3.5), y(zc + 2.75), (gw - 7) * S5, 5.5 * S5, fill=GRAY, stroke=INK)
    # brace
    s.line(x(3.5), y(8), x(gw - 3.5), y(gh - 8), 6, ACC)
    s.dim_h(x(0), x(gw), y(0), f'{gw:.1f}" LEAF WIDTH', offset=40)
    s.dim_v(y(0), y(gh), x(gw), f'{gh:.1f}"', offset=36)

    s.text(620, 70, "HARDWARE (WOOD-FIRST)", 16, ACC, bold=True)
    lines = [
        "HINGE: 1.25\" oak pivots W-003 (structurally best on a freestanding P1).",
        "  — Bottom socket in the sill/threshold at P1; top in the cap soffit.",
        "  — Leaf weight in compression to the driveway — not a cantilever pintle.",
        "  — Gate lifts straight up (+Z) for winter. Optional stainless pintle is backup only.",
        "LATCH B — DEFAULT (fully freestanding, against the house):",
        "  — 1.5\" × 3.5\" × 18\" sliding oak bar through latch stile.",
        "  — Bar enters mortise in P0 latch post; gravity catch.",
        "  — Cross-peg + optional keyed padlock hasp on bar.",
        "  — NO epoxy, NO house receiver, NO planter at P0.",
        "LATCH A — OPTIONAL ONLY (if you later choose a house strike):",
        "  — Oak strike block on the wall you own — not in this default kit.",
        "SWING: Into garden (confirm site). Clear arc 36\".",
        "JOINERY: Drawbored mortise & tenon at every stile/rail (hozo).",
        "  Diagonal brace half-lapped into rails — no fasteners.",
        "INFILL: Horizontal bands match the Prairie screen — ¾\" dog gaps.",
    ]
    for i, t in enumerate(lines):
        s.text(620, 100 + i * 22, t, 13, INK)

    s.text(40, 980, "PRIVACY: Gate infill matches the Prairie band rhythm. Bottom clear 0.375\" (dog). Top clear 0.50\" under cap.", 13, DIM)

    s.save()


def sheet_m6():
    s = Sheet("M-6", "Cut list & board feet", "Buy list for one hardware-store run · Buffalo")
    s.titleblock()
    s.text(40, 70, "LUMBER BUY LIST — DIMENSIONAL STOCK (paint-grade OK)", 16, ACC, bold=True)

    fam_meta = {
        "4x6x8": ("4×6", "8'", "Posts + cross-ties nested"),
        "4x6x16": ("4×6", "16'", "Dodai sills F-001 / F-002"),
        "2x10x10": ("2×10", "10'", "Prairie nuki / housed bands R-001/003/005/007"),
        "2x8x12": ("2×8", "12'", "Cap C-001 + stub C-002 nested"),
        "2x6x10": ("2×6", "10'", "Kick K-001 + housed 2×6 bands"),
        "2x6x8": ("2×6", "8'", "Gate + planters + braces nested"),
        "2x2x8": ("2×2", "8'", "Tectonic T-001 Darwin Martin blocks"),
        "2x4x8": ("2×4", "8'", "Kusabi W-001 blanks"),
        "oak_1x4x4": ("1×4 oak", "4'", "Pegs / latch / oak pivots"),
    }
    bf_by = {}
    for b in NEST["boards"]:
        bf_by[b["PURCHASE"]] = bf_by.get(b["PURCHASE"], 0) + b["BF"]
    rows = [("Qty", "Nominal", "Length", "Use", "Board feet")]
    for fam in ("4x6x8", "4x6x16", "2x10x10", "2x8x12", "2x6x10", "2x6x8", "2x2x8", "2x4x8", "oak_1x4x4"):
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

    s.text(40, 980, "CUT ORDER: sills/ties → posts → nuki/housed dados → bands → dry assemble → cap scarf + light dado → gate + oak pivots → paint → set → plant.", 13, DIM)
    s.save()


if __name__ == "__main__":
    sheet_m1()
    sheet_m2()
    sheet_m3()
    sheet_m4()
    sheet_m5()
    sheet_m6()
    print("MARTIN plans done →", OUT)
