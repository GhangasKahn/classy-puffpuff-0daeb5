#!/usr/bin/env python3
"""MARTIN parametric fabrication source of truth.

Internal unit: inch. Convert only at CAD/export interfaces.
All dependent geometry is derived. Do not copy these numbers elsewhere —
import this module or consume martin.json.

Run:  python3 fence/martin/fab/martin_ssot.py
"""

from __future__ import annotations

import csv
import json
import math
import os
from copy import deepcopy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
IN_MM = 25.4

PROJECT = {
    "PROJECT_ID": "MARTIN",
    "PROJECT_NAME": "Prairie removable fence — Buffalo NY",
    "REVISION": "D",
    "UNITS": "inch",
    "DESIGN_STANDARD": "Japanese joinery / Prairie horizontals / winter-removable",
    "MATERIAL_SYSTEM": "Select DF mill stock re-dimensioned + white oak hardware",
    "TOLERANCE_CLASS": "T2 joinery / T1 general / T0 site verify",
    "AUTHOR": "owner shop · Festool MFT / Bridge City / Zenwu",
    "MODEL_VERSION": "1.0",
    "DATE": "2026-08-13",
    "CAD_PLATFORM": "FreeCAD Python + OpenSCAD preview + SVG drawings",
}

# ---------------------------------------------------------------------------
# Master parameters (inches). Classification: V=verified, D=derived,
# A=assumed, E=estimated, M=to be measured.
# ---------------------------------------------------------------------------
PARAMS = {
    "overall_length": {"value": 143.0, "class": "V", "note": "Site opening, outer face to outer face"},
    "overall_height": {"value": 65.0, "class": "V", "note": "Pad top to cap top"},
    "post_x": {"value": 3.5, "class": "D", "note": "Finished face along run; milled from 6×6"},
    "post_y": {"value": 5.5, "class": "D", "note": "Finished depth; keep 6×6 actual face"},
    "post_tenon_x": {"value": 2.5, "class": "A", "note": "Foot tenon; ~1″ shoulders on 3.5″ face"},
    "post_tenon_y": {"value": 4.5, "class": "A", "note": "Foot tenon; ~0.5″ shoulders on 5.5″ face"},
    "post_tenon_h": {"value": 12.0, "class": "A", "note": "Into sleeved pier"},
    "gate_clear": {"value": 36.0, "class": "V", "note": "Clear opening between P0 and P1 inner faces"},
    "gate_gap": {"value": 0.5, "class": "A", "note": "Each side of leaf — seasonal + swing"},
    "leaf_t": {"value": 1.5, "class": "D", "note": "Gate leaf thickness = rail_t"},
    "stile_w": {"value": 3.5, "class": "A", "note": "Gate stile face, ripped from 2×12 remainder"},
    "rail_gate_h": {"value": 5.5, "class": "A", "note": "Gate rails aligning with Prairie bands"},
    "brace_w": {"value": 3.5, "class": "A", "note": "Half-lap brace width"},
    "rail_t": {"value": 1.5, "class": "D", "note": "Nuki thickness = 2×12 actual"},
    "rail_h": {"value": 7.25, "class": "D", "note": "Nuki height ripped from 2×12 outer zone (not equal thirds)"},
    "rail_z_cl": {"value": (10.0, 28.0, 46.0), "class": "A", "note": "Prairie band centerlines AFF pad"},
    "cap_t": {"value": 1.5, "class": "D", "note": "Cap thickness = rail_t"},
    "cap_w": {"value": 7.25, "class": "D", "note": "Cap width = rail_h"},
    "board_t": {"value": 0.75, "class": "D", "note": "From 1×12 planed true"},
    "board_w": {"value": 5.5, "class": "D", "note": "From 1×12 edge strips"},
    "board_gap": {"value": 0.25, "class": "A", "note": "FLOATING drainage / movement"},
    "pad_overhang": {"value": 6.0, "class": "A", "note": "Each end beyond timber envelope"},
    "pad_width": {"value": 28.0, "class": "A", "note": "Across grade"},
    "pad_thick": {"value": 6.0, "class": "A", "note": "Leveling pad thickness"},
    "drop_off": {"value": 5.0, "class": "M", "note": "Driveway→garden; FIELD VERIFY before pour"},
    "pier_xy": {"value": 14.0, "class": "A", "note": "Tip-out socket pier plan"},
    "pier_h": {"value": 18.0, "class": "A", "note": "Pier height below pad top"},
    "sleeve_wall": {"value": 0.25, "class": "A", "note": "PVC/galv liner wall"},
    "sleeve_clearance": {"value": 0.25, "class": "A", "note": "Tenon-to-sleeve winter pull — do not tighten"},
    "gravel_h": {"value": 6.0, "class": "A", "note": "Compacted #57"},
    "gravel_pad_extra": {"value": 4.0, "class": "A", "note": "Gravel beyond pad"},
    "latch_bar_x": {"value": 18.0, "class": "A", "note": "Sliding oak bar length"},
    "latch_bar_y": {"value": 1.5, "class": "A", "note": "Bar thickness"},
    "latch_bar_z": {"value": 3.5, "class": "A", "note": "Bar height"},
    "house_receiver_depth": {"value": 4.0, "class": "A", "note": "Latch A sleeve into house"},
    "nuki_height_ease": {"value": 0.0625, "class": "A", "note": "Seasonal mortise height ease only"},
    "nuki_reveal": {"value": 0.5, "class": "A", "note": "Rail overhang past post outer faces"},
    "cap_reveal": {"value": 0.75, "class": "A", "note": "Cap overhang past post outer faces"},
    "drawbore_offset": {"value": 0.125, "class": "A", "note": "Toward shoulder"},
    "peg_d": {"value": 0.375, "class": "A", "note": "White oak drawbore peg"},
    "kusabi_t": {"value": 0.625, "class": "A", "note": "Wedge thickness"},
    "kusabi_w": {"value": 1.125, "class": "A", "note": "Wedge width"},
    "kusabi_l": {"value": 5.5, "class": "A", "note": "Wedge length"},
    "groove_d": {"value": 0.375, "class": "A", "note": "Board plow depth"},
    "groove_w": {"value": 0.875, "class": "A", "note": "Board plow width; ~1/8″ total float on 3/4″ boards"},
    "saw_kerf": {"value": 0.125, "class": "A", "note": "TS / track-saw kerf for nesting"},
    "waste_factor": {"value": 0.22, "class": "A", "note": "Mill re-dimension + grain selection waste"},
    "plumb_tol": {"value": 0.125, "class": "A", "note": "Posts over 65″"},
    "shoulder_tol": {"value": 0.03125, "class": "A", "note": "Foot tenon shoulders T2"},
    "layout_tol": {"value": 0.015625, "class": "A", "note": "1/64″ joinery layout"},
    "sleeve_drain_d": {"value": 0.5, "class": "A", "note": "Drain at sleeve bottom"},
    "board_course_clear": {"value": 0.125, "class": "A", "note": "Board end clearance to rail"},
    "board_pad_clear": {"value": 1.5, "class": "A", "note": "Bottom course above pad"},
}


def pv(name: str) -> float:
    v = PARAMS[name]["value"]
    if isinstance(v, (tuple, list)):
        raise TypeError(name)
    return float(v)


