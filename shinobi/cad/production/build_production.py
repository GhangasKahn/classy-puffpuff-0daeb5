#!/usr/bin/env python3
"""SHINOBI//82 KAGE — production B-rep CAD for Zen-Wu review.

Exports STEP AP214 solids, DXF EDM profiles, viewing STL, and a zip
Luke can open without the website. Units: millimetres.

Status: proposed geometry pending workshop process review.
Not a released manufacturing revision.
"""

from __future__ import annotations

import json
import math
import zipfile
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parent
CAD = ROOT.parent
STEP = CAD / "step"
STL = CAD / "stl"
DXF = CAD / "dxf"
PROD_STEP = ROOT / "step"

TANG_L = 28.00
TANG_H = 10.00
TANG_T = 2.00
SLOT_CLEAR_H = 0.12
SLOT_CLEAR_T = 0.10
SLOT_CLEAR_L = 0.20
WEDGE_L = 16.00
WEDGE_W = 7.20
WEDGE_T0 = 2.40
WEDGE_T1 = 1.55


def _solid(wp: cq.Workplane) -> cq.Workplane:
    """Collapse a workplane to a single solid and refuse empty results."""
    obj = wp.combine() if hasattr(wp, "combine") else wp
    shape = obj.val()
    vol = float(shape.Volume())
    if vol < 5.0:
        raise RuntimeError(f"solid volume {vol:.3f} mm³ is too small — construction failed")
    return cq.Workplane(obj.plane).newObject([shape])


def _bbox(wp: cq.Workplane) -> tuple[float, float, float]:
    bb = wp.val().BoundingBox()
    return (round(bb.xlen, 3), round(bb.ylen, 3), round(bb.zlen, 3))


def export_all(workplane: cq.Workplane, stem: str, stl_tol: float = 0.12) -> dict:
    STEP.mkdir(parents=True, exist_ok=True)
    STL.mkdir(parents=True, exist_ok=True)
    PROD_STEP.mkdir(parents=True, exist_ok=True)
    wp = _solid(workplane)
    step_path = STEP / f"{stem}.step"
    stl_path = STL / f"{stem}.stl"
    cq.exporters.export(wp, str(step_path))
    (PROD_STEP / f"{stem}.step").write_bytes(step_path.read_bytes())
    shape = wp.val()
    # Planar shop faces stay few-tri; fillets tessellate. Keep both honest.
    try:
        shape.exportStl(str(stl_path), tolerance=stl_tol, angularTolerance=0.22)
    except TypeError:
        cq.exporters.export(wp, str(stl_path))
    if not stl_path.exists() or stl_path.stat().st_size < 200:
        cq.exporters.export(wp, str(stl_path))
    rec = {
        "id": stem,
        "file": f"cad/stl/{stem}.stl",
        "step": f"cad/step/{stem}.step",
        "volume_mm3": round(float(shape.Volume()), 2),
        "bounds_mm": list(_bbox(wp)),
        "triangles": _stl_tris(stl_path),
    }
    print(
        f"  {stem:16s}  STEP {step_path.stat().st_size/1024:6.1f} KB  "
        f"STL {stl_path.stat().st_size/1024:6.1f} KB  "
        f"V {rec['volume_mm3']:8.1f}  {rec['bounds_mm']}"
    )
    return rec


def _stl_tris(path: Path) -> int:
    data = path.read_bytes()
    if data[:5] == b"solid":
        return data.lower().count(b"facet")
    return int.from_bytes(data[80:84], "little")


def export_dxf(wp: cq.Workplane, stem: str) -> None:
    DXF.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(wp, str(DXF / f"{stem}.dxf"))


def _bevel_cutter(length: float, thick: float, angle_deg: float, from_top: bool, z_edge: float) -> cq.Workplane:
    """Triangular prism along +X that leaves a flat grind to the edge line."""
    ang = math.radians(angle_deg)
    if from_top:
        rise = thick - z_edge
        land = rise / math.tan(ang) if ang else rise
        pts = [(0.0, thick), (land, thick), (0.0, z_edge)]
    else:
        rise = z_edge
        land = rise / math.tan(ang) if ang else rise
        pts = [(0.0, 0.0), (land, 0.0), (0.0, z_edge)]
    return (
        cq.Workplane("YZ")
        .polyline(pts)
        .close()
        .extrude(length + 8.0)
        .translate((-4.0, 0, 0))
    )


