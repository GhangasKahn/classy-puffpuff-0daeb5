"""
WALTER — 16" closed-frame drum thickness sander.

Design brief
------------
  * Capacity: 16.00" wide × 0.06–4.00" thick
  * Drum: 5.00" Ø Baltic-birch stack on 3/4" Stressproof shaft, ~1089 RPM
  * Drive: dedicated 1 HP TEFC 1725 RPM (not a table-saw parasite)
  * Feed: crowned-roller PVC conveyor + 24 V PWM, 0–16 FPM
  * Table: dual 3/4-6 Acme screws, UHMW ways, phenolic/HDPE platen
  * Idle-end flange bearing on jack screws for drum-to-table parallelism

Lineage (problems this redesign kills)
-------------------------------------
  ShopNotes #86 sat on a table saw; Ron Walters (woodgears.ca + YouTube
  W-5Sj6kBVic) added a 1/3 HP motor, flange bearings, and an oak-thread
  table — and still could not make a sanding-belt-on-PVC conveyor track.
  MDF drums cracked; Formica platens scored; there was no fine drum jack.

  This model is original engineering. It is not a copy of copyrighted
  magazine drawings.

Run headless:
  freecadcmd walter_sander.py

Outputs (./exports):
  walter.FCStd, walter_assembly.step,
  walter_ply.stl, walter_steel.stl, walter_drum.stl, walter_conveyor.stl
"""

from __future__ import annotations

import math
import os

import FreeCAD as App
import Mesh
import MeshPart
import Part

V = App.Vector

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")
os.makedirs(OUT, exist_ok=True)

IN = 25.4


def inch(n: float) -> float:
    return n * IN


# ----------------------------------------------------------------------------
# Parameters — inches are the shop language; FreeCAD works in mm
# Must mirror scripts/gen_walter_plans.py and walter_sander.scad
# ----------------------------------------------------------------------------
P = dict(
    base_x=inch(22.00),
    base_y=inch(36.00),
    base_t=inch(0.75),
    wall_t=inch(1.50),
    inner_w=inch(16.50),
    wall_h=inch(20.00),
    drum_od=inch(5.00),
    drum_face=inch(16.00),
    drum_z=inch(13.50),
    drum_y=inch(18.00),
    shaft_d=inch(0.75),
    shaft_len=inch(22.00),
    table_t=inch(0.75),
    uhmw_t=inch(0.125),
    opening=inch(1.50),
    roller_od=inch(2.00),
    roller_cd=inch(26.86),
    roller_y_in=inch(4.57),
    roller_shaft=inch(0.625),
    acme_d=inch(0.75),
    motor_od=inch(6.50),
    motor_len=inch(8.00),
    motor_y=inch(28.00),
    motor_z=inch(4.60),
    pulley_mot_d=inch(3.00),
    pulley_drm_d=inch(4.75),
    pulley_t=inch(0.75),
    hood_t=inch(0.25),
    port_d=inch(4.00),
    plate_t=inch(0.25),
)

idle_outer_x = 0.0
idle_inner_x = P["wall_t"]
drive_inner_x = P["wall_t"] + P["inner_w"]
drive_outer_x = drive_inner_x + P["wall_t"]
drum_gap = (P["inner_w"] - P["drum_face"]) / 2.0
drum_x0 = idle_inner_x + drum_gap
table_top_z = P["drum_z"] - P["drum_od"] / 2.0 - P["opening"]
roller_y_out = P["roller_y_in"] + P["roller_cd"]
platen_y0 = inch(5.50)
platen_y1 = inch(30.50)
platen_len = platen_y1 - platen_y0
acme_ys = (inch(10.0), inch(26.0))
acme_x = (idle_inner_x + drive_inner_x) / 2.0

ply, steel, drum, conveyor = [], [], [], []


def box(dx, dy, dz, x, y, z):
    return Part.makeBox(dx, dy, dz, V(x, y, z))


def cyl(d, h, x, y, z, axis="x"):
    c = Part.makeCylinder(d / 2.0, h)
    if axis == "x":
        c.rotate(V(0, 0, 0), V(0, 1, 0), 90)
        c.translate(V(x, y, z))
    elif axis == "y":
        c.rotate(V(0, 0, 0), V(1, 0, 0), -90)
        c.translate(V(x, y, z))
    else:
        c.translate(V(x, y, z))
    return c


def fuse(parts):
    if not parts:
        return None
    s = parts[0]
    for p in parts[1:]:
        s = s.fuse(p)
    return s


def make_frame():
    ply.append(box(P["base_x"], P["base_y"], P["base_t"], 0, 0, 0))
    ply.append(box(inch(1.50), P["base_y"] - inch(2), inch(1.50),
                   inch(0.75), inch(1.0), -inch(1.50)))
    ply.append(box(inch(1.50), P["base_y"] - inch(2), inch(1.50),
                   P["base_x"] - inch(2.25), inch(1.0), -inch(1.50)))
    ply.append(box(P["wall_t"], P["base_y"], P["wall_h"] - P["base_t"],
                   idle_outer_x, 0, P["base_t"]))
    ply.append(box(P["wall_t"], P["base_y"], P["wall_h"] - P["base_t"],
                   drive_inner_x, 0, P["base_t"]))
    ply.append(box(P["inner_w"], inch(1.50), inch(3.50),
                   idle_inner_x, inch(1.0), P["base_t"]))
    ply.append(box(P["inner_w"], inch(1.50), inch(3.50),
                   idle_inner_x, P["base_y"] - inch(2.5), P["base_t"]))
    steel.append(box(P["plate_t"], inch(6), inch(6),
                     idle_inner_x, P["drum_y"] - inch(3), P["drum_z"] - inch(3)))
    steel.append(box(P["plate_t"], inch(6), inch(6),
                     drive_inner_x - P["plate_t"], P["drum_y"] - inch(3),
                     P["drum_z"] - inch(3)))