def layout() -> dict:
    """Derived envelope. Change overall_length and posts/bays follow."""
    L = pv("overall_length")
    H = pv("overall_height")
    fx = pv("post_x")
    fy = pv("post_y")
    gate = pv("gate_clear")
    cap_t = pv("cap_t")
    tenon_h = pv("post_tenon_h")
    rh = pv("rail_h")
    zs = tuple(PARAMS["rail_z_cl"]["value"])

    p0 = fx / 2.0
    p1 = fx + gate + fx / 2.0
    p1_right = p1 + fx / 2.0
    p3_left = L - fx
    clear_span = p3_left - p1_right
    bay_clear = (clear_span - fx) / 2.0
    p2 = p1_right + bay_clear + fx / 2.0
    p3 = L - fx / 2.0

    nuki_x0 = p1 - fx / 2.0 - pv("nuki_reveal")
    nuki_x1 = p3 + fx / 2.0 + pv("nuki_reveal")
    nuki_len = nuki_x1 - nuki_x0

    cap_x0 = p1 - fx / 2.0 - pv("cap_reveal")
    cap_x1 = p3 + fx / 2.0 + pv("cap_reveal")
    cap_len = cap_x1 - cap_x0

    # D-001: post length is height minus cap plus tenon — NOT height + tenon.
    post_above = H - cap_t
    post_finished_l = post_above + tenon_h

    leaf_w = gate - 2 * pv("gate_gap")
    leaf_h = H - cap_t - 0.5
    leaf_x0 = fx + pv("gate_gap")

    pitch = pv("board_w") + pv("board_gap")
    n_bay = max(1, int(math.floor((bay_clear + pv("board_gap")) / pitch)))
    gate_inner = leaf_w - 2 * pv("stile_w")
    n_gate = max(1, int(math.floor((gate_inner + pv("board_gap")) / pitch)))

    cc = pv("board_course_clear")
    courses = [
        ("C1_below_R1", pv("board_pad_clear"), zs[0] - rh / 2.0 - cc),
        ("C2_R1_R2", zs[0] + rh / 2.0 + cc, zs[1] - rh / 2.0 - cc),
        ("C3_R2_R3", zs[1] + rh / 2.0 + cc, zs[2] - rh / 2.0 - cc),
        ("C4_above_R3", zs[2] + rh / 2.0 + cc, H - cap_t - cc),
    ]
    course_h = [(cid, round(z1 - z0, 4), z0, z1) for cid, z0, z1 in courses]

    pad_len = L + 2 * pv("pad_overhang")
    mortise_h = rh + pv("nuki_height_ease")
    mortise_w = pv("rail_t")  # match measured rail; sliding fit
    cheek = (fy - mortise_w) / 2.0

    return {
        "post_centers": (round(p0, 4), round(p1, 4), round(p2, 4), round(p3, 4)),
        "post_ids": ("P0", "P1", "P2", "P3"),
        "bay_clear": round(bay_clear, 4),
        "nuki_length": round(nuki_len, 4),
        "cap_length": round(cap_len, 4),
        "post_above_pad": round(post_above, 4),
        "post_finished_length": round(post_finished_l, 4),
        "leaf_width": round(leaf_w, 4),
        "leaf_height": round(leaf_h, 4),
        "leaf_x0": round(leaf_x0, 4),
        "boards_per_bay": n_bay,
        "boards_gate": n_gate,
        "bays": 2,
        "course_heights": course_h,
        "privacy_board_qty": n_bay * 2 * len(course_h),
        "pad_length": round(pad_len, 4),
        "mortise_width": round(mortise_w, 4),
        "mortise_height": round(mortise_h, 4),
        "mortise_cheek": round(cheek, 4),
        "equations": {
            "P0": "post_x / 2",
            "P1": "post_x + gate_clear + post_x / 2",
            "bay_clear": "(overall_length - 3*post_x - gate_clear) / 2",
            "P2": "P1 + post_x/2 + bay_clear + post_x/2",
            "P3": "overall_length - post_x / 2",
            "post_finished_length": "overall_height - cap_t + post_tenon_h",
            "nuki_length": "(P3 - P1) + post_x + 2*nuki_reveal",
            "mortise_height": "rail_h + nuki_height_ease",
            "mortise_cheek": "(post_y - rail_t) / 2",
            "leaf_width": "gate_clear - 2*gate_gap",
        },
    }


def bf(t, w, l_in) -> float:
    return round(t * w * l_in / 144.0, 2)


def _part(**kw):
    kw.setdefault("MAKE_OR_BUY", "MAKE")
    kw.setdefault("REVISION", PROJECT["REVISION"])
    kw.setdefault("GRAIN_DIRECTION", "length")
    return kw


