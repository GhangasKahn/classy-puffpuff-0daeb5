"""
MARTIN FreeCAD model — Rev C
Semantic parts from martin_kernel.build_project(). Native CAD unit: mm.

Run:  freecadcmd martin_fence.py
"""

from __future__ import annotations

import os
import sys

import FreeCAD as App
import Mesh
import MeshPart
import Part

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from martin_kernel import MM, PROJECT, build_project, inch_mm, v  # noqa: E402

V = App.Vector
OUT = os.path.join(HERE, "exports")
os.makedirs(OUT, exist_ok=True)


def box_in(dx, dy, dz, x, y, z):
    """Inches → mm box."""
    return Part.makeBox(
        inch_mm(dx), inch_mm(dy), inch_mm(dz),
        V(inch_mm(x), inch_mm(y), inch_mm(z)),
    )


def cbox_in(dx, dy, dz, cx, cy, z):
    return box_in(dx, dy, dz, cx - dx / 2.0, cy - dy / 2.0, z)


def fab_props(obj, part):
    grp = "Fabrication"
    mapping = {
        "PartNumber": str(part.get("PART_ID", "")),
        "PartName": str(part.get("PART_NAME", "")),
        "Quantity": str(part.get("QUANTITY", "")),
        "Material": str(part.get("MATERIAL", "")),
        "Species": str(part.get("SPECIES", "")),
        "Grade": str(part.get("GRADE", "")),
        "RoughLength": str(part.get("ROUGH_LENGTH", "")),
        "RoughWidth": str(part.get("ROUGH_WIDTH", "")),
        "RoughThickness": str(part.get("ROUGH_THICKNESS", "")),
        "FinishedLength": str(part.get("FINISHED_LENGTH", "")),
        "FinishedWidth": str(part.get("FINISHED_WIDTH", "")),
        "FinishedThickness": str(part.get("FINISHED_THICKNESS", "")),
        "GrainDirection": str(part.get("GRAIN_DIRECTION", "")),
        "ReferenceFace": str(part.get("REFERENCE_FACE", "")),
        "Process": str(part.get("PROCESS", "")),
        "Finish": "owner gray — mask locking faces",
        "Notes": str(part.get("NOTES", "")),
        "Revision": str(part.get("REVISION", PROJECT["REVISION"])),
    }
    for name, val in mapping.items():
        try:
            obj.addProperty("App::PropertyString", name, grp)
            setattr(obj, name, val)
        except Exception:
            try:
                setattr(obj, name, val)
            except Exception:
                pass


def add_shape(doc, name, shape, part_meta, group):
    obj = doc.addObject("Part::Feature", name)
    obj.Label = name
    obj.Shape = shape
    fab_props(obj, part_meta or {})
    group.addObject(obj)
    return obj


