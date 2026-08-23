#!/usr/bin/env python3
"""Export WALTER CAD: STL, OBJ, parameters.json, isometric/ortho SVG renders.

No FreeCAD or OpenSCAD required. Geometry comes from walter_kernel.py.
Run:  python3 scripts/gen_walter_cad.py
"""

from __future__ import annotations

import json
import math
import os
import struct
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(ROOT, "..", "sander", "walter", "cad")
sys.path.insert(0, CAD)

from walter_kernel import (  # noqa: E402
    Box,
    Cyl,
    IN,
    P,
    REV,
    assembly,
    dump_parameters,
)

EXPORTS = os.path.join(CAD, "exports")
RENDERS = os.path.join(CAD, "..", "renders")
os.makedirs(EXPORTS, exist_ok=True)
os.makedirs(RENDERS, exist_ok=True)


# ---- tessellation ------------------------------------------------------------
def _n(a, b, c):
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    L = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return (nx / L, ny / L, nz / L)


def box_tris(p: Box):
    x, y, z, dx, dy, dz = p.x, p.y, p.z, p.dx, p.dy, p.dz
    v = [
        (x, y, z), (x + dx, y, z), (x + dx, y + dy, z), (x, y + dy, z),
        (x, y, z + dz), (x + dx, y, z + dz), (x + dx, y + dy, z + dz), (x, y + dy, z + dz),
    ]
    faces = (
        (0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
        (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0),
    )
    tris = []
    for a, b, c, d in faces:
        tris.append((v[a], v[b], v[c]))
        tris.append((v[a], v[c], v[d]))
    return tris


def cyl_tris(p: Cyl, segs=24):
    d, h = p.d, p.h
    r = d / 2.0
    ax = p.axis
    tris = []

    def pt(i, along, rad=r):
        a = 2 * math.pi * i / segs
        c, s = math.cos(a), math.sin(a)
        if ax == "x":
            return (p.x + along, p.y + rad * c, p.z + rad * s)
        if ax == "y":
            return (p.x + rad * c, p.y + along, p.z + rad * s)
        return (p.x + rad * c, p.y + rad * s, p.z + along)

    for i in range(segs):
        j = (i + 1) % segs
        a0, a1 = pt(i, 0), pt(j, 0)
        b0, b1 = pt(i, h), pt(j, h)
        tris.append((a0, a1, b1))
        tris.append((a0, b1, b0))
        ctr0 = pt(0, 0, 0)
        ctr1 = pt(0, h, 0)
        tris.append((ctr0, a1, a0))
        tris.append((ctr1, b0, b1))
    return tris


def prim_tris(p):
    if isinstance(p, Box):
        return box_tris(p)
    return cyl_tris(p)


def to_mm(tri):
    return tuple((x * IN, y * IN, z * IN) for (x, y, z) in tri)


# ---- STL / OBJ ---------------------------------------------------------------
def write_stl(path, tris_mm, name="walter"):
    n = len(tris_mm)
    with open(path, "wb") as f:
        header = name.encode("ascii", "replace")[:80].ljust(80, b"\0")
        f.write(header)
        f.write(struct.pack("<I", n))
        for a, b, c in tris_mm:
            nx, ny, nz = _n(a, b, c)
            f.write(struct.pack("<12fH", nx, ny, nz, *a, *b, *c, 0))
    print("wrote", path, n, "tris")


def write_obj(path, parts):
    vcount = 1
    lines = ["# WALTER drum sander Rev " + REV, "o walter"]
    for p in parts:
        for a, b, c in prim_tris(p):
            for pt in (a, b, c):
                lines.append("v {:.4f} {:.4f} {:.4f}".format(pt[0] * IN, pt[1] * IN, pt[2] * IN))
            lines.append(f"f {vcount} {vcount+1} {vcount+2}")
            vcount += 3
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote", path)


# ---- SVG projection ----------------------------------------------------------
def iso(x, y, z):
    # classic cabinet isometric, inches → px later
    sx = (x - y) * 0.86602540378
    sy = -z + (x + y) * 0.5
    return sx, sy


def ortho_front(x, y, z):
    return x, -z


def ortho_side(x, y, z):
    return y, -z


def ortho_top(x, y, z):
    return x, -y


def face_quads(p: Box):
    x, y, z, dx, dy, dz = p.x, p.y, p.z, p.dx, p.dy, p.dz
    v = [
        (x, y, z), (x + dx, y, z), (x + dx, y + dy, z), (x, y + dy, z),
        (x, y, z + dz), (x + dx, y, z + dz), (x + dx, y + dy, z + dz), (x, y + dy, z + dz),
    ]
    return [
        (p.color, (v[0], v[1], v[2], v[3])),
        (p.color, (v[4], v[5], v[6], v[7])),
        (p.color, (v[0], v[1], v[5], v[4])),
        (p.color, (v[1], v[2], v[6], v[5])),
        (p.color, (v[2], v[3], v[7], v[6])),
        (p.color, (v[3], v[0], v[4], v[7])),
    ]


def cyl_quads(p: Cyl, segs=16):
    faces = []
    r, h, ax = p.d / 2.0, p.h, p.axis

    def pt(i, along):
        a = 2 * math.pi * i / segs
        c, s = math.cos(a), math.sin(a)
        if ax == "x":
            return (p.x + along, p.y + r * c, p.z + r * s)
        if ax == "y":
            return (p.x + r * c, p.y + along, p.z + r * s)
        return (p.x + r * c, p.y + r * s, p.z + along)

    for i in range(segs):
        j = (i + 1) % segs
        faces.append((p.color, (pt(i, 0), pt(j, 0), pt(j, h), pt(i, h))))
    return faces


def project_scene(parts, proj, scale, ox, oy, w, h, bg="#14110e", stroke="#1c1914"):
    faces = []
    for p in parts:
        if isinstance(p, Box):
            faces.extend(face_quads(p))
        else:
            faces.extend(cyl_quads(p))

    def depth(face):
        pts = face[1]
        return sum(pts[i][0] + pts[i][1] + pts[i][2] for i in range(len(pts))) / len(pts)

    faces.sort(key=depth)
    polys = []
    xs, ys = [], []
    for color, pts in faces:
        xy = [proj(*pt) for pt in pts]
        xs += [p[0] for p in xy]
        ys += [p[1] for p in xy]
        polys.append((color, xy))
    if not xs:
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"/>'
    # fit
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    sx = (w - 80) / (maxx - minx + 1e-6)
    sy = (h - 80) / (maxy - miny + 1e-6)
    s = min(sx, sy) * scale
    cx = (minx + maxx) / 2
    cy = (miny + maxy) / 2

    def T(x, y):
        return ox + (x - cx) * s + w / 2, oy + (y - cy) * s + h / 2

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        f'<rect width="{w}" height="{h}" fill="{bg}"/>',
    ]
    for color, xy in polys:
        pts = " ".join(f"{T(x,y)[0]:.1f},{T(x,y)[1]:.1f}" for x, y in xy)
        out.append(
            f'<polygon points="{pts}" fill="{color}" stroke="{stroke}" '
            f'stroke-width="0.7" stroke-linejoin="round"/>'
        )
    out.append("</svg>")
    return "\n".join(out)