def parts(ly: dict) -> list:
    """Part registry. Identical parts share one ID with QTY>1."""
    pf = ly["post_finished_length"]
    nuki = ly["nuki_length"]
    cap = ly["cap_length"]
    leaf_h = ly["leaf_height"]
    leaf_w = ly["leaf_width"]
    stile = pv("stile_w")
    inner = leaf_w - 2 * stile
    posts_meta = [
        ("L-001", "P0 Latch post", "Latch / house side — nuki mortises, no kusabi; latch B mortise"),
        ("L-002", "P1 Hinge post", "Gate pintles; nuki + kusabi; gudgeon faces"),
        ("L-003", "P2 Mid post", "Cap scarf bearing; nuki + kusabi"),
        ("L-004", "P3 End post", "Run terminus; nuki + kusabi"),
    ]
    out = []
    for pid, name, note in posts_meta:
        out.append(_part(
            PART_ID=pid, PART_NAME=name, PART_CATEGORY="post", ASSEMBLY="A-FRAME",
            QUANTITY=1, MATERIAL="Douglas fir", SPECIES="DF", GRADE="Select / #1",
            PURCHASE="6×6 × 8′",
            ROUGH_THICKNESS=5.5, ROUGH_WIDTH=5.5, ROUGH_LENGTH=77.0,
            FINISHED_THICKNESS=pv("post_x"), FINISHED_WIDTH=pv("post_y"),
            FINISHED_LENGTH=pf,
            REFERENCE_FACE="garden face", REFERENCE_EDGE="run-left arris",
            REFERENCE_END="tenon shoulder (pad top)",
            PROCESS="rip 6×6→3½×5½ · shoulder tenon · bore/chisel nuki · kusabi slots except L-001",
            JOINERY="foot tenon + nuki mortise" + ("" if pid == "L-001" else " + kusabi"),
            HANDED="unique", NOTES=note,
            BOARD_FEET_NET=bf(pv("post_x"), pv("post_y"), pf),
        ))

    for i, rid in enumerate(("R-001", "R-002", "R-003")):
        cl = PARAMS["rail_z_cl"]["value"][i]
        out.append(_part(
            PART_ID=rid, PART_NAME=f"Nuki Prairie band R{i+1}", PART_CATEGORY="rail",
            ASSEMBLY="A-PRIVACY", QUANTITY=1, MATERIAL="Douglas fir", SPECIES="DF",
            GRADE="Select / #1", PURCHASE="2×12 × 12′ outer zone",
            ROUGH_THICKNESS=1.5, ROUGH_WIDTH=11.25, ROUGH_LENGTH=144.0,
            FINISHED_THICKNESS=pv("rail_t"), FINISHED_WIDTH=pv("rail_h"),
            FINISHED_LENGTH=nuki,
            REFERENCE_FACE="top edge", REFERENCE_EDGE="garden face",
            REFERENCE_END="P1 overhang",
            PROCESS="rip 7¼″ from 2×12 outer zone · plow grooves · dry-slide",
            JOINERY="nuki through L-002/003/004 + kusabi",
            HANDED="identical-orientation", NOTES=f"CL AFF {cl}″",
            BOARD_FEET_NET=bf(pv("rail_t"), pv("rail_h"), nuki),
        ))

    cap_half = round(cap / 2.0, 3)
    out.append(_part(
        PART_ID="R-004", PART_NAME="Cap scarf leaf A (P1–P2)", PART_CATEGORY="cap",
        ASSEMBLY="A-PRIVACY", QUANTITY=1, MATERIAL="Douglas fir", SPECIES="DF",
        GRADE="Select / #1", PURCHASE="2×12 × 12′",
        ROUGH_THICKNESS=1.5, ROUGH_WIDTH=11.25, ROUGH_LENGTH=144.0,
        FINISHED_THICKNESS=pv("cap_t"), FINISHED_WIDTH=pv("cap_w"),
        FINISHED_LENGTH=cap_half,
        REFERENCE_FACE="top", REFERENCE_EDGE="garden", REFERENCE_END="P2 scarf",
        PROCESS="kama-tsugi · shoot · drawbore", JOINERY="kama-tsugi J-KAMA-01",
        HANDED="left-of-scarf", NOTES="Mates R-005 at P2",
        BOARD_FEET_NET=bf(pv("cap_t"), pv("cap_w"), cap_half),
    ))
    out.append(_part(
        PART_ID="R-005", PART_NAME="Cap scarf leaf B (P2–P3)", PART_CATEGORY="cap",
        ASSEMBLY="A-PRIVACY", QUANTITY=1, MATERIAL="Douglas fir", SPECIES="DF",
        GRADE="Select / #1", PURCHASE="2×12 × 12′",
        ROUGH_THICKNESS=1.5, ROUGH_WIDTH=11.25, ROUGH_LENGTH=72.0,
        FINISHED_THICKNESS=pv("cap_t"), FINISHED_WIDTH=pv("cap_w"),
        FINISHED_LENGTH=cap_half,
        REFERENCE_FACE="top", REFERENCE_EDGE="garden", REFERENCE_END="P2 scarf",
        PROCESS="kama-tsugi · shoot · drawbore", JOINERY="kama-tsugi J-KAMA-01",
        HANDED="right-of-scarf", NOTES="Mates R-004 at P2",
        BOARD_FEET_NET=bf(pv("cap_t"), pv("cap_w"), cap_half),
    ))
    out.append(_part(
        PART_ID="R-006", PART_NAME="Cap stub over P0", PART_CATEGORY="cap",
        ASSEMBLY="A-GATE", QUANTITY=1, MATERIAL="Douglas fir", SPECIES="DF",
        GRADE="Select / #1", PURCHASE="2×12 offcut",
        ROUGH_THICKNESS=1.5, ROUGH_WIDTH=7.25, ROUGH_LENGTH=12.0,
        FINISHED_THICKNESS=pv("cap_t"), FINISHED_WIDTH=pv("cap_w"),
        FINISHED_LENGTH=round(pv("post_x") + 1.0, 3),
        REFERENCE_FACE="top", REFERENCE_EDGE="garden", REFERENCE_END="house",
        PROCESS="crosscut · plane", JOINERY="bears on L-001; does not bridge gate",
        HANDED="none", NOTES="Does not span gate opening",
        BOARD_FEET_NET=bf(pv("cap_t"), pv("cap_w"), pv("post_x") + 1.0),
    ))

    for cid, h, z0, z1 in ly["course_heights"]:
        qty = ly["boards_per_bay"] * ly["bays"]
        out.append(_part(
            PART_ID=f"P-{cid[:2]}", PART_NAME=f"Privacy board {cid}",
            PART_CATEGORY="board", ASSEMBLY="A-PRIVACY", QUANTITY=qty,
            MATERIAL="Douglas fir", SPECIES="DF", GRADE="Select VG-leaning",
            PURCHASE="1×12 × 10′ edge strips",
            ROUGH_THICKNESS=0.75, ROUGH_WIDTH=11.25, ROUGH_LENGTH=120.0,
            FINISHED_THICKNESS=pv("board_t"), FINISHED_WIDTH=pv("board_w"),
            FINISHED_LENGTH=h,
            REFERENCE_FACE="garden", REFERENCE_EDGE="left", REFERENCE_END="bottom",
            PROCESS="rip VG edge · plane ¾″ · cut to course",
            JOINERY="FLOATING in R-001–R-003 grooves — no fasteners",
            HANDED="identical", NOTES=f"z {z0:.3f}–{z1:.3f} AFF; gap {pv('board_gap')}″",
            BOARD_FEET_NET=round(qty * bf(pv("board_t"), pv("board_w"), h), 2),
            CONSTRAINT="FLOATING",
        ))

    out.append(_part(
        PART_ID="G-001", PART_NAME="Gate stile (pair)", PART_CATEGORY="gate",
        ASSEMBLY="A-GATE", QUANTITY=2, MATERIAL="Douglas fir", SPECIES="DF",
        GRADE="Select / #1", PURCHASE="2×12 remainder 3½″ strip",
        ROUGH_THICKNESS=1.5, ROUGH_WIDTH=3.5, ROUGH_LENGTH=leaf_h + 1.0,
        FINISHED_THICKNESS=pv("leaf_t"), FINISHED_WIDTH=stile, FINISHED_LENGTH=leaf_h,
        REFERENCE_FACE="garden", REFERENCE_EDGE="outer", REFERENCE_END="bottom",
        PROCESS="hozo mortises · pintle gudgeons on P1 stile",
        JOINERY="hozo drawbore to G-010 rails", HANDED="LH/RH pair",
        NOTES="G-001A latch stile · G-001B hinge stile — mark both",
        BOARD_FEET_NET=round(2 * bf(pv("leaf_t"), stile, leaf_h), 2),
    ))
    out.append(_part(
        PART_ID="G-010", PART_NAME="Gate rails (Prairie-aligned + top/bottom)",
        PART_CATEGORY="gate", ASSEMBLY="A-GATE", QUANTITY=5, MATERIAL="Douglas fir",
        SPECIES="DF", GRADE="Select / #1", PURCHASE="2×12 remainder",
        ROUGH_THICKNESS=1.5, ROUGH_WIDTH=5.5, ROUGH_LENGTH=inner + 3.0,
        FINISHED_THICKNESS=pv("leaf_t"), FINISHED_WIDTH=pv("rail_gate_h"),
        FINISHED_LENGTH=inner,
        REFERENCE_FACE="garden", REFERENCE_EDGE="top", REFERENCE_END="tenon shoulder",
        PROCESS="tenon both ends · drawbore from MFT stop",
        JOINERY="hozo into G-001", HANDED="identical",
        NOTES="Three align R1–R3 CL; extra top/bottom 3.5″ rails in CAD",
        BOARD_FEET_NET=round(5 * bf(pv("leaf_t"), pv("rail_gate_h"), inner), 2),
    ))
    brace_len = round(math.hypot(inner, leaf_h - 10.0), 3)
    out.append(_part(
        PART_ID="G-020", PART_NAME="Gate diagonal brace", PART_CATEGORY="gate",
        ASSEMBLY="A-GATE", QUANTITY=1, MATERIAL="Douglas fir", SPECIES="DF",
        GRADE="Select / #1", PURCHASE="2×12 remainder",
        ROUGH_THICKNESS=1.5, ROUGH_WIDTH=3.5, ROUGH_LENGTH=brace_len + 2.0,
        FINISHED_THICKNESS=pv("leaf_t"), FINISHED_WIDTH=pv("brace_w"),
        FINISHED_LENGTH=brace_len,
        REFERENCE_FACE="garden", REFERENCE_EDGE="long", REFERENCE_END="lower hinge",
        PROCESS="protractor angle · half-lap · Preda shoot",
        JOINERY="half-lap into G-010 — no fasteners", HANDED="none",
        NOTES="Compression brace; orientation: low at latch, high at hinge (confirm swing)",
        BOARD_FEET_NET=bf(pv("leaf_t"), pv("brace_w"), brace_len),
    ))
    gq = ly["boards_gate"]
    out.append(_part(
        PART_ID="G-030", PART_NAME="Gate infill boards", PART_CATEGORY="board",
        ASSEMBLY="A-GATE", QUANTITY=gq, MATERIAL="Douglas fir", SPECIES="DF",
        GRADE="Select VG-leaning", PURCHASE="1×12 edge strips",
        ROUGH_THICKNESS=0.75, ROUGH_WIDTH=5.5, ROUGH_LENGTH=leaf_h,
        FINISHED_THICKNESS=pv("board_t"), FINISHED_WIDTH=pv("board_w"),
        FINISHED_LENGTH=round(leaf_h - 8.0, 3),
        REFERENCE_FACE="garden", REFERENCE_EDGE="left", REFERENCE_END="bottom",
        PROCESS="float / retain in gate frame language",
        JOINERY="FLOATING — no fasteners", HANDED="identical",
        NOTES="Match privacy 1×6 language", CONSTRAINT="FLOATING",
        BOARD_FEET_NET=round(gq * bf(pv("board_t"), pv("board_w"), leaf_h - 8), 2),
    ))

    nuki_seats = 3 * 3  # R1–R3 × P1–P3
    out.append(_part(
        PART_ID="K-001", PART_NAME="Kusabi wedge", PART_CATEGORY="joinery",
        ASSEMBLY="A-PRIVACY", QUANTITY=nuki_seats + 3, MATERIAL="White oak",
        SPECIES="Q. alba", GRADE="clear", PURCHASE="8/4 × 6″ × 6′",
        ROUGH_THICKNESS=0.75, ROUGH_WIDTH=1.25, ROUGH_LENGTH=6.0,
        FINISHED_THICKNESS=pv("kusabi_t"), FINISHED_WIDTH=pv("kusabi_w"),
        FINISHED_LENGTH=pv("kusabi_l"),
        REFERENCE_FACE="drive face", REFERENCE_EDGE="long", REFERENCE_END="thin",
        PROCESS="kerf tools set angle · rip · hand-fit each slot · label",
        JOINERY="friction lock — NEVER glue", HANDED="fit-to-slot",
        NOTES=f"{nuki_seats} seats + 3 spares. Softwood forbidden outdoors.",
        CONSTRAINT="CLEARANCED", BOARD_FEET_NET=bf(0.75, 6.0, 72.0) * 0.15,
    ))
    out.append(_part(
        PART_ID="H-001", PART_NAME="Drawbore peg", PART_CATEGORY="joinery",
        ASSEMBLY="A-GATE", QUANTITY=12, MATERIAL="White oak", SPECIES="Q. alba",
        GRADE="clear", PURCHASE="8/4 offcut",
        ROUGH_THICKNESS=0.5, ROUGH_WIDTH=0.5, ROUGH_LENGTH=4.0,
        FINISHED_THICKNESS=pv("peg_d"), FINISHED_WIDTH=pv("peg_d"),
        FINISHED_LENGTH=3.0,
        REFERENCE_FACE="n/a", REFERENCE_EDGE="n/a", REFERENCE_END="entry chamfer",
        PROCESS="rasp/turn ⌀⅜ · light Taylor countersink on mortise mouth only",
        JOINERY="drawbore ⅛″ offset", HANDED="none",
        NOTES="Gate hozo + cap scarf. Not structural nails.",
        BOARD_FEET_NET=0.1,
    ))
    out.append(_part(
        PART_ID="H-002", PART_NAME="Wooden pintle + gudgeon set", PART_CATEGORY="hardware-wood",
        ASSEMBLY="A-GATE", QUANTITY=2, MATERIAL="White oak / hard maple",
        SPECIES="oak", GRADE="clear", PURCHASE="8/4",
        ROUGH_THICKNESS=1.5, ROUGH_WIDTH=1.5, ROUGH_LENGTH=8.0,
        FINISHED_THICKNESS=1.0, FINISHED_WIDTH=1.0, FINISHED_LENGTH=6.0,
        REFERENCE_FACE="bearing", REFERENCE_EDGE="plumb", REFERENCE_END="tip",
        PROCESS="turn/rasp · dry-fit lift-off", JOINERY="wood hinge — lift straight up",
        HANDED="pair", NOTES="On L-002. Optional stainless upgrade is only allowed metal hinge.",
        MAKE_OR_BUY="MAKE", BOARD_FEET_NET=0.2,
    ))
    out.append(_part(
        PART_ID="H-003", PART_NAME="Sliding latch bar", PART_CATEGORY="hardware-wood",
        ASSEMBLY="A-GATE", QUANTITY=1, MATERIAL="White oak", SPECIES="Q. alba",
        GRADE="clear", PURCHASE="8/4",
        ROUGH_THICKNESS=1.75, ROUGH_WIDTH=3.75, ROUGH_LENGTH=20.0,
        FINISHED_THICKNESS=pv("latch_bar_y"), FINISHED_WIDTH=pv("latch_bar_z"),
        FINISHED_LENGTH=pv("latch_bar_x"),
        REFERENCE_FACE="top", REFERENCE_EDGE="long", REFERENCE_END="house",
        PROCESS="plane · fit stile slot", JOINERY="sliding — Latch A house sleeve or Latch B P0 mortise",
        HANDED="none", NOTES="Cross-peg + optional padlock hasp (only metal lock)",
        BOARD_FEET_NET=bf(pv("latch_bar_y"), pv("latch_bar_z"), pv("latch_bar_x")),
    ))

    # Purchased / site
    out.append(_part(
        PART_ID="H-010", PART_NAME="Sleeve liner", PART_CATEGORY="hardware",
        ASSEMBLY="A-BASE", QUANTITY=4, MAKE_OR_BUY="BUY", MATERIAL="PVC Sch40 or galv.",
        SPECIES="—", GRADE="—", PURCHASE="tube to tenon + ¼″ clear",
        ROUGH_THICKNESS=0, ROUGH_WIDTH=0, ROUGH_LENGTH=pv("post_tenon_h") + 2.0,
        FINISHED_THICKNESS=0, FINISHED_WIDTH=0, FINISHED_LENGTH=pv("post_tenon_h") + 1.5,
        REFERENCE_FACE="n/a", REFERENCE_EDGE="n/a", REFERENCE_END="drain",
        PROCESS="drill ⌀½″ drain at bottom", JOINERY="receives foot tenon CLEARANCE",
        HANDED="none", NOTES="Do not tighten around tenon — winter pull",
        BOARD_FEET_NET=0,
    ))
    out.append(_part(
        PART_ID="C-001", PART_NAME="Leveling pad", PART_CATEGORY="concrete",
        ASSEMBLY="A-BASE", QUANTITY=1, MAKE_OR_BUY="MAKE", MATERIAL="4000 psi AE concrete",
        SPECIES="—", GRADE="air-entrained", PURCHASE="~0.35 yd³ with piers",
        ROUGH_THICKNESS=pv("pad_thick"), ROUGH_WIDTH=pv("pad_width"),
        ROUGH_LENGTH=ly["pad_length"],
        FINISHED_THICKNESS=pv("pad_thick"), FINISHED_WIDTH=pv("pad_width"),
        FINISHED_LENGTH=ly["pad_length"],
        REFERENCE_FACE="top (level)", REFERENCE_EDGE="driveway", REFERENCE_END="P0 end",
        PROCESS="form · pour · cure", JOINERY="n/a", HANDED="none",
        NOTES=f"Drop makeup default {pv('drop_off')}″ — class M field verify",
        BOARD_FEET_NET=0,
    ))
    out.append(_part(
        PART_ID="C-002", PART_NAME="Socket pier", PART_CATEGORY="concrete",
        ASSEMBLY="A-BASE", QUANTITY=4, MAKE_OR_BUY="MAKE", MATERIAL="4000 psi AE concrete",
        SPECIES="—", GRADE="air-entrained / optional precast", PURCHASE="with C-001",
        ROUGH_THICKNESS=pv("pier_xy"), ROUGH_WIDTH=pv("pier_xy"), ROUGH_LENGTH=pv("pier_h"),
        FINISHED_THICKNESS=pv("pier_xy"), FINISHED_WIDTH=pv("pier_xy"),
        FINISHED_LENGTH=pv("pier_h"),
        REFERENCE_FACE="top", REFERENCE_EDGE="garden", REFERENCE_END="top",
        PROCESS="form or precast · tip-out", JOINERY="sleeve pocket",
        HANDED="none", NOTES="Winter: tip onto dolly; store dry", BOARD_FEET_NET=0,
    ))
    out.append(_part(
        PART_ID="H-020", PART_NAME="Optional stainless pintle set", PART_CATEGORY="hardware",
        ASSEMBLY="A-GATE", QUANTITY=1, MAKE_OR_BUY="BUY", MATERIAL="Stainless",
        SPECIES="—", GRADE="—", PURCHASE="optional",
        ROUGH_THICKNESS=0, ROUGH_WIDTH=0, ROUGH_LENGTH=0,
        FINISHED_THICKNESS=0, FINISHED_WIDTH=0, FINISHED_LENGTH=0,
        REFERENCE_FACE="n/a", REFERENCE_EDGE="n/a", REFERENCE_END="n/a",
        PROCESS="install only if wood pintles rejected", JOINERY="only allowed metal hinge",
        HANDED="pair", NOTES="Not required. Timber frame stays nail-free either way.",
        BOARD_FEET_NET=0,
    ))
    return out


