#!/usr/bin/env python3
"""Generate WALTER 16" drum-sander build-plan SVG sheets (A3 landscape).

Dimensions come from sander/walter/cad/walter_kernel.py (single source of truth).
Run:  python3 scripts/gen_walter_plans.py
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(ROOT, "..", "sander", "walter", "cad")
sys.path.insert(0, CAD)

from walter_kernel import (  # noqa: E402
    P,
    drive_inner,
    drive_outer,
    drum_gap,
    drum_rpm,
    feed_fpm,
    idle_inner,
    sfm,
)

OUT = os.path.join(ROOT, "..", "sander", "walter", "plans")
os.makedirs(OUT, exist_ok=True)

# ---- sheet primitives --------------------------------------------------------
W, Hpx = 1680, 1188  # A3 landscape @ ~4 px/mm
INK, DIM, ACC, PAPER, LIGHT = "#1c1914", "#6b5340", "#b4532a", "#f4efe6", "#d4cbb8"
STEEL, DRUM, BELT, SAFE = "#5c656c", "#7a5a3a", "#2a2a2c", "#3d5a4c"
GRAY, WARN = "#6e7578", "#8a3a2a"
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

    def rect(self, x, y, w, h, fill="none", stroke=INK, sw=2, dash=None, rx=0):
        d = f" stroke-dasharray='{dash}'" if dash else ""
        r = f" rx='{rx}'" if rx else ""
        self.add(
            f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' "
            f"fill='{fill}' stroke='{stroke}' stroke-width='{sw}'{d}{r}/>"
        )

    def circle(self, cx, cy, r, fill="none", stroke=INK, sw=2, dash=None):
        d = f" stroke-dasharray='{dash}'" if dash else ""
        self.add(
            f"<circle cx='{cx:.1f}' cy='{cy:.1f}' r='{r:.1f}' "
            f"fill='{fill}' stroke='{stroke}' stroke-width='{sw}'{d}/>"
        )

    def ellipse(self, cx, cy, rx, ry, fill="none", stroke=INK, sw=2):
        self.add(
            f"<ellipse cx='{cx:.1f}' cy='{cy:.1f}' rx='{rx:.1f}' ry='{ry:.1f}' "
            f"fill='{fill}' stroke='{stroke}' stroke-width='{sw}'/>"
        )

    def poly(self, pts, fill="none", stroke=INK, sw=2, close=True):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        tag = "polygon" if close else "polyline"
        self.add(f"<{tag} points='{p}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}'/>")

    def arc_path(self, d, fill="none", stroke=INK, sw=2):
        self.add(f"<path d='{d}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}'/>")

    def text(
        self, x, y, s, size=20, color=INK, anchor="start",
        mono=True, bold=False, rot=None, bg=False,
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

    def dim_h(self, x1, x2, y, label, offset=0, size=15):
        yy = y + offset
        for x in (x1, x2):
            self.line(x, y, x, yy + (8 if offset >= 0 else -8), 1, DIM)
        self.line(x1, yy, x2, yy, 1.4, DIM)
        for x, s in ((x1, 1), (x2, -1)):
            self.poly(
                [(x, yy), (x + s * 10, yy - 4), (x + s * 10, yy + 4)],
                fill=DIM, stroke=DIM, sw=0.5,
            )
        self.text((x1 + x2) / 2, yy - 6, label, size, DIM, "middle", bg=True)

    def dim_v(self, y1, y2, x, label, offset=0, size=15):
        xx = x + offset
        for y in (y1, y2):
            self.line(x, y, xx + (8 if offset >= 0 else -8), y, 1, DIM)
        self.line(xx, y1, xx, y2, 1.4, DIM)
        for y, s in ((y1, 1), (y2, -1)):
            self.poly(
                [(xx, y), (xx - 4, y + s * 10), (xx + 4, y + s * 10)],
                fill=DIM, stroke=DIM, sw=0.5,
            )
        self.text(
            xx + (12 if offset >= 0 else -12), (y1 + y2) / 2 + 5, label, size, DIM,
            "start" if offset >= 0 else "end", bg=True, rot=-90,
        )

    def note(self, x, y, lines, size=13, width=420):
        self.rect(x, y, width, 22 + 18 * len(lines), fill="#efe8dc", stroke=DIM, sw=1)
        for i, ln in enumerate(lines):
            self.text(x + 12, y + 22 + i * 18, ln, size, INK if i else ACC, bold=(i == 0))

    def titleblock(self):
        self.rect(0, 0, W, Hpx, fill=PAPER, stroke=INK, sw=3)
        self.rect(24, 24, W - 48, Hpx - 48, fill="none", stroke=INK, sw=1.2)
        self.line(24, Hpx - 90, W - 24, Hpx - 90, 1.5, INK)
        self.text(40, Hpx - 58, "WALTER", 28, ACC, bold=True, mono=False)
        self.text(175, Hpx - 62, f"{self.code}  ·  {self.title}", 18, INK, bold=True)
        self.text(40, Hpx - 34, self.scale_note, 13, DIM)
        self.text(W - 40, Hpx - 58, "16″ closed-frame drum thickness sander", 14, DIM, "end")
        self.text(W - 40, Hpx - 34, "Original engineering  ·  Rev C  ·  Shop build", 13, DIM, "end")

    def save(self, filename):
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
        return path


# ============================================================================
# W-1  General arrangement
# ============================================================================
def sheet_w1():
    s = Sheet("W-1", "General arrangement", "Scale ~1:8  ·  dimensions in inches")
    s.titleblock()
    s.text(40, 62, "INFEED ELEVATION", 15, ACC, bold=True)
    s.text(40, 82, "Looking from the operator side  ·  drum above conveyor  ·  16″ capacity", 13, DIM)

    # scale 18 px/in for front (width 22" → 396, height ~22" → 396)
    S = 18.0
    ox, oy = 70, 720  # origin at base bottom-left, y up in model → svg down

    def X(xin):
        return ox + xin * S

    def Z(zin):
        return oy - zin * S

    # base
    s.rect(X(0), Z(P["base_t"]), P["base_x"] * S, P["base_t"] * S, fill=LIGHT, stroke=INK, sw=1.6)
    # idle wall
    s.rect(X(0), Z(P["wall_h"]), P["wall_t"] * S, (P["wall_h"] - P["base_t"]) * S, fill="#c4b49a", stroke=INK, sw=1.6)
    # drive wall
    s.rect(X(drive_inner), Z(P["wall_h"]), P["wall_t"] * S, (P["wall_h"] - P["base_t"]) * S, fill="#c4b49a", stroke=INK, sw=1.6)
    # belt guard
    s.rect(X(drive_outer), Z(17.5), 2.2 * S, 16.5 * S, fill="#efe8dc", stroke=INK, sw=1.2, dash="6 4")
    # drum
    cx, cz = X(idle_inner + P["inner_w"] / 2), Z(P["drum_z"])
    s.ellipse(cx, cz, (P["drum_face"] / 2) * S * 0.08 + (P["inner_w"] / 2) * S, (P["drum_od"] / 2) * S,
              fill=DRUM, stroke=INK, sw=1.6)
    # actually drum is a circle in this view (axis across page)
    s.rect(X(idle_inner + drum_gap), Z(P["drum_z"] + P["drum_od"] / 2),
           P["drum_face"] * S, P["drum_od"] * S, fill=DRUM, stroke=INK, sw=1.8)
    s.rect(X(idle_inner + drum_gap), Z(P["drum_z"] + P["drum_od"] / 2 + 0.06),
           P["drum_face"] * S, 0.12 * S, fill=ACC, stroke="none", sw=0)
    # shaft ends
    s.circle(X(0.4), Z(P["drum_z"]), 0.4 * S, fill=STEEL, stroke=INK, sw=1)
    s.circle(X(drive_outer + 0.9), Z(P["drum_z"]), (P["pulley_drm"] / 2) * S, fill=STEEL, stroke=INK, sw=1.4)
    # table / conveyor
    tt = P["drum_z"] - P["drum_od"] / 2 - 1.5
    s.rect(X(idle_inner + 0.12), Z(tt), (P["inner_w"] - 0.24) * S, 0.9 * S, fill="#e8eef0", stroke=INK, sw=1.4)
    # hood
    s.rect(X(idle_inner + 0.1), Z(P["drum_z"] + 3.2), (P["inner_w"] - 0.2) * S, 1.6 * S,
           fill="none", stroke=SAFE, sw=1.8, dash="8 4")
    # motor (dashed in this view, behind guard)
    s.circle(X(drive_outer + 1.1), Z(4.6), (3.25) * S * 0.55, fill="#2a2a2c", stroke=INK, sw=1.2)

    s.dim_h(X(0), X(P["base_x"]), Z(0) + 8, '22.00" overall', offset=28)
    s.dim_h(X(idle_inner), X(drive_inner), Z(P["wall_h"]) - 8, '16.50" inner / 16.00" sanding', offset=-22)
    s.dim_v(Z(P["wall_h"]), Z(0), X(0), '20.00" walls', offset=-36)
    s.dim_v(Z(P["drum_z"] + P["drum_od"] / 2), Z(P["drum_z"] - P["drum_od"] / 2),
            X(drive_outer + 2.4), '5.00" drum', offset=24)

    s.text(X(idle_inner + 8.25), Z(tt) - 8, "CONVEYOR / PLATEN", 11, DIM, "middle")
    s.text(X(idle_inner + 8.25), Z(P["drum_z"]), "DRUM", 12, PAPER, "middle", bold=True)
    s.text(X(drive_outer + 1.1), Z(17.8), "GUARD", 11, DIM, "middle")

    # ---- side elevation ----
    s.text(520, 62, "DRIVE-SIDE ELEVATION", 15, ACC, bold=True)
    s.text(520, 82, "Motor below outfeed  ·  4L belt  ·  crowned conveyor  ·  4″ dust port", 13, DIM)

    S2 = 16.0
    ox2, oy2 = 540, 720

    def Y(yin):
        return ox2 + yin * S2

    def Z2(zin):
        return oy2 - zin * S2

    s.rect(Y(0), Z2(P["wall_h"]), P["base_y"] * S2, (P["wall_h"]) * S2, fill="#c4b49a", stroke=INK, sw=1.6)
    s.rect(Y(0), Z2(P["base_t"]), P["base_y"] * S2, P["base_t"] * S2, fill=LIGHT, stroke=INK, sw=1.4)
    # drum circle
    s.circle(Y(P["drum_y"]), Z2(P["drum_z"]), (P["drum_od"] / 2) * S2, fill=DRUM, stroke=INK, sw=1.8)
    s.circle(Y(P["drum_y"]), Z2(P["drum_z"]), 0.38 * S2, fill=STEEL, stroke=INK, sw=1)
    # pulley
    s.circle(Y(P["drum_y"]), Z2(P["drum_z"]), (P["pulley_drm"] / 2) * S2, fill="none", stroke=STEEL, sw=1.4, dash="4 3")
    # motor
    s.circle(Y(28.0), Z2(4.6), 3.25 * S2, fill="#2a2a2c", stroke=INK, sw=1.4)
    s.circle(Y(28.0), Z2(4.6), (P["pulley_mot"] / 2) * S2, fill=STEEL, stroke=INK, sw=1)
    # belt
    s.line(Y(P["drum_y"]), Z2(P["drum_z"] + P["pulley_drm"] / 2),
           Y(28.0), Z2(4.6 + P["pulley_mot"] / 2), 2.2, BELT)
    s.line(Y(P["drum_y"]), Z2(P["drum_z"] - P["pulley_drm"] / 2),
           Y(28.0), Z2(4.6 - P["pulley_mot"] / 2), 2.2, BELT)
    # conveyor rollers
    tt = P["drum_z"] - P["drum_od"] / 2 - 1.5
    for y in (P["roller_y_in"], P["roller_y_in"] + P["roller_cd"]):
        s.circle(Y(y), Z2(tt - 1.0), 1.0 * S2, fill=STEEL, stroke=INK, sw=1.2)
    s.rect(Y(P["roller_y_in"]), Z2(tt), P["roller_cd"] * S2, 0.12 * S2, fill=BELT, stroke="none")
    s.rect(Y(5.5), Z2(tt), 25.0 * S2, 0.75 * S2, fill="#e8eef0", stroke=INK, sw=1.2)
    # hood
    s.rect(Y(P["drum_y"] - 4.2), Z2(P["drum_z"] + 3.3), 8.4 * S2, 2.4 * S2,
           fill="none", stroke=SAFE, sw=1.6)
    s.circle(Y(P["drum_y"] + 5.2), Z2(P["drum_z"] + 0.8), 2.0 * S2, fill="none", stroke=STEEL, sw=1.5)
    s.text(Y(P["drum_y"] + 5.2), Z2(P["drum_z"] + 0.8) + 4, "4\"", 11, STEEL, "middle")

    s.dim_h(Y(0), Y(P["base_y"]), Z2(0) + 8, '36.00" depth', offset=28)
    s.dim_h(Y(P["roller_y_in"]), Y(P["roller_y_in"] + P["roller_cd"]), Z2(tt - 2.2),
            '26.86" roller c-c', offset=20)
    s.dim_v(Z2(P["drum_z"]), Z2(0), Y(0), '13.50" axis', offset=-32)

    s.text(Y(P["drum_y"]), Z2(P["drum_z"]) - 8, "DRUM 1089 RPM", 11, PAPER, "middle", bold=True)
    s.text(Y(28.0), Z2(4.6) + 5, "1 HP", 11, PAPER, "middle", bold=True)

    # spec panel
    s.rect(1160, 48, 496, 980, fill="#efe8dc", stroke=INK, sw=1.4)
    s.text(1180, 78, "DESIGN INTENT", 16, ACC, bold=True)
    rows = [
        ("Capacity", '16.00" wide  ×  0.06–4.00" thick'),
        ("Drum", '5.00" Ø  ×  16.00" face, birch stack'),
        ("Shaft", '¾" 1144 Stressproof × 22", 3/16" key'),
        ("Speed", f"{drum_rpm:.0f} RPM  ·  {sfm:.0f} SFM"),
        ("Motor", "1 HP TEFC 1725 RPM, NEMA 56C"),
        ("Pulleys", '3.00" motor / 4.75" drum, 4L440'),
        ("Feed", '16×60 PVC belt, 0–16 FPM PWM'),
        ("Rollers", '2.00" Al tube, 0.030" crown'),
        ("Elevation", "dual ¾-6 Acme, HTD-sync, 4.5\" travel"),
        ("Ways", "UHMW-lined dados + phenolic platen"),
        ("Bearings", "UCFL204-12 flange, self-aligning"),
        ("Drum jack", "idle-end ¼-20 ±0.040\" parallelism"),
        ("Dust", '4" port, 400 CFM, brush strip'),
        ("Envelope", '22 × 36 × 22" benchtop'),
        ("Mass (est.)", "95–110 lb without stand"),
    ]
    y = 108
    for k, v in rows:
        s.text(1180, y, k.upper(), 11, ACC, bold=True)
        s.text(1180, y + 18, v, 13, INK)
        s.line(1180, y + 28, 1636, y + 28, 0.6, LIGHT)
        y += 44

    s.text(1180, y + 8, "NOT A COPY OF SHOPNOTES #86", 12, WARN, bold=True)
    s.text(1180, y + 28, "Original redesign of Walters' documented", 12, DIM)
    s.text(1180, y + 46, "failure modes. Do not reproduce magazine art.", 12, DIM)

    s.save("W1_general.svg")


# ============================================================================
# W-2  Frame
# ============================================================================
def sheet_w2():
    s = Sheet("W-2", "Frame & bearing walls", "Scale ~1:6  ·  ¾\" Baltic birch, doubled at bearings")
    s.titleblock()

    s.text(40, 62, "IDLE-SIDE WALL — INNER FACE", 15, ACC, bold=True)
    s.text(40, 82, "1.50\" (two layers ¾\" BB, grain crossed)  ·  steel plate spreads flange-bearing load", 13, DIM)

    S = 22.0
    ox, oy = 50, 900

    def Y(v):
        return ox + v * S

    def Z(v):
        return oy - v * S

    # wall
    s.rect(Y(0), Z(P["wall_h"]), P["base_y"] * S, P["wall_h"] * S, fill="#c4b49a", stroke=INK, sw=2)
    # dado for table rail
    dado_z = 6.5
    s.rect(Y(4.5), Z(dado_z + 2.25), 27 * S, 2.25 * S, fill="#efe8dc", stroke=ACC, sw=1.4, dash="6 3")
    s.text(Y(18), Z(dado_z + 1.1), "UHMW DADO  0.50 × 2.25 × 27\"", 12, ACC, "middle")
    # bearing plate
    s.rect(Y(P["drum_y"] - 3), Z(P["drum_z"] + 3), 6 * S, 6 * S, fill=STEEL, stroke=INK, sw=1.6)
    s.circle(Y(P["drum_y"]), Z(P["drum_z"]), 0.55 * S, fill=PAPER, stroke=INK, sw=1.4)
    s.text(Y(P["drum_y"]), Z(P["drum_z"] + 3.4), "¼\" STEEL PLATE 6×6", 12, PAPER, "middle", bold=True)
    # jack screw holes
    for dy in (-2.2, 2.2):
        s.circle(Y(P["drum_y"] + dy), Z(P["drum_z"]), 0.13 * S, fill=ACC, stroke=INK, sw=1)
    s.text(Y(P["drum_y"]), Z(P["drum_z"] - 3.5), "¼-20 JACK SCREWS  (idle wall only)", 12, ACC, "middle")
    # slots for bearing bolts (vertical)
    for dy in (-1.85, 1.85):
        s.rect(Y(P["drum_y"] + dy) - 4, Z(P["drum_z"] + 0.45), 8, 0.90 * S, fill=PAPER, stroke=INK, sw=1)
    s.text(Y(P["drum_y"] + 4.6), Z(P["drum_z"]), "SLOTTED", 11, DIM, rot=-90)

    # stretchers
    s.rect(Y(1.0), Z(4.25), 1.5 * S, 3.5 * S, fill=LIGHT, stroke=INK, sw=1.4)
    s.rect(Y(P["base_y"] - 2.5), Z(4.25), 1.5 * S, 3.5 * S, fill=LIGHT, stroke=INK, sw=1.4)

    s.dim_h(Y(0), Y(P["base_y"]), Z(0) + 6, '36.00"', offset=26)
    s.dim_v(Z(P["wall_h"]), Z(0), Y(0), '20.00"', offset=-30)
    s.dim_v(Z(P["drum_z"] + P["drum_od"] / 2), Z(P["drum_z"] - P["drum_od"] / 2),
            Y(P["base_y"]), 'drum Ø shown dashed', offset=22)
    s.circle(Y(P["drum_y"]), Z(P["drum_z"]), (P["drum_od"] / 2) * S, fill="none", stroke=DRUM, sw=1.2, dash="5 4")

    # base plan
    s.text(900, 62, "BASE PLAN", 15, ACC, bold=True)
    s.text(900, 82, "¾\" BB  22.00 × 36.00  ·  1½ × 1½ hardwood rails under, ¾\" inset", 13, DIM)
    S3 = 18.0
    ox3, oy3 = 920, 820

    def Xp(v):
        return ox3 + v * S3

    def Yp(v):
        return oy3 - v * S3

    s.rect(Xp(0), Yp(P["base_y"]), P["base_x"] * S3, P["base_y"] * S3, fill=LIGHT, stroke=INK, sw=2)
    s.rect(Xp(0), Yp(P["base_y"]), P["wall_t"] * S3, P["base_y"] * S3, fill="#c4b49a", stroke=INK, sw=1.4)
    s.rect(Xp(drive_inner), Yp(P["base_y"]), P["wall_t"] * S3, P["base_y"] * S3, fill="#c4b49a", stroke=INK, sw=1.4)
    s.rect(Xp(idle_inner), Yp(2.5), P["inner_w"] * S3, 1.5 * S3, fill="#b9aa90", stroke=INK, sw=1.2)
    s.rect(Xp(idle_inner), Yp(P["base_y"] - 1.0), P["inner_w"] * S3, 1.5 * S3, fill="#b9aa90", stroke=INK, sw=1.2)
    # motor bay
    s.rect(Xp(drive_outer), Yp(32.5), 2.5 * S3, 10 * S3, fill="#efe8dc", stroke=INK, sw=1.2, dash="5 3")
    s.text(Xp(21.1), Yp(27), "MOTOR", 11, DIM, "middle", rot=-90)
    s.dim_h(Xp(0), Xp(P["base_x"]), Yp(0) + 8, '22.00"', offset=24)
    s.dim_h(Xp(idle_inner), Xp(drive_inner), Yp(P["base_y"]) - 6, '16.50" clear', offset=-20)
    s.dim_v(Yp(P["base_y"]), Yp(0), Xp(0), '36.00"', offset=-28)

    s.note(900, 860, [
        "FRAME NOTES",
        "• Glue two ¾\" BB skins per wall, grain crossed, clamp on a flat door.",
        "• Drill bearing holes after glue-up; use the steel plate as a drill jig.",
        "• Idle wall: vertical slots + jack screws. Drive wall: round holes, fixed.",
        "• Screw-and-glue stretchers with #8 × 2\" and waterproof PVA (Titebond III).",
        "• Do not use MDF for walls or drum. Walters' MDF discs cracked in service.",
    ], width=720)

    s.save("W2_frame.svg")


# ============================================================================
# W-3  Drum
# ============================================================================
def sheet_w3():
    s = Sheet("W-3", "Drum, shaft & abrasive", "Scale as noted  ·  turn in place after glue-up")
    s.titleblock()

    s.text(40, 62, "SHAFT  —  ¾\" × 22.00\"  1144 STRESSPROOF  (or 1045 ground)", 15, ACC, bold=True)

    # shaft drawing
    y = 140
    s.rect(80, y, 1400, 36, fill=STEEL, stroke=INK, sw=1.6)
    # features
    marks = [
        (80, "DRIVE END"),
        (80 + (0.5 / 22) * 1400, "pulley"),
        (80 + (2.0 / 22) * 1400, "drive bearing"),
        (80 + (3.5 / 22) * 1400, "end bell"),
        (80 + (19.5 / 22) * 1400, "end bell"),
        (80 + (21.0 / 22) * 1400, "idle bearing"),
        (1480, "IDLE"),
    ]
    s.dim_h(80, 1480, y + 36, '22.00"', offset=28)
    s.text(80, y - 12, "DRIVE", 12, DIM)
    s.text(1480, y - 12, "IDLE", 12, DIM, "end")
    # keyways
    s.rect(80 + (3.2 / 22) * 1400, y - 8, (4.0 / 22) * 1400, 8, fill=ACC, stroke=INK, sw=1)
    s.rect(80 + (14.8 / 22) * 1400, y - 8, (4.0 / 22) * 1400, 8, fill=ACC, stroke=INK, sw=1)
    s.text(80 + (5.2 / 22) * 1400, y - 14, "3/16\" SQ KEYWAY × 4.00\"", 12, ACC, "middle")
    s.text(80 + (16.8 / 22) * 1400, y - 14, "3/16\" SQ KEYWAY × 4.00\"", 12, ACC, "middle")
    s.text(80, y + 92, "Do not use plain cold-rolled as the only shaft. Walters' CRS + piano-wire pins worked, then he wanted better steel.", 13, DIM)
    s.text(80, y + 112, "Cross-drill is a last resort. A proper key is removable and does not stress-risers the shaft as badly as a through-pin.", 13, DIM)

    # disc stack
    s.text(40, 290, "DISC STACK  —  21 × ¾\" BALTIC BIRCH, Ø 5.125\" BLANK, TURNED TO 5.000\"", 15, ACC, bold=True)
    ox, oy = 80, 520
    for i in range(21):
        x = ox + i * 28
        fill = "#c4b49a" if i not in (0, 20) else STEEL
        s.rect(x, oy - 90, 24, 180, fill=fill, stroke=INK, sw=1)
        if i % 4 == 3 and i < 20:
            s.rect(x + 24, oy - 90, 4, 180, fill=PAPER, stroke=ACC, sw=0.8)
    s.text(ox + 10.5 * 28, oy + 110, "21 discs × 0.75\" = 15.75\"  +  two 1/8\" Al end bells  →  16.00\" face", 14, INK, "middle")
    s.text(ox + 10.5 * 28, oy + 132, "0.5 mm expansion gap every 4th glue line (Walters: hairline cracks without gaps)", 13, DIM, "middle")
    s.dim_h(ox, ox + 21 * 28 - 4, oy + 90, '15.75" stack', offset=0)

    # section through disc
    s.text(900, 290, "DISC DETAIL", 15, ACC, bold=True)
    s.circle(1120, 430, 90, fill="#c4b49a", stroke=INK, sw=2)
    s.circle(1120, 430, 14, fill=PAPER, stroke=INK, sw=1.6)
    s.rect(1106, 416, 28, 10, fill=ACC, stroke=INK, sw=1)  # key
    s.line(1120, 430, 1210, 370, 1, DIM)
    s.text(1220, 368, 'Ø 5.125" blank', 13, DIM)
    s.line(1120, 430, 1210, 490, 1, DIM)
    s.text(1220, 494, 'Ø 0.748" bore  (press on shaft)', 13, DIM)
    s.text(1120, 545, "Bore 0.002\" under shaft. Dry-fit. Polyurethane or epoxy.", 12, DIM, "middle")

    # wrap
    s.text(40, 690, "SPIRAL WRAP  —  3\" ROLL ON 4\" HOOK TAPE  ·  PAPER RETAINERS IN END BELLS", 15, ACC, bold=True)
    # drum rectangle with spiral
    s.rect(80, 720, 720, 140, fill=DRUM, stroke=INK, sw=1.6)
    for i in range(12):
        x0 = 90 + i * 58
        s.line(x0, 730, x0 + 70, 850, 2, ACC)
    s.rect(80, 720, 18, 140, fill=STEEL, stroke=INK, sw=1)
    s.rect(782, 720, 18, 140, fill=STEEL, stroke=INK, sw=1)
    # retainer slots
    s.rect(84, 770, 10, 40, fill=PAPER, stroke=INK, sw=1)
    s.rect(786, 770, 10, 40, fill=PAPER, stroke=INK, sw=1)
    s.text(440, 890, "Start in idle-end slot. Wrap 15–20°. Tuck drive-end into slot. No tape-on-tape lumps.", 13, DIM, "middle")

    s.note(860, 700, [
        "ABRASIVE + TRUING",
        "• PSA hook tape 4\" wide on the turned drum (covers 3\" paper gaps).",
        "• Prefer hook-and-loop paper so you are not glued to the drum forever",
        "  (Walters: Velcro so sticky that replacing it meant a new drum).",
        "• End-bell slots let you change paper without destroying the wrap.",
        "• After wrap, true the drum: lock table, run, feed a sanding block",
        "  on a carrier until the whole face cuts evenly.",
        "• Then set idle-end jack screws so a 16\" test board kisses both ends.",
        "• Stay off paint and varnish — they load paper instantly.",
    ], width=760, size=13)

    s.save("W3_drum.svg")


# ============================================================================
# W-4  Table elevation
# ============================================================================
def sheet_w4():
    s = Sheet("W-4", "Table elevation", "Dual ¾-6 Acme  ·  0.167\" per rev  ·  4.50\" travel")
    s.titleblock()

    s.text(40, 62, "ELEVATION SCHEME  —  REPLACE THE OAK DOWEL", 15, ACC, bold=True)
    s.text(40, 82, "Walters cut threads in a 2×4 with a wood tap. It worked. It also wears, swells, and has no sync.", 13, DIM)

    # schematic side view of screws
    S = 20.0
    ox, oy = 80, 780

    def Y(v):
        return ox + v * S

    def Z(v):
        return oy - v * S

    # walls ghost
    s.rect(Y(0), Z(18), 36 * S, 18 * S, fill="none", stroke=LIGHT, sw=1.5, dash="6 4")
    # platen
    s.rect(Y(5.5), Z(11.0), 25 * S, 1.0 * S, fill="#e8eef0", stroke=INK, sw=1.6)
    s.text(Y(18), Z(10.4), "PLATEN  ¾\" BB + ⅛\" HDPE/PHENOLIC", 12, DIM, "middle")
    # screws
    for y in (10.0, 26.0):
        s.rect(Y(y) - 7, Z(14), 14, 12 * S, fill=STEEL, stroke=INK, sw=1.4)
        s.rect(Y(y) - 18, Z(11.0), 36, 18, fill=ACC, stroke=INK, sw=1.2)
        s.text(Y(y), Z(5.2), "¾-6 ACME", 11, ACC, "middle")
    # sync belt
    s.line(Y(10), Z(3.4), Y(26), Z(3.4), 3, BELT)
    s.circle(Y(10), Z(3.4), 16, fill=STEEL, stroke=INK, sw=1.2)
    s.circle(Y(26), Z(3.4), 16, fill=STEEL, stroke=INK, sw=1.2)
    s.text(Y(18), Z(2.4), "5 mm HTD BELT  OR  #25 CHAIN  —  KEEPS SCREWS IN TIME", 12, DIM, "middle")
    # handwheel
    s.circle(Y(4.2), Z(3.4), 36, fill=PAPER, stroke=INK, sw=2)
    s.circle(Y(4.2), Z(3.4), 8, fill=STEEL, stroke=INK, sw=1)
    s.text(Y(4.2), Z(1.2), "4\" HANDWHEEL", 12, INK, "middle")
    # ways
    s.rect(Y(6), Z(12.8), 24 * S, 0.4 * S, fill="#cfd8dc", stroke=INK, sw=1)
    s.text(Y(18), Z(13.4), "UHMW WAYS IN DADOS (BOTH WALLS)", 12, DIM, "middle")
    # lock knobs
    s.circle(Y(8), Z(12.2), 10, fill=ACC, stroke=INK, sw=1)
    s.circle(Y(28), Z(12.2), 10, fill=ACC, stroke=INK, sw=1)
    s.text(Y(8), Z(12.9), "LOCK", 10, ACC, "middle")

    s.dim_h(Y(10), Y(26), Z(14), '16.00" screw spacing', offset=-24)
    s.dim_v(Z(11.0), Z(6.5), Y(36), '4.50" travel', offset=20)

    # detail: nut block
    s.text(900, 62, "NUT BLOCK  (each screw)", 15, ACC, bold=True)
    s.rect(940, 100, 220, 160, fill=LIGHT, stroke=INK, sw=1.6)
    s.rect(1020, 90, 60, 180, fill=STEEL, stroke=INK, sw=1.4)
    s.rect(1005, 155, 90, 50, fill=ACC, stroke=INK, sw=1.2)
    s.text(1050, 185, "BRONZE", 11, PAPER, "middle", bold=True)
    s.text(1050, 290, '2×2×3" hardwood + ¾-6 ACME nut', 13, DIM, "middle")
    s.text(1050, 310, "McMaster 6350K15 or equivalent", 12, DIM, "middle")

    s.text(900, 350, "RESOLUTION", 15, ACC, bold=True)
    rows = [
        ("Acme", "¾-6  →  0.1667\" per revolution"),
        ("Fine feel", "¼ turn = 0.042\"  ·  1/16 turn ≈ 0.010\""),
        ("Readout", "6\" digital caliper glued to idle wall, probe on platen"),
        ("Or", "0.001\" dial indicator on a magnetic base"),
        ("Lock", "two 5/16-18 star knobs clamp the rails after setting"),
        ("Check", "16\" straightedge + feeler gauges, both ends of drum"),
        ("Drift", "if one screw leads, skip a tooth on the HTD and retime"),
    ]
    y = 380
    for k, v in rows:
        s.text(920, y, k.upper(), 12, ACC, bold=True)
        s.text(1040, y, v, 13, INK)
        y += 28

    s.note(900, 600, [
        "WHY NOT FOUR CORNER SCREWS",
        "• Four independent screws will rack the platen. Two, mechanically timed,",
        "  plus stiff torsion-box platen, is how mills and commercial sanders do it.",
        "• Drum parallelism is a separate adjustment (idle bearing jack, sheet W-3/W-2).",
        "  Do not use table tilt to fake a tapered drum — that sands a wedge.",
        "• Optional: one screw + linear rails + a long torsion box. Dual is more forgiving.",
    ], width=720)

    s.note(40, 860, [
        "PLATEN  —  NOT FORMICA",
        "• Walters' Formica top scored immediately. Use ⅛\" HDPE, UHMW, or phenolic on ¾\" BB.",
        "• Face must be dead flat under the drum: torsion-box the platen (¼\" skins, ¾\" grid).",
        "• A 0.010\" hump under the drum prints as a stripe on every board.",
    ], width=800)

    s.save("W4_elevation.svg")


# ============================================================================
# W-5  Conveyor
# ============================================================================
def sheet_w5():
    s = Sheet("W-5", "Conveyor & tracking", "The subsystem that failed three times on the original")
    s.titleblock()

    s.text(40, 62, "WHY THE ORIGINAL CONVEYOR WOULD NOT TRACK", 15, ACC, bold=True)
    s.text(40, 82, "Walters used a 16×48 sanding belt on PVC pipe. He rebuilt it three times. Power feed was fine. Tracking was not.", 13, DIM)

    # three failure cartoons
    boxes = [
        (40, 110, "1  PVC IS NOT ROUND", "Pipe is extruded, oval, and", "not concentric on a shaft.", "Turn aluminum or stacked birch."),
        (430, 110, "2  NO CROWN", "Flat rollers do not self-center.", "A 0.030\" crown (high in the", "middle) is the whole trick."),
        (820, 110, "3  WRONG BELT", "Sanding belts are stiff, jointed,", "and want to walk. Use 2-ply", "PVC/PU conveyor belting."),
    ]
    for x, y, t, a, b, c in boxes:
        s.rect(x, y, 370, 130, fill="#efe8dc", stroke=WARN, sw=1.4)
        s.text(x + 16, y + 28, t, 14, WARN, bold=True)
        s.text(x + 16, y + 54, a, 13, INK)
        s.text(x + 16, y + 74, b, 13, INK)
        s.text(x + 16, y + 94, c, 13, INK)

    s.rect(1210, 110, 430, 130, fill="#e4eee6", stroke=SAFE, sw=1.4)
    s.text(1226, 138, "4  NO SKEW ADJUST", 14, SAFE, bold=True)
    s.text(1226, 164, "One roller must pivot a few", 13, INK)
    s.text(1226, 184, "thou. Two ¼-20 skew screws", 13, INK)
    s.text(1226, 204, "on the idle roller pillow.", 13, INK)

    # roller section
    s.text(40, 280, "CROWNED ROLLER  —  2.00\" OD × 16.25\"  ALUMINUM TUBE  ·  ⅝\" SHAFT", 15, ACC, bold=True)
    ox, oy = 80, 430
    # exaggerated crown
    s.poly(
        [(ox, oy), (ox + 700, oy), (ox + 700, oy + 70), (ox + 350, oy + 52), (ox, oy + 70)],
        fill=STEEL, stroke=INK, sw=1.6,
    )
    s.line(ox, oy + 35, ox + 700, oy + 35, 1, DIM, dash="4 3")
    s.dim_h(ox, ox + 700, oy + 70, '16.25" face', offset=24)
    s.dim_v(oy + 52, oy + 70, ox + 350, '0.030" crown (exaggerated)', offset=20)
    s.circle(ox - 20, oy + 35, 18, fill=STEEL, stroke=INK, sw=1.2)
    s.circle(ox - 20, oy + 35, 7, fill=PAPER, stroke=INK, sw=1)
    s.text(ox + 350, oy - 16, "Turn or lathe-file a gentle barrel. High point at mid-span. Both rollers.", 13, DIM, "middle")

    # tracking plan
    s.text(40, 560, "TRACKING  —  IDLE ROLLER SKEW", 15, ACC, bold=True)
    s.rect(80, 590, 640, 200, fill="#efe8dc", stroke=INK, sw=1.4)
    # rollers top view
    s.rect(120, 640, 28, 120, fill=STEEL, stroke=INK, sw=1.4)  # drive, fixed
    s.poly([(560, 648), (588, 652), (588, 748), (560, 752)], fill=STEEL, stroke=ACC, sw=1.6)  # idle skewed
    s.rect(148, 690, 412, 18, fill=BELT, stroke=INK, sw=1)
    s.text(134, 780, "DRIVE", 11, DIM, "middle")
    s.text(574, 780, "IDLE (skew)", 11, ACC, "middle")
    s.text(360, 625, "Belt walks toward the end that contacts first.", 12, DIM, "middle")
    s.note(80, 810, [
        "PROCEDURE",
        "1. Tension until the belt does not slip under a 16\" oak board.",
        "2. Run empty. If it walks left, skew idle so the right end leads slightly.",
        "3. Tiny moves. 1/8 turn of a ¼-20 is a lot. Mark the nuts.",
        "4. Then feed a board. Reload tension after the first hour — belts stretch.",
    ], width=640)

    # drive
    s.text(860, 280, "FEED DRIVE", 15, ACC, bold=True)
    rows = [
        ("Belt", "16.00\" × 60\" endless, 2-ply PVC, FS top / FS or bare back"),
        ("NOT", "a sanding belt. Not rubber inner-tube. Not canvas."),
        ("Centers", f"{P['roller_cd']:.2f}\"  (from 60\" belt − π·2.00\")"),
        ("Take-up", "¾\" of screw travel on idle bearings"),
        ("Motor", "24 V DC worm gearmotor, ~30 RPM at roller, PWM 0–16 FPM"),
        ("Calc", f"π × 2.00\" / 12 × 30 rpm  =  {feed_fpm:.1f} FPM at 30 rpm"),
        ("Mount", "Chain or HTD to drive roller. Motor on the TABLE so height is independent."),
        ("Platen", "UHMW under the belt, 1/32\" below roller crowns, dead flat"),
        ("Option B", "Delete conveyor. HDPE sliding table + push stick. Simpler. Slower."),
    ]
    y = 314
    for k, v in rows:
        s.text(860, y, k.upper(), 12, ACC, bold=True)
        s.text(980, y, v, 13, INK)
        y += 26

    s.note(860, 570, [
        "OPTION B  —  SLIDING TABLE  (if you do not want a belt)",
        "• 18×24\" HDPE on UHMW ways. Fence on the outfeed. Push with a carrier board.",
        "• Same drum, same elevation, same dust hood. No tracking to fight.",
        "• Heslop's first kickback was a short part. Never sand pieces shorter than 12\"",
        "  unless they are stuck to a carrier with hot-melt or carpet tape.",
    ], width=760)

    s.save("W5_conveyor.svg")


# ============================================================================
# W-6  Drive & electrics
# ============================================================================
def sheet_w6():
    s = Sheet("W-6", "Drive, belt & electrics", "1 HP TEFC  ·  hinged mount  ·  no-volt release")
    s.titleblock()

    s.text(40, 62, "BELT DRIVE  —  DO NOT HANG THE MOTOR ON GRAVITY ALONE", 15, ACC, bold=True)
    s.text(40, 82, "Walters' motor pivoted on a wooden dowel; weight tensioned the belt. On startup the pulley climbed and the belt went slack.", 13, DIM)

    # pulley diagram
    s.circle(280, 320, 95, fill=STEEL, stroke=INK, sw=2)   # drum pulley ~4.75 scaled
    s.circle(280, 320, 12, fill=PAPER, stroke=INK, sw=1)
    s.circle(280, 560, 60, fill="#2a2a2c", stroke=INK, sw=2)  # motor 3.00
    s.circle(280, 560, 10, fill=STEEL, stroke=INK, sw=1)
    s.line(280 - 95, 320, 280 - 60, 560, 8, BELT)
    s.line(280 + 95, 320, 280 + 60, 560, 8, BELT)
    s.text(280, 318, "4.75\"", 14, PAPER, "middle", bold=True)
    s.text(280, 558, "3.00\"", 13, PAPER, "middle", bold=True)
    s.text(280, 210, "DRUM PULLEY", 13, ACC, "middle", bold=True)
    s.text(280, 640, "MOTOR PULLEY", 13, ACC, "middle", bold=True)
    s.text(430, 430, f"{drum_rpm:.0f} RPM", 18, ACC, bold=True)
    s.text(430, 454, f"{sfm:.0f} SFM", 16, INK)
    s.text(430, 478, "1725 × 3.00 / 4.75", 13, DIM)

    s.note(80, 680, [
        "MOUNT",
        "• ¼\" steel hinge plate, 8 × 10, bolted to the drive wall.",
        "• Motor on 56C face (or foot) with slots for belt line-up.",
        "• Turnbuckle or 5/16\" all-thread from plate to base — set tension, lock nuts.",
        "• Optional gas spring as a helper, not as the only tension.",
        "• 4L440 link belt preferred (install without tearing the machine down).",
        "• Guard: ¼\" BB or perforated steel, fully enclosed, latch, no finger holes.",
    ], width=640)

    s.text(760, 62, "ELECTRICAL  —  115 V BRANCH, DEDICATED 20 A", 15, ACC, bold=True)
    # block diagram
    blocks = [
        (780, 110, "NEMA 5-20"),
        (1020, 110, "E-STOP"),
        (1260, 110, "MAG STARTER"),
        (780, 230, "OL RELAY"),
        (1020, 230, "DRUM MOTOR"),
        (1260, 230, "HOOD SW"),
        (780, 350, "24 V PSU"),
        (1020, 350, "PWM"),
        (1260, 350, "FEED MOTOR"),
    ]
    for x, y, t in blocks:
        s.rect(x, y, 200, 70, fill="#efe8dc", stroke=INK, sw=1.4, rx=4)
        s.text(x + 100, y + 42, t, 14, INK, "middle", bold=True)
    # arrows
    def arr(x1, y1, x2, y2):
        s.line(x1, y1, x2, y2, 1.6, INK)
    arr(980, 145, 1020, 145)
    arr(1220, 145, 1260, 145)
    arr(1360, 180, 1360, 230)
    arr(1260, 265, 1220, 265)
    arr(1020, 265, 980, 265)
    arr(880, 180, 880, 230)
    arr(880, 300, 880, 350)
    arr(980, 385, 1020, 385)
    arr(1220, 385, 1260, 385)

    s.text(780, 450, "Magnetic starter = no-volt release. If the lights blink, the drum does not restart in your hands.", 13, DIM)
    s.text(780, 472, "Hood switch is optional but cheap: machine will not run with the guard off.", 13, DIM)
    s.text(780, 494, "Feed PWM is extra-low-voltage. Fuse the 24 V separately. E-stop kills both contactors.", 13, DIM)

    s.note(760, 530, [
        "MOTOR SIZING",
        "• Walters ran 1/3 HP successfully — with very light passes on a hand-fed table.",
        "• Powered 16\" feed at 10 FPM will stall 1/3 HP in oak. Spec 1 HP; 1.5 HP is luxury.",
        "• Optional: 1 HP 3-phase + VFD, 800–1600 RPM drum for grit changes.",
        "• TEFC, not open drip-proof. This machine makes a dust storm (Walters' words).",
        "• Have a licensed electrician sign off if you are not one. This sheet is not a code drawing.",
    ], width=860)

    s.note(760, 740, [
        "STARTUP SEQUENCE",
        "1. Dust collector on.  2. Hood latched.  3. Table locked.  4. Drum on, wait for speed.",
        "5. Feed on, slow.  6. Board in.  7. If it stalls: feed off first, then drum.",
        "Never start the drum with a board already under it.",
    ], width=860)

    s.save("W6_drive.svg")


# ============================================================================
# W-7  Dust & safety
# ============================================================================
def sheet_w7():
    s = Sheet("W-7", "Dust hood & safety", "400 CFM  ·  4\" port  ·  this is not a planer")
    s.titleblock()

    s.text(40, 62, "HOOD  —  ¼\" BALTIC BIRCH  ·  SLIPS OVER THE DRUM  ·  LATCHES", 15, ACC, bold=True)

    S = 22.0
    ox, oy = 80, 520

    def Y(v):
        return ox + v * S

    def Z(v):
        return oy - v * S

    # drum
    s.circle(Y(8), Z(5), 2.5 * S, fill=DRUM, stroke=INK, sw=2)
    # rotation arrow
    s.arc_path(
        f"M {Y(8)+40:.1f},{Z(5)-2.5*S+8:.1f} A {2.5*S:.1f} {2.5*S:.1f} 0 0 1 {Y(8)+2.5*S-8:.1f},{Z(5)+20:.1f}",
        stroke=ACC, sw=2.5,
    )
    s.text(Y(11.2), Z(7.2), "ROTATION", 12, ACC, bold=True)
    s.text(Y(11.2), Z(6.5), "bottom moves toward infeed", 12, DIM)
    # hood U
    s.poly(
        [(Y(3), Z(8.4)), (Y(3), Z(3.8)), (Y(13), Z(3.8)), (Y(13), Z(8.4)),
         (Y(12.6), Z(8.4)), (Y(12.6), Z(4.2)), (Y(3.4), Z(4.2)), (Y(3.4), Z(8.4))],
        fill="#c5cec8", stroke=SAFE, sw=2,
    )
    s.circle(Y(13.6), Z(6.2), 2.0 * S, fill="none", stroke=STEEL, sw=2)
    s.text(Y(13.6), Z(6.2) + 4, "4\"", 14, STEEL, "middle", bold=True)
    # brush
    s.rect(Y(3.2), Z(3.6), 4.5 * S, 0.35 * S, fill=ACC, stroke=INK, sw=1)
    s.text(Y(5.4), Z(3.1), "BRUSH STRIP", 11, ACC, "middle")
    # board
    s.rect(Y(0.5), Z(2.4), 10 * S, 0.6 * S, fill=LIGHT, stroke=INK, sw=1.4)
    s.text(Y(5.5), Z(2.1), "WORK  →", 12, DIM, "middle")
    s.text(Y(5.5), Z(1.5), "INFEED", 12, ACC, "middle", bold=True)
    s.text(Y(16), Z(1.5), "OUTFEED  (port faces back)", 12, DIM, "middle")

    s.note(40, 600, [
        "DUST  —  WALTERS TOOK THE HOOD OFF ONCE AND ESTIMATED THE MACHINE",
        "COULD LAY ¼\" OF DUST ACROSS A SHOP IN 20 MINUTES. BELIEVE HIM.",
        "• 4\" port into a real collector, 400+ CFM. A shop-vac is a joke on a 16\" drum.",
        "• Seal the hood to the walls with foam weatherstrip. Leakage is what you breathe.",
        "• Board itself blocks side flow; some dust still exits the outfeed. Sweep.",
        "• MDF (if you ignore the drum spec) is the worst. Birch is merely bad.",
    ], width=760)

    s.text(860, 62, "SAFE USE  —  THIS IS NOT A PLANER", 15, ACC, bold=True)
    rules = [
        ("Light passes", "0.005–0.015\" per pass. If the motor note changes, you took too much."),
        ("No short stock", "Minimum 12\" long, or hot-melt to a carrier. Heslop kicked a small part."),
        ("Grain", "Feed with the grain when you can. Cross-grain is fine; just slower."),
        ("Grit", "80 for thicknessing. 120/150 for finish. Do not skip from 80 to 220 on the drum."),
        ("Snipe", "Infeed and outfeed rollers/platen must be coplanar. Support long boards."),
        ("Taper", "Idle jack can sand a controlled taper. Zero the jack for flat work."),
        ("Paper", "Stop if you smell burning or see glaze. Dull paper heats the drum."),
        ("Hands", "Never reach under the drum. Use a push block on the outfeed."),
        ("Hearing", "1 HP + drum is loud. Hearing protection is not optional."),
        ("Fire", "Empty the collector. Fine sanding dust is fuel. No finishing vapors in the shop."),
    ]
    y = 100
    for k, v in rules:
        s.rect(860, y - 18, 760, 44, fill="#efe8dc", stroke=LIGHT, sw=1)
        s.text(876, y, k.upper(), 12, ACC, bold=True)
        s.text(1040, y, v, 13, INK)
        y += 50

    s.note(860, 620, [
        "INTERLOCKS (minimum)",
        "• E-stop in reach of the operator's left hand (infeed corner).",
        "• Magnetic starter — power blip does not auto-restart.",
        "• Belt guard closed. Hood latched. No jewelry, no gloves on rotating shafts.",
        "• Disconnect / lockout before paper changes or bearing work.",
    ], width=760)

    s.save("W7_dust_safety.svg")


# ============================================================================
# W-8  Cut list & BOM
# ============================================================================
def sheet_w8():
    s = Sheet("W-8", "Cut list, BOM & hardware", "Shop-build  ·  buy extra ply  ·  prices are 2026-ish ballpark")
    s.titleblock()

    s.text(40, 58, "PLYWOOD  —  ¾\" BALTIC BIRCH (18 mm) UNLESS NOTED", 14, ACC, bold=True)

    ply = [
        ("A", "Base", '22.00 × 36.00 × ¾"', "1"),
        ("B", "Idle wall (2 layers)", '20.00 × 36.00 × ¾"', "2"),
        ("C", "Drive wall (2 layers)", '20.00 × 36.00 × ¾"', "2"),
        ("D", "Stretchers", '16.50 × 3.50 × ¾"', "2"),
        ("E", "Base rails (hard maple)", '33.00 × 1.50 × 1.50"', "2"),
        ("F", "Platen skins", '16.25 × 25.00 × ¼"', "2"),
        ("G", "Platen grid", '¾\" strips, ~8 bf', "—"),
        ("H", "Table rails", '25.00 × 2.00 × ½"', "2"),
        ("J", "Drum discs Ø 5.125\"", '¾\" × 21 discs', "21"),
        ("K", "Hood panels", '¼\" BB, ~4 ft²', "1 sheet ¼\""),
        ("L", "Belt guard", '17 × 17 × ¼\" + edges', "1"),
        ("M", "Nut blocks", '2.00 × 2.00 × 3.00"', "2"),
    ]
    y = 78
    s.text(40, y, "ID", 11, DIM, bold=True)
    s.text(90, y, "PART", 11, DIM, bold=True)
    s.text(360, y, "SIZE", 11, DIM, bold=True)
    s.text(620, y, "QTY", 11, DIM, bold=True)
    y = 96
    for i, (i_d, name, size, qty) in enumerate(ply):
        if i % 2 == 0:
            s.rect(36, y - 14, 700, 22, fill="#efe8dc", stroke="none", sw=0)
        s.text(40, y, i_d, 13, ACC, bold=True)
        s.text(90, y, name, 13, INK)
        s.text(360, y, size, 13, INK)
        s.text(620, y, qty, 13, INK)
        y += 22
    s.text(40, y + 8, "Sheet count: three 5×5 (or 5×10) ¾\" BB + one ¼\" BB. Buy the good stuff — voids become vibration.", 12, DIM)

    s.text(780, 58, "HARDWARE", 14, ACC, bold=True)
    hw = [
        ("Shaft", '¾" × 22" 1144 Stressproof, keyed'),
        ("Bearings (drum)", "UCFL204-12  2-bolt flange  ×2"),
        ("Bearings (rollers)", "UCFL201-10  ⅝\"  ×4"),
        ("Rollers", '2.00" Al tube × 16.25" ×2, ⅝" shaft'),
        ("Acme", "¾-6 × 12\" screws ×2 + bronze nuts ×2"),
        ("Sync", "5 mm HTD 15 mm belt + 16T pulleys ×2"),
        ("Handwheel", '4" cast, ¾" bore'),
        ("Pulleys", '3.00" and 4.75" 4L, ¾" bore'),
        ("Belt", "4L440 link belt"),
        ("Conveyor belt", '16" × 60" 2-ply PVC, endless'),
        ("Motor", "1 HP TEFC 1725 RPM 115 V 56C"),
        ("Feed motor", "24 V DC worm gearmotor ~30 RPM"),
        ("PWM + PSU", "24 V 5 A meanwell-class + PWM"),
        ("Starter", "Magnetic / DP contactor + OL + NOVR"),
        ("E-stop", "40 mm mushroom, NC, 1×"),
        ("Switch", "Hood interlock, optional"),
        ("Plate", '¼" × 6 × 6 steel ×2  (bearing)'),
        ("Hinge plate", '¼" × 8 × 10 steel'),
        ("UHMW", "1/8 × 2 × 48 strip (ways) + platen face"),
        ("Hook tape", '4" PSA hook, 5 yd'),
        ("Abrasive", '3" × 25\' rolls, 80 / 120 / 150'),
        ("Port", '4" dust flange + 12" hose'),
        ("Brush", "nylon strip, 16\""),
        ("Fasteners", "#8 / 5/16 / ¼-20 assortment, T-nuts"),
        ("Finish", "wipe-on poly or paint; oil the ways"),
    ]
    y = 78
    for i, (k, v) in enumerate(hw):
        if i % 2 == 0:
            s.rect(776, y - 14, 860, 20, fill="#efe8dc", stroke="none", sw=0)
        s.text(786, y, k.upper(), 11, ACC, bold=True)
        s.text(980, y, v, 12, INK)
        y += 20

    s.text(40, 430, "BUILD SEQUENCE", 14, ACC, bold=True)
    phases = [
        ("1  DRUM", "Bandsaw discs. Bore on the drill press with a fence. Dry-stack on the keyed shaft with 0.5 mm gaps every 4. Glue. True between centers or in the machine."),
        ("2  FRAME", "Glue doubled walls. Cut dados. Bolt steel plates. Stretchers. Base rails. Square the box before the glue grabs — this is the machine's accuracy."),
        ("3  TABLE", "Torsion-box platen. UHMW ways. Nut blocks. Acme screws + HTD. Digital caliper. Lock knobs. Check travel is parallel."),
        ("4  CONVEYOR", "Turn crowns. Mount rollers. Skew hardware. Endless-splice or buy endless. Track empty, then loaded. PWM feed last."),
        ("5  DRIVE", "Hinge plate, motor, pulleys, link belt, turnbuckle, guard. Wire starter / E-stop / optional hood switch. Dust port."),
        ("6  TUNE", "Paper wrap. True drum. Jack idle bearing to a 16\" test board. 0.010\" passes in poplar first. Then oak. Then trust it."),
    ]
    y = 456
    for t, body in phases:
        s.text(40, y, t, 13, ACC, bold=True)
        s.text(160, y, body, 12, INK)
        y += 36

    s.note(40, 680, [
        "BUDGET  (order-of-magnitude, USD, 2026 hobby-shop pricing)",
        "Plywood + hardwood  $180–260    Steel / shaft / bearings  $160–220    Motor 1 HP TEFC  $180–280",
        "Conveyor belt + rollers + gearmotor  $200–320    Acme / HTD / pulleys / belt  $120–180",
        "Electrics (starter, E-stop, PWM, PSU, cord)  $140–220    Abrasive + hook tape + dust bits  $80–140",
        "TOTAL  ≈  $1,100–1,600  depending on what is already on the shelf. A used SuperMax 16-32 is ~$1,800–2,400.",
        "You are buying capability and the right to repair it, not a bargain against Harbor Freight.",
    ], width=1600)

    s.note(40, 860, [
        "SOURCES & LINEAGE  —  READ THESE, THEN BUILD THIS, NOT THOSE",
        "Ron Walters, woodgears.ca/reader/walters/drum_sander.html  ·  YouTube W-5Sj6kBVic (same machine).",
        "Simon Heslop (crowned plywood rollers, birch drum, kickback on short stock). Todd Hunt (open C-frame, 6\" thick).",
        "ShopNotes #86 is copyrighted. Do not scan or redraw it. This package is an original redesign of the failure modes they all published.",
        "Not a stamped PE document. Shafting, electrics, and guarding are your responsibility. If a number on a sheet fights the CAD, trust the CAD parameters and file an issue.",
    ], width=1600)

    s.save("W8_bom.svg")


def main():
    sheet_w1()
    sheet_w2()
    sheet_w3()
    sheet_w4()
    sheet_w5()
    sheet_w6()
    sheet_w7()
    sheet_w8()
    from gen_walter_plans_extra import emit as emit_extra
    emit_extra()
    print("WALTER plans done →", OUT)


if __name__ == "__main__":
    main()
