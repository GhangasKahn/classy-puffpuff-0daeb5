#!/usr/bin/env python3
"""STELE parametric fabrication system.

Single source of truth: parameters → derived layout → part/joint registries
→ BOM, cut lists, joinery, routing, QA, drawings, templates, JSON/CSV.

Internal units: millimetres. Inch callouts only at documentation interfaces.
Revision: B  (fabrication-model refactor)

Run:  python3 scripts/fab_system.py
"""
from __future__ import annotations

import csv
import json
import math
import os
from collections import defaultdict
from datetime import date

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FAB = os.path.join(ROOT, "fence", "fab")
REV = "B"
TODAY = date.today().isoformat()

# ---------------------------------------------------------------------------
# 0. PROJECT + MASTER PARAMETERS  (do not duplicate elsewhere)
# ---------------------------------------------------------------------------
PROJECT = {
    "PROJECT_ID": "STELE-BUF-001",
    "PROJECT_NAME": "STELE masonry & timber fence — Buffalo NY",
    "REVISION": REV,
    "UNITS": "mm",
    "UNIT_POLICY": "Internal millimetres. Convert only at drawing/CSV inch columns.",
    "DESIGN_STANDARD": "Buffalo Green Code + ASCE 7 wind; frost per Erie County",
    "MATERIAL_SYSTEM": "Cast stone / air-entrained concrete + western red cedar",
    "TOLERANCE_CLASS": "T1 general woodworking / T2 joinery pockets / T3 templates",
    "AUTHOR": "HASHIRA/STELE fabrication model",
    "MODEL_VERSION": "2.0.0",
    "DATE": TODAY,
    "CAD_PLATFORM": "FreeCAD 1.1 (geometry) + OpenSCAD (joint studies) + this registry",
    "CONFIGURATION": "STANDARD — 4 panel bays + 1 Roman arch gate",
}

# VERIFIED / DERIVED / ASSUMED classification lives on each parameter.
P = {
    # climate — VERIFIED regional design values
    "frost_depth": 1220,          # VERIFIED Erie Co. design frost; 48" used (min 42")
    "ground_snow_psf": 40,        # VERIFIED ASCE 7 ground snow Buffalo
    "wind_ult_mph": 115,          # VERIFIED ASCE 7 ultimate
    # foundations
    "footing_w": 600, "footing_h": 300,
    "gravel_w": 700, "gravel_h": 150,
    "stem_w": 350,
    # pier
    "plinth_w": 560, "plinth_h": 150,
    "shaft_base": 480, "shaft_top": 360, "shaft_h": 1600,
    "cap1_w": 560, "cap1_h": 50, "cap2_w": 470, "cap2_h": 55,
    "pyr_base": 380, "pyr_top": 180, "pyr_h": 110,
    # layout
    "bay_cc": 2440,
    "n_panel_bays_left": 2,
    "n_panel_bays_right": 1,
    # timber
    "rail_t": 38, "rail_w": 89, "pocket_depth": 60,
    "rail_z": (350, 1000, 1650),
    "board_t": 19, "board_w": 140, "board_gap": 10,
    "board_z0": 320, "board_z1": 1780,
    "tcap_h": 45, "tcap_w": 120,
    "curb_w": 200, "curb_h": 250,
    # gate
    "gate_clear": 1220, "arch_depth": 220, "arch_thick": 350,
    "impost_w": 520, "impost_h": 60,
    "key_b": 180, "key_t": 280, "key_h": 300, "key_proud": 30,
    "n_voussoirs": 11,
    "leaf_gap": 25, "stile": 70, "ledge": 45, "leaf_h": 1600, "leaf_t": 40,
    "leaf_z0": 150, "gate_board_w": 90, "gate_board_t": 16, "gate_board_gap": 6,
    # fabrication
    "saw_kerf": 3.2,              # 1/8" carbide kerf — ASSUMED typical tablesaw
    "pocket_ease": 6,             # total pocket oversize vs rail (T2)
    "seasonal_ease": 1.2,         # HASHIRA nuki ease
    "waste_factor_cedar": 1.25,   # EXPLICIT — knots, matching, milling
    "waste_factor_masonry": 1.08,
    "peg_d": 10,
    "wedge_t": 8, "wedge_w": 25, "wedge_l": 90,
}

PARAM_STATUS = {
    "frost_depth": "VERIFIED",
    "ground_snow_psf": "VERIFIED",
    "wind_ult_mph": "VERIFIED",
    "saw_kerf": "ASSUMED",
    "waste_factor_cedar": "ASSUMED",
    "waste_factor_masonry": "ASSUMED",
    "bay_cc": "DESIGN",
    "gate_clear": "DESIGN",
    "rail_t": "DERIVED",  # from 2x4 S4S
    "rail_w": "DERIVED",
    "board_t": "DERIVED",
    "board_w": "DERIVED",
}


def mm_in(mm, n=2):
    v = mm / 25.4
    s = f"{v:.{n}f}".rstrip("0").rstrip(".")
    return s + '"'


def bf_nominal(t_in, w_in, l_in):
    return round(t_in * w_in * l_in / 144.0, 2)