def joints(ly: dict) -> list:
    zs = PARAMS["rail_z_cl"]["value"]
    j = []
    for pi, post in enumerate(("L-002", "L-003", "L-004")):
        for ri, rail in enumerate(("R-001", "R-002", "R-003")):
            j.append({
                "JOINT_ID": f"J-NUKI-{post[-1]}{ri+1}",
                "JOINT_TYPE": "nuki + kusabi",
                "PART_A": post, "PART_B": rail,
                "LOCATION": f"CL AFF {zs[ri]}″ through {post}",
                "MORTISE_WIDTH": ly["mortise_width"],
                "MORTISE_HEIGHT": ly["mortise_height"],
                "MORTISE_DEPTH": "through",
                "FIT_CLASS": "SLIDING then WEDGED",
                "CONSTRAINT": "CLEARANCED height / locational width",
                "ASSEMBLY_DIRECTION": "+X rail through post",
                "TOOLING": "bore waste · Zenwu walls · Temple/flush trim · kerf-tool kusabi",
            })
    j.append({
        "JOINT_ID": "J-TENON-FOOT",
        "JOINT_TYPE": "shouldered foot tenon into sleeve",
        "PART_A": "L-001…L-004", "PART_B": "H-010 / C-002",
        "LOCATION": "pad top datum = tenon shoulder",
        "TENON_WIDTH": pv("post_tenon_x"), "TENON_HEIGHT": pv("post_tenon_y"),
        "TENON_LENGTH": pv("post_tenon_h"),
        "FIT_CLASS": "CLEARANCE (+¼″ sleeve)",
        "CONSTRAINT": "CLEARANCED — winter pull",
        "ASSEMBLY_DIRECTION": "-Z drop in",
        "TOOLING": "TS LS 36 shoulders ±1/32″ · plane cheeks",
    })
    j.append({
        "JOINT_ID": "J-KAMA-01",
        "JOINT_TYPE": "kama-tsugi (sickle scarf)",
        "PART_A": "R-004", "PART_B": "R-005",
        "LOCATION": "centered on L-003 / P2",
        "DOWEL_DIAMETER": pv("peg_d"), "DRAWBORE_OFFSET": pv("drawbore_offset"),
        "FIT_CLASS": "DRAWBORED",
        "CONSTRAINT": "FIXED along run after peg",
        "ASSEMBLY_DIRECTION": "in-plane scarf",
        "TOOLING": "Universal V2 protractor · Preda shoot · MFT peg stop",
    })
    j.append({
        "JOINT_ID": "J-HOZO-GATE",
        "JOINT_TYPE": "hozo mortise & tenon drawbored",
        "PART_A": "G-001", "PART_B": "G-010",
        "LOCATION": "every stile/rail intersection",
        "DOWEL_DIAMETER": pv("peg_d"), "DRAWBORE_OFFSET": pv("drawbore_offset"),
        "TENON_THICKNESS_RULE": "~1/3 of 1.5″ leaf = 0.5″ (confirm on stock)",
        "FIT_CLASS": "DRAWBORED",
        "CONSTRAINT": "FIXED after peg; reverse by driving pegs out",
        "ASSEMBLY_DIRECTION": "rails into stiles",
        "TOOLING": "Bridge City tenon + kerf tools · Temple saws · Zenwu · MFT stop",
    })
    j.append({
        "JOINT_ID": "J-LAP-BRACE",
        "JOINT_TYPE": "half-lap",
        "PART_A": "G-020", "PART_B": "G-010",
        "LOCATION": "diagonal across gate leaf",
        "FIT_CLASS": "SNUG geometry / friction — no fasteners",
        "CONSTRAINT": "FIXED in-plane",
        "ASSEMBLY_DIRECTION": "into rail faces",
        "TOOLING": "protractor · shoot on Preda board",
    })
    j.append({
        "JOINT_ID": "J-GROOVE",
        "JOINT_TYPE": "floating plow",
        "PART_A": "R-001…R-003", "PART_B": "P-C* boards",
        "LOCATION": "rail edges, ⅜×⅞",
        "FIT_CLASS": "FREE / FLOATING",
        "CONSTRAINT": "FLOATING",
        "ASSEMBLY_DIRECTION": "-Z drop from top before cap",
        "TOOLING": "one locked TS + LS 36 setup for all rails — no router",
    })
    j.append({
        "JOINT_ID": "J-LATCH",
        "JOINT_TYPE": "sliding bar",
        "PART_A": "H-003", "PART_B": "house sleeve (A) or L-001 mortise (B)",
        "LOCATION": "R2 height",
        "FIT_CLASS": "SLIDING",
        "CONSTRAINT": "SLIDING",
        "ASSEMBLY_DIRECTION": "-X toward house / P0",
        "TOOLING": "plane to slot; epoxy sleeve Latch A only (not timber fasteners)",
    })
    return j


