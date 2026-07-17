#!/usr/bin/env python3
"""Generate STELE build-plan SVG sheets (A3 landscape, printable).

Dimensions mirror fence/stele/cad/stele_fence.py (mm), with inch callouts.
Run:  python3 scripts/gen_stele_plans.py
"""

import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "fence", "stele", "plans")
os.makedirs(OUT, exist_ok=True)

# ---- parameters (must mirror stele_fence.py) --------------------------------
P = dict(
    frost_depth=1220, footing_w=600, footing_h=300, gravel_w=700, gravel_h=150,
    stem_w=350, plinth_w=560, plinth_h=150,
    shaft_base=480, shaft_top=360, shaft_h=1600,
    cap1_w=560, cap1_h=50, cap2_w=470, cap2_h=55,
    pyr_base=380, pyr_top=180, pyr_h=110,
    bay_cc=2440, rail_t=38, rail_w=89, rail_z=(350, 1000, 1650), pocket_depth=60,
    board_t=19, board_w=140, board_gap=10, board_z0=320, board_z1=1780,
    tcap_h=45, tcap_w=120, curb_w=200, curb_h=250,
    gate_clear=1220, arch_depth=220, arch_thick=350,
    impost_w=520, impost_h=60, key_b=180, key_t=280, key_h=300,
)

PIER_TOP = P["plinth_h"] + P["shaft_h"] + P["cap1_h"] + P["cap2_h"] + P["pyr_h"]  # 1965
SPRING = P["plinth_h"] + P["shaft_h"] + P["impost_h"]                              # 1810
CROWN = SPRING + P["gate_clear"] / 2 + P["arch_depth"]                              # 2640

# ---- sheet primitives --------------------------------------------------------
W, H = 1680, 1188  # A3 landscape @ 4 px/mm
INK, DIM, ACC, PAPER, LIGHT = "#26241f", "#8a6f4d", "#a34e2b", "#f6f3ea", "#c8c2b2"
MONO = "font-family='IBM Plex Mono, Menlo, monospace'"
SER = "font-family='Georgia, serif'"


def inch(mm):
    v = mm / 25.4
    return ("%.1f" % v).rstrip("0").rstrip(".") + '"'


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            if "&amp;" not in s and "&lt;" not in s and "&#" not in s else s)


