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
            "ShopNotes 86 → Walters → Rev A solid-table redesign",
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
    table_z = 14.0
    s.rect(
        X(1),
        Y(table_z + S.table_thick),
        S.table_depth * sc,
        S.table_thick * sc,
        fill=LIGHT,
        stroke=INK,
        sw=1.5,
    )
    s.text(X(S.table_depth / 2 + 1), Y(table_z + S.table_thick / 2) + 5, "TABLE", 12, DIM, "middle")
    # Drum
    drum_cx, drum_cz = 11.0, table_z + S.table_thick + S.drum_od / 2 + 0.05
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
    s.rect(fx, fy - S.side_height * fs * 0.55, S.side_thick * fs, S.side_height * fs * 0.55, fill=WOOD, stroke=INK)
    s.rect(
        fx + (span + S.side_thick) * fs,
        fy - S.side_height * fs * 0.55,
        S.side_thick * fs,
        S.side_height * fs * 0.55,
        fill=WOOD,
        stroke=INK,
    )
    # drum as rectangle (end view is circle already; here cylinder face)
    drum_w = S.drum_length * fs
    s.rect(
        fx + S.side_thick * fs + (span * fs - drum_w) / 2,
        fy - 280,
        drum_w,
        S.drum_od * fs,
        fill=MDF,
        stroke=INK,
        sw=1.5,
    )
    s.rect(
        fx + S.side_thick * fs,
        fy - 200,
        span * fs,
        S.table_thick * fs,
        fill=LIGHT,
        stroke=INK,
    )
    s.dim_h(
        fx + S.side_thick * fs,
        fx + S.side_thick * fs + span * fs,
        fy - 40,
        f'{span}" CLEAR / {S.capacity_width}" WORK',
        offset=20,
    )

    notes = [
        "LINEAGE: ShopNotes 86 table-saw unit → Walters dedicated motor → this Rev A.",
        "FEED: Solid laminated table + push sticks. Conveyor deleted (tracking failures).",
        "DRIVE: 3″ motor / 5″ drum pulleys → ~1035 RPM · ~1350 sfpm surface.",
        "DRUM: 19×¾″ core + 2×¾″ BB ends on precision ¾″ shaft · Velcro hook wrap.",
        "ADJUST: Idler flange bearing on jack/shim pad for parallelism or light taper.",
        "SAFETY: Hood is a guard. Never open while spinning. Light passes only.",
        "DUST: 4″ port to collector. MDF dust is heavy — run extraction every session.",
    ]
    for i, n in enumerate(notes):
        s.text(780, 560 + i * 26, n, 13, INK)

    s.save("D1_general.svg")