def main_build():
    proj = build_project()
    ly = proj["layout"]
    parts_by_id = {p["PART_ID"]: p for p in proj["parts"]}

    doc = App.newDocument("MARTIN")
    master = doc.addObject("App::Part", "A000_MASTER")
    a_base = doc.addObject("App::Part", "A001_BASE")
    a_posts = doc.addObject("App::Part", "A010_POSTS")
    a_frame = doc.addObject("App::Part", "A020_PRIVACY_FRAME")
    a_gate = doc.addObject("App::Part", "A030_GATE")
    master.addObject(a_base)
    master.addObject(a_posts)
    master.addObject(a_frame)
    master.addObject(a_gate)

    feature_objs = []
    timber, concrete, gravel, sleeve = [], [], [], []

    # pad
    pad = cbox_in(ly["pad_len"], ly["pad_width"], v("pad_thick"),
                  ly["overall_length"] / 2.0, 0, -v("pad_thick"))
    feature_objs.append(add_shape(doc, "F001_Leveling_Pad", pad, parts_by_id["F-001"], a_base))
    concrete.append(pad)

    makeup = cbox_in(ly["pad_len"], v("pad_width") * 0.45, v("drop_off"),
                     ly["overall_length"] / 2.0, v("pad_width") * 0.28,
                     -v("pad_thick") - v("drop_off"))
    feature_objs.append(add_shape(doc, "F002_Dropoff_Makeup", makeup, parts_by_id["F-002"], a_base))
    concrete.append(makeup)

    grav = cbox_in(
        ly["pad_len"] + 2 * v("gravel_extra"),
        v("pad_width") + 2 * v("gravel_extra"),
        v("gravel_h"),
        ly["overall_length"] / 2.0, 0,
        -v("pad_thick") - v("drop_off") - v("gravel_h"),
    )
    feature_objs.append(add_shape(doc, "F004_Gravel_Bed", grav, parts_by_id["F-004"], a_base))
    gravel.append(grav)

    fx, fy = v("post_x"), v("post_y")
    rh, rt = v("rail_h"), v("rail_t")

    for i, pst in enumerate(ly["posts"]):
        cx = pst["cx"]
        pid = pst["id"]
        body = cbox_in(fx, fy, ly["post_body_h"], cx, 0, 0)
        ten = cbox_in(v("post_tenon_x"), v("post_tenon_y"), v("post_tenon_h"),
                      cx, 0, -v("post_tenon_h"))
        post = body.fuse(ten)
        for zc in ly["rail_cls"]:
            mz = zc - rh / 2.0
            pocket = cbox_in(fx + 0.08, rt + v("nuki_fit"), rh + 0.04, cx, 0, mz)
            post = post.cut(pocket)
        if pst["mark"] != "P0":
            for zc in ly["rail_cls"]:
                slot = cbox_in(v("kusabi_t"), fy + 0.08, v("kusabi_w"),
                               cx + fx * 0.28, 0, zc)
                post = post.cut(slot)
        nm = pid.replace("-", "") + "_" + pst["mark"] + "_" + pst["role"].replace(" ", "_")[:24]
        feature_objs.append(add_shape(doc, nm, post, parts_by_id[pid], a_posts))
        timber.append(post)

        pier = cbox_in(v("pier_xy"), v("pier_xy"), v("pier_h"), cx, 0, -v("pier_h"))
        pocket = cbox_in(ly["sleeve_id_x"], ly["sleeve_id_y"], v("post_tenon_h") + 2.0,
                         cx, 0, -v("post_tenon_h") - 1.0)
        pier = pier.cut(pocket)
        feature_objs.append(add_shape(doc, f"F003_Pier_{pst['mark']}", pier, parts_by_id["F-003"], a_base))
        concrete.append(pier)

        sw = v("sleeve_wall")
        outer = cbox_in(ly["sleeve_id_x"] + 2 * sw, ly["sleeve_id_y"] + 2 * sw,
                        v("post_tenon_h") + 1.5, cx, 0, -v("post_tenon_h") - 0.5)
        inner = cbox_in(ly["sleeve_id_x"], ly["sleeve_id_y"], v("post_tenon_h") + 2.0,
                        cx, 0, -v("post_tenon_h") - 0.5)
        sl = outer.cut(inner)
        feature_objs.append(add_shape(doc, f"H001_Sleeve_{pst['mark']}", sl, parts_by_id["H-001"], a_base))
        sleeve.append(sl)

    # nuki rails
    for j, (rid, cl) in enumerate(zip(("R-001", "R-002", "R-003"), ly["rail_cls"])):
        rail = box_in(ly["nuki_len"], rt, rh, ly["nuki_x0"], -rt / 2.0, cl - rh / 2.0)
        feature_objs.append(add_shape(doc, rid.replace("-", "") + "_Nuki", rail, parts_by_id[rid], a_frame))
        timber.append(rail)

    cap = box_in(ly["cap_len"], v("cap_w"), v("cap_t"),
                 ly["cap_x0"], -v("cap_w") / 2.0, ly["overall_height"] - v("cap_t"))
    feature_objs.append(add_shape(doc, "C001_Privacy_Cap", cap, parts_by_id["C-001"], a_frame))
    timber.append(cap)

    stub = cbox_in(ly["cap_stub_len"], v("cap_w"), v("cap_t"),
                   ly["posts"][0]["cx"], 0, ly["overall_height"] - v("cap_t"))
    feature_objs.append(add_shape(doc, "C002_Latch_Cap_Stub", stub, parts_by_id["C-002"], a_posts))
    timber.append(stub)

    # privacy boards
    pitch = v("board_w") + v("board_gap")
    yb = -fy / 2.0 + 0.5
    for bay_i, (left_id, right_id) in enumerate(((1, 2), (2, 3))):
        x_left = ly["posts"][left_id]["cx"] + fx / 2.0
        x_start = x_left + ly["board_inset"]
        for ci, course in enumerate(ly["courses"]):
            bh = course["h"]
            bid = "B-001" if ci == 0 else ("B-003" if ci == 3 else "B-002")
            for i in range(ly["n_bay"]):
                x = x_start + i * pitch
                brd = box_in(v("board_w"), v("board_t"), bh, x, yb, course["z0"])
                nm = f"{bid.replace('-', '')}_bay{bay_i}_c{ci}_i{i}"
                feature_objs.append(add_shape(doc, nm, brd, parts_by_id[bid], a_frame))
                timber.append(brd)

    # gate
    import math
    gap = v("gate_gap")
    x0 = fx + gap
    w = ly["gate_leaf_w"]
    t = v("leaf_t")
    y0 = -t / 2.0
    z0 = v("gate_bottom_clear")
    gh = ly["gate_h"]
    stile = v("stile_w")
    hs = box_in(stile, t, gh, x0, y0, z0)
    ls = box_in(stile, t, gh, x0 + w - stile, y0, z0)
    feature_objs.append(add_shape(doc, "G001_Hinge_Stile", hs, parts_by_id["G-001"], a_gate))
    feature_objs.append(add_shape(doc, "G002_Latch_Stile", ls, parts_by_id["G-002"], a_gate))
    timber += [hs, ls]
    for rid, cl, gw in (
        ("G-003", v("rail_cl_1"), v("rail_gate_h")),
        ("G-004", v("rail_cl_2"), v("rail_gate_h")),
        ("G-005", v("rail_cl_3"), v("rail_gate_h")),
    ):
        g = box_in(w - 2 * stile, t, gw, x0 + stile, y0, cl - gw / 2.0)
        feature_objs.append(add_shape(doc, rid.replace("-", "") + "_Gate_Rail", g, parts_by_id[rid], a_gate))
        timber.append(g)
    for rid, zz, ht in (("G-006", z0, 3.5), ("G-007", z0 + gh - 3.5, 3.5)):
        g = box_in(w - 2 * stile, t, ht, x0 + stile, y0, zz)
        feature_objs.append(add_shape(doc, rid.replace("-", "") + "_Gate_Rail", g, parts_by_id[rid], a_gate))
        timber.append(g)
    brace_len = math.hypot(ly["gate_inner"], gh - 10.0)
    brace = box_in(brace_len, t, v("brace_w"), 0, y0, 0)
    brace.rotate(V(0, 0, 0), V(0, 1, 0), -math.degrees(math.atan2(gh - 10.0, ly["gate_inner"])))
    brace.translate(V(inch_mm(x0 + stile), 0, inch_mm(z0 + 5)))
    feature_objs.append(add_shape(doc, "G008_Brace", brace, parts_by_id["G-008"], a_gate))
    timber.append(brace)

    inner = ly["gate_inner"]
    n = ly["n_gate_boards"]
    used = n * v("board_w") + (n - 1) * v("board_gap")
    xs = x0 + stile + (inner - used) / 2.0
    bh = gh - 8.0
    for i in range(n):
        g = box_in(v("board_w"), v("board_t"), bh, xs + i * pitch, y0 + t * 0.15, z0 + 4.0)
        feature_objs.append(add_shape(doc, f"G009_Infill_{i}", g, parts_by_id["G-009"], a_gate))
        timber.append(g)

    bar = box_in(v("latch_bar_l"), v("latch_bar_t"), v("latch_bar_w"),
                 x0 - v("latch_bar_l") + 2.0, -v("latch_bar_t") / 2.0,
                 v("rail_cl_2") - v("latch_bar_w") / 2.0)
    feature_objs.append(add_shape(doc, "G010_Latch_Bar", bar, parts_by_id["G-010"], a_gate))
    timber.append(bar)

    doc.recompute()
    doc.saveAs(os.path.join(OUT, "martin.FCStd"))

    import Import
    Import.export(feature_objs, os.path.join(OUT, "martin_assembly.step"))

    for name, shapes in (("timber", timber), ("concrete", concrete), ("gravel", gravel), ("sleeve", sleeve)):
        if not shapes:
            continue
        comp = Part.makeCompound(shapes)
        mesh = MeshPart.meshFromShape(Shape=comp, LinearDeflection=1.5, AngularDeflection=0.4)
        mobj = doc.addObject("Mesh::Feature", name + "_mesh")
        mobj.Mesh = mesh
        Mesh.export([mobj], os.path.join(OUT, "martin_%s.stl" % name))

    print("MARTIN exports written to", OUT)
    print("Revision:", PROJECT["REVISION"])
    print("Run length (mm):", inch_mm(ly["overall_length"]), "(%g in)" % ly["overall_length"])
    print("Height (mm):", inch_mm(ly["overall_height"]), "(%g in)" % ly["overall_height"])
    print("Gate clear (mm):", inch_mm(ly["gate_clear"]), "(%g in)" % ly["gate_clear"])
    print("Post centers (in):", [p["cx"] for p in ly["posts"]])
    print("Bay clear (in):", ly["bay_clear"])
    print("Post blank (in):", ly["post_blank_l"])
    print("Gate h (in):", ly["gate_h"])
    print("Drop-off makeup (in):", v("drop_off"))


# FreeCAD executes scripts without __main__
main_build()