class Sheet:
    def __init__(self, code, title, scale_note):
        self.code, self.title, self.scale_note = code, title, scale_note
        self.b = []

    def add(self, s):
        self.b.append(s)

    def line(self, x1, y1, x2, y2, w=2, color=INK, dash=None):
        d = f" stroke-dasharray='{dash}'" if dash else ""
        self.add(f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' "
                 f"stroke='{color}' stroke-width='{w}'{d}/>")

    def rect(self, x, y, w, h, fill="none", stroke=INK, sw=2, dash=None):
        d = f" stroke-dasharray='{dash}'" if dash else ""
        self.add(f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' "
                 f"fill='{fill}' stroke='{stroke}' stroke-width='{sw}'{d}/>")

    def poly(self, pts, fill="none", stroke=INK, sw=2, close=True):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        tag = "polygon" if close else "polyline"
        self.add(f"<{tag} points='{p}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}'/>")

    def text(self, x, y, s, size=20, color=INK, anchor="start", mono=True, bold=False, rot=None, bg=False):
        f = MONO if mono else SER
        wgt = " font-weight='600'" if bold else ""
        r = f" transform='rotate({rot} {x:.1f} {y:.1f})'" if rot is not None else ""
        if bg and rot is None:
            w = len(s) * size * 0.62
            bx = {"start": x - 4, "middle": x - w / 2 - 4, "end": x - w - 4}[anchor]
            self.add(f"<rect x='{bx:.1f}' y='{y - size:.1f}' width='{w + 8:.1f}' "
                     f"height='{size + 6:.1f}' fill='{PAPER}'/>")
        self.add(f"<text x='{x:.1f}' y='{y:.1f}' {f} font-size='{size}' fill='{color}' "
                 f"text-anchor='{anchor}'{wgt}{r}>{esc(s)}</text>")

    def dim_h(self, x1, x2, y, label, offset=0, size=17):
        """Horizontal dimension between x1..x2 at height y."""
        yy = y + offset
        for x in (x1, x2):
            self.line(x, y, x, yy + 8, 1, DIM)
        self.line(x1, yy, x2, yy, 1.4, DIM)
        for x, s in ((x1, 1), (x2, -1)):
            self.poly([(x, yy), (x + s * 12, yy - 4), (x + s * 12, yy + 4)], fill=DIM, stroke=DIM, sw=0.5)
        self.text((x1 + x2) / 2, yy - 7, label, size, DIM, "middle", bg=True)

    def dim_v(self, y1, y2, x, label, offset=0, size=17):
        xx = x + offset
        for y in (y1, y2):
            self.line(x, y, xx + (8 if offset >= 0 else -8), y, 1, DIM)
        self.line(xx, y1, xx, y2, 1.4, DIM)
        for y, s in ((y1, 1), (y2, -1)):
            self.poly([(xx, y), (xx - 4, y + s * 12), (xx + 4, y + s * 12)], fill=DIM, stroke=DIM, sw=0.5)
        self.text(xx + 10, (y1 + y2) / 2 + 5, label, size, DIM, bg=True)

    def note(self, x, y, lines, size=17, lh=24):
        for i, s in enumerate(lines):
            self.text(x, y + i * lh, s, size)

    def save(self, fname, sheet_no, total):
        frame = 30
        tb_h = 96
        head = (
            f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {H}' "
            f"font-size='20'>"
            f"<rect width='{W}' height='{H}' fill='{PAPER}'/>"
            f"<rect x='{frame}' y='{frame}' width='{W-2*frame}' height='{H-2*frame}' "
            f"fill='none' stroke='{INK}' stroke-width='3'/>"
        )
        # title block
        tb = []
        tb.append(f"<rect x='{frame}' y='{H-frame-tb_h}' width='{W-2*frame}' height='{tb_h}' "
                  f"fill='{PAPER}' stroke='{INK}' stroke-width='3'/>")
        tb.append(f"<line x1='{W-560}' y1='{H-frame-tb_h}' x2='{W-560}' y2='{H-frame}' stroke='{INK}' stroke-width='2'/>")
        tb.append(f"<line x1='{W-260}' y1='{H-frame-tb_h}' x2='{W-260}' y2='{H-frame}' stroke='{INK}' stroke-width='2'/>")
        tb.append(f"<text x='{frame+24}' y='{H-frame-tb_h+38}' {SER} font-size='30' fill='{INK}' font-weight='600'>STELE — masonry &amp; timber fence</text>")
        tb.append(f"<text x='{frame+24}' y='{H-frame-tb_h+72}' {MONO} font-size='17' fill='{DIM}'>BUFFALO NY · FROST 48in · SNOW 40psf GROUND · WIND 115mph ULT · FREEZE-THAW SEVERE</text>")
        tb.append(f"<text x='{W-536}' y='{H-frame-tb_h+38}' {MONO} font-size='17' fill='{INK}'>{self.title}</text>")
        tb.append(f"<text x='{W-536}' y='{H-frame-tb_h+70}' {MONO} font-size='15' fill='{DIM}'>{self.scale_note} · mm [in]</text>")
        tb.append(f"<text x='{W-236}' y='{H-frame-tb_h+42}' {MONO} font-size='26' fill='{ACC}' font-weight='600'>{self.code}</text>")
        tb.append(f"<text x='{W-236}' y='{H-frame-tb_h+72}' {MONO} font-size='16' fill='{DIM}'>SHEET {sheet_no} OF {total}</text>")
        svg = head + "".join(self.b) + "".join(tb) + "</svg>"
        with open(os.path.join(OUT, fname), "w") as f:
            f.write(svg)
        print("wrote", fname)


TOTAL = 5

# =============================================================================
# S-1 — cover: overall elevation + plan + criteria
# =============================================================================
s = Sheet("S-1", "GENERAL ARRANGEMENT", "ELEV + PLAN 1:60")
s.text(70, 110, "STELE", 64, INK, mono=False, bold=True)
s.text(72, 148, "A fence built like the old world — Egyptian batter, Roman foundations, Mayan caps.", 19, DIM)

# ---- overall front elevation, 1:60 → px = mm * 4/60 = /15
sc = 4 / 60.0
ox, oy = 120, 560  # grade line y
run = 11940


def X(mm):
    return ox + mm * sc


def Y(mm):
    return oy - mm * sc


piers = [0, 2440, 4880, 7320, 9020, 11460]
gate_l, gate_r = 7320, 9020
s.line(X(-400), oy, X(run + 400), oy, 2.5)  # grade
for i, cx in enumerate(piers):
    b, t = P["shaft_base"] * sc, P["shaft_top"] * sc
    x = X(cx)
    zp, zs = Y(P["plinth_h"]), Y(P["plinth_h"] + P["shaft_h"])
    s.rect(x - P["plinth_w"] / 2 * sc, zp, P["plinth_w"] * sc, P["plinth_h"] * sc)
    s.poly([(x - b / 2, zp), (x + b / 2, zp), (x + t / 2, zs), (x - t / 2, zs)])
    if cx in (gate_l, gate_r):
        s.rect(x - P["impost_w"] / 2 * sc, Y(SPRING), P["impost_w"] * sc, P["impost_h"] * sc)
    else:
        s.rect(x - P["cap1_w"] / 2 * sc, Y(P["plinth_h"] + P["shaft_h"] + P["cap1_h"]), P["cap1_w"] * sc, P["cap1_h"] * sc)
        s.rect(x - P["cap2_w"] / 2 * sc, Y(P["plinth_h"] + P["shaft_h"] + P["cap1_h"] + P["cap2_h"]), P["cap2_w"] * sc, P["cap2_h"] * sc)
        s.poly([(x - P["pyr_base"] / 2 * sc, Y(PIER_TOP - P["pyr_h"])), (x + P["pyr_base"] / 2 * sc, Y(PIER_TOP - P["pyr_h"])),
                (x + P["pyr_top"] / 2 * sc, Y(PIER_TOP)), (x - P["pyr_top"] / 2 * sc, Y(PIER_TOP))])

