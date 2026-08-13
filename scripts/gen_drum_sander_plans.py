#!/usr/bin/env python3
"""Generate WALTER DS-16 build-plan SVG sheets (A3 landscape, printable).

Dimensions mirror shop/drum-sander/cad/walter_ds16.py.
Run:  python3 scripts/gen_drum_sander_plans.py
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "shop", "drum-sander", "cad"))
from walter_ds16 import GEOM as G  # noqa: E402
from walter_ds16 import SPEC as S  # noqa: E402

OUT = os.path.join(ROOT, "shop", "drum-sander", "plans")
os.makedirs(OUT, exist_ok=True)

W, Hpx = 1680, 1188  # A3 landscape @ ~4 px/mm
INK, DIM, ACC, PAPER, LIGHT = "#1a1f24", "#5a6a4a", "#3d5a4c", "#f3f1ec", "#c5c8c2"
GRAY = "#6e7578"
STEEL = "#8a9098"
WOOD = "#c4a574"
MDF = "#b8a990"
MONO = "font-family='IBM Plex Mono, Menlo, monospace'"
SER = "font-family='Georgia, serif'"


def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Sheet:
    def __init__(self, code: str, title: str, scale_note: str):
        self.code, self.title, self.scale_note = code, title, scale_note
        self.b: list[str] = []

    def add(self, s: str) -> None:
        self.b.append(s)

    def line(self, x1, y1, x2, y2, w=2, color=INK, dash=None):
        d = f" stroke-dasharray='{dash}'" if dash else ""
        self.add(
            f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' "
            f"stroke='{color}' stroke-width='{w}'{d}/>"
        )

    def rect(self, x, y, w, h, fill="none", stroke=INK, sw=2, dash=None, rx=0):
        d = f" stroke-dasharray='{dash}'" if dash else ""
        r = f" rx='{rx}'" if rx else ""
        self.add(
            f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' "
            f"fill='{fill}' stroke='{stroke}' stroke-width='{sw}'{d}{r}/>"
        )

    def circle(self, cx, cy, r, fill="none", stroke=INK, sw=2):
        self.add(
            f"<circle cx='{cx:.1f}' cy='{cy:.1f}' r='{r:.1f}' "
            f"fill='{fill}' stroke='{stroke}' stroke-width='{sw}'/>"
        )

    def ellipse(self, cx, cy, rx, ry, fill="none", stroke=INK, sw=2):
        self.add(
            f"<ellipse cx='{cx:.1f}' cy='{cy:.1f}' rx='{rx:.1f}' ry='{ry:.1f}' "
            f"fill='{fill}' stroke='{stroke}' stroke-width='{sw}'/>"
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
            ww = len(s) * size * 0.58
            bx = {"start": x - 4, "middle": x - ww / 2 - 4, "end": x - ww - 4}[anchor]
            self.add(
                f"<rect x='{bx:.1f}' y='{y - size:.1f}' width='{ww + 8:.1f}' "
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
        for x, sgn in ((x1, 1), (x2, -1)):
            self.poly(
                [(x, yy), (x + sgn * 10, yy - 4), (x + sgn * 10, yy + 4)],
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
        for y, sgn in ((y1, 1), (y2, -1)):
            self.poly(
                [(xx, y), (xx - 4, y + sgn * 10), (xx + 4, y + sgn * 10)],
                fill=DIM,
                stroke=DIM,
                sw=0.5,
            )
        self.text(
            xx + (12 if offset >= 0 else -12),
            (y1 + y2) / 2 + 5,
            label,
            size,
            DIM,
            "start" if offset >= 0 else "end",
            bg=True,
            rot=-90,
        )

    def titleblock(self):
        self.rect(0, 0, W, Hpx, fill=PAPER, stroke=INK, sw=3)
        self.rect(24, 24, W - 48, Hpx - 48, fill="none", stroke=INK, sw=1.2)
        self.line(24, Hpx - 90, W - 24, Hpx - 90, 1.5, INK)
        self.text(40, Hpx - 58, "WALTER", 28, ACC, bold=True, mono=False)
        self.text(170, Hpx - 62, f"{self.code}  ·  {self.title}", 18, INK, bold=True)
        self.text(40, Hpx - 34, self.scale_note, 13, DIM)
        self.text(W - 40, Hpx - 58, "DS-16 · Dedicated drum thickness sander", 14, DIM, "end")
        self.text(
            W - 40,
            Hpx - 34,
            "ShopNotes 86 → Walters → Rev B geometry · fab B.2 (individual part sheets)",
            13,
            DIM,
            "end",
        )

    def save(self, filename: str):
        path = os.path.join(OUT, filename)
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


def sheet_d1():
    s = Sheet("D-1", "General arrangement", "Scale ~1:8 · inches · overall machine")
    s.titleblock()
    s.text(40, 70, "SIDE ELEVATION — drive side", 16, ACC, bold=True)
    s.text(
        40,
        94,
        f'{S.capacity_width}" capacity · ⌀{S.drum_od}" drum @ ~{S.drum_rpm:g} RPM · '
        f'{S.motor_hp:g} HP {S.motor_rpm:g} RPM · solid sliding table (no conveyor)',
        14,
        DIM,
    )

    # Side view geometry
    sc = 18.0
    ox, oy = 80, 920  # origin: floor / front-left of base

    def X(xin):
        return ox + xin * sc

    def Y(zin):
        return oy - zin * sc

    # Base / sides
    s.rect(X(0), Y(S.side_height), S.side_depth * sc, S.side_height * sc, fill=WOOD, stroke=INK, sw=1.8)
    # Table
    table_z = G.table_z_display
    s.rect(
        X(1),
        Y(table_z + G.table_thick),
        G.table_depth * sc,
        G.table_thick * sc,
        fill=LIGHT,
        stroke=INK,
        sw=1.5,
    )
    s.text(X(G.table_depth / 2 + 1), Y(table_z + G.table_thick / 2) + 5, "TABLE", 12, DIM, "middle")
    # Drum
    drum_cx, drum_cz = G.bearing_cl_y, G.bearing_cl_z
    s.circle(X(drum_cx), Y(drum_cz), (S.drum_od / 2) * sc, fill=MDF, stroke=INK, sw=2)
    s.circle(X(drum_cx), Y(drum_cz), 4, fill=STEEL, stroke=INK, sw=1)
    s.text(X(drum_cx), Y(drum_cz) - S.drum_od / 2 * sc - 12, "DRUM ⌀5\"", 13, ACC, "middle", bold=True)
    # Hood arc hint
    s.ellipse(
        X(drum_cx),
        Y(drum_cz),
        (S.drum_od / 2 + 1.2) * sc,
        (S.drum_od / 2 + 1.5) * sc,
        fill="none",
        stroke=ACC,
        sw=1.5,
    )
    s.text(X(drum_cx + 4), Y(drum_cz + 4), "HOOD", 12, ACC)
    # Motor
    s.rect(X(3), Y(8), 8 * sc, 6 * sc, fill=GRAY, stroke=INK, sw=1.5)
    s.text(X(7), Y(5) + 5, "MOTOR ½ HP", 12, PAPER, "middle", bold=True)
    s.circle(X(7), Y(8), 1.5 * sc, fill="none", stroke=STEEL, sw=2)  # pulley hint
    # Elev screw
    s.line(X(18), Y(table_z), X(18), Y(4), 2, STEEL)
    s.text(X(18.4), Y(9), "ELEV", 11, DIM)

    s.dim_h(X(0), X(S.side_depth), Y(0), f'{S.side_depth}" DEPTH', offset=36)
    s.dim_v(Y(0), Y(S.side_height), X(0), f'{S.side_height}"', offset=-40)

    # Front mini
    s.text(780, 70, "FRONT ELEVATION", 16, ACC, bold=True)
    fx, fy = 820, 520
    fs = 14.0
    span = S.clear_between_sides
    # sides
    s.rect(fx, fy - S.side_height * fs * 0.55, G.side_thick * fs, S.side_height * fs * 0.55, fill=WOOD, stroke=INK)
    s.rect(
        fx + (span + G.side_thick) * fs,
        fy - S.side_height * fs * 0.55,
        G.side_thick * fs,
        S.side_height * fs * 0.55,
        fill=WOOD,
        stroke=INK,
    )
    # drum as rectangle (end view is circle already; here cylinder face)
    drum_w = G.drum_length * fs
    s.rect(
        fx + G.side_thick * fs + (span * fs - drum_w) / 2,
        fy - 280,
        drum_w,
        S.drum_od * fs,
        fill=MDF,
        stroke=INK,
        sw=1.5,
    )
    s.rect(
        fx + G.side_thick * fs,
        fy - 200,
        span * fs,
        G.table_thick * fs,
        fill=LIGHT,
        stroke=INK,
    )
    s.dim_h(
        fx + G.side_thick * fs,
        fx + G.side_thick * fs + span * fs,
        fy - 40,
        f'{span}" CLEAR / {S.capacity_width}" WORK',
        offset=20,
    )

    notes = [
        "LINEAGE: ShopNotes 86 → Walters → Rev A solid table → Rev B geometry.",
        "FEED: Table in UHMW ways + spring hold-downs. Conveyor still deleted.",
        "LIFT: Dual ½-10 Acme, chain-coupled. Left uncouples for taper; home dog.",
        "DRIVE: 3″ / 5″ pulleys → ~1035 RPM · ~1350 sfpm. Pulley faces coplanar.",
        "DRUM: Pack-bored discs · floating idler bearing · true, then wrap, then re-clock.",
        "QUALITY: |A−B| ≤ 0.003″ paper-on · TIR ≤ 0.002″ · 0.001″ finish passes.",
        "SAFETY: Hood is a guard. Hold-downs on. Never open while spinning.",
    ]
    for i, n in enumerate(notes):
        s.text(780, 560 + i * 26, n, 13, INK)

    s.save("D1_general.svg")


def sheet_d2():
    s = Sheet("D-2", "Frame & table", "Scale ~1:6 · Baltic birch structure")
    s.titleblock()
    s.text(40, 70, "SIDE PANEL — layout (stack-drill as a pair, then split)", 16, ACC, bold=True)

    sc = 22.0
    ox, oy = 60, 780

    def X(v):
        return ox + v * sc

    def Y(v):
        return oy - v * sc

    s.rect(X(0), Y(S.side_height), S.side_depth * sc, S.side_height * sc, fill=WOOD, stroke=INK, sw=2)
    # bearing center
    bx, bz = G.bearing_cl_y, G.bearing_cl_z
    s.circle(X(bx), Y(bz), 1.1 * sc, fill="none", stroke=ACC, sw=2)
    s.circle(X(bx), Y(bz), 0.375 * sc, fill=STEEL, stroke=INK)
    s.text(X(bx) + 30, Y(bz), "FLANGE BEARING CL", 12, ACC)
    # UHMW way
    s.rect(X(1.5), Y(S.way_z + S.way_stock), (S.side_depth - 3) * sc, S.way_stock * sc, fill=LIGHT, stroke=ACC, sw=1.5)
    s.text(X(10.5), Y(S.way_z + S.way_stock + 0.4), f"P-007 WAY  rebate {G.way_rebate:.3f}\"  project {G.way_project:.3f}\"", 11, ACC, "middle", bold=True)
    s.circle(X(G.acme_y_infeed), Y(12), 0.25 * sc, fill="none", stroke=STEEL, sw=1.5)
    s.circle(X(G.acme_y_outfeed), Y(12), 0.25 * sc, fill="none", stroke=STEEL, sw=1.5)
    s.text(X(G.acme_y_infeed), Y(10.6), "L ACME", 10, STEEL, "middle")
    s.text(X(G.acme_y_outfeed), Y(10.6), "R ACME", 10, STEEL, "middle")
    # motor pivot
    s.circle(X(4), Y(6), 0.4 * sc, fill="none", stroke=GRAY, sw=1.5)
    s.text(X(4), Y(4.5), "MOTOR PIVOT", 11, DIM, "middle")

    s.dim_h(X(0), X(S.side_depth), Y(0), f'{S.side_depth}"', offset=40)
    s.dim_v(Y(0), Y(S.side_height), X(0), f'{S.side_height}"', offset=-36)
    s.dim_h(X(0), X(bx), Y(S.side_height), f'{bx:g}"', offset=-28)
    s.dim_v(Y(0), Y(bz), X(S.side_depth), f'{bz:g}"', offset=36)

    # Table detail
    s.text(900, 70, "TABLE — TORSION BOX + WEAR FACE", 16, ACC, bold=True)
    s.rect(920, 120, 280, 36, fill=STEEL, stroke=INK, sw=1.5)
    s.text(1060, 143, "WEAR: PHENOLIC / MIC-6", 12, PAPER, "middle", bold=True)
    s.rect(920, 156, 280, 36, fill=WOOD, stroke=INK, sw=1.5)
    s.text(1060, 179, '¾" SKIN A', 12, INK, "middle")
    s.rect(920, 192, 280, 28, fill=MDF, stroke=INK, sw=1.2, dash="4 3")
    s.text(1060, 211, '½" RIBS @ 4" O.C. — FULL GLUE', 11, INK, "middle")
    s.rect(920, 220, 280, 36, fill=WOOD, stroke=INK, sw=1.5)
    s.text(1060, 243, '¾" SKIN B', 12, INK, "middle")
    s.text(920, 280, f'{G.table_width}" W × {G.table_depth}" D · flatness ≤ {S.table_flat_tol:.3f}" diag.', 13, DIM)

    s.text(900, 330, "DUAL-END LIFT (Rev B)", 16, ACC, bold=True)
    rows = [
        ("Screws", "Two ½″-10 Acme × 12″ + bronze nuts"),
        ("Couple", "#25 chain · both screws turn together"),
        ("Taper", "Uncouple LEFT sprocket · then recouple"),
        ("Home", "Dog stop = last known parallel"),
        ("Ways", f"J-002 rebate {G.way_rebate:.3f}″ · project {G.way_project:.3f}″"),
        ("Travel", f'{S.elev_travel}" · 1/{S.acme_tpi:g} turn ≈ {G.acme_per_turn:.4f}″'),
    ]
    yy = 368
    for a, b in rows:
        s.text(920, yy, a, 13, DIM, bold=True)
        s.text(1040, yy, b, 13, INK)
        yy += 26

    s.text(40, 860, "STRETCHERS — 3× between sides  ·  STACK-DRILL SIDES AS A PAIR", 16, ACC, bold=True)
    s.text(
        40,
        890,
        f'Front / mid / rear: P-003  {G.stretcher_length:g}" × {S.stretcher_height:g}" × {G.side_thick:g}"  housed {S.stretcher_housing:g}" each end (J-001). Ways — not stretchers — locate the table.',
        14,
        INK,
    )
    s.text(
        40,
        920,
        "Idler flange is FLOATING (axial slots). Drive flange is FIXED. Over-constraining both bearings bananas the shaft.",
        14,
        INK,
    )

    s.save("D2_frame.svg")


def sheet_d3():
    s = Sheet("D-3", "Drum & shaft", "Scale ~1:3 · drum stack detail")
    s.titleblock()
    s.text(40, 70, "DRUM ASSEMBLY — exploded stack", 16, ACC, bold=True)
    s.text(
        40,
        94,
        f'{S.disc_count_core} core discs + {S.disc_count_ends} BB ends · ⌀{S.drum_od}" × {G.drum_length}" · '
        f'precision ⌀{S.shaft_od}" shaft {S.shaft_length}" long',
        14,
        DIM,
    )

    # Shaft line
    s.line(80, 400, 1500, 400, 3, STEEL)
    s.text(80, 380, "SHAFT →", 14, STEEL, bold=True)

    # Discs
    x0 = 200
    n = 12  # draw representative
    dw = 40
    for i in range(n):
        fill = WOOD if i in (0, n - 1) else MDF
        s.rect(x0 + i * (dw + 8), 280, dw, 240, fill=fill, stroke=INK, sw=1.5)
        if i > 0 and i % 3 == 0:
            s.rect(x0 + i * (dw + 8) - 6, 280, 4, 240, fill=PAPER, stroke=ACC, sw=1)
    s.text(x0, 550, "BB END", 12, ACC, bold=True)
    s.text(x0 + 5 * (dw + 8), 550, "MDF / BB CORE  (+ 1 mm relief every 4)", 12, DIM)
    s.text(x0 + (n - 1) * (dw + 8), 550, "BB END", 12, ACC, bold=True)

    # Pulley
    s.circle(1580 - 60, 400, 55, fill=GRAY, stroke=INK, sw=2)
    s.text(1580 - 60, 480, '5" PULLEY', 12, DIM, "middle")

    # Bearing boxes
    for bx, lab in ((160, "DRIVE FIXED"), (1380, "IDLER FLOAT")):
        s.rect(bx, 330, 50, 140, fill=STEEL, stroke=INK, sw=1.5)
        s.text(bx + 25, 500, lab, 11, ACC, "middle", bold=True)
    s.text(1180, 540, "axial slots — do not lock both", 12, ACC)

    s.text(40, 620, "KEYING & GLUE", 16, ACC, bold=True)
    bullets = [
        f"Cross-drill shaft; drive {S.key_wire_od}\" piano wire stubs so discs cannot spin on shaft.",
        "Laminate with polyurethane or waterproof PVA; clamp axially while curing.",
        "MDF option: 1 mm cardboard/plastic relief every 4 discs — prevents glue-swell cracks (Walters/Wandel).",
        "Birch option: all Baltic birch discs — heavier, more stable (Heslop preference after MDF roller issues).",
        "Pack-bore all discs in a jig (not one-at-a-time) so the bore is coaxial. Static-balance end discs.",
        "True OD on the full-width sled that rides the ways (TIR ≤ 0.002″). THEN wrap paper. THEN re-clock A/B.",
        f"Wrap {S.velcro_width}\" hook Velcro; spiral {S.sandpaper_width}\" loop paper. Paper thickness is not uniform — expect A/B to move.",
    ]
    for i, b in enumerate(bullets):
        s.text(40, 660 + i * 28, "•  " + b, 14, INK)

    s.text(40, 860, "DRIVE MATH", 16, ACC, bold=True)
    s.text(
        40,
        890,
        f"RPM_drum = {S.motor_rpm:g} × ({S.pulley_motor_od:g}/{S.pulley_drum_od:g}) ≈ {S.drum_rpm:g} RPM   ·   "
        f"Surface ≈ π × {S.drum_od:g}/12 × {S.drum_rpm:g} ≈ 1,350 sfpm",
        14,
        INK,
    )
    s.text(
        40,
        920,
        "Walters ran ~1100 RPM with a ~4.75″ drum pulley. Either ratio is fine; keep belt aligned and locked.",
        14,
        DIM,
    )

    s.save("D3_drum.svg")


def sheet_d4():
    s = Sheet("D-4", "Drive & elevation", "Motor cradle · belt path · table lift")
    s.titleblock()
    s.text(40, 70, "MOTOR CRADLE — gravity tension + lock", 16, ACC, bold=True)

    # Schematic
    s.rect(80, 140, 220, 160, fill=GRAY, stroke=INK, sw=2)
    s.text(190, 220, "MOTOR", 16, PAPER, "middle", bold=True)
    s.circle(190, 360, 40, fill="none", stroke=STEEL, sw=3)
    s.text(190, 420, '3" PULLEY', 12, DIM, "middle")
    s.line(230, 360, 520, 200, 3, STEEL)
    s.text(360, 260, "V-BELT", 12, STEEL)
    s.circle(560, 180, 60, fill=MDF, stroke=INK, sw=2)
    s.text(560, 280, '5" DRUM PULLEY', 12, DIM, "middle")
    s.circle(120, 380, 12, fill=ACC, stroke=INK)
    s.text(120, 460, "PIVOT DOWEL", 12, ACC, "middle", bold=True)
    s.line(280, 200, 280, 120, 2, ACC, dash="4 3")
    s.text(300, 140, "LOCK SCREW — set after tension", 13, ACC)

    notes = [
        "Hang motor so weight tensions the belt (Walters).",
        "After tension is right, lock the cradle — running belts pump a free hinge (Wandel).",
        "Keep pulley faces coplanar; misalignment eats belts and throws vibration.",
        "Use a switch box on the frame — no dangling cords across the feed path.",
    ]
    for i, n in enumerate(notes):
        s.text(700, 140 + i * 32, "•  " + n, 14, INK)

    s.text(40, 520, "DUAL ACME LIFT — chain couple", 16, ACC, bold=True)
    s.rect(80, 560, 480, 28, fill=LIGHT, stroke=INK)
    s.text(320, 580, "TABLE IN UHMW WAYS", 12, DIM, "middle")
    s.line(160, 588, 160, 780, 4, STEEL)
    s.line(480, 588, 480, 780, 4, STEEL)
    s.rect(130, 720, 60, 36, fill=WOOD, stroke=INK)
    s.rect(450, 720, 60, 36, fill=WOOD, stroke=INK)
    s.text(160, 742, "L", 12, INK, "middle", bold=True)
    s.text(480, 742, "R", 12, INK, "middle", bold=True)
    s.line(190, 738, 450, 738, 2, ACC)
    s.text(320, 728, "#25 CHAIN", 11, ACC, "middle")
    s.circle(160, 700, 14, fill="none", stroke=ACC, sw=2)
    s.text(160, 670, "CLUTCH", 10, ACC, "middle")

    elev = [
        "Both screws turn together → table stays coplanar while rising.",
        "Uncouple LEFT only to correct |A−B| or to sand a taper.",
        "Set the home dog at the last known parallel — return without re-indicating.",
        "1/40 turn of ½-10 Acme ≈ 0.0025″ at that end.",
        "Ways take feed load. Screws take elevation. Do not mix those jobs.",
        "Light contact only. Finish passes 0.001″. This is not a planer.",
    ]
    for i, e in enumerate(elev):
        s.text(700, 540 + i * 30, f"{i + 1}.  {e}", 14, INK)

    s.text(40, 860, "PULLEY COPLANAR + FLOATING IDLER", 16, ACC, bold=True)
    s.text(
        40,
        895,
        "Straightedge across both pulley faces before locking the motor cradle. Axial-float the idler flange so the shaft is not a three-force beam.",
        14,
        INK,
    )
    s.text(
        40,
        925,
        "Oak locator blocks under both bearings so the drum returns to the same seat after removal — then re-check TIR, not just seat marks.",
        14,
        INK,
    )

    s.save("D4_drive.svg")


def sheet_d5():
    s = Sheet("D-5", "Dust hood & safety", "Kerf-bent guard · 4″ extraction")
    s.titleblock()
    s.text(40, 70, "DUST HOOD — kerf-bent ¼″ ply (Walters method)", 16, ACC, bold=True)

    # Hood profile
    s.poly(
        [
            (120, 420),
            (200, 200),
            (480, 140),
            (760, 200),
            (840, 420),
            (760, 480),
            (200, 480),
        ],
        fill=LIGHT,
        stroke=INK,
        sw=2,
    )
    s.circle(480, 340, 90, fill=MDF, stroke=INK, sw=1.5)
    s.text(480, 345, "DRUM", 12, INK, "middle", bold=True)
    s.circle(780, 180, 35, fill="none", stroke=ACC, sw=2)
    s.text(780, 120, '4" PORT', 13, ACC, "middle", bold=True)

    steps = [
        "Cut ¼″ pine/birch blank oversized for the drum arc.",
        "Kerf halfway through on the inside face — model-airplane style.",
        "Wet the outside face; wood cups toward the kerfs.",
        "Glue onto a form; clamp with sandbags / bands until dry.",
        "Fill kerfs with sawdust + glue; wipe smooth; sand; finish.",
        "Fit snug over the sides — paraffin on paint rubs for easy removal.",
        "Port to 4″ hose (Walters preferred 4″ over 3″ for this machine).",
    ]
    for i, st in enumerate(steps):
        s.text(920, 140 + i * 36, f"{i + 1}.  {st}", 14, INK)

    s.text(40, 560, "SAFETY RULES", 16, ACC, bold=True)
    rules = [
        "Hood ON = primary guard. Open hood only when drum is stopped and unplugged.",
        "Hands never under the drum. Use push sticks; minimum stock length ~12″.",
        "Small parts: adhere to a longer sled. Kickback risk is real (Heslop).",
        "Not a planer — multiple light passes. Listen for motor bog; back off.",
        "Stay off paint/finish with the drum paper — loads and burns grit.",
        "Eye + hearing + respirator when truing MDF or running without full extraction.",
        "Disconnect power before paper changes, bearing work, or belt service.",
    ]
    for i, r in enumerate(rules):
        s.text(40, 600 + i * 30, "▸  " + r, 14, INK)

    s.save("D5_hood.svg")


def sheet_d6():
    s = Sheet("D-6", "Cut list & BOM", "Shopping · hardware · sequence")
    s.titleblock()
    s.text(40, 70, "PLYWOOD / LUMBER CUT LIST", 16, ACC, bold=True)

    from walter_ds16 import cut_list, hardware_bom, assembly_phases

    yy = 108
    s.text(40, yy, "ID", 11, DIM, bold=True)
    s.text(110, yy, "QTY", 11, DIM, bold=True)
    s.text(160, yy, "FINISHED", 11, DIM, bold=True)
    s.text(520, yy, "STOCK", 11, DIM, bold=True)
    s.text(720, yy, "PART", 11, DIM, bold=True)
    yy += 20
    for row in cut_list():
        s.text(40, yy, row["part_id"], 11, ACC, bold=True)
        s.text(110, yy, str(row["qty"]), 11, INK)
        s.text(160, yy, row["size"][:38], 11, INK)
        s.text(520, yy, row["stock"][:18], 11, INK)
        s.text(720, yy, row["use"][:42], 11, INK)
        yy += 18

    s.text(40, yy + 12, "HARDWARE (hold-down / oscillator detail on D-8)", 16, ACC, bold=True)
    yy += 38
    for row in hardware_bom()[:10]:
        s.text(40, yy, row["qty"][:8], 12, ACC, bold=True)
        s.text(110, yy, row["item"][:78], 12, INK)
        yy += 20

    s.text(1100, 70, "BUILD SEQUENCE", 16, ACC, bold=True)
    yy = 108
    for step in assembly_phases():
        s.text(1100, yy, step["id"].upper() + "  " + step["title"][:34], 12, INK, bold=True)
        yy += 26

    s.text(
        40,
        1050,
        "Sources: woodgears.ca/reader/walters/drum_sander.html · YouTube W-5Sj6kBVic · "
        "ShopNotes 86 · Jet/Grizzly parallel & tension-roller practice",
        12,
        DIM,
    )

    s.save("D6_cutlist.svg")


def sheet_d7():
    s = Sheet("D-7", "Geometry & calibration", "Parallelism · coplanarity · indicator protocol")
    s.titleblock()
    s.text(40, 70, "THREE PLANES THAT MAKE THE CUT QUALITY", 16, ACC, bold=True)

    # Table plane box
    s.rect(60, 110, 420, 200, fill=LIGHT, stroke=INK, sw=1.5)
    s.text(270, 145, "1  TABLE PLANE", 14, ACC, "middle", bold=True)
    s.text(80, 180, "Torsion box + wear face", 13, INK)
    s.text(80, 204, f"Flatness ≤ {S.table_flat_tol:.3f}\" on both diagonals", 13, INK)
    s.text(80, 228, "UHMW ways: no twist, no rack", 13, INK)
    s.text(80, 252, "Wear face is the metrology surface", 13, INK)

    s.rect(510, 110, 420, 200, fill=MDF, stroke=INK, sw=1.5)
    s.text(720, 145, "2  DRUM AXIS", 14, ACC, "middle", bold=True)
    s.text(530, 180, f"TIR ≤ {S.drum_tir:.3f}\" paper off", 13, INK)
    s.text(530, 204, "Pack-bore + floating idler", 13, INK)
    s.text(530, 228, "True on ways-riding sled", 13, INK)
    s.text(530, 252, "Re-clock AFTER paper wrap", 13, INK)

    s.rect(960, 110, 420, 200, fill=WOOD, stroke=INK, sw=1.5)
    s.text(1170, 145, "3  FEED VECTOR", 14, ACC, "middle", bold=True)
    s.text(980, 180, "Hold-downs keep stock on plane 1", 13, INK)
    s.text(980, 204, "Ways take thrust; screws take lift", 13, INK)
    s.text(980, 228, "Steady feed = even chip load", 13, INK)
    s.text(980, 252, "Oscillator erases spiral tracks", 13, INK)

    # A/B diagram
    s.text(40, 350, "A / B INDICATOR CLOCK  —  paper ON  —  same indicator, both ends", 16, ACC, bold=True)
    s.rect(80, 380, 520, 80, fill=MDF, stroke=INK)
    s.text(340, 425, "DRUM  (paper on)", 14, INK, "middle", bold=True)
    s.rect(80, 490, 520, 36, fill=LIGHT, stroke=INK)
    s.text(340, 514, "TABLE WEAR FACE", 12, DIM, "middle")
    s.line(120, 380, 120, 560, 1.5, ACC, dash="4 3")
    s.line(560, 380, 560, 560, 1.5, ACC, dash="4 3")
    s.text(120, 580, "A  DRIVE", 13, ACC, "middle", bold=True)
    s.text(560, 580, "B  IDLER", 13, ACC, "middle", bold=True)
    s.text(340, 580, f"|A − B|  ≤  {S.parallel_tol:.3f}\"", 14, INK, "middle", bold=True)

    from walter_ds16 import quality_targets, pass_schedule, calibration_steps

    s.text(700, 350, "QUALITY TARGETS", 16, ACC, bold=True)
    yy = 384
    for row in quality_targets():
        s.text(700, yy, row["check"], 12, INK, bold=True)
        s.text(980, yy, row["spec"], 12, DIM)
        yy += 24

    s.text(40, 640, "CALIBRATION SEQUENCE (unplugged)", 16, ACC, bold=True)
    yy = 672
    for step in calibration_steps():
        s.text(40, yy, step["id"].upper(), 12, ACC, bold=True)
        s.text(90, yy, step["title"] + " — " + step["body"][:88], 12, INK)
        yy += 24

    s.text(40, 900, "PASS SCHEDULE", 16, ACC, bold=True)
    xx = 40
    for p in pass_schedule():
        s.rect(xx, 920, 280, 70, fill=LIGHT, stroke=INK, sw=1)
        s.text(xx + 14, 948, f"{p['grit']} grit  ·  {p['depth']}", 13, ACC, bold=True)
        s.text(xx + 14, 972, p["use"], 12, INK)
        xx += 300

    s.save("D7_geometry.svg")


def sheet_d8():
    s = Sheet("D-8", "Hold-downs & output", "Rollers · truing sled · optional oscillator")
    s.titleblock()
    s.text(40, 70, "SPRING HOLD-DOWN ROLLERS — the snipe / chatter fix", 16, ACC, bold=True)

    # drum + rollers schematic
    s.circle(280, 260, 70, fill=MDF, stroke=INK, sw=2)
    s.text(280, 265, "DRUM", 12, INK, "middle", bold=True)
    s.circle(140, 330, 28, fill=GRAY, stroke=INK, sw=1.5)
    s.circle(420, 330, 28, fill=GRAY, stroke=INK, sw=1.5)
    s.text(140, 390, "INFEED", 12, ACC, "middle", bold=True)
    s.text(420, 390, "OUTFEED", 12, ACC, "middle", bold=True)
    s.rect(80, 358, 400, 16, fill=LIGHT, stroke=INK)
    s.text(280, 430, f"Set rollers {S.roller_setbelow:.3f}\" BELOW drum OD (paper on)", 13, DIM, "middle")

    rules = [
        f"Rollers: ⌀{S.roller_od}\" rubber × ~{G.roller_len}\" on ⅜″ axles, spring yokes.",
        "Light springs. Excess pressure = snipe (same as Jet/Grizzly tension rollers).",
        "Leading-end snipe → ease OUTFEED spring. Trailing-end snipe → ease INFEED.",
        "Stock shorter than 12″ rides a sled that the rollers can still pinch.",
        "Hold-downs keep the board on the table plane — that is coplanarity in use, not just at setup.",
    ]
    for i, r in enumerate(rules):
        s.text(560, 120 + i * 32, "•  " + r, 14, INK)

    s.text(40, 470, "FULL-WIDTH TRUING SLED", 16, ACC, bold=True)
    s.rect(40, 500, 480, 80, fill=MDF, stroke=INK)
    s.text(280, 545, "ABRASIVE FACE-UP  ·  RIDES THE WAYS", 13, INK, "middle", bold=True)
    s.text(40, 610, "True paper-off to 0.002″ TIR. The sled is as wide as the drum so you cannot dish the middle.", 13, INK)

    s.text(560, 470, "OPTIONAL SLOW OSCILLATOR", 16, ACC, bold=True)
    osc = [
        f"Stroke {S.osc_stroke:g}\" at ~{S.osc_cpm:g} cycles/min — NOT drum RPM.",
        "60–90 RPM gearmotor + scotch yoke on the floating idler housing.",
        "Drum RPM axial cam is vibration, not oscillation. Keep them separate.",
        "Erases the helical tracks of a 3″ spiral wrap (the commercial trick).",
        "Belt must tolerate ⅛″ walk — slightly wide pulley or crown.",
        "Hood clearance = stroke + ¼″. Switch osc off for veneer if you want.",
    ]
    for i, o in enumerate(osc):
        s.text(560, 510 + i * 28, "•  " + o, 14, INK)

    s.text(40, 680, "OUTPUT MODES", 16, ACC, bold=True)
    modes = [
        ("THICKNESS", "Home dog in. Hold-downs on. 80→120→180. Caliper 4 corners. Stop at 0.001″ passes."),
        ("TAPER", "Uncouple left. Drop B a few thousandths. Door edges, guitar sides. Return to home dog."),
        ("VENEER", "220 grit, 0.001″, hold-downs, extractor on, optional osc off. Backer sled."),
        ("WIDE / FLIP", "If a panel is wider than 15.5″, leave B ~0.002″ low, flip, overlap — Jet ridge trick."),
        ("CROSS", "Last finish pass: rotate the panel 90° to break remaining tracks."),
    ]
    yy = 716
    for name, body in modes:
        s.text(40, yy, name, 13, ACC, bold=True)
        s.text(180, yy, body, 13, INK)
        yy += 28

    s.text(40, 880, "WHY REV A WAS NOT ENOUGH", 16, ACC, bold=True)
    s.text(40, 912, "One screw + one shimmed bearing can be parallel once. Paper wrap, humidity, and a racking table undo it.", 13, INK)
    s.text(40, 940, "No hold-downs: the board lifts into the drum — snipe and thickness scatter even with a perfect A/B.", 13, INK)
    s.text(40, 968, "Spiral wrap without oscillation: helical grooves. Dual lift + ways + rollers + clocking is the actual quality stack.", 13, INK)

    s.save("D8_holddowns.svg")


def sheet_d10():
    s = Sheet("D-10", "Lumberyard & fasteners", "Store trip · nesting · inch / mm · phone pack")
    s.titleblock()
    from walter_ds16 import fastener_schedule, lumberyard, nest_sheets

    s.text(40, 70, "NEST THE 5′×5′ SHEETS BEFORE YOU BUY — keep 16.5″ (419 mm) inner span", 16, ACC, bold=True)
    s.text(
        40,
        94,
        "Euro 18 mm Baltic birch is the usual ¾″ substitute. Recut sides to actual thickness; do not assume 0.750″.",
        13,
        DIM,
    )

    px = 5.4  # px per inch
    origins = [(40, 120), (400, 120), (760, 120)]
    for sheet, (ox, oy) in zip(nest_sheets(), origins):
        sw, sh = sheet["sheet_w"] * px, sheet["sheet_h"] * px
        s.rect(ox, oy, sw, sh, fill=LIGHT, stroke=INK, sw=1.5)
        s.text(ox, oy - 8, sheet["name"][:42], 11, ACC, bold=True)
        for p in sheet["parts"]:
            x, y = ox + p["x"] * px, oy + p["y"] * px
            w, h = p["w"] * px, p["h"] * px
            fill = WOOD if "Side" in p["label"] or "Skin" in p["label"] else (MDF if "Disc" in p["label"] else PAPER)
            s.rect(x, y, w, h, fill=fill, stroke=INK, sw=0.8)
            if p["w"] >= 8 and "Disc" not in p["label"]:
                s.text(x + w / 2, y + h / 2 + 4, p["label"], 9, INK, "middle")
        s.text(ox, oy + sh + 16, sheet["note"][:52], 10, DIM)

    s.text(40, 500, "LUMBERYARD CARD  (inch / mm)", 16, ACC, bold=True)
    yy = 528
    s.text(40, yy, "WHERE", 11, DIM, bold=True)
    s.text(160, yy, "BUY", 11, DIM, bold=True)
    s.text(720, yy, "QTY", 11, DIM, bold=True)
    s.text(900, yy, "FOR", 11, DIM, bold=True)
    yy += 20
    for row in lumberyard():
        s.text(40, yy, row["where"][:14], 11, ACC, bold=True)
        s.text(160, yy, row["item"][:58], 11, INK)
        s.text(720, yy, row["qty"][:22], 11, INK)
        s.text(900, yy, row["use"][:48], 11, DIM)
        yy += 18

    s.text(40, 720, "HARDWARE AISLE + SPECIALTY  (the list the plywood BOM was missing)", 16, ACC, bold=True)
    yy = 748
    col_x = (40, 860)
    rows = fastener_schedule()
    mid = (len(rows) + 1) // 2
    for col, chunk in enumerate((rows[:mid], rows[mid:])):
        x = col_x[col]
        y = yy
        for row in chunk:
            s.text(x, y, row["qty"][:12], 11, ACC, bold=True)
            s.text(x + 110, y, row["item"][:48], 11, INK)
            s.text(x + 520, y, row["use"][:28], 11, DIM)
            y += 17

    s.text(
        40,
        1050,
        "Phone: /walter/pack → ZIP (Share → Save to Files) · /walter/pocket → field card · Add Build app to Home Screen for offline.",
        12,
        DIM,
    )
    s.save("D10_lumberyard.svg")


def sheet_d11():
    s = Sheet("D-11", "Part register", "Fabrication B.2 · persistent IDs · see IDX + P-sheets")
    s.titleblock()
    from walter_ds16 import parts, datums, nest_yield, GEOM as Gg

    s.text(40, 70, "MAKE / BUY-CUT REGISTER  —  Python SSOT  cad/walter_ds16.py", 16, ACC, bold=True)
    s.text(
        40,
        94,
        f"Inner span {S.clear_between_sides:g}″ · table {Gg.table_width:g}″ · way project {Gg.way_project:.3f}″ / rebate {Gg.way_rebate:.3f}″ · stretcher {Gg.stretcher_length:g}″ housed",
        13,
        DIM,
    )
    yy = 124
    s.text(40, yy, "ID", 11, DIM, bold=True)
    s.text(120, yy, "Q", 11, DIM, bold=True)
    s.text(155, yy, "NAME", 11, DIM, bold=True)
    s.text(520, yy, "FINISHED T×W×L", 11, DIM, bold=True)
    s.text(820, yy, "HAND", 11, DIM, bold=True)
    s.text(980, yy, "JOINERY / DATUM", 11, DIM, bold=True)
    yy += 18
    for p in parts():
        s.text(40, yy, p["part_id"], 11, ACC, bold=True)
        s.text(120, yy, str(p["qty"]), 11, INK)
        s.text(155, yy, p["part_name"][:38], 11, INK)
        s.text(520, yy, (p["finished_size"] or p["purchase_size"] or "—")[:32], 11, INK)
        s.text(820, yy, p["handed"][:14], 11, DIM)
        s.text(980, yy, (p["joinery"] or p["reference_face"] or "")[:42], 11, DIM)
        yy += 16

    s.text(40, yy + 10, "DATUMS", 14, ACC, bold=True)
    yy += 32
    for d in datums():
        s.text(40, yy, d["id"], 12, ACC, bold=True)
        s.text(160, yy, f'{d["on"]}  ·  {d["what"]}  —  {d["use"]}', 12, INK)
        yy += 18

    s.text(40, yy + 8, "SHEET YIELD", 14, ACC, bold=True)
    yy += 28
    for n in nest_yield():
        s.text(40, yy, f'{n["sheet"][:42]}   yield {n["yield_pct"]}%   waste {n["waste_pct"]}%   {n["part_count"]} parts', 12, INK)
        yy += 18

    s.text(40, 1050, "Cut from the P-sheets (IDX). D-1…D-12 are overviews. If span changes, stretcher length, table width, and way rebate recompute — do not edit numbers on the sheet.", 12, DIM)
    s.save("D11_register.svg")


def sheet_d12():
    s = Sheet("D-12", "Joinery, routing, QA", "J-IDs · stop setups · inspection gates")
    s.titleblock()
    from walter_ds16 import joints, operations, inspection, decisions, fmea

    s.text(40, 70, "JOINT REGISTER", 16, ACC, bold=True)
    yy = 98
    for j in joints():
        s.text(40, yy, j["joint_id"], 12, ACC, bold=True)
        s.text(110, yy, f'{j["joint_type"][:22]}  {j["part_a"]} → {j["part_b"]}', 12, INK)
        note = (j.get("notes") or j.get("fit_class") or "")[:70]
        s.text(980, yy, note, 11, DIM)
        yy += 17

    s.text(40, yy + 8, "STOP SETUPS  —  do not move the stop until the listed parts are done", 16, ACC, bold=True)
    yy += 32
    for op in operations():
        s.text(40, yy, op["op"], 12, ACC, bold=True)
        s.text(110, yy, f'{op["title"][:28]}  {op.get("setting","")[:36]}  {", ".join(op.get("parts", []))[:28]}', 12, INK)
        yy += 17

    s.text(40, yy + 8, "QA GATES", 16, ACC, bold=True)
    yy += 30
    col = 0
    y0 = yy
    for i, q in enumerate(inspection()):
        x = 40 + (i % 2) * 800
        y = y0 + (i // 2) * 22
        s.text(x, y, q["qc"], 12, ACC, bold=True)
        s.text(x + 70, y, f'{q["check"]}: {q["spec"][:56]}', 12, INK)
        yy = y

    s.text(40, 900, "DECISIONS B.1", 16, ACC, bold=True)
    yy = 928
    for d in decisions()[-3:]:
        s.text(40, yy, d["id"], 12, ACC, bold=True)
        s.text(110, yy, f'{d["decision"]}  —  {d["reason"][:70]}', 12, INK)
        yy += 18

    s.text(40, 1000, "FMEA (shop, not certified structural analysis)", 14, ACC, bold=True)
    yy = 1024
    for f in fmea()[:4]:
        s.text(40, yy, f'{f["mode"]}: {f["mitigation"]}', 12, INK)
        yy += 16

    s.save("D12_joinery.svg")


def main():
    sheet_d1()
    sheet_d2()
    sheet_d3()
    sheet_d4()
    sheet_d5()
    sheet_d6()
    sheet_d7()
    sheet_d8()
    sheet_d10()
    sheet_d11()
    sheet_d12()
    print("done →", OUT)


if __name__ == "__main__":
    main()
