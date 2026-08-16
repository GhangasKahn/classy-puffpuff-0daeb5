#!/usr/bin/env python3
"""Wandel-style individual fabrication sheets for WALTER DS-16.

Each make part, plus assembly and hardware sheets: isometric solid, 2D face
with datum dimensioning, hole chart, and shop callouts.

Run after the SSOT is valid:
  python3 scripts/gen_walter_part_sheets.py
"""

from __future__ import annotations

import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "shop", "drum-sander", "cad"))

from walter_ds16 import GEOM as G  # noqa: E402
from walter_ds16 import SPEC as S  # noqa: E402
from walter_ds16 import (  # noqa: E402
    AXIS_I_SHELL,
    MECH_ADJ_AT_WORK,
    PROJECT,
    fmt_in,
    hardware,
    parts,
    shop_drawings,
    side_features,
    stretcher_records,
)

OUT = os.path.join(ROOT, "shop", "drum-sander", "plans")
os.makedirs(OUT, exist_ok=True)

# A3 landscape @ ~4 px/mm — same canvas as D-1…D-12
W, Hpx = 1680, 1188
INK = "#1a1a1a"
DIM = "#3d4a38"
NOTE = "#2a2a2a"
PAPER = "#ffffff"
GREEN = "#5f8f62"  # plywood structure (Wandel)
TAN = "#e6d09a"  # solid wood / moving parts
UHMW = "#d5d9de"
STEEL = "#c5c8cc"
ALUM = "#9aa8b0"
BRONZE = "#c4783a"
MDF = "#c4b496"
PHEN = "#8a9098"
KNOB = "#2c2e32"
ACC = "#3d5a4c"
LIGHT = "#eef1ea"
MONO = "font-family='IBM Plex Mono, Menlo, monospace'"
SANS = "font-family='Libre Franklin, Helvetica, Arial, sans-serif'"


def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inch(v: float, nd: int = 2) -> str:
    return fmt_in(v, nd)


# ---------------------------------------------------------------------------
# Mesh / isometric (y-up, same convention as gen_drum_sander_iso.py)
# ---------------------------------------------------------------------------


