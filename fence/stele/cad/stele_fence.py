"""
STELE — Buffalo NY old-world fence, parametric FreeCAD model.

Design language:
  * Egyptian  — battered (tapered) pier shafts: mass + water shedding
  * Roman     — foundations below frost, semicircular arch gate, keystone
  * Mayan     — corbelled stepped caps, raised plinth platform

Climate targets (Buffalo / Erie County NY):
  * Footing bottom 48" (1220 mm) below grade — under frost line
  * Timber held >= 12" above grade on masonry curb (splash / snowbank)
  * All masonry tops sloped or stepped; drip kerfs called out in plans
  * Air-entrained 4000 psi concrete; gravel drainage pad under footings

Run headless:
  freecadcmd stele_fence.py

Outputs (into ./exports):
  stele.FCStd, stele_assembly.step, and per-material STLs
  (masonry / timber / concrete / gravel) for rendering.
"""

import os

import FreeCAD as App
import Part
import Mesh
import MeshPart

V = App.Vector

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")
os.makedirs(OUT, exist_ok=True)

# ----------------------------------------------------------------------------
# Parameters (mm) — grade is z = 0, fence runs along +x, y is thickness
# ----------------------------------------------------------------------------
P = dict(
    # foundations (Roman: below frost, drained)
    frost_depth=1220,          # 48" Buffalo frost protection
    footing_w=600,             # 24" square pad
    footing_h=300,             # 12" thick
    gravel_w=700,
    gravel_h=150,              # 6" compacted #57 stone
    stem_w=350,                # concrete stem to grade

    # plinth + pier shaft (Egyptian batter)
    plinth_w=560, plinth_h=150,
    shaft_base=480, shaft_top=360, shaft_h=1600,   # batter ~1:27/side

    # Mayan stepped cap
    cap1_w=560, cap1_h=50,
    cap2_w=470, cap2_h=55,
    pyr_base=380, pyr_top=180, pyr_h=110,

    # bays
    bay_cc=2440,               # 8 ft pier centers, panel bays
    n_panel_bays_left=2,       # panel bays left of gate
    n_panel_bays_right=1,      # panel bays right of gate

    # timber infill (Hashira through-rails)
    rail_t=38, rail_w=89,      # 2x4 cedar on edge
    rail_z=(350, 1000, 1650),  # rail centerlines
    pocket_depth=60,
    board_t=19, board_w=140, board_gap=10,
    board_z0=320, board_z1=1780,
    tcap_h=45, tcap_w=120,     # sloped timber cap rail

    # masonry curb between piers (keeps wood out of snow/splash)
    curb_w=200, curb_h=250,

    # Roman arch gate
    gate_clear=1220,           # 4 ft clear opening
    arch_depth=220,            # radial depth of ring
    arch_thick=350,            # y thickness
    impost_w=520, impost_h=60,
    key_b=180, key_t=280, key_h=300, key_proud=30,

    # gate leaf (ledged + braced cedar)
    leaf_gap=25, stile=70, ledge=45, leaf_h=1600, leaf_t=40,
)

masonry, timber, concrete, gravel = [], [], [], []


def box(l, w, h, x, y, z):
    return Part.makeBox(l, w, h, V(x, y, z))


def cbox(l, w, h, cx, cy, z):
    """Box centered on (cx, cy) at base height z."""
    return Part.makeBox(l, w, h, V(cx - l / 2.0, cy - w / 2.0, z))


def sq_wire(side, z):
    s = side / 2.0
    return Part.makePolygon(
        [V(-s, -s, z), V(s, -s, z), V(s, s, z), V(-s, s, z), V(-s, -s, z)]
    )


def rect_wire(lx, ly, z):
    x, y = lx / 2.0, ly / 2.0
    return Part.makePolygon(
        [V(-x, -y, z), V(x, -y, z), V(x, y, z), V(-x, y, z), V(-x, -y, z)]
    )


def battered_shaft(base, top, h, z0):
    return Part.makeLoft([sq_wire(base, z0), sq_wire(top, z0 + h)], True)