def hardware() -> list:
    return [
        {"HARDWARE_ID": "H-010", "DESCRIPTION": "Sleeve liner PVC Sch40 or galvanized tube",
         "SIZE": "ID = 2.5×4.5 tenon + ¼″ clear", "QTY": 4, "MAKE_OR_BUY": "BUY",
         "NOTES": "⌀½″ drain at bottom"},
        {"HARDWARE_ID": "H-020", "DESCRIPTION": "Optional stainless pintle hinge set",
         "SIZE": "lift-off pair", "QTY": 1, "MAKE_OR_BUY": "BUY",
         "NOTES": "Only allowed metal hinge; wood pintles are default"},
        {"HARDWARE_ID": "H-021", "DESCRIPTION": "Optional keyed padlock hasp",
         "SIZE": "to suit H-003 bar", "QTY": 1, "MAKE_OR_BUY": "BUY",
         "NOTES": "Locking only — not structural"},
        {"HARDWARE_ID": "H-022", "DESCRIPTION": "Epoxy anchoring adhesive (Latch A)",
         "SIZE": "house sleeve only", "QTY": 1, "MAKE_OR_BUY": "BUY",
         "NOTES": "Never on timber locking faces"},
        {"HARDWARE_ID": "C-CON", "DESCRIPTION": "Concrete 4000 psi air-entrained",
         "SIZE": "~0.35 yd³", "QTY": 1, "MAKE_OR_BUY": "BUY", "NOTES": "Pad + 4 piers"},
        {"HARDWARE_ID": "C-STN", "DESCRIPTION": "#57 crushed stone",
         "SIZE": "~0.4 yd³", "QTY": 1, "MAKE_OR_BUY": "BUY", "NOTES": "Under pad"},
        {"HARDWARE_ID": "F-001", "DESCRIPTION": "Exterior primer + owner gray ×2 + end sealer",
         "SIZE": "1 kit", "QTY": 1, "MAKE_OR_BUY": "BUY", "NOTES": "Mask wedges/tenons/pegs/sleeves"},
    ]


def mill_buy() -> list:
    """Procurement — not finished parts. BF is purchase size."""
    return [
        {"ITEM": 1, "QTY": 4, "NOMINAL": "6×6", "LENGTH_FT": 8, "SPECIES": "DF Select / #1",
         "USE": "Posts L-001…L-004", "BF": 96.0, "YIELD": "mill to 3½×5½ × 75.5″ finished"},
        {"ITEM": 2, "QTY": 5, "NOMINAL": "2×12", "LENGTH_FT": 12, "SPECIES": "DF Select / #1",
         "USE": "Nuki R-001…003 + cap + gate", "BF": 120.0,
         "YIELD": "rip 7¼″ outer zone + 3½″ remainder; pith scrap ≠ joinery"},
        {"ITEM": 3, "QTY": 2, "NOMINAL": "2×12", "LENGTH_FT": 10, "SPECIES": "DF Select / #1",
         "USE": "Gate / brace / spare cheeks", "BF": 40.0, "YIELD": "same outer-zone rule"},
        {"ITEM": 4, "QTY": 6, "NOMINAL": "1×12", "LENGTH_FT": 10, "SPECIES": "DF Select VG-ish",
         "USE": "Privacy + gate boards", "BF": 60.0, "YIELD": "edge strips → ¾×5½"},
        {"ITEM": 5, "QTY": 1, "NOMINAL": "8/4×6″", "LENGTH_FT": 6, "SPECIES": "White oak",
         "USE": "K-001 H-001 H-002 H-003", "BF": 6.0, "YIELD": "wedges, pegs, pintles, latch"},
    ]