def _distal_cutter(x0: float, x1: float, z0: float, z1: float, yspan: float) -> cq.Workplane:
    """Removes the square tip so thickness falls from z0 to z1 along X."""
    return (
        cq.Workplane("XZ")
        .polyline([(x0, z0), (x1 + 2.0, z0), (x1 + 2.0, z1), (x0, z0)])
        .close()
        .extrude(yspan + 8.0)
        .translate((0, -(yspan / 2 + 4.0), 0))
    )


def _tang(z_center: float, y_center: float) -> cq.Workplane:
    """Shoulder at X=0, tang runs −X. Shared kusabi contract."""
    return (
        cq.Workplane("XY")
        .center(-TANG_L / 2, y_center)
        .rect(TANG_L, TANG_H)
        .extrude(TANG_T)
        .translate((0, 0, z_center - TANG_T / 2))
    )


def frame() -> cq.Workplane:
    """Ti-6Al-4V monocoque. Two rinse apertures, kusabi slot, radiused eye."""
    L, H, T = 94.00, 16.20, 4.60
    body = cq.Workplane("XY").center(L / 2, 0).rect(L, H).extrude(T)
    body = body.edges("|Z").fillet(2.20)
    body = (
        body.faces(">Z")
        .workplane()
        .center(-L / 2 + 28.0, 0.15)
        .slot2D(22.0, 6.40, 0)
        .center(28.0, -0.30)
        .slot2D(18.0, 6.10, 0)
        .cutThruAll()
    )
    body = (
        body.faces("<X")
        .workplane(centerOption="CenterOfBoundBox")
        .rect(TANG_H + SLOT_CLEAR_H, TANG_T + SLOT_CLEAR_T)
        .cutBlind(-(TANG_L + SLOT_CLEAR_L))
    )
    body = (
        body.faces(">Y")
        .workplane(centerOption="CenterOfBoundBox")
        .center(-L / 2 + 10.0, 0)
        .rect(WEDGE_L, WEDGE_T0)
        .cutBlind(-6.4)
    )
    body = body.faces(">Z").workplane().center(L / 2 - 8.2, 0).hole(4.40)
    try:
        body = body.edges("%Circle").fillet(0.30)
    except Exception:
        pass
    return body


def mizu() -> cq.Workplane:
    """MIZU-82: 82 mm low-belly, distal taper, 60/40 hamaguri as two flats."""
    pts = [
        (0.0, 0.00),
        (0.0, 15.20),
        (21.0, 14.60),
        (48.0, 12.10),
        (70.0, 8.40),
        (82.0, 3.10),
        (82.0, 1.10),
        (70.0, 0.85),
        (40.0, 0.55),
        (18.0, 0.25),
        (0.0, 0.00),
    ]
    thick = 1.55
    blade = cq.Workplane("XY").polyline(pts).close().extrude(thick)
    blade = blade.cut(_distal_cutter(48.0, 82.0, thick, 0.60, 16.0))
    z_edge = 0.40 * 0.60  # 40% from ura at the thinned tip class
    z_edge = 0.62
    blade = blade.cut(_bevel_cutter(86.0, thick, 15.0, from_top=True, z_edge=z_edge))
    blade = blade.cut(_bevel_cutter(86.0, thick, 12.0, from_top=False, z_edge=z_edge))
    tang = _tang(z_center=thick / 2, y_center=15.20 - TANG_H / 2 - 0.30)
    return blade.union(tang)


def kumiko() -> cq.Workplane:
    """KUMIKO-42: dead-flat ura, 15° single flat bevel."""
    pts = [
        (0.0, 0.00),
        (0.0, 12.40),
        (18.0, 12.10),
        (34.0, 9.20),
        (42.0, 4.60),
        (42.0, 1.80),
        (28.0, 0.35),
        (0.0, 0.00),
    ]
    thick = 2.00
    blade = cq.Workplane("XY").polyline(pts).close().extrude(thick)
    blade = blade.cut(_bevel_cutter(46.0, thick, 15.0, from_top=True, z_edge=0.0))
    tang = _tang(z_center=thick / 2, y_center=12.40 - TANG_H / 2 - 0.30)
    return blade.union(tang)