def stepped_cap(z0):
    c1 = cbox(P["cap1_w"], P["cap1_w"], P["cap1_h"], 0, 0, z0)
    c2 = cbox(P["cap2_w"], P["cap2_w"], P["cap2_h"], 0, 0, z0 + P["cap1_h"])
    pyr = Part.makeLoft(
        [
            sq_wire(P["pyr_base"], z0 + P["cap1_h"] + P["cap2_h"]),
            sq_wire(P["pyr_top"], z0 + P["cap1_h"] + P["cap2_h"] + P["pyr_h"]),
        ],
        True,
    )
    return c1.fuse(c2).fuse(pyr)


def pier(cx, with_cap=True, pockets=("left", "right")):
    """Full pier at center cx: gravel/footing/stem below, plinth+shaft+cap above."""
    gravel.append(
        cbox(P["gravel_w"], P["gravel_w"], P["gravel_h"], cx, 0,
             -P["frost_depth"] - P["gravel_h"])
    )
    concrete.append(
        cbox(P["footing_w"], P["footing_w"], P["footing_h"], cx, 0, -P["frost_depth"])
    )
    concrete.append(
        cbox(P["stem_w"], P["stem_w"], P["frost_depth"] - P["footing_h"], cx, 0,
             -P["frost_depth"] + P["footing_h"])
    )

    plinth = cbox(P["plinth_w"], P["plinth_w"], P["plinth_h"], cx, 0, 0)
    shaft = battered_shaft(P["shaft_base"], P["shaft_top"], P["shaft_h"], P["plinth_h"])
    shaft.translate(V(cx, 0, 0))
    body = plinth.fuse(shaft)

    # rail pockets (Hashira nuki seats), cut into shaft faces toward the bays
    pk_x = P["pocket_depth"] + 40
    for side in pockets:
        sgn = -1 if side == "left" else 1
        for zc in P["rail_z"]:
            pocket = cbox(
                pk_x, P["rail_t"] + 6, P["rail_w"] + 6,
                cx + sgn * (P["shaft_base"] / 2.0 + pk_x / 2.0 - P["pocket_depth"]),
                0, zc - (P["rail_w"] + 6) / 2.0,
            )
            body = body.cut(pocket)

    if with_cap:
        body = body.fuse(stepped_cap(P["plinth_h"] + P["shaft_h"]))
    masonry.append(body)
    return body