def save_svg(path, svg):
    with open(path, "w") as f:
        f.write(svg + "\n")
    print("wrote", path)


def scad_parameters(path):
    lines = ["// auto-generated from walter_kernel.py — do not edit by hand", "IN = 25.4;", "function inch(n) = n * IN;"]
    skip = {"acme_y"}
    for k, v in P.items():
        if k in skip:
            continue
        if isinstance(v, (int, float)):
            lines.append(f"{k} = inch({v});")
    lines.append(f"acme_y = [inch({P['acme_y'][0]}), inch({P['acme_y'][1]})];")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote", path)


def main():
    dump_parameters(os.path.join(CAD, "parameters.json"))
    parts_preview = assembly(opening=1.5, explode=0, cutaway=False, discs=True)
    with open(os.path.join(CAD, "parts.json"), "w") as f:
        json.dump(
            {
                "rev": REV,
                "count": len(parts_preview),
                "groups": sorted({p.group for p in parts_preview}),
                "parts": [{"name": p.name, "group": p.group, "kind": p.kind} for p in parts_preview],
            },
            f,
            indent=2,
        )
        f.write("\n")
    print("wrote", os.path.join(CAD, "parts.json"), len(parts_preview), "solids")
    scad_parameters(os.path.join(CAD, "scad", "parameters.scad") if False else os.path.join(CAD, "parameters.scad"))

    scenes = {
        "assembly": assembly(opening=1.5, explode=0, cutaway=False, discs=True),
        "cutaway": assembly(opening=1.5, explode=0, cutaway=True, discs=True),
        "exploded": assembly(opening=1.5, explode=1.0, cutaway=False, discs=True),
        "stand": assembly(opening=1.5, explode=0, cutaway=False, discs=False, stand=True),
    }

    groups = ("frame", "steel", "drum", "table", "conveyor", "motor", "hood", "guard")
    assembled = scenes["assembly"]
    for g in groups:
        subset = [p for p in assembled if p.group == g]
        if not subset:
            continue
        tris = [to_mm(t) for p in subset for t in prim_tris(p)]
        write_stl(os.path.join(EXPORTS, f"walter_{g}.stl"), tris, f"walter_{g}")
    tris_all = [to_mm(t) for p in assembled for t in prim_tris(p)]
    write_stl(os.path.join(EXPORTS, "walter_assembly.stl"), tris_all, "walter_assembly")
    write_obj(os.path.join(EXPORTS, "walter_assembly.obj"), assembled)
    exploded = scenes["exploded"]
    write_stl(
        os.path.join(EXPORTS, "walter_exploded.stl"),
        [to_mm(t) for p in exploded for t in prim_tris(p)],
        "walter_exploded",
    )
    write_stl(
        os.path.join(EXPORTS, "walter_stand.stl"),
        [to_mm(t) for p in scenes["stand"] for t in prim_tris(p)],
        "walter_stand",
    )

    # compact disc-less mesh for preview speed (hide the belt guard so the drum reads)
    preview = [
        p for p in assembly(opening=1.5, explode=0, cutaway=False, discs=False)
        if p.group != "guard"
    ]
    save_svg(
        os.path.join(RENDERS, "walter_iso.svg"),
        project_scene(preview, iso, 0.92, 0, 0, 1600, 1000, bg="#14110e", stroke="#2a241c"),
    )
    save_svg(
        os.path.join(RENDERS, "walter_infeed.svg"),
        project_scene(preview, ortho_front, 0.95, 0, 0, 1400, 1000, bg="#14110e", stroke="#2a241c"),
    )
    save_svg(
        os.path.join(RENDERS, "walter_drive.svg"),
        project_scene(preview, ortho_side, 0.95, 0, 0, 1600, 900, bg="#14110e", stroke="#2a241c"),
    )
    save_svg(
        os.path.join(RENDERS, "walter_top.svg"),
        project_scene(preview, ortho_top, 0.95, 0, 0, 1400, 900, bg="#14110e", stroke="#2a241c"),
    )
    save_svg(
        os.path.join(RENDERS, "walter_cutaway.svg"),
        project_scene(
            assembly(1.5, 0, True, discs=False), iso, 0.92, 0, 0, 1600, 1000, bg="#14110e", stroke="#2a241c"
        ),
    )
    save_svg(
        os.path.join(RENDERS, "walter_exploded.svg"),
        project_scene(
            assembly(1.5, 1.0, False, discs=False), iso, 0.88, 0, 0, 1600, 1100, bg="#14110e", stroke="#2a241c"
        ),
    )
    save_svg(
        os.path.join(RENDERS, "walter_stand.svg"),
        project_scene(scenes["stand"], iso, 0.9, 0, 0, 1400, 1100, bg="#14110e", stroke="#2a241c"),
    )
    # paper-friendly light isometric for print covers
    save_svg(
        os.path.join(RENDERS, "walter_iso_paper.svg"),
        project_scene(preview, iso, 0.92, 0, 0, 1600, 1000, bg="#f4efe6", stroke="#3a3228"),
    )
    # hero = iso
    save_svg(os.path.join(RENDERS, "hero.svg"), open(os.path.join(RENDERS, "walter_iso.svg")).read())
    print("WALTER CAD Rev", REV, "done")


if __name__ == "__main__":
    main()
