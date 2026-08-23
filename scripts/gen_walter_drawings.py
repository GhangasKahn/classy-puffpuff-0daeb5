#!/usr/bin/env python3
"""WALTER Rev C — WOODWRIGHT PLANFORGE drawing family (G/A/E/P/J/M/F/Q).

A3 landscape SVGs generated from walter_kernel + walter_project.
Shop blueprints W-1…W-14 remain in plans/; this set is the audit package.

Run: python3 scripts/gen_walter_drawings.py
"""

from __future__ import annotations

import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAD = os.path.join(ROOT, "sander", "walter", "cad")
sys.path.insert(0, CAD)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from walter_kernel import (  # noqa: E402
    P,
    REV,
    drive_inner,
    drive_outer,
    drum_rpm,
    drum_x0,
    feed_fpm,
    idle_inner,
    sfm,
    table_top_z,
)
from walter_project import PROJECT, build_project, sheet_index  # noqa: E402
from gen_walter_manual import paint_machine  # noqa: E402

OUT = os.path.join(ROOT, "sander", "walter", "fab", "06_DRAWINGS")
os.makedirs(OUT, exist_ok=True)

PROJ = build_project()
W, Hpx = 1680, 1188
INK, DIM, ACC, PAPER, LIGHT = "#1c1914", "#6b5340", "#b4532a", "#f4efe6", "#d4cbb8"
STEEL, DRUM, BELT, SAFE, WARN = "#5c656c", "#7a5a3a", "#2a2a2c", "#3d5a4c", "#8a3a2a"
MONO = "font-family='IBM Plex Mono, Menlo, monospace'"
SER = "font-family='Georgia, serif'"
BANNER = "NOT FOR UNCONDITIONAL FABRICATION  ·  R3 POWERED MACHINE  ·  ELECTRICIAN [P]  ·  FIRST-RUN [T]  ·  DO NOT SCALE PERSPECTIVE"
SHEETS = []


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Sheet:
    def __init__(self, code, title, scale_note):
        self.code, self.title, self.scale_note = code, title, scale_note
        self.b = []

    def add(self, s):
        self.b.append(s)

    def line(self, x1, y1, x2, y2, w=2, color=INK, dash=None):
        d = f" stroke-dasharray='{dash}'" if dash else ""
        self.add(f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' stroke='{color}' stroke-width='{w}'{d}/>")

    def rect(self, x, y, w, h, fill="none", stroke=INK, sw=2, dash=None, rx=0):
        d = f" stroke-dasharray='{dash}'" if dash else ""
        r = f" rx='{rx}'" if rx else ""
        self.add(f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}'{d}{r}/>")

    def circle(self, cx, cy, r, fill="none", stroke=INK, sw=2, dash=None):
        d = f" stroke-dasharray='{dash}'" if dash else ""
        self.add(f"<circle cx='{cx:.1f}' cy='{cy:.1f}' r='{r:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}'{d}/>")

    def poly(self, pts, fill="none", stroke=INK, sw=2):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.add(f"<polygon points='{p}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}' stroke-linejoin='round'/>")

    def text(self, x, y, s, size=16, color=INK, anchor="start", bold=False, mono=True, rot=None, bg=False):
        f = MONO if mono else SER
        wgt = " font-weight='600'" if bold else ""
        r = f" transform='rotate({rot} {x:.1f} {y:.1f})'" if rot is not None else ""
        if bg and rot is None:
            w = max(24, len(str(s)) * size * 0.56)
            bx = {"start": x - 4, "middle": x - w / 2 - 4, "end": x - w - 4}[anchor]
            self.add(f"<rect x='{bx:.1f}' y='{y - size:.1f}' width='{w + 8:.1f}' height='{size + 6:.1f}' fill='{PAPER}'/>")
        self.add(f"<text x='{x:.1f}' y='{y:.1f}' {f} font-size='{size}' fill='{color}' text-anchor='{anchor}'{wgt}{r}>{esc(s)}</text>")

    def dim_h(self, x1, x2, y, label, offset=0, size=14):
        yy = y + offset
        for x in (x1, x2):
            self.line(x, y, x, yy + (8 if offset >= 0 else -8), 1, DIM)
        self.line(x1, yy, x2, yy, 1.4, DIM)
        for x, sgn in ((x1, 1), (x2, -1)):
            self.poly([(x, yy), (x + sgn * 10, yy - 4), (x + sgn * 10, yy + 4)], fill=DIM, stroke=DIM, sw=0.5)
        self.text((x1 + x2) / 2, yy - 6, label, size, DIM, "middle", bg=True)

    def dim_v(self, y1, y2, x, label, offset=0, size=14):
        xx = x + offset
        for y in (y1, y2):
            self.line(x, y, xx + (8 if offset >= 0 else -8), y, 1, DIM)
        self.line(xx, y1, xx, y2, 1.4, DIM)
        for y, sgn in ((y1, 1), (y2, -1)):
            self.poly([(xx, y), (xx - 4, y + sgn * 10), (xx + 4, y + sgn * 10)], fill=DIM, stroke=DIM, sw=0.5)
        self.text(xx + (12 if offset >= 0 else -12), (y1 + y2) / 2 + 5, label, size, DIM,
                  "start" if offset >= 0 else "end", bg=True, rot=-90)

    def note(self, x, y, lines, width=440):
        self.rect(x, y, width, 22 + 18 * len(lines), fill="#efe8dc", stroke=DIM, sw=1)
        for i, ln in enumerate(lines):
            self.text(x + 12, y + 22 + i * 18, ln, 13, INK if i else ACC, bold=(i == 0))

    def balloon(self, x, y, n, leader=None):
        if leader:
            self.line(leader[0], leader[1], x, y, 1.2, INK)
        self.circle(x, y, 14, fill=PAPER, stroke=INK, sw=2)
        self.text(x, y + 5, str(n), 13, INK, "middle", bold=True)

    def titleblock(self):
        """Prepend frame so it sits behind geometry."""
        orig = self.b
        self.b = []
        self.rect(0, 0, W, Hpx, fill=PAPER, stroke=INK, sw=3)
        self.rect(24, 24, W - 48, 32, fill="#3a1814", stroke="none")
        self.text(40, 46, BANNER, 12, "#f3e6dc")
        self.rect(24, 56, W - 48, Hpx - 80, fill="none", stroke=INK, sw=1.2)
        self.line(24, Hpx - 92, W - 24, Hpx - 92, 1.5)
        self.text(40, Hpx - 60, "WALTER", 26, ACC, bold=True, mono=False)
        self.text(175, Hpx - 64, f"{self.code}  ·  {self.title}", 17, INK, bold=True)
        self.text(40, Hpx - 36, self.scale_note, 12, DIM)
        self.text(W - 40, Hpx - 60, f"{PROJECT['CODE']}  ·  Rev {REV}  ·  {PROJECT['RELEASE_STATE']}", 12, DIM, "end")
        self.text(W - 40, Hpx - 36, "Inches controlling  ·  3rd-angle  ·  PLANFORGE v1.0  ·  not a ShopNotes reprint", 12, DIM, "end")
        self.b = self.b + orig

    def save(self, filename, caption):
        self.titleblock()
        path = os.path.join(OUT, filename)
        svg = (
            f"<?xml version='1.0' encoding='UTF-8'?>\n"
            f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{Hpx}' viewBox='0 0 {W} {Hpx}'>\n"
            + "\n".join(self.b)
            + "\n</svg>\n"
        )
        with open(path, "w") as f:
            f.write(svg)
        SHEETS.append((filename, self.code, caption))
        print("wrote", os.path.relpath(path, ROOT))


def sheet_g001():
    s = Sheet("G-001", "Cover / release / sheet index", "NTS  ·  governance sheet")
    s.text(48, 108, "WALTER", 72, INK, bold=True, mono=False)
    s.text(52, 148, "16″ CLOSED-FRAME DRUM THICKNESS SANDER", 18, ACC, bold=True)
    s.text(52, 176, f"WOODWRIGHT PLANFORGE v1.0  ·  kernel {PROJECT['MODEL_VERSION']}  ·  {PROJECT['CODE']}", 14, DIM)
    paint_machine(s, 1180, 520, 420, highlight=(), explode=0.0, discs=False)
    s.rect(48, 210, 720, 48, fill="#f7e8de", stroke=WARN, sw=2)
    s.text(64, 240, "RELEASE: FABRICATION-READY WITH CONDITIONS — not PE-stamped, not UL, not FABRICATION-READY (unconditional).", 13, WARN, bold=True)
    cond = PROJECT["CONDITIONS"]
    s.text(52, 292, "STOP-WORK UNTIL CLOSED", 14, ACC, bold=True)
    for i, c in enumerate(cond):
        s.text(52, 318 + i * 22, f"{i + 1}.  {c[:110]}", 12, INK)
    s.text(52, 500, "RISK CLASS R3", 14, ACC, bold=True)
    for i, t in enumerate(PROJECT["RISK_TRIGGERS"]):
        s.text(52, 524 + i * 20, f"•  {t[:108]}", 12, INK)
    s.text(52, 680, "DATUMS", 14, ACC, bold=True)
    for i, d in enumerate(PROJECT["DATUMS"]):
        s.text(52, 704 + i * 20, d[:118], 12, INK)
    s.text(52, 800, "SHEET INDEX (this family)  ·  N/A recorded, not omitted by accident", 14, ACC, bold=True)
    idx = [f"{r['ID']}  {r['STATUS']}  {r['PURPOSE'][:42]}" for r in sheet_index()]
    for i, name in enumerate(idx):
        col, row = i // 12, i % 12
        s.text(52 + col * 540, 820 + row * 16, name, 11, INK)
    s.note(48, 1040, [
        "W-1…W-14 in /plans/  ·  LEGO /manual/  ·  guidebook /planforge/  ·  STL /cad/exports/  ·  cut from P-sheets + T-DISC, never A-101",
    ], width=1580)
    s.save("G-001_cover.svg", "Cover, release state, sheet index")


def sheet_g002():
    s = Sheet("G-002", "Design basis / requirements / units", "NTS  ·  inches controlling")
    s.text(48, 96, "UNITS, DATUMS, CALCULATIONS", 18, ACC, bold=True)
    s.note(48, 112, [
        "CONTROLLING UNITS",
        "Inches in the shop. Millimetres only at CAD mesh export (×25.4).",
        "Fractional layout to 1/32″ unless a fit is tighter (bore, crown, OD).",
        "Reference temperature: shop ~68 °F. Acclimate Baltic birch before final mill.",
        f"Drum RPM [D] = 1725 × 3.00 / 4.75 = {drum_rpm:.2f}",
        f"SFM [D] = π × 5.00 × rpm / 12 = {sfm:.1f}",
        f"Feed at 30 rpm roller [D] = π × 2.00 / 12 × 30 = {feed_fpm:.2f} FPM",
        "Elevation [D] = 1/6 = 0.1667 in/rev on ¾-6 Acme.",
    ], width=760)
    s.text(48, 340, "REQUIREMENTS (MUST / SHOULD / EXCLUDED)", 16, ACC, bold=True)
    y = 368
    for r in PROJ["requirements"]:
        s.text(48, y, f"{r['ID']}", 12, ACC, bold=True)
        s.text(130, y, f"{r['PRI']:9}  {r['STATEMENT'][:88]}", 12, INK)
        s.text(1300, y, r["EVIDENCE"], 12, DIM, "end")
        y += 20
    s.note(48, 720, [
        "EVIDENCE CLASSES",
        "G given · M measured · S sourced · D derived · A assumed · E estimated · T test · P professional-verify",
        "McMaster PNs except 6245K47 / 6191K37 are [E] search hints. Open the live page.",
        "W-12 wiring is design intent, not NEC. Electrician [P].",
        "ShopNotes #86 remains copyrighted. Do not scan or redraw it.",
    ], width=900)
    s.save("G-002_basis.svg", "Design basis, requirements, derived speeds")


def sheet_a101():
    s = Sheet("A-101", "Dimensioned isometric — navigation only", "NTS isometric  ·  DO NOT SCALE  ·  see A-102 for orthographic")
    paint_machine(s, 840, 560, 640, highlight=(), explode=0, discs=False)
    s.text(80, 120, "22.00", 16, DIM)
    s.dim_h(280, 1400, 980, "22.00  BASE X  [G]", offset=-8)
    s.text(1480, 400, "20.00 WALL", 14, DIM, rot=-90)
    s.note(48, 112, [
        "NAVIGATION ISOMETRIC — NOT A FABRICATION VIEW",
        "Overall envelope 22.00 × 36.00 × 22.00 benchtop [G] (walls 20.00). Optional stand +32.00.",
        "Orange in CAD renders is copper semantics, not a part ID. Use balloons on E-101.",
        "Cut from P-sheets, T-DISC, T-PLATE. Never scale this perspective.",
    ], width=620)
    s.save("A-101_isometric.svg", "Overall isometric — do not scale")


def sheet_a102():
    s = Sheet("A-102", "Orthographic general arrangement", "Scale 1:8  ·  16 px/in  ·  3rd angle  ·  inches")
    S = 16.0
    # FRONT (infeed) — looking +Y
    ox, oz = 80, 520

    def X(xin):
        return ox + xin * S

    def Zf(zin):
        return oz - zin * S

    s.text(80, 88, "FRONT — INFEED  (+Y)", 14, ACC, bold=True)
    s.rect(X(0), Zf(P["wall_h"]), P["base_x"] * S, P["wall_h"] * S, fill="#c4a574", stroke=INK, sw=1.6)
    s.rect(X(0), Zf(P["base_t"]), P["base_x"] * S, P["base_t"] * S, fill="#8a6a42", stroke=INK, sw=1.4)
    s.circle(X(P["base_x"] / 2), Zf(P["drum_z"]), (P["drum_od"] / 2) * S, fill=DRUM, stroke=INK, sw=1.6)
    s.circle(X(P["base_x"] / 2), Zf(P["drum_z"]), 4, fill=PAPER, stroke=INK, sw=1)
    tt = table_top_z(1.5)
    s.rect(X(idle_inner), Zf(tt), P["inner_w"] * S, 0.20 * S, fill=BELT, stroke=INK, sw=0.8)
    s.circle(X(P["base_x"] / 2), Zf(tt - P["roller_od"] / 2), (P["roller_od"] / 2) * S, fill=STEEL, stroke=INK, sw=1.2)
    s.dim_h(X(0), X(P["base_x"]), Zf(0), "22.00", offset=28)
    s.dim_v(Zf(0), Zf(P["wall_h"]), X(0), "20.00", offset=-28)
    s.dim_v(Zf(P["drum_z"] - P["drum_od"] / 2), Zf(P["drum_z"] + P["drum_od"] / 2), X(P["base_x"]), "5.00 Ø", offset=36)

    # TOP
    ox2, oy2 = 560, 200
    s.text(560, 88, "TOP  (−Z)", 14, ACC, bold=True)

    def XT(xin):
        return ox2 + xin * S

    def YT(yin):
        return oy2 + yin * S

    s.rect(XT(0), YT(0), P["base_x"] * S, P["base_y"] * S, fill="#efe8dc", stroke=INK, sw=1.6)
    s.rect(XT(0), YT(0), P["wall_t"] * S, P["base_y"] * S, fill="#c4a574", stroke=INK, sw=1.2)
    s.rect(XT(drive_inner), YT(0), P["wall_t"] * S, P["base_y"] * S, fill="#b89660", stroke=INK, sw=1.2)
    s.rect(XT(drum_x0), YT(P["drum_y"] - 2.5), P["drum_face"] * S, 5.0 * S, fill=DRUM, stroke=INK, sw=1.4)
    s.circle(XT(idle_inner + P["inner_w"] / 2), YT(P["roller_y_in"]), 8, fill=STEEL, stroke=INK)
    s.circle(XT(idle_inner + P["inner_w"] / 2), YT(P["roller_y_in"] + P["roller_cd"]), 8, fill=STEEL, stroke=INK)
    s.dim_v(YT(0), YT(P["base_y"]), XT(P["base_x"]), "36.00", offset=28)
    s.dim_h(XT(idle_inner), XT(drive_inner), YT(0), "16.50 INNER", offset=-22)
    s.dim_h(XT(drum_x0), XT(drum_x0 + P["drum_face"]), YT(P["drum_y"] + 3.2), "16.00 FACE", offset=18)

    # RIGHT (drive)
    ox3, oz3 = 1120, 520
    s.text(1120, 88, "RIGHT — DRIVE  (+X)", 14, ACC, bold=True)

    def YR(yin):
        return ox3 + yin * S * 0.85

    def ZR(zin):
        return oz3 - zin * S

    s.rect(YR(0), ZR(P["wall_h"]), P["base_y"] * S * 0.85, P["wall_h"] * S, fill="#b89660", stroke=INK, sw=1.6)
    s.circle(YR(P["drum_y"]), ZR(P["drum_z"]), (P["pulley_drm"] / 2) * S, fill=STEEL, stroke=INK, sw=1.6)
    s.circle(YR(P["motor_y"]), ZR(P["motor_z"]), (P["pulley_mot"] / 2) * S, fill="#161616", stroke=INK, sw=1.6)
    s.line(YR(P["drum_y"]), ZR(P["drum_z"] + P["pulley_drm"] / 2), YR(P["motor_y"]), ZR(P["motor_z"] + P["pulley_mot"] / 2), 2.2, BELT)
    s.dim_h(YR(0), YR(P["base_y"]), ZR(0), "36.00", offset=28)
    s.note(80, 780, [
        "DATUMS ON THIS SHEET",
        "D1 base top = Z0. Walls sit on it.",
        "D2 drum axis Z 13.50  Y 18.00 — story stick both plates.",
        "Section A-103 cuts at Y = 18.00 looking to infeed.",
        "Motor 56C on hinged plate outboard of drive wall. Guard omitted for clarity — see M-101.",
    ], width=620)
    s.save("A-102_ortho.svg", "Front / top / drive orthographic GA")


def sheet_a103():
    s = Sheet("A-103", "Section at drum axis D2", "Scale 1:6  ·  ~21 px/in  ·  section at Y = 18.00")
    S = 21.0
    ox, oz = 120, 780

    def X(xin):
        return ox + xin * S

    def Z(zin):
        return oz - zin * S

    s.text(80, 92, "SECTION A–A  ·  LOOKING TO INFEED  ·  HATCH = CUT MATERIAL", 14, ACC, bold=True)
    # base + walls
    s.rect(X(0), Z(P["base_t"]), P["base_x"] * S, P["base_t"] * S, fill="#8a6a42", stroke=INK, sw=1.8)
    s.rect(X(0), Z(P["wall_h"]), P["wall_t"] * S, (P["wall_h"] - P["base_t"]) * S, fill="#c4a574", stroke=INK, sw=1.8)
    s.rect(X(drive_inner), Z(P["wall_h"]), P["wall_t"] * S, (P["wall_h"] - P["base_t"]) * S, fill="#b89660", stroke=INK, sw=1.8)
    # hatch walls
    for i in range(8):
        y0 = Z(P["wall_h"]) + i * 28
        s.line(X(0), y0, X(P["wall_t"]), y0 + 18, 0.6, DIM)
        s.line(X(drive_inner), y0, X(drive_outer), y0 + 18, 0.6, DIM)
    # drum
    s.circle(X(idle_inner + P["inner_w"] / 2), Z(P["drum_z"]), (P["drum_od"] / 2) * S, fill=DRUM, stroke=INK, sw=2)
    s.circle(X(idle_inner + P["inner_w"] / 2), Z(P["drum_z"]), (P["shaft_d"] / 2) * S, fill="#d0d4d6", stroke=INK, sw=1)
    # platen
    tt = table_top_z(1.5)
    s.rect(X(idle_inner + 0.12), Z(tt), (P["inner_w"] - 0.24) * S, (P["table_t"] + P["uhmw_t"]) * S, fill="#e8eef0", stroke=INK, sw=1.4)
    s.rect(X(idle_inner - 0.38), Z(tt - 0.2), 0.50 * S, 2.0 * S, fill="#8a6a42", stroke=INK, sw=1.2)
    s.rect(X(drive_inner - 0.12), Z(tt - 0.2), 0.50 * S, 2.0 * S, fill="#8a6a42", stroke=INK, sw=1.2)
    # plates
    s.rect(X(idle_inner), Z(P["drum_z"] + 3), P["plate_t"] * S, P["plate"] * S, fill=STEEL, stroke=INK, sw=1.4)
    s.rect(X(drive_inner - P["plate_t"]), Z(P["drum_z"] + 3), P["plate_t"] * S, P["plate"] * S, fill=STEEL, stroke=INK, sw=1.4)
    s.dim_v(Z(0), Z(P["drum_z"]), X(0), "13.50 D2", offset=-40)
    s.dim_h(X(idle_inner), X(drive_inner), Z(0), "16.50", offset=36)
    s.dim_h(X(drum_x0), X(drum_x0 + P["drum_face"]), Z(P["drum_z"] + 3.2), "16.00 FACE", offset=-24)
    s.note(980, 120, [
        "SECTION NOTES",
        "Opening shown 1.50″ [A default]. Travel 0.06–4.00.",
        "Ways in dados: 0.02–0.04 sliding fit. Oil, never paint.",
        "Idle plate (left) is slotted 0.90″ for jack travel.",
        "Drive plate (right) is round-hole, fixed.",
        "Hood and guard omitted — see M-101 / W-7.",
        "Hatch direction distinguishes idle vs drive wall.",
    ], width=460)
    s.save("A-103_section.svg", "Section at drum axis Y=18.00")


def sheet_e101():
    s = Sheet("E-101", "Exploded assembly with BOM balloons", "NTS exploded  ·  balloons = part register  ·  do not scale")
    paint_machine(s, 720, 560, 520, highlight=(), explode=0.55, discs=False)
    items = [
        (1, "F-001", "base"), (2, "F-002", "idle wall"), (3, "F-003", "drive wall"),
        (4, "D-001", "disc stack"), (5, "ST-004", "shaft"), (6, "T-001", "platen"),
        (7, "C-001", "rollers"), (8, "C-004", "PVC belt"), (9, "M-001", "1 HP"),
        (10, "M-003", "guard"), (11, "HD-001", "hood"), (12, "ST-007", "Acme"),
    ]
    s.text(48, 96, "ITEM BALLOONS MATCH PART REGISTER", 14, ACC, bold=True)
    y = 120
    for n, pid, lab in items:
        s.balloon(64, y, n)
        p = next((r for r in PROJ["parts"] if r["PART_ID"] == pid), {})
        s.text(88, y + 5, f"{pid}  {p.get('DESC', lab)}", 13, INK)
        y += 36
    s.balloon(1180, 220, 11, leader=(980, 280))
    s.balloon(1280, 420, 9, leader=(1100, 480))
    s.balloon(1280, 620, 10, leader=(1080, 600))
    s.balloon(420, 700, 1, leader=(560, 640))
    s.balloon(420, 420, 4, leader=(700, 400))
    s.note(1100, 760, [
        "EXPLODE AXES",
        "Drum +Z  ·  table −Z  ·  motor +X  ·  hood +Z",
        "Hardware stacks: E-103 is N/A as a separate sheet —",
        "see W-9 and planforge/MCMASTER_SCHEDULE.csv.",
        "Assembly order: bags 1→6 / LEGO steps 01–22.",
    ], width=420)
    s.save("E-101_exploded.svg", "Exploded isometric with part balloons")


def sheet_p201():
    s = Sheet("P-201", "Part D-001 — drum disc blank", "Scale 4:1 on blank  ·  1:1 template is T-DISC  ·  inches")
    ox, oy, sc = 520, 520, 72  # px per inch → Ø5.125 ≈ 369
    r = (P["drum_blank"] / 2) * sc
    rb = (0.748 / 2) * sc
    s.circle(ox, oy, r, fill="#c4b49a", stroke=INK, sw=2.4)
    s.circle(ox, oy, rb, fill=PAPER, stroke=INK, sw=2)
    kw = P["key_w"] * sc
    s.rect(ox - kw / 2, oy - rb - 14, kw, 28, fill=ACC, stroke=INK, sw=1.4)
    s.line(ox - r - 20, oy, ox + r + 20, oy, 0.8, DIM, dash="6 5")
    s.line(ox, oy - r - 20, ox, oy + r + 20, 0.8, DIM, dash="6 5")
    s.dim_h(ox - r, ox + r, oy + r, "Ø 5.125 BLANK", offset=36)
    s.dim_h(ox - rb, ox + rb, oy, "Ø 0.748 +0.000/−0.002", offset=-80)
    s.text(ox, oy + r + 86, "AFTER TRUE (Q02): Ø 5.000 ±0.010  REF ON THIS SHEET — TURN THE STACK", 13, ACC, "middle", bold=True)
    s.note(980, 120, [
        "D-001  QTY 21  ·  ¾″ Baltic birch",
        "Grain: face ply; random rotation around stack is OK.",
        "Bore on the drill-press fence. One setup, all 21.",
        "Keyway 3/16 after bore. File or broach. No glue in keyway.",
        "Print T-DISC.svg at 100%. Check 1.00″ AND 100 mm bars.",
        "Show face: either face. Defect: no voids at bore.",
        "Mating: ST-004 shaft, ST-005 keys, ST-006 bells.",
        "Rough: Ø 5.25 from sheet. Finish: this drawing.",
    ], width=480)
    s.note(980, 380, [
        "INSPECTION",
        "Pin gauge 0.748 go / 0.750 no-go.",
        "Key seats on 3/16 square without rocking.",
        "Blank OD within 1/16 of the template line.",
    ], width=480)
    s.save("P-201_disc.svg", "Part D-001 disc blank")


def sheet_p202():
    s = Sheet("P-202", "Parts F-002 / F-003 — doubled walls", "Scale 1:10  ·  8 px/in  ·  inches")
    S = 8.0
    ox, oy = 80, 140
    s.rect(ox, oy, 36 * S, 20 * S, fill="#c4a574", stroke=INK, sw=2)
    s.rect(ox + 8, oy + 8, 36 * S - 16, 20 * S - 16, fill="none", stroke=DIM, sw=1, dash="5 4")
    s.dim_h(ox, ox + 36 * S, oy + 20 * S, "36.00 Y", offset=28)
    s.dim_v(oy, oy + 20 * S, ox, "20.00 Z", offset=-28)
    # bearing window
    cx = ox + 18 * S
    cy = oy + (20 - 13.50) * S
    s.rect(cx - 3 * S, cy - 3 * S, 6 * S, 6 * S, fill=STEEL, stroke=INK, sw=1.6)
    s.circle(cx, cy, 0.7 * S, fill=PAPER, stroke=INK, sw=1.4)
    s.text(cx, cy - 3 * S - 10, "PLATE SEAT  D2", 12, ACC, "middle", bold=True)
    s.note(80, 400, [
        "F-002 IDLE WALL  ·  F-003 DRIVE WALL",
        "Each wall = two ¾″ Baltic birch skins, grain crossed, PVA, cauls on a flat door.",
        "Finished 20.00 × 36.00 × 1.50. Inner faces are datums for dados and plates.",
        "Idle wall: slot two plate holes 0.90″ vertical for jack travel (J-202).",
        "Drive wall: round holes, plate fixed. Do not slot both — the machine will rack.",
        "Reject pith, voids at the plate, and skins that do not glue flat.",
    ], width=720)
    s.note(840, 140, [
        "JOINERY J-WALL",
        "Glue on a known-flat door. Winding sticks after cure.",
        "Stretchers F-004/005 at infeed and outfeed, 16.50 × 3.50 × 0.75.",
        "Base F-001 22.00 × 36.00 × 0.75 sits under walls (D1).",
        "Maple rails F-006/007 under the base, 33 × 1.50 × 1.50.",
    ], width=520)
    s.save("P-202_wall.svg", "Doubled walls F-002 / F-003")


def sheet_p203():
    s = Sheet("P-203", "Parts ST-001 / ST-002 — bearing plates", "Scale 2:1  ·  48 px/in  ·  inches  ·  1:1 also T-PLATE")
    sc = 48.0
    ox, oy = 160, 160
    s.rect(ox, oy, 6 * sc, 6 * sc, fill="#8a9096", stroke=INK, sw=2.2)
    s.circle(ox + 3 * sc, oy + 3 * sc, 0.55 * sc, fill=PAPER, stroke=INK, sw=2)
    for dx in (-1.85, 1.85):
        s.circle(ox + (3 + dx) * sc, oy + 3 * sc, 0.17 * sc, fill=PAPER, stroke=ACC, sw=1.8)
    s.dim_h(ox, ox + 6 * sc, oy + 6 * sc, "6.00", offset=32)
    s.dim_v(oy, oy + 6 * sc, ox, "6.00", offset=-32)
    s.dim_h(ox + (3 - 1.85) * sc, ox + (3 + 1.85) * sc, oy + 3 * sc, "3.70 CL", offset=-70)
    s.note(80, 560, [
        "ST-001 IDLE — SLOT the two 5/16 holes 0.90″ vertically. UCFL204 rides the jack.",
        "ST-002 DRIVE — round holes, no slots. This plate is the fixed end of D2.",
        "Material A36 ¼″. Deburr. Use the plate as the drill jig on the birch wall.",
        "Print T-PLATE.svg at 100%. Check both calibration bars before transferring.",
    ], width=780)
    s.note(900, 140, [
        "MATING",
        "UCFL204-12 ¾″ inserts [E PN 6661K13].",
        "Jack screws ¼-20 under idle flange (D3 zero = coplanar).",
        "Story-stick D2 from base top and infeed face — one stick, both walls.",
    ], width=480)
    s.save("P-203_plate.svg", "Steel bearing plates ST-001 / ST-002")


def sheet_p204():
    s = Sheet("P-204", "Part T-001 — torsion-box platen", "Scale 1:8  ·  16 px/in  ·  inches")
    S = 16.0
    ox, oy = 80, 140
    s.rect(ox, oy, 25 * S, 16.25 * S, fill="#c4a574", stroke=INK, sw=2)
    for i in range(1, 5):
        s.line(ox + i * 5 * S, oy, ox + i * 5 * S, oy + 16.25 * S, 1, DIM, dash="4 4")
    for j in range(1, 3):
        s.line(ox, oy + j * (16.25 / 3) * S, ox + 25 * S, oy + j * (16.25 / 3) * S, 1, DIM, dash="4 4")
    s.dim_h(ox, ox + 25 * S, oy + 16.25 * S, "25.00 Y", offset=28)
    s.dim_v(oy, oy + 16.25 * S, ox, "16.25 X", offset=-36)
    s.note(80, 480, [
        "T-001  ¼″ BB skins + ¾″ grid  ·  finished 16.25 × 25.00 × 0.75",
        "T-002 UHMW ⅛″ face, same footprint, mechanical screws — replaceable wear part.",
        "Grid: ¾″ strips on ~5″ centers. Skin grain along X (across the machine).",
        "Flat to a known straightedge before UHMW. A 0.010″ hump prints as a stripe.",
        "Ways T-003/004 glue/screw to the long edges; sliding faces get oil, not paint.",
    ], width=820)
    s.save("P-204_platen.svg", "Torsion-box platen T-001")


def sheet_j201():
    s = Sheet("J-201", "Joint J-DRUM — keyed disc stack", "Scale ~1:2 on section  ·  inches")
    s.text(48, 96, "ASSEMBLED SECTION THROUGH SHAFT", 14, ACC, bold=True)
    ox, oy = 80, 280
    s.rect(ox, oy, 640, 90, fill="#c4b49a", stroke=INK, sw=2)
    for i in range(8):
        s.line(ox + 80 * i, oy, ox + 80 * i, oy + 90, 1.2, INK)
        if i in (3, 7):
            s.rect(ox + 80 * i - 4, oy, 8, 90, fill=PAPER, stroke=ACC, sw=1.2)
    s.rect(ox - 20, oy + 32, 700, 26, fill="#d0d4d6", stroke=INK, sw=1.6)
    s.rect(ox + 40, oy + 18, 120, 10, fill=ACC, stroke=INK, sw=1)
    s.text(ox + 100, oy + 14, "KEY 3/16 × 4.00  ST-005", 12, ACC, bold=True)
    s.text(ox, oy + 120, "0.5 mm GAP EVERY 4 DISCS  ·  NO GLUE IN KEYWAY", 13, ACC, bold=True)
    s.note(80, 460, [
        "SEQUENCE",
        "1. Number discs 1–21. Dry-stack. Confirm 16.00 face after bells.",
        "2. PVA on faces only. Clamp as a column. Wipe the keyway.",
        "3. End bells ST-006, retainer slots at idle and drive.",
        "4. True OD to 5.000 ±0.010 (Q02) between centers or in-machine on a carrier.",
        "FAILURE: glue in the keyway locks the stack to the shaft forever.",
        "FAILURE: no gaps + MDF = hairline cracks (Walters). Birch + 0.5 mm.",
    ], width=780)
    s.note(900, 120, [
        "FIT",
        "Bore 0.748 on Ø0.750 shaft = 0.002 under.",
        "Freeze shaft or warm discs, or ream one disc.",
        "Key is removable 1045/1144 — not piano wire.",
        "Inspection: Q02 + no rock on the key.",
    ], width=480)
    s.save("J-201_drum.svg", "Drum stack joinery J-DRUM")


def sheet_j202():
    s = Sheet("J-202", "Joints J-WAY / J-ACME / idle jack", "Scale ~1:4  ·  inches")
    s.text(48, 96, "UHMW WAY IN DADO  ·  ACME NUT BLOCK  ·  IDLE JACK D3", 14, ACC, bold=True)
    s.rect(80, 140, 40, 220, fill="#c4a574", stroke=INK, sw=2)
    s.rect(120, 180, 28, 140, fill="#e8eef0", stroke=INK, sw=2)
    s.rect(148, 200, 220, 24, fill="#c4a574", stroke=INK, sw=1.6)
    s.text(160, 176, "PLATEN", 12, DIM)
    s.text(88, 380, "WALL DADO", 12, DIM)
    s.text(124, 340, "WAY", 12, ACC, bold=True)
    s.circle(520, 250, 18, fill=STEEL, stroke=INK, sw=2)
    s.rect(500, 268, 40, 80, fill="#8a6a42", stroke=INK, sw=1.6)
    s.text(520, 380, "¾-6 ACME IN BRONZE NUT / MAPLE BLOCK", 12, ACC, "middle", bold=True)
    s.rect(760, 160, 16, 160, fill=STEEL, stroke=INK, sw=2)
    s.rect(748, 300, 40, 12, fill="#8a9298", stroke=INK, sw=1.4)
    s.text(820, 250, "¼-20 JACK  ±0.040", 13, ACC, bold=True)
    s.note(80, 440, [
        "J-WAY: 0.50 × 2.00 ways in wall dados. Sliding 0.02–0.04. Oil. Never paint sliding faces.",
        "J-ACME: clock both bronze nuts (datum D4) before the HTD 5 mm belt. Witness paint.",
        "Four independent screws will rack — Walters' oak dowel was one; four corners are worse.",
        "Idle jack: mid-slot = D3 zero = plates coplanar. True the drum, then jack for parallelism.",
        "Lock knobs on the ways before any cut. DRO is a readout, not a clamp.",
    ], width=900)
    s.save("J-202_ways.svg", "Ways, Acme timing, idle jack")


def sheet_j203():
    s = Sheet("J-203", "Joint J-CROWN — barrel rollers and PVC belt", "Scale enlarged  ·  crown is 0.030″  ·  inches")
    s.text(48, 96, "BOTH ROLLERS  ·  0.030″ BARREL  ·  NOT A SANDING BELT", 14, ACC, bold=True)
    ox, oy = 120, 280
    # exaggerated crown
    s.poly([(ox, oy + 40), (ox + 200, oy), (ox + 400, oy + 40), (ox + 400, oy + 70), (ox + 200, oy + 30), (ox, oy + 70)], fill=STEEL, stroke=INK, sw=2)
    s.line(ox, oy + 55, ox + 400, oy + 55, 1, DIM, dash="5 4")
    s.text(ox + 200, oy - 16, "CROWN 0.030 ±0.005 AT MIDSPAN  [G]", 14, ACC, "middle", bold=True)
    s.rect(ox, oy + 120, 400, 14, fill=BELT, stroke=INK, sw=1.4)
    s.text(ox + 200, oy + 160, "2-PLY PVC CONVEYOR  16.00 × 60.00 ENDLESS", 13, INK, "middle", bold=True)
    s.note(80, 480, [
        "Walters used a 16×48 sanding belt on PVC pipe. It never tracked (three rebuilds).",
        "Turn a barrel on aluminum tube 2.00 OD × 16.25. Flat rollers do not self-center.",
        "Idle-end ¼-20 skew. Belt 1/32 above the UHMW. Track empty 60 s, then loaded (Q04).",
        "Option B if tracking fails: HDPE sliding table — see W-5. Do not return to a sanding belt.",
        "Roller CD 26.86 [D]. Shafts ⅝″ in UCFL201-10.",
    ], width=920)
    s.save("J-203_crown.svg", "Roller crown and conveyor belt")


def sheet_j204():
    s = Sheet("J-204", "Joint J-WRAP — spiral abrasive", "NTS wrap development  ·  see also W-13")
    s.text(48, 96, "START IN THE IDLE-END BELL SLOT  ·  θ ≈ 17°", 14, ACC, bold=True)
    s.rect(80, 140, 720, 200, fill="#c4b49a", stroke=INK, sw=2)
    for i in range(7):
        x0 = 90 + i * 100
        s.line(x0, 150, x0 + 80, 320, 3, ACC)
    s.rect(80, 140, 18, 200, fill=STEEL, stroke=INK, sw=1.4)
    s.rect(782, 140, 18, 200, fill=STEEL, stroke=INK, sw=1.4)
    s.text(89, 250, "IDLE SLOT", 11, PAPER, rot=-90)
    s.note(80, 380, [
        "PSA hook tape on the turned OD. 3″ roll, 80 / 120 / 150.",
        "Start the paper in the idle-end retainer slot; finish in the drive-end slot.",
        "Trace the first wrap. No lumps, no gaps that print as stripes.",
        "Walters' Velcro was permanent — a new drum to change paper. Slots make wrap a wear part.",
        "True on a carrier board until the whole 16″ face cuts (Q09).",
    ], width=900)
    s.save("J-204_wrap.svg", "Abrasive wrap J-WRAP")


def sheet_m101():
    s = Sheet("M-101", "Drive — hinge, 4L, guard, starter", "NTS mechanism  ·  W-6 / W-12 for wiring intent")
    s.text(48, 96, "1 HP TEFC 56C  ·  3.00 / 4.75 4L  ·  HINGE + TURNBUCKLE", 14, ACC, bold=True)
    s.circle(280, 360, 90, fill=STEEL, stroke=INK, sw=2)
    s.circle(280, 360, 12, fill=PAPER, stroke=INK)
    s.text(280, 480, "DRUM  Ø4.75", 13, ACC, "middle", bold=True)
    s.circle(620, 520, 56, fill="#161616", stroke=INK, sw=2)
    s.circle(620, 520, 10, fill=PAPER, stroke=INK)
    s.text(620, 600, "MOTOR  Ø3.00", 13, ACC, "middle", bold=True)
    s.line(280 + 70, 300, 620 - 40, 480, 8, BELT)
    s.rect(700, 300, 40, 280, fill=STEEL, stroke=INK, sw=2)
    s.text(760, 440, "HINGE PLATE ST-003", 13, ACC, bold=True)
    s.rect(760, 560, 90, 22, fill="#8a9298", stroke=INK, sw=1.4)
    s.text(760, 610, "TURNBUCKLE M-004", 13, INK)
    s.rect(900, 140, 200, 200, fill="#c4a574", stroke=INK, sw=2)
    s.text(1000, 250, "M-003 GUARD", 13, ACC, "middle", bold=True)
    s.note(80, 680, [
        f"Ratio 3.00/4.75 on 1725 RPM → {drum_rpm:.0f} RPM / {sfm:.0f} SFM [D].",
        "4L440 link [S] 6191K37 and 4.75 pulley [S] 6245K47 — still verify live catalog.",
        "Gravity motor-on-dowel went slack on startup (Walters). Hinge + turnbuckle is the fix.",
        "Guard fully enclosed. No finger slot at the pinch. Magnetic starter + mushroom E-stop.",
        "W-12 is design intent, not NEC. Electrician sizes OL heaters to FLA [P].",
        "Q06: restore power after E-stop — drum must not auto-restart.",
    ], width=980)
    s.save("M-101_drive.svg", "Drive hinge, belt, guard")


def sheet_m102():
    s = Sheet("M-102", "Conveyor kinematics and feed", "NTS  ·  inches / FPM")
    s.text(48, 96, "POWERED FEED  0–16 FPM  ·  24 V PWM  ·  CROWNED ROLLERS", 14, ACC, bold=True)
    s.circle(200, 280, 40, fill=STEEL, stroke=INK, sw=2)
    s.circle(720, 280, 40, fill=STEEL, stroke=INK, sw=2)
    s.rect(200, 232, 520, 16, fill=BELT, stroke=INK, sw=1.2)
    s.rect(200, 312, 520, 16, fill=BELT, stroke=INK, sw=1.2)
    s.dim_h(200, 720, 360, "26.86 CD  [D]", offset=8)
    s.text(200, 200, "INFEED", 12, ACC, "middle", bold=True)
    s.text(720, 200, "OUTFEED + GEARMOTOR", 12, ACC, "middle", bold=True)
    s.note(80, 440, [
        f"Feed at 30 rpm roller [D] = π × 2.00 / 12 × 30 = {feed_fpm:.2f} FPM. PWM 0–16 FPM target.",
        "24 V worm gearmotor on the outfeed shaft. Isolated from 115 V drum circuit.",
        "Belt 16.00 × 60.00 2-ply PVC endless — specify conveyor belting, not abrasive.",
        "Workpiece must be ≥12″ or on a carrier. Short stock is a projectile (F06).",
        "Rotation: drum bottom toward infeed (against feed); dust into the back hood.",
    ], width=920)
    s.save("M-102_conveyor.svg", "Conveyor kinematics")


def sheet_m103():
    s = Sheet("M-103", "Elevation — dual Acme, HTD, datum D4", "NTS mechanism  ·  inches  ·  ¾-6")
    s.text(48, 96, "TWO SCREWS · ONE CRANK · CLOCK NUTS BEFORE THE BELT", 14, ACC, bold=True)
    ox, oy = 80, 160
    s.rect(ox, oy, 40, 320, fill="#c4a574", stroke=INK, sw=2)
    s.rect(ox + 520, oy, 40, 320, fill="#c4a574", stroke=INK, sw=2)
    s.text(ox + 20, oy + 340, "IDLE ACME", 12, ACC, "middle", bold=True)
    s.text(ox + 540, oy + 340, "DRIVE ACME", 12, ACC, "middle", bold=True)
    s.rect(ox + 12, oy + 40, 16, 280, fill=STEEL, stroke=INK, sw=1.4)
    s.rect(ox + 532, oy + 40, 16, 280, fill=STEEL, stroke=INK, sw=1.4)
    s.rect(ox - 20, oy + 220, 80, 48, fill="#8a6a42", stroke=INK, sw=1.6)
    s.rect(ox + 500, oy + 220, 80, 48, fill="#8a6a42", stroke=INK, sw=1.6)
    s.text(ox + 20, oy + 250, "T-005", 12, PAPER, "middle", bold=True)
    s.text(ox + 540, oy + 250, "T-005", 12, PAPER, "middle", bold=True)
    s.line(ox + 20, oy + 56, ox + 540, oy + 56, 6, BELT)
    s.text(ox + 280, oy + 46, "HTD 5 mm 16T  (or #25 chain)", 13, ACC, "middle", bold=True)
    s.circle(ox + 640, oy + 56, 36, fill="#161616", stroke=INK, sw=2)
    s.text(ox + 640, oy + 110, "T-006 4″", 13, ACC, "middle", bold=True)
    s.dim_h(ox + 20, ox + 540, oy + 300, "ACME AT Y 10.00 AND 26.00  [G]", offset=36)
    s.note(80, 560, [
        f"Pitch [D] = 1/{P['acme_tpi']} = {1.0/P['acme_tpi']:.4f} in/rev on ¾-6. Travel {P['travel']:.2f} in [G].",
        "Datum D4: clock both bronze nuts together, paint a witness, THEN fit the HTD belt.",
        "Four independent corner screws will rack the platen (Walters-adjacent failure). Two screws, one crank.",
        "Ways T-003/004 slide 0.02–0.04 in wall dados. Oil. Never paint. See J-202 / P-211.",
        "Q05: witness marks still aligned after a full up/down. Q10: jack at D3 zero before trusting taper.",
    ], width=1200)
    s.save("M-103_elevation.svg", "Dual Acme elevation and HTD")


def sheet_m104():
    s = Sheet("M-104", "Dust collection — hood, port, collector as safeguard", "NTS  ·  4 in port  ·  ≥400 CFM")
    s.text(48, 96, "THE HOOD IS A SAFEGUARD  ·  NOT AN ACCESSORY  ·  COLLECTOR ON BEFORE ANY SPIN", 14, ACC, bold=True)
    s.rect(120, 180, 420, 160, fill="#3d4a46", stroke=INK, sw=2)
    s.circle(330, 220, 40, fill=PAPER, stroke=INK, sw=2)
    s.text(330, 228, "4″", 16, ACC, "middle", bold=True)
    s.text(330, 370, "HD-001 inverted-U  ·  HD-002 flange  ·  HD-003 brush at infeed lip", 13, INK, "middle")
    s.rect(120, 348, 420, 14, fill="#8a9298", stroke=INK, sw=1)
    s.text(330, 400, "BRUSH STRIP", 12, DIM, "middle")
    s.note(620, 160, [
        "AIR / DUST",
        "Port Ø 4.00 [G]. Target ≥400 CFM at the hood, not at the impeller nameplate.",
        "Fine birch dust is combustible. Collector + hood are part of the machine (SAFE-002).",
        "Foam HD-001 to the walls. Tissue test Q07: paper should suck at the infeed gap.",
        "Do not run without the collector. Do not dump fines into a shop-vac bag as the only capture.",
        "Brush strip on the infeed lip reduces leak. Outfeed leak is acceptable if infeed is pulling.",
        "See P-209 for parts, W-7 for shop notes, Q07 for acceptance.",
    ], width=820)
    s.note(80, 500, [
        "HOLD POINT",
        "Bag 6 before any test cut: hood latched, 4″ hose on, collector started, then drum.",
        "If the motor note changes or dust blows at the operator, stop. Re-seal, then 0.010″ poplar.",
        "This sheet is not an NFPA 664 dust-system design. Shop collector selection is [A]/[P].",
    ], width=1400)
    s.save("M-104_dust.svg", "Dust hood and collector as safeguard")


def sheet_f101():
    s = Sheet("F-101", "Stock nest / rough breakdown", "NTS nest  ·  5×5 Baltic birch  ·  do not optimize past one spare disc")
    s.text(48, 96, "THREE ¾″ 5×5 SHEETS + ONE ¼″ SHEET  ·  GRAIN AND SPARES FIRST", 14, ACC, bold=True)
    for i, title in enumerate(("SHEET 1  BASE + WALL SKINS", "SHEET 2  WALL SKINS", "SHEET 3  21 DISCS + STRETCHERS")):
        x = 60 + i * 520
        s.rect(x, 130, 480, 480, fill="#efe8dc", stroke=INK, sw=2)
        s.text(x + 16, 156, title, 13, ACC, bold=True)
        if i == 0:
            s.rect(x + 30, 180, 220, 360, fill="#c4a574", stroke=INK, sw=1.4)
            s.text(x + 140, 360, "F-001", 14, INK, "middle")
            s.rect(x + 270, 180, 180, 360, fill="#b89660", stroke=INK, sw=1.4)
            s.text(x + 360, 360, "F-002a", 14, INK, "middle")
        elif i == 1:
            s.rect(x + 30, 180, 180, 360, fill="#c4a574", stroke=INK, sw=1.4)
            s.text(x + 120, 360, "F-002b", 14, INK, "middle")
            s.rect(x + 230, 180, 180, 360, fill="#b89660", stroke=INK, sw=1.4)
            s.text(x + 320, 360, "F-003a", 14, INK, "middle")
        else:
            for r in range(5):
                for c in range(5):
                    if r * 5 + c < 21:
                        s.circle(x + 70 + c * 80, 220 + r * 72, 28, fill="#c4b49a", stroke=INK, sw=1)
            s.text(x + 240, 590, "D-001 ×21 + 1 spare if the sheet allows", 12, DIM, "middle")
    s.note(60, 640, [
        "¼″ sheet: platen skins T-001, hood HD-001, guard M-003. Maple: rails F-006/007, nut blocks T-005, ways.",
        "Kerf + trim: leave 1/8 on plywood lengths. Rest overnight after breaking down, then mill to finished.",
        "Do not nest a disc on a void. One machining error on D-001 is cheaper than a second 5×5 if you kept a spare.",
        "N-001 stand is optional — sheet 4 if you build it. See W-11.",
    ], width=1500)
    s.save("F-101_nest.svg", "Plywood nest and rough breakdown")


def sheet_q101():
    s = Sheet("Q-101", "Inspection and commissioning Q01–Q10", "NTS  ·  hold points  ·  first-run [T]")
    s.text(48, 96, "DO NOT SKIP  ·  BLINK TEST BEFORE ANY BOARD", 14, ACC, bold=True)
    checks = [
        ("Q01", "Walls square; plates coplanar (winding sticks)", "square + sticks"),
        ("Q02", "Drum OD 5.000 ±0.010 after turning", "caliper"),
        ("Q03", "Drum parallel to platen, 16″ feeler both ends", "feeler + straightedge"),
        ("Q04", "Conveyor tracks empty 60 s, then loaded", "marks + clock"),
        ("Q05", "Acme nuts clocked — witness marks aligned", "paint pen"),
        ("Q06", "E-stop kills drum + feed; no auto-restart", "blink test"),
        ("Q07", "Hood on, 4″ pulling, no leak at walls", "tissue"),
        ("Q08", "Guard closed; no finger path to belt pinch", "visual"),
        ("Q09", "First 0.010″ poplar even cut, then oak", "ear + caliper"),
        ("Q10", "Idle jack at D3 zero before trusting taper", "jacks"),
    ]
    for i, (qid, chk, tool) in enumerate(checks):
        y = 130 + i * 52
        s.rect(80, y, 36, 36, fill=PAPER, stroke=INK, sw=2)
        s.text(140, y + 16, qid, 16, ACC, bold=True)
        s.text(210, y + 16, chk, 15, INK)
        s.text(210, y + 36, f"Tool: {tool}", 12, DIM)
    s.note(1100, 130, [
        "FIRST-RUN ORDER [T]",
        "1. Collector on. Hood latched.",
        "2. Table locked. Ways oiled.",
        "3. No workpiece. Guard closed.",
        "4. Drum. Listen. Stop.",
        "5. Feed empty 60 s.",
        "6. Poplar 0.010″.",
        "NEVER start with a board under the drum.",
        "NEVER stand in the infeed ejection line.",
        "This is not a planer.",
        "Electrician [P] before energizing 115 V.",
    ], width=420)
    s.save("Q-101_inspect.svg", "Inspection Q01–Q10 and first-run")


def _plist(s, pids, x, y):
    parts = {p["PART_ID"]: p for p in PROJ["parts"]}
    s.text(x, y, "FINISHED SIZES FROM PART REGISTER", 13, ACC, bold=True)
    yy = y + 24
    for pid in pids:
        p = parts[pid]
        s.text(x, yy, f"{pid}  {p['QTY']}×  {p['DESC'][:36]}", 13, INK, bold=True)
        s.text(x + 14, yy + 16, f"{p['FINISHED']}  ·  {p['MAT']}  ·  {p['MAKE']}", 12, DIM)
        yy += 38
    return yy


def sheet_g003():
    s = Sheet("G-003", "Evidence / revision / calculation register", "NTS  ·  do not invent citations")
    s.text(48, 96, "EVIDENCE CLASSES  G M S D A E T P", 16, ACC, bold=True)
    y = 120
    for e in PROJ["evidence"]:
        s.text(48, y, f"{e['ID']}  [{e['CLASS']}]", 13, ACC, bold=True)
        s.text(200, y, e["DESC"][:88], 12, INK)
        y += 20
    s.note(48, 360, [
        "REVISION",
        f"Kernel {PROJECT['MODEL_VERSION']}  ·  Rev {REV}  ·  {PROJECT['CODE']}",
        "Change a master parameter in walter_kernel.py only, then regenerate.",
        "Do not edit parameters.json, SVG dimensions, or BOM cells by hand.",
        "ShopNotes #86 remains copyrighted. Hardware notes 6245K47 / 6191K37 are [S] public;",
        "still verify the live catalog. All other PNs are [E] search hints.",
    ], width=900)
    s.note(48, 540, [
        "CALCULATION REGISTER (see also CALCULATIONS.md)",
        f"CAL-001 drum_rpm [D] = 1725 × 3.00 / 4.75 = {drum_rpm:.2f} r/min",
        f"CAL-002 sfm [D] = π × 5.00 × rpm / 12 = {sfm:.1f} ft/min",
        f"CAL-003 feed_fpm [D] = π × 2.00 / 12 × 30 = {feed_fpm:.2f} ft/min at 30 r/min roller",
        "CAL-004 elevation [D] = 1/6 = 0.1667 in/rev on ¾-6 Acme",
        "CAL-005 inner_w [G] = 16.50; drum_face [G] = 16.00; gap each side = 0.25",
        "These are arithmetic identities, not tested surface-speed coupons. Tach optional.",
    ], width=1100)
    s.save("G-003_evidence.svg", "Evidence, revision, calculations")


def sheet_g004():
    s = Sheet("G-004", "Safety / FMEA / professional review", "NTS  ·  R3  ·  PPE is last layer")
    s.rect(48, 88, 1584, 36, fill="#3a1814", stroke="none")
    s.text(64, 112, "PROFESSIONAL REVIEW REQUIRED  ·  NOT OSHA CERTIFIED  ·  NOT UL  ·  NOT PE-STAMPED", 14, "#f3e6dc", bold=True)
    s.text(48, 150, PROJECT["PROFESSIONAL_REVIEW"][:118], 13, WARN)
    y = 180
    for t in PROJECT["RISK_TRIGGERS"]:
        s.text(48, y, f"•  {t[:110]}", 13, INK)
        y += 20
    s.text(48, 340, "FMEA (severity 1–10)  ·  catastrophic low-likelihood still flagged", 14, ACC, bold=True)
    y = 368
    for f in PROJ["fmea"]:
        s.text(48, y, f"{f['id']}  SEV {f['sev']}", 12, ACC, bold=True)
        s.text(170, y, f"{f['item']}: {f['cause'][:50]} → {f['prev'][:42]}", 12, INK)
        y += 20
    s.note(48, 600, [
        "HIERARCHY OF CONTROLS ON THIS MACHINE",
        "Eliminate: no sanding-belt conveyor; no gravity motor mount; no light-switch-only disconnect.",
        "Engineer: enclosed guard, hood @ 4″ / 400 CFM, magnetic starter / NOVR, jack + timed Acme.",
        "Administrate: 12″ min stock or carrier; startup card; Q06 blink test.",
        "PPE: eye/ear/dust — last layer, not a substitute for the guard or collector.",
        "First-run: collector on, hood on, no workpiece, then 0.010″ poplar. Never stand in the infeed line.",
    ], width=1100)
    s.save("G-004_safety.svg", "R3 safety, FMEA, professional review")


def sheet_a104():
    s = Sheet("A-104", "Opening envelope / nips / human interface", "NTS  ·  phantom = travel  ·  inches")
    s.text(48, 96, "TABLE TRAVEL 0.06–4.00  ·  4.50 WAY TRAVEL  ·  OPERATOR AT INFEED (−Y)", 14, ACC, bold=True)
    S = 14.0
    ox, oz = 80, 620

    def X(xin):
        return ox + xin * S

    def Z(zin):
        return oz - zin * S

    s.rect(X(0), Z(P["wall_h"]), P["base_x"] * S, P["wall_h"] * S, fill="#efe8dc", stroke=INK, sw=1.4)
    s.circle(X(P["base_x"] / 2), Z(P["drum_z"]), (P["drum_od"] / 2) * S, fill=DRUM, stroke=INK, sw=2)
    # opening min / max as phantom platens
    zmin = table_top_z(P["opening_min"])
    zmax = table_top_z(P["opening_max"])
    s.rect(X(idle_inner), Z(zmin), P["inner_w"] * S, 8, fill="none", stroke=ACC, sw=1.6, dash="6 4")
    s.rect(X(idle_inner), Z(zmax), P["inner_w"] * S, 8, fill="none", stroke=DIM, sw=1.6, dash="6 4")
    s.text(X(P["base_x"] / 2), Z(zmin) - 10, "MIN 0.06  (phantom)", 12, ACC, "middle")
    s.text(X(P["base_x"] / 2), Z(zmax) + 22, "MAX 4.00  (phantom)", 12, DIM, "middle")
    s.note(720, 120, [
        "HUMAN / NIP / EJECTION",
        "Operator stands at infeed (Y = 0). Drum bottom rotates toward operator.",
        "Nip 1: drum-to-work. Nip 2: conveyor rollers. Nip 3: 4L belt outboard — M-003 covers it.",
        "Ejection: short stock back toward infeed. 12″ minimum or carrier (F06).",
        "Reach: elevation handwheel at infeed-left. E-stop at drive-side, not behind the belt.",
        "Opening default 1.50 [A] for drawings. DRO reads from a wall-mounted caliper.",
        "A-105 N/A — no floor anchors. Optional N-001 stand is a cabinet, not a foundation.",
    ], width=720)
    s.save("A-104_envelope.svg", "Opening envelope, nips, operator")


def sheet_e102():
    s = Sheet("E-102", "Assembly dependency / bags / clamps", "NTS  ·  bags 1–6  ·  see LEGO manual")
    s.text(48, 96, "DO NOT GLUE THE MACHINE IN ONE SHOT  ·  DRY-FIT EACH BAG", 14, ACC, bold=True)
    bags = [
        ("1 DRUM", "Column clamp on the shaft. No glue in keyway. True before bag 6 wrap."),
        ("2 FRAME", "Walls on a door. Box on D1. Winding sticks on plates. Jacks at D3 zero."),
        ("3 TABLE", "Platen flat first. Ways oiled. Clock Acme D4 before HTD."),
        ("4 CONVEYOR", "Crowns first. Belt last. Track empty, then loaded."),
        ("5 DRIVE", "Hinge plate, then motor (two-hand lift), then 4L, then FULL guard, then electrician."),
        ("6 HOOD/TUNE", "Hood + collector before spin. Wrap. Jack parallel. Q01–Q10. Card. Poplar."),
    ]
    for i, (name, note) in enumerate(bags):
        x = 48 + (i % 3) * 520
        y = 130 + (i // 3) * 220
        s.rect(x, y, 500, 200, fill="#efe8dc", stroke=INK, sw=2, rx=8)
        s.rect(x + 16, y + 16, 64, 40, fill=ACC, stroke=INK, sw=1.5, rx=8)
        s.text(x + 48, y + 44, str(i + 1), 22, PAPER, "middle", bold=True)
        s.text(x + 96, y + 44, name, 16, INK, bold=True)
        s.text(x + 16, y + 90, note[:48], 13, INK)
        s.text(x + 16, y + 112, note[48:96] if len(note) > 48 else "", 13, DIM)
        s.text(x + 16, y + 160, "Manual: step pages for this bag.", 12, DIM)
    s.note(48, 600, [
        "CLAMP / CURE",
        "Bag 1: column clamps, overnight PVA. Bag 2: cauls on a door, then box clamps on D1.",
        "Bag 3: platen skins under even cauls. Ways mechanical. Do not glue UHMW across the whole face if you want to replace it.",
        "Hold points: keyway dry; drive plate not slotted; Acme clocked; 115 V not live; Q06 before Q09.",
        "E-103 N/A as a drawing — fastener stacks live in MCMASTER_SCHEDULE.csv and W-9.",
    ], width=1500)
    s.save("E-102_sequence.svg", "Bag sequence and clamp plan")


def sheet_p205():
    s = Sheet("P-205", "Parts F-001 / F-004…F-007 — base, stretchers, rails", "NTS  ·  inches from register")
    _plist(s, ["F-001", "F-004", "F-005", "F-006", "F-007"], 48, 100)
    S = 10.0
    ox, oy = 720, 140
    s.rect(ox, oy, 36 * S, 22 * S, fill="#c4a574", stroke=INK, sw=2)
    s.dim_h(ox, ox + 36 * S, oy + 22 * S, "36.00 Y  F-001", offset=24)
    s.dim_v(oy, oy + 22 * S, ox, "22.00 X", offset=-28)
    s.note(48, 520, [
        "F-001 sits on maple rails F-006/007. Walls sit on F-001 (datum D1). Stretchers F-004/005 at infeed and outfeed.",
        "Grain on F-001 along Y (depth). Stretchers grain along X. Rails grain along Y.",
        "Do not let a stretcher lift a wall off D1. Dry-fit diagonals before glue.",
    ], width=1100)
    s.save("P-205_frame.svg", "Base, stretchers, maple rails")


def sheet_p206():
    s = Sheet("P-206", "Parts ST-004 / ST-005 / ST-006 — shaft, keys, bells", "Scale mixed  ·  inches")
    _plist(s, ["ST-004", "ST-005", "ST-006"], 48, 100)
    s.rect(48, 280, 880, 36, fill="#d0d4d6", stroke=INK, sw=2)
    s.dim_h(48, 928, 316, "22.00  Ø 0.750  1144 STRESSPROOF", offset=28)
    s.rect(120, 268, 160, 12, fill=ACC, stroke=INK, sw=1)
    s.text(200, 262, "KEYWAY 3/16 × 4.00  TWO PLACES", 12, ACC, "middle", bold=True)
    s.circle(1200, 320, 90, fill="#8a9298", stroke=INK, sw=2)
    s.circle(1200, 320, 18, fill=PAPER, stroke=INK, sw=1.4)
    s.text(1200, 430, "ST-006 Ø 5.04 × 0.125  SLOT", 13, ACC, "middle", bold=True)
    s.note(48, 500, [
        "Not CRS + piano wire. Removable square keys. Bells carry the wrap-retainer slots (J-204).",
        "Turn the stack on this shaft. Do not run an unbalanced blank (Q02).",
        "BUY/MAKE: a shop can mill keyways or buy a keyed ¾″ × 22 blank and cut to length.",
    ], width=1100)
    s.save("P-206_shaft.svg", "Shaft, keys, end bells")


def sheet_p207():
    s = Sheet("P-207", "Part ST-003 — motor hinge plate", "Scale 1:4  ·  24 px/in  ·  inches")
    sc = 24.0
    ox, oy = 80, 140
    s.rect(ox, oy, 10 * sc, 8 * sc, fill=STEEL, stroke=INK, sw=2)
    s.dim_h(ox, ox + 10 * sc, oy + 8 * sc, "10.00", offset=28)
    s.dim_v(oy, oy + 8 * sc, ox, "8.00", offset=-28)
    s.circle(ox + 2 * sc, oy + 4 * sc, 0.3 * sc, fill=PAPER, stroke=INK, sw=1.4)
    s.text(ox + 5 * sc, oy + 4 * sc, "56C PATTERN — VERIFY MOTOR DRAWING [S]", 13, ACC, "middle", bold=True)
    s.note(80, 420, [
        "A36 ¼″. Hinge on the drive-wall outboard face. Turnbuckle M-004 to the wall, not motor weight on a dowel.",
        "Do not drill the 56C pattern from a retailer photo. Open the motor dimension sheet or measure the face.",
        "Mating: M-001, ST-008/009, 4L440, M-003 guard must still close over the hinge.",
    ], width=1100)
    s.save("P-207_hinge.svg", "Motor hinge plate ST-003")


def sheet_p208():
    s = Sheet("P-208", "Parts C-001 / C-002 — crowned aluminum rollers", "Scale enlarged crown  ·  inches")
    _plist(s, ["C-001", "C-002", "C-003"], 48, 100)
    ox, oy = 80, 280
    s.poly([(ox, oy + 40), (ox + 280, oy), (ox + 560, oy + 40), (ox + 560, oy + 70), (ox + 280, oy + 30), (ox, oy + 70)], fill=STEEL, stroke=INK, sw=2)
    s.dim_h(ox, ox + 560, oy + 70, "16.25 FACE  ·  2.00 OD  ·  CROWN 0.030 ±0.005", offset=36)
    s.note(48, 480, [
        "Turn the barrel on both rollers. Flat rollers will not self-center. PVC pipe is not a roller.",
        "Shafts C-003 are ⅝″ × 22 BUY in UCFL201-10. Belt C-004 is BUY endless PVC — not a sanding belt.",
        "See J-203 and M-102. Q04 empty 60 s then loaded.",
    ], width=1100)
    s.save("P-208_rollers.svg", "Crowned rollers C-001 / C-002")


def sheet_p209():
    s = Sheet("P-209", "Parts HD-001 / M-003 — hood and belt guard", "NTS  ·  inches  ·  guard is not optional")
    _plist(s, ["HD-001", "HD-002", "HD-003", "M-003"], 48, 100)
    s.rect(720, 120, 280, 140, fill="#3d4a46", stroke=INK, sw=2)
    s.circle(860, 190, 36, fill=PAPER, stroke=INK, sw=2)
    s.text(860, 280, "4″ PORT  ≥400 CFM", 13, ACC, "middle", bold=True)
    s.rect(1080, 120, 200, 200, fill="#c4a574", stroke=INK, sw=2)
    s.text(1180, 230, "M-003", 16, ACC, "middle", bold=True)
    s.note(48, 420, [
        "Hood: ¼″ birch inverted-U, foam to the walls, nylon brush on the infeed lip. Collector on before any spin.",
        "Guard: fully enclosed ¼″ BB around the 4L run. No finger slot at the pinch. Q08.",
        "Approximate envelope on the register (~) is [A] until the motor/pulley stack is in hand — size the guard to the installed CD.",
    ], width=1200)
    s.save("P-209_hood_guard.svg", "Hood HD-001 and guard M-003")


def sheet_p210():
    s = Sheet("P-210", "Part N-001 — optional 32″ cabinet stand", "Scale 1:12  ·  OPTIONAL  ·  inches")
    S = 8.0
    ox, oy = 80, 160
    s.rect(ox, oy, 22 * S, 32 * S, fill="#c4a574", stroke=INK, sw=2)
    s.dim_h(ox, ox + 22 * S, oy + 32 * S, "22.00", offset=24)
    s.dim_v(oy, oy + 32 * S, ox, "32.00 AFF", offset=-28)
    s.note(400, 160, [
        "OPTIONAL. Benchtop machine does not require N-001.",
        "If built: ¾″ BB sides 32 × 32, shelf, back, mobile base of your choice.",
        "Platen height target ~36–40″ AFF for standing work [A].",
        "Not a seismic anchorage. Not a foundation. A-105 remains N/A.",
        "See shop sheet W-11.",
    ], width=720)
    s.save("P-210_stand.svg", "Optional cabinet N-001")


def sheet_p211():
    s = Sheet("P-211", "Parts T-002 / T-003 / T-004 / T-005 — UHMW, ways, nut blocks", "NTS  ·  inches")
    _plist(s, ["T-002", "T-003", "T-004", "T-005", "T-006"], 48, 100)
    s.note(48, 380, [
        "T-002 is a replaceable wear face, same footprint as T-001, mechanical screws. Do not glue it forever.",
        "Ways 0.50 × 2.00 × 25.00 maple + UHMW. Sliding 0.02–0.04 in wall dados. Oil. Never paint.",
        "Nut blocks: bronze nut captured in maple, long grain to the screw. Clock D4 before HTD. T-006 4″ handwheel BUY.",
        "See J-202.",
    ], width=1200)
    s.save("P-211_ways.svg", "UHMW face, ways, nut blocks")


def sheet_m105():
    s = Sheet("M-105", "Electrical intent — PROFESSIONAL REVIEW REQUIRED", "NTS  ·  NOT NEC  ·  NOT A PERMIT DRAWING  ·  [P]")
    s.rect(48, 88, 1584, 44, fill="#3a1814", stroke="none")
    s.text(64, 118, "DO NOT ENERGIZE 115 V FROM THIS SHEET  ·  QUALIFIED ELECTRICIAN [P]  ·  W-12 IS DESIGN INTENT", 14, "#f3e6dc", bold=True)
    boxes = [
        (80, 180, "115 V 20 A", "Dedicated branch. Grounding. Strain relief."),
        (420, 180, "DISCONNECT", "Magnetic starter / DP contactor. Not a light switch."),
        (760, 180, "OL HEATERS", "Size to motor FLA on the nameplate. Do not guess amps."),
        (1100, 180, "E-STOP NC", "40 mm mushroom in the coil circuit. Q06: no auto-restart."),
        (80, 380, "DRUM M-001", "1 HP TEFC 1725 56C. Guard closed before RUN."),
        (420, 380, "24 V FEED", "Isolated PSU + PWM. Not taken from the 115 V coil."),
        (760, 380, "POWER-LOSS", "NOVR: restore power must not restart the drum."),
        (1100, 380, "FIRST RUN [T]", "Collector → hood → lock → drum → feed. No board under drum."),
    ]
    for x, y, t, n in boxes:
        s.rect(x, y, 300, 140, fill="#efe8dc", stroke=INK, sw=2)
        s.text(x + 16, y + 36, t, 15, ACC, bold=True)
        s.text(x + 16, y + 70, n[:34], 12, INK)
        s.text(x + 16, y + 92, n[34:68] if len(n) > 34 else "", 12, DIM)
    s.note(80, 580, [
        "This is a state diagram for the builder and the electrician, not a wiring schedule for a permit.",
        "Typical 1 HP 115 V FLA is often ~13 A — that sentence is [E], not a heater catalog number. Read the nameplate.",
        "AI / this HTML book is not a protective measure. Interlocks and NOVR are electromechanical.",
        "See W-12. Q06 is a hold point. SAFE-001 remains OPEN until the electrician and blink test close it.",
    ], width=1400)
    s.save("M-105_electrics.svg", "Electrical intent — professional review")


def sheet_f102():
    s = Sheet("F-102", "Operations routing OP-01 … OP-14", "NTS  ·  hold points in copper")
    s.text(48, 96, "PRESERVE DATUMS  ·  JOINERY WHILE PARTS ARE EASY TO HOLD  ·  TRUE DRUM BEFORE WRAP", 14, ACC, bold=True)
    ops = [
        "OP-01 D-001 bandsaw T-DISC", "OP-02 bore 0.748 + keyway", "OP-03 glue column — HOLD keyway dry",
        "OP-04 true Ø 5.000 — HOLD unbalanced", "OP-05 glue walls grain-crossed", "OP-06 plates as jigs — HOLD idle slots only",
        "OP-07 square box D1", "OP-08 platen + UHMW", "OP-09 clock Acme D4 — HOLD before HTD",
        "OP-10 turn 0.030 crowns", "OP-11 PVC belt — HOLD not sanding belt", "OP-12 motor/guard — HOLD electrician",
        "OP-13 hood + collector — HOLD before spin", "OP-14 Q01–Q10 + poplar — HOLD blink test",
    ]
    for i, op in enumerate(ops):
        col, row = i // 7, i % 7
        x, y = 48 + col * 780, 130 + row * 70
        s.rect(x, y, 760, 58, fill="#efe8dc" if "HOLD" in op else PAPER, stroke=ACC if "HOLD" in op else INK, sw=1.6)
        s.text(x + 16, y + 36, op, 14, INK, bold=True)
    s.text(48, 650, "Full routing with tools, jigs, hazards: fab/08_CUT_LISTS/operations.csv", 13, DIM)
    s.save("F-102_routing.svg", "Operations routing OP-01–14")


def write_index():
    figs = []
    for fn, code, cap in SHEETS:
        figs.append(
            f"<figure><img src='{fn}' alt='{esc(cap)}'/><figcaption><b>{esc(code)}</b> {esc(cap)}</figcaption></figure>"
        )
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/>
<title>WALTER PLANFORGE drawings — Rev {REV}</title>
<style>
body{{margin:0;background:#1c1914;color:#f4efe6;font-family:"IBM Plex Mono",monospace}}
header{{padding:32px 24px 8px;max-width:1200px;margin:0 auto}}
h1{{font-family:Georgia,serif;font-size:42px;margin:8px 0}}
.sub{{color:#8a7a68;max-width:70ch}}
nav a{{color:#d47248;margin-right:12px;font-size:12px}}
main{{max-width:1200px;margin:0 auto;padding:12px 24px 80px}}
img{{width:100%;background:#f4efe6;border:1px solid #3a3228}}
figcaption{{padding:8px 0 28px;color:#8a7a68;font-size:12px}}
figcaption b{{color:#d47248;margin-right:8px}}
</style></head><body>
<header>
<p>WALTER · Rev {REV} · WOODWRIGHT PLANFORGE v1.0 · {esc(PROJECT['CODE'])}</p>
<h1>Drawing family</h1>
<p class="sub">G/A/E/P/J/M/F/Q sheets. Release: {esc(PROJECT['RELEASE_STATE'])}. Do not scale perspective. Print A3 at 100%.</p>
<nav>
<a href="../../planforge/">Planforge</a>
<a href="../../manual/">LEGO manual</a>
<a href="../../plans/W1_general.svg">W-1</a>
<a href="../../">Landing</a>
</nav>
</header>
<main>{''.join(figs)}</main>
</body></html>
"""
    path = os.path.join(OUT, "index.html")
    with open(path, "w") as f:
        f.write(html)
    print("wrote", os.path.relpath(path, ROOT))


def main():
    sheet_g001()
    sheet_g002()
    sheet_g003()
    sheet_g004()
    sheet_a101()
    sheet_a102()
    sheet_a103()
    sheet_a104()
    sheet_e101()
    sheet_e102()
    sheet_p201()
    sheet_p202()
    sheet_p203()
    sheet_p204()
    sheet_p205()
    sheet_p206()
    sheet_p207()
    sheet_p208()
    sheet_p209()
    sheet_p210()
    sheet_p211()
    sheet_j201()
    sheet_j202()
    sheet_j203()
    sheet_j204()
    sheet_m101()
    sheet_m102()
    sheet_m103()
    sheet_m104()
    sheet_m105()
    sheet_f101()
    sheet_f102()
    sheet_q101()
    write_index()
    print(f"WALTER PLANFORGE drawings Rev {REV}: {len(SHEETS)} sheets")


if __name__ == "__main__":
    main()