def stock_nests() -> list:
    """2×12 × 12′ cutting-stock — not a mere length total."""
    nuki = layout()["nuki_length"]
    kerf = pv("saw_kerf")
    return [
        {"BOARD": "2x12-12-01", "PARTS": f"R-001 nuki {nuki}″", "KERF": kerf,
         "REMAINDER_IN": round(144 - nuki - kerf, 2), "NOTES": "remainder → G-010 blanks"},
        {"BOARD": "2x12-12-02", "PARTS": f"R-002 nuki {nuki}″", "KERF": kerf,
         "REMAINDER_IN": round(144 - nuki - kerf, 2), "NOTES": "remainder → G-010 / G-020"},
        {"BOARD": "2x12-12-03", "PARTS": f"R-003 nuki {nuki}″", "KERF": kerf,
         "REMAINDER_IN": round(144 - nuki - kerf, 2), "NOTES": "remainder → G-001 stiles"},
        {"BOARD": "2x12-12-04", "PARTS": "R-004 + R-005 cap halves + R-006 stub", "KERF": kerf,
         "REMAINDER_IN": round(144 - layout()["cap_length"] - 12 - 2 * kerf, 2), "NOTES": "scarf pair from one stick if grain matches"},
        {"BOARD": "2x12-12-05", "PARTS": "spare nuki cheek / gate extra / stakes", "KERF": kerf,
         "REMAINDER_IN": 144, "NOTES": "do not use pith zone for joinery"},
        {"BOARD": "6x6-08-01..04", "PARTS": "L-001…L-004 rough 77″", "KERF": kerf,
         "REMAINDER_IN": round(96 - 77, 2), "NOTES": "one post per blank; remainder firewood/stakes"},
    ]


def operations() -> list:
    """Stop-grouped routing for owner kit. No router. No nails in timber."""
    return [
        {"OP": "OP010", "SETUP": "S-001", "PARTS": "all mill stock", "TOOL": "visual + winding sticks + Incra",
         "ACTION": "Select; reject pith-centered / twist >1/8″ in 8′ / ring shake",
         "REFERENCE": "face grain", "TOLERANCE": "T0", "STOP": "—"},
        {"OP": "OP020", "SETUP": "S-002", "PARTS": "all DF", "TOOL": "stickers ¾″ @ 12–16″",
         "ACTION": "Sticker 14+ days; end-sealer; weight top",
         "REFERENCE": "flat sleepers", "TOLERANCE": "MC stabilize to shop", "STOP": "—"},
        {"OP": "OP030", "SETUP": "S-010", "PARTS": "L-001…L-004", "TOOL": "TS + LS 36 + Fence Guide V2",
         "ACTION": "Rip 6×6 → 3½×5½; joint/plane reference garden face",
         "REFERENCE": "REFERENCE FACE against fence", "TOLERANCE": "T1 ±1/32″ section", "STOP": "fence locked"},
        {"OP": "OP040", "SETUP": "S-011", "PARTS": "L-001…L-004", "TOOL": "Festool track saw + MFT dogs",
         "ACTION": f"Crosscut finished length {layout()['post_finished_length']}″ after tenon layout; rough 77″ first",
         "REFERENCE": "DATUM END = tenon tip during rough; then shoulder", "TOLERANCE": "T1", "STOP": "MFT stop — DO NOT MOVE for all four"},
        {"OP": "OP050", "SETUP": "S-012", "PARTS": "L-001…L-004", "TOOL": "TS LS 36",
         "ACTION": "Shoulder foot tenon 2.5×4.5×12; plane cheeks; dry-fit H-010",
         "REFERENCE": "shoulder = pad-top datum", "TOLERANCE": "T2 ±1/32″", "STOP": "fence locked"},
        {"OP": "OP060", "SETUP": "S-013", "PARTS": "L-001…L-004", "TOOL": "story stick + M1 + Kuratoga",
         "ACTION": "Layout nuki CL 10 / 28 / 46 from pad-top datum (shoulder)",
         "REFERENCE": "Datum End = tenon shoulder", "TOLERANCE": "T2 1/64″", "STOP": "story stick — one stick for all posts"},
        {"OP": "OP070", "SETUP": "S-014", "PARTS": "L-001…L-004", "TOOL": "drill + Zenwu Y2 + Ti hammer + Temple flush trim",
         "ACTION": "Bore waste; chisel mortise to measured rail thickness × (7.25+1/16)",
         "REFERENCE": "cheeks parallel to reference face", "TOLERANCE": "T2 sliding, no rattle", "STOP": "—"},
        {"OP": "OP080", "SETUP": "S-015", "PARTS": "L-002 L-003 L-004", "TOOL": "Bridge City kerf tools + chisel",
         "ACTION": "Kusabi cheek slots; label K-001 to each seat",
         "REFERENCE": "rail dry-assembled position", "TOLERANCE": "T2 hand-fit", "STOP": "—"},
        {"OP": "OP090", "SETUP": "S-020", "PARTS": "R-001 R-002 R-003", "TOOL": "TS + LS 36",
         "ACTION": "Rip 7¼″ from 2×12 OUTER zone (not pith); plane faces",
         "REFERENCE": "VG/rift-leaning edge to garden", "TOLERANCE": "T1", "STOP": "fence locked — all three rails"},
        {"OP": "OP100", "SETUP": "S-021", "PARTS": "R-001 R-002 R-003", "TOOL": "TS + LS 36",
         "ACTION": "Plow ⅜×⅞ grooves; one setup all edges",
         "REFERENCE": "REFERENCE FACE down / fence on reference edge", "TOLERANCE": "T2 test on scrap", "STOP": "DO NOT MOVE fence until all grooves done"},
        {"OP": "OP110", "SETUP": "S-022", "PARTS": "R-001 R-002 R-003", "TOOL": "track saw / miter",
         "ACTION": f"Crosscut nuki to {layout()['nuki_length']}″ after dry-slide through posts",
         "REFERENCE": "P1 overhang datum", "TOLERANCE": "T1", "STOP": "MFT stop"},
        {"OP": "OP120", "SETUP": "S-030", "PARTS": "P-C* G-030", "TOOL": "TS + plane",
         "ACTION": "Rip 1×12 edges to 5½″; plane ¾″; cut courses after rails exist",
         "REFERENCE": "VG edge", "TOLERANCE": "T1", "STOP": "course stops per C1–C4"},
        {"OP": "OP130", "SETUP": "S-040", "PARTS": "R-004 R-005", "TOOL": "protractor + Preda shoot",
         "ACTION": "Kama-tsugi at P2; close to light; drawbore last",
         "REFERENCE": "top face coplanar", "TOLERANCE": "T2", "STOP": "peg from MFT"},
        {"OP": "OP140", "SETUP": "S-050", "PARTS": "G-001 G-010 G-020", "TOOL": "Bridge City tenon + Temple + Zenwu",
         "ACTION": "Hozo frame; half-lap brace; drawbore ⅛″; wooden pintles",
         "REFERENCE": "stile outer = leaf datum", "TOLERANCE": "T2", "STOP": "peg holes MFT"},
        {"OP": "OP150", "SETUP": "S-060", "PARTS": "all timber", "TOOL": "brushes",
         "ACTION": "Prime + gray ×2; mask locking faces",
         "REFERENCE": "—", "TOLERANCE": "T0", "STOP": "—"},
        {"OP": "OP160", "SETUP": "S-070", "PARTS": "A-MASTER", "TOOL": "level / plumb",
         "ACTION": "Drop posts; re-wedge; hang gate; latch; plumb ≤⅛″ / 65″",
         "REFERENCE": "pad top", "TOLERANCE": "T1 plumb", "STOP": "—"},
    ]


