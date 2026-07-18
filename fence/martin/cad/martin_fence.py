"""
MARTIN — Prairie School removable fence for Buffalo NY.

Design brief
------------
  * Overall envelope: 143" long × 65" high (owner site opening)
  * Style: Darwin Martin / Frank Lloyd Wright Prairie horizontals
    + Japanese hand-cut joinery (no nails / screws in the timber)
  * Lumber: hardware-store dimensional stock (prefer 2×6 / 2×8 / 4×6)
  * Finish: exterior paint — owner gray (mask all wedge / hinge faces)
  * Removable for winter: lift-out timber modules + tip-out socket piers
  * Leveling pad corrects driveway → garden drop-off
  * Gate: 36" clear, wooden pintle hinges, sliding bar latch
    (house-concrete receiver OR latch-post receiver)

Climate targets (Buffalo / Erie County NY)
-----------------------------------------
  * Socket pier mass + wedge lock resists 115 mph ultimate wind (ASCE 7)
  * Timber held clear of splash / snowpack on raised pad
  * All end grain sealed; rain-screen gaps in vertical boards
  * No trapped water in joinery (nuki drains; wedges removable)

Run headless:
  freecadcmd martin_fence.py

Outputs (./exports):
  martin.FCStd, martin_assembly.step,
  martin_timber.stl, martin_concrete.stl, martin_gravel.stl, martin_sleeve.stl
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

IN = 25.4  # mm


def inch(n: float) -> float:
    return n * IN


# ----------------------------------------------------------------------------
# Parameters — inches are the owner language; FreeCAD works in mm
# ----------------------------------------------------------------------------
P = dict(
    # envelope
    length=inch(143.0),
    height=inch(65.0),

    # 4×6 posts (actual 3.5 × 5.5): face along run = 3.5, depth = 5.5
    post_x=inch(3.5),
    post_y=inch(5.5),
    post_tenon_x=inch(2.5),
    post_tenon_y=inch(4.5),
    post_tenon_h=inch(12.0),

    # gate
    gate_clear=inch(36.0),
    gate_gap=inch(0.5),          # each side of leaf
    leaf_t=inch(1.5),            # 2× stock leaf thickness
    stile_w=inch(3.5),           # 2×4 / ripped 2×6 stile face
    rail_gate_h=inch(5.5),       # 2×6 gate rails
    brace_w=inch(3.5),

    # Prairie rails — 2×8 on edge (visible 7.25" bands)
    rail_t=inch(1.5),
    rail_h=inch(7.25),
    # rail centerlines above pad (AFF)
    rail_z_cl=(inch(10.0), inch(28.0), inch(46.0)),
    # cap — 2×8 flat on top of posts
    cap_t=inch(1.5),
    cap_w=inch(7.25),

    # privacy boards — 1×6 (matches existing ¾" fence thickness)
    board_t=inch(0.75),
    board_w=inch(5.5),
    board_gap=inch(0.25),

    # leveling pad + socket piers (removable piers sit on pad)
    pad_overhang=inch(6.0),
    pad_width=inch(28.0),
    pad_thick=inch(6.0),
    # assume driveway→garden drop of 5"; pad top is level — thick end absorbs it
    drop_off=inch(5.0),
    pier_xy=inch(14.0),
    pier_h=inch(18.0),
    sleeve_wall=inch(0.25),
    gravel_h=inch(6.0),
    gravel_pad_extra=inch(4.0),

    # latch bar into house concrete (optional receiver shown at x=0)
    latch_bar_x=inch(18.0),
    latch_bar_y=inch(1.5),
    latch_bar_z=inch(3.5),
    house_receiver_depth=inch(4.0),
)

timber, concrete, gravel, sleeve = [], [], [], []


def box(dx, dy, dz, x, y, z):
    return Part.makeBox(dx, dy, dz, V(x, y, z))


def cbox(dx, dy, dz, cx, cy, z):
    return Part.makeBox(dx, dy, dz, V(cx - dx / 2.0, cy - dy / 2.0, z))


# ---- post layout (centers along +x) -----------------------------------------
# Outer faces at 0 and L. Gate clear between P0 and P1.
# Two equal privacy bays between P1 and P3 with mid-post P2.
fx = P["post_x"]
L = P["length"]
gate = P["gate_clear"]

P0 = fx / 2.0
P1 = fx + gate + fx / 2.0
# remaining clear between P1 right face and P3 left face
p1_right = P1 + fx / 2.0
p3_left = L - fx
clear_span = p3_left - p1_right
# mid post consumes fx of that span; two equal clears
bay_clear = (clear_span - fx) / 2.0
P2 = p1_right + bay_clear + fx / 2.0
P3 = L - fx / 2.0
POSTS = (P0, P1, P2, P3)

H = P["height"]
pad_z0 = 0.0  # pad top = finished reference grade for timber


def post_blank(cx, with_tenon=True):
    """Post from pad top up to under-cap, plus optional foot tenon into sleeve."""
    body = cbox(P["post_x"], P["post_y"], H - P["cap_t"], cx, 0, pad_z0)
    if not with_tenon:
        return body
    tenon = cbox(
        P["post_tenon_x"], P["post_tenon_y"], P["post_tenon_h"],
        cx, 0, pad_z0 - P["post_tenon_h"],
    )
    return body.fuse(tenon)


def nuki_mortises(post_shape, cx, rail_zs, through=True):
    """Cut through-mortises for Prairie rails (nuki seats)."""
    cut = post_shape
    for zc in rail_zs:
        mz = zc - P["rail_h"] / 2.0
        # through in X for nuki; depth leaves cheeks on Y
        pocket = cbox(
            P["post_x"] + 2 if through else P["post_x"] * 0.55,
            P["rail_t"] + 1.0,
            P["rail_h"] + 1.0,
            cx, 0, mz,
        )
        cut = cut.cut(pocket)
    return cut


def wedge_slots(post_shape, cx, rail_zs):
    """Diagonal wedge kerfs through post cheeks (locking peg seats)."""
    cut = post_shape
    for zc in rail_zs:
        # small rectangular wedge slot beside rail, through Y
        slot = cbox(
            inch(0.75), P["post_y"] + 2, inch(1.25),
            cx + P["post_x"] * 0.28, 0, zc - inch(0.15),
        )
        cut = cut.cut(slot)
    return cut


def make_posts():
    rail_zs = P["rail_z_cl"]
    for i, cx in enumerate(POSTS):
        p = post_blank(cx, with_tenon=True)
        # all posts get rail mortises; P0 only gets latch-side short rails / none through
        if i == 0:
            # latch post: mortises for gate latch bar + optional short return rail stubs
            p = nuki_mortises(p, cx, rail_zs, through=True)
        else:
            p = nuki_mortises(p, cx, rail_zs, through=True)
            p = wedge_slots(p, cx, rail_zs)
        timber.append(p)


def make_privacy_rails():
    """Continuous 2×8 nuki rails through P1–P3 (privacy run)."""
    x0 = P1 - fx / 2.0 - inch(0.5)  # slight reveal past hinge post outer
    x1 = P3 + fx / 2.0 + inch(0.5)
    length = x1 - x0
    for zc in P["rail_z_cl"]:
        z = zc - P["rail_h"] / 2.0
        rail = box(length, P["rail_t"], P["rail_h"], x0, -P["rail_t"] / 2.0, z)
        timber.append(rail)


def make_cap():
    """2×8 flat cap: latch stub over P0 + continuous privacy cap P1–P3.
    Scarf joint (kama-tsugi) implied at P2 — modeled as continuous for clarity."""
    # gate header / latch cap over P0 (does not bridge gate — leaf has its own top)
    c0 = cbox(fx + inch(1.0), P["cap_w"], P["cap_t"], P0, 0, H - P["cap_t"])
    timber.append(c0)
    x0 = P1 - fx / 2.0 - inch(0.75)
    x1 = P3 + fx / 2.0 + inch(0.75)
    cap = box(x1 - x0, P["cap_w"], P["cap_t"], x0, -P["cap_w"] / 2.0, H - P["cap_t"])
    timber.append(cap)


def board_span_z():
    """Vertical board extents between rail bands (three courses)."""
    zs = P["rail_z_cl"]
    rh = P["rail_h"]
    courses = []
    # below first rail → above pad with clearance
    courses.append((pad_z0 + inch(1.5), zs[0] - rh / 2.0 - inch(0.125)))
    # between rails
    for a, b in zip(zs, zs[1:]):
        courses.append((a + rh / 2.0 + inch(0.125), b - rh / 2.0 - inch(0.125)))
    # above top rail → under cap
    courses.append((zs[-1] + rh / 2.0 + inch(0.125), H - P["cap_t"] - inch(0.125)))
    return courses


def fill_bay_boards(x_left_inner, x_right_inner):
    """1×6 vertical boards floating in rail grooves (no fasteners)."""
    clear = x_right_inner - x_left_inner
    pitch = P["board_w"] + P["board_gap"]
    n = max(1, int(math.floor((clear + P["board_gap"]) / pitch)))
    # center the group
    used = n * P["board_w"] + (n - 1) * P["board_gap"]
    x_start = x_left_inner + (clear - used) / 2.0
    # boards sit just inside post depth, garden face
    y = -P["post_y"] / 2.0 + inch(0.5)
    for course_z0, course_z1 in board_span_z():
        bh = course_z1 - course_z0
        if bh < inch(1.0):
            continue
        for i in range(n):
            x = x_start + i * pitch
            timber.append(box(P["board_w"], P["board_t"], bh, x, y, course_z0))


def make_boards():
    # bay P1–P2
    fill_bay_boards(P1 + fx / 2.0, P2 - fx / 2.0)
    # bay P2–P3
    fill_bay_boards(P2 + fx / 2.0, P3 - fx / 2.0)


def make_gate_leaf():
    """Ledged & braced gate leaf — drawbored M&T (geometry), wooden pintles."""
    gap = P["gate_gap"]
    x0 = fx + gap
    x1 = fx + gate - gap
    w = x1 - x0
    t = P["leaf_t"]
    # leaf centered on fence centerline in Y, slightly toward garden for swing
    y0 = -t / 2.0
    h = H - P["cap_t"] - inch(0.5)
    z0 = pad_z0 + inch(1.0)

    stile = P["stile_w"]
    # stiles
    timber.append(box(stile, t, h, x0, y0, z0))
    timber.append(box(stile, t, h, x1 - stile, y0, z0))
    # three gate rails aligning with Prairie bands
    for zc in P["rail_z_cl"]:
        rz = zc - P["rail_gate_h"] / 2.0
        timber.append(
            box(w - 2 * stile, t, P["rail_gate_h"], x0 + stile, y0, rz)
        )
    # top rail under cap line
    timber.append(
        box(w - 2 * stile, t, inch(3.5), x0 + stile, y0, z0 + h - inch(3.5))
    )
    # bottom rail
    timber.append(
        box(w - 2 * stile, t, inch(3.5), x0 + stile, y0, z0)
    )
    # diagonal brace (half-lap implied)
    brace_len = math.hypot(w - 2 * stile, h - inch(10))
    brace = box(brace_len, t, P["brace_w"], 0, y0, 0)
    # rotate in XZ about origin then place
    brace.rotate(V(0, 0, 0), V(0, 1, 0), -math.degrees(math.atan2(h - inch(10), w - 2 * stile)))
    brace.translate(V(x0 + stile, 0, z0 + inch(5)))
    timber.append(brace)

    # vertical infill boards on gate (same 1×6 language)
    inner_w = w - 2 * stile
    pitch = P["board_w"] + P["board_gap"]
    n = max(1, int(math.floor((inner_w + P["board_gap"]) / pitch)))
    used = n * P["board_w"] + (n - 1) * P["board_gap"]
    xs = x0 + stile + (inner_w - used) / 2.0
    yb = y0 + t * 0.15
    for i in range(n):
        timber.append(
            box(P["board_w"], P["board_t"], h - inch(8), xs + i * pitch, yb, z0 + inch(4))
        )

    # sliding latch bar (wood) — extends toward house into receiver
    bar = box(
        P["latch_bar_x"], P["latch_bar_y"], P["latch_bar_z"],
        x0 - P["latch_bar_x"] + inch(2.0),
        -P["latch_bar_y"] / 2.0,
        P["rail_z_cl"][1] - P["latch_bar_z"] / 2.0,
    )
    timber.append(bar)


def make_pad_and_piers():
    """Leveling pad (corrects drop-off) + four tip-out socket piers + sleeves."""
    pad_len = L + 2 * P["pad_overhang"]
    pad_w = P["pad_width"]
    # wedge / stepped pad: model as rectangular with thick end under garden
    # top at z=0; bottom slopes from -pad_thick (driveway) to -(pad_thick+drop)
    # FreeCAD: approximate with flat 6" pad + note; plus thickened pier pockets
    pad = cbox(pad_len, pad_w, P["pad_thick"], L / 2.0, 0, -P["pad_thick"])
    concrete.append(pad)

    # drop-off makeup curb on garden side (fills the 5" grade break)
    makeup = cbox(
        pad_len, pad_w * 0.45, P["drop_off"],
        L / 2.0, pad_w * 0.28, -P["pad_thick"] - P["drop_off"],
    )
    concrete.append(makeup)

    gravel.append(
        cbox(
            pad_len + 2 * P["gravel_pad_extra"],
            pad_w + 2 * P["gravel_pad_extra"],
            P["gravel_h"],
            L / 2.0, 0,
            -P["pad_thick"] - P["drop_off"] - P["gravel_h"],
        )
    )

    for cx in POSTS:
        pier = cbox(P["pier_xy"], P["pier_xy"], P["pier_h"], cx, 0, -P["pier_h"])
        # hollow for sleeve — cut pocket
        pocket = cbox(
            P["post_tenon_x"] + inch(0.5),
            P["post_tenon_y"] + inch(0.5),
            P["post_tenon_h"] + inch(2.0),
            cx, 0, -P["post_tenon_h"] - inch(1.0),
        )
        pier = pier.cut(pocket)
        concrete.append(pier)

        # sleeve liner (PVC / galvanized) — drain hole at bottom implied
        sw = P["sleeve_wall"]
        outer = cbox(
            P["post_tenon_x"] + inch(0.5) + 2 * sw,
            P["post_tenon_y"] + inch(0.5) + 2 * sw,
            P["post_tenon_h"] + inch(1.5),
            cx, 0, -P["post_tenon_h"] - inch(0.5),
        )
        inner = cbox(
            P["post_tenon_x"] + inch(0.5),
            P["post_tenon_y"] + inch(0.5),
            P["post_tenon_h"] + inch(2.0),
            cx, 0, -P["post_tenon_h"] - inch(0.5),
        )
        sleeve.append(outer.cut(inner))


# FreeCAD runs scripts with __name__ != "__main__" — execute at import time.
doc = App.newDocument("MARTIN")

make_pad_and_piers()
make_posts()
make_privacy_rails()
make_cap()
make_boards()
make_gate_leaf()

groups = [
    ("timber", timber),
    ("concrete", concrete),
    ("gravel", gravel),
    ("sleeve", sleeve),
]

feature_objs = []
for name, shapes in groups:
    if not shapes:
        continue
    # compound keeps parts distinct for STEP; fuse not required for export
    comp = Part.makeCompound(shapes)
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = comp
    feature_objs.append(obj)

doc.recompute()
doc.saveAs(os.path.join(OUT, "martin.FCStd"))

import Import
Import.export(feature_objs, os.path.join(OUT, "martin_assembly.step"))

for name, shapes in groups:
    if not shapes:
        continue
    comp = Part.makeCompound(shapes)
    mesh = MeshPart.meshFromShape(
        Shape=comp, LinearDeflection=1.5, AngularDeflection=0.4
    )
    mobj = doc.addObject("Mesh::Feature", name + "_mesh")
    mobj.Mesh = mesh
    Mesh.export([mobj], os.path.join(OUT, "martin_%s.stl" % name))

print("MARTIN exports written to", OUT)
print("Run length (mm):", L, "(%g in)" % (L / IN))
print("Height (mm):", H, "(%g in)" % (H / IN))
print("Gate clear (mm):", gate, "(%g in)" % (gate / IN))
print("Post centers (in):", [round(p / IN, 2) for p in POSTS])
print("Bay clear (in):", round(bay_clear / IN, 2))
print("Drop-off makeup (in):", P["drop_off"] / IN)