def nata() -> cq.Workplane:
    """NATA-60: 24° single bevel, chisel-style. No baton face."""
    pts = [
        (0.0, 0.00),
        (0.0, 17.80),
        (22.0, 17.20),
        (44.0, 14.00),
        (60.0, 8.20),
        (60.0, 2.40),
        (36.0, 0.50),
        (0.0, 0.00),
    ]
    thick = 2.40
    blade = cq.Workplane("XY").polyline(pts).close().extrude(thick)
    blade = blade.cut(_bevel_cutter(64.0, thick, 24.0, from_top=True, z_edge=0.0))
    tang = _tang(z_center=thick / 2, y_center=17.80 - TANG_H / 2 - 0.30)
    return blade.union(tang)


def wedge() -> cq.Workplane:
    """Kusabi wedge — 2° close, drives from the spine."""
    return (
        cq.Workplane("XY")
        .moveTo(0, 0)
        .lineTo(WEDGE_L, 0)
        .lineTo(WEDGE_L, WEDGE_T1)
        .lineTo(0, WEDGE_T0)
        .close()
        .extrude(WEDGE_W)
        .edges("|Z")
        .fillet(0.25)
    )


def saya() -> cq.Workplane:
    """Kiri/honoki slip saya, 1.8 mm walls, drain, cord eye."""
    L, W, H, wall = 92.00, 20.00, 9.20, 1.80
    body = cq.Workplane("XY").box(L, W, H)
    body = body.edges("|Z").fillet(1.20)
    cavity = cq.Workplane("XY").box(L - wall * 2 + 4, 16.40, 5.40).translate((4, 0, 0.15))
    body = body.cut(cavity)
    body = body.faces("<Y").workplane(centerOption="CenterOfBoundBox").center(L / 2 - 10, 0).hole(3.20)
    body = body.faces(">X").workplane(centerOption="CenterOfBoundBox").hole(3.00)
    return body


def spike() -> cq.Workplane:
    """KAGE-HARI: 34 mm point, 18 mm tang, cap, 3.2 mm lock pin."""
    point = cq.Workplane("YZ").circle(1.70).workplane(offset=34.00).circle(0.18).loft(combine=True)
    tang = cq.Workplane("YZ").circle(1.55).extrude(-18.00)
    cap = cq.Workplane("YZ").workplane(offset=-18.00).circle(4.10).extrude(-3.20)
    pin = cq.Workplane("XZ").center(-10.0, 0).circle(1.60).extrude(8.00)
    return point.union(tang).union(cap).union(pin)


def togi() -> cq.Workplane:
    """TOGI plate 52 × 18 × 2.8, two 3.2 holes, T-lock slot, 0.15 chamfer."""
    plate = cq.Workplane("XY").box(52.00, 18.00, 2.80)
    plate = plate.edges("|Z").fillet(0.80)
    plate = plate.faces(">Z").workplane().pushPoints([(20.0, 4.20), (20.0, -4.20)]).hole(3.20)
    plate = (
        plate.faces(">Y")
        .workplane(centerOption="CenterOfBoundBox")
        .center(-16.0, 0)
        .rect(8.00, 1.70)
        .cutBlind(-6.00)
    )
    try:
        plate = plate.edges("%Circle").chamfer(0.15)
    except Exception:
        pass
    return plate


def tweezer() -> cq.Workplane:
    """Beta-titanium pinbone tweezer, 46 mm."""
    arm = (
        cq.Workplane("XY")
        .moveTo(0, 0.55)
        .lineTo(46, 0.15)
        .lineTo(46, 0.55)
        .lineTo(0, 2.55)
        .close()
        .extrude(1.10)
    )
    other = (
        cq.Workplane("XY")
        .moveTo(0, -0.55)
        .lineTo(46, -0.15)
        .lineTo(46, -0.55)
        .lineTo(0, -2.55)
        .close()
        .extrude(1.10)
    )
    hinge = cq.Workplane("XY").center(2.4, 0).rect(6.4, 6.4).extrude(1.20)
    return arm.union(other).union(hinge)


def cassette() -> cq.Workplane:
    """64 mm vented SHINKEI cassette. Open channels, no sealed cavity."""
    body = cq.Workplane("XY").box(64.00, 16.00, 8.20)
    body = body.edges("|Z").fillet(1.00)
    body = body.faces(">Z").workplane().rect(56.00, 10.00).cutBlind(-5.40)
    body = (
        body.faces(">Y")
        .workplane(centerOption="CenterOfBoundBox")
        .pushPoints([(-18.0, 0), (-6.0, 0), (6.0, 0), (18.0, 0)])
        .circle(1.10)
        .cutThruAll()
    )
    return body