def inspection() -> list:
    return [
        {"QC": "QC-01", "GATE": "M0", "CHECK": "Site 143″ and drop-off re-measured", "CLASS": "M",
         "CRITERIA": "Record drop; do not pour on default 5″ if field differs"},
        {"QC": "QC-02", "GATE": "M4", "CHECK": "Stock reject pith / twist / shake after sticker", "CLASS": "T1",
         "CRITERIA": "No pith in finished nuki/post section; twist ≤1/8″ in 8′"},
        {"QC": "QC-03", "GATE": "M4", "CHECK": "Four posts finished length", "CLASS": "T1",
         "CRITERIA": f"{layout()['post_finished_length']}″ ±1/16″"},
        {"QC": "QC-04", "GATE": "M3", "CHECK": "Foot tenon drops/lifts in each sleeve", "CLASS": "T2",
         "CRITERIA": "Hand drop, no twist bind; ¼″ clearance kept"},
        {"QC": "QC-05", "GATE": "M3", "CHECK": "Nuki slides each post dry before final wedge", "CLASS": "T2",
         "CRITERIA": "Sliding width; height ease 1/16″ only; no side rattle"},
        {"QC": "QC-06", "GATE": "M3", "CHECK": "Mortise CL 10 / 28 / 46 from shoulder datum", "CLASS": "T2",
         "CRITERIA": "Story-stick match all posts"},
        {"QC": "QC-07", "GATE": "M5", "CHECK": "Cap scarf closes to light", "CLASS": "T2",
         "CRITERIA": "Shoot-fit before peg"},
        {"QC": "QC-08", "GATE": "M5", "CHECK": "Gate hangs plumb and lifts off pintles", "CLASS": "T1",
         "CRITERIA": "Straight-up winter removal; 36″ clear arc"},
        {"QC": "QC-09", "GATE": "M5", "CHECK": "No nails/screws/glue on locking faces", "CLASS": "T0",
         "CRITERIA": "Visual; fastener ban"},
        {"QC": "QC-10", "GATE": "M7", "CHECK": "Plumb ≤⅛″ over 65″ after set", "CLASS": "T1",
         "CRITERIA": "Walk the run"},
        {"QC": "QC-11", "GATE": "M7", "CHECK": "Wedges labeled and reversible", "CLASS": "T0",
         "CRITERIA": "Winter knock-down dry-run once"},
    ]


def decisions() -> list:
    return [
        {"ID": "D-001", "DECISION": "Post finished length = height − cap_t + tenon_h = 75.5″, not 77″",
         "REASON": "77″ (65+12) double-counted the 1.5″ cap. CAD body was already H−cap_t.",
         "AFFECTED": "L-001…L-004, M-6, app data, cut lists"},
        {"ID": "D-002", "DECISION": "Rip 7.25″ from 2×12 outer zone, not equal thirds",
         "REASON": "2×12 actual 11.25″; equal third is 3.75″ — too narrow for Prairie band.",
         "AFFECTED": "R-001…R-005, M-8 yield map"},
        {"ID": "D-003", "DECISION": "Nuki mortise width = measured rail thickness (not a second 1.5″)",
         "REASON": "Single source: rail_t. Sliding fit, no rattle.",
         "AFFECTED": "J-NUKI-*, OP070"},
        {"ID": "D-004", "DECISION": "No nails/screws/plates/glue on timber locking faces",
         "REASON": "Japanese mechanical lock + winter knock-down + Buffalo freeze-thaw.",
         "AFFECTED": "all joints"},
        {"ID": "D-005", "DECISION": "drop_off remains 5″ default class M",
         "REASON": "Must be field-measured before pour.",
         "AFFECTED": "C-001 makeup"},
        {"ID": "D-006", "DECISION": "Hozo tenon thickness ~1/3 of 1.5″ leaf = 0.5″ — confirm on stock",
         "REASON": "Rule of thumb; unusual if leaf milled off 1.5″.",
         "AFFECTED": "J-HOZO-GATE, G-001, G-010"},
    ]


def tools() -> list:
    return [
        "Festool track saw + MFT (Hongdui dogs / track hinge)",
        "Table saw + Festool TS LS 36 + Woodpeckers Fence Guide V2",
        "Miter saw + Ryobi (rough crosscuts only)",
        "Temple Tool rip + crosscut + flush trim",
        "Zenwu Y2 chisels + titanium hammer",
        "Stanley #5 + Bridge City bench plane",
        "Adrian Preda LW bench + shooting board",
        "Bridge City Universal V2 protractor, tenon tool, both kerf tools, Multi-Tool M1",
        "Incra 12″ rules + Kuratoga metal pencil",
        "Cordless drill + impact + Taylor countersink (peg mouths only)",
        "Clamps, stickers, winding sticks, level, paint kit",
    ]


def drawing_index() -> list:
    return [
        {"DWG": "G-000", "TITLE": "Cover / revision / drawing index", "FILE": "G000_cover.svg"},
        {"DWG": "GA-100", "TITLE": "General arrangement (was M-1)", "FILE": "M1_general.svg"},
        {"DWG": "GA-110", "TITLE": "Elevation & rail schedule (was M-2)", "FILE": "M2_elevation.svg"},
        {"DWG": "EX-200", "TITLE": "Exploded assembly (app Walk/Explode)", "FILE": "app/"},
        {"DWG": "J-400", "TITLE": "Joinery details (was M-3)", "FILE": "M3_joinery.svg"},
        {"DWG": "GA-140", "TITLE": "Pad & piers (was M-4)", "FILE": "M4_pad_piers.svg"},
        {"DWG": "P-350", "TITLE": "Gate & latch (was M-5)", "FILE": "M5_gate_latch.svg"},
        {"DWG": "S-401", "TITLE": "Master BOM / mill buy (was M-6)", "FILE": "M6_cutlist.svg"},
        {"DWG": "S-410", "TITLE": "Shop method / stops (was M-7)", "FILE": "M7_shop.svg"},
        {"DWG": "S-420", "TITLE": "Mill grain / warpage (was M-8)", "FILE": "M8_mill.svg"},
        {"DWG": "S-402", "TITLE": "Rough + finished cut list", "FILE": "S402_cutlist.svg"},
        {"DWG": "QA-700", "TITLE": "Inspection plan", "FILE": "QA700_inspection.svg"},
        {"DWG": "P-301", "TITLE": "Post L-001…L-004", "FILE": "P301_post.svg"},
    ]


def labels(parts_list: list) -> list:
    out = []
    for p in parts_list:
        if p["MAKE_OR_BUY"] != "MAKE":
            continue
        if p["PART_CATEGORY"] in ("concrete",):
            continue
        out.append({
            "PART_ID": p["PART_ID"],
            "NAME": p["PART_NAME"],
            "QTY": p["QUANTITY"],
            "FACE": p.get("REFERENCE_FACE", ""),
            "EDGE": p.get("REFERENCE_EDGE", ""),
            "END": p.get("REFERENCE_END", ""),
            "MATES": p.get("JOINERY", ""),
            "REV": p.get("REVISION", PROJECT["REVISION"]),
        })
    return out


def inch_params() -> dict:
    """Flat inch dict for drawing generators (values only)."""
    d = {}
    for k, meta in PARAMS.items():
        d[k] = meta["value"]
    return d


