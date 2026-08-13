#!/usr/bin/env python3
"""Isometric / orthographic 3D views of WALTER DS-16 from the parametric spec.

Writes SVG renders (assembled, exploded, front, side) plus plan sheet D-9.
Run:  python3 scripts/gen_drum_sander_iso.py
"""

from __future__ import annotations

import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "shop", "drum-sander", "cad"))
from walter_ds16 import SPEC as S  # noqa: E402

REND = os.path.join(ROOT, "shop", "drum-sander", "renders")
PLANS = os.path.join(ROOT, "shop", "drum-sander", "plans")
os.makedirs(REND, exist_ok=True)

INK = "#1a1f24"
PAPER = "#f3f1ec"


def shade(hex_color: str, k: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = max(0, min(255, int(r * k)))
    g = max(0, min(255, int(g * k)))
    b = max(0, min(255, int(b * k)))
    return f"#{r:02x}{g:02x}{b:02x}"


class Mesh:
    def __init__(self, part: str, color: str):
        self.part = part
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
        # light from (+x, +y, -z)
        lit = max(0.35, min(1.0, 0.45 + 0.55 * (nx * 0.35 + ny * 0.85 - nz * 0.4)))
        self.faces.append((tuple(verts), lit))


def box(part, color, x0, y0, z0, dx, dy, dz) -> Mesh:
    """Axis-aligned box. y is up."""
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
    m = Mesh(part, color)
    faces = (
        (0, 1, 2, 3),  # -z
        (5, 4, 7, 6),  # +z
        (4, 0, 3, 7),  # -x
        (1, 5, 6, 2),  # +x
        (4, 5, 1, 0),  # -y
        (3, 2, 6, 7),  # +y
    )
    for idx in faces:
        m.add_face([p[i] for i in idx])
    return m


def cyl_x(part, color, cx, cy, cz, length, r, segs=16) -> Mesh:
    """Cylinder along X, centered at (cx,cy,cz)."""
    m = Mesh(part, color)
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


def machine(explode: float = 0.0) -> list[Mesh]:
    """Build solid list. explode 0–1 separates major groups."""
    e = explode
    side_t = S.side_thick
    clear = S.clear_between_sides
    W = clear + 2 * side_t
    D = S.side_depth
    H = S.side_height
    hx, hz = W / 2, D / 2

    ex_side = e * 4.5
    ey_hood = e * 7
    ey_drum = e * 3.5
    ey_table = e * -3.2
    ez_motor = e * -5
    ez_roll = e * 2.2

    meshes: list[Mesh] = []

    # Base
    meshes.append(box("base", "#a89070", -hx, 0, -hz, W, 0.75, D))

    # Sides
    meshes.append(box("sides", "#c4a574", -hx - ex_side, 0.75, -hz, side_t, H - 0.75, D))
    meshes.append(box("sides", "#c4a574", hx - side_t + ex_side, 0.75, -hz, side_t, H - 0.75, D))

    # Stretchers (3)
    for y in (6.0, 12.0, 20.0):
        meshes.append(box("stretch", "#8a7355", -hx + side_t, y, -2.0, clear, 0.75, 4.0))

    # Ways
    meshes.append(box("ways", "#d9dcde", -hx + side_t, 10.0, -hz + 1, 0.75, 0.75, D - 2))
    meshes.append(box("ways", "#d9dcde", hx - side_t - 0.75, 10.0, -hz + 1, 0.75, 0.75, D - 2))

    # Table + wear
    tw, td, tt = S.table_width, S.table_depth, S.table_thick
    ty = 14.0 + ey_table
    meshes.append(box("table", "#c4b8a4", -tw / 2, ty, -td / 2, tw, tt - 0.25, td))
    meshes.append(box("table", "#d9dcde", -tw / 2, ty + tt - 0.25, -td / 2, tw, 0.25, td))

    # Acme screws
    for x in (-6.8, 6.8):
        meshes.append(box("elev", "#8a9098", x - 0.25, 2.0, -6.25, 0.5, 14.0 + ey_table * 0.3, 0.5))

    # Drum / shaft / bearings
    dy = 18.5 + ey_drum
    meshes.append(cyl_x("drum", "#b8a990", 0, dy, 0, S.drum_length, S.drum_od / 2, 20))
    meshes.append(cyl_x("shaft", "#8a9098", 0, dy, 0, S.shaft_length, S.shaft_od / 2, 12))
    for x, part in ((-8.1, "shaft"), (8.1, "shaft")):
        meshes.append(box(part, "#6e7578", x - 0.35, dy - 1.4, -1.4, 0.7, 2.8, 2.8))

    # Pulleys + belt hint
    meshes.append(cyl_x("motor", "#5a6068", 10.4, dy, 0, 0.9, 2.5, 16))  # drum pulley
    mx = 6.2
    my = 6.5
    mz = -7.5 + ez_motor
    meshes.append(box("motor", "#4a5058", mx - 3, my, mz, 6.0, 6.0, 8.0))
    meshes.append(cyl_x("motor", "#5a6068", mx + 3.2, my + 3.2, mz + 4, 0.8, 1.5, 14))

    # Hold-down rollers
    ry = 16.15 + ey_table
    meshes.append(cyl_x("rollers", "#5a6068", 0, ry, -3.6 - ez_roll, S.roller_len, S.roller_od / 2, 12))
    meshes.append(cyl_x("rollers", "#5a6068", 0, ry, 3.6 + ez_roll, S.roller_len, S.roller_od / 2, 12))
    meshes.append(box("rollers", "#8a7355", -8.2, ry + 0.4, -4.4 - ez_roll, 16.4, 0.4, 0.8))
    meshes.append(box("rollers", "#8a7355", -8.2, ry + 0.4, 3.6 + ez_roll, 16.4, 0.4, 0.8))

    # Hood (faceted arch of boxes)
    for i in range(7):
        a0 = math.pi * (0.12 + i * 0.12)
        a1 = math.pi * (0.12 + (i + 1) * 0.12)
        r0, r1 = 4.4, 5.6
        # approximate with a thin box along the arc
        mid = (a0 + a1) / 2
        cx = 0
        cy = dy + (r0 + r1) / 2 * math.sin(mid) * 0.15 + ey_hood
        # simpler: stacked roof slabs
        t = i / 6
        y = dy + 2.2 + math.sin(t * math.pi) * 2.8 + ey_hood
        z = -4.2 + t * 8.4
        meshes.append(box("hood", "#9aa8a0", -7.6, y, z - 0.7, 15.2, 0.35, 1.4))
    meshes.append(cyl_x("hood", "#7a8f68", 7.6, dy + 4.8 + ey_hood, 0, 1.2, 2.0, 12))  # 4" port

    return meshes


def project(p, mode: str):
    x, y, z = p
    if mode == "iso":
        sx = (x - z) * math.cos(math.radians(30))
        sy = y + (x + z) * math.sin(math.radians(30))
        depth = x * 0.3 + y * 0.2 + z * 0.9
        return sx, sy, depth
    if mode == "front":  # looking +z
        return x, y, -z
    if mode == "side":  # looking +x (drive side)
        return -z, y, x
    raise ValueError(mode)


def render(meshes: list[Mesh], mode: str, w: int, h: int, pad: float = 48) -> str:
    tris: list[tuple[float, str, list[tuple[float, float]]]] = []
    for m in meshes:
        for verts, lit in m.faces:
            proj = [project(v, mode) for v in verts]
            depth = sum(p[2] for p in proj) / len(proj)
            # backface: skip if projected area winds wrong and dim
            area = 0.0
            for i, p in enumerate(proj):
                q = proj[(i + 1) % len(proj)]
                area += p[0] * q[1] - q[0] * p[1]
            if area <= 0:
                continue
            col = shade(m.color, 0.55 + 0.45 * lit)
            tris.append((depth, col, [(p[0], p[1]) for p in proj]))
    tris.sort(key=lambda t: t[0])  # far to near

    xs = [x for _, _, pts in tris for x, _ in pts]
    ys = [y for _, _, pts in tris for _, y in pts]
    if not xs:
        xs, ys = [0], [0]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    spanx = max(maxx - minx, 1e-6)
    spany = max(maxy - miny, 1e-6)
    scale = min((w - 2 * pad) / spanx, (h - 2 * pad) / spany)

    def xy(x, y):
        return pad + (x - minx) * scale, h - pad - (y - miny) * scale

    parts = [
        f"<rect width='{w}' height='{h}' fill='{PAPER}'/>",
    ]
    for _, col, pts in tris:
        d = " ".join(f"{xy(x, y)[0]:.1f},{xy(x, y)[1]:.1f}" for x, y in pts)
        parts.append(
            f"<polygon points='{d}' fill='{col}' stroke='{INK}' stroke-width='0.7' "
            f"stroke-linejoin='round'/>"
        )
    return "\n".join(parts)


def write_svg(path: str, body: str, w: int, h: int, title: str) -> None:
    svg = (
        f"<?xml version='1.0' encoding='UTF-8'?>\n"
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' "
        f"viewBox='0 0 {w} {h}'>\n"
        f"<title>{title}</title>\n{body}\n</svg>\n"
    )
    with open(path, "w") as f:
        f.write(svg)
    print("wrote", path)


def sheet_d9():
    w, h = 1680, 1188
    iso = render(machine(0), "iso", 820, 620, 36)
    exp = render(machine(0.85), "iso", 820, 620, 36)
    front = render(machine(0), "front", 520, 420, 28)
    side = render(machine(0), "side", 520, 420, 28)

    def nest(x, y, inner, iw, ih):
        return f"<g transform='translate({x},{y})'>{inner}</g>"

    body = [
        f"<rect width='{w}' height='{h}' fill='{PAPER}' stroke='{INK}' stroke-width='3'/>",
        f"<rect x='24' y='24' width='{w-48}' height='{h-48}' fill='none' stroke='{INK}' stroke-width='1.2'/>",
        f"<line x1='24' y1='{h-90}' x2='{w-24}' y2='{h-90}' stroke='{INK}' stroke-width='1.5'/>",
        "<text x='40' y='1130' font-family='Georgia, serif' font-size='28' fill='#3d5a4c' font-weight='600'>WALTER</text>",
        "<text x='170' y='1126' font-family='IBM Plex Mono, Menlo, monospace' font-size='18' fill='#1a1f24' font-weight='600'>D-9  ·  3D model views</text>",
        "<text x='40' y='1154' font-family='IBM Plex Mono, Menlo, monospace' font-size='13' fill='#5a6a4a'>Isometric · exploded · orthographic · inches</text>",
        "<text x='1640' y='1130' font-family='IBM Plex Mono, Menlo, monospace' font-size='14' fill='#5a6a4a' text-anchor='end'>DS-16 · Rev B geometry</text>",
        "<text x='1640' y='1154' font-family='IBM Plex Mono, Menlo, monospace' font-size='13' fill='#5a6a4a' text-anchor='end'>Parametric solids from walter_ds16.py</text>",
        "<text x='48' y='62' font-family='IBM Plex Mono, Menlo, monospace' font-size='16' fill='#3d5a4c' font-weight='600'>ISOMETRIC — assembled</text>",
        nest(40, 70, iso, 820, 620),
        "<text x='880' y='62' font-family='IBM Plex Mono, Menlo, monospace' font-size='16' fill='#3d5a4c' font-weight='600'>ISOMETRIC — exploded</text>",
        nest(860, 70, exp, 820, 620),
        "<text x='48' y='720' font-family='IBM Plex Mono, Menlo, monospace' font-size='16' fill='#3d5a4c' font-weight='600'>FRONT</text>",
        nest(40, 730, front, 520, 420),
        "<text x='600' y='720' font-family='IBM Plex Mono, Menlo, monospace' font-size='16' fill='#3d5a4c' font-weight='600'>DRIVE SIDE</text>",
        nest(580, 730, side, 520, 420),
        "<text x='1140' y='750' font-family='IBM Plex Mono, Menlo, monospace' font-size='13' fill='#1a1f24'>Baltic birch frame · UHMW ways</text>",
        "<text x='1140' y='778' font-family='IBM Plex Mono, Menlo, monospace' font-size='13' fill='#1a1f24'>Torsion-box table + wear face</text>",
        "<text x='1140' y='806' font-family='IBM Plex Mono, Menlo, monospace' font-size='13' fill='#1a1f24'>⌀5″ drum · dual Acme · hold-downs</text>",
        "<text x='1140' y='834' font-family='IBM Plex Mono, Menlo, monospace' font-size='13' fill='#1a1f24'>Interactive model: /shop/drum-sander/model/</text>",
        "<text x='1140' y='862' font-family='IBM Plex Mono, Menlo, monospace' font-size='13' fill='#1a1f24'>OpenSCAD: cad/walter_ds16.scad</text>",
    ]
    write_svg(os.path.join(PLANS, "D9_model.svg"), "\n".join(body), w, h, "WALTER DS-16 D-9 3D model views")


def main():
    write_svg(
        os.path.join(REND, "iso_assembled.svg"),
        render(machine(0), "iso", 1400, 1000, 60),
        1400,
        1000,
        "WALTER DS-16 isometric assembled",
    )
    write_svg(
        os.path.join(REND, "iso_exploded.svg"),
        render(machine(1.0), "iso", 1400, 1000, 60),
        1400,
        1000,
        "WALTER DS-16 isometric exploded",
    )
    write_svg(
        os.path.join(REND, "ortho_front.svg"),
        render(machine(0), "front", 1200, 900, 50),
        1200,
        900,
        "WALTER DS-16 front elevation solid",
    )
    write_svg(
        os.path.join(REND, "ortho_side.svg"),
        render(machine(0), "side", 1200, 900, 50),
        1200,
        900,
        "WALTER DS-16 drive-side solid",
    )
    sheet_d9()


if __name__ == "__main__":
    main()