def locator() -> cq.Workplane:
    plate = cq.Workplane("XY").box(22.00, 8.00, 0.70)
    plate = plate.edges("|Z").fillet(0.80)
    plate = plate.faces(">Z").workplane().hole(2.20)
    return plate


def chest() -> cq.Workplane:
    """Kiri studio chest, 4 mm walls, open top."""
    L, W, H, wall = 168.00, 78.00, 22.00, 4.00
    outer = cq.Workplane("XY").box(L, W, H)
    outer = outer.edges("|Z").fillet(3.00)
    inner = cq.Workplane("XY").box(L - wall * 2, W - wall * 2, H).translate((0, 0, wall))
    return outer.cut(inner)


def wire_coil(d: float, coil_r: float, turns: int, pitch: float) -> cq.Workplane:
    """Display coil. Production wires are straight Nitinol stock — see BOM."""
    steps = turns * 24
    pts = [
        cq.Vector(
            coil_r * math.cos(i / 24 * 2 * math.pi),
            coil_r * math.sin(i / 24 * 2 * math.pi),
            i / 24 * pitch,
        )
        for i in range(steps + 1)
    ]
    spine = cq.Workplane("XY").spline(pts)
    return cq.Workplane("XZ").center(coil_r, 0).circle(d / 2).sweep(spine, isFrenet=True)


def wire_stock(d: float, length: float) -> cq.Workplane:
    """Straight production stock. Viewer uses a short sample; BOM has full length."""
    sample = min(length, 80.0)
    return cq.Workplane("XY").circle(d / 2).extrude(sample)


def profiles() -> None:
    """EDM / waterjet profiles — XY, millimetres, 1:1, tang included."""
    export_dxf(cq.Workplane("XY").rect(94, 16.20), "frame-outline")
    mizu_tang_y = 15.20 - TANG_H / 2 - 0.30
    export_dxf(
        cq.Workplane("XY")
        .polyline(
            [
                (-TANG_L, mizu_tang_y - TANG_H / 2),
                (0, mizu_tang_y - TANG_H / 2),
                (0, 0),
                (18, 0.25),
                (40, 0.55),
                (70, 0.85),
                (82, 1.10),
                (82, 3.10),
                (70, 8.40),
                (48, 12.10),
                (21, 14.60),
                (0, 15.20),
                (0, mizu_tang_y + TANG_H / 2),
                (-TANG_L, mizu_tang_y + TANG_H / 2),
            ]
        )
        .close(),
        "mizu-profile",
    )
    export_dxf(
        cq.Workplane("XY").polyline(
            [(0, 0), (0, 12.40), (18, 12.10), (34, 9.20), (42, 4.60), (42, 1.80), (28, 0.35), (0, 0)]
        ).close(),
        "kumiko-profile",
    )
    export_dxf(
        cq.Workplane("XY").polyline(
            [(0, 0), (0, 17.80), (22, 17.20), (44, 14.00), (60, 8.20), (60, 2.40), (36, 0.50), (0, 0)]
        ).close(),
        "nata-profile",
    )
    export_dxf(cq.Workplane("XY").rect(TANG_L, TANG_H), "tang-kusabi")
    export_dxf(cq.Workplane("XY").rect(52, 18), "togi-outline")
    export_dxf(
        cq.Workplane("XY")
        .moveTo(0, 0)
        .lineTo(WEDGE_L, 0)
        .lineTo(WEDGE_L, WEDGE_T1)
        .lineTo(0, WEDGE_T0)
        .close(),
        "wedge-profile",
    )