def panel_bay(cx0, cx1):
    """Timber infill + curb between pier centers cx0 -> cx1."""
    clear = (cx1 - cx0) - P["shaft_base"]
    x0 = cx0 + P["shaft_base"] / 2.0

    # masonry curb
    masonry.append(box(clear, P["curb_w"], P["curb_h"], x0, -P["curb_w"] / 2.0, 0))

    # through rails, engaged into pier pockets
    rail_len = clear + 2 * P["pocket_depth"]
    for zc in P["rail_z"]:
        timber.append(
            box(rail_len, P["rail_t"], P["rail_w"],
                x0 - P["pocket_depth"], -P["rail_t"] / 2.0, zc - P["rail_w"] / 2.0)
        )

    # vertical boards, rain-screen side
    pitch = P["board_w"] + P["board_gap"]
    n = int((clear - P["board_gap"]) // pitch)
    span = n * pitch - P["board_gap"]
    bx = x0 + (clear - span) / 2.0
    by = -P["rail_t"] / 2.0 - P["board_t"] - 2
    bh = P["board_z1"] - P["board_z0"]
    for i in range(n):
        timber.append(
            box(P["board_w"], P["board_t"], bh, bx + i * pitch, by, P["board_z0"])
        )

    # sloped timber cap (8 deg wash, modeled as wedge loft)
    zc0 = P["board_z1"]
    w = P["tcap_w"]
    lo = rect_wire(rail_len, w, 0)
    hi = rect_wire(rail_len, w, 0)
    hi.translate(V(0, 0, P["tcap_h"]))
    cap = Part.makeLoft([lo, hi], True)
    wedge_cut = box(rail_len + 20, w, P["tcap_h"], -rail_len / 2.0 - 10, -w / 2.0, 0)
    wedge_cut = wedge_cut.common(cap)  # keep simple prism
    slope = Part.makeLoft(
        [
            Part.makePolygon([
                V(-rail_len / 2.0, -w / 2.0, 0), V(rail_len / 2.0, -w / 2.0, 0),
                V(rail_len / 2.0, -w / 2.0, P["tcap_h"]),
                V(-rail_len / 2.0, -w / 2.0, P["tcap_h"]),
                V(-rail_len / 2.0, -w / 2.0, 0),
            ]),
            Part.makePolygon([
                V(-rail_len / 2.0, w / 2.0, 0), V(rail_len / 2.0, w / 2.0, 0),
                V(rail_len / 2.0, w / 2.0, P["tcap_h"] * 0.35),
                V(-rail_len / 2.0, w / 2.0, P["tcap_h"] * 0.35),
                V(-rail_len / 2.0, w / 2.0, 0),
            ]),
        ],
        True,
    )
    slope.translate(V(x0 - P["pocket_depth"] + rail_len / 2.0, 0, zc0))
    timber.append(slope)


def gate_bay(cx0):
    """Roman arch gate. Returns center x of far gate pier."""
    span_cc = P["gate_clear"] + P["shaft_base"]
    cx1 = cx0 + span_cc
    gc = (cx0 + cx1) / 2.0  # gate centerline

    # gate piers (no stepped caps — imposts + arch crown instead)
    pier(cx0, with_cap=False, pockets=("left",))
    pier(cx1, with_cap=False, pockets=("right",))

    z_spring = P["plinth_h"] + P["shaft_h"] + P["impost_h"]

    # impost blocks
    for cx in (cx0, cx1):
        masonry.append(
            cbox(P["impost_w"], P["impost_w"], P["impost_h"], cx, 0,
                 P["plinth_h"] + P["shaft_h"])
        )

    # semicircular arch ring (extruded half-annulus)
    r_in = P["gate_clear"] / 2.0
    r_out = r_in + P["arch_depth"]
    t = P["arch_thick"]
    cyl_out = Part.makeCylinder(r_out, t, V(gc, -t / 2.0, z_spring), V(0, 1, 0))
    cyl_in = Part.makeCylinder(r_in, t, V(gc, -t / 2.0, z_spring), V(0, 1, 0))
    ring = cyl_out.cut(cyl_in)
    below = box(2 * r_out + 20, t + 20, r_out + 20,
                gc - r_out - 10, -t / 2.0 - 10, z_spring - r_out - 20)
    arch = ring.cut(below)
    masonry.append(arch)

    # keystone (tapered, proud of the ring)
    kb, kt, kh = P["key_b"], P["key_t"], P["key_h"]
    ky = t + 2 * P["key_proud"]
    z_key = z_spring + r_out - kh + 60
    key = Part.makeLoft(
        [
            Part.makePolygon([
                V(gc - kb / 2.0, -ky / 2.0, z_key), V(gc + kb / 2.0, -ky / 2.0, z_key),
                V(gc + kb / 2.0, ky / 2.0, z_key), V(gc - kb / 2.0, ky / 2.0, z_key),
                V(gc - kb / 2.0, -ky / 2.0, z_key),
            ]),
            Part.makePolygon([
                V(gc - kt / 2.0, -ky / 2.0, z_key + kh), V(gc + kt / 2.0, -ky / 2.0, z_key + kh),
                V(gc + kt / 2.0, ky / 2.0, z_key + kh), V(gc - kt / 2.0, ky / 2.0, z_key + kh),
                V(gc - kt / 2.0, -ky / 2.0, z_key + kh),
            ]),
        ],
        True,
    )
    masonry.append(key)

    # ledged + braced cedar leaf
    lw = P["gate_clear"] - 2 * P["leaf_gap"]
    lx0 = gc - lw / 2.0
    lt, lh = P["leaf_t"], P["leaf_h"]
    st, lg = P["stile"], P["ledge"]
    z0 = 150  # over threshold clearance
    # stiles
    timber.append(box(st, lt, lh, lx0, -lt / 2.0, z0))
    timber.append(box(st, lt, lh, lx0 + lw - st, -lt / 2.0, z0))
    # ledges (top / mid / bottom)
    for zl in (z0 + 40, z0 + lh / 2.0 - lg / 2.0, z0 + lh - lg - 40):
        timber.append(box(lw - 2 * st, lg, lg, lx0 + st, -lg / 2.0, zl))
    # diagonal brace (from bottom hinge side up to latch side)
    brace = box(lw * 1.25, lg, lg, 0, 0, 0)
    import math
    ang = math.degrees(math.atan2(lh - 2 * (lg + 40) - lg, lw - 2 * st))
    brace.rotate(V(0, 0, 0), V(0, 1, 0), -ang)
    brace.translate(V(lx0 + st, -lg / 2.0, z0 + 40 + lg))
    leaf_clip = box(lw - 2 * st, lg + 4, lh - 60, lx0 + st, -(lg + 4) / 2.0, z0 + 30)
    timber.append(brace.common(leaf_clip))
    # face boards
    pitch = 90 + 6
    nb = int(lw // pitch)
    span = nb * pitch - 6
    bx = lx0 + (lw - span) / 2.0
    for i in range(nb):
        timber.append(box(90, 16, lh, bx + i * pitch, -lt / 2.0 - 16 - 1, z0))

    return cx1


# ----------------------------------------------------------------------------
# Assembly: [panel bays] + arch gate + [panel bays]
# ----------------------------------------------------------------------------
centers = [0.0]
for _ in range(P["n_panel_bays_left"]):
    centers.append(centers[-1] + P["bay_cc"])

# left run of piers; last one also borders the connecting bay into the gate
for i, cx in enumerate(centers):
    pk = []
    if i > 0:
        pk.append("left")
    pk.append("right")
    pier(cx, with_cap=True, pockets=tuple(pk))

for i in range(len(centers) - 1):
    panel_bay(centers[i], centers[i + 1])

# gate — a fresh pair of piers just right of the last panel pier
gate_left = centers[-1] + P["bay_cc"]
panel_bay(centers[-1], gate_left)  # connecting panel into gate-left pier
gate_right = gate_bay(gate_left)

# right run
rc = [gate_right]
for _ in range(P["n_panel_bays_right"]):
    nxt = rc[-1] + P["bay_cc"]
    panel_bay(rc[-1], nxt)
    rc.append(nxt)
for i, cx in enumerate(rc[1:], start=1):
    pk = ["left"] if i == len(rc) - 1 else ["left", "right"]
    pier(cx, with_cap=True, pockets=tuple(pk))

# NOTE: gate piers were built inside gate_bay(); left-run piers above.

# ----------------------------------------------------------------------------
# Document, exports
# ----------------------------------------------------------------------------
doc = App.newDocument("Stele")

groups = [
    ("Masonry", masonry, (0.82, 0.78, 0.66)),
    ("Timber", timber, (0.55, 0.38, 0.22)),
    ("Concrete", concrete, (0.62, 0.62, 0.60)),
    ("Gravel", gravel, (0.35, 0.34, 0.32)),
]

feature_objs = []
for name, shapes, rgb in groups:
    if not shapes:
        continue
    comp = Part.makeCompound(shapes)
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = comp
    feature_objs.append(obj)

doc.recompute()
doc.saveAs(os.path.join(OUT, "stele.FCStd"))

# STEP assembly
import Import
Import.export(feature_objs, os.path.join(OUT, "stele_assembly.step"))

# per-material STLs for rendering
for name, shapes, rgb in groups:
    if not shapes:
        continue
    comp = Part.makeCompound(shapes)
    mesh = MeshPart.meshFromShape(Shape=comp, LinearDeflection=2.0, AngularDeflection=0.35)
    mobj = doc.addObject("Mesh::Feature", name + "_mesh")
    mobj.Mesh = mesh
    Mesh.export([mobj], os.path.join(OUT, "stele_%s.stl" % name.lower()))

print("STELE exports written to", OUT)
total_len = (rc[-1] - 0) + P["shaft_base"]
print("Run length (mm):", total_len)
print("Pier top (mm):", P["plinth_h"] + P["shaft_h"] + P["cap1_h"] + P["cap2_h"] + P["pyr_h"])
print("Arch crown (mm):", P["plinth_h"] + P["shaft_h"] + P["impost_h"] + P["gate_clear"] / 2.0 + P["arch_depth"])