# timber bays (hatch as vertical strokes)
bays = [(0, 2440), (2440, 4880), (4880, 7320), (9020, 11460)]
for a, b_ in bays:
    xa, xb = X(a + P["shaft_base"] / 2), X(b_ - P["shaft_base"] / 2)
    s.rect(xa, Y(P["curb_h"]), xb - xa, P["curb_h"] * sc, stroke=INK, sw=1.5)
    s.rect(xa, Y(P["board_z1"]), xb - xa, (P["board_z1"] - P["board_z0"]) * sc, stroke=INK, sw=1.5)
    n = int((xb - xa) // 10)
    for i in range(1, n):
        s.line(xa + i * 10, Y(P["board_z1"]) + 2, xa + i * 10, Y(P["board_z0"]) - 2, 0.6, LIGHT)
    s.rect(xa, Y(P["board_z1"] + P["tcap_h"]), xb - xa, P["tcap_h"] * sc, stroke=INK, sw=1.5)

# arch
gc = X((gate_l + gate_r) / 2)
r_in, r_out = P["gate_clear"] / 2 * sc, (P["gate_clear"] / 2 + P["arch_depth"]) * sc
ys = Y(SPRING)
s.add(f"<path d='M {gc-r_out:.1f} {ys:.1f} A {r_out:.1f} {r_out:.1f} 0 0 1 {gc+r_out:.1f} {ys:.1f}' fill='none' stroke='{INK}' stroke-width='2'/>")
s.add(f"<path d='M {gc-r_in:.1f} {ys:.1f} A {r_in:.1f} {r_in:.1f} 0 0 1 {gc+r_in:.1f} {ys:.1f}' fill='none' stroke='{INK}' stroke-width='2'/>")
s.rect(gc - P["key_t"] / 2 * sc, Y(CROWN + 60) , P["key_t"] * sc, P["key_h"] * sc)
# leaf
s.rect(X(gate_l + P["shaft_base"] / 2 + 25), Y(150 + 1600), (P["gate_clear"] - 50) * sc, 1600 * sc, sw=1.5)

s.dim_h(X(0), X(2440), Y(PIER_TOP) - 26, "2440 [8'-0\"] TYP BAY", -22)
s.dim_h(X(gate_l), X(gate_r), Y(CROWN) - 40, "1700 CC · 1220 [48\"] CLEAR", -20)
s.dim_v(Y(PIER_TOP), oy, X(run) + 100, "1965", 20)
s.dim_v(Y(CROWN), oy, X(run) + 170, "2640", 20)
s.dim_h(X(0), X(run), oy + 60, "11 940 [39'-2\"] OVERALL — 4 PANEL BAYS + ARCH GATE", 26)
s.text(X(0) - 60, oy + 22, "GRADE", 15, DIM)

# ---- plan view, 1:60, below elevation
oy2 = 800
s.text(120, oy2 - 60, "PLAN", 22, INK, bold=True)
for cx in piers:
    s.rect(X(cx) - P["shaft_base"] / 2 * sc, oy2 - P["shaft_base"] / 2 * sc, P["shaft_base"] * sc, P["shaft_base"] * sc)
for a, b_ in bays:
    xa, xb = X(a + P["shaft_base"] / 2), X(b_ - P["shaft_base"] / 2)
    s.rect(xa, oy2 - P["rail_t"] / 2 * sc, xb - xa, P["rail_t"] * sc, sw=1)
    s.rect(xa, oy2 - P["rail_t"] / 2 * sc - P["board_t"] * sc - 1, xb - xa, P["board_t"] * sc, sw=1)
s.line(X(gate_l + P["shaft_base"] / 2), oy2, X(gate_r - P["shaft_base"] / 2), oy2, 1.4, DIM, dash="8 6")
s.text(gc, oy2 + 40, "GATE SWING", 15, DIM, "middle")
s.text(120, oy2 + 76, "STREET SIDE — BOARD FACE (RAIN-SCREEN)", 15, DIM)

# ---- criteria block
s.note(1200, 180, [
    "DESIGN CRITERIA — BUFFALO NY",
    "· FROST: FTG BASE 1220 [48\"]",
    "  BELOW GRADE",
    "· SNOW 40 PSF GROUND + DRIFT",
    "· WIND 115 MPH ULT (ASCE 7)",
    "· CONC 4000 PSI AIR-ENTRAINED",
    "· MASONRY: CAST STONE /",
    "  LIMESTONE VENEER, TYPE S",
    "· TIMBER: W. RED CEDAR OR",
    "  BLACK LOCUST",
    "· WOOD >= 250 [10\"] ABOVE",
    "  GRADE ON CURB",
    "· VERIFY BUFFALO GREEN CODE",
    "  HEIGHT LIMITS BEFORE BUILD",
    "",
    "SHEET INDEX",
    "S-1 GENERAL  S-2 PANEL BAY",
    "S-3 FOUNDATION  S-4 PIER",
    "S-5 ROMAN ARCH GATE",
], 17, 27)
s.save("S1_general.svg", 1, TOTAL)

# =============================================================================
# S-2 — panel bay elevation, 1:20
# =============================================================================
s = Sheet("S-2", "PANEL BAY — ELEVATION + RAIL SECTION", "1:20")
sc = 4 / 20.0
ox, oy = 210, 880


def X2(mm):
    return ox + mm * sc


def Y2(mm):
    return oy - mm * sc


s.line(X2(-300), oy, X2(2800), oy, 2.5)
for cx in (0, 2440):
    x = X2(cx)
    zp, zs = Y2(P["plinth_h"]), Y2(P["plinth_h"] + P["shaft_h"])
    s.rect(x - P["plinth_w"] / 2 * sc, zp, P["plinth_w"] * sc, P["plinth_h"] * sc)
    s.poly([(x - P["shaft_base"] / 2 * sc, zp), (x + P["shaft_base"] / 2 * sc, zp),
            (x + P["shaft_top"] / 2 * sc, zs), (x - P["shaft_top"] / 2 * sc, zs)])
    s.rect(x - P["cap1_w"] / 2 * sc, Y2(P["plinth_h"] + P["shaft_h"] + P["cap1_h"]), P["cap1_w"] * sc, P["cap1_h"] * sc)
    s.rect(x - P["cap2_w"] / 2 * sc, Y2(P["plinth_h"] + P["shaft_h"] + P["cap1_h"] + P["cap2_h"]), P["cap2_w"] * sc, P["cap2_h"] * sc)
    s.poly([(x - P["pyr_base"] / 2 * sc, Y2(PIER_TOP - P["pyr_h"])), (x + P["pyr_base"] / 2 * sc, Y2(PIER_TOP - P["pyr_h"])),
            (x + P["pyr_top"] / 2 * sc, Y2(PIER_TOP)), (x - P["pyr_top"] / 2 * sc, Y2(PIER_TOP))])

xa, xb = X2(P["shaft_base"] / 2), X2(2440 - P["shaft_base"] / 2)
s.rect(xa, Y2(P["curb_h"]), xb - xa, P["curb_h"] * sc, sw=1.6)
for zc in P["rail_z"]:
    s.rect(xa - P["pocket_depth"] * sc, Y2(zc + P["rail_w"] / 2), (xb - xa) + 2 * P["pocket_depth"] * sc, P["rail_w"] * sc, stroke=ACC, sw=1.6, dash="10 5")
pitch = P["board_w"] + P["board_gap"]
clear = 2440 - P["shaft_base"]
n = int((clear - P["board_gap"]) // pitch)
span = n * pitch - P["board_gap"]
bx0 = P["shaft_base"] / 2 + (clear - span) / 2
for i in range(n):
    s.rect(X2(bx0 + i * pitch), Y2(P["board_z1"]), P["board_w"] * sc, (P["board_z1"] - P["board_z0"]) * sc, sw=1.1)
s.rect(xa - P["pocket_depth"] * sc, Y2(P["board_z1"] + P["tcap_h"]), (xb - xa) + 2 * P["pocket_depth"] * sc, P["tcap_h"] * sc, sw=1.6)

s.dim_h(X2(0), X2(2440), Y2(PIER_TOP) - 30, "2440 [8'-0\"] CC", -24)
s.dim_h(xa, xb, oy + 46, f"{clear:.0f} [{inch(clear)}] CLEAR", 22)
s.dim_v(Y2(P["rail_z"][0]), oy, X2(2440) + 150, "350", 30)
s.dim_v(Y2(P["rail_z"][1]), oy, X2(2440) + 230, "1000", 30)
s.dim_v(Y2(P["rail_z"][2]), oy, X2(2440) + 310, "1650", 30)
s.dim_v(Y2(P["board_z1"] + P["tcap_h"]), oy, X2(-160), "1825 [71.9\"] PANEL TOP", -74)
s.dim_v(Y2(P["curb_h"]), oy, X2(-60), "250", -40)

s.note(1150, 240, [
    "RAILS: 38x89 [2x4] CEDAR ON EDGE,",
    "  SET 60 [2.4\"] INTO PIER POCKETS",
    "  (HASHIRA NUKI — THROUGH-RAIL).",
    "  WEDGE-LOCK, NO FACE SCREWS.",
    "BOARDS: 19x140 [1x6] VERTICAL,",
    "  10 GAP — RAIN-SCREEN AIRFLOW,",
    "  FASTEN TO RAILS ONLY, SS RING",
    "  SHANK NAILS 2 PER CROSSING.",
    "CAP: 45x120 CEDAR, 8 DEG WASH,",
    "  DRIP KERF BOTH EDGES.",
    "CURB: CAST CONC OR SOLID CMU,",
    "  KEEPS BOARDS CLEAR OF SNOW,",
    "  SPLASH + PLOW BERM.",
], 17, 26)

# rail/pocket detail inset, 1:5
s.text(1150, 620, "RAIL POCKET DETAIL — 1:5", 18, INK, bold=True)
dsc = 4 / 5.0
dx, dy = 1180, 660
s.rect(dx, dy, 120 * dsc, 200 * dsc)  # pier face patch
s.rect(dx + 60 * dsc, dy + 40 * dsc, 200 * dsc, (P["rail_w"] + 6) * dsc, stroke=ACC, sw=1.6, dash="8 4")
s.rect(dx + 66 * dsc, dy + 43 * dsc, 260 * dsc, P["rail_w"] * dsc)
s.text(dx + 130, dy + 26, "POCKET 44x95, 60 DEEP", 14, ACC)
s.text(dx + 150, dy + 105, "38x89 RAIL + HW WEDGE", 14, DIM)
s.text(dx + 8, dy + 190, "SLOPE POCKET FLOOR 5 DEG OUT — DRAIN", 14, DIM)
s.save("S2_panel_bay.svg", 2, TOTAL)

# =============================================================================
# S-3 — foundation section, 1:15
# =============================================================================
s = Sheet("S-3", "PIER FOUNDATION — SECTION", "1:15")
sc = 4 / 15.0
ox, oy = 640, 300


def X3(mm):
    return ox + mm * sc


def Y3(mm):
    return oy - mm * sc


gl = oy  # grade
s.line(X3(-1500), gl, X3(1500), gl, 2.5)
s.text(X3(-1460), gl - 10, "GRADE", 15, DIM)

# gravel
s.rect(X3(-P["gravel_w"] / 2), Y3(-P["frost_depth"]), P["gravel_w"] * sc, P["gravel_h"] * sc, stroke=INK, sw=1.6)
# hatch gravel
for i in range(1, 14):
    xx = X3(-P["gravel_w"] / 2) + i * (P["gravel_w"] * sc / 14)
    s.line(xx, Y3(-P["frost_depth"]), xx - 8, Y3(-P["frost_depth"]) + P["gravel_h"] * sc, 0.8, LIGHT)
# footing
s.rect(X3(-P["footing_w"] / 2), Y3(-P["frost_depth"] + P["footing_h"]), P["footing_w"] * sc, P["footing_h"] * sc, sw=2)
# stem
s.rect(X3(-P["stem_w"] / 2), Y3(0), P["stem_w"] * sc, (P["frost_depth"] - P["footing_h"]) * sc, sw=2)
# plinth + shaft start
s.rect(X3(-P["plinth_w"] / 2), Y3(P["plinth_h"]), P["plinth_w"] * sc, P["plinth_h"] * sc, sw=2)
s.poly([(X3(-P["shaft_base"] / 2), Y3(P["plinth_h"])), (X3(P["shaft_base"] / 2), Y3(P["plinth_h"])),
        (X3(P["shaft_top"] / 2), Y3(P["plinth_h"] + 700)), (X3(-P["shaft_top"] / 2), Y3(P["plinth_h"] + 700))], close=False)
s.line(X3(-P["shaft_top"] / 2) , Y3(P["plinth_h"] + 700), X3(P["shaft_top"] / 2), Y3(P["plinth_h"] + 700), 1.2, LIGHT, dash="6 6")
s.text(X3(0), Y3(P["plinth_h"] + 740), "SHAFT CONT. — SEE S-4", 14, DIM, "middle")

# rebar
for dx_ in (-100, 0, 100):
    s.line(X3(dx_), Y3(-P["frost_depth"] + 60), X3(dx_), Y3(120), 1.6, ACC, dash="3 5")
s.line(X3(-P["footing_w"] / 2 + 60), Y3(-P["frost_depth"] + 70), X3(P["footing_w"] / 2 - 60), Y3(-P["frost_depth"] + 70), 1.6, ACC, dash="3 5")
s.text(X3(-P["footing_w"] / 2) - 16, Y3(-P["frost_depth"] + 90), "(4) #4 VERT + #3 TIES @ 300", 15, ACC, "end", bg=True)
s.text(X3(-P["footing_w"] / 2) - 16, Y3(-P["frost_depth"] + 40), "(3) #4 EW BOTTOM, 75 COVER", 15, ACC, "end", bg=True)

# dims
s.dim_v(Y3(0), Y3(-P["frost_depth"]), X3(-P["gravel_w"] / 2) - 130, "1220 [48\"] FROST", -60)
s.dim_v(Y3(-P["frost_depth"] + P["footing_h"]), Y3(-P["frost_depth"]), X3(P["gravel_w"] / 2) + 60, "300 [12\"]", 40)
s.dim_v(Y3(-P["frost_depth"]), Y3(-P["frost_depth"] - P["gravel_h"]), X3(P["gravel_w"] / 2) + 60, "150 [6\"] #57 STONE", 40)
s.dim_h(X3(-P["footing_w"] / 2), X3(P["footing_w"] / 2), Y3(-P["frost_depth"] - P["gravel_h"]) + 70, "600 [24\"] SQ", 40)
s.dim_h(X3(-P["stem_w"] / 2), X3(P["stem_w"] / 2), Y3(-500), "350 [14\"]", 0)
s.dim_h(X3(-P["plinth_w"] / 2), X3(P["plinth_w"] / 2), Y3(P["plinth_h"]) - 26, "560 [22\"]", -20)

s.note(1130, 240, [
    "FOUNDATION NOTES",
    "1. EXCAVATE TO UNDISTURBED SOIL,",
    "   MIN 1220 [48\"] BELOW FINISH GRADE.",
    "2. 150 COMPACTED #57 STONE — DRAINS",
    "   WATER AWAY FROM BEARING PLANE",
    "   (ROMAN RULE: NEVER LET THE BASE",
    "   SIT WET).",
    "3. POUR FTG + STEM MONOLITHIC WHERE",
    "   POSSIBLE. 4000 PSI AIR-ENTRAINED.",
    "4. DAMP-PROOF STEM TOP 150; BREAK",
    "   BOND W/ PLINTH USING FLASHING —",
    "   CAPILLARY CUT.",
    "5. BACKFILL FREE-DRAINING GRAVEL,",
    "   SLOPE GRADE AWAY 5%.",
    "6. CURB BETWEEN PIERS: 200x250,",
    "   THICKENED EDGE 300 DEEP, (2) #4",
    "   CONT — FLOATS INDEPENDENT OF",
    "   PIER FTGS (HEAVE ISOLATION).",
], 17, 26)
s.save("S3_foundation.svg", 3, TOTAL)

# =============================================================================
# S-4 — pier details, 1:10
# =============================================================================
s = Sheet("S-4", "PIER — BATTER + CAP DETAILS", "1:10")
sc = 4 / 10.0
ox, oy = 470, 980


def X4(mm):
    return ox + mm * sc


def Y4(mm):
    return oy - mm * sc


s.line(X4(-600), oy, X4(600), oy, 2.5)
s.rect(X4(-P["plinth_w"] / 2), Y4(P["plinth_h"]), P["plinth_w"] * sc, P["plinth_h"] * sc, sw=2)
s.poly([(X4(-P["shaft_base"] / 2), Y4(P["plinth_h"])), (X4(P["shaft_base"] / 2), Y4(P["plinth_h"])),
        (X4(P["shaft_top"] / 2), Y4(P["plinth_h"] + P["shaft_h"])), (X4(-P["shaft_top"] / 2), Y4(P["plinth_h"] + P["shaft_h"]))])
s.rect(X4(-P["cap1_w"] / 2), Y4(P["plinth_h"] + P["shaft_h"] + P["cap1_h"]), P["cap1_w"] * sc, P["cap1_h"] * sc, sw=2)
s.rect(X4(-P["cap2_w"] / 2), Y4(P["plinth_h"] + P["shaft_h"] + P["cap1_h"] + P["cap2_h"]), P["cap2_w"] * sc, P["cap2_h"] * sc, sw=2)
s.poly([(X4(-P["pyr_base"] / 2), Y4(PIER_TOP - P["pyr_h"])), (X4(P["pyr_base"] / 2), Y4(PIER_TOP - P["pyr_h"])),
        (X4(P["pyr_top"] / 2), Y4(PIER_TOP)), (X4(-P["pyr_top"] / 2), Y4(PIER_TOP))])

# batter callout
s.line(X4(P["shaft_base"] / 2), Y4(P["plinth_h"]), X4(P["shaft_base"] / 2), Y4(P["plinth_h"] + P["shaft_h"]), 1.2, ACC, dash="8 5")
s.text(X4(P["shaft_base"] / 2) + 46, Y4(P["plinth_h"] + 780), "BATTER 60/1600 = 1:26.7 PER FACE (EGYPTIAN TALUS)", 15, ACC, rot=-90)

# rail pockets
for zc in P["rail_z"]:
    s.rect(X4(P["shaft_base"] / 2 - 40) - P["pocket_depth"] * sc, Y4(zc + (P["rail_w"] + 6) / 2), P["pocket_depth"] * sc + 40 * sc, (P["rail_w"] + 6) * sc, stroke=ACC, sw=1.4, dash="8 4")
    s.text(X4(P["shaft_base"] / 2) + 12, Y4(zc) + 5, f"POCKET CL {zc}", 13, ACC)

# dims
s.dim_h(X4(-P["shaft_base"] / 2), X4(P["shaft_base"] / 2), oy + 30, "480 [19\"]", 14)
s.dim_h(X4(-P["shaft_top"] / 2), X4(P["shaft_top"] / 2), Y4(P["plinth_h"] + P["shaft_h"]) - 24, "360 [14.2\"]", -18)
s.dim_v(Y4(P["plinth_h"]), oy, X4(-P["plinth_w"] / 2) - 60, "150", -36)
s.dim_v(Y4(P["plinth_h"] + P["shaft_h"]), Y4(P["plinth_h"]), X4(-P["plinth_w"] / 2) - 130, "1600 [63\"]", -46)
s.dim_v(Y4(PIER_TOP), Y4(P["plinth_h"] + P["shaft_h"]), X4(-P["plinth_w"] / 2) - 60, "215", -36)

# cap detail inset, 1:4
s.text(1050, 220, "CAP EDGE DETAIL — 1:4", 18, INK, bold=True)
dsc = 1.0
dx, dy = 1100, 260
# tier 1 edge w/ drip kerf
s.poly([(dx, dy + 90), (dx + 240, dy + 90), (dx + 240, dy + 40), (dx + 190, dy + 40), (dx + 190, dy), (dx, dy)], close=False)
s.add(f"<circle cx='{dx+215}' cy='{dy+78}' r='7' fill='none' stroke='{ACC}' stroke-width='2'/>")
s.line(dx + 215, dy + 85, dx + 215, dy + 90, 2, ACC)
s.text(dx + 250, dy + 60, "DRIP KERF 8x8 — 20 FROM EDGE,", 15, ACC)
s.text(dx + 250, dy + 84, "ALL 4 SIDES, TIERS 1 + 2", 15, ACC)
s.text(dx, dy + 130, "ALL CAP TOPS: 1:12 WASH MIN TO SHED —", 15, DIM)
s.text(dx, dy + 154, "PYRAMID TOP SELF-SHEDS (MAYAN CORBEL STACK)", 15, DIM)

s.note(1050, 480, [
    "PIER CONSTRUCTION OPTIONS",
    "A. CAST STONE UNITS (SHOWN):",
    "   3 BATTERED DRUMS + 3 CAP UNITS,",
    "   EPOXY DOWELS #4, TYPE S MORTAR.",
    "B. CMU CORE + LIMESTONE VENEER:",
    "   200 CMU GROUTED SOLID W/ (4)#4,",
    "   ANCHORS @ 400 EW.",
    "C. SOLID LOCAL LIMESTONE (ONONDAGA):",
    "   THE 500-YEAR VERSION. DRY-FIT,",
    "   LEAD OR MORTAR SET.",
    "",
    "MASS RULE (OLD WORLD): PIER SELF-",
    "WEIGHT >= 3x PANEL WIND REACTION.",
    "BATTER MOVES THE RESULTANT INSIDE",
    "THE MIDDLE THIRD — NO TENSION AT",
    "ANY BED JOINT.",
], 17, 26)
s.save("S4_pier.svg", 4, TOTAL)

# =============================================================================
# S-5 — arch gate, 1:15
# =============================================================================
s = Sheet("S-5", "ROMAN ARCH GATE", "1:15")
sc = 4 / 15.0
ox, oy = 560, 960


def X5(mm):
    return ox + mm * sc


def Y5(mm):
    return oy - mm * sc


gc_m = 0.0
s.line(X5(-1800), oy, X5(1800), oy, 2.5)
for sgn in (-1, 1):
    cx = sgn * (P["gate_clear"] / 2 + P["shaft_base"] / 2)
    x = X5(cx)
    zp = Y5(P["plinth_h"])
    s.rect(x - P["plinth_w"] / 2 * sc, zp, P["plinth_w"] * sc, P["plinth_h"] * sc)
    s.poly([(x - P["shaft_base"] / 2 * sc, zp), (x + P["shaft_base"] / 2 * sc, zp),
            (x + P["shaft_top"] / 2 * sc, Y5(P["plinth_h"] + P["shaft_h"])), (x - P["shaft_top"] / 2 * sc, Y5(P["plinth_h"] + P["shaft_h"]))])
    s.rect(x - P["impost_w"] / 2 * sc, Y5(SPRING), P["impost_w"] * sc, P["impost_h"] * sc)

r_in = P["gate_clear"] / 2 * sc
r_out = (P["gate_clear"] / 2 + P["arch_depth"]) * sc
ys = Y5(SPRING)
gx = X5(gc_m)
s.add(f"<path d='M {gx-r_out:.1f} {ys:.1f} A {r_out:.1f} {r_out:.1f} 0 0 1 {gx+r_out:.1f} {ys:.1f}' fill='none' stroke='{INK}' stroke-width='2.4'/>")
s.add(f"<path d='M {gx-r_in:.1f} {ys:.1f} A {r_in:.1f} {r_in:.1f} 0 0 1 {gx+r_in:.1f} {ys:.1f}' fill='none' stroke='{INK}' stroke-width='2.4'/>")

# voussoir joints — 11 radial lines
import math
NV = 11
for i in range(NV + 1):
    a = math.pi - i * math.pi / NV
    x1, y1 = gx + r_in * math.cos(a), ys - r_in * math.sin(a)
    x2, y2 = gx + r_out * math.cos(a), ys - r_out * math.sin(a)
    s.line(x1, y1, x2, y2, 1.4)
# keystone
s.poly([(gx - P["key_b"] / 2 * sc, Y5(SPRING + P["gate_clear"] / 2 + P["arch_depth"] - P["key_h"] + 60)),
        (gx + P["key_b"] / 2 * sc, Y5(SPRING + P["gate_clear"] / 2 + P["arch_depth"] - P["key_h"] + 60)),
        (gx + P["key_t"] / 2 * sc, Y5(CROWN + 60)), (gx - P["key_t"] / 2 * sc, Y5(CROWN + 60))], sw=2.2)
s.text(gx, Y5(CROWN + 60) - 12, "KEYSTONE — PROUD 30 EA FACE", 15, ACC, "middle")

# springline + radius callouts
s.line(X5(-1500), ys, X5(1500), ys, 1.2, DIM, dash="10 6")
s.text(X5(-1480), ys - 8, "SPRINGLINE 1810 [71.3\"]", 14, DIM)
s.line(gx, ys, gx + r_in * math.cos(math.pi * 0.75), ys - r_in * math.sin(math.pi * 0.75), 1.4, ACC)
s.text(gx - r_in * 0.62, ys - r_in * 0.48, "R610 INTRADOS", 15, ACC)
s.dim_h(X5(-P["gate_clear"] / 2), X5(P["gate_clear"] / 2), oy + 46, "1220 [48\"] CLEAR", 22)
s.dim_v(Y5(CROWN), oy, X5(1420), "2640 CROWN", 30)

# leaf
lx = X5(-P["gate_clear"] / 2 + 25)
lw = (P["gate_clear"] - 50) * sc
s.rect(lx, Y5(150 + 1600), lw, 1600 * sc, sw=1.6)
for zl in (150 + 40, 150 + 800 - 22, 150 + 1600 - 45 - 40):
    s.rect(lx + 14, Y5(zl + 45), lw - 28, 45 * sc, sw=1)
s.line(lx + 14, Y5(150 + 40 + 45), lx + lw - 14, Y5(150 + 1600 - 85), 1.4, INK)
s.text(gx, Y5(800), "LEDGED + BRACED CEDAR LEAF", 14, DIM, "middle")
s.text(gx, Y5(720), "BRACE RISES FROM HINGE SIDE", 14, DIM, "middle")

s.note(1150, 240, [
    "ARCH NOTES (ROMAN PRACTICE)",
    "1. 11 CAST-STONE VOUSSOIRS + KEY.",
    "   RADIAL JOINTS 10 MORTAR TYPE S.",
    "2. BUILD ON TIMBER CENTERING; DO",
    "   NOT STRIKE UNTIL MORTAR CURED",
    "   7 DAYS MIN.",
    "3. ARCH BEARS ON IMPOSTS ONLY —",
    "   PURE COMPRESSION. NO STEEL",
    "   NEEDED; SS DOWELS AT IMPOSTS",
    "   FOR ERECTION ONLY.",
    "4. CROWN 2640 — CHECK BUFFALO",
    "   GATE/ARBOR HEIGHT ALLOWANCE.",
    "5. HINGES: SS BALL-BEARING, M12",
    "   EPOXY ANCHORS INTO PIER — 100",
    "   EDGE DIST MIN.",
    "6. LEAF SWINGS INWARD, CLEAR OF",
    "   SNOW BERM AT THRESHOLD.",
], 17, 26)
s.save("S5_arch_gate.svg", 5, TOTAL)

print("All sheets written to", OUT)
