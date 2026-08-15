#!/usr/bin/env python3
"""SHINOBI//82 KAGE — parametric part builder.

Builds each kit part from parameters.json, writes STL (downloadable CAD)
and a shared TOGI hammered texture sampled from the plate still.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image

ROOT = Path(__file__).resolve().parent
OUT_STL = ROOT / "stl"
OUT_TEX = ROOT.parent / "assets" / "cad"
PARAMS = json.loads((ROOT / "parameters.json").read_text())


def merge(meshes: list[trimesh.Trimesh]) -> trimesh.Trimesh:
    mesh = trimesh.util.concatenate(meshes)
    mesh.merge_vertices()
    mesh.remove_unreferenced_vertices()
    return mesh


def box(sx: float, sy: float, sz: float, at=(0.0, 0.0, 0.0)) -> trimesh.Trimesh:
    m = trimesh.creation.box(extents=(sx, sy, sz))
    m.apply_translation(at)
    return m


def cyl(r: float, h: float, at=(0.0, 0.0, 0.0), axis="z") -> trimesh.Trimesh:
    m = trimesh.creation.cylinder(radius=r, height=h, sections=28)
    if axis == "x":
        m.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
    elif axis == "y":
        m.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
    m.apply_translation(at)
    return m


def cone(r: float, h: float, at=(0.0, 0.0, 0.0), axis="x") -> trimesh.Trimesh:
    m = trimesh.creation.cone(radius=r, height=h, sections=28)
    if axis == "x":
        m.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [0, 1, 0]))
    m.apply_translation(at)
    return m


def blade_body(length: float, heel_h: float, tip_h: float, heel_t: float, tip_t: float, tang: float) -> trimesh.Trimesh:
    """Tapered blade + rectangular tang. X along length, Y height, Z thickness."""
    hx, hy, hz = heel_t / 2, heel_h / 2, 0
    tx, ty = tip_t / 2, tip_h / 2
    verts = np.array(
        [
            [0, -hy, -hx],
            [0, hy, -hx],
            [0, hy, hx],
            [0, -hy, hx],
            [length, -ty, -tx],
            [length, ty * 0.35, -tx],
            [length, ty * 0.15, tx],
            [length, -ty, tx],
        ],
        dtype=float,
    )
    faces = np.array(
        [
            [0, 1, 2],
            [0, 2, 3],
            [4, 6, 5],
            [4, 7, 6],
            [0, 4, 5],
            [0, 5, 1],
            [1, 5, 6],
            [1, 6, 2],
            [2, 6, 7],
            [2, 7, 3],
            [3, 7, 4],
            [3, 4, 0],
        ],
        dtype=int,
    )
    blade = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    tang_m = box(tang, min(heel_h * 0.72, 10.2), min(heel_t * 1.15, 2.2), (-tang / 2, 0, 0))
    return merge([blade, tang_m])


def part_frame(p: dict) -> trimesh.Trimesh:
    L, H, R, rail = p["length"], p["height"], p["ridge"], p["rail"]
    web = p["web"]
    pieces = [
        box(L - 8, rail, R, (L / 2 - 2, H / 2 - rail / 2, 0)),
        box(L - 18, rail, R * 0.78, (L / 2 - 6, -H / 2 + rail / 2, 0)),
        box(web, H - 2.2, R * 0.7, (18, 0, 0)),
        box(web, H - 3.4, R * 0.7, (40, 0.4, 0)),
        box(web, H - 2.8, R * 0.7, (62, -0.2, 0)),
        box(12, H, R, (L - 4, 0, 0)),
        box(10, H * 0.7, R, (4, 0, 0)),
    ]
    pommel = cyl(H / 2.15, R, (L + 2, 0, 0), axis="z")
    hole = cyl(p["pommel_hole"] / 2, R + 2, (L + 2, 0, 0), axis="z")
    body = merge(pieces + [pommel])
    try:
        body = body.difference(hole, engine="auto")
    except Exception:
        body = merge([body])
    return body


def part_mizu(p: dict) -> trimesh.Trimesh:
    return blade_body(p["blade"], p["heel_height"], p["tip_height"], p["heel_thick"], p["tip_thick"], p["tang"])


def part_kumiko(p: dict) -> trimesh.Trimesh:
    blade = blade_body(p["blade"], p["height"], p["height"] * 0.55, p["thick"], p["thick"] * 0.55, p["tang"])
    return blade


def part_nata(p: dict) -> trimesh.Trimesh:
    return blade_body(p["blade"], p["height"], p["height"] * 0.7, p["thick"], p["thick"] * 0.7, p["tang"])


def part_saya(p: dict) -> trimesh.Trimesh:
    outer = box(p["length"], p["width"], p["height"])
    inner = box(p["length"] - p["wall"] * 2, p["width"] - p["wall"] * 2, p["height"] - p["wall"], (2, 0, 0.2))
    try:
        body = outer.difference(inner, engine="auto")
    except Exception:
        body = merge([box(p["length"], p["width"], p["wall"], (0, 0, -p["height"] / 2 + p["wall"] / 2)),
                      box(p["length"], p["wall"], p["height"], (0, p["width"] / 2 - p["wall"] / 2, 0)),
                      box(p["length"], p["wall"], p["height"], (0, -p["width"] / 2 + p["wall"] / 2, 0)),
                      box(p["wall"], p["width"], p["height"], (-p["length"] / 2 + p["wall"] / 2, 0, 0))])
    drain = cyl(1.6, p["width"] + 2, (p["length"] / 2 - 8, 0, -p["height"] / 2 + 1.2), axis="y")
    try:
        body = body.difference(drain, engine="auto")
    except Exception:
        pass
    return body


def part_spike(p: dict) -> trimesh.Trimesh:
    point = cone(p["root"] / 2, p["point"], (p["point"] / 2, 0, 0), axis="x")
    tang = cyl(p["root"] / 2 * 0.92, p["tang"], (-p["tang"] / 2, 0, 0), axis="x")
    cap = cyl(4.2, 3.2, (-p["tang"] - 1.2, 0, 0), axis="x")
    return merge([point, tang, cap])


def part_togi(p: dict) -> trimesh.Trimesh:
    plate = box(p["length"], p["width"], p["thick"])
    h1 = cyl(p["hole"] / 2, p["thick"] + 2, (p["length"] / 2 - 6, 4.2, 0))
    h2 = cyl(p["hole"] / 2, p["thick"] + 2, (p["length"] / 2 - 6, -4.2, 0))
    try:
        return plate.difference(h1, engine="auto").difference(h2, engine="auto")
    except Exception:
        return plate


def part_tweezer(p: dict) -> trimesh.Trimesh:
    arm = box(p["length"], p["width"] * 0.38, p["thick"], (0, p["width"] * 0.28, 0))
    arm2 = box(p["length"], p["width"] * 0.38, p["thick"], (0, -p["width"] * 0.28, 0))
    hinge = box(6, p["width"], p["thick"] * 1.2, (-p["length"] / 2 + 3, 0, 0))
    return merge([arm, arm2, hinge])


def part_cassette(p: dict) -> trimesh.Trimesh:
    shell = box(p["length"], p["width"], p["height"])
    cavity = box(p["length"] - 3.2, p["width"] - 3.2, p["height"] - 2.2, (0, 0, 0.4))
    try:
        body = shell.difference(cavity, engine="auto")
    except Exception:
        body = shell
    vents = [cyl(1.1, p["width"] + 2, (i, 0, 0), axis="y") for i in (-18, -6, 6, 18)]
    for v in vents:
        try:
            body = body.difference(v, engine="auto")
        except Exception:
            break
    return body


def part_wire(diameter: float, coil_r=7.5, turns=6) -> trimesh.Trimesh:
    segs = []
    prev = None
    steps = int(turns * 32)
    for i in range(steps + 1):
        t = i / 32
        ang = t * 2 * math.pi
        pt = np.array([coil_r * math.cos(ang), coil_r * math.sin(ang), t * 1.35])
        if prev is not None:
            delta = pt - prev
            height = float(np.linalg.norm(delta))
            if height < 1e-6:
                continue
            mid = (pt + prev) / 2
            seg = trimesh.creation.cylinder(radius=diameter / 2, height=height, sections=10)
            seg.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], delta))
            seg.apply_translation(mid)
            segs.append(seg)
        prev = pt
    return merge(segs) if segs else cyl(diameter / 2, turns * 1.35, axis="z")


def part_locator(p: dict) -> trimesh.Trimesh:
    return box(p["length"], p["width"], p["thick"])


def part_wedge(p: dict) -> trimesh.Trimesh:
    return blade_body(p["length"], p["width"], p["width"] * 0.45, p["thick"], 0.4, 0.1)


def part_chest(p: dict) -> trimesh.Trimesh:
    outer = box(p["length"], p["width"], p["height"])
    inner = box(p["length"] - p["wall"] * 2, p["width"] - p["wall"] * 2, p["height"], (0, 0, p["wall"] / 2))
    try:
        return outer.difference(inner, engine="auto")
    except Exception:
        floor = box(p["length"], p["width"], p["wall"], (0, 0, -p["height"] / 2 + p["wall"] / 2))
        walls = [
            box(p["length"], p["wall"], p["height"], (0, p["width"] / 2 - p["wall"] / 2, 0)),
            box(p["length"], p["wall"], p["height"], (0, -p["width"] / 2 + p["wall"] / 2, 0)),
            box(p["wall"], p["width"], p["height"], (p["length"] / 2 - p["wall"] / 2, 0, 0)),
            box(p["wall"], p["width"], p["height"], (-p["length"] / 2 + p["wall"] / 2, 0, 0)),
        ]
        return merge([floor, *walls])


def write_togi_texture() -> None:
    """Build one shared hammered map from the TOGI plate still."""
    OUT_TEX.mkdir(parents=True, exist_ok=True)
    src = ROOT.parent / "assets" / "metal-strop.webp"
    img = Image.open(src).convert("RGB")
    w, h = img.size
    crop = img.crop((int(w * 0.18), int(h * 0.22), int(w * 0.82), int(h * 0.78))).resize((1024, 1024), Image.Resampling.LANCZOS)
    arr = np.asarray(crop).astype(np.float32)
    # Make a loosely tileable field by blending opposite edges.
    fade = np.linspace(0, 1, 80)
    for i, a in enumerate(fade):
        arr[i] = arr[i] * a + arr[-1 - i] * (1 - a)
        arr[-1 - i] = arr[-1 - i] * a + arr[i] * (1 - a)
        arr[:, i] = arr[:, i] * a + arr[:, -1 - i] * (1 - a)
        arr[:, -1 - i] = arr[:, -1 - i] * a + arr[:, i] * (1 - a)
    albedo = np.clip(arr, 0, 255).astype(np.uint8)
    Image.fromarray(albedo).save(OUT_TEX / "togi-albedo.png")
    gray = albedo.mean(axis=2)
    dx = np.gradient(gray, axis=1)
    dy = np.gradient(gray, axis=0)
    normal = np.dstack((127 - dx * 0.35, 127 + dy * 0.35, np.full_like(gray, 220)))
    normal = np.clip(normal, 0, 255).astype(np.uint8)
    Image.fromarray(normal).save(OUT_TEX / "togi-normal.png")


def main() -> None:
    OUT_STL.mkdir(parents=True, exist_ok=True)
    write_togi_texture()
    builders = {
        "01-frame": lambda: part_frame(PARAMS["frame"]),
        "02-mizu": lambda: part_mizu(PARAMS["mizu"]),
        "03-kumiko": lambda: part_kumiko(PARAMS["kumiko"]),
        "04-nata": lambda: part_nata(PARAMS["nata"]),
        "05-saya": lambda: part_saya(PARAMS["saya"]),
        "06-spike": lambda: part_spike(PARAMS["spike"]),
        "07-togi": lambda: part_togi(PARAMS["togi"]),
        "08-tweezer": lambda: part_tweezer(PARAMS["tweezer"]),
        "09-cassette": lambda: part_cassette(PARAMS["cassette"]),
        "10-s50": lambda: part_wire(PARAMS["s50"]["diameter"], 6.2, 5),
        "11-l80": lambda: part_wire(PARAMS["l80"]["diameter"], 8.4, 6),
        "12-locator": lambda: part_locator(PARAMS["locator"]),
        "13-wedge": lambda: part_wedge(PARAMS["wedge"]),
        "14-chest": lambda: part_chest(PARAMS["chest"]),
    }
    catalog = []
    for name, fn in builders.items():
        mesh = fn()
        if not isinstance(mesh, trimesh.Trimesh):
            raise SystemExit(f"{name} did not return a mesh")
        path = OUT_STL / f"{name}.stl"
        mesh.export(path)
        catalog.append(
            {
                "id": name,
                "file": f"cad/stl/{name}.stl",
                "triangles": int(len(mesh.faces)),
                "bounds_mm": [round(float(x), 2) for x in mesh.extents],
            }
        )
        print(f"wrote {path.name:20s}  faces={len(mesh.faces):5d}  extents={mesh.extents}")
    (ROOT / "catalog.json").write_text(json.dumps(catalog, indent=2))
    print("catalog", ROOT / "catalog.json")


if __name__ == "__main__":
    main()