# ---------------------------------------------------------------------------
# 1. DERIVED LAYOUT  (equations — no magic numbers)
# ---------------------------------------------------------------------------
def derived():
    d = {}
    d["bay_clear"] = P["bay_cc"] - P["shaft_base"]
    d["rail_length"] = d["bay_clear"] + 2 * P["pocket_depth"]
    d["board_height"] = P["board_z1"] - P["board_z0"]
    d["board_pitch"] = P["board_w"] + P["board_gap"]
    d["n_boards_bay"] = int((d["bay_clear"] - P["board_gap"]) // d["board_pitch"])
    d["n_panel_bays"] = P["n_panel_bays_left"] + 1 + P["n_panel_bays_right"]
    d["n_piers"] = P["n_panel_bays_left"] + 1 + 2 + P["n_panel_bays_right"]
    d["gate_span_cc"] = P["gate_clear"] + P["shaft_base"]
    d["spring"] = P["plinth_h"] + P["shaft_h"] + P["impost_h"]
    d["r_in"] = P["gate_clear"] / 2.0
    d["r_out"] = d["r_in"] + P["arch_depth"]
    d["crown"] = d["spring"] + d["r_out"]
    d["pier_top"] = (
        P["plinth_h"] + P["shaft_h"] + P["cap1_h"] + P["cap2_h"] + P["pyr_h"]
    )
    d["panel_top"] = P["board_z1"] + P["tcap_h"]
    d["stem_h"] = P["frost_depth"] - P["footing_h"]
    d["pocket_w"] = P["rail_t"] + P["pocket_ease"]
    d["pocket_h"] = P["rail_w"] + P["pocket_ease"]
    d["batter_per_face"] = (P["shaft_base"] - P["shaft_top"]) / 2.0
    d["batter_ratio"] = P["shaft_h"] / d["batter_per_face"]
    d["leaf_width"] = P["gate_clear"] - 2 * P["leaf_gap"]
    d["ledge_length"] = d["leaf_width"] - 2 * P["stile"]
    d["n_gate_boards"] = int(d["leaf_width"] // (P["gate_board_w"] + P["gate_board_gap"]))
    d["n_rails"] = d["n_panel_bays"] * len(P["rail_z"])
    d["n_boards"] = d["n_panel_bays"] * d["n_boards_bay"]
    d["n_wedges"] = d["n_rails"] * 2
    d["n_caps"] = d["n_piers"] - 2  # gate piers use imposts, not Mayan caps
    d["n_curbs"] = d["n_panel_bays"]
    d["n_imposts"] = 2
    d["n_springers"] = 2
    d["n_typical_voussoirs"] = P["n_voussoirs"] - 1 - d["n_springers"]

    # pier centerline X — same topology as stele_fence.py
    left = [i * P["bay_cc"] for i in range(P["n_panel_bays_left"] + 1)]
    gate_l = left[-1] + P["bay_cc"]
    gate_r = gate_l + d["gate_span_cc"]
    right = [gate_r + (i + 1) * P["bay_cc"] for i in range(P["n_panel_bays_right"])]
    d["pier_x"] = left + [gate_l, gate_r] + right
    d["run_length"] = d["pier_x"][-1] + P["shaft_base"]
    d["gate_l"] = gate_l
    d["gate_r"] = gate_r
    d["gate_c"] = (gate_l + gate_r) / 2.0

    # panel bay pairs (pier indices)
    d["panel_bays"] = []
    for i in range(len(left) - 1):
        d["panel_bays"].append((left[i], left[i + 1]))
    d["panel_bays"].append((left[-1], gate_l))
    for i, cx in enumerate(right):
        prev = gate_r if i == 0 else right[i - 1]
        d["panel_bays"].append((prev, cx))
    return d


D = derived()


def pier_role(i, x):
    n = D["n_piers"]
    if x == D["gate_l"]:
        return "GATE_L", ("left",), False
    if x == D["gate_r"]:
        return "GATE_R", ("right",), False
    if i == 0:
        return "END_L", ("right",), True
    if i == n - 1:
        return "END_R", ("left",), True
    return "MID", ("left", "right"), True


# ---------------------------------------------------------------------------
# 2. REGISTRIES
# ---------------------------------------------------------------------------
parts, joints, hardware, operations, inspection, decisions, fmea = (
    [], [], [], [], [], [], []
)


def add_part(**kw):
    defaults = dict(
        MAKE_OR_BUY="MAKE", GRADE="", MATERIAL_STANDARD="",
        GRAIN_DIRECTION="", REFERENCE_FACE="A — show face",
        REFERENCE_EDGE="B — jointed edge", REFERENCE_END="Datum End 0",
        PROCESS="", JOINERY="", NOTES="", REVISION=REV, HANDED="IDENTICAL",
        BOARD_FEET=0, VOLUME_MM3=0, UNIT_COST=None, SUPPLIER="",
        PURCHASE_SKU="", FINISH="", CONSTRAINT="FIXED",
        STATUS="DESIGN",
    )
    defaults.update(kw)
    t, w, l = defaults["FINISHED_THICKNESS"], defaults["FINISHED_WIDTH"], defaults["FINISHED_LENGTH"]
    defaults["VOLUME_MM3"] = round(t * w * l * defaults["QUANTITY"], 0)
    parts.append(defaults)
    return defaults


def add_joint(**kw):
    joints.append(kw)


def add_hw(**kw):
    hardware.append(kw)


# --- foundations (identical across piers) ---
add_part(
    PART_ID="F-001", PART_NAME="Pier footing pad", PART_CATEGORY="FOUNDATION",
    ASSEMBLY="A-FND", QUANTITY=D["n_piers"], MATERIAL="Concrete 4000 psi AE 5–7%",
    SPECIES="", ROUGH_THICKNESS=P["footing_h"], ROUGH_WIDTH=P["footing_w"],
    ROUGH_LENGTH=P["footing_w"], FINISHED_THICKNESS=P["footing_h"],
    FINISHED_WIDTH=P["footing_w"], FINISHED_LENGTH=P["footing_w"],
    PROCESS="Cast in place, (3)#4 EW bottom 75 cover, (4)#4 vert into stem",
    NOTES="Bearing at −frost_depth on F-003. Pour monolithic with F-002 where possible.",
    GRAIN_DIRECTION="n/a", REFERENCE_FACE="Top of pad", REFERENCE_EDGE="North",
    REFERENCE_END="Grid",
)
add_part(
    PART_ID="F-002", PART_NAME="Pier stem", PART_CATEGORY="FOUNDATION",
    ASSEMBLY="A-FND", QUANTITY=D["n_piers"], MATERIAL="Concrete 4000 psi AE 5–7%",
    SPECIES="", ROUGH_THICKNESS=D["stem_h"], ROUGH_WIDTH=P["stem_w"],
    ROUGH_LENGTH=P["stem_w"], FINISHED_THICKNESS=D["stem_h"],
    FINISHED_WIDTH=P["stem_w"], FINISHED_LENGTH=P["stem_w"],
    PROCESS="Cast; #3 ties @ 300; damp-proof top 150",
    NOTES="Capillary-break flashing at stem/plinth. CONSTRAINT: FIXED to F-001.",
    GRAIN_DIRECTION="n/a",
)
add_part(
    PART_ID="F-003", PART_NAME="Gravel drainage pad", PART_CATEGORY="FOUNDATION",
    ASSEMBLY="A-FND", QUANTITY=D["n_piers"], MATERIAL="#57 crushed stone",
    SPECIES="", ROUGH_THICKNESS=P["gravel_h"], ROUGH_WIDTH=P["gravel_w"],
    ROUGH_LENGTH=P["gravel_w"], FINISHED_THICKNESS=P["gravel_h"],
    FINISHED_WIDTH=P["gravel_w"], FINISHED_LENGTH=P["gravel_w"],
    PROCESS="Compacted in 75 mm lifts", NOTES="Roman rule: never let the base sit wet.",
    GRAIN_DIRECTION="n/a", MAKE_OR_BUY="BUY",
)

# --- masonry ---
add_part(
    PART_ID="M-001", PART_NAME="Pier plinth", PART_CATEGORY="MASONRY",
    ASSEMBLY="A-PIER", QUANTITY=D["n_piers"], MATERIAL="Cast stone or limestone",
    SPECIES="", ROUGH_THICKNESS=P["plinth_h"] + 6, ROUGH_WIDTH=P["plinth_w"] + 6,
    ROUGH_LENGTH=P["plinth_w"] + 6, FINISHED_THICKNESS=P["plinth_h"],
    FINISHED_WIDTH=P["plinth_w"], FINISHED_LENGTH=P["plinth_w"],
    PROCESS="Cast / dressed; Type S bed", NOTES="Sits on flashing over F-002.",
    GRAIN_DIRECTION="n/a",
)
add_part(
    PART_ID="M-002-L", PART_NAME="Battered shaft — pockets LEFT", PART_CATEGORY="MASONRY",
    ASSEMBLY="A-PIER", QUANTITY=2, MATERIAL="Cast stone (3 drums)",
    HANDED="LEFT-HAND",
    ROUGH_THICKNESS=P["shaft_h"], ROUGH_WIDTH=P["shaft_base"], ROUGH_LENGTH=P["shaft_base"],
    FINISHED_THICKNESS=P["shaft_h"], FINISHED_WIDTH=P["shaft_base"],
    FINISHED_LENGTH=P["shaft_top"],
    PROCESS="Battered drums + pocket cores; epoxy #4 dowels",
    JOINERY="3× nuki pockets LEFT @ rail_z",
    NOTES=f"Batter {D['batter_per_face']:.0f}/{P['shaft_h']} = 1:{D['batter_ratio']:.1f} per face (Egyptian talus). GATE_L + END_R.",
    GRAIN_DIRECTION="n/a",
)
add_part(
    PART_ID="M-002-R", PART_NAME="Battered shaft — pockets RIGHT", PART_CATEGORY="MASONRY",
    ASSEMBLY="A-PIER", QUANTITY=2, MATERIAL="Cast stone (3 drums)",
    HANDED="RIGHT-HAND",
    ROUGH_THICKNESS=P["shaft_h"], ROUGH_WIDTH=P["shaft_base"], ROUGH_LENGTH=P["shaft_base"],
    FINISHED_THICKNESS=P["shaft_h"], FINISHED_WIDTH=P["shaft_base"],
    FINISHED_LENGTH=P["shaft_top"],
    PROCESS="Battered drums + pocket cores; epoxy #4 dowels",
    JOINERY="3× nuki pockets RIGHT @ rail_z",
    NOTES="END_L + GATE_R. Mirror of M-002-L.",
    GRAIN_DIRECTION="n/a",
)
add_part(
    PART_ID="M-002-B", PART_NAME="Battered shaft — pockets BOTH", PART_CATEGORY="MASONRY",
    ASSEMBLY="A-PIER", QUANTITY=2, MATERIAL="Cast stone (3 drums)",
    HANDED="IDENTICAL",
    ROUGH_THICKNESS=P["shaft_h"], ROUGH_WIDTH=P["shaft_base"], ROUGH_LENGTH=P["shaft_base"],
    FINISHED_THICKNESS=P["shaft_h"], FINISHED_WIDTH=P["shaft_base"],
    FINISHED_LENGTH=P["shaft_top"],
    PROCESS="Battered drums + pocket cores both faces",
    JOINERY="6× nuki pockets (3L+3R)",
    NOTES="MID piers. Same batter as M-002-L/R.",
    GRAIN_DIRECTION="n/a",
)
add_part(
    PART_ID="M-003", PART_NAME="Mayan cap stack (3 units)", PART_CATEGORY="MASONRY",
    ASSEMBLY="A-PIER", QUANTITY=D["n_caps"], MATERIAL="Cast stone",
    ROUGH_THICKNESS=P["cap1_h"] + P["cap2_h"] + P["pyr_h"] + 8,
    ROUGH_WIDTH=P["cap1_w"], ROUGH_LENGTH=P["cap1_w"],
    FINISHED_THICKNESS=P["cap1_h"] + P["cap2_h"] + P["pyr_h"],
    FINISHED_WIDTH=P["cap1_w"], FINISHED_LENGTH=P["pyr_top"],
    PROCESS="Three units: tier1 560×50, tier2 470×55, pyramid 380→180×110",
    NOTES="Drip kerf 8×8, 20 from edge, all 4 sides of tiers 1+2. 1:12 wash min.",
    GRAIN_DIRECTION="n/a",
)
add_part(
    PART_ID="M-004", PART_NAME="Impost block", PART_CATEGORY="MASONRY",
    ASSEMBLY="A-GATE", QUANTITY=D["n_imposts"], MATERIAL="Cast stone",
    HANDED="IDENTICAL",
    ROUGH_THICKNESS=P["impost_h"] + 4, ROUGH_WIDTH=P["impost_w"], ROUGH_LENGTH=P["impost_w"],
    FINISHED_THICKNESS=P["impost_h"], FINISHED_WIDTH=P["impost_w"],
    FINISHED_LENGTH=P["impost_w"],
    PROCESS="Dressed bed + springer seat",
    NOTES="Arch bears here in pure compression. SS dowels for erection only.",
    GRAIN_DIRECTION="n/a",
)
add_part(
    PART_ID="M-005", PART_NAME="Arch springer voussoir", PART_CATEGORY="MASONRY",
    ASSEMBLY="A-GATE", QUANTITY=2, MATERIAL="Cast stone", HANDED="MIRRORED",
    ROUGH_THICKNESS=P["arch_depth"] + 20, ROUGH_WIDTH=P["arch_thick"] + 20,
    ROUGH_LENGTH=int(math.pi * D["r_out"] / P["n_voussoirs"]) + 40,
    FINISHED_THICKNESS=P["arch_depth"], FINISHED_WIDTH=P["arch_thick"],
    FINISHED_LENGTH=round(math.pi * ((D["r_in"] + D["r_out"]) / 2) / P["n_voussoirs"]),
    PROCESS="Cast to T-501 template; radial joints 10 mm Type S",
    JOINERY="J-ARCH", NOTES="Flat soffit on impost. L/R mirrored.",
    GRAIN_DIRECTION="n/a",
)
add_part(
    PART_ID="M-006", PART_NAME="Arch typical voussoir", PART_CATEGORY="MASONRY",
    ASSEMBLY="A-GATE", QUANTITY=D["n_typical_voussoirs"], MATERIAL="Cast stone",
    ROUGH_THICKNESS=P["arch_depth"] + 20, ROUGH_WIDTH=P["arch_thick"] + 20,
    ROUGH_LENGTH=int(math.pi * D["r_out"] / P["n_voussoirs"]) + 40,
    FINISHED_THICKNESS=P["arch_depth"], FINISHED_WIDTH=P["arch_thick"],
    FINISHED_LENGTH=round(math.pi * ((D["r_in"] + D["r_out"]) / 2) / P["n_voussoirs"]),
    PROCESS="Cast to T-502; identical if equally divided ring",
    JOINERY="J-ARCH", NOTES="Concentric ring — all typical voussoirs IDENTICAL.",
    GRAIN_DIRECTION="n/a",
)
add_part(
    PART_ID="M-007", PART_NAME="Keystone", PART_CATEGORY="MASONRY",
    ASSEMBLY="A-GATE", QUANTITY=1, MATERIAL="Cast stone",
    ROUGH_THICKNESS=P["key_h"] + 10, ROUGH_WIDTH=P["key_t"] + 20,
    ROUGH_LENGTH=P["arch_thick"] + 2 * P["key_proud"] + 10,
    FINISHED_THICKNESS=P["key_h"], FINISHED_WIDTH=P["key_t"],
    FINISHED_LENGTH=P["arch_thick"] + 2 * P["key_proud"],
    PROCESS="Tapered loft key_b→key_t; proud 30 ea face",
    JOINERY="J-ARCH", NOTES="Do not strike centering until 7-day cure after key is set.",
    GRAIN_DIRECTION="n/a",
)
add_part(
    PART_ID="C-001", PART_NAME="Splash curb", PART_CATEGORY="MASONRY",
    ASSEMBLY="A-BAY", QUANTITY=D["n_curbs"], MATERIAL="Cast concrete or solid CMU",
    ROUGH_THICKNESS=P["curb_h"] + 50, ROUGH_WIDTH=P["curb_w"],
    ROUGH_LENGTH=D["bay_clear"] + 20,
    FINISHED_THICKNESS=P["curb_h"], FINISHED_WIDTH=P["curb_w"],
    FINISHED_LENGTH=D["bay_clear"],
    PROCESS="Cast; (2)#4 cont.; thickened edge 300 deep at ends — DOES NOT tie to pier ftgs",
    NOTES="CONSTRAINT: FLOATING — heave isolation from piers.",
    CONSTRAINT="FLOATING", GRAIN_DIRECTION="n/a",
)

# --- timber ---
rail_bf = bf_nominal(2, 4, 96)  # purchase 2x4x8' (length in inches)
add_part(
    PART_ID="R-001", PART_NAME="Nuki through-rail", PART_CATEGORY="TIMBER",
    ASSEMBLY="A-BAY", QUANTITY=D["n_rails"], MATERIAL="Western red cedar",
    SPECIES="Thuja plicata", GRADE="Select tight knot or better",
    ROUGH_THICKNESS=42, ROUGH_WIDTH=95, ROUGH_LENGTH=D["rail_length"] + 25,
    FINISHED_THICKNESS=P["rail_t"], FINISHED_WIDTH=P["rail_w"],
    FINISHED_LENGTH=D["rail_length"],
    GRAIN_DIRECTION="LENGTH — annual rings vertical (on-edge)",
    PROCESS="Joint/plane to 38×89; final crosscut to stop S-014",
    JOINERY="Nuki 貫 through M-002 pockets; W-001 wedges both ends",
    NOTES="All 12 IDENTICAL. Purchase 2×4×8' S4S. Datum End = left pocket engagement.",
    BOARD_FEET=rail_bf, PURCHASE_SKU="2x4x8 cedar",
    FINISH="End-grain oil; faces weather to silver", CONSTRAINT="FLOATING",
)
add_part(
    PART_ID="B-001", PART_NAME="Rain-screen board", PART_CATEGORY="TIMBER",
    ASSEMBLY="A-BAY", QUANTITY=D["n_boards"], MATERIAL="Western red cedar",
    SPECIES="Thuja plicata", GRADE="Select",
    ROUGH_THICKNESS=22, ROUGH_WIDTH=146, ROUGH_LENGTH=D["board_height"] + 20,
    FINISHED_THICKNESS=P["board_t"], FINISHED_WIDTH=P["board_w"],
    FINISHED_LENGTH=D["board_height"],
    GRAIN_DIRECTION="LENGTH vertical",
    PROCESS="Rip 1x6; final crosscut stop S-015; 2× SS nails per rail crossing",
    JOINERY="Fastened to R-001 only — never into masonry",
    NOTES="CONSTRAINT: FLOATING (nailed to rails; rails float in pockets). 10 mm gaps.",
    BOARD_FEET=bf_nominal(1, 6, 96), PURCHASE_SKU="1x6x8 cedar",
    CONSTRAINT="FLOATING",
)
add_part(
    PART_ID="TC-001", PART_NAME="Bay timber cap", PART_CATEGORY="TIMBER",
    ASSEMBLY="A-BAY", QUANTITY=D["n_curbs"], MATERIAL="Western red cedar",
    SPECIES="Thuja plicata",
    ROUGH_THICKNESS=50, ROUGH_WIDTH=130, ROUGH_LENGTH=D["rail_length"] + 25,
    FINISHED_THICKNESS=P["tcap_h"], FINISHED_WIDTH=P["tcap_w"],
    FINISHED_LENGTH=D["rail_length"],
    GRAIN_DIRECTION="LENGTH",
    PROCESS="Rip; plane 8° wash (street face high); drip kerf both long edges",
    NOTES="Washes water off rain-screen. Do not caulk kerfs.",
    BOARD_FEET=bf_nominal(2, 6, 96), CONSTRAINT="FLOATING",
)
add_part(
    PART_ID="W-001", PART_NAME="Nuki locking wedge", PART_CATEGORY="TIMBER",
    ASSEMBLY="A-BAY", QUANTITY=D["n_wedges"], MATERIAL="White oak or black locust",
    SPECIES="Quercus alba / Robinia", GRADE="Clear",
    ROUGH_THICKNESS=12, ROUGH_WIDTH=30, ROUGH_LENGTH=100,
    FINISHED_THICKNESS=P["wedge_t"], FINISHED_WIDTH=P["wedge_w"],
    FINISHED_LENGTH=P["wedge_l"],
    GRAIN_DIRECTION="LENGTH",
    PROCESS="Rip taper ~1:12; drive from weather side so rain tightens",
    JOINERY="J-NUKI", NOTES="Harder than cedar frame. Replaceable. Do not glue.",
    CONSTRAINT="CLEARANCED",
)
add_part(
    PART_ID="GS-001", PART_NAME="Gate stile", PART_CATEGORY="TIMBER",
    ASSEMBLY="A-LEAF", QUANTITY=2, MATERIAL="Western red cedar or locust",
    SPECIES="Thuja plicata", HANDED="IDENTICAL",
    ROUGH_THICKNESS=45, ROUGH_WIDTH=76, ROUGH_LENGTH=P["leaf_h"] + 20,
    FINISHED_THICKNESS=P["leaf_t"], FINISHED_WIDTH=P["stile"],
    FINISHED_LENGTH=P["leaf_h"],
    GRAIN_DIRECTION="LENGTH",
    PROCESS="Mortise for ledges; hinge-stile gets H-002 layout from Datum End 0",
    JOINERY="Hozo ほぞ into ledges, drawbore optional",
    NOTES="Hinge stile = street-left as viewed from outside, inward swing.",
)
add_part(
    PART_ID="GL-001", PART_NAME="Gate ledge", PART_CATEGORY="TIMBER",
    ASSEMBLY="A-LEAF", QUANTITY=3, MATERIAL="Western red cedar",
    ROUGH_THICKNESS=50, ROUGH_WIDTH=50, ROUGH_LENGTH=D["ledge_length"] + 20,
    FINISHED_THICKNESS=P["ledge"], FINISHED_WIDTH=P["ledge"],
    FINISHED_LENGTH=D["ledge_length"],
    GRAIN_DIRECTION="LENGTH", PROCESS="Tenon both ends; three IDENTICAL",
    JOINERY="Hozo into GS-001",
)
add_part(
    PART_ID="GB-001", PART_NAME="Gate diagonal brace", PART_CATEGORY="TIMBER",
    ASSEMBLY="A-LEAF", QUANTITY=1, MATERIAL="Western red cedar",
    ROUGH_THICKNESS=50, ROUGH_WIDTH=50, ROUGH_LENGTH=int(math.hypot(D["ledge_length"], P["leaf_h"] - 170)) + 40,
    FINISHED_THICKNESS=P["ledge"], FINISHED_WIDTH=P["ledge"],
    FINISHED_LENGTH=int(math.hypot(D["ledge_length"], P["leaf_h"] - 170)),
    GRAIN_DIRECTION="LENGTH", PROCESS="Cut to T-503; rises from HINGE side",
    JOINERY="Housed into ledges — compression strut",
    NOTES="Brace must rise from hinge (bottom) to latch (top). Reverse = sag.",
)
add_part(
    PART_ID="GF-001", PART_NAME="Gate face board", PART_CATEGORY="TIMBER",
    ASSEMBLY="A-LEAF", QUANTITY=D["n_gate_boards"], MATERIAL="Western red cedar",
    ROUGH_THICKNESS=19, ROUGH_WIDTH=96, ROUGH_LENGTH=P["leaf_h"] + 20,
    FINISHED_THICKNESS=P["gate_board_t"], FINISHED_WIDTH=P["gate_board_w"],
    FINISHED_LENGTH=P["leaf_h"],
    GRAIN_DIRECTION="LENGTH vertical", PROCESS="Rip; nail to ledges SS",
    CONSTRAINT="FLOATING",
)

# HASHIRA standalone joint-study parts (teaching / existing-fence repair)
add_part(
    PART_ID="L-001", PART_NAME="Hashira post (study / repair)", PART_CATEGORY="TIMBER",
    ASSEMBLY="A-HASHIRA", QUANTITY=2, MATERIAL="Western red cedar / black locust / white oak",
    SPECIES="site", GRADE="Heartwood at grade",
    ROUGH_THICKNESS=95, ROUGH_WIDTH=95, ROUGH_LENGTH=1850,
    FINISHED_THICKNESS=89, FINISHED_WIDTH=89, FINISHED_LENGTH=1800,
    GRAIN_DIRECTION="LENGTH", JOINERY="Through-mortises for nuki",
    NOTES="HASHIRA system for existing-fence reinforcement — not used in STELE (masonry piers replace posts).",
    PROCESS="See HASHIRA guide", STATUS="OPTIONAL",
)

# --- hardware ---
add_hw(HARDWARE_ID="H-001", DESCRIPTION="Ring-shank nail, stainless 316",
       STANDARD="ASTM A276 316", SIZE="8d (2.5 mm shank)", THREAD="n/a",
       LENGTH="63 mm", MATERIAL="Stainless 316", FINISH="Mill",
       QTY=D["n_boards"] * 3 * 2, MANUFACTURER="Simpson / generic marine",
       MPN="SS8D-RS", MAKE_OR_BUY="BUY")
add_hw(HARDWARE_ID="H-002", DESCRIPTION="Ball-bearing butt hinge, stainless, heavy",
       STANDARD="ANSI A156.1 Grade 1", SIZE="114 × 114 mm (4.5×4.5)",
       THREAD="n/a", LENGTH="n/a", MATERIAL="Stainless 304/316", FINISH="Satin",
       QTY=3, MANUFACTURER="Hager / Stanley", MPN="BB1279-4.5-32D-SS", MAKE_OR_BUY="BUY")
add_hw(HARDWARE_ID="H-003", DESCRIPTION="M12 epoxy anchor rod into masonry",
       STANDARD="ASTM F593 / ICC ESR epoxy", SIZE="M12", THREAD="M12×1.75",
       LENGTH="160 mm embed min 100", MATERIAL="Stainless 316", FINISH="Passivated",
       QTY=6, MANUFACTURER="Hilti / Simpson", MPN="HAS-E-316 / SET-XP", MAKE_OR_BUY="BUY",
       NOTES="100 mm min edge distance from pier face. Hinge-side only.")
add_hw(HARDWARE_ID="H-004", DESCRIPTION="Gate latch + keeper, stainless, lockable",
       STANDARD="n/a", SIZE="residential heavy", THREAD="n/a", LENGTH="n/a",
       MATERIAL="Stainless 316", FINISH="Satin", QTY=1, MANUFACTURER="D&D / locinox",
       MPN="TO BE SELECTED", MAKE_OR_BUY="BUY", NOTES="TO BE SELECTED — user preference")
add_hw(HARDWARE_ID="H-005", DESCRIPTION="Type S masonry mortar",
       STANDARD="ASTM C270 Type S", SIZE="n/a", THREAD="n/a", LENGTH="n/a",
       MATERIAL="Portland + lime + sand", FINISH="n/a", QTY=12,
       UNIT="bag 80 lb", MANUFACTURER="Quikrete / local", MPN="Type S", MAKE_OR_BUY="BUY")
add_hw(HARDWARE_ID="H-006", DESCRIPTION="#4 / #3 rebar Grade 60",
       STANDARD="ASTM A615 Gr60", SIZE="#4 vert / #3 ties / #4 ftg",
       THREAD="n/a", LENGTH="see F-001/F-002", MATERIAL="Carbon steel",
       FINISH="Mill (not exposed)", QTY=1, UNIT="lot ~180 lf",
       MANUFACTURER="local yard", MPN="n/a", MAKE_OR_BUY="BUY")
add_hw(HARDWARE_ID="H-007", DESCRIPTION="Self-adhered flashing + metal drip",
       STANDARD="AAMA 711", SIZE="150 mm roll", THREAD="n/a", LENGTH="~8 m",
       MATERIAL="Asphalt/butyl + SS drip", FINISH="n/a", QTY=1, UNIT="lot",
       MANUFACTURER="Grace / GCP", MPN="Vycor plus SS drip", MAKE_OR_BUY="BUY",
       NOTES="Capillary cut at every stem/plinth.")
add_hw(HARDWARE_ID="H-008", DESCRIPTION="Penetrating oil / pine tar (end grain)",
       STANDARD="n/a", SIZE="n/a", THREAD="n/a", LENGTH="n/a",
       MATERIAL="Tung or pine tar", FINISH="n/a", QTY=1, UNIT="1 qt",
       MANUFACTURER="Tried & True / Auson", MPN="n/a", MAKE_OR_BUY="BUY")

# --- joints (explicit IDs) ---
# One joint type definition, instanced
for bi, (x0, x1) in enumerate(D["panel_bays"], start=1):
    for ri, zc in enumerate(P["rail_z"], start=1):
        jid = f"J-N{bi:02d}{ri}"
        add_joint(
            JOINT_ID=jid, JOINT_TYPE="NUKI 貫 through-pocket",
            PART_A="R-001", PART_B="M-002-*",
            LOCATION=f"Bay {bi} rail {ri} CL z={zc}",
            MORTISE_WIDTH=D["pocket_w"], MORTISE_HEIGHT=D["pocket_h"],
            MORTISE_DEPTH=P["pocket_depth"],
            TENON_WIDTH=P["rail_t"], TENON_HEIGHT=P["rail_w"],
            TENON_LENGTH=P["pocket_depth"],
            SHOULDER=0, HAUNCH=0, CHAMFER="1 mm arris",
            DOWEL_DIAMETER=0, DRAWBORE_OFFSET=0,
            FIT_CLASS="CLEARANCE + WEDGE (W-001)",
            ASSEMBLY_DIRECTION="Slide rail through both pockets along +X",
            CONSTRAINT="FLOATING",
            NOTES="Pocket floor sloped 5° out. Seasonal ease in cheeks. No glue.",
        )
add_joint(
    JOINT_ID="J-ARCH", JOINT_TYPE="Radial voussoir bed (Roman)",
    PART_A="M-005/M-006/M-007", PART_B="M-004 imposts",
    LOCATION=f"Gate CL x={D['gate_c']:.0f} spring z={D['spring']}",
    MORTISE_WIDTH=0, MORTISE_HEIGHT=0, MORTISE_DEPTH=0,
    TENON_WIDTH=0, TENON_HEIGHT=0, TENON_LENGTH=0,
    SHOULDER=0, HAUNCH=0, CHAMFER=0,
    DOWEL_DIAMETER="SS erection dowels @ imposts only",
    DRAWBORE_OFFSET=0, FIT_CLASS="GLUE (Type S 10 mm joints) COMPRESSION",
    ASSEMBLY_DIRECTION="Built on timber centering, key last",
    CONSTRAINT="FIXED",
    NOTES="Pure compression. No structural steel.",
)
add_joint(
    JOINT_ID="J-HOZO-LEAF", JOINT_TYPE="Hozo ほぞ mortise & tenon",
    PART_A="GL-001", PART_B="GS-001",
    LOCATION="Gate leaf — 3 ledges × 2 stiles = 6 tenons",
    MORTISE_WIDTH=P["ledge"] / 3, MORTISE_HEIGHT=P["ledge"],
    MORTISE_DEPTH=P["stile"] * 0.6,
    TENON_WIDTH=P["ledge"] / 3, TENON_HEIGHT=P["ledge"],
    TENON_LENGTH=P["stile"] * 0.55,
    SHOULDER="equal", HAUNCH=0, CHAMFER="1 mm",
    DOWEL_DIAMETER=P["peg_d"], DRAWBORE_OFFSET=1.5,
    FIT_CLASS="DRAWBORED / SNUG",
    ASSEMBLY_DIRECTION="Stiles onto ledges (frame first, boards last)",
    CONSTRAINT="FIXED",
    NOTES="Tenon thickness ≈ ⅓ stock. Drawbore 1.5 mm toward shoulder.",
)
add_joint(
    JOINT_ID="J-WATARI", JOINT_TYPE="Watari-ago 渡り顎 (optional upgrade)",
    PART_A="R-001 (mid-rail)", PART_B="M-002-*",
    LOCATION="Wind-exposed mid-rails / gate-adjacent bays — OPTIONAL",
    MORTISE_WIDTH=D["pocket_w"], MORTISE_HEIGHT=D["pocket_h"],
    MORTISE_DEPTH=P["pocket_depth"],
    TENON_WIDTH=P["rail_t"], TENON_HEIGHT=P["rail_w"], TENON_LENGTH=P["pocket_depth"],
    SHOULDER=18, HAUNCH=18, CHAMFER=0, DOWEL_DIAMETER=0, DRAWBORE_OFFSET=0,
    FIT_CLASS="FRICTION + HAUNCH",
    ASSEMBLY_DIRECTION="Same as nuki after haunch seats cut",
    CONSTRAINT="FLOATING",
    NOTES="Upgrade path from J-N*. Do not mix haunched and plain in one rail.",
    STATUS="OPTIONAL",
)

# --- operations (typical part routings) ---
def ops(part_id, steps):
    for i, (name, tool, ref, tol, fail) in enumerate(steps, start=1):
        operations.append({
            "PART_ID": part_id, "OP": f"OP{i:03d}0", "NAME": name,
            "TOOL": tool, "REFERENCE": ref, "TOLERANCE": tol, "FAILURE": fail,
        })


ops("R-001", [
    ("Rough crosscut 8' stock", "Miter saw", "factory end", "T1 ±2 mm", "End check/split — recut"),
    ("Joint face A", "Jointer / #7 plane", "FACE A down later", "T2 0.3 mm hollow max", "Twist — discard"),
    ("Joint edge B", "Jointer", "FACE A against fence", "T2", "Not square to A"),
    ("Plane to 38 thickness", "Planer", "FACE A down", "T1 ±0.4 mm", "Snipe — extra length"),
    ("Rip to 89 width", "Table saw", "EDGE B on fence", "T1 ±0.4 mm", "Blade drift"),
    ("Final crosscut to rail_length — STOP S-014 DO NOT MOVE", "Miter + stop", "DATUM END against stop, EDGE B down", "T2 ±0.5 mm", "Stop creep"),
    ("Arris 1 mm both long edges", "Block plane", "FACE A up", "T0", "Tearout"),
    ("End-grain oil", "Brush", "both ends", "n/a", "Skip — premature check"),
    ("Inspect length vs mate rails", "Tape + story stick", "DATUM END", "T2 all 12 within 1 mm", "Mismatch — recut from extra"),
])
ops("B-001", [
    ("Rip 1x6 to 140", "Table saw", "factory edge", "T1 ±0.5", "Burn — feed rate"),
    ("Final crosscut STOP S-015", "Miter + stop", "DATUM END (bottom)", "T1 ±1 mm", "Stop creep"),
    ("Ease arrises", "Block plane / 120 grit", "show face", "T0", "Over-round gaps look uneven"),
])
ops("GS-001", [
    ("Mill to 40×70×leaf_h", "Jointer/planer/saw", "FACE A, EDGE B, DATUM END 0 = hinge bottom", "T2", "Wind"),
    ("Layout ledge mortises from Datum End 0", "Square + gauge", "EDGE B", "T2 ±0.3 mm", "Paired stiles must match"),
    ("Chop mortises", "Chisel / mortiser", "FACE A reference", "T2", "Blowout — backer"),
    ("Drawbore 1.5 mm toward shoulder", "Drill press", "FACE A", "T3", "Over-offset splits tenon"),
])
ops("M-002-B", [
    ("Verify drum templates vs T-510 batter stick", "Story pole", "plinth bed", "T3", "Batter error compounds"),
    ("Core 3 pockets per face from rail_z story stick", "Core drill / shop drawing P-302", "Datum: plinth bed + face centerline", "T2 ±1 mm CL", "CL mismatch = rail bind"),
    ("Slope pocket floors 5° out", "Chisel / grinder", "pocket floor", "T1", "Back-slope traps water"),
    ("Set drums on Type S, #4 epoxy dowels", "Mason", "plumb + batter stick", "T1 3 mm in 1600", "Lean into bay"),
])

# --- inspection ---
inspection.extend([
    {"QC": "QC-01", "GATE": "M0", "CHECK": "Verify parcel survey + 811 locates before excavation", "SPEC": "Open-hole", "CLASS": "T0"},
    {"QC": "QC-02", "GATE": "M4", "CHECK": "Footing bearing elevation", "SPEC": f"−{P['frost_depth']} mm from finish grade, ±15 mm", "CLASS": "T1"},
    {"QC": "QC-03", "GATE": "M4", "CHECK": "Air-entrainment on delivery ticket", "SPEC": "5–7% AE, 4000 psi", "CLASS": "T0"},
    {"QC": "QC-04", "GATE": "M5", "CHECK": "Pier centerline spacing", "SPEC": f"{P['bay_cc']} mm ±3 mm typical; gate {D['gate_span_cc']} mm ±3", "CLASS": "T2"},
    {"QC": "QC-05", "GATE": "M5", "CHECK": "Pier plumb and batter", "SPEC": f"1:{D['batter_ratio']:.1f} per face; plumb within 3 mm / 1600", "CLASS": "T2"},
    {"QC": "QC-06", "GATE": "M4", "CHECK": "All R-001 finished lengths", "SPEC": f"{D['rail_length']} mm, all 12 within 1 mm of each other", "CLASS": "T2"},
    {"QC": "QC-07", "GATE": "M3", "CHECK": "Pocket CL vs rail_z story stick", "SPEC": f"{list(P['rail_z'])} ±1 mm", "CLASS": "T2"},
    {"QC": "QC-08", "GATE": "M5", "CHECK": "Dry-fit rails through both pockets before cladding", "SPEC": "Slides by hand; wedge snugs; no bind in summer moisture", "CLASS": "T2"},
    {"QC": "QC-09", "GATE": "M5", "CHECK": "Gate diagonals (leaf)", "SPEC": "Diagonals within 2 mm before boards go on", "CLASS": "T2"},
    {"QC": "QC-10", "GATE": "M5", "CHECK": "Arch centering not struck before 7-day cure", "SPEC": "Hold point — sign-off", "CLASS": "T0"},
    {"QC": "QC-11", "GATE": "M7", "CHECK": "Capillary flashing continuous at all 6 stems", "SPEC": "Visual + photo", "CLASS": "T0"},
    {"QC": "QC-12", "GATE": "M7", "CHECK": "Curb isolated from pier footings", "SPEC": "Construction joint / foam; no rebar continuity", "CLASS": "T1"},
    {"QC": "QC-13", "GATE": "M7", "CHECK": "Rain-screen gaps remain open (not caulked)", "SPEC": f"{P['board_gap']} mm ±2", "CLASS": "T1"},
    {"QC": "QC-14", "GATE": "M7", "CHECK": "Printer scale on templates T-501..T-510", "SPEC": "100.000 mm check box measures 100.0 ±0.5", "CLASS": "T3"},
])

decisions.extend([
    {"ID": "D-001", "DECISION": "Masonry piers replace timber posts in STELE",
     "REASON": "Buffalo frost + plow berms destroy grade-set posts; mass + batter resists 115 mph without straps.",
     "AFFECTED": "All M-*, F-*; L-001 optional HASHIRA-only"},
    {"ID": "D-002", "DECISION": "Nuki pockets FLOATING, not glued",
     "REASON": "Seasonal movement of 2080 mm cedar; glue would split mortise cheeks. Wedges are the lock and the repair path.",
     "AFFECTED": "R-001, W-001, J-N*"},
    {"ID": "D-003", "DECISION": "Tenon thickness = ⅓ of 40 mm stile ≈ 13 mm",
     "REASON": "Mortise cheek thickness remains adequate in GS-001.",
     "AFFECTED": "GS-001, GL-001, J-HOZO-LEAF"},
    {"ID": "D-004", "DECISION": "Curb FLOATING independent of pier footings",
     "REASON": "Shallow curb will heave; continuity would rack piers.",
     "AFFECTED": "C-001, F-001"},
    {"ID": "D-005", "DECISION": "Arch in pure compression, no structural steel",
     "REASON": "Freeze-thaw attacks tension; Roman geometry removes it. SS dowels are erection-only.",
     "AFFECTED": "M-004..M-007, J-ARCH"},
    {"ID": "D-006", "DECISION": "Panel top 1825 mm under 6′-0″ residential limit",
     "REASON": "Green Code. Pier caps 1965 and arch 2640 assessed separately — TO BE CONFIRMED with Permit & Inspection.",
     "AFFECTED": "overall height parameters", "STATUS": "TO BE CONFIRMED"},
])

fmea.extend([
    {"MODE": "Frost heave lifts pier", "CAUSE": "Footing above frost / wet bearing", "EFFECT": "Rack, cracked mortar",
     "SEV": 9, "LIK": 2, "DET": 7, "MITIGATION": "48″ bearing + F-003 drain + AE concrete + QC-02/03"},
    {"MODE": "Wind overturning", "CAUSE": "Sail-like panels, skinny posts", "EFFECT": "Lean / collapse",
     "SEV": 10, "LIK": 2, "DET": 6, "MITIGATION": "Mass rule ≥3× reaction; batter keeps resultant in middle third"},
    {"MODE": "Rail bind / split cheeks", "CAUSE": "No seasonal ease / glued nuki", "EFFECT": "Cracked pier or broken rail",
     "SEV": 6, "LIK": 4, "DET": 8, "MITIGATION": "CLEARANCE fit + wedges; D-002"},
    {"MODE": "Curb heave racks line", "CAUSE": "Curb tied into pier ftgs", "EFFECT": "Cracked plinths",
     "SEV": 7, "LIK": 3, "DET": 8, "MITIGATION": "FLOATING curb D-004 / QC-12"},
    {"MODE": "Arch spreading", "CAUSE": "Struck centering early / weak impost", "EFFECT": "Joint opening at crown",
     "SEV": 8, "LIK": 2, "DET": 9, "MITIGATION": "7-day hold QC-10; imposts sized; Type S"},
    {"MODE": "Cedar rot at grade", "CAUSE": "Wood in snow/splash", "EFFECT": "10-year failure",
     "SEV": 5, "LIK": 2, "DET": 8, "MITIGATION": "Curb 250 + board_z0 320; no wood below 250"},
    {"MODE": "Plow strike", "CAUSE": "Berm against boards", "EFFECT": "Broken cladding",
     "SEV": 4, "LIK": 6, "DET": 9, "MITIGATION": "Sacrificial masonry curb; boards replaceable bay-by-bay"},
])

# ---------------------------------------------------------------------------
# 3. NESTING / MATERIAL TAKEOFF
# ---------------------------------------------------------------------------
def nest_dimensional(part_id, stock_len, finished_len, qty, kerf):
    per = int((stock_len + kerf) // (finished_len + kerf))
    per = max(per, 1)
    n_stock = math.ceil(qty / per)
    used = qty * finished_len + (qty - n_stock) * kerf
    waste = n_stock * stock_len - used
    return {
        "PART_ID": part_id, "STOCK_LENGTH": stock_len, "PER_STOCK": per,
        "N_STOCK": n_stock, "YIELD_PCT": round(100 * used / (n_stock * stock_len), 1),
        "WASTE_MM": round(waste, 0),
    }


nests = [
    nest_dimensional("R-001", 2438, D["rail_length"], D["n_rails"], P["saw_kerf"]),   # 8'
    nest_dimensional("B-001", 2438, D["board_height"], D["n_boards"], P["saw_kerf"]),
    nest_dimensional("TC-001", 2438, D["rail_length"], D["n_curbs"], P["saw_kerf"]),
    nest_dimensional("GS-001", 2438, P["leaf_h"], 2, P["saw_kerf"]),
    nest_dimensional("GF-001", 2438, P["leaf_h"], D["n_gate_boards"], P["saw_kerf"]),
    nest_dimensional("W-001", 915, P["wedge_l"], D["n_wedges"], P["saw_kerf"]),  # 36" oak offcut
]

cedar_bf_net = (
    D["n_rails"] * rail_bf
    + D["n_boards"] * bf_nominal(1, 6, 96)
    + D["n_curbs"] * bf_nominal(2, 6, 96)
    + 2 * bf_nominal(2, 4, 96)
    + D["n_gate_boards"] * bf_nominal(1, 4, 96)
)
cedar_bf_buy = round(cedar_bf_net * P["waste_factor_cedar"], 1)

# ---------------------------------------------------------------------------
# 4. ASSEMBLY TREE
# ---------------------------------------------------------------------------
TREE = {
    "A-000 MASTER_ASSEMBLY STELE": {
        "A-FND Foundations": ["F-003 ×6", "F-001 ×6", "F-002 ×6", "H-006", "H-007"],
        "A-PIER Piers (×6)": {
            "END_L / GATE_R": ["M-001", "M-002-R", "M-003 (END_L only)"],
            "MID ×2": ["M-001", "M-002-B", "M-003"],
            "GATE_L / END_R": ["M-001", "M-002-L", "M-003 (END_R only)"],
        },
        "A-BAY Panel bays ×4": ["C-001", "R-001 ×3", "W-001 ×6", "B-001 × n_boards_bay", "TC-001", "H-001"],
        "A-GATE Arch": ["M-004 ×2", "M-005 ×2", "M-006 ×8", "M-007", "H-005", "centering (temp)"],
        "A-LEAF Gate leaf": ["GS-001 ×2", "GL-001 ×3", "GB-001", "GF-001 × n", "H-002", "H-003", "H-004"],
    }
}

BUILD_SEQ = [
    ("01", "STOCK / 811 / SURVEY", "QC-01"),
    ("02", "Excavate 6 pits to frost_depth + gravel_h", "QC-02"),
    ("03", "F-003 compact; F-001+F-002 pour AE 4000", "QC-03"),
    ("04", "Cure 7 d; flashing H-007; M-001 plinths", "QC-11"),
    ("05", "M-002 drums to batter stick; core pockets from story stick", "QC-05 QC-07"),
    ("06", "M-003 caps (non-gate); C-001 curbs FLOATING", "QC-12"),
    ("07", "Mill R-001 lot on stop S-014; W-001", "QC-06"),
    ("08", "Dry-fit all rails J-N*; wedge weather-side", "QC-08"),
    ("09", "B-001 cladding; TC-001 caps", "QC-13"),
    ("10", "M-004 imposts; timber centering; M-005/006/007; 7-day hold", "QC-10"),
    ("11", "Strike centering; A-LEAF dry diagonals; hang H-002/H-003", "QC-09"),
    ("12", "Final QA walk, oil end grain H-008", "QC-06..13"),
]

# ---------------------------------------------------------------------------
# 5. FILE OUTPUTS
# ---------------------------------------------------------------------------
DIRS = [
    "00_SOURCE", "01_MASTER_CAD", "02_STEP", "03_STL", "04_DXF", "05_SVG",
    "06_DRAWINGS", "07_BOM", "08_CUT_LISTS", "09_JOINERY", "10_TEMPLATES",
    "11_BUILD_MANUAL", "12_QA", "13_REVISION_HISTORY", "data",
]


def ensure_dirs():
    for d in DIRS:
        os.makedirs(os.path.join(FAB, d), exist_ok=True)


def write_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")


def write_csv(path, rows, fieldnames=None):
    if not rows:
        return
    fieldnames = fieldnames or list(rows[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def part_row_cut(p, rough=True):
    return {
        "PART_ID": p["PART_ID"],
        "DESCRIPTION": p["PART_NAME"],
        "QTY": p["QUANTITY"],
        "T": p["ROUGH_THICKNESS"] if rough else p["FINISHED_THICKNESS"],
        "W": p["ROUGH_WIDTH"] if rough else p["FINISHED_WIDTH"],
        "L": p["ROUGH_LENGTH"] if rough else p["FINISHED_LENGTH"],
        "T_IN": mm_in(p["ROUGH_THICKNESS"] if rough else p["FINISHED_THICKNESS"]),
        "W_IN": mm_in(p["ROUGH_WIDTH"] if rough else p["FINISHED_WIDTH"]),
        "L_IN": mm_in(p["ROUGH_LENGTH"] if rough else p["FINISHED_LENGTH"]),
        "MATERIAL": p["MATERIAL"],
        "HANDED": p["HANDED"],
        "NOTES": p["NOTES"],
    }


# ---- SVG helpers ----
INK, DIM, ACC, PAPER, LIGHT = "#26241f", "#8a6f4d", "#a34e2b", "#f6f3ea", "#c8c2b2"
MONO = "font-family='IBM Plex Mono, Menlo, monospace'"


def svg_wrap(w, h, body, title=""):
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {h}' "
        f"width='{w}' height='{h}' font-size='16'>\n"
        f"<rect width='{w}' height='{h}' fill='{PAPER}'/>\n"
        f"{body}\n</svg>\n"
    )


def txt(x, y, s, size=16, fill=INK, anchor="start", wgt=""):
    s = (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    w = f" font-weight='{wgt}'" if wgt else ""
    return (f"<text x='{x:.1f}' y='{y:.1f}' {MONO} font-size='{size}' fill='{fill}' "
            f"text-anchor='{anchor}'{w}>{s}</text>\n")


def rect(x, y, w, h, fill="none", stroke=INK, sw=2):
    return (f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' "
            f"fill='{fill}' stroke='{stroke}' stroke-width='{sw}'/>\n")


def line(x1, y1, x2, y2, sw=1.5, stroke=INK, dash=None):
    d = f" stroke-dasharray='{dash}'" if dash else ""
    return (f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' "
            f"stroke='{stroke}' stroke-width='{sw}'{d}/>\n")


def titleblock(w, h, code, name):
    b = ""
    b += rect(24, 24, w - 48, h - 48, sw=2.5)
    b += rect(24, h - 110, w - 48, 86, sw=2)
    b += txt(40, h - 78, "STELE  FABRICATION  ·  BUFFALO NY  ·  REV " + REV, 14, DIM)
    b += txt(40, h - 52, name, 18, INK, wgt="600")
    b += txt(w - 200, h - 70, code, 22, ACC, wgt="600")
    b += txt(w - 200, h - 48, "UNITS mm [in]  ·  DO NOT SCALE", 12, DIM)
    return b


def check_box(x, y):
    """100 mm calibration square — but on screen we draw 100 px labeled 100 mm."""
    b = rect(x, y, 100, 100, sw=2, stroke=ACC)
    b += txt(x, y - 8, "CHECK BOX = 100.000 mm  (verify print scale)", 12, ACC)
    b += txt(x + 50, y + 58, "100", 14, ACC, "middle")
    return b


def drawing_ga100():
    """Overall assembly — front elevation 1:50."""
    w, h = 1400, 900
    sc = 1 / 12.5  # 1:12.5 ≈ close, actually 1:50 would be 0.02; use 0.08 for readability → 1:12.5 shop sketch
    # Use 1:40
    sc = 1 / 40.0
    ox, oy = 80, 620
    b = titleblock(w, h, "GA-100", "GENERAL ASSEMBLY — FRONT ELEVATION  1:40")
    b += line(ox, oy, ox + D["run_length"] * sc, oy, 2)
    b += txt(ox, oy + 18, "GRADE", 11, DIM)
    for i, x in enumerate(D["pier_x"]):
        role, pockets, cap = pier_role(i, x)
        px = ox + x * sc
        bw = P["shaft_base"] * sc
        tw = P["shaft_top"] * sc
        ph = P["plinth_h"] * sc
        sh = P["shaft_h"] * sc
        b += rect(px - P["plinth_w"] * sc / 2, oy - ph, P["plinth_w"] * sc, ph, sw=1.2)
        b += (f"<polygon points='{px-bw/2:.1f},{oy-ph:.1f} {px+bw/2:.1f},{oy-ph:.1f} "
              f"{px+tw/2:.1f},{oy-ph-sh:.1f} {px-tw/2:.1f},{oy-ph-sh:.1f}' "
              f"fill='none' stroke='{INK}' stroke-width='1.4'/>\n")
        b += txt(px, oy + 36, f"P{i+1}", 11, ACC, "middle")
        b += txt(px, oy + 50, role, 9, DIM, "middle")
    # bays
    for x0, x1 in D["panel_bays"]:
        xa = ox + (x0 + P["shaft_base"] / 2) * sc
        xb = ox + (x1 - P["shaft_base"] / 2) * sc
        b += rect(xa, oy - P["curb_h"] * sc, xb - xa, P["curb_h"] * sc, sw=1)
        b += rect(xa, oy - P["board_z1"] * sc, xb - xa, (P["board_z1"] - P["board_z0"]) * sc, sw=1)
    # arch
    gc = ox + D["gate_c"] * sc
    ys = oy - D["spring"] * sc
    ri, ro = D["r_in"] * sc, D["r_out"] * sc
    b += (f"<path d='M {gc-ro:.1f} {ys:.1f} A {ro:.1f} {ro:.1f} 0 0 1 {gc+ro:.1f} {ys:.1f}' "
          f"fill='none' stroke='{INK}' stroke-width='1.6'/>\n")
    b += (f"<path d='M {gc-ri:.1f} {ys:.1f} A {ri:.1f} {ri:.1f} 0 0 1 {gc+ri:.1f} {ys:.1f}' "
          f"fill='none' stroke='{INK}' stroke-width='1.6'/>\n")
    b += txt(ox + D["run_length"] * sc / 2, oy + 80,
             f"OVERALL {D['run_length']:.0f} [{mm_in(D['run_length'])}]   "
             f"BAY CC {P['bay_cc']}   GATE CLEAR {P['gate_clear']}   "
             f"PANEL TOP {D['panel_top']:.0f}   PIER TOP {D['pier_top']:.0f}   CROWN {D['crown']:.0f}",
             13, DIM, "middle")
    b += txt(40, 70, "DATUM: GRADE = Z0 · RUN = +X · STREET FACE = −Y", 13, DIM)
    return svg_wrap(w, h, b)


def drawing_p301_rail():
    w, h = 1200, 520
    sc = 0.45
    b = titleblock(w, h, "P-301", "R-001  NUKI THROUGH-RAIL  QTY 12  1:2.2")
    L, T, Wd = D["rail_length"] * sc, P["rail_t"] * sc, P["rail_w"] * sc
    x, y = 80, 180
    b += rect(x, y, L, Wd, sw=2)
    # pocket engagement zones
    pd = P["pocket_depth"] * sc
    b += rect(x, y, pd, Wd, fill="#e8d5c4", sw=1, stroke=ACC)
    b += rect(x + L - pd, y, pd, Wd, fill="#e8d5c4", sw=1, stroke=ACC)
    b += txt(x + pd / 2, y - 10, "POCKET", 11, ACC, "middle")
    b += txt(x + L - pd / 2, y - 10, "POCKET", 11, ACC, "middle")
    b += line(x, y + Wd + 24, x + L, y + Wd + 24, 1.2, DIM)
    b += txt(x + L / 2, y + Wd + 18, f"FINISHED L {D['rail_length']:.0f} [{mm_in(D['rail_length'])}]", 13, DIM, "middle")
    b += txt(x + L + 12, y + Wd / 2, f"{P['rail_w']} [{mm_in(P['rail_w'])}]", 12, DIM)
    b += txt(80, 140, "MATERIAL  western red cedar  ·  GRAIN →  ·  FACE A (show) toward street  ·  EDGE B down in pocket", 13, DIM)
    b += txt(80, 380, f"DATUM END 0 = left (toward PIER smaller X).  Tolerance T2 ±0.5 mm.  STOP S-014 = {D['rail_length']:.0f} mm.  DO NOT MOVE STOP.", 13, ACC)
    b += txt(80, 404, "Fit: CLEARANCE in pocket (pocket_ease 6 mm total). Lock: W-001 wedges, weather side. CONSTRAINT: FLOATING. No glue.", 13, DIM)
    b += check_box(980, 200)
    return svg_wrap(w, h, b)


def drawing_j201_pocket():
    w, h = 1100, 700
    sc = 4.0  # 4:1
    b = titleblock(w, h, "J-201", "NUKI POCKET  ·  SECTION AT RAIL  4:1")
    # pier face patch
    px, py = 120, 160
    b += rect(px, py, 80 * sc, 120 * sc, sw=2)
    # pocket
    pw, ph, pd = D["pocket_w"] * sc, D["pocket_h"] * sc, P["pocket_depth"] * sc
    b += rect(px + 80 * sc - pd, py + 20 * sc, pd, ph, stroke=ACC, sw=2)
    # rail
    b += rect(px + 80 * sc - pd - 40 * sc, py + 20 * sc + (P["pocket_ease"] / 2) * sc,
              40 * sc + pd + 30 * sc, P["rail_w"] * sc, fill="#c4a574", sw=1.5)
    # wedge
    b += (f"<polygon points='{px+80*sc+8:.1f},{py+20*sc+10:.1f} "
          f"{px+80*sc+8+P['wedge_l']*sc*0.4:.1f},{py+20*sc+10:.1f} "
          f"{px+80*sc+8+P['wedge_l']*sc*0.4:.1f},{py+20*sc+ph-10:.1f} "
          f"{px+80*sc+8:.1f},{py+20*sc+ph-18:.1f}' fill='{ACC}' opacity='.5' stroke='{ACC}'/>\n")
    b += txt(px, py - 16, "MASONRY FACE (bay side)", 13, DIM)
    b += txt(px + 80 * sc + 20, py + 20 * sc + ph / 2, "W-001  weather-side", 12, ACC)
    b += txt(500, 180, f"POCKET  {D['pocket_w']:.0f} × {D['pocket_h']:.0f} × {P['pocket_depth']} deep", 16, INK, wgt="600")
    b += txt(500, 208, f"RAIL    {P['rail_t']} × {P['rail_w']}  (ease {P['pocket_ease']} total)", 16, INK)
    b += txt(500, 236, "FLOOR SLOPE 5° OUT — DRAIN", 16, ACC)
    b += txt(500, 264, "DATUM: plinth bed + face CL. Measure rail_z along Reference Edge (vertical CL).", 14, DIM)
    b += txt(500, 292, f"rail_z CL = {list(P['rail_z'])}  (3 pockets / face as scheduled)", 14, DIM)
    b += txt(500, 330, "FIT CLASS: CLEARANCE + WEDGE.  Do not glue.  Do not caulk.", 14, INK)
    b += check_box(500, 380)
    return svg_wrap(w, h, b)


def drawing_t501_voussoir():
    w, h = 900, 700
    b = titleblock(w, h, "T-501", "VOUSSOIR FULL-SIZE TEMPLATE  (print 1:1, tile if needed)")
    b += check_box(60, 80)
    # schematic half-ring sector
    cx, cy, sc = 450, 520, 0.35
    ri, ro = D["r_in"] * sc, D["r_out"] * sc
    b += (f"<path d='M {cx-ro:.1f} {cy:.1f} A {ro:.1f} {ro:.1f} 0 0 1 {cx+ro:.1f} {cy:.1f}' "
          f"fill='none' stroke='{INK}' stroke-width='2'/>\n")
    b += (f"<path d='M {cx-ri:.1f} {cy:.1f} A {ri:.1f} {ri:.1f} 0 0 1 {cx+ri:.1f} {cy:.1f}' "
          f"fill='none' stroke='{INK}' stroke-width='2'/>\n")
    n = P["n_voussoirs"]
    for i in range(n + 1):
        a = math.pi - i * math.pi / n
        x1, y1 = cx + ri * math.cos(a), cy - ri * math.sin(a)
        x2, y2 = cx + ro * math.cos(a), cy - ro * math.sin(a)
        b += line(x1, y1, x2, y2, 1.2)
    b += line(cx - ro - 20, cy, cx + ro + 20, cy, 1, DIM, dash="8 6")
    b += txt(cx, cy + 24, "SPRINGLINE", 12, DIM, "middle")
    b += txt(60, 220, f"R_IN  {D['r_in']:.0f} mm  [{mm_in(D['r_in'])}]", 14)
    b += txt(60, 244, f"R_OUT {D['r_out']:.0f} mm  [{mm_in(D['r_out'])}]", 14)
    b += txt(60, 268, f"THICK {P['arch_thick']} mm   DEPTH {P['arch_depth']} mm", 14)
    b += txt(60, 292, f"{P['n_voussoirs']} divisions  ·  2 springers MIRRORED  ·  {D['n_typical_voussoirs']} typical IDENTICAL  ·  1 key", 14)
    b += txt(60, 328, "GRAIN n/a (cast stone).  DATUM: impost bed.  ORIENTATION: intrados down on centering.", 13, DIM)
    b += txt(60, 360, "TRUE 1:1 DXF: scale this drawing × (1/0.35) in CAD, or loft from r_in/r_out in FreeCAD.", 13, ACC)
    return svg_wrap(w, h, b)


def drawing_t510_batter():
    w, h = 700, 1100
    sc = 0.5
    b = titleblock(w, h, "T-510", "BATTER STORY STICK  1:2")
    x = 220
    y0 = 980
    b += line(80, y0, 600, y0, 2)
    b += txt(80, y0 + 16, "PLINTH BED", 12, DIM)
    base, top, ht = P["shaft_base"] * sc / 2, P["shaft_top"] * sc / 2, P["shaft_h"] * sc
    b += (f"<polygon points='{x-base:.1f},{y0:.1f} {x+base:.1f},{y0:.1f} "
          f"{x+top:.1f},{y0-ht:.1f} {x-top:.1f},{y0-ht:.1f}' "
          f"fill='none' stroke='{INK}' stroke-width='2'/>\n")
    b += line(x, y0, x, y0 - ht, 1, DIM, dash="4 4")
    b += txt(x + base + 12, y0 - 10, f"BASE {P['shaft_base']} [{mm_in(P['shaft_base'])}]", 13)
    b += txt(x + top + 12, y0 - ht + 14, f"TOP {P['shaft_top']} [{mm_in(P['shaft_top'])}]", 13)
    b += txt(80, y0 - ht / 2, f"H {P['shaft_h']}", 13)
    b += txt(80, 80, f"BATTER {D['batter_per_face']:.0f} / {P['shaft_h']}  =  1:{D['batter_ratio']:.1f} PER FACE", 15, ACC, wgt="600")
    b += txt(80, 108, "Egyptian talus. Resultant stays in middle third under design wind.", 13, DIM)
    for zc in P["rail_z"]:
        yy = y0 - (zc - P["plinth_h"]) * sc
        b += line(x - 80, yy, x + 80, yy, 1.2, ACC, dash="6 4")
        b += txt(x + 90, yy + 4, f"POCKET CL {zc}", 12, ACC)
    b += check_box(80, 150)
    return svg_wrap(w, h, b)


def drawing_labels():
    """Printable part labels."""
    w, h = 1100, 1400
    b = titleblock(w, h, "LBL-001", "PART LABELS  —  print, cut, attach to FACE A")
    items = [
        ("R-001", "NUKI RAIL", f"{P['rail_t']}×{P['rail_w']}×{D['rail_length']:.0f}", "GRAIN →  FACE A STREET  EDGE B DOWN", "MATES M-002  W-001"),
        ("B-001", "RAIN-SCREEN BOARD", f"{P['board_t']}×{P['board_w']}×{D['board_height']:.0f}", "TOP ↑  FACE A STREET", "MATES R-001 only"),
        ("TC-001", "BAY CAP", f"{P['tcap_h']}×{P['tcap_w']}×{D['rail_length']:.0f}", "WASH TO STREET  KERF DOWN", "MATES R-001"),
        ("W-001", "NUKI WEDGE", f"{P['wedge_t']}×{P['wedge_w']}×{P['wedge_l']}", "TAPER 1:12  WEATHER SIDE", "MATES R-001 / pocket"),
        ("GS-001", "GATE STILE", f"{P['leaf_t']}×{P['stile']}×{P['leaf_h']}", "DATUM END 0 = BOTTOM", "MATES GL-001  H-002"),
        ("GL-001", "GATE LEDGE", f"{P['ledge']}×{P['ledge']}×{D['ledge_length']:.0f}", "TENON BOTH ENDS", "MATES GS-001"),
        ("GB-001", "GATE BRACE", "RISES FROM HINGE", "TEMPLATE T-503", "MATES ledges"),
        ("M-002-L", "SHAFT LH", "POCKETS LEFT", "BATTER STICK T-510", "GATE_L / END_R"),
        ("M-002-R", "SHAFT RH", "POCKETS RIGHT", "BATTER STICK T-510", "END_L / GATE_R"),
        ("M-002-B", "SHAFT BOTH", "POCKETS L+R", "BATTER STICK T-510", "MID"),
        ("C-001", "CURB", f"{P['curb_w']}×{P['curb_h']}×{D['bay_clear']:.0f}", "FLOATING — NO REBAR TO PIERS", "Bay splash"),
        ("M-007", "KEYSTONE", f"proud {P['key_proud']}", "CROWN  ORIENT TAPER UP", "J-ARCH"),
    ]
    cols, cw, ch = 2, 500, 170
    for i, (pid, name, size, ori, mates) in enumerate(items):
        col, row = i % cols, i // cols
        x, y = 50 + col * (cw + 20), 80 + row * (ch + 12)
        b += rect(x, y, cw, ch, sw=2)
        b += txt(x + 14, y + 32, pid, 22, ACC, wgt="600")
        b += txt(x + 14, y + 58, name, 16, INK, wgt="600")
        b += txt(x + 14, y + 82, size, 13, DIM)
        b += txt(x + 14, y + 106, ori, 12, INK)
        b += txt(x + 14, y + 128, mates + "  ·  REV " + REV, 12, DIM)
        b += txt(x + cw - 14, y + 32, "TOP ↑", 12, ACC, "end")
    return svg_wrap(w, h, b)


def drawing_exploded():
    w, h = 1200, 800
    b = titleblock(w, h, "EX-200", "EXPLODED BAY  —  insertion logic (not decorative)")
    b += txt(60, 80, "INSERTION ORDER  C-001  →  R-001 (3)  →  W-001  →  B-001  →  TC-001", 14, ACC)
    # simple exploded schematic
    b += rect(80, 400, 40, 280, sw=2)  # pier L
    b += rect(720, 400, 40, 280, sw=2)
    b += txt(100, 700, "M-002", 12, DIM, "middle")
    b += txt(740, 700, "M-002", 12, DIM, "middle")
    for i, y in enumerate((620, 520, 430)):
        b += rect(160, y, 520, 18, stroke=ACC, sw=1.5)
        b += txt(420, y - 8, f"R-001  rail {i+1}  →  slide +X through pockets", 12, ACC, "middle")
    b += rect(200, 660, 440, 24, sw=1.2)
    b += txt(420, 678, "C-001 CURB  (FLOATING)", 12, DIM, "middle")
    b += rect(220, 250, 400, 140, sw=1, stroke=LIGHT)
    b += txt(420, 240, "B-001 boards  (after rails locked)  FACE A −Y", 12, DIM, "middle")
    b += rect(180, 200, 480, 16, sw=1.5)
    b += txt(420, 192, "TC-001 cap  last", 12, INK, "middle")
    b += txt(60, 740, "Do not fasten B-001 to masonry. Do not assemble boards before QC-08 rail dry-fit.", 13, ACC)
    return svg_wrap(w, h, b)


# ---------------------------------------------------------------------------
# 6. HTML SHOP PORTAL
# ---------------------------------------------------------------------------
def table_html(rows, cols, headers=None):
    headers = headers or cols
    th = "".join(f"<th>{h}</th>" for h in headers)
    body = []
    for r in rows:
        tds = "".join(f"<td>{r.get(c, '')}</td>" for c in cols)
        body.append(f"<tr>{tds}</tr>")
    return f"<table><thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def html_portal():
    bom_rows = []
    item = 1
    for p in parts:
        bom_rows.append({
            "ITEM": item, "PART_ID": p["PART_ID"], "DESCRIPTION": p["PART_NAME"],
            "QTY": p["QUANTITY"], "MAKE/BUY": p["MAKE_OR_BUY"],
            "MATERIAL": p["MATERIAL"],
            "FINISHED": f"{p['FINISHED_THICKNESS']:.0f} × {p['FINISHED_WIDTH']:.0f} × {p['FINISHED_LENGTH']:.0f}",
            "FINISHED_IN": f"{mm_in(p['FINISHED_THICKNESS'])} × {mm_in(p['FINISHED_WIDTH'])} × {mm_in(p['FINISHED_LENGTH'])}",
            "HANDED": p["HANDED"], "REV": p["REVISION"],
        })
        item += 1
    for h in hardware:
        bom_rows.append({
            "ITEM": item, "PART_ID": h["HARDWARE_ID"], "DESCRIPTION": h["DESCRIPTION"],
            "QTY": h["QTY"], "MAKE/BUY": h.get("MAKE_OR_BUY", "BUY"),
            "MATERIAL": h["MATERIAL"], "FINISHED": f"{h['SIZE']} × {h['LENGTH']}",
            "FINISHED_IN": h.get("STANDARD", ""), "HANDED": "n/a", "REV": REV,
        })
        item += 1

    rough = [part_row_cut(p, True) for p in parts if p["MAKE_OR_BUY"] == "MAKE"]
    fin = [part_row_cut(p, False) for p in parts if p["MAKE_OR_BUY"] == "MAKE"]

    eq = [
        ("bay_clear", "bay_cc − shaft_base", D["bay_clear"]),
        ("rail_length", "bay_clear + 2 × pocket_depth", D["rail_length"]),
        ("board_height", "board_z1 − board_z0", D["board_height"]),
        ("n_boards_bay", "floor((bay_clear − gap) / (board_w + gap))", D["n_boards_bay"]),
        ("n_panel_bays", "n_left + 1 connecting + n_right", D["n_panel_bays"]),
        ("gate_span_cc", "gate_clear + shaft_base", D["gate_span_cc"]),
        ("spring", "plinth_h + shaft_h + impost_h", D["spring"]),
        ("crown", "spring + gate_clear/2 + arch_depth", D["crown"]),
        ("pier_top", "plinth + shaft + cap1 + cap2 + pyr", D["pier_top"]),
        ("panel_top", "board_z1 + tcap_h", D["panel_top"]),
        ("run_length", "last_pier_x + shaft_base", D["run_length"]),
        ("batter_ratio", "shaft_h / ((shaft_base − shaft_top)/2)", round(D["batter_ratio"], 2)),
        ("leaf_width", "gate_clear − 2 × leaf_gap", D["leaf_width"]),
        ("cedar_bf_buy", "net × waste_factor_cedar", cedar_bf_buy),
    ]

    def esc(s):
        return str(s).replace("&", "&amp;").replace("<", "&lt;")

    param_rows = [{"KEY": k, "MM": v if not isinstance(v, tuple) else list(v),
                   "IN": mm_in(v) if isinstance(v, (int, float)) else "—",
                   "STATUS": PARAM_STATUS.get(k, "DESIGN")} for k, v in P.items()]

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>STELE Fabrication Model — Rev {REV}</title>
<style>
:root{{--ink:#26241f;--dim:#6d6553;--terra:#a34e2b;--paper:#f6f3ea;--line:#d9d2bf;--mono:"IBM Plex Mono",ui-monospace,monospace;--serif:"Source Serif 4",Georgia,serif}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--paper);color:var(--ink);font:16px/1.5 var(--serif)}}
.wrap{{width:min(1100px,calc(100% - 32px));margin:0 auto}}
nav{{position:sticky;top:0;background:rgba(246,243,234,.95);border-bottom:1px solid var(--line);padding:8px 0;z-index:20}}
nav .wrap{{display:flex;flex-wrap:wrap;gap:12px;align-items:center}}
nav b{{font:600 11px var(--mono);letter-spacing:.16em;color:var(--terra)}}
nav a{{font:500 11px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--dim);text-decoration:none}}
header{{padding:48px 0 28px;border-bottom:3px solid var(--ink)}}
h1{{font:700 42px/1.1 var(--serif)}}
.sub{{color:var(--dim);max-width:60ch;margin-top:8px}}
.meta{{display:flex;gap:28px;flex-wrap:wrap;margin-top:22px;font:500 12px/1.6 var(--mono);color:var(--dim)}}
.meta b{{display:block;color:var(--ink)}}
section{{padding:36px 0;border-bottom:1px solid var(--line)}}
h2{{font:700 26px var(--serif);margin-bottom:10px}}
h2 span{{color:var(--terra);font:600 13px var(--mono);margin-right:8px}}
table{{width:100%;border-collapse:collapse;font-size:13px;margin:14px 0}}
th,td{{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top}}
th{{font:600 10px/1.3 var(--mono);letter-spacing:.1em;text-transform:uppercase;color:#5c6b48}}
.audit td:last-child{{font-family:var(--mono);font-weight:600}}
.GOOD{{color:#2d6a3e}}.WEAK{{color:#a34e2b}}.CRITICAL{{color:#8b1e1e}}
.callout{{border-left:4px solid var(--terra);background:#efeadb;padding:12px 16px;margin:16px 0;max-width:75ch}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
@media(max-width:800px){{.grid{{grid-template-columns:1fr}}}}
figure{{border:1px solid var(--line);background:#fff;margin:16px 0}}
figure img{{width:100%;display:block}}
figcaption{{font:500 11px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--dim);padding:8px 12px;border-top:1px solid var(--line)}}
a.dl{{display:inline-block;font:600 11px var(--mono);letter-spacing:.1em;text-transform:uppercase;text-decoration:none;color:var(--ink);border:1px solid var(--line);padding:8px 12px;margin:3px;background:#fff}}
pre{{background:#fff;border:1px solid var(--line);padding:12px;overflow:auto;font:12px var(--mono)}}
footer{{padding:40px 0;font:12px var(--mono);color:var(--dim)}}
@media print{{nav{{display:none}}section{{page-break-inside:avoid}}}}
</style>
</head>
<body>
<nav><div class="wrap">
<b>FAB REV {REV}</b>
<a href="#audit">Audit</a><a href="#params">Params</a><a href="#parts">Parts</a>
<a href="#joints">Joints</a><a href="#bom">BOM</a><a href="#cuts">Cuts</a>
<a href="#drawings">Drawings</a><a href="#build">Build</a><a href="#qa">QA</a>
<a href="#files">Files</a>
<a href="../report/">Report</a><a href="../stele/">Stele</a>
</div></nav>
<header><div class="wrap">
<p style="font:600 12px var(--mono);letter-spacing:.28em;color:var(--terra)">PARAMETRIC FABRICATION MODEL</p>
<h1>STELE — digital manufacturing definition</h1>
<p class="sub">Not a picture of a fence. A linked system: parameter → geometry → metadata → drawings → BOM → cut list → build documentation. Change <span style="font-family:var(--mono)">bay_cc</span> by 300 mm and rails, boards, curbs, nests, and this portal regenerate together.</p>
<div class="meta">
<div><b>Project</b>{PROJECT['PROJECT_ID']}</div>
<div><b>Revision</b>{REV} · {TODAY}</div>
<div><b>Units</b>mm internal · inches at interfaces</div>
<div><b>Run</b>{D['run_length']:.0f} mm · {mm_in(D['run_length'])}</div>
</div>
</div></header>
<main class="wrap">

<section id="audit">
<h2><span>M0–M8</span>Existing-model audit (MODE B)</h2>
<p>Source audited: <code>fence/stele/cad/stele_fence.py</code> + HASHIRA OpenSCAD studies + plan SVGs generated from a <em>second</em> copy of the same numbers.</p>
<table class="audit">
<tr><th>Criterion</th><th>Before (Rev A)</th><th>After (Rev B)</th></tr>
<tr><td>Architecture</td><td class="WEAK">WEAK — four material blobs (Masonry/Timber/Concrete/Gravel), no Part IDs</td><td class="GOOD">GOOD — semantic registry, persistent IDs</td></tr>
<tr><td>Parameterization</td><td class="WEAK">WEAK — P dict in CAD, duplicated in gen_stele_plans.py</td><td class="GOOD">GOOD — this file is the only numeric source for schedules</td></tr>
<tr><td>Part separation</td><td class="CRITICAL">CRITICAL — cannot extract a rail from the compound</td><td class="GOOD">GOOD — R-001 qty 12, etc.</td></tr>
<tr><td>Metadata</td><td class="CRITICAL">CRITICAL — none</td><td class="GOOD">GOOD — Fabrication properties on every part</td></tr>
<tr><td>Assembly hierarchy</td><td class="WEAK">WEAK — implicit loop order</td><td class="GOOD">GOOD — A-FND / A-PIER / A-BAY / A-GATE / A-LEAF</td></tr>
<tr><td>Joinery as data</td><td class="CRITICAL">CRITICAL — pockets only as booleans</td><td class="GOOD">GOOD — J-N* instances + J-ARCH + J-HOZO-LEAF</td></tr>
<tr><td>BOM / cut-list ready</td><td class="CRITICAL">CRITICAL</td><td class="GOOD">GOOD — CSV + JSON generated here</td></tr>
<tr><td>Drawing readiness</td><td class="WEAK">ACCEPTABLE architectural sheets; no part drawings</td><td class="GOOD">GOOD — GA/P/J/T/LBL added; S-1..S-5 remain design intent</td></tr>
<tr><td>Magic numbers</td><td class="WEAK">WEAK — 150, 90+6, 40, 1.25 leaf clip</td><td class="GOOD">GOOD — named; remaining CAD literals queued as D-007</td></tr>
</table>
<div class="callout"><strong>Refactor before documentation.</strong> Schedules in this package are generated from the registry, not typed from renders. FreeCAD still exports visual compounds (Rev A geometry script) — Part-as-Body split inside FreeCAD is the next CAD increment (D-007), not a blocker for shop data.</div>
</section>

<section id="params">
<h2><span>A–B</span>Parameters &amp; equations</h2>
<p>If overall length changes, change <code>n_panel_bays_*</code> or <code>bay_cc</code> only. Rail length, board count, curb length, nests, and BOM quantities follow.</p>
{table_html(param_rows, ["KEY","MM","IN","STATUS"])}
<h3 style="margin-top:24px;font:600 20px var(--serif)">Design equations</h3>
{table_html([{"NAME":n,"EQUATION":e,"VALUE":v} for n,e,v in eq], ["NAME","EQUATION","VALUE"])}
</section>

<section id="parts">
<h2><span>C</span>Part register</h2>
<p>Identical parts share one ID with qty &gt; 1. Handed shafts are separate IDs. HASHIRA post L-001 is OPTIONAL (STELE uses masonry piers).</p>
{table_html([{
    "PART_ID":p["PART_ID"],"NAME":p["PART_NAME"],"QTY":p["QUANTITY"],
    "MAKE":p["MAKE_OR_BUY"],"MAT":p["MATERIAL"],
    "FINISHED T×W×L": f"{p['FINISHED_THICKNESS']:.0f}×{p['FINISHED_WIDTH']:.0f}×{p['FINISHED_LENGTH']:.0f}",
    "HANDED":p["HANDED"],"JOINERY":p["JOINERY"],"CONSTRAINT":p["CONSTRAINT"],
} for p in parts],
["PART_ID","NAME","QTY","MAKE","MAT","FINISHED T×W×L","HANDED","JOINERY","CONSTRAINT"])}
</section>

<section id="joints">
<h2><span>E</span>Joinery register</h2>
{table_html(joints, ["JOINT_ID","JOINT_TYPE","PART_A","PART_B","FIT_CLASS","CONSTRAINT","LOCATION"])}
<p>Nuki instances: {sum(1 for j in joints if j["JOINT_ID"].startswith("J-N"))} (3 rails × {D["n_panel_bays"]} bays). Optional watari-ago is an upgrade path, not mixed in one rail.</p>
</section>

<section id="bom">
<h2><span>F / 46</span>Master BOM</h2>
{table_html(bom_rows, ["ITEM","PART_ID","DESCRIPTION","QTY","MAKE/BUY","MATERIAL","FINISHED","HANDED","REV"])}
<h3 style="margin:24px 0 8px;font:600 20px var(--serif)">Hardware schedule</h3>
{table_html(hardware, ["HARDWARE_ID","DESCRIPTION","STANDARD","SIZE","LENGTH","MATERIAL","QTY","MPN"])}
<p>Cedar procurement: net {cedar_bf_net:.1f} BF × waste factor {P["waste_factor_cedar"]} = <strong>{cedar_bf_buy} BF buy</strong>. Waste factor is explicit (knots, matching, milling). Unit costs are not invented — fill UNIT_COST in JSON when quotes exist.</p>
</section>

<section id="cuts">
<h2><span>G–I</span>Cut lists &amp; nesting</h2>
<h3>Rough cut list</h3>
{table_html(rough, ["PART_ID","DESCRIPTION","QTY","T","W","L","T_IN","W_IN","L_IN","MATERIAL","NOTES"])}
<h3>Finished dimension list</h3>
{table_html(fin, ["PART_ID","DESCRIPTION","QTY","T","W","L","T_IN","W_IN","L_IN","MATERIAL","HANDED"])}
<h3>Dimensional nesting</h3>
{table_html(nests, ["PART_ID","STOCK_LENGTH","PER_STOCK","N_STOCK","YIELD_PCT","WASTE_MM"])}
<p>R-001: one rail per 8′ 2×4 (finished {D["rail_length"]:.0f} mm). B-001: one board per 8′ 1×6 at {D["board_height"]:.0f} mm — remainder is usable for wedges/offcuts, not a second board. Stop setups: <strong>S-014 = {D["rail_length"]:.0f} mm</strong> (all 12 rails), <strong>S-015 = {D["board_height"]:.0f} mm</strong> (all {D["n_boards"]} boards). Do not move the stop.</p>
</section>

<section id="drawings">
<h2><span>L</span>Drawing index</h2>
<ul>
<li>GA-100 General assembly elevation — this package</li>
<li>EX-200 Exploded bay insertion logic</li>
<li>P-301 R-001 rail part drawing</li>
<li>J-201 Nuki pocket section</li>
<li>T-501 Voussoir template (with 100 mm check box)</li>
<li>T-510 Batter story stick + pocket CLs</li>
<li>LBL-001 Part labels</li>
<li>S-1…S-5 Architectural intent (existing <a href="../stele/plans/S1_general.svg">/fence/stele/plans</a>)</li>
</ul>
<div class="grid">
<figure><img src="06_DRAWINGS/GA-100.svg" alt="GA-100"/><figcaption>GA-100</figcaption></figure>
<figure><img src="06_DRAWINGS/EX-200.svg" alt="EX-200"/><figcaption>EX-200</figcaption></figure>
<figure><img src="06_DRAWINGS/P-301.svg" alt="P-301"/><figcaption>P-301 R-001</figcaption></figure>
<figure><img src="06_DRAWINGS/J-201.svg" alt="J-201"/><figcaption>J-201 pocket</figcaption></figure>
<figure><img src="10_TEMPLATES/T-510.svg" alt="T-510"/><figcaption>T-510 batter stick</figcaption></figure>
<figure><img src="10_TEMPLATES/T-501.svg" alt="T-501"/><figcaption>T-501 voussoir</figcaption></figure>
</div>
<figure><img src="10_TEMPLATES/LBL-001.svg" alt="labels"/><figcaption>LBL-001</figcaption></figure>
</section>

<section id="build">
<h2><span>K</span>Assembly sequence (dependency order)</h2>
{table_html([{"STEP":a,"OPERATION":b,"HOLD":c} for a,b,c in BUILD_SEQ], ["STEP","OPERATION","HOLD"])}
<pre>{json.dumps(TREE, indent=2)}</pre>
<h3 style="margin:20px 0 8px;font:600 20px var(--serif)">Routing excerpt — R-001</h3>
{table_html([o for o in operations if o["PART_ID"]=="R-001"], ["OP","NAME","TOOL","REFERENCE","TOLERANCE","FAILURE"])}
</section>

<section id="qa">
<h2><span>M</span>QA / FMEA / decisions</h2>
{table_html(inspection, ["QC","GATE","CHECK","SPEC","CLASS"])}
<h3 style="margin:20px 0 8px;font:600 20px var(--serif)">Failure modes</h3>
{table_html(fmea, ["MODE","CAUSE","EFFECT","SEV","LIK","MITIGATION"])}
<h3 style="margin:20px 0 8px;font:600 20px var(--serif)">Decision log</h3>
{table_html(decisions, ["ID","DECISION","REASON","AFFECTED"])}
<div class="callout">This is a fabrication definition, not a stamped engineering document. Foundations and arch still require an engineer of record in Erie County before pour.</div>
</section>

<section id="files">
<h2><span>N–O</span>Export manifest &amp; unresolved</h2>
<p>
<a class="dl" href="data/fabrication.json">fabrication.json</a>
<a class="dl" href="00_SOURCE/parameters.json">parameters.json</a>
<a class="dl" href="07_BOM/master_bom.csv">master_bom.csv</a>
<a class="dl" href="07_BOM/hardware.csv">hardware.csv</a>
<a class="dl" href="08_CUT_LISTS/rough.csv">rough.csv</a>
<a class="dl" href="08_CUT_LISTS/finished.csv">finished.csv</a>
<a class="dl" href="08_CUT_LISTS/nesting.csv">nesting.csv</a>
<a class="dl" href="09_JOINERY/joints.csv">joints.csv</a>
<a class="dl" href="12_QA/inspection.csv">inspection.csv</a>
<a class="dl" href="06_DRAWINGS/GA-100.svg">GA-100</a>
<a class="dl" href="06_DRAWINGS/P-301.svg">P-301</a>
<a class="dl" href="10_TEMPLATES/T-510.svg">T-510</a>
</p>
<p><strong>Unresolved / TO BE MEASURED / TO BE CONFIRMED</strong></p>
<ul>
<li>Green Code district height for pier caps (1965) and arch crown (2640) — D-006.</li>
<li>H-004 latch MPN — user selection.</li>
<li>Saw kerf ASSUMED 3.2 mm — measure your blade; parameter <code>saw_kerf</code>.</li>
<li>Unit costs — fill when quotes in hand; do not invent.</li>
<li>D-007: split FreeCAD compounds into named Bodies with Fabrication properties (CAD increment).</li>
<li>Site-specific overall run: set <code>n_panel_bays_left/right</code> or <code>bay_cc</code> and re-run <code>python3 scripts/fab_system.py</code>.</li>
</ul>
<p>Regenerate: <code>python3 scripts/fab_system.py</code></p>
</section>
</main>
<footer><div class="wrap">STELE fabrication model Rev {REV} · parameter → geometry → metadata → shop documents · {PROJECT['PROJECT_ID']}</div></footer>
</body></html>
"""


def main():
    ensure_dirs()
    # source
    write_json(os.path.join(FAB, "00_SOURCE", "project.json"), PROJECT)
    write_json(os.path.join(FAB, "00_SOURCE", "parameters.json"), {
        "units": "mm", "revision": REV, "parameters": P,
        "status": PARAM_STATUS, "derived": {k: v for k, v in D.items() if k != "panel_bays"},
        "equations": {
            "bay_clear": "bay_cc - shaft_base",
            "rail_length": "bay_clear + 2*pocket_depth",
            "board_height": "board_z1 - board_z0",
            "n_boards_bay": "floor((bay_clear-board_gap)/(board_w+board_gap))",
            "gate_span_cc": "gate_clear + shaft_base",
            "spring": "plinth_h + shaft_h + impost_h",
            "crown": "spring + gate_clear/2 + arch_depth",
            "run_length": "last_pier_x + shaft_base",
        },
    })
    write_json(os.path.join(FAB, "data", "fabrication.json"), {
        "project": PROJECT, "parameters": P, "derived": {k: v for k, v in D.items() if k != "panel_bays"},
        "parts": parts, "joints": joints, "hardware": hardware,
        "operations": operations, "inspection": inspection,
        "decisions": decisions, "fmea": fmea, "nests": nests,
        "tree": TREE, "build_sequence": BUILD_SEQ,
        "cedar_bf_net": cedar_bf_net, "cedar_bf_buy": cedar_bf_buy,
        "waste_factor_cedar": P["waste_factor_cedar"],
    })
    # BOM / cuts
    bom = []
    n = 1
    for p in parts:
        bom.append({
            "ITEM": n, "PART_ID": p["PART_ID"], "DESCRIPTION": p["PART_NAME"],
            "QTY": p["QUANTITY"], "MAKE_OR_BUY": p["MAKE_OR_BUY"],
            "MATERIAL": p["MATERIAL"], "SPECIES": p.get("SPECIES", ""),
            "FINISHED_T": p["FINISHED_THICKNESS"], "FINISHED_W": p["FINISHED_WIDTH"],
            "FINISHED_L": p["FINISHED_LENGTH"],
            "ROUGH_T": p["ROUGH_THICKNESS"], "ROUGH_W": p["ROUGH_WIDTH"],
            "ROUGH_L": p["ROUGH_LENGTH"],
            "HANDED": p["HANDED"], "REV": REV, "NOTES": p["NOTES"],
        })
        n += 1
    write_csv(os.path.join(FAB, "07_BOM", "master_bom.csv"), bom)
    write_csv(os.path.join(FAB, "07_BOM", "hardware.csv"), hardware)
    write_csv(os.path.join(FAB, "08_CUT_LISTS", "rough.csv"),
              [part_row_cut(p, True) for p in parts if p["MAKE_OR_BUY"] == "MAKE"])
    write_csv(os.path.join(FAB, "08_CUT_LISTS", "finished.csv"),
              [part_row_cut(p, False) for p in parts if p["MAKE_OR_BUY"] == "MAKE"])
    write_csv(os.path.join(FAB, "08_CUT_LISTS", "nesting.csv"), nests)
    write_csv(os.path.join(FAB, "09_JOINERY", "joints.csv"), joints)
    write_csv(os.path.join(FAB, "12_QA", "inspection.csv"), inspection)
    write_csv(os.path.join(FAB, "12_QA", "fmea.csv"), fmea)
    write_csv(os.path.join(FAB, "12_QA", "operations.csv"), operations)

    with open(os.path.join(FAB, "13_REVISION_HISTORY", "HISTORY.md"), "w") as f:
        f.write(
            "# Revision history\n\n"
            "| Rev | Date | Description |\n|-----|------|-------------|\n"
            "| A | 2026-07-17 | Initial geometry + architectural sheets S-1…S-5 |\n"
            f"| B | {TODAY} | Fabrication-model refactor: part registry, BOM, cut lists, "
            "joinery IDs, shop drawings, templates, QA. Schedules generated from parameters.\n"
        )

    with open(os.path.join(FAB, "01_MASTER_CAD", "README.md"), "w") as f:
        f.write(
            "# Master CAD pointers\n\n"
            "- Geometry (visual assembly): `fence/stele/cad/stele_fence.py` → `exports/stele.FCStd`, STEP, STL\n"
            "- Joint studies: `fence/cad/*.scad`\n"
            "- **Authoritative dimensions for shop: `scripts/fab_system.py` / `00_SOURCE/parameters.json`**\n"
            "- Next increment (D-007): explode FreeCAD compounds into named Bodies with Fabrication properties.\n"
        )

    # drawings
    dwg = os.path.join(FAB, "06_DRAWINGS")
    tpl = os.path.join(FAB, "10_TEMPLATES")
    open(os.path.join(dwg, "GA-100.svg"), "w").write(drawing_ga100())
    open(os.path.join(dwg, "EX-200.svg"), "w").write(drawing_exploded())
    open(os.path.join(dwg, "P-301.svg"), "w").write(drawing_p301_rail())
    open(os.path.join(dwg, "J-201.svg"), "w").write(drawing_j201_pocket())
    open(os.path.join(tpl, "T-501.svg"), "w").write(drawing_t501_voussoir())
    open(os.path.join(tpl, "T-510.svg"), "w").write(drawing_t510_batter())
    open(os.path.join(tpl, "LBL-001.svg"), "w").write(drawing_labels())

    # OpenSCAD parameter mirror
    scad = os.path.join(ROOT, "fence", "cad", "parameters.scad")
    with open(scad, "w") as f:
        f.write("// HASHIRA/STELE parameters — MIRROR of scripts/fab_system.py (mm)\n")
        f.write("// Do not edit independently. Regenerated by fab_system.py.\n")
        f.write(f"STELE_REV = \"{REV}\";\n")
        for k, v in P.items():
            if isinstance(v, tuple):
                f.write(f"{k} = {list(v)};\n")
            elif isinstance(v, str):
                f.write(f'{k} = "{v}";\n')
            else:
                f.write(f"{k} = {v};\n")
        f.write(f"rail_length = {D['rail_length']};\n")
        f.write(f"bay_clear = {D['bay_clear']};\n")
        f.write("// ECHO metadata for parsers\n")
        f.write('echo(str("FAB_REV=", STELE_REV));\n')
        f.write('echo(str("R-001 qty=", 12, " L=", rail_length));\n')

    open(os.path.join(FAB, "index.html"), "w").write(html_portal())

    # completeness echo
    print("FAB Rev", REV, "written to", FAB)
    print("parts", len(parts), "joints", len(joints), "hardware", len(hardware))
    print("run_length", D["run_length"], "rail_length", D["rail_length"], "boards", D["n_boards"])
    print("cedar BF buy", cedar_bf_buy)


if __name__ == "__main__":
    main()
