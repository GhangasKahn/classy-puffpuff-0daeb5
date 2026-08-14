"""
MARTIN FreeCAD model — Rev F Darwin Martin Tree of Life light-screen.
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
    timber, ballast = [], []

    fx, fy = v("post_x"), v("post_y")
    rt = v("rail_t")
    sh, st = ly["sill_h"], ly["sill_t"]
    sill_x0 = -v("sill_overhang")

    # driveway sill (high, y negative)
    ds = box_in(ly["sill_len"], st, sh, sill_x0, ly["drive_sill_cy"] - st / 2.0, -sh)
    feature_objs.append(add_shape(doc, "F001_Driveway_Sill", ds, parts_by_id["F-001"], a_base))
    timber.append(ds)
    # garden sill (low, packing under)
    gs = box_in(ly["sill_len"], st, sh, sill_x0, ly["garden_sill_cy"] - st / 2.0, -sh)
    feature_objs.append(add_shape(doc, "F002_Garden_Sill", gs, parts_by_id["F-002"], a_base))
    timber.append(gs)

    for i, pst in enumerate(ly["posts"]):
        cx = pst["cx"]
        pid = pst["id"]
        body = cbox_in(fx, fy, ly["post_body_h"], cx, 0, 0)
        ten = cbox_in(v("post_tenon_x"), v("post_tenon_y"), v("post_tenon_h"),
                      cx, 0, -v("post_tenon_h"))
        post = body.fuse(ten)
        if pst["mark"] != "P0":
            for s in ly["slats"]:
                mz = s["z0"]
                hh = s["h"]
                if s["nuki"]:
                    pocket = cbox_in(fx + 0.08, rt + v("nuki_fit"), hh + 0.04, cx, 0, mz)
                    post = post.cut(pocket)
                    slot = cbox_in(v("kusabi_t"), fy + 0.08, v("kusabi_w"),
                                   cx + fx * 0.28, 0, s["cl"])
                    post = post.cut(slot)
                elif s["id"].startswith("Q-"):
                    dx = v("groove_d")
                    for sign in (-1.0, 1.0):
                        hx = cx + sign * (fx / 2.0 - dx / 2.0)
                        dado = cbox_in(dx + 0.04, v("board_t") + v("nuki_fit"), hh + 0.04, hx, 0, mz)
                        post = post.cut(dado)
        nm = pid.replace("-", "") + "_" + pst["mark"] + "_" + pst["role"].replace(" ", "_")[:24]
        feature_objs.append(add_shape(doc, nm, post, parts_by_id[pid], a_posts))
        timber.append(post)

        # cross-tie
        ty0 = ly["drive_sill_cy"] - st / 2.0 - v("tie_reveal")
        tie = box_in(fx, ly["tie_len"], sh, cx - fx / 2.0, ty0, -sh)
        mort = cbox_in(v("post_tenon_x") + 0.04, v("post_tenon_y") + 0.04, v("post_tenon_h") + 0.1,
                       cx, 0, -v("post_tenon_h"))
        tie = tie.cut(mort)
        feature_objs.append(add_shape(doc, f"F003_Tie_{pst['mark']}", tie, parts_by_id["F-003"], a_base))
        timber.append(tie)

        # packing under garden sill — only if outriggers leave the slab
        if ly["pack_h"] > 0.05:
            pack = cbox_in(v("pack_len"), v("pack_w"), ly["pack_h"],
                           cx, ly["garden_sill_cy"], -sh - ly["pack_h"])
            feature_objs.append(add_shape(doc, f"F004_Pack_{pst['mark']}", pack, parts_by_id["F-004"], a_base))
            timber.append(pack)

    # live planters — garden side of privacy bays only (NOT at house / P0)
    px, py, ph = v("planter_x"), v("planter_y"), v("planter_h")
    stone_h = v("planter_stone_h")
    for i, (left, right) in enumerate(((1, 2), (2, 3)), 1):
        pcx = (ly["posts"][left]["cx"] + ly["posts"][right]["cx"]) / 2.0
        y0 = fy / 2.0 + 0.5
        box = box_in(px, py, ph, pcx - px / 2.0, y0, 0)
        feature_objs.append(add_shape(doc, f"F005_Planter_{i}", box, parts_by_id["F-005"], a_base))
        timber.append(box)
        fill = box_in(px - 2.0, py - 2.0, stone_h, pcx - (px - 2.0) / 2.0, y0 + 1.0, 0.25)
        feature_objs.append(add_shape(doc, f"H007_Stone_{i}", fill, parts_by_id["H-007"], a_base))
        ballast.append(fill)

    # sujikai braces (simplified boxes)
    for i, pst in enumerate(ly["posts"]):
        if pst["mark"] not in ("P0", "P3"):
            continue
        bl = ly["brace_len"]
        br = box_in(1.5, v("brace_w"), bl, pst["cx"] - 0.75, ly["drive_sill_cy"] - v("brace_w") / 2.0, 0)
        feature_objs.append(add_shape(doc, f"F006_Brace_{pst['mark']}", br, parts_by_id["F-006"], a_base))
        timber.append(br)

    # Water table + belts (full nuki_len) and per-bay recessed cassettes
    for s in ly["slats"]:
        if s["id"].startswith("Q-"):
            rec = v("board_t")
            for bi, (la, rb) in enumerate(((1, 2), (2, 3))):
                x0 = ly["posts"][la]["cx"] + fx / 2.0
                ww = ly["bay_clear"]
                panel = box_in(ww, rec, s["h"], x0, -rec / 2.0 - 0.35, s["z0"])
                tag = "TreeOfLife" if s["id"] == "Q-002" else "NestedRects"
                feature_objs.append(add_shape(doc, s["id"].replace("-", "") + f"_{tag}_B{bi}", panel, parts_by_id[s["id"]], a_frame))
                timber.append(panel)
            continue
        band = box_in(ly["nuki_len"], rt, s["h"], ly["nuki_x0"], -rt / 2.0, s["z0"])
        tag = "WaterTable" if s["id"] == "K-001" else "Belt"
        feature_objs.append(add_shape(doc, s["id"].replace("-", "") + "_" + tag, band, parts_by_id[s["id"]], a_frame))
        timber.append(band)

    cap = box_in(ly["cap_len"], v("cap_w"), v("cap_t"),
                 ly["cap_x0"], -v("cap_w") / 2.0, ly["overall_height"] - v("cap_t"))
    feature_objs.append(add_shape(doc, "C001_Prairie_Eave", cap, parts_by_id["C-001"], a_frame))
    timber.append(cap)

    fascia = box_in(ly["cap_len"], v("board_t"), v("fascia_h"),
                    ly["cap_x0"], v("cap_w") / 2.0 - v("board_t"),
                    ly["overall_height"] - v("cap_t") - v("fascia_h"))
    feature_objs.append(add_shape(doc, "C003_Eave_Fascia", fascia, parts_by_id["C-003"], a_frame))
    timber.append(fascia)

    stub = cbox_in(ly["cap_stub_len"], v("cap_w"), v("cap_t"),
                   ly["posts"][0]["cx"], 0, ly["overall_height"] - v("cap_t"))
    feature_objs.append(add_shape(doc, "C002_Latch_Cap_Stub", stub, parts_by_id["C-002"], a_posts))
    timber.append(stub)

    # Roman-brick wrap on P1/P2/P3 — garden face at belt heights
    bs = v("block_s")
    belts = [s for s in ly["slats"] if s["id"].startswith("R-")]
    for pst in ly["posts"]:
        if pst["mark"] == "P0":
            continue
        for zi, sl in enumerate(belts):
            zc = sl["cl"]
            for k in range(3):
                blk = cbox_in(bs, bs, bs, pst["cx"] + (k - 1) * (bs + 0.12), fy / 2.0 + bs / 2.0 + 0.05, zc - bs / 2.0)
                feature_objs.append(add_shape(doc, f"T001_{pst['mark']}_{zi}_{k}", blk, parts_by_id["T-001"], a_frame))
                timber.append(blk)

    # gate
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
    nuki_rails = [s for s in ly["slats"] if s["nuki"] and s["id"].startswith("R-")]
    for rid, sl in zip(("G-003", "G-004"), nuki_rails):
        gw = v("rail_gate_h")
        g = box_in(w - 2 * stile, t, gw, x0 + stile, y0, sl["cl"] - gw / 2.0)
        feature_objs.append(add_shape(doc, rid.replace("-", "") + "_Gate_Rail", g, parts_by_id[rid], a_gate))
        timber.append(g)
    q3 = next(s for s in ly["slats"] if s["id"] == "Q-003")
    g5 = box_in(w - 2 * stile, t, v("rail_gate_h"), x0 + stile, y0, q3["cl"] - v("rail_gate_h") / 2.0)
    feature_objs.append(add_shape(doc, "G005_Gate_Rail", g5, parts_by_id["G-005"], a_gate))
    timber.append(g5)
    for rid, zz, ht in (("G-006", z0, 3.5), ("G-007", z0 + gh - 3.5, 3.5)):
        g = box_in(w - 2 * stile, t, ht, x0 + stile, y0, zz)
        feature_objs.append(add_shape(doc, rid.replace("-", "") + "_Gate_Rail", g, parts_by_id[rid], a_gate))
        timber.append(g)
    # G-008 shop brace is driveway-face only — omit from garden-facing CAD solids

    rec = v("board_t")
    for i, s in enumerate(ly["slats"]):
        if not s["id"].startswith("Q-"):
            continue
        z0b = max(s["z0"], z0)
        z1b = min(s["z1"], z0 + gh)
        if z1b - z0b < 0.4:
            continue
        g = box_in(ly["gate_inner"], rec, z1b - z0b, x0 + stile, y0 + t * 0.2, z0b)
        feature_objs.append(add_shape(doc, f"G009_Cassette_{s['id'].replace('-', '')}", g, parts_by_id["G-009"], a_gate))
        timber.append(g)
    # Tree of Life muntins on the gate (trunks / pots / frames — not every jewel)
    for m in ly["motifs"]:
        if m.get("bay") != "gate" or m.get("kind") != "tree-of-life":
            continue
        for j, r in enumerate(m.get("rects") or []):
            if r.get("role") not in ("trunk", "pot", "frame"):
                continue
            if r["w"] < 0.3 or r["h"] < 0.3:
                continue
            mun = box_in(r["w"], rec, r["h"], r["x"], y0 + t * 0.35, r["z"])
            feature_objs.append(add_shape(doc, f"G009_Muntin_{j}", mun, parts_by_id["G-009"], a_gate))
            timber.append(mun)

    bar = box_in(v("latch_bar_l"), v("latch_bar_t"), v("latch_bar_w"),
                 x0 - v("latch_bar_l") + 2.0, -v("latch_bar_t") / 2.0,
                 ly["latch_cl"] - v("latch_bar_w") / 2.0)
    feature_objs.append(add_shape(doc, "G010_Latch_Bar", bar, parts_by_id["G-010"], a_gate))
    timber.append(bar)

    doc.recompute()
    doc.saveAs(os.path.join(OUT, "martin.FCStd"))

    import Import
    Import.export(feature_objs, os.path.join(OUT, "martin_assembly.step"))

    for name, shapes in (("timber", timber), ("ballast", ballast)):
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