def write_docs() -> None:
    transmittal = """SHINOBI//82 KAGE — CAD TRANSMITTAL FOR ZEN-WU REVIEW
=====================================================
To:      Luke Lyu / Zen-Wu Toolworks  <luke@zenwutoolworks.com>
From:    SHINOBI//82 KAGE proposal
Date:    15 August 2026
Status:  Proposed engineering package. Not a released manufacturing revision.
Units:   millimetres. Coordinates: right-hand, X along length.
Origin:  blades — shoulder at X=0, edge at Y=0, ura at Z=0.
         frame  — nose at X=0, length +X.

1. WHAT THIS IS
   B-rep solids in STEP AP214 (ISO 10303), EDM/waterjet profiles in DXF,
   and STL tessellations for viewing only. Built so the Wuhan shop can
   open the parts in the same class of CAD used for Zen-Wu tools
   (STEP in, EDM profile out). The website viewer is not the master.

   Earlier site meshes were trimesh massing studies (boxy, 12–24 faces).
   These files replace them.

2. MATING CONTRACT — KUSABI
   All blades share one tang:
     tang length  28.00
     tang height  10.00
     tang thick    2.00
   Frame slot: +0.12 H, +0.10 T, +0.20 L clearance.
   Wedge: 16.00 long, 2.40 → 1.55 thick, 7.20 wide, drives from the spine.
   First article: blue the tang, seat, check rock at the choil.

3. MATERIALS (proposed)
   Frame, wedge, cassette, tweezer, TOGI substrate : Ti-6Al-4V
   MIZU-82 edge                                  : MagnaMax candidate, 62.5–63.0 HRC pending coupon
   KUMIKO-42 edge                                : ZW-V1 or MagnaCut, workshop choice
   NATA-60 edge                                  : MagnaCut candidate
   Spike                                         : hardened stainless or tool steel, 58+ HRC, not the knife steel
   Saya                                          : kiri or honoki, 1.8 wall
   Wires                                         : Nitinol, straight stock 0.8×500 and 1.2×800
   Tether                                        : Dyneema SK99, radiused 4.40 eye only

4. FINISH
   Frame: DLC or equivalent charcoal. Hammered / TOGI texture on contact rails only.
   Edges: 800–1000 diamond, 1 μm deburr on MIZU. KUMIKO and NATA as flat bevels.
   Food-contact: no adhesive, no trapped cavity, rinse-through apertures.

5. TOLERANCES (proposed first-article)
   Tang / slot     ±0.05
   Reference ura   0.02 flatness on KUMIKO lands
   Blade warp      0.15 max
   Aperture webs   3.60 min
   Lanyard eye     4.40 +0.10 / 0, full radius, no burr

6. WHAT IS NOT IN THIS PACKAGE
   Heat-treat recipe (Zen-Wu process).
   FEA of the skeleton (required before a 50-unit pilot).
   Left-hand mirrors (mirror the blade, ura, and lamination — do not resharpen opposite).
   Weighed prototypes.
   A claim that these files are ready to cut metal without workshop review.

7. FILES
   step/*.step     solids (master) — open these in CAD
   dxf/*.dxf       EDM / waterjet profiles, 1:1 mm
   BOM.csv         line items
   parameters.json millimetre ledger
   STL tessellations stay on the website for viewing. They are not the master.
"""
    bom = """line,id,name,qty,material,blank_or_stock,notes
01,01-frame,Handle frame,1,Ti-6Al-4V,94 x 16.2 x 4.6 plate,Rinse slots; kusabi slot; Ø4.40 eye
02,02-mizu,MIZU-82,1,MagnaMax candidate,82 blade + 28 tang x 15.2 x 1.55,60/40 hamaguri as two flats; distal to 0.60
03,03-kumiko,KUMIKO-42,1,ZW-V1 or MagnaCut,42 + 28 tang x 12.4 x 2.00,Dead-flat ura; 15° single bevel
04,04-nata,NATA-60,1,MagnaCut candidate,60 + 28 tang x 17.8 x 2.40,24° chisel; no baton
05,05-saya,Slip saya,1,kiri or honoki,92 x 20 x 9.2,1.8 wall; drain; cord eye
06,06-spike,KAGE-HARI,1,hardened SS / tool steel,Ø3.4 x 55,58+ HRC; not the knife steel
07,07-togi,TOGI plate,1,Ti-6Al-4V,52 x 18 x 2.8,Two Ø3.2; T-lock
08,08-tweezer,Pinbone tweezer,1,beta titanium,46 x 6.4 x 1.1,Food-contact rinse
09,09-cassette,SHINKEI cassette,1,Ti-6Al-4V,64 x 16 x 8.2,Open vents; no sealed cavity
10,10-s50,S-50 wire,1,Nitinol,Ø0.80 x 500 straight,Coil on the site is display only
11,11-l80,L-80 wire,1,Nitinol,Ø1.20 x 800 straight,Coil on the site is display only
12,12-locator,Sleeve locator,1,cloth / polymer,22 x 8 x 0.7,Findable pale mark
13,13-wedge,Kusabi wedge,1,Ti-6Al-4V,16 x 7.2 x 2.40→1.55,2° close from the spine
14,14-chest,Studio chest,1,kiri,168 x 78 x 22 x 4 wall,Open top; miter-ready
"""
    readme = """SHINOBI//82 KAGE — files for Luke / Zen-Wu
==========================================
Open TRANSMITTAL.txt first. Then step/01-frame.step in your CAD.

Master: STEP. STL is for the website viewer only.
DXF profiles are 1:1 millimetres for EDM / waterjet conversation.

This is a proposed collaboration. It is not an announced Zen-Wu product.
"""
    (ROOT / "TRANSMITTAL.txt").write_text(transmittal)
    (CAD / "TRANSMITTAL.txt").write_text(transmittal)
    (ROOT / "BOM.csv").write_text(bom)
    (CAD / "BOM.csv").write_text(bom)
    (ROOT / "README.txt").write_text(readme)
    (CAD / "README.txt").write_text(readme)


