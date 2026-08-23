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
from walter_project import PROJECT, build_project  # noqa: E402
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
    s.text(52, 810, "SHEET INDEX (this family)", 14, ACC, bold=True)
    idx = [
        "G-001 Cover / release", "G-002 Design basis", "A-101 Iso (navigation only)", "A-102 Orthographic GA",
        "A-103 Section at D2", "E-101 Exploded + balloons", "P-201 Disc D-001", "P-202 Wall F-002/003",
        "P-203 Bearing plate ST-001/002", "P-204 Platen T-001", "J-201 Drum stack", "J-202 Ways + Acme",
        "J-203 Crown + belt", "J-204 Wrap", "M-101 Drive", "M-102 Conveyor", "F-101 Nest", "Q-101 Inspection",
    ]
    for i, name in enumerate(idx):
        col, row = i // 9, i % 9
        s.text(52 + col * 340, 836 + row * 18, name, 12, INK)
    s.note(900, 780, [
        "ALSO IN THIS PACKAGE",
        "W-1…W-14 shop blueprints in /plans/",
        "LEGO 22-step manual in /manual/",
        "Guidebook HTML in /planforge/",
        "Kernel STL/OBJ in /cad/exports/",
        "Do not scale A-101. Cut from P-sheets + T-DISC.",
    ], width=460)
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
        "Overall envelope 22.00 × 36.00 × 20.00 benchtop [G]. Optional stand +32.00.",
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
    sheet_a101()
    sheet_a102()
    sheet_a103()
    sheet_e101()
    sheet_p201()
    sheet_p202()
    sheet_p203()
    sheet_p204()
    sheet_j201()
    sheet_j202()
    sheet_j203()
    sheet_j204()
    sheet_m101()
    sheet_m102()
    sheet_f101()
    sheet_q101()
    write_index()
    print(f"WALTER PLANFORGE drawings Rev {REV}: {len(SHEETS)} sheets")


if __name__ == "__main__":
    main()
