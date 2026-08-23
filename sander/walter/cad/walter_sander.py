"""
WALTER — 16" closed-frame drum thickness sander (FreeCAD).

Geometry is imported from walter_kernel.py (inches) and converted to mm.
Run headless:  freecadcmd walter_sander.py

Outputs (./exports):
  walter.FCStd, walter_assembly.step,
  walter_{group}.stl for each kernel group, walter_assembly.stl
"""

from __future__ import annotations

import os
import sys

import FreeCAD as App
import Mesh
import MeshPart
import Part

V = App.Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "exports")
os.makedirs(OUT, exist_ok=True)

from walter_kernel import (  # noqa: E402
    Box,
    Cyl,
    IN,
    REV,
    assembly,
    drum_rpm,
    sfm,
)


def prim_to_shape(p):
    if isinstance(p, Box):
        return Part.makeBox(p.dx * IN, p.dy * IN, p.dz * IN, V(p.x * IN, p.y * IN, p.z * IN))
    c = Part.makeCylinder(p.d * IN / 2.0, p.h * IN)
    if p.axis == "x":
        c.rotate(V(0, 0, 0), V(0, 1, 0), 90)
    elif p.axis == "y":
        c.rotate(V(0, 0, 0), V(1, 0, 0), -90)
    c.translate(V(p.x * IN, p.y * IN, p.z * IN))
    return c


def fuse(parts):
    if not parts:
        return None
    s = parts[0]
    for p in parts[1:]:
        s = s.fuse(p)
    return s


def export_compound(name, shapes):
    if not shapes:
        return None
    shape = fuse(shapes)
    doc = App.newDocument(name)
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    mesh = doc.addObject("Mesh::Feature", name + "_mesh")
    mesh.Mesh = MeshPart.meshFromShape(
        Shape=shape, LinearDeflection=0.6, AngularDeflection=0.35, Relative=False
    )
    stl = os.path.join(OUT, f"{name}.stl")
    mesh.Mesh.write(stl)
    print("wrote", stl)
    return shape


def main():
    parts = assembly(opening=1.5, explode=0, cutaway=False, discs=True)
    groups = {}
    for p in parts:
        groups.setdefault(p.group, []).append(prim_to_shape(p))

    shapes = []
    for name, plist in groups.items():
        s = export_compound(f"walter_{name}", plist)
        if s:
            shapes.append(s)

    fused = fuse(shapes) if shapes else None
    doc = App.newDocument("walter")
    if fused:
        obj = doc.addObject("Part::Feature", "walter_assembly")
        obj.Shape = fused
        step = os.path.join(OUT, "walter_assembly.step")
        fused.exportStep(step)
        print("wrote", step)
        fcstd = os.path.join(OUT, "walter.FCStd")
        doc.saveAs(fcstd)
        print("wrote", fcstd)

    print("WALTER 16-inch drum sander  Rev", REV)
    print("Capacity  16.00 in wide × 0.06–4.00 in thick")
    print(f"Drum      5.00 in Ø @ {drum_rpm:.0f} RPM  ({sfm:.0f} SFM)")
    print("Drive     1 HP TEFC 1725 × 3.00/4.75 pulleys")
    print("Feed      16×60 PVC belt, crowned 2.00 in rollers, 0–16 FPM")
    print("Envelope  22 × 36 × 22 in benchtop")


if __name__ == "__main__":
    main()