def model():
    ly = layout()
    plist = parts(ly)
    buy = mill_buy()
    net_bf = round(sum(p.get("BOARD_FEET_NET") or 0 for p in plist), 2)
    proc_bf = round(sum(b["BF"] for b in buy), 2)
    return {
        "project": PROJECT,
        "parameters": PARAMS,
        "layout": ly,
        "parts": plist,
        "joints": joints(ly),
        "hardware": hardware(),
        "mill_buy": buy,
        "stock_nests": stock_nests(),
        "operations": operations(),
        "inspection": inspection(),
        "decisions": decisions(),
        "tools": tools(),
        "drawing_index": drawing_index(),
        "labels": labels(plist),
        "assemblies": {
            "A-MASTER": ["A-BASE", "A-FRAME", "A-PRIVACY", "A-GATE", "A-FINISH"],
            "A-BASE": ["C-001", "C-002", "H-010"],
            "A-FRAME": ["L-001", "L-002", "L-003", "L-004"],
            "A-PRIVACY": ["R-001", "R-002", "R-003", "R-004", "R-005", "P-C*", "K-001"],
            "A-GATE": ["G-001", "G-010", "G-020", "G-030", "H-001", "H-002", "H-003", "R-006"],
            "A-FINISH": ["F-001"],
        },
        "material": {
            "net_board_feet_finished": net_bf,
            "procurement_board_feet": proc_bf,
            "waste_factor": pv("waste_factor"),
            "implied_yield": round(net_bf / proc_bf, 3) if proc_bf else 0,
        },
        "unresolved": [
            {"ID": "U-001", "ITEM": "drop_off", "CLASS": "M", "ACTION": "Measure driveway→garden before forming C-001"},
            {"ID": "U-002", "ITEM": "Latch A vs B", "CLASS": "A", "ACTION": "Confirm house-concrete ownership / waterproofing"},
            {"ID": "U-003", "ITEM": "Hozo tenon thickness", "CLASS": "A", "ACTION": "Confirm ~0.5″ on actual leaf stock"},
            {"ID": "U-004", "ITEM": "Board course lengths", "CLASS": "D", "ACTION": "Cut after rails dry-fit — do not pre-cut all from drawing alone"},
            {"ID": "U-005", "ITEM": "Saw kerf", "CLASS": "A", "ACTION": "Measure actual TS / track-saw kerf; parameter saw_kerf"},
        ],
        "audit": {
            "MODEL_ARCHITECTURE": "WEAK→ACCEPTABLE after SSOT (was monolithic unlabelled solids)",
            "PARAMETERIZATION_QUALITY": "ACCEPTABLE (central PARAMS + derived layout)",
            "PART_SEPARATION": "GOOD in registry; CAD solids still grouped timber/concrete until FreeCAD relabel",
            "METADATA_QUALITY": "GOOD in JSON/CSV; CAD custom properties not yet attached in FreeCAD",
            "ASSEMBLY_STRUCTURE": "ACCEPTABLE (logical assemblies in data)",
            "JOINERY_STRUCTURE": "GOOD (explicit Joint IDs)",
            "DRAWING_READINESS": "ACCEPTABLE (M-series + S-402/QA-700/P-301/G-000)",
            "BOM_READINESS": "GOOD (generated from parts+mill_buy)",
            "CUT_LIST_READINESS": "GOOD",
            "EXPORT_READINESS": "ACCEPTABLE (JSON/CSV; STEP/STL remain grouped)",
            "MAJOR_RISKS": [
                "FreeCAD script still boolean-groups timber; Part IDs live in SSOT not FCStd labels",
                "drop_off unverified",
                "Historical 77″ post length conflict resolved as D-001",
            ],
            "REFACTORING_REQUIRED": "Next: label FreeCAD objects from PART_ID when regenerating FCStd",
        },
        "gates": {
            "M0": "PASS — requirements captured",
            "M1": "PASS — envelope 143×65",
            "M2": "PASS — part register",
            "M3": "PASS — joints explicit",
            "M4": "PASS — owner-tool routing",
            "M5": "PASS — assembly/walk sequence",
            "M6": "PASS — drawings + schedules",
            "M7": "PASS — QC list",
            "M8": "PASS — revision D on project + parts",
        },
    }


def _write_csv(path, rows, fieldnames=None):
    if not rows:
        return
    fieldnames = fieldnames or list(rows[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_package(m=None):
    m = m or model()
    os.makedirs(os.path.join(HERE, "07_BOM"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "08_CUT_LISTS"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "09_JOINERY"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "10_TEMPLATES"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "11_BUILD_MANUAL"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "12_QA"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "13_REVISION_HISTORY"), exist_ok=True)

    json_path = os.path.join(HERE, "martin.json")
    with open(json_path, "w") as f:
        json.dump(m, f, indent=2)
        f.write("\n")

    app_json = os.path.join(HERE, "..", "app", "martin.json")
    with open(app_json, "w") as f:
        json.dump(m, f, indent=2)
        f.write("\n")

    _write_csv(os.path.join(HERE, "07_BOM", "BOM_mill_buy.csv"), m["mill_buy"])
    _write_csv(os.path.join(HERE, "07_BOM", "BOM_parts.csv"), m["parts"])
    _write_csv(os.path.join(HERE, "07_BOM", "hardware.csv"), m["hardware"])
    _write_csv(os.path.join(HERE, "08_CUT_LISTS", "finished.csv"), [
        {k: p[k] for k in ("PART_ID", "PART_NAME", "QUANTITY", "MATERIAL",
                           "FINISHED_THICKNESS", "FINISHED_WIDTH", "FINISHED_LENGTH", "NOTES")
         if k in p}
        for p in m["parts"] if p["MAKE_OR_BUY"] == "MAKE" and p["PART_CATEGORY"] not in ("concrete",)
    ])
    _write_csv(os.path.join(HERE, "08_CUT_LISTS", "rough.csv"), [
        {k: p[k] for k in ("PART_ID", "PART_NAME", "QUANTITY", "PURCHASE",
                           "ROUGH_THICKNESS", "ROUGH_WIDTH", "ROUGH_LENGTH", "PROCESS")
         if k in p}
        for p in m["parts"] if p["MAKE_OR_BUY"] == "MAKE" and p["PART_CATEGORY"] not in ("concrete",)
    ])
    _write_csv(os.path.join(HERE, "08_CUT_LISTS", "stock_nests.csv"), m["stock_nests"])
    _write_csv(os.path.join(HERE, "09_JOINERY", "joints.csv"), m["joints"])
    _write_csv(os.path.join(HERE, "11_BUILD_MANUAL", "routing.csv"), m["operations"])
    _write_csv(os.path.join(HERE, "12_QA", "inspection.csv"), m["inspection"])
    _write_csv(os.path.join(HERE, "10_TEMPLATES", "labels.csv"), m["labels"])

    with open(os.path.join(HERE, "13_REVISION_HISTORY", "REVISIONS.md"), "w") as f:
        f.write("# MARTIN revision history\n\n")
        f.write("| Rev | Notes |\n|-----|-------|\n")
        f.write("| A | Initial geometry / hardware-store BOM |\n")
        f.write("| B | Owner-tool sequence (Festool / Bridge City / Zenwu) |\n")
        f.write("| C | Mill-stock 6×6 / 2×12 / 1×12 + grain rules |\n")
        f.write("| D | Parametric fabrication SSOT: part/joint IDs, derived post length 75.5″ (D-001), JSON/CSV package |\n")

    # OpenSCAD parameters (inch units documented)
    scad = os.path.join(HERE, "..", "cad", "parameters.scad")
    ly = m["layout"]
    with open(scad, "w") as f:
        f.write("// AUTO-GENERATED from martin_ssot.py — do not edit by hand\n")
        f.write("// Units: inches. Rev " + PROJECT["REVISION"] + "\n")
        f.write(f"overall_length = {pv('overall_length')};\n")
        f.write(f"overall_height = {pv('overall_height')};\n")
        f.write(f"post_x = {pv('post_x')};\npost_y = {pv('post_y')};\n")
        f.write(f"gate_clear = {pv('gate_clear')};\n")
        f.write(f"rail_t = {pv('rail_t')};\nrail_h = {pv('rail_h')};\n")
        f.write(f"post_finished_length = {ly['post_finished_length']};\n")
        f.write(f"nuki_length = {ly['nuki_length']};\n")
        f.write(f"bay_clear = {ly['bay_clear']};\n")
        f.write(f"mortise_width = {ly['mortise_width']};\n")
        f.write(f"mortise_height = {ly['mortise_height']};\n")

    meta = os.path.join(HERE, "..", "cad", "metadata.scad")
    with open(meta, "w") as f:
        f.write("// AUTO-GENERATED part echo for external parsers\n")
        f.write("include <parameters.scad>;\n")
        for p in m["parts"]:
            if p["MAKE_OR_BUY"] != "MAKE":
                continue
            f.write(
                f'echo("PART", "{p["PART_ID"]}", "{p["PART_NAME"]}", {p["QUANTITY"]}, '
                f'"{p["MATERIAL"]}", {p.get("FINISHED_THICKNESS", 0)}, '
                f'{p.get("FINISHED_WIDTH", 0)}, {p.get("FINISHED_LENGTH", 0)});\n'
            )

    return json_path


if __name__ == "__main__":
    m = model()
    path = write_package(m)
    print("MARTIN SSOT", PROJECT["REVISION"], "→", path)
    print("post_finished_length", m["layout"]["post_finished_length"])
    print("nuki_length", m["layout"]["nuki_length"])
    print("bay_clear", m["layout"]["bay_clear"])
    print("parts", len(m["parts"]), "joints", len(m["joints"]))
    print("procurement_bf", m["material"]["procurement_board_feet"])