def shade(hex_color: str, k: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = max(0, min(255, int(r * k)))
    g = max(0, min(255, int(g * k)))
    b = max(0, min(255, int(b * k)))
    return f"#{r:02x}{g:02x}{b:02x}"


class Mesh:
    def __init__(self, color: str):
        self.color = color
        self.faces: list[tuple[tuple[tuple[float, float, float], ...], float]] = []

    def add_face(self, verts: list[tuple[float, float, float]]) -> None:
        if len(verts) < 3:
            return
        ax, ay, az = verts[0]
        bx, by, bz = verts[1]
        cx, cy, cz = verts[2]
        ux, uy, uz = bx - ax, by - ay, bz - az
        vx, vy, vz = cx - ax, cy - ay, cz - az
        nx = uy * vz - uz * vy
        ny = uz * vx - ux * vz
        nz = ux * vy - uy * vx
        nlen = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        nx, ny, nz = nx / nlen, ny / nlen, nz / nlen
        lit = max(0.35, min(1.0, 0.45 + 0.55 * (nx * 0.35 + ny * 0.85 - nz * 0.4)))
        self.faces.append((tuple(verts), lit))


def box(color, x0, y0, z0, dx, dy, dz) -> Mesh:
    x1, y1, z1 = x0 + dx, y0 + dy, z0 + dz
    p = [
        (x0, y0, z0),
        (x1, y0, z0),
        (x1, y1, z0),
        (x0, y1, z0),
        (x0, y0, z1),
        (x1, y0, z1),
        (x1, y1, z1),
        (x0, y1, z1),
    ]
    m = Mesh(color)
    for idx in ((0, 1, 2, 3), (5, 4, 7, 6), (4, 0, 3, 7), (1, 5, 6, 2), (4, 5, 1, 0), (3, 2, 6, 7)):
        m.add_face([p[i] for i in idx])
    return m


def cyl_x(color, cx, cy, cz, length, r, segs=16) -> Mesh:
    m = Mesh(color)
    x0, x1 = cx - length / 2, cx + length / 2
    ring0, ring1 = [], []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        y = cy + r * math.cos(a)
        z = cz + r * math.sin(a)
        ring0.append((x0, y, z))
        ring1.append((x1, y, z))
    for i in range(segs):
        j = (i + 1) % segs
        m.add_face([ring0[i], ring0[j], ring1[j], ring1[i]])
    m.add_face(list(reversed(ring0)))
    m.add_face(ring1)
    return m


def cyl_z(color, cx, cy, cz, length, r, segs=16) -> Mesh:
    m = Mesh(color)
    z0, z1 = cz - length / 2, cz + length / 2
    ring0, ring1 = [], []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        x = cx + r * math.cos(a)
        y = cy + r * math.sin(a)
        ring0.append((x, y, z0))
        ring1.append((x, y, z1))
    for i in range(segs):
        j = (i + 1) % segs
        m.add_face([ring0[i], ring0[j], ring1[j], ring1[i]])
    m.add_face(list(reversed(ring0)))
    m.add_face(ring1)
    return m


def iso_project(p):
    x, y, z = p
    sx = (x - z) * math.cos(math.radians(30))
    sy = y + (x + z) * math.sin(math.radians(30))
    depth = x * 0.3 + y * 0.2 + z * 0.9
    return sx, sy, depth


def iso_group(meshes: list[Mesh], x: float, y: float, w: float, h: float, pad: float = 12) -> str:
    tris: list[tuple[float, str, list[tuple[float, float]]]] = []
    for m in meshes:
        for verts, lit in m.faces:
            proj = [iso_project(v) for v in verts]
            depth = sum(p[2] for p in proj) / len(proj)
            area = 0.0
            for i, p in enumerate(proj):
                q = proj[(i + 1) % len(proj)]
                area += p[0] * q[1] - q[0] * p[1]
            if area <= 0:
                continue
            col = shade(m.color, 0.55 + 0.45 * lit)
            tris.append((depth, col, [(p[0], p[1]) for p in proj]))
    if not tris:
        return ""
    tris.sort(key=lambda t: t[0])
    xs = [px for _, _, pts in tris for px, _ in pts]
    ys = [py for _, _, pts in tris for _, py in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    spanx = max(maxx - minx, 1e-6)
    spany = max(maxy - miny, 1e-6)
    sc = min((w - 2 * pad) / spanx, (h - 2 * pad) / spany)
    ox = x + pad - minx * sc
    oy = y + h - pad + miny * sc  # flip y into SVG
    bits = [f"<g stroke='{INK}' stroke-width='1.1' stroke-linejoin='round'>"]
    for _, col, pts in tris:
        poly = " ".join(f"{ox + px * sc:.1f},{oy - py * sc:.1f}" for px, py in pts)
        bits.append(f"<polygon points='{poly}' fill='{col}'/>")
    bits.append("</g>")
    return "\n".join(bits)


# ---------------------------------------------------------------------------
# Drawing sheet
# ---------------------------------------------------------------------------


class Sheet:
    def __init__(self, code: str, title: str, scale_note: str, subtitle: str = ""):
        self.code, self.title, self.scale_note = code, title, scale_note
        self.subtitle = subtitle
        self.b: list[str] = []

    def add(self, s: str) -> None:
        self.b.append(s)

    def line(self, x1, y1, x2, y2, w=1.4, color=INK, dash=None):
        d = f" stroke-dasharray='{dash}'" if dash else ""
        self.add(
            f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' "
            f"stroke='{color}' stroke-width='{w}'{d}/>"
        )

    def rect(self, x, y, w, h, fill="none", stroke=INK, sw=1.6, dash=None, rx=0):
        d = f" stroke-dasharray='{dash}'" if dash else ""
        r = f" rx='{rx}'" if rx else ""
        self.add(
            f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' "
            f"fill='{fill}' stroke='{stroke}' stroke-width='{sw}'{d}{r}/>"
        )

    def circle(self, cx, cy, r, fill="none", stroke=INK, sw=1.5):
        self.add(
            f"<circle cx='{cx:.1f}' cy='{cy:.1f}' r='{r:.1f}' fill='{fill}' "
            f"stroke='{stroke}' stroke-width='{sw}'/>"
        )

    def poly(self, pts, fill="none", stroke=INK, sw=1.4, close=True):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        tag = "polygon" if close else "polyline"
        self.add(f"<{tag} points='{p}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}'/>")

    def text(self, x, y, s, size=16, color=INK, anchor="start", mono=True, bold=False, rot=None, bg=False):
        f = MONO if mono else SANS
        wgt = " font-weight='600'" if bold else ""
        r = f" transform='rotate({rot} {x:.1f} {y:.1f})'" if rot is not None else ""
        if bg and rot is None:
            ww = max(8, len(s) * size * 0.56)
            bx = {"start": x - 3, "middle": x - ww / 2 - 3, "end": x - ww - 3}[anchor]
            self.add(
                f"<rect x='{bx:.1f}' y='{y - size + 1:.1f}' width='{ww + 6:.1f}' "
                f"height='{size + 5:.1f}' fill='{PAPER}'/>"
            )
        self.add(
            f"<text x='{x:.1f}' y='{y:.1f}' {f} font-size='{size}' fill='{color}' "
            f"text-anchor='{anchor}'{wgt}{r}>{esc(s)}</text>"
        )

    def dim_h(self, x1, x2, y, label, offset=0, size=13):
        yy = y + offset
        for x in (x1, x2):
            self.line(x, y, x, yy + (6 if offset >= 0 else -6), 0.9, DIM)
        self.line(x1, yy, x2, yy, 1.15, DIM)
        for x, sgn in ((x1, 1), (x2, -1)):
            self.poly([(x, yy), (x + sgn * 8, yy - 3.2), (x + sgn * 8, yy + 3.2)], fill=DIM, stroke=DIM, sw=0.4)
        self.text((x1 + x2) / 2, yy - 5 if offset >= 0 else yy + 12, label, size, DIM, "middle", bg=True)

    def dim_v(self, y1, y2, x, label, offset=0, size=13):
        xx = x + offset
        for y in (y1, y2):
            self.line(x, y, xx + (6 if offset >= 0 else -6), y, 0.9, DIM)
        self.line(xx, y1, xx, y2, 1.15, DIM)
        for y, sgn in ((y1, 1), (y2, -1)):
            self.poly([(xx, y), (xx - 3.2, y + sgn * 8), (xx + 3.2, y + sgn * 8)], fill=DIM, stroke=DIM, sw=0.4)
        self.text(
            xx + (10 if offset >= 0 else -10),
            (y1 + y2) / 2 + 4,
            label,
            size,
            DIM,
            "start" if offset >= 0 else "end",
            bg=True,
            rot=-90,
        )

    def leader(self, x, y, tx, ty, text, size=12, anchor=None):
        self.line(x, y, tx, ty, 1.0, INK)
        self.circle(x, y, 2.2, fill=INK, stroke=INK, sw=0.5)
        if anchor is None:
            anchor = "start" if tx >= x else "end"
        self.text(tx + (6 if anchor == "start" else -6), ty - 2, text, size, NOTE, anchor, mono=False)

    def titleblock(self, qty: str = "", material: str = "", evidence: str = ""):
        self.rect(0, 0, W, Hpx, fill=PAPER, stroke=INK, sw=2.4)
        self.rect(20, 20, W - 40, Hpx - 40, fill="none", stroke=INK, sw=1.0)
        self.line(20, 78, W - 20, 78, 1.4, INK)
        self.line(20, Hpx - 78, W - 20, Hpx - 78, 1.4, INK)
        self.text(36, 52, self.code, 28, ACC, bold=True)
        self.text(200, 48, self.title, 22, INK, bold=True, mono=False)
        if self.subtitle:
            self.text(200, 70, self.subtitle, 13, DIM, mono=False)
        if qty:
            self.text(1180, 48, qty, 14, INK, "end", bold=True)
        if material:
            self.text(1180, 70, material, 12, DIM, "end", mono=False)
        self.text(36, Hpx - 52, "WALTER DS-16", 16, ACC, bold=True, mono=False)
        self.text(200, Hpx - 54, self.scale_note, 12, DIM)
        self.text(W - 36, Hpx - 54, f"Rev {S.revision} geometry · fab {S.fabrication_rev} · FABRICATION REVIEW · inches", 12, DIM, "end")
        self.text(W - 36, Hpx - 34, "Confirm flange BCD before drilling · " + (evidence or PROJECT["unit_policy"]), 11, DIM, "end")

    def iso_frame(self, x, y, w, h, caption: str, meshes: list[Mesh]):
        self.rect(x, y, w, h, fill=LIGHT, stroke=INK, sw=1.0)
        self.add(iso_group(meshes, x, y, w, h))
        self.text(x + 10, y + 18, caption, 11, DIM, bold=True)

    def notes(self, x, y, lines: list[str], title: str = "SHOP NOTES"):
        self.text(x, y, title, 13, ACC, bold=True)
        yy = y + 20
        for line in lines:
            wrap = _wrap(line, 62)
            for i, row in enumerate(wrap):
                self.text(x, yy, ("• " if i == 0 else "  ") + row, 12, NOTE, mono=False)
                yy += 16
            yy += 4
        return yy

    def save(self, filename: str) -> None:
        path = os.path.join(OUT, filename)
        svg = (
            f"<?xml version='1.0' encoding='UTF-8'?>\n"
            f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{Hpx}' "
            f"viewBox='0 0 {W} {Hpx}'>\n" + "\n".join(self.b) + "\n</svg>\n"
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print("wrote", path)


def _wrap(text: str, width: int) -> list[str]:
    words = text.split()
    rows, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if len(trial) <= width:
            cur = trial
        else:
            if cur:
                rows.append(cur)
            cur = w
    if cur:
        rows.append(cur)
    return rows or [""]


def part_by_id(pid: str) -> dict:
    for p in parts():
        if p["part_id"] == pid:
            return p
    raise KeyError(pid)


# ---------------------------------------------------------------------------
# P-001L / P-001R — the sheets a builder actually fabricates from
# ---------------------------------------------------------------------------


def sheet_p001(hand: str) -> None:
    pid = f"P-001{hand}"
    p = part_by_id(pid)
    feat = side_features(hand=hand)
    name = "Side panel, drive (left)" if hand == "L" else "Side panel, idler (right)"
    sh = Sheet(
        pid,
        name,
        f"Inner face · ~18 px/inch · print A3 · Datum Y0 = infeed · Datum Z0 = bottom",
        subtitle=p["notes"],
    )
    sh.titleblock(
        qty="MAKE 1  ·  stack-drill with mate",
        material=f'{p["material"]}  ·  {p["finished_size"]}',
        evidence=feat["evidence"]["flange_bcd"],
    )

    # 2D inner face: Y → +X paper, Z → −Y paper
    sc = 18.0
    ox, oy = 90, 900

    def X(y_in: float) -> float:
        return ox + y_in * sc

    def Y(z_in: float) -> float:
        return oy - z_in * sc

    sh.rect(X(0), Y(S.side_height), S.side_depth * sc, S.side_height * sc, fill=GREEN, stroke=INK, sw=2.0)
    sh.text(X(S.side_depth / 2), Y(S.side_height) - 14, "INNER FACE — looking from inside the machine", 13, ACC, "middle", bold=True)

    way = feat["way"]
    sh.rect(
        X(way["y0"]),
        Y(way["z1"]),
        (way["y1"] - way["y0"]) * sc,
        (way["z1"] - way["z0"]) * sc,
        fill=UHMW,
        stroke=ACC,
        sw=1.4,
    )
    sh.text(X((way["y0"] + way["y1"]) / 2), Y(way["z1"]) - 8, f'J-002 way rebate  {inch(way["depth"], 3)}" deep', 11, ACC, "middle", bold=True)

    for d in feat["dados"]:
        sh.rect(
            X(d["y0"]),
            Y(d["z1"]),
            (d["y1"] - d["y0"]) * sc,
            (d["z1"] - d["z0"]) * sc,
            fill=TAN,
            stroke=INK,
            sw=1.2,
        )
        sh.text(X(d["y1"]) + 8, Y((d["z0"] + d["z1"]) / 2) + 4, d["id"], 10, DIM)

    by, bz = feat["bearing_cl"]["y"], feat["bearing_cl"]["z"]
    sh.circle(X(by), Y(bz), (feat["bearing_cl"]["shaft_clear_dia"] / 2) * sc, fill=PAPER, stroke=INK, sw=1.4)
    sh.circle(X(by), Y(bz), 2.4, fill=INK, stroke=INK, sw=0.5)
    for b in feat["flange_bolts"]:
        sh.circle(X(b["y"]), Y(b["z"]), (b["dia"] / 2) * sc, fill=PAPER, stroke=INK, sw=1.3)
        sh.text(X(b["y"]) + 10, Y(b["z"]) - 8, b["id"], 9, DIM)

    for scw in feat["stretcher_screws"]:
        sh.circle(X(scw["y"]), Y(scw["z"]), 0.09 * sc, fill="none", stroke=INK, sw=1.0)

    if feat["motor_pivot"]:
        mp = feat["motor_pivot"]
        sh.circle(X(mp["y"]), Y(mp["z"]), (mp["dia"] / 2) * sc + 3, fill="none", stroke=ACC, sw=1.4)
        sh.circle(X(mp["y"]), Y(mp["z"]), (mp["dia"] / 2) * sc, fill=PAPER, stroke=INK, sw=1.2)
        sh.leader(X(mp["y"]), Y(mp["z"]), X(0) - 10, Y(mp["z"]) + 40, "Motor pivot ¼-20  (drive only)", 12)

    if feat["indicator_pad"]:
        ip = feat["indicator_pad"]
        sh.circle(X(ip["y"]), Y(ip["z"]), (ip["dia"] / 2) * sc, fill=PAPER, stroke=ACC, sw=1.4)
        sh.leader(X(ip["y"]), Y(ip["z"]), X(S.side_depth) + 20, Y(ip["z"]) - 30, "A-clock pad ¼-20  (drive only)", 12)

    # overall dims
    sh.dim_h(X(0), X(S.side_depth), Y(0), f'{inch(S.side_depth)}"', offset=36)
    sh.dim_v(Y(0), Y(S.side_height), X(0), f'{inch(S.side_height)}"', offset=-40)
    sh.dim_h(X(0), X(by), Y(S.side_height), f'{inch(by)}"', offset=-28)
    sh.dim_v(Y(0), Y(bz), X(S.side_depth), f'{inch(bz)}"', offset=32)
    sh.dim_h(X(way["y0"]), X(way["y1"]), Y(way["z0"]), f'{inch(way["y1"] - way["y0"])}" way Y', offset=22)
    sh.dim_v(Y(way["z0"]), Y(way["z1"]), X(way["y0"]), f'{inch(way["z1"] - way["z0"])}" way Z', offset=-22)
    d0 = feat["dados"][0]
    sh.dim_h(X(0), X(d0["y0"]), Y(d0["z0"]), f'{inch(d0["y0"])}"', offset=18)
    sh.dim_v(Y(d0["z0"]), Y(d0["z1"]), X(d0["y1"]), f'{inch(S.stretcher_height)}"', offset=16)

    sh.text(X(1.0), Y(1.2), "DATUM Y0 infeed", 11, DIM)
    sh.text(X(0.3), Y(2.4), "DATUM Z0 bottom", 11, DIM, rot=-90)

    # isometric
    t, dpth, ht = G.side_thick, S.side_depth, S.side_height
    meshes = [box(GREEN, 0, 0, 0, t, ht, dpth)]
    meshes.append(box(UHMW, t - way["depth"], way["z0"], way["y0"], way["depth"], way["z1"] - way["z0"], way["y1"] - way["y0"]))
    for dd in feat["dados"]:
        meshes.append(box(TAN, t - dd["depth"], dd["z0"], dd["y0"], dd["depth"], dd["z1"] - dd["z0"], dd["y1"] - dd["y0"]))
    meshes.append(cyl_x(STEEL, t / 2, bz, by, t + 0.4, feat["bearing_cl"]["shaft_clear_dia"] / 2, 14))
    sh.iso_frame(1080, 100, 540, 340, "Isometric — inner face toward camera", meshes)

    # hole chart
    sh.rect(1080, 460, 540, 280, fill=LIGHT, stroke=INK, sw=1.0)
    sh.text(1096, 484, "HOLE CHART  (inner-face Y / Z)", 13, ACC, bold=True)
    headers = [("ID", 1096), ("Y", 1180), ("Z", 1280), ("DRILL", 1380)]
    for h, x in headers:
        sh.text(x, 508, h, 11, DIM, bold=True)
    yy = 530
    rows = [
        ("SHAFT", inch(by), inch(bz), f'⌀{inch(feat["bearing_cl"]["shaft_clear_dia"])}" clear'),
        ("FB1–4", f"CL ± {inch(S.flange_bolt_square / 2)}", "square", f'⌀{inch(S.flange_bolt_clr)}"  (5/16)'),
    ]
    if feat["motor_pivot"]:
        mp = feat["motor_pivot"]
        rows.append(("PIVOT", inch(mp["y"]), inch(mp["z"]), f'⌀{inch(mp["dia"])}" tap ¼-20'))
    if feat["indicator_pad"]:
        ip = feat["indicator_pad"]
        rows.append(("PAD", inch(ip["y"]), inch(ip["z"]), f'⌀{inch(ip["dia"])}" tap ¼-20'))
    rows.append(("SS*", "dado Y", "dado Z mid", "#8 pilot — drill after clamp"))
    for rid, yv, zv, drill in rows:
        sh.text(1096, yy, rid, 12, INK, bold=True)
        sh.text(1180, yy, yv, 12, INK)
        sh.text(1280, yy, zv, 12, INK)
        sh.text(1380, yy, drill, 12, INK)
        yy += 22
    sh.text(1096, 720, "Flange square CTC is ASSUMED. Transfer the purchased flange.", 11, DIM, mono=False)

    notes = [
        "Stack-drill P-001L and P-001R face-to-face (S-008) for bearing CL, flange bolts, and stretcher pilots. Then split.",
        "Dados J-001 and way rebate J-002 are INNER FACE only and mirrored. Do not dado the pair while stacked.",
        f'Way rebate {inch(G.way_rebate, 3)}" deep × {inch(S.way_width)}" wide × {inch(G.way_len)}" tall, centered on drum CL, so P-007 projects {inch(G.way_project, 3)}". Vertical — the table does not sit on this strip.',
        "Clamp each stretcher in its housing, then drill #8 pilots through the side into P-003 (S-006). Countersink from the outside.",
    ]
    if hand == "L":
        notes.append("Drive flange H-001 is FIXED (J-006). This side is the drum-axis datum. Torque the flange bolts.")
        notes.append(feat["motor_pivot"]["note"])
        notes.append(feat["indicator_pad"]["note"])
    else:
        notes.append(feat["idler_pad"]["note"])
        notes.append("Do not copy the motor pivot or A-clock pad onto this panel.")
    sh.notes(1080, 760, notes, "FABRICATION SEQUENCE")
    sh.save(p["sheet"])


# ---------------------------------------------------------------------------
# Rectangular / special part sheets
# ---------------------------------------------------------------------------


def sheet_rect(
    pid: str,
    filename: str,
    view_caption: str,
    color: str,
    notes: list[str],
    holes: list[tuple[float, float, float, str]] | None = None,
    extras=None,
    iso_meshes=None,
    l_dim: float | None = None,
    w_dim: float | None = None,
    t_dim: float | None = None,
) -> None:
    p = part_by_id(pid)
    L = l_dim if l_dim is not None else p["finished_l"]
    Ww = w_dim if w_dim is not None else p["finished_w"]
    T = t_dim if t_dim is not None else p["finished_t"]
    sh = Sheet(pid, p["part_name"], f"Qty {p['qty']}  ·  {p['process']}", subtitle=p["notes"] or p["joinery"])
    sh.titleblock(
        qty=f"MAKE {p['qty']}  ·  {p['handed']}",
        material=f'{p["material"]}  ·  {p["finished_size"] or p["purchase_size"]}',
        evidence=p.get("evidence", ""),
    )

    # Fit a plan view in the left 2/3
    max_w, max_h = 980, 720
    sc = min(max_w / max(L, 0.1), max_h / max(Ww, 0.1), 48)
    ox, oy = 80, 160
    sh.text(ox, 110, view_caption, 14, ACC, bold=True)
    sh.rect(ox, oy, L * sc, Ww * sc, fill=color, stroke=INK, sw=2.0)
    sh.dim_h(ox, ox + L * sc, oy + Ww * sc, f'{inch(L)}"', offset=28)
    sh.dim_v(oy, oy + Ww * sc, ox, f'{inch(Ww)}"', offset=-32)
    sh.text(ox + L * sc + 16, oy + 14, f'T {inch(T)}"', 13, DIM)

    if holes:
        for hx, hy, hd, hid in holes:
            sh.circle(ox + hx * sc, oy + hy * sc, max(2.5, (hd / 2) * sc), fill=PAPER, stroke=INK, sw=1.2)
            sh.text(ox + hx * sc + 8, oy + hy * sc - 6, hid, 10, DIM)

    if extras:
        extras(sh, ox, oy, sc, L, Ww)

    meshes = iso_meshes or [box(color, 0, 0, 0, L, T, Ww)]
    sh.iso_frame(1120, 100, 500, 300, "Isometric", meshes)

    sh.rect(1120, 420, 500, 280, fill=LIGHT, stroke=INK, sw=1.0)
    sh.text(1136, 444, "PART DATA", 13, ACC, bold=True)
    meta = [
        ("Stock", p.get("purchase_size") or p.get("rough_size") or "—"),
        ("Joinery", (p.get("joinery") or "—")[:42]),
        ("Ref face", (p.get("reference_face") or "—")[:42]),
        ("Ref edge", (p.get("reference_edge") or "—")[:42]),
        ("Grain", (p.get("grain_direction") or "—")[:42]),
        ("Evidence", p.get("evidence", "DERIVED")),
    ]
    yy = 470
    for k, v in meta:
        sh.text(1136, yy, k, 12, DIM, bold=True)
        sh.text(1260, yy, v, 12, INK, mono=False)
        yy += 22

    sh.notes(80, 928, notes)
    sh.save(filename)


def sheet_p002() -> None:
    L, Ww, T = G.base_width, G.base_depth, S.base_thick
    holes = []
    # screws up into each side — four along each long edge
    ys = (2.0, 8.0, 14.0, 20.0)
    for i, y in enumerate(ys):
        holes.append((S.ply_actual / 2, y, 0.19, f"L{i+1}"))
        holes.append((L - S.ply_actual / 2, y, 0.19, f"R{i+1}"))

    def extras(sh, ox, oy, sc, LL, WW):
        sh.leader(ox + S.ply_actual / 2 * sc, oy + 8 * sc, ox - 10, oy - 24, "J-010  #8 through into P-001L/R. Drill after clamp-up.", 12)
        sh.text(ox + LL * sc / 2, oy + WW * sc / 2, "TOP FACE", 14, ACC, "middle", bold=True)

    meshes = [box(GREEN, 0, 0, 0, L, T, Ww)]
    sheet_rect(
        "P-002",
        "P002_base.svg",
        "BASE DECK — top face  (X across drum, Y feed)",
        GREEN,
        [
            f'Finished {inch(L)}" × {inch(Ww)}" × {inch(T)}". Width follows ply_actual so 18 mm Euro BB still keeps 16.5" clear.',
            "Clamp the sides to the deck, square the diagonals (QC-03), then drill J-010 pilots through the deck into the side bottom edges.",
            "Do not use this deck as the table datum. Ways locate the table.",
        ],
        holes=holes,
        extras=extras,
        iso_meshes=meshes,
        l_dim=L,
        w_dim=Ww,
        t_dim=T,
    )


def sheet_p003() -> None:
    L, Ww, T = G.stretcher_length, S.stretcher_height, G.side_thick

    def extras(sh, ox, oy, sc, LL, WW):
        sh.rect(ox, oy, S.stretcher_housing * sc, WW * sc, fill="none", stroke=ACC, sw=1.4, dash="5 4")
        sh.rect(ox + (LL - S.stretcher_housing) * sc, oy, S.stretcher_housing * sc, WW * sc, fill="none", stroke=ACC, sw=1.4, dash="5 4")
        sh.leader(ox + 4, oy + WW * sc / 2, ox - 8, oy - 20, f'Housed {inch(S.stretcher_housing)}" each end (J-001)', 12)
        sh.text(ox + LL * sc / 2, oy + WW * sc / 2 + 6, "MAKE 3  ·  ONE STOP", 13, ACC, "middle", bold=True)

    meshes = [box(TAN, 0, 0, 0, L, T, Ww)]
    sheet_rect(
        "P-003",
        "P003_stretcher.svg",
        "STRETCHER — one of three, identical  (S-003 do not move the stop)",
        TAN,
        [
            f'Rip {inch(S.stretcher_height)}" (S-004), then crosscut all three to {inch(G.stretcher_length)}" housed length (S-003).',
            "Ends sit in ¼″ dados on the inner faces, standing on edge (4″ is Z). Clamp, then drill pilots through the side (see P-001).",
            "Stations IN-LO / OUT-LO / OUT-HI miss the table envelope. Ways — not stretchers — locate the table.",
        ],
        extras=extras,
        iso_meshes=meshes,
        l_dim=L,
        w_dim=Ww,
        t_dim=T,
    )


def sheet_p004() -> None:
    L, Ww, T = G.table_width, G.table_depth, S.table_skin
    meshes = [box(GREEN, 0, 0, 0, L, T, Ww)]
    sheet_rect(
        "P-004",
        "P004_table_skin.svg",
        "TABLE SKIN — make two, show-face outboard",
        GREEN,
        [
            "Cut the pair to one stop (S-005). Diagonals equal before glue.",
            "Glue continuously to the P-005 rib grid (J-003). Flatten the box before bonding the wear face.",
            f'Finished table in plan is {inch(G.table_width)}" × {inch(G.table_depth)}" so it clears the ways with {inch(S.slide_clearance, 3)}" per side.',
        ],
        iso_meshes=meshes,
        l_dim=L,
        w_dim=Ww,
        t_dim=T,
    )


def sheet_p005() -> None:
    L = G.table_width - 0.5
    Ww = G.table_thick - 0.25
    T = S.table_rib
    n = max(2, int(round((G.table_depth - 1.0) / S.table_rib_oc)) + 1)

    def extras(sh, ox, oy, sc, LL, WW):
        sh.text(ox + LL * sc / 2, oy + WW * sc / 2, f"TYP.  {n} RIBS  @  {inch(S.table_rib_oc)}\" O.C.", 13, ACC, "middle", bold=True)

    meshes = [box(MDF, 0, 0, 0, L, T, Ww)]
    sheet_rect(
        "P-005",
        "P005_table_ribs.svg",
        "TORSION-BOX RIB — typical; qty from 4″ o.c. in 22″ depth",
        MDF,
        [
            f'Rip ½" stock. Length {inch(L)}" (½" shy of skin each end). Qty is ESTIMATED from spacing — cut from offcuts.',
            "Full glue, no dry joints. The grid is what keeps the wear face from dishing.",
        ],
        extras=extras,
        iso_meshes=meshes,
        l_dim=L,
        w_dim=Ww,
        t_dim=T,
    )


def sheet_p006() -> None:
    L, Ww, T = G.table_width, G.table_depth, 0.5
    meshes = [box(PHEN, 0, 0, 0, L, T, Ww)]
    sheet_rect(
        "P-006",
        "P006_wear_face.svg",
        "WEAR FACE — this is the inspection plane (DATUM-D)",
        PHEN,
        [
            "Buy ½″ phenolic or ⅜″ MIC-6. Bond to a flattened torsion box (J-004). Keep a spare.",
            f"QC-05: flatness ≤ {S.table_flat_tol:.3f}″ on both diagonals before you ever wrap paper.",
            "Do not oil. Paste wax only if a board wants to stick.",
        ],
        iso_meshes=meshes,
        l_dim=L,
        w_dim=Ww,
        t_dim=T,
    )


def sheet_p007() -> None:
    L, Ww, T = G.way_len, S.way_width, S.way_stock
    meshes = [box(UHMW, 0, 0, 0, L, T, Ww)]
    sheet_rect(
        "P-007",
        "P007_uhmw_way.svg",
        "UHMW WAY — make two  (vertical strip, let into J-002, then wax)",
        UHMW,
        [
            f'Vertical. {inch(G.way_len)}" Z × {inch(S.way_width)}" Y, centered on drum CL. Projects {inch(G.way_project, 3)}" past the inner face.',
            f'Rebate is {inch(G.way_rebate, 3)}" so a {inch(G.table_width)}" table still fits the {inch(S.clear_between_sides)}" span.',
            "Bond into the rebate. Optional #8 flush screws from the outer face. Dry lube with paste wax — no oil.",
            "QC-04: both ways plumb. The table shoes wrap this tongue; the Acme does the lifting.",
        ],
        iso_meshes=meshes,
        l_dim=L,
        w_dim=Ww,
        t_dim=T,
    )


def sheet_p017() -> None:
    L, Ww, T = G.shoe_h, G.shoe_w, G.shoe_t
    meshes = [box(UHMW, 0, 0, 0, L, T, Ww)]
    sheet_rect(
        "P-017",
        "P017_table_shoe.svg",
        "TABLE SHOE — make two, mirror pair  (wraps the vertical tongue)",
        UHMW,
        [
            f'Groove the outboard face {inch(G.shoe_groove_depth, 3)}" deep × {inch(G.shoe_groove_width, 3)}" wide.',
            f'Tongue is {inch(G.way_project, 3)}" × {inch(G.way_width)}". X play {inch(G.shoe_groove_depth - G.way_project, 3)}", Y play {inch(G.shoe_groove_width - G.way_width, 3)}" (CALC-005).',
            "Bolt under the table edge, centered on drum CL. Table moves in Z only (J-012).",
            "Hardwood with a UHMW liner is acceptable if you cannot get a thick UHMW offcut.",
        ],
        iso_meshes=meshes,
        l_dim=L,
        w_dim=Ww,
        t_dim=T,
    )


def sheet_p018() -> None:
    L, Ww, T = G.thrust_l, G.thrust_w, G.thrust_h
    def extras(sh, ox, oy, sc, LL, WW):
        sh.circle(ox + LL * sc / 2, oy + WW * sc / 2, 0.25 * sc, fill=PAPER, stroke=INK, sw=1.4)
        sh.leader(ox + LL * sc / 2, oy + WW * sc / 2, ox + LL * sc + 12, oy - 18, "⌀½″ through + thrust-washer counterbore", 12)
    meshes = [box(TAN, 0, 0, 0, L, T, Ww)]
    sheet_rect(
        "P-018",
        "P018_thrust_block.svg",
        "ACME THRUST BLOCK — make two, screw to the base on drum CL",
        TAN,
        [
            f'Both blocks at Y {inch(G.acme_y)}" (drum CL), left and right X. Not at the infeed and outfeed.',
            "Thrust washer + e-clip under the screw (H-026). Sanding load tries to pull the screw out of the base.",
            "Block size is ASSUMED. Hole follows ½-10 Acme.",
        ],
        extras=extras,
        iso_meshes=meshes,
        l_dim=L,
        w_dim=Ww,
        t_dim=T,
    )


def sheet_p019() -> None:
    L, Ww, T = G.dog_l, G.dog_w, G.dog_h
    meshes = [box(STEEL, 0, 0, 0, L, T, Ww)]
    sheet_rect(
        "P-019",
        "P019_home_dog.svg",
        "PARALLEL HOME DOG — make one, left side",
        STEEL,
        [
            "Bolt to the base beside the left Acme. The left clutch hits this stop at last known |A−B|.",
            "Set after paper-on parallel (ST-14). Uncouple left for taper; recouple against this dog.",
            "Size is ASSUMED. Function is the stop, not the block.",
        ],
        iso_meshes=meshes,
        l_dim=L,
        w_dim=Ww,
        t_dim=T,
    )


def sheet_disc(pid: str, filename: str, color: str, extra_notes: list[str]) -> None:
    p = part_by_id(pid)
    od = G.drum_oversize_od
    sh = Sheet(pid, p["part_name"], f"Qty {p['qty']}  ·  bandsaw oversize, pack-bore, then true on the sled")
    sh.titleblock(qty=f"MAKE {p['qty']}", material=f'{p["material"]}  ·  {p["finished_size"]}', evidence=p["evidence"])
    sc = 70
    cx, cy = 420, 520
    sh.circle(cx, cy, (od / 2) * sc, fill=color, stroke=INK, sw=2.0)
    sh.circle(cx, cy, (S.shaft_od / 2) * sc, fill=PAPER, stroke=INK, sw=1.6)
    sh.line(cx, cy - (od / 2) * sc, cx, cy + (od / 2) * sc, 0.8, DIM, dash="4 4")
    sh.line(cx - (od / 2) * sc, cy, cx + (od / 2) * sc, cy, 0.8, DIM, dash="4 4")
    sh.dim_h(cx - (od / 2) * sc, cx + (od / 2) * sc, cy + (od / 2) * sc, f'⌀{inch(od)}" bandsaw', offset=36)
    sh.dim_h(cx - (S.shaft_od / 2) * sc, cx + (S.shaft_od / 2) * sc, cy, f'⌀{inch(S.shaft_od)}" bore', offset=-48)
    sh.text(cx, 140, "TRUE ON P-013 TO ⌀5.00″  ·  DO NOT DISH THE MIDDLE", 13, ACC, "middle", bold=True)
    meshes = [cyl_x(color, 0, 0, 0, S.disc_thick, od / 2, 28)]
    sh.iso_frame(1000, 120, 520, 320, "Isometric disc", meshes)
    notes = [
        f"Bandsaw ~{inch(S.disc_bandsaw_oversize, 3)}\" over finish OD. Pack-bore the whole stack in P-015 (S-009).",
        f"1 mm relief every {S.spacer_every_n} MDF discs so the pack can take a deep true without burning.",
        "⅛″ piano-wire keys (H-018) keep discs from spinning on the shaft.",
    ] + extra_notes
    sh.notes(80, 928, notes)
    sh.save(filename)


def sheet_p010() -> None:
    p = part_by_id("P-010")
    sh = Sheet("P-010", p["part_name"], "Precision-ground shaft  ·  incoming TIR ≤ 0.0005″")
    sh.titleblock(qty="BUY-CUT 1", material=p["notes"], evidence="VERIFIED")
    sc = 48
    ox, oy = 80, 280
    sh.rect(ox, oy, S.shaft_length * sc * 0.35, S.shaft_od * sc, fill=STEEL, stroke=INK, sw=1.8, rx=4)
    # draw at a readable scale: length compressed in the 2D bar, true dim called
    bar_w = 980
    sh.rect(ox, oy, bar_w, 36, fill=STEEL, stroke=INK, sw=1.8, rx=6)
    sh.dim_h(ox, ox + bar_w, oy + 36, f'{inch(S.shaft_length)}" finished  (buy {inch(S.shaft_length)} TG&P, MC-02)', offset=28)
    sh.dim_v(oy, oy + 36, ox, f'⌀{inch(S.shaft_od)}"', offset=-36)
    sh.leader(ox + 80, oy, ox + 80, oy - 48, "Drive end — H-001 FIXED (J-006)", 12)
    sh.leader(ox + bar_w - 80, oy + 36, ox + bar_w - 40, oy + 90, "Idler end — H-002 FLOATING pad (J-007)", 12)
    meshes = [cyl_x(STEEL, 0, 0, 0, S.shaft_length, S.shaft_od / 2, 20)]
    sh.iso_frame(80, 480, 700, 280, "Isometric shaft", meshes)
    sh.notes(
        820,
        500,
        [
            "Do not lock both flanges. Drive is the datum; idler must let the shaft grow.",
            "Key slots: ⅛″ piano wire, snug in the discs, not a press that bananas the pack.",
            f"After truing: TIR ≤ {S.drum_tir:.3f}″ mid-span paper-off (QC-06), then wrap, then re-clock |A−B|.",
        ],
    )
    sh.save("P010_shaft.svg")


def sheet_p011() -> None:
    p = part_by_id("P-011")
    L, Ww, T = S.hood_blank_w, S.hood_blank_h, S.hood_ply

    def extras(sh, ox, oy, sc, LL, WW):
        sh.circle(ox + LL * sc - 40, oy + WW * sc / 2, (S.dust_port_od / 2) * sc * 0.35, fill="none", stroke=ACC, sw=1.6)
        sh.leader(ox + LL * sc - 40, oy + WW * sc / 2, ox + LL * sc + 10, oy - 16, '4" dust port (trim to drum arc)', 12)
        for i in range(8):
            x = ox + 20 + i * (LL * sc - 80) / 7
            sh.line(x, oy + 8, x, oy + WW * sc - 8, 0.7, DIM, dash="3 4")
        sh.text(ox + 24, oy + 22, "KERFS  ·  sawdust-glue fill", 11, DIM)

    meshes = [box(GREEN, 0, 0, 0, L, T, Ww)]
    sheet_rect(
        "P-011",
        "P011_hood.svg",
        "HOOD BLANK — kerf-bend around the drum, then trim",
        GREEN,
        [
            S.hood_method,
            "Hood ON is the primary guard. Paraffin the paint-rubs against the sides.",
            "Blank size is ESTIMATED — trim to the drum arc after the first dry-fit.",
        ],
        extras=extras,
        iso_meshes=meshes,
        l_dim=L,
        w_dim=Ww,
        t_dim=T,
    )


def sheet_p012() -> None:
    L, Ww, T = S.cradle_w, S.cradle_h, G.side_thick
    holes = [
        (1.5, 1.5, S.motor_pivot_dia, "PIVOT"),
        (L - 1.5, 1.5, 0.266, "LOCK"),
        (L / 2, Ww - 1.5, 0.266, "T-NUT"),
    ]
    meshes = [box(TAN, 0, 0, 0, L, T, Ww)]
    sheet_rect(
        "P-012",
        "P012_motor_cradle.svg",
        "MOTOR PIVOT CRADLE — gravity tensions the belt, then lock",
        TAN,
        [
            "J-008: ¼-20 T-nuts. Pivot on P-001L, then lock so the belt cannot pump.",
            "Pulley faces coplanar with a straightedge (QC-09) before you lock.",
            "Size the V-belt to the measured center distance after the cradle is locked — not before.",
        ],
        holes=holes,
        iso_meshes=meshes,
        l_dim=L,
        w_dim=Ww,
        t_dim=T,
    )


def sheet_p013() -> None:
    L, Ww, T = G.table_width, S.sled_depth, G.side_thick
    meshes = [box(MDF, 0, 0, 0, L, T, Ww)]
    sheet_rect(
        "P-013",
        "P013_truing_sled.svg",
        "FULL-WIDTH TRUING SLED — abrasive face up, rides the ways",
        MDF,
        [
            "As wide as the drum so you cannot dish the middle. This is how the drum becomes a cylinder.",
            f"True paper-off to TIR ≤ {S.drum_tir:.3f}″ (S-010), then wrap, then re-clock A/B.",
            "Do not true with the hold-down rollers dragging on the sled — lift or remove them.",
        ],
        iso_meshes=meshes,
        l_dim=L,
        w_dim=Ww,
        t_dim=T,
    )


def sheet_p014() -> None:
    L, Ww, T = S.yoke_length, S.yoke_width, S.yoke_thick
    holes = [
        (1.25, Ww / 2, 0.332, "PIV-A"),
        (L - 1.25, Ww / 2, 0.332, "PIV-B"),
        (L / 2, Ww / 2, 0.266, "SPRING"),
    ]
    meshes = [box(TAN, 0, 0, 0, L, T, Ww)]
    sheet_rect(
        "P-014",
        "P014_roller_yoke.svg",
        "HOLD-DOWN YOKE — make two (infeed + outfeed)",
        TAN,
        [
            f"Rollers sit {S.roller_setbelow:.3f}″ below drum OD, paper on (QC-08). Too much spring = snipe.",
            "Shoulder-bolt pivots (H-012). Light compression springs (H-011). Star knobs lock the height (H-013).",
            "Hardwood or 1½″ aluminum angle both work. Match the pair.",
        ],
        holes=holes,
        iso_meshes=meshes,
        l_dim=L,
        w_dim=Ww,
        t_dim=T,
    )


def sheet_p015() -> None:
    L, Ww, T = S.bore_jig, S.bore_jig, G.side_thick

    def extras(sh, ox, oy, sc, LL, WW):
        sh.rect(ox + 20, oy + WW * sc - 40, LL * sc - 40, 24, fill=TAN, stroke=INK, sw=1.2)
        sh.circle(ox + LL * sc / 2, oy + WW * sc / 2, (S.shaft_od / 2) * sc, fill=PAPER, stroke=INK, sw=1.6)
        sh.text(ox + LL * sc / 2, oy + 28, "FENCE + CLAMP WALL  ·  BORE THE PACK AS ONE", 12, ACC, "middle", bold=True)

    meshes = [box(MDF, 0, 0, 0, L, T, Ww)]
    sheet_rect(
        "P-015",
        "P015_pack_bore.svg",
        f"PACK-BORE JIG — fence and clamp wall, ream ⌀{inch(S.shaft_od)}″ through the stack (Option B)",
        MDF,
        [
            f"Option B only. Bore P-008 and P-009 as one pack (S-009) to ⌀{inch(S.shaft_od)}″. A disc bored alone will not run true.",
            "Ream, don't hog. The shaft is the locational fit (J-005). Baseline drum is P-020/P-021 (J-106).",
        ],
        extras=extras,
        iso_meshes=meshes,
        l_dim=L,
        w_dim=Ww,
        t_dim=T,
    )


def sheet_p016() -> None:
    L, Ww, T = 2.5, 2.0, 1.5

    def extras(sh, ox, oy, sc, LL, WW):
        sh.circle(ox + LL * sc / 2, oy + WW * sc / 2, 0.35 * sc, fill=BRONZE, stroke=INK, sw=1.4)
        sh.leader(ox + LL * sc / 2, oy + WW * sc / 2, ox + LL * sc + 12, oy - 18, "Bronze nut ½-10  (BUY)", 12)

    meshes = [
        box(TAN, 0, 0, 0, L, T, Ww),
        cyl_z(BRONZE, L / 2, Ww / 2, T / 2, T + 0.2, 0.35, 14),
    ]
    sheet_rect(
        "P-016",
        "P016_nut_block.svg",
        "ACME NUT BLOCK — make two, bolt to table underside",
        TAN,
        [
            "Block size is ASSUMED; the bronze nut is BUY. Both nuts; chain-coupled rotation (H-008).",
            "Left screw uncouples for taper. Dog stop is the last known parallel home.",
            f"½-10 Acme · {inch(G.acme_per_turn, 4)}\" per turn. Travel {inch(S.elev_travel)}\".",
        ],
        extras=extras,
        iso_meshes=meshes,
        l_dim=L,
        w_dim=Ww,
        t_dim=T,
    )


def sheet_p020() -> None:
    p = part_by_id("P-020")
    sh = Sheet("P-020", p["part_name"], "Option A baseline drum  ·  wall is a stiffness requirement (CALC-C02)")
    sh.titleblock(qty="MAKE 1", material=p["material"], evidence="DERIVED from CALC-C02")
    od, wall, length = S.shell_od, S.shell_wall, G.drum_length
    idia = od - 2 * wall
    sc = 42
    ox, oy = 80, 180
    sh.text(ox, 120, "LONGITUDINAL SECTION  ·  ID and OD both shown", 14, ACC, bold=True)
    sh.rect(ox, oy, length * sc, od * sc, fill=ALUM, stroke=INK, sw=1.8)
    sh.rect(ox, oy + wall * sc, length * sc, idia * sc, fill=PAPER, stroke=INK, sw=1.4)
    sh.dim_h(ox, ox + length * sc, oy + od * sc, f'{inch(length)}" finished  (cut ⅛″ long, then face square)', offset=28)
    sh.dim_v(oy, oy + od * sc, ox, f'OD ⌀{inch(od)}"', offset=-40)
    sh.dim_v(oy + wall * sc, oy + (wall + idia) * sc, ox + length * sc, f'ID ⌀{inch(idia)}"', offset=36)
    sh.leader(ox + 40, oy + wall * sc / 2, ox + 120, oy - 28, f'wall {inch(wall, 3)}"  ·  I_shell = {AXIS_I_SHELL:.2f} in⁴', 12)
    sh.leader(ox + 30, oy + od * sc / 2, ox + 40, oy + od * sc + 80, f"P-021 plug seats {inch(S.plug_inset, 2)}\" inboard (J-106)", 12)
    sh.iso_frame(80, 520, 700, 300, "Isometric shell", [cyl_x(ALUM, 0, 0, 0, length, od / 2, 24)])
    sh.notes(
        820,
        160,
        [
            "This part is why Rev C holds the accuracy spec. Do not substitute decorative thin-wall tube (MC-01).",
            f"Cut from 18″ stock. Face both ends square. Finished length {inch(length)}″ matches the 21-disc pack so Option B remains a drop-in.",
            "Bond and cross-pin to P-021 (J-106). Never adhesive alone on a rotating part.",
            "True the OD in the machine's own bearings (ST-13). Truing in a lathe and then moving the drum re-introduces TIR.",
            "Option B (P-008/P-009 stack) is the documented no-lathe alternative with an explicit accuracy penalty (D-047).",
        ],
    )
    sh.save("P020_drum_shell.svg")


def sheet_p021() -> None:
    p = part_by_id("P-021")
    sh = Sheet("P-021", p["part_name"], "ONE LATHE SETUP  ·  bore and OD concentric  ·  make 2")
    sh.titleblock(qty="MAKE 2", material=p["material"], evidence="DERIVED from ALN-01 TIR budget")
    od_plug = S.shell_od - 2 * S.shell_wall
    sc = 90
    ox, oy = 120, 200
    r = (od_plug / 2) * sc
    cx, cy = ox + r + 20, oy + r + 20
    sh.circle(cx, cy, r, fill=ALUM, stroke=INK, sw=2.0)
    sh.circle(cx, cy, (S.shaft_od / 2) * sc, fill=PAPER, stroke=INK, sw=1.6)
    sh.dim_h(cx - r, cx + r, cy + r, f'OD ⌀{inch(od_plug, 3)}"  (measure YOUR tube ID)', offset=32)
    sh.text(cx, cy - 8, f'bore ⌀{inch(S.shaft_od)}"', 13, DIM, "middle")
    sh.text(ox, 120, "END VIEW — turn OD, then bore, then part off. Do not re-chuck.", 14, ACC, bold=True)
    ox2, oy2 = 720, 240
    sh.rect(ox2, oy2, S.plug_thick * sc, od_plug * sc, fill=ALUM, stroke=INK, sw=1.8)
    sh.rect(ox2, oy2 + ((od_plug - S.shaft_od) / 2) * sc, S.plug_thick * sc, S.shaft_od * sc, fill=PAPER, stroke=INK, sw=1.4)
    sh.dim_h(ox2, ox2 + S.plug_thick * sc, oy2 + od_plug * sc, f'T {inch(S.plug_thick)}"', offset=28)
    sh.text(ox2, oy2 - 16, "SIDE VIEW", 12, DIM, bold=True)
    sh.iso_frame(80, 620, 520, 280, "Isometric plug", [cyl_x(ALUM, 0, 0, 0, S.plug_thick, od_plug / 2, 20)])
    sh.notes(
        640,
        620,
        [
            "Concentricity of bore to OD becomes drum TIR directly. One setup, two operations.",
            f"Light push fit on the {inch(S.shaft_od)}\" shaft — no rock. Clamp collars H-029 locate axially (J-106).",
            "Cross-pin through the shell wall in two places 90° apart after the epoxy cures. Pins carry torque.",
            "Make a spare from the same bar. 3D-print is not a substitute for this part.",
        ],
    )
    sh.save("P021_drum_plug.svg")


def sheet_p022() -> None:
    L, Ww, T = S.side_depth, S.way_width, S.way_stock
    drop = L / 40.0

    def extras(sh, ox, oy, sc, LL, WW):
        sh.poly(
            [(ox, oy), (ox + LL * sc, oy + drop * sc), (ox + LL * sc, oy + WW * sc), (ox, oy + WW * sc)],
            fill=UHMW,
            stroke=INK,
            sw=1.6,
        )
        sh.text(ox + 12, oy + 18, "THICK END — wedges DOWN", 11, ACC, bold=True)
        sh.text(ox + LL * sc - 12, oy + drop * sc + 16, "THIN", 11, DIM, "end", bold=True)
        for i, frac in enumerate((0.2, 0.5, 0.8)):
            sh.circle(ox + frac * LL * sc, oy + WW * sc / 2, 5, fill=PAPER, stroke=INK, sw=1.2)
            sh.text(ox + frac * LL * sc + 8, oy + WW * sc / 2 - 8, f"¼-20 #{i + 1}", 10, DIM)

    sheet_rect(
        "P-022",
        "P022_gib.svg",
        "TAPERED GIB 1:40 — idler side only. Mark the thick end before it leaves the jig.",
        UHMW,
        [
            f"Taper 1:40 over {inch(L)}\" → {inch(drop, 3)}\" drop.",
            f"Target running clearance {S.gib_clearance:.4f}″ after the shoes are on (ST-16, QC-17). This kills the 0.020″ Rev B way-play term.",
            "Brass-tip ¼-20 adjusters only (H-031 / MC-07). Bare steel brinells the UHMW and the setting drifts.",
            "Set the gib FIRST and leave it. Parallelism is the P-023 jack, not this part (J-105).",
        ],
        extras=extras,
        iso_meshes=[box(UHMW, 0, 0, 0, L, T, Ww)],
        l_dim=L,
        w_dim=Ww,
        t_dim=T,
    )


def sheet_p023() -> None:
    L, Ww, T = 8.0, 4.0, 0.375
    holes = [
        (1.0, Ww / 2, 0.375, "PIVOT ⅜″ ream"),
        (1.0 + S.jack_arm_l2, Ww / 2, S.ply_shaft_clear_dia, "SHAFT CLR"),
        (1.0 + S.jack_arm_l1, Ww / 2, 0.266, "JACK PAD"),
    ]

    def extras(sh, ox, oy, sc, LL, WW):
        bx = ox + (1.0 + S.jack_arm_l2) * sc
        by = oy + WW * sc / 2
        half = (S.flange_bolt_square / 2) * sc
        for dx, dy in ((-half, -half), (half, -half), (half, half), (-half, half)):
            sh.circle(bx + dx, by + dy, 4, fill=PAPER, stroke=INK, sw=1.1)
        sh.text(bx, by + half + 18, f'flange square {inch(S.flange_bolt_square)}" ASSUMED — MEASURE YOURS', 11, DIM, "middle")

    sheet_rect(
        "P-023",
        "P023_idler_plate.svg",
        "IDLER MICRO-ADJUST PLATE — 3D-print at 1:1 before cutting metal",
        ALUM,
        [
            f"Pivot-to-bearing L2 = {inch(S.jack_arm_l2)}\". Pivot-to-jack L1 = {inch(S.jack_arm_l1)}\". Reduction L2/L1.",
            f"¼-28 jack (H-030) → {MECH_ADJ_AT_WORK * 1000:.2f} mil at the work per full turn (CALC-C07).",
            "Ream the pivot for H-032. Transfer the purchased flange BCD — do not drill from the square on this sheet.",
            "Print this sheet at 1:1 and tape it to the stock before you drill (user joinery standard).",
        ],
        holes=holes,
        extras=extras,
        iso_meshes=[box(ALUM, 0, 0, 0, L, T, Ww)],
        l_dim=L,
        w_dim=Ww,
        t_dim=T,
    )


def sheet_p024() -> None:
    L, Ww, T = 2.0, 1.25, 0.75
    sheet_rect(
        "P-024",
        "P024_jack_block.svg",
        "JACK SCREW BLOCK — tap through, chase the thread clean",
        STEEL,
        [
            f"Tap ¼-{S.jack_thread_tpi:g} through. A ragged thread reads as backlash in ALN-01.",
            "Bolt to P-001R so the H-030 screw bears on a pad, not on plywood.",
            "Brass or nylon tip under the screw point so it does not dig in and lose calibration.",
        ],
        holes=[(L / 2, Ww / 2, 0.201, f"TAP ¼-{S.jack_thread_tpi:g}")],
        iso_meshes=[box(STEEL, 0, 0, 0, L, T, Ww)],
        l_dim=L,
        w_dim=Ww,
        t_dim=T,
    )


# ---------------------------------------------------------------------------
# Assembly sheets
# ---------------------------------------------------------------------------


def sheet_a01() -> None:
    sh = Sheet("A-01", "Frame assembly", "P-001L/R · P-002 · P-003 ×3 · P-007 ×2 · P-018 ×2  ·  glue-up")
    sh.titleblock(qty="A-FRAME", material="Baltic birch + UHMW", evidence="QC-03 diagonals · QC-04 ways · QC-13 clearance")
    t, dpth, ht = G.side_thick, S.side_depth, S.side_height
    Wbox = G.overall_width
    meshes = [
        box(GREEN, 0, 0, 0, Wbox, S.base_thick, dpth),
        box(GREEN, 0, S.base_thick, 0, t, ht - S.base_thick, dpth),
        box(GREEN, Wbox - t, S.base_thick, 0, t, ht - S.base_thick, dpth),
    ]
    for rec in stretcher_records():
        meshes.append(box(TAN, t - S.stretcher_housing, rec["z0"], rec["y0"], G.stretcher_length, S.stretcher_height, rec["y1"] - rec["y0"]))
    meshes.append(box(UHMW, t - G.way_rebate, G.way_z0, G.way_y0, S.way_stock, G.way_len, G.way_width))
    meshes.append(box(UHMW, Wbox - t - G.way_project, G.way_z0, G.way_y0, S.way_stock, G.way_len, G.way_width))
    sh.iso_frame(40, 100, 900, 700, "Box + vertical ways — inner span 16.50″ is the constraint", meshes)
    sh.notes(
        980,
        140,
        [
            "1. Cut P-001L/R to one height stop and one depth stop (S-001, S-002).",
            "2. Stack-drill bearing CL, flange bolts, stretcher pilots (S-008).",
            "3. Split. Dado J-001 and rebate J-002 on inner faces only (mirror).",
            "4. Dry-fit P-003. Clamp, square diagonals, glue, through-screw.",
            "5. Bond vertical P-007. Wax. Shoes wrap the tongue; if the table binds you stole the span.",
            f"Keep {inch(S.clear_between_sides)}\" (419 mm) between inner faces even if ply is 18 mm Euro BB.",
            "Layout: HYBRID. Panel joinery is face/edge. Drum, Acme, and ways are centerline from DATUM-B/A.",
        ],
        "ASSEMBLY ORDER",
    )
    sh.rect(980, 520, 640, 300, fill=LIGHT, stroke=INK, sw=1.0)
    sh.text(996, 548, "CRITICAL FITS", 13, ACC, bold=True)
    rows = [
        ("Inner span", f'{inch(S.clear_between_sides)}"'),
        ("Table width", f'{inch(G.table_width)}"'),
        ("Way project", f'{inch(G.way_project, 3)}"'),
        ("Way rebate", f'{inch(G.way_rebate, 3)}"'),
        ("Stretcher L", f'{inch(G.stretcher_length)}" housed'),
        ("Slide gap", f'{inch(S.slide_clearance, 3)}"/side'),
    ]
    yy = 578
    for k, v in rows:
        sh.text(996, yy, k, 13, DIM, bold=True)
        sh.text(1200, yy, v, 13, INK)
        yy += 28
    sh.save("A01_frame.svg")


def sheet_a02() -> None:
    sh = Sheet("A-02", "Drum assembly", "Option A: P-020 + P-021×2 + P-010  ·  Option B: P-008×19 + P-009×2")
    sh.titleblock(qty="A-DRUM", material="6061 shell baseline · MDF disc stack is Option B")
    meshes = [cyl_x(ALUM, 0, 0, 0, G.drum_length, S.drum_od / 2, 24)]
    meshes.append(cyl_x(STEEL, 0, 0, 0, S.shaft_length, S.shaft_od / 2, 14))
    meshes.append(box(STEEL, -G.drum_length / 2 - 1.2, -1.4, -1.4, 0.7, 2.8, 2.8))
    meshes.append(box(STEEL, G.drum_length / 2 + 0.5, -1.4, -1.4, 0.7, 2.8, 2.8))
    sh.iso_frame(40, 100, 980, 560, f'⌀{inch(S.drum_od)}" × {inch(G.drum_length)}"  ·  ~{S.drum_rpm:g} RPM  ·  1¼″ shaft', meshes)
    sh.notes(
        1060,
        140,
        [
            "OPTION A (baseline): turn P-021 plugs in one lathe setup, bond+pin into P-020 (J-106). Wall is stiffness, not cosmetics (CALC-C02).",
            "OPTION B (no lathe): pack-bore P-008/P-009 in P-015. Accept the accuracy penalty (D-047) — the stack is not structural in bending.",
            "Drive bearing H-001 locked to P-001L (J-006). This is DATUM-E.",
            "Idler H-002 on P-023 micro-adjust plate (J-105 / J-007). Snug bolts. Axial float required.",
            f"True on P-013 in the machine's own bearings to TIR ≤ {S.drum_tir:.4f}″ paper-off, then wrap, then ALN-01 |A−B| ≤ {S.aln_spec:.3f}″ paper-on.",
            "Spiral wrap, 3″ paper on 4″ hook. Optional ⅛″ slow osc erases tracks — that motor is not drum RPM.",
        ],
        "DRUM BUILD",
    )
    sh.save("A02_drum.svg")


def sheet_a03() -> None:
    sh = Sheet("A-03", "Table assembly", "P-004 ×2 · P-005 ribs · P-006 wear · P-016 ×2 · P-017 ×2 · H-007/H-008")
    sh.titleblock(qty="A-TABLE", material="Torsion box + phenolic/MIC-6")
    tw, td, tt = G.table_width, G.table_depth, G.table_thick
    meshes = [
        box(GREEN, 0, 0, 0, tw, tt - 0.25, td),
        box(PHEN, 0, tt - 0.25, 0, tw, 0.25, td),
    ]
    sh.iso_frame(40, 100, 900, 520, "Wear face up — this is the plane you indicate", meshes)
    sh.notes(
        980,
        140,
        [
            "Glue the box. Flatten. Then bond the wear face. QC-05 before any sanding.",
            "Bronze nuts P-016 on the underside, both on the drum centerline — not at infeed and outfeed.",
            "P-017 shoes wrap the vertical ways. Uncouple LEFT for taper. Recouple against P-019 — last known parallel.",
            f"Shoes capture X/Y with {inch(G.shoe_groove_depth - G.way_project, 3)}\" X play. If the table does not rise, the ways are proud — see D-020 / D-027.",
        ],
        "TABLE BUILD",
    )
    sh.save("A03_table.svg")


def sheet_a04() -> None:
    sh = Sheet("A-04", "Drive assembly", f"{S.motor_hp:g} HP · {S.pulley_motor_od:g}″ / {S.pulley_drum_od:g}″ · 4L belt")
    sh.titleblock(qty="A-DRIVE", material="TEFC motor + P-012 cradle")
    meshes = [
        box(KNOB, 0, 0, 0, 6, 6, 8),
        cyl_x(STEEL, 6.4, 3.2, 4, 0.9, S.pulley_motor_od / 2, 16),
        box(TAN, -0.4, -0.4, -0.5, 7, 0.75, 9),
    ]
    sh.iso_frame(40, 100, 800, 500, "Cradle below, pulleys coplanar", meshes)
    sh.notes(
        900,
        140,
        [
            "Pivot P-012 on P-001L. Gravity tensions the belt; lock so it cannot pump (J-008).",
            "Straightedge across both pulley faces (QC-09). Belt size is measured after lock.",
            "Follow local electrical code for H-006 / H-020. This sheet is mechanical, not a wiring diagram.",
            f"Drum speed ~{S.drum_rpm:g} RPM · ~{G.surface_fpm:g} sfpm. Do not use a router-speed spindle.",
        ],
        "DRIVE",
    )
    sh.save("A04_drive.svg")


def sheet_a05() -> None:
    sh = Sheet("A-05", "Hold-downs", "P-014 ×2 · H-009 rollers · springs · 0.030″ below drum")
    sh.titleblock(qty="A-TABLE / hold-downs", material="Yokes + rubber rollers")
    meshes = [
        cyl_x(KNOB, 0, 0, 0, G.roller_len, S.roller_od / 2, 16),
        box(TAN, -G.roller_len / 2, 0.5, -0.4, G.roller_len, 0.4, 0.8),
    ]
    sh.iso_frame(40, 100, 900, 420, "Infeed shown; outfeed is the pair", meshes)
    sh.notes(
        980,
        140,
        [
            f"Set rollers {S.roller_setbelow:.3f}″ below drum OD with paper on (QC-08). Feeler gauge.",
            "Light springs. Stiff springs put a bow in thin stock and you sand a banana.",
            "Minimum board length ~12″ or use a sled. Hands never under the drum. Hood ON is the guard.",
        ],
        "SET-UP",
    )
    sh.save("A05_holddowns.svg")


# ---------------------------------------------------------------------------
# Hardware BOM sheet (Wandel "Hardware" page)
# ---------------------------------------------------------------------------


def sheet_h01() -> None:
    sh = Sheet("H-01", "Hardware", "Illustrated buy-list  ·  qty is for one machine")
    sh.titleblock(qty="BUY", material="Confirm flange BCD · mixed inch/metric ok if consistent")
    items = [
        (80, 110, "H-001 / H-002", "Mounted ball bearings, 1¼″ bore, self-aligning. Need 2. Drive FIXED, idler FLOATING. Required C on H-02."),
        (80, 250, "H-007", "½-10 Acme × 12″ + bronze nut + flange. Need 2."),
        (80, 370, "H-013", "Star knobs ⅜-16 + 1½″ studs. Need 6. Way locks and yokes."),
        (80, 500, "H-014 / H-015", "#8 × 1¼″ (need 100) and #8 × 2″ (need 50) coarse cabinet screws."),
        (80, 640, "H-021", "Dial indicator 0.001″ + mag base. Or a caliper in wooden blocks."),
        (80, 780, "H-009", f"Rubber rollers ⌀{inch(S.roller_od)}\" × ~{inch(G.roller_len)}\". Need 2."),
        (900, 110, "H-003 / H-004", f"{inch(S.pulley_motor_od)}\" motor and {inch(S.pulley_drum_od)}\" drum 4L pulleys."),
        (900, 250, "H-006", f"{S.motor_hp:g} HP {S.motor_rpm:g} RPM TEFC, 115 V. Code the wiring."),
        (900, 370, "H-017", "5/16-18 × 1″ hex + nylock + washer. Need 8. Confirm flange hole."),
        (900, 500, "H-016", "¼-20 T-nuts + 1¼″ bolts. Need 8. Motor cradle."),
        (900, 640, "H-018", "⅛″ piano wire, 12″. Disc keys — must fit tightly."),
        (900, 780, "H-022", "Hook Velcro 4″ PSA + 3″ loop paper 80/120/180/220."),
    ]
    # simple hardware glyphs
    sh.circle(140, 170, 36, fill=STEEL, stroke=INK, sw=1.4)
    sh.circle(140, 170, 10, fill=PAPER, stroke=INK, sw=1.2)
    for a in (45, 135, 225, 315):
        x = 140 + 24 * math.cos(math.radians(a))
        y = 170 + 24 * math.sin(math.radians(a))
        sh.circle(x, y, 4, fill=PAPER, stroke=INK, sw=1.0)

    sh.rect(120, 300, 12, 90, fill=STEEL, stroke=INK, sw=1.2)
    sh.rect(108, 388, 36, 14, fill=BRONZE, stroke=INK, sw=1.1)

    # star knob
    cx, cy = 140, 545
    pts = []
    for i in range(8):
        ang = math.radians(-90 + i * 45)
        r = 22 if i % 2 == 0 else 12
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    sh.poly(pts, fill=KNOB, stroke=INK, sw=1.2)
    sh.circle(cx, cy, 5, fill=STEEL, stroke=INK, sw=1.0)

    # screws
    for i, length in enumerate((42, 32, 24)):
        x = 110 + i * 28
        sh.rect(x, 690, 8, length, fill=STEEL, stroke=INK, sw=1.0)
        sh.poly([(x - 3, 690), (x + 11, 690), (x + 4, 682)], fill=STEEL, stroke=INK, sw=0.8)

    sh.circle(140, 830, 28, fill=STEEL, stroke=INK, sw=1.3)
    sh.text(140, 834, "0.001", 9, INK, "middle")

    sh.rect(120, 900, 90, 18, fill=KNOB, stroke=INK, sw=1.1, rx=8)

    sh.circle(960, 175, 28, fill=STEEL, stroke=INK, sw=1.3)
    sh.circle(1040, 175, 40, fill=STEEL, stroke=INK, sw=1.3)

    sh.rect(930, 300, 70, 50, fill=KNOB, stroke=INK, sw=1.2)

    sh.rect(950, 410, 10, 36, fill=STEEL, stroke=INK, sw=1.0)
    sh.poly([(945, 410), (965, 410), (955, 400)], fill=STEEL, stroke=INK, sw=0.8)

    for line_x, line_y, code, desc in items:
        sh.text(line_x + 90 if line_x < 800 else line_x + 120, line_y + 20, code, 13, ACC, bold=True)
        wrap = _wrap(desc, 48)
        yy = line_y + 40
        for row in wrap:
            sh.text(line_x + 90 if line_x < 800 else line_x + 120, yy, row, 12, NOTE, mono=False)
            yy += 16

    sh.text(80, 1048, "Also: H-005 belt (size after cradle lock) · H-008 #25 chain + left clutch/dog · H-011 springs · H-012 shoulder bolts · H-019 4″ port · H-020 switch/cord · H-023 Titebond III · H-024 paste wax · H-025 optional osc motor.", 12, DIM, mono=False)
    sh.save("H01_hardware.svg")


def sheet_idx() -> None:
    sh = Sheet("IDX", "Drawing index", "Print A3 landscape  ·  part sheets are the fabrication drawings")
    sh.titleblock(qty=f"fab {S.fabrication_rev}", material="Python SSOT  cad/walter_ds16.py")
    sh.text(48, 110, "Use the P-sheets to cut and drill. D-1…D-12 are overviews. A-sheets are assembly. H-01 is the buy list.", 14, NOTE, mono=False)
    groups = [
        ("OVERVIEW", [d for d in shop_drawings() if d["group"] == "overview"]),
        ("PARTS (MAKE)", [d for d in shop_drawings() if d["group"] == "part"]),
        ("ASSEMBLY", [d for d in shop_drawings() if d["group"] == "assembly"]),
        ("HARDWARE / INDEX", [d for d in shop_drawings() if d["group"] in ("hardware", "index")]),
    ]
    x0 = 48
    for gi, (title, rows) in enumerate(groups):
        x = x0 + (gi % 2) * 800
        y = 150 + (gi // 2) * 420
        sh.text(x, y, title, 16, ACC, bold=True)
        yy = y + 28
        sh.text(x, yy, "CODE", 11, DIM, bold=True)
        sh.text(x + 110, yy, "SHEET", 11, DIM, bold=True)
        sh.text(x + 420, yy, "FILE", 11, DIM, bold=True)
        yy += 20
        for d in rows:
            sh.text(x, yy, d["code"], 13, ACC, bold=True)
            sh.text(x + 110, yy, d["title"][:34], 13, INK, mono=False)
            sh.text(x + 420, yy, d["file"], 12, DIM)
            yy += 20
    sh.text(48, 1040, "Color: green = plywood structure · tan = solid wood / jigs · silver = hardware · pale = UHMW. Flange bolt circle is ASSUMED until you transfer the part you bought.", 13, DIM, mono=False)
    sh.save("IDX_drawings.svg")


def main() -> None:
    sheet_idx()
    sheet_p001("L")
    sheet_p001("R")
    sheet_p002()
    sheet_p003()
    sheet_p004()
    sheet_p005()
    sheet_p006()
    sheet_p007()
    sheet_disc("P-008", "P008_disc_core.svg", MDF, ["Core discs are MDF. They true fast; they also absorb humidity — store the drum indoors."])
    sheet_disc("P-009", "P009_disc_end.svg", GREEN, ["Birch ends. Static-balance these two. They take the flange load."])
    sheet_p010()
    sheet_p011()
    sheet_p012()
    sheet_p013()
    sheet_p014()
    sheet_p015()
    sheet_p016()
    sheet_p017()
    sheet_p018()
    sheet_p019()
    sheet_p020()
    sheet_p021()
    sheet_p022()
    sheet_p023()
    sheet_p024()
    sheet_a01()
    sheet_a02()
    sheet_a03()
    sheet_a04()
    sheet_a05()
    sheet_h01()
    print("done →", OUT, "sheets", len([d for d in shop_drawings() if d.get("dir") != "renders"]))


if __name__ == "__main__":
    main()