def write_zip() -> Path:
    zip_path = CAD / "SHINOBI82-KAGE-Zen-Wu-review.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in [
            "TRANSMITTAL.txt",
            "README.txt",
            "BOM.csv",
            "parameters.json",
        ]:
            zf.write(CAD / rel, rel)
        skip = {"10-s50.step", "11-l80.step"}  # display coils; production is straight stock
        for folder in ("step", "dxf"):
            for path in sorted((CAD / folder).glob("*")):
                if path.name in skip:
                    continue
                zf.write(path, f"{folder}/{path.name}")
    print(f"  zip {zip_path.name}  {zip_path.stat().st_size/1024:6.1f} KB")
    return zip_path


def kit_assembly(parts: dict[str, cq.Workplane]) -> None:
    """Parts in a row so the shop can inspect every solid in one STEP."""
    assy = cq.Assembly(name="SHINOBI82-KAGE-kit")
    x = 0.0
    order = [
        "01-frame",
        "02-mizu",
        "03-kumiko",
        "04-nata",
        "05-saya",
        "06-spike",
        "07-togi",
        "08-tweezer",
        "09-cassette",
        "12-locator",
        "13-wedge",
        "14-chest",
    ]
    for name in order:
        if name not in parts:
            continue
        wp = parts[name]
        bb = wp.val().BoundingBox()
        assy.add(wp, name=name, loc=cq.Location(cq.Vector(x - bb.xmin, -bb.ymin, -bb.zmin)))
        x += bb.xlen + 12.0
    out = STEP / "00-kit-layout.step"
    assy.save(str(out))
    (PROD_STEP / "00-kit-layout.step").write_bytes(out.read_bytes())
    print(f"  00-kit-layout     STEP {out.stat().st_size/1024:6.1f} KB")


def main() -> None:
    print("Building production solids…")
    catalog = []
    built: dict[str, cq.Workplane] = {}

    jobs = [
        ("01-frame", frame),
        ("02-mizu", mizu),
        ("03-kumiko", kumiko),
        ("04-nata", nata),
        ("05-saya", saya),
        ("06-spike", spike),
        ("07-togi", togi),
        ("08-tweezer", tweezer),
        ("09-cassette", cassette),
        ("12-locator", locator),
        ("13-wedge", wedge),
        ("14-chest", chest),
    ]
    for stem, fn in jobs:
        wp = fn()
        built[stem] = wp
        catalog.append(export_all(wp, stem))

    for stem, args in (
        ("10-s50", (0.80, 6.20, 5, 1.35)),
        ("11-l80", (1.20, 8.40, 6, 1.45)),
    ):
        try:
            wp = wire_coil(*args)
            built[stem] = wp
            rec = export_all(wp, stem, stl_tol=0.35)
            # Keep the lighter display-coil STL already on the site.
            rec["note"] = "Viewer STL is a display coil. Production stock is straight Nitinol — see BOM."
            catalog.append(rec)
        except Exception as exc:
            print(f"  {stem} coil failed ({exc}); exporting straight stock sample")
            d = args[0]
            wp = wire_stock(d, 80.0)
            built[stem] = wp
            catalog.append(export_all(wp, stem))

    profiles()
    try:
        kit_assembly(built)
    except Exception as exc:
        print("  assembly skipped:", exc)
    write_docs()
    write_zip()
    (CAD / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n")
    print("done", CAD)


if __name__ == "__main__":
    main()