def sheet_d2():
    s = Sheet("D-2", "Frame & table", "Scale ~1:6 · Baltic birch structure")
    s.titleblock()
    s.text(40, 70, "SIDE PANEL — layout (make 2, mirrored)", 16, ACC, bold=True)

    sc = 22.0
    ox, oy = 60, 780

    def X(v):
        return ox + v * sc

    def Y(v):
        return oy - v * sc

    s.rect(X(0), Y(S.side_height), S.side_depth * sc, S.side_height * sc, fill=WOOD, stroke=INK, sw=2)
    # bearing center
    bx, bz = 11.0, 18.5
    s.circle(X(bx), Y(bz), 1.1 * sc, fill="none", stroke=ACC, sw=2)
    s.circle(X(bx), Y(bz), 0.375 * sc, fill=STEEL, stroke=INK)
    s.text(X(bx) + 30, Y(bz), "FLANGE BEARING CL", 12, ACC)
    # table slot
    s.rect(X(1.5), Y(16), 17 * sc, 0.4 * sc, fill="none", stroke=DIM, sw=1.5, dash="6 4")
    s.text(X(10), Y(16.5), "TABLE LOCK SLOT", 11, DIM, "middle")
    # motor pivot
    s.circle(X(4), Y(6), 0.4 * sc, fill="none", stroke=GRAY, sw=1.5)
    s.text(X(4), Y(4.5), "MOTOR PIVOT", 11, DIM, "middle")

    s.dim_h(X(0), X(S.side_depth), Y(0), f'{S.side_depth}"', offset=40)
    s.dim_v(Y(0), Y(S.side_height), X(0), f'{S.side_height}"', offset=-36)
    s.dim_h(X(0), X(bx), Y(S.side_height), f'{bx:g}"', offset=-28)
    s.dim_v(Y(0), Y(bz), X(S.side_depth), f'{bz:g}"', offset=36)

    # Table detail
    s.text(900, 70, "TABLE SANDWICH", 16, ACC, bold=True)
    s.rect(920, 120, 280, 40, fill=STEEL, stroke=INK, sw=1.5)
    s.text(1060, 145, "WEAR: PHENOLIC / FORMICA", 12, PAPER, "middle", bold=True)
    s.rect(920, 160, 280, 50, fill=WOOD, stroke=INK, sw=1.5)
    s.text(1060, 190, '¾" PLY LAYER A', 12, INK, "middle")
    s.rect(920, 210, 280, 50, fill=MDF, stroke=INK, sw=1.5)
    s.text(1060, 240, '¾" PLY LAYER B — FULL GLUE', 12, INK, "middle")
    s.text(920, 290, f'Finished: {S.table_width}" W × {S.table_depth}" D × {S.table_thick}"', 13, DIM)
    s.text(920, 318, "Do not screw-only — torsional stiffness needs continuous glue.", 13, INK)

    s.text(900, 380, "ELEVATION MECHANISM", 16, ACC, bold=True)
    rows = [
        ("Screw", S.elev_screw),
        ("Travel", f'{S.elev_travel}" typical'),
        ("Locks", f"{S.lock_knobs}× star knobs + elongated washers"),
        ("Nut", "Tapped oak 2×4 or Acme nut in stretcher"),
        ("Tip", "Unload screw with knobs before fine adjust"),
    ]
    yy = 420
    for a, b in rows:
        s.text(920, yy, a, 13, DIM, bold=True)
        s.text(1040, yy, b, 13, INK)
        yy += 28

    s.text(40, 860, "STRETCHERS — 3× between sides", 16, ACC, bold=True)
    s.text(
        40,
        890,
        f'Front / mid / rear: {S.clear_between_sides}" long × 4" × ¾" Baltic birch. '
        "Glue + screws. Mid stretcher carries elev nut.",
        14,
        INK,
    )
    s.text(
        40,
        920,
        "Idler-side bearing pad: oak block with jack screws or shim stack — "
        "Walters' recommended fix for out-of-parallel after paper wrap.",
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
        f'{S.disc_count_core} core discs + {S.disc_count_ends} BB ends · ⌀{S.drum_od}" × {S.drum_length}" · '
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
    for bx, lab in ((160, "DRIVE FLANGE"), (1380, "IDLER FLANGE*")):
        s.rect(bx, 330, 50, 140, fill=STEEL, stroke=INK, sw=1.5)
        s.text(bx + 25, 500, lab, 11, ACC, "middle", bold=True)
    s.text(1200, 540, "* adjustable height pad", 12, ACC)

    s.text(40, 620, "KEYING & GLUE", 16, ACC, bold=True)
    bullets = [
        f"Cross-drill shaft; drive {S.key_wire_od}\" piano wire stubs so discs cannot spin on shaft.",
        "Laminate with polyurethane or waterproof PVA; clamp axially while curing.",
        "MDF option: 1 mm cardboard/plastic relief every 4 discs — prevents glue-swell cracks (Walters/Wandel).",
        "Birch option: all Baltic birch discs — heavier, more stable (Heslop preference after MDF roller issues).",
        "True the OD in place: abrasive face-up on a sled, light passes until concentric to the table plane.",
        f"Wrap {S.velcro_width}\" hook Velcro; spiral {S.sandpaper_width}\" loop paper. Centrifugal force seats the hooks.",
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

    s.text(40, 520, "TABLE ELEVATION", 16, ACC, bold=True)
    s.rect(80, 560, 400, 30, fill=LIGHT, stroke=INK)
    s.text(280, 580, "TABLE", 12, DIM, "middle")
    s.line(280, 590, 280, 780, 4, STEEL)
    s.rect(250, 720, 60, 40, fill=WOOD, stroke=INK)
    s.text(280, 745, "NUT", 11, INK, "middle", bold=True)
    s.text(320, 700, "ACME / WOOD THREAD", 12, DIM)
    s.rect(120, 620, 40, 80, fill=STEEL, stroke=INK)
    s.rect(400, 620, 40, 80, fill=STEEL, stroke=INK)
    s.text(140, 640, "LOCK", 10, PAPER, "middle")
    s.text(420, 640, "LOCK", 10, PAPER, "middle")

    elev = [
        "Loosen both star knobs.",
        "Turn elevating screw — light contact only.",
        "Retighten knobs to unload the screw threads.",
        "Elongated Formica/phenolic washers protect paint (Walters tip).",
        "Never take a heavy cut — drum sanders remove thousandths per pass.",
    ]
    for i, e in enumerate(elev):
        s.text(700, 560 + i * 32, f"{i + 1}.  {e}", 14, INK)

    s.text(40, 860, "IDLER BEARING MICRO-ADJUST", 16, ACC, bold=True)
    s.text(
        40,
        895,
        "Jack screws or shim stock under the left (idler) flange bearing correct "
        "paper-thickness error and allow intentional light taper sanding.",
        14,
        INK,
    )
    s.text(
        40,
        925,
        "Reference oak locator blocks under both bearings so the drum returns to the same seat after removal.",
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

    yy = 110
    s.text(40, yy, "QTY", 12, DIM, bold=True)
    s.text(100, yy, "SIZE", 12, DIM, bold=True)
    s.text(520, yy, "STOCK", 12, DIM, bold=True)
    s.text(780, yy, "USE", 12, DIM, bold=True)
    yy += 28
    for row in cut_list():
        s.text(40, yy, str(row["qty"]), 13, INK)
        s.text(100, yy, row["size"], 13, INK)
        s.text(520, yy, row["stock"], 13, INK)
        s.text(780, yy, row["use"], 13, INK)
        yy += 26

    s.text(40, yy + 20, "HARDWARE BOM", 16, ACC, bold=True)
    yy += 50
    for row in hardware_bom():
        s.text(40, yy, row["qty"], 13, ACC, bold=True)
        s.text(100, yy, row["item"], 13, INK)
        yy += 24
        if yy > 900:
            break

    # Assembly column
    s.text(1100, 70, "BUILD SEQUENCE", 16, ACC, bold=True)
    yy = 110
    for step in assembly_phases():
        s.text(1100, yy, step["id"].upper() + "  " + step["title"], 12, INK, bold=True)
        yy += 22
        # wrap body lightly
        body = step["body"]
        if len(body) > 48:
            body = body[:48] + "…"
        s.text(1100, yy, body, 11, DIM)
        yy += 28

    s.text(
        40,
        1050,
        "Sources: woodgears.ca/reader/walters/drum_sander.html · YouTube W-5Sj6kBVic · "
        "ShopNotes 86 · Heslop/Hawley notes on woodgears.ca",
        12,
        DIM,
    )

    s.save("D6_cutlist.svg")


def main():
    sheet_d1()
    sheet_d2()
    sheet_d3()
    sheet_d4()
    sheet_d5()
    sheet_d6()
    print("done →", OUT)


if __name__ == "__main__":
    main()