def make_drum():
    drum.append(cyl(P["drum_od"], P["drum_face"], drum_x0, P["drum_y"], P["drum_z"]))
    drum.append(cyl(P["shaft_d"], P["shaft_len"], inch(-0.25), P["drum_y"], P["drum_z"]))
    steel.append(cyl(P["pulley_drm_d"], P["pulley_t"],
                     drive_outer_x + inch(0.20), P["drum_y"], P["drum_z"]))
    # flange bearings (simplified as discs)
    for x, flip in ((idle_inner_x, 1), (drive_inner_x, -1)):
        steel.append(cyl(inch(2.85), inch(0.55), x, P["drum_y"], P["drum_z"]))


def make_table():
    ply.append(box(P["inner_w"] - inch(0.24), platen_len, P["table_t"],
                   idle_inner_x + inch(0.12), platen_y0,
                   table_top_z - P["table_t"] - P["uhmw_t"]))
    conveyor.append(box(P["inner_w"] - inch(0.24), platen_len, P["uhmw_t"],
                        idle_inner_x + inch(0.12), platen_y0,
                        table_top_z - P["uhmw_t"]))
    for y in (P["roller_y_in"], roller_y_out):
        steel.append(cyl(P["roller_od"], P["inner_w"] - inch(0.24),
                         idle_inner_x + inch(0.12), y,
                         table_top_z - P["roller_od"] / 2.0))
        steel.append(cyl(P["roller_shaft"], drive_outer_x + inch(1.0),
                         idle_outer_x - inch(0.5), y,
                         table_top_z - P["roller_od"] / 2.0))
    for y in acme_ys:
        steel.append(cyl(P["acme_d"], inch(12.0), acme_x, y, inch(2.0), axis="z"))


def make_motor():
    motor_x = drive_outer_x + inch(0.25)
    steel.append(cyl(P["motor_od"], P["motor_len"],
                     motor_x, P["motor_y"], P["motor_z"]))
    steel.append(cyl(P["pulley_mot_d"], P["pulley_t"],
                     drive_outer_x + inch(0.20), P["motor_y"], P["motor_z"]))
    steel.append(box(inch(0.25), inch(8.5), inch(7.5),
                     drive_outer_x - inch(0.12), P["motor_y"] - inch(4), inch(1.0)))


def make_hood():
    ply.append(box(P["inner_w"] - inch(0.16), inch(8.4), P["hood_t"],
                   idle_inner_x + inch(0.08), P["drum_y"] - inch(4.2),
                   P["drum_z"] + inch(0.4)))
    steel.append(cyl(P["port_d"] + inch(0.15), inch(2.2),
                     acme_x, P["drum_y"] + inch(4.1), P["drum_z"] + inch(0.6),
                     axis="y"))


def export_compound(name, parts):
    if not parts:
        return None
    shape = fuse(parts)
    doc = App.newDocument(name)
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    # tessellate
    mesh = doc.addObject("Mesh::Feature", name + "_mesh")
    mesh.Mesh = MeshPart.meshFromShape(
        Shape=shape, LinearDeflection=0.6, AngularDeflection=0.35, Relative=False
    )
    stl = os.path.join(OUT, f"{name}.stl")
    mesh.Mesh.write(stl)
    print("wrote", stl)
    return shape


def main():
    make_frame()
    make_drum()
    make_table()
    make_motor()
    make_hood()

    shapes = []
    for name, parts in (
        ("walter_ply", ply),
        ("walter_steel", steel),
        ("walter_drum", drum),
        ("walter_conveyor", conveyor),
    ):
        s = export_compound(name, parts)
        if s:
            shapes.append(s)

    assembly = fuse(shapes) if shapes else None
    doc = App.newDocument("walter")
    if assembly:
        obj = doc.addObject("Part::Feature", "walter_assembly")
        obj.Shape = assembly
        step = os.path.join(OUT, "walter_assembly.step")
        assembly.exportStep(step)
        print("wrote", step)
        fcstd = os.path.join(OUT, "walter.FCStd")
        doc.saveAs(fcstd)
        print("wrote", fcstd)

    print("WALTER 16-inch drum sander")
    print("Capacity  16.00 in wide × 0.06–4.00 in thick")
    print("Drum      5.00 in Ø @ ~1089 RPM  (1427 SFM)")
    print("Drive     1 HP TEFC 1725 × 3.00/4.75 pulleys")
    print("Feed      16×60 PVC belt, crowned 2.00 in rollers, 0–16 FPM")
    print("Envelope  22 × 36 × 22 in benchtop")


if __name__ == "__main__":
    main()
