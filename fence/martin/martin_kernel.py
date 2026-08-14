"""
MARTIN fabrication kernel — single source of dimensional truth.

Native unit: inch. Convert to millimetres only at CAD / export interfaces.
FreeCAD, OpenSCAD, drawings, BOM, cut lists, and the Build app all derive
from build_project(). Do not duplicate controlling dimensions elsewhere.

Rev D — sit-on-grade freestanding ladder base (no digging, no cement, no stone pads).
"""

from __future__ import annotations

import math
from copy import deepcopy

MM = 25.4

# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------
PROJECT = {
    "PROJECT_ID": "MARTIN",
    "PROJECT_NAME": "Prairie removable fence — Buffalo NY",
    "REVISION": "D",
    "UNITS": "inch",
    "DESIGN_STANDARD": "Prairie / Darwin Martin + Japanese joinery; Buffalo Green Code verify",
    "MATERIAL_SYSTEM": "dimensional lumber only (paint-grade SPF or equivalent) + removable sandbag ballast",
    "TOLERANCE_CLASS": "T1 general woodworking; T2 nuki / hozo / drawbore",
    "AUTHOR": "MARTIN fabrication model",
    "MODEL_VERSION": "4.0.0",
    "DATE": "2026-08-14",
    "CAD": ["FreeCAD 1.1", "OpenSCAD"],
}

# ---------------------------------------------------------------------------
# Master parameters (inches). Evidence tags: VERIFIED | DERIVED | ASSUMED | ESTIMATED | TBM
# ---------------------------------------------------------------------------
P = {
    # envelope — owner
    "overall_length": {"v": 143.0, "src": "VERIFIED", "note": "owner site opening"},
    "overall_height": {"v": 65.0, "src": "VERIFIED", "note": "sill top (driveway datum) to cap top"},
    "existing_board_t": {"v": 0.75, "src": "VERIFIED", "note": "existing fence thickness"},

    # stock actuals (S4S dimensional)
    "post_x": {"v": 3.5, "src": "DERIVED", "note": "4×6 actual face along run"},
    "post_y": {"v": 5.5, "src": "DERIVED", "note": "4×6 actual depth"},
    "rail_t": {"v": 1.5, "src": "DERIVED", "note": "2×8 actual thickness"},
    "rail_h": {"v": 7.25, "src": "DERIVED", "note": "2×8 actual width, on edge"},
    "cap_t": {"v": 1.5, "src": "DERIVED", "note": "2×8 flat"},
    "cap_w": {"v": 7.25, "src": "DERIVED", "note": "2×8 flat width"},
    "board_t": {"v": 0.75, "src": "VERIFIED", "note": "1×6 actual = existing ¾″"},
    "board_w": {"v": 5.5, "src": "DERIVED", "note": "1×6 actual"},
    "board_gap": {"v": 0.25, "src": "ASSUMED", "note": "rain-screen drainage gap"},
    "stile_w": {"v": 3.5, "src": "DERIVED", "note": "2×4 / ripped 2×6 face"},
    "leaf_t": {"v": 1.5, "src": "DERIVED", "note": "2× stock gate thickness"},
    "rail_gate_h": {"v": 5.5, "src": "DERIVED", "note": "2×6 gate rail"},
    "brace_w": {"v": 3.5, "src": "DERIVED"},

    # joinery
    "post_tenon_x": {"v": 2.5, "src": "ASSUMED", "note": "shoulder 0.5″ each side of 3.5"},
    "post_tenon_y": {"v": 4.5, "src": "ASSUMED", "note": "shoulder 0.5″ each side of 5.5"},
    "post_tenon_h": {"v": 3.5, "src": "ASSUMED", "note": "into 5.5″ cross-tie; leave ~2″ below mortise"},
    "rail_reveal": {"v": 0.50, "src": "ASSUMED", "note": "nuki projection past outer post faces"},
    "cap_overhang": {"v": 0.75, "src": "ASSUMED"},
    "groove_d": {"v": 0.375, "src": "ASSUMED", "note": "board dado depth in rail edge"},
    "groove_w": {"v": 0.875, "src": "ASSUMED", "note": "board t + 1/8″ clearance"},
    "board_end_clear": {"v": 0.125, "src": "ASSUMED", "note": "float gap at rail"},
    "kusabi_t": {"v": 0.625, "src": "ASSUMED"},
    "kusabi_w": {"v": 1.125, "src": "ASSUMED"},
    "kusabi_l": {"v": 5.5, "src": "DERIVED", "note": "equals post_y — through cheek"},
    "drawbore_offset": {"v": 0.125, "src": "ASSUMED", "note": "T2 hozo"},
    "peg_d": {"v": 0.375, "src": "ASSUMED", "note": "oak peg"},
    "nuki_fit": {"v": 0.03, "src": "ASSUMED", "note": "sliding/clearance on rail thickness, ~1/32″"},

    # gate
    "gate_clear": {"v": 36.0, "src": "ASSUMED", "note": "design — mower/cart; not owner-measured"},
    "gate_gap": {"v": 0.50, "src": "ASSUMED", "note": "each side of leaf"},
    "gate_bottom_clear": {"v": 1.00, "src": "ASSUMED", "note": "above sill top — snow/splash"},
    "gate_top_clear": {"v": 0.50, "src": "ASSUMED", "note": "under cap — Rev C fix vs Rev B overlap"},
    "latch_bar_l": {"v": 18.0, "src": "ASSUMED"},
    "latch_bar_t": {"v": 1.50, "src": "DERIVED", "note": "2× stock"},
    "latch_bar_w": {"v": 3.50, "src": "DERIVED", "note": "2×4 actual"},
    "house_receiver_depth": {"v": 4.0, "src": "ASSUMED", "note": "Latch A — TBM at wall"},
    "pintle_count": {"v": 2.0, "src": "ASSUMED"},

    # prairie bands (AFF to rail centerline)
    "rail_cl_1": {"v": 10.0, "src": "ASSUMED", "note": "splash rail"},
    "rail_cl_2": {"v": 28.0, "src": "ASSUMED", "note": "latch alignment"},
    "rail_cl_3": {"v": 46.0, "src": "ASSUMED", "note": "upper band"},

    # sit-on-grade ladder base (NO digging, NO cement, NO stone pads)
    "sill_overhang": {"v": 6.0, "src": "ASSUMED", "note": "dodai past outer post faces"},
    "sill_t": {"v": 3.5, "src": "DERIVED", "note": "4×6 actual thickness (across Y)"},
    "sill_h": {"v": 5.5, "src": "DERIVED", "note": "4×6 on edge — Prairie base beam"},
    "base_spread_cl": {"v": 36.0, "src": "ASSUMED", "note": "driveway-sill CL to garden-sill CL; wind lever"},
    "tie_reveal": {"v": 1.0, "src": "ASSUMED", "note": "cross-tie past outer sill faces"},
    "drop_off": {"v": 5.0, "src": "ESTIMATED", "note": "TBM — driveway→garden; timber packing under garden sill"},
    "pack_w": {"v": 5.5, "src": "DERIVED", "note": "packing crib matches sill height face"},
    "pack_len": {"v": 12.0, "src": "ASSUMED", "note": "crib length along sill at each tie"},
    "ballast_box_x": {"v": 14.0, "src": "ASSUMED", "note": "timber box inside, along run"},
    "ballast_box_y": {"v": 10.0, "src": "ASSUMED", "note": "timber box inside, across run"},
    "ballast_box_h": {"v": 10.0, "src": "ASSUMED"},
    "ballast_bag_lb": {"v": 50.0, "src": "ASSUMED", "note": "woven sandbag, removable"},
    "wind_psf": {"v": 15.0, "src": "ASSUMED", "note": "planning pressure, not PE; Buffalo ~90 mph simplified"},
    "wind_fs": {"v": 1.5, "src": "ASSUMED", "note": "planning factor of safety on overturning"},
    "furniture_pad_t": {"v": 0.5, "src": "ASSUMED", "note": "rubber pads under driveway sill — protect pavement"},
    "brace_z": {"v": 18.0, "src": "ASSUMED", "note": "sujikai meets post above sill top"},

    # manufacture
    "saw_kerf": {"v": 0.125, "src": "ASSUMED", "note": "thin-kerf circular / table saw"},
    "waste_factor": {"v": 0.15, "src": "ASSUMED", "note": "joinery / defect / matching"},
    "board_above_pad": {"v": 1.50, "src": "ASSUMED", "note": "bottom course start AFF (sill top)"},
}


def v(name: str) -> float:
    return float(P[name]["v"])


def src(name: str) -> str:
    return P[name]["src"]


def inch_mm(x: float) -> float:
    return x * MM


def rnd(x: float, places: int = 3) -> float:
    return round(float(x) + 0.0, places)


def bf_nominal(nom_t: float, nom_w: float, length_ft: float) -> float:
    """Board feet from nominal purchase size (US convention)."""
    return rnd(nom_t * nom_w * length_ft / 12.0, 2)


# ---------------------------------------------------------------------------
# Derived layout
# ---------------------------------------------------------------------------
def layout() -> dict:
    L = v("overall_length")
    H = v("overall_height")
    fx = v("post_x")
    fy = v("post_y")
    gate = v("gate_clear")
    cap_t = v("cap_t")
    rh = v("rail_h")
    rt = v("rail_t")

    # Datum: outer latch-side face x=0, sill top z=0, post centerline y=0
    p0 = fx / 2.0
    p1 = fx + gate + fx / 2.0
    p3 = L - fx / 2.0
    p1_right = p1 + fx / 2.0
    p3_left = L - fx
    clear_span = p3_left - p1_right  # = L - 3*fx - gate
    bay_clear = (clear_span - fx) / 2.0  # = (L - 4*fx - gate) / 2
    p2 = p1_right + bay_clear + fx / 2.0
    posts = [
        {"id": "L-001", "mark": "P0", "cx": rnd(p0), "role": "latch post", "handed": "NONE"},
        {"id": "L-002", "mark": "P1", "cx": rnd(p1), "role": "hinge post", "handed": "NONE"},
        {"id": "L-003", "mark": "P2", "cx": rnd(p2), "role": "mid post / cap scarf", "handed": "NONE"},
        {"id": "L-004", "mark": "P3", "cx": rnd(p3), "role": "end post", "handed": "NONE"},
    ]

    nuki_x0 = p1 - fx / 2.0 - v("rail_reveal")
    nuki_x1 = p3 + fx / 2.0 + v("rail_reveal")
    nuki_len = nuki_x1 - nuki_x0

    cap_x0 = p1 - fx / 2.0 - v("cap_overhang")
    cap_x1 = p3 + fx / 2.0 + v("cap_overhang")
    cap_len = cap_x1 - cap_x0

    post_body_h = H - cap_t
    post_blank_l = post_body_h + v("post_tenon_h")

    rail_cls = (v("rail_cl_1"), v("rail_cl_2"), v("rail_cl_3"))
    courses = []
    # bottom course
    courses.append(
        {
            "id": "C1",
            "z0": v("board_above_pad"),
            "z1": rail_cls[0] - rh / 2.0 - v("board_end_clear"),
        }
    )
    for a, b in zip(rail_cls, rail_cls[1:]):
        courses.append(
            {
                "id": "C" + str(len(courses) + 1),
                "z0": a + rh / 2.0 + v("board_end_clear"),
                "z1": b - rh / 2.0 - v("board_end_clear"),
            }
        )
    courses.append(
        {
            "id": "C4",
            "z0": rail_cls[-1] + rh / 2.0 + v("board_end_clear"),
            "z1": H - cap_t - v("board_end_clear"),
        }
    )
    for c in courses:
        c["h"] = rnd(c["z1"] - c["z0"])
        c["z0"] = rnd(c["z0"])
        c["z1"] = rnd(c["z1"])

    pitch = v("board_w") + v("board_gap")
    n_bay = max(1, int(math.floor((bay_clear + v("board_gap")) / pitch)))
    used = n_bay * v("board_w") + (n_bay - 1) * v("board_gap")
    board_inset = rnd((bay_clear - used) / 2.0)

    gate_leaf_w = gate - 2.0 * v("gate_gap")
    gate_h = H - cap_t - v("gate_bottom_clear") - v("gate_top_clear")
    gate_inner = gate_leaf_w - 2.0 * v("stile_w")
    n_gate_b = max(1, int(math.floor((gate_inner + v("board_gap")) / pitch)))

    sill_len = L + 2.0 * v("sill_overhang")
    spread = v("base_spread_cl")
    sill_t = v("sill_t")
    tie_len = spread + sill_t + 2.0 * v("tie_reveal")
    base_width = spread + sill_t  # outer sill face to outer sill face
    garden_sill_cy = spread / 2.0
    drive_sill_cy = -spread / 2.0
    brace_len = math.hypot(spread / 2.0, v("brace_z"))
    pack_layers = max(1, int(math.ceil(v("drop_off") / 1.5)))  # 2×6 actual 1.5″
    pack_h = rnd(pack_layers * 1.5)

    # tenon ratio check
    tenon_ratio_x = v("post_tenon_x") / fx
    cheek_x = (fx - v("post_tenon_x")) / 2.0
    cheek_y = (fy - v("post_tenon_y")) / 2.0
    nuki_cheek_y = (fy - rt) / 2.0

    return {
        "overall_length": L,
        "overall_height": H,
        "post_x": fx,
        "post_y": fy,
        "posts": posts,
        "bay_clear": rnd(bay_clear),
        "gate_clear": gate,
        "nuki_x0": rnd(nuki_x0),
        "nuki_x1": rnd(nuki_x1),
        "nuki_len": rnd(nuki_len),
        "cap_x0": rnd(cap_x0),
        "cap_len": rnd(cap_len),
        "cap_stub_len": rnd(fx + 1.0),
        "post_body_h": rnd(post_body_h),
        "post_blank_l": rnd(post_blank_l),
        "rail_cls": rail_cls,
        "courses": courses,
        "n_bay": n_bay,
        "board_inset": board_inset,
        "used_bay": rnd(used),
        "gate_leaf_w": rnd(gate_leaf_w),
        "gate_h": rnd(gate_h),
        "gate_inner": rnd(gate_inner),
        "n_gate_boards": n_gate_b,
        "sill_len": rnd(sill_len),
        "sill_t": sill_t,
        "sill_h": v("sill_h"),
        "base_spread_cl": spread,
        "base_width": rnd(base_width),
        "tie_len": rnd(tie_len),
        "garden_sill_cy": rnd(garden_sill_cy),
        "drive_sill_cy": rnd(drive_sill_cy),
        "brace_len": rnd(brace_len),
        "pack_layers": pack_layers,
        "pack_h": pack_h,
        "tenon_ratio_x": rnd(tenon_ratio_x, 3),
        "cheek_x": rnd(cheek_x),
        "cheek_y": rnd(cheek_y),
        "nuki_cheek_y": rnd(nuki_cheek_y),
        "equations": {
            "bay_clear": "(overall_length - 4*post_x - gate_clear) / 2",
            "nuki_len": "(P3_outer + rail_reveal) - (P1_outer - rail_reveal)",
            "post_blank_l": "overall_height - cap_t + post_tenon_h",
            "gate_h": "overall_height - cap_t - gate_bottom_clear - gate_top_clear",
            "sill_len": "overall_length + 2*sill_overhang",
            "tie_len": "base_spread_cl + sill_t + 2*tie_reveal",
            "base_width": "base_spread_cl + sill_t",
        },
    }


# ---------------------------------------------------------------------------
# Parts
# ---------------------------------------------------------------------------
def _part(**kw):
    base = {
        "MAKE_OR_BUY": "MAKE",
        "GRADE": "paint-grade #2 or better, straight",
        "GRAIN_DIRECTION": "length",
        "REFERENCE_FACE": "garden face (Y-)",
        "REFERENCE_EDGE": "latch-side (X-)",
        "REFERENCE_END": "datum end A — tenon shoulder / sill top",
        "REVISION": PROJECT["REVISION"],
        "PROCESS": "",
        "JOINERY": "",
        "NOTES": "",
        "HANDED": "IDENTICAL",
        "FIT": "",
        "TOLERANCE_CLASS": "T1",
        "MOVEMENT": "FIXED",
    }
    base.update(kw)
    return base


def parts(ly=None):
    ly = ly or layout()
    H = v("overall_height")
    posts = []
    for p in ly["posts"]:
        notes = p["role"]
        joinery = "foot tenon into F-003 cross-tie + 3 nuki mortises"
        if p["mark"] == "P0":
            joinery += "; latch-bar mortise (Latch B); no kusabi (gate side)"
        elif p["mark"] == "P1":
            joinery += "; 3 kusabi slots; 2 pintle mortises"
        elif p["mark"] == "P2":
            joinery += "; 3 kusabi slots; cap scarf bearing"
        else:
            joinery += "; 3 kusabi slots"
        posts.append(
            _part(
                PART_ID=p["id"],
                PART_NAME=f"{p['mark']} {p['role']}",
                PART_CATEGORY="L",
                ASSEMBLY="A-010 POSTS",
                QUANTITY=1,
                MATERIAL="solid lumber",
                SPECIES="SPF or SYP paint-grade (cedar optional)",
                PURCHASE="4×6 × 8′",
                ROUGH_THICKNESS=3.5,
                ROUGH_WIDTH=5.5,
                ROUGH_LENGTH=rnd(ly["post_blank_l"] + 1.0),
                FINISHED_THICKNESS=3.5,
                FINISHED_WIDTH=5.5,
                FINISHED_LENGTH=ly["post_blank_l"],
                BOARD_FEET=bf_nominal(4, 6, 8),
                JOINERY=joinery,
                PROCESS="OP010–OP100 post routing",
                NOTES=notes,
                TOLERANCE_CLASS="T2",
                DATUM="shoulder at sill top; tenon −Z into cross-tie",
                cx=p["cx"],
                mark=p["mark"],
            )
        )

    rail_names = [
        ("R-001", "R1 bottom Prairie nuki", v("rail_cl_1")),
        ("R-002", "R2 mid Prairie nuki", v("rail_cl_2")),
        ("R-003", "R3 upper Prairie nuki", v("rail_cl_3")),
    ]
    rails = []
    for pid, name, cl in rail_names:
        rails.append(
            _part(
                PART_ID=pid,
                PART_NAME=name,
                PART_CATEGORY="R",
                ASSEMBLY="A-020 PRIVACY_FRAME",
                QUANTITY=1,
                MATERIAL="solid lumber",
                SPECIES="SPF/SYP paint-grade",
                PURCHASE="2×8 × 10′",
                ROUGH_THICKNESS=1.5,
                ROUGH_WIDTH=7.25,
                ROUGH_LENGTH=rnd(ly["nuki_len"] + 1.0),
                FINISHED_THICKNESS=1.5,
                FINISHED_WIDTH=7.25,
                FINISHED_LENGTH=ly["nuki_len"],
                BOARD_FEET=bf_nominal(2, 8, 10),
                JOINERY="nuki through L-002/003/004; board grooves both edges; kusabi slots",
                PROCESS="OP010–OP080 rail routing",
                TOLERANCE_CLASS="T2",
                FIT="SLIDING in mortise (nuki_fit)",
                MOVEMENT="FLOATING along length (seasonal); locked by kusabi at posts",
                cl=cl,
            )
        )

    cap = _part(
        PART_ID="C-001",
        PART_NAME="Privacy cap (kama-tsugi pair)",
        PART_CATEGORY="C",
        ASSEMBLY="A-020 PRIVACY_FRAME",
        QUANTITY=1,
        MATERIAL="solid lumber",
        SPECIES="SPF/SYP paint-grade",
        PURCHASE="2×8 × 12′",
        ROUGH_THICKNESS=1.5,
        ROUGH_WIDTH=7.25,
        ROUGH_LENGTH=rnd(ly["cap_len"] + 1.0),
        FINISHED_THICKNESS=1.5,
        FINISHED_WIDTH=7.25,
        FINISHED_LENGTH=ly["cap_len"],
        BOARD_FEET=bf_nominal(2, 8, 12),
        JOINERY="kama-tsugi scarf at L-003 centerline, drawbored",
        NOTES="Cut as two halves after scarf layout; still one Part ID for the finished cap",
        TOLERANCE_CLASS="T2",
        HANDED="LEFT-HAND + RIGHT-HAND halves after scarf",
        MOVEMENT="FIXED at scarf; cap floats slightly on post tops",
    )
    cap_stub = _part(
        PART_ID="C-002",
        PART_NAME="Latch-post cap stub",
        PART_CATEGORY="C",
        ASSEMBLY="A-010 POSTS",
        QUANTITY=1,
        MATERIAL="solid lumber",
        SPECIES="SPF/SYP paint-grade",
        PURCHASE="from C-001 offcut / 2×8",
        ROUGH_THICKNESS=1.5,
        ROUGH_WIDTH=7.25,
        ROUGH_LENGTH=rnd(ly["cap_stub_len"] + 0.5),
        FINISHED_THICKNESS=1.5,
        FINISHED_WIDTH=7.25,
        FINISHED_LENGTH=ly["cap_stub_len"],
        BOARD_FEET=0,
        JOINERY="hozo to L-001 top",
        NOTES="Does not bridge gate",
    )

    boards = []
    # C2 and C3 same height → one ID
    h_c1 = ly["courses"][0]["h"]
    h_mid = ly["courses"][1]["h"]
    h_c4 = ly["courses"][3]["h"]
    n_per_course = ly["n_bay"] * 2  # two bays
    boards.append(
        _part(
            PART_ID="B-001",
            PART_NAME="Privacy board course C1 (below R1)",
            PART_CATEGORY="B",
            ASSEMBLY="A-020 PRIVACY_FRAME",
            QUANTITY=n_per_course,
            MATERIAL="solid lumber",
            SPECIES="SPF/SYP 1×6",
            PURCHASE="1×6 × 8′",
            ROUGH_THICKNESS=0.75,
            ROUGH_WIDTH=5.5,
            ROUGH_LENGTH=rnd(h_c1 + 0.5),
            FINISHED_THICKNESS=0.75,
            FINISHED_WIDTH=5.5,
            FINISHED_LENGTH=h_c1,
            BOARD_FEET=0,
            JOINERY="floats in R-001 bottom groove; no fasteners",
            MOVEMENT="FLOATING",
            FIT="CLEARANCE in groove",
        )
    )
    boards.append(
        _part(
            PART_ID="B-002",
            PART_NAME="Privacy board courses C2+C3 (between rails)",
            PART_CATEGORY="B",
            ASSEMBLY="A-020 PRIVACY_FRAME",
            QUANTITY=n_per_course * 2,
            MATERIAL="solid lumber",
            SPECIES="SPF/SYP 1×6",
            PURCHASE="1×6 × 8′",
            ROUGH_THICKNESS=0.75,
            ROUGH_WIDTH=5.5,
            ROUGH_LENGTH=rnd(h_mid + 0.5),
            FINISHED_THICKNESS=0.75,
            FINISHED_WIDTH=5.5,
            FINISHED_LENGTH=h_mid,
            BOARD_FEET=0,
            JOINERY="floats in rail grooves",
            MOVEMENT="FLOATING",
            FIT="CLEARANCE",
        )
    )
    boards.append(
        _part(
            PART_ID="B-003",
            PART_NAME="Privacy board course C4 (above R3)",
            PART_CATEGORY="B",
            ASSEMBLY="A-020 PRIVACY_FRAME",
            QUANTITY=n_per_course,
            MATERIAL="solid lumber",
            SPECIES="SPF/SYP 1×6",
            PURCHASE="1×6 × 8′",
            ROUGH_THICKNESS=0.75,
            ROUGH_WIDTH=5.5,
            ROUGH_LENGTH=rnd(h_c4 + 0.5),
            FINISHED_THICKNESS=0.75,
            FINISHED_WIDTH=5.5,
            FINISHED_LENGTH=h_c4,
            BOARD_FEET=0,
            JOINERY="floats; retained by C-001",
            MOVEMENT="FLOATING",
        )
    )

    gate_parts = [
        _part(
            PART_ID="G-001",
            PART_NAME="Gate hinge stile",
            PART_CATEGORY="G",
            ASSEMBLY="A-030 GATE",
            QUANTITY=1,
            MATERIAL="solid lumber",
            SPECIES="SPF/SYP or oak upgrade",
            PURCHASE="2×6 × 8′",
            ROUGH_THICKNESS=1.5,
            ROUGH_WIDTH=3.5,
            ROUGH_LENGTH=rnd(ly["gate_h"] + 1.0),
            FINISHED_THICKNESS=1.5,
            FINISHED_WIDTH=3.5,
            FINISHED_LENGTH=ly["gate_h"],
            JOINERY="hozo mortises for G-003..G-007; pintle gudgeons",
            HANDED="HINGE-HAND (P1)",
            TOLERANCE_CLASS="T2",
        ),
        _part(
            PART_ID="G-002",
            PART_NAME="Gate latch stile",
            PART_CATEGORY="G",
            ASSEMBLY="A-030 GATE",
            QUANTITY=1,
            MATERIAL="solid lumber",
            SPECIES="SPF/SYP or oak upgrade",
            PURCHASE="2×6 × 8′",
            ROUGH_THICKNESS=1.5,
            ROUGH_WIDTH=3.5,
            ROUGH_LENGTH=rnd(ly["gate_h"] + 1.0),
            FINISHED_THICKNESS=1.5,
            FINISHED_WIDTH=3.5,
            FINISHED_LENGTH=ly["gate_h"],
            JOINERY="hozo mortises; latch-bar mortise",
            HANDED="LATCH-HAND (P0)",
            TOLERANCE_CLASS="T2",
        ),
        _part(
            PART_ID="G-003",
            PART_NAME="Gate rail aligned to R1",
            PART_CATEGORY="G",
            ASSEMBLY="A-030 GATE",
            QUANTITY=1,
            MATERIAL="solid lumber",
            PURCHASE="2×6 × 8′",
            ROUGH_THICKNESS=1.5,
            ROUGH_WIDTH=5.5,
            ROUGH_LENGTH=rnd(ly["gate_inner"] + 2.0 * 1.5),  # tenons into stiles
            FINISHED_THICKNESS=1.5,
            FINISHED_WIDTH=5.5,
            FINISHED_LENGTH=rnd(ly["gate_inner"] + 2.0 * 1.25),
            JOINERY="haunched hozo both ends, drawbored",
            NOTES="finished length includes tenons; shoulder-to-shoulder = gate_inner",
            TOLERANCE_CLASS="T2",
        ),
        _part(
            PART_ID="G-004",
            PART_NAME="Gate rail aligned to R2 (latch)",
            PART_CATEGORY="G",
            ASSEMBLY="A-030 GATE",
            QUANTITY=1,
            MATERIAL="solid lumber",
            PURCHASE="2×6 × 8′",
            ROUGH_THICKNESS=1.5,
            ROUGH_WIDTH=5.5,
            ROUGH_LENGTH=rnd(ly["gate_inner"] + 3.0),
            FINISHED_THICKNESS=1.5,
            FINISHED_WIDTH=5.5,
            FINISHED_LENGTH=rnd(ly["gate_inner"] + 2.0 * 1.25),
            JOINERY="haunched hozo, drawbored; latch path",
            TOLERANCE_CLASS="T2",
        ),
        _part(
            PART_ID="G-005",
            PART_NAME="Gate rail aligned to R3",
            PART_CATEGORY="G",
            ASSEMBLY="A-030 GATE",
            QUANTITY=1,
            MATERIAL="solid lumber",
            PURCHASE="2×6 × 8′",
            ROUGH_THICKNESS=1.5,
            ROUGH_WIDTH=5.5,
            ROUGH_LENGTH=rnd(ly["gate_inner"] + 3.0),
            FINISHED_THICKNESS=1.5,
            FINISHED_WIDTH=5.5,
            FINISHED_LENGTH=rnd(ly["gate_inner"] + 2.0 * 1.25),
            JOINERY="haunched hozo, drawbored",
            TOLERANCE_CLASS="T2",
        ),
        _part(
            PART_ID="G-006",
            PART_NAME="Gate bottom rail",
            PART_CATEGORY="G",
            ASSEMBLY="A-030 GATE",
            QUANTITY=1,
            MATERIAL="solid lumber",
            PURCHASE="2×6 × 8′",
            ROUGH_THICKNESS=1.5,
            ROUGH_WIDTH=3.5,
            ROUGH_LENGTH=rnd(ly["gate_inner"] + 3.0),
            FINISHED_THICKNESS=1.5,
            FINISHED_WIDTH=3.5,
            FINISHED_LENGTH=rnd(ly["gate_inner"] + 2.0 * 1.25),
            JOINERY="hozo, drawbored",
            TOLERANCE_CLASS="T2",
        ),
        _part(
            PART_ID="G-007",
            PART_NAME="Gate top rail",
            PART_CATEGORY="G",
            ASSEMBLY="A-030 GATE",
            QUANTITY=1,
            MATERIAL="solid lumber",
            PURCHASE="2×6 × 8′",
            ROUGH_THICKNESS=1.5,
            ROUGH_WIDTH=3.5,
            ROUGH_LENGTH=rnd(ly["gate_inner"] + 3.0),
            FINISHED_THICKNESS=1.5,
            FINISHED_WIDTH=3.5,
            FINISHED_LENGTH=rnd(ly["gate_inner"] + 2.0 * 1.25),
            JOINERY="hozo, drawbored",
            TOLERANCE_CLASS="T2",
        ),
        _part(
            PART_ID="G-008",
            PART_NAME="Gate diagonal brace",
            PART_CATEGORY="G",
            ASSEMBLY="A-030 GATE",
            QUANTITY=1,
            MATERIAL="solid lumber",
            PURCHASE="2×4 / 2×6 offcut",
            ROUGH_THICKNESS=1.5,
            ROUGH_WIDTH=3.5,
            ROUGH_LENGTH=rnd(math.hypot(ly["gate_inner"], ly["gate_h"] - 10.0) + 1.0),
            FINISHED_THICKNESS=1.5,
            FINISHED_WIDTH=3.5,
            FINISHED_LENGTH=rnd(math.hypot(ly["gate_inner"], ly["gate_h"] - 10.0)),
            JOINERY="half-lap into G-003 and G-007 (compression brace, hinge-bottom to latch-top)",
            FIT="GLUE optional on laps; still mechanically captured",
        ),
        _part(
            PART_ID="G-009",
            PART_NAME="Gate infill board",
            PART_CATEGORY="B",
            ASSEMBLY="A-030 GATE",
            QUANTITY=ly["n_gate_boards"],
            MATERIAL="solid lumber",
            SPECIES="1×6",
            PURCHASE="1×6 × 8′",
            ROUGH_THICKNESS=0.75,
            ROUGH_WIDTH=5.5,
            ROUGH_LENGTH=rnd(ly["gate_h"] - 8.0 + 0.5),
            FINISHED_THICKNESS=0.75,
            FINISHED_WIDTH=5.5,
            FINISHED_LENGTH=rnd(ly["gate_h"] - 8.0),
            JOINERY="groove / stop in gate rails — FLOATING",
            MOVEMENT="FLOATING",
        ),
        _part(
            PART_ID="G-010",
            PART_NAME="Sliding latch bar",
            PART_CATEGORY="G",
            ASSEMBLY="A-030 GATE",
            QUANTITY=1,
            MATERIAL="white oak (preferred) or hard maple",
            SPECIES="oak",
            PURCHASE="1×4 oak × 4′ / 2×4",
            ROUGH_THICKNESS=v("latch_bar_t"),
            ROUGH_WIDTH=v("latch_bar_w"),
            ROUGH_LENGTH=rnd(v("latch_bar_l") + 1.0),
            FINISHED_THICKNESS=v("latch_bar_t"),
            FINISHED_WIDTH=v("latch_bar_w"),
            FINISHED_LENGTH=v("latch_bar_l"),
            JOINERY="slides in G-002 into L-001 mortise (Latch B default); cross-peg hole",
            FIT="SLIDING",
            TOLERANCE_CLASS="T2",
        ),
    ]

    wedges = _part(
        PART_ID="W-001",
        PART_NAME="Kusabi locking wedge",
        PART_CATEGORY="W",
        ASSEMBLY="A-020 PRIVACY_FRAME",
        QUANTITY=17,  # 3 rails × 3 posts + 2 sills × 4 ties
        MATERIAL="white oak / hard maple",
        SPECIES="oak",
        PURCHASE="2×4 × 8′ ripped",
        ROUGH_THICKNESS=v("kusabi_t"),
        ROUGH_WIDTH=v("kusabi_w"),
        ROUGH_LENGTH=rnd(v("kusabi_l") + 0.5),
        FINISHED_THICKNESS=v("kusabi_t"),
        FINISHED_WIDTH=v("kusabi_w"),
        FINISHED_LENGTH=v("kusabi_l"),
        JOINERY="driven in cheek slot; NEVER glue",
        FIT="INTERFERENCE (tapered drive)",
        TOLERANCE_CLASS="T2",
        NOTES="9 rail + 8 sill/tie + 3 extras. Label bag for winter. NEVER glue.",
    )
    pegs = _part(
        PART_ID="W-002",
        PART_NAME="Drawbore / latch oak peg",
        PART_CATEGORY="W",
        ASSEMBLY="A-030 GATE",
        QUANTITY=14,
        MATERIAL="white oak",
        PURCHASE="1×4 oak × 4′",
        ROUGH_THICKNESS=v("peg_d"),
        ROUGH_WIDTH=v("peg_d"),
        ROUGH_LENGTH=2.5,
        FINISHED_THICKNESS=v("peg_d"),
        FINISHED_WIDTH=v("peg_d"),
        FINISHED_LENGTH=2.25,
        JOINERY="drawbore 1/8″ offset",
        FIT="DRAWBORED",
        TOLERANCE_CLASS="T2",
        NOTES="10 gate M&T + 1 cap scarf + 1 latch cross-peg + 2 spare",
    )
    pintle = _part(
        PART_ID="W-003",
        PART_NAME="Wooden pintle (or stainless upgrade)",
        PART_CATEGORY="W",
        ASSEMBLY="A-030 GATE",
        QUANTITY=2,
        MAKE_OR_BUY="MAKE",
        MATERIAL="white oak / hard maple (BUY: stainless pintle set)",
        PURCHASE="oak offcut or H-003",
        ROUGH_THICKNESS=1.0,
        ROUGH_WIDTH=1.0,
        ROUGH_LENGTH=4.0,
        FINISHED_THICKNESS=0.75,
        FINISHED_WIDTH=0.75,
        FINISHED_LENGTH=3.5,
        JOINERY="gudgeon in G-001; pintle in L-002",
        FIT="LOCATIONAL / lift-off",
        NOTES="Gate lifts straight up for winter. Metal optional — only purchased metal on fence if used.",
    )

    civil = [
        _part(
            PART_ID="F-001",
            PART_NAME="Driveway dodai sill",
            PART_CATEGORY="F",
            ASSEMBLY="A-001 BASE",
            QUANTITY=1,
            MATERIAL="solid lumber",
            SPECIES="SPF/SYP paint-grade (cedar optional)",
            PURCHASE="4×6 × 16′",
            ROUGH_THICKNESS=3.5,
            ROUGH_WIDTH=5.5,
            ROUGH_LENGTH=rnd(ly["sill_len"] + 1.0),
            FINISHED_THICKNESS=3.5,
            FINISHED_WIDTH=5.5,
            FINISHED_LENGTH=ly["sill_len"],
            BOARD_FEET=bf_nominal(4, 6, 16),
            JOINERY="half-lap + peg at four F-003 ties; sits on H-001 pads — NO pour",
            NOTES="High side. Sit on existing driveway. Rubber pads protect pavement.",
            TOLERANCE_CLASS="T2",
        ),
        _part(
            PART_ID="F-002",
            PART_NAME="Garden dodai sill",
            PART_CATEGORY="F",
            ASSEMBLY="A-001 BASE",
            QUANTITY=1,
            MATERIAL="solid lumber",
            SPECIES="SPF/SYP paint-grade (cedar optional)",
            PURCHASE="4×6 × 16′",
            ROUGH_THICKNESS=3.5,
            ROUGH_WIDTH=5.5,
            ROUGH_LENGTH=rnd(ly["sill_len"] + 1.0),
            FINISHED_THICKNESS=3.5,
            FINISHED_WIDTH=5.5,
            FINISHED_LENGTH=ly["sill_len"],
            BOARD_FEET=bf_nominal(4, 6, 16),
            JOINERY="half-lap + peg at four F-003 ties; bears on F-004 packing",
            NOTES="Low side. Level with F-001 via timber packing — drop_off TBM. No cement.",
            TOLERANCE_CLASS="T2",
        ),
        _part(
            PART_ID="F-003",
            PART_NAME="Cross-tie / post shoe",
            PART_CATEGORY="F",
            ASSEMBLY="A-001 BASE",
            QUANTITY=4,
            MATERIAL="solid lumber",
            SPECIES="SPF/SYP paint-grade",
            PURCHASE="4×6 × 8′",
            ROUGH_THICKNESS=3.5,
            ROUGH_WIDTH=5.5,
            ROUGH_LENGTH=rnd(ly["tie_len"] + 1.0),
            FINISHED_THICKNESS=3.5,
            FINISHED_WIDTH=5.5,
            FINISHED_LENGTH=ly["tie_len"],
            BOARD_FEET=bf_nominal(4, 6, 8),
            JOINERY="mortise for post foot tenon; half-lap to F-001/F-002",
            NOTES="One at each post CL. Posts drop in for winter lift-out.",
            TOLERANCE_CLASS="T2",
            HANDED="IDENTICAL",
        ),
        _part(
            PART_ID="F-004",
            PART_NAME="Garden packing crib",
            PART_CATEGORY="F",
            ASSEMBLY="A-001 BASE",
            QUANTITY=4,
            MATERIAL="solid lumber",
            SPECIES="SPF/SYP 2×6 stacked",
            PURCHASE="2×6 × 8′",
            ROUGH_THICKNESS=1.5,
            ROUGH_WIDTH=v("pack_w"),
            ROUGH_LENGTH=v("pack_len"),
            FINISHED_THICKNESS=ly["pack_h"],
            FINISHED_WIDTH=v("pack_w"),
            FINISHED_LENGTH=v("pack_len"),
            BOARD_FEET=0,
            JOINERY="dry-stacked layers; no glue; shims to TBM drop_off",
            NOTES=f'{ly["pack_layers"]} layers of 1.50″ 2×6 ≈ {ly["pack_h"]}" to match estimated {v("drop_off")}" drop. Field-fit.',
            MOVEMENT="SLOTTED / shimmable",
        ),
        _part(
            PART_ID="F-005",
            PART_NAME="Ballast box (empty timber frame)",
            PART_CATEGORY="F",
            ASSEMBLY="A-001 BASE",
            QUANTITY=4,
            MATERIAL="solid lumber",
            SPECIES="SPF/SYP 2×6",
            PURCHASE="2×6 × 8′",
            ROUGH_THICKNESS=1.5,
            ROUGH_WIDTH=1.5,
            ROUGH_LENGTH=rnd(2 * (v("ballast_box_x") + v("ballast_box_y")) + 8),
            FINISHED_THICKNESS=v("ballast_box_h"),
            FINISHED_WIDTH=v("ballast_box_y") + 3.0,
            FINISHED_LENGTH=rnd(2 * (v("ballast_box_x") + v("ballast_box_y"))),
            BOARD_FEET=0,
            JOINERY="pegged frame; sits on sills at four corners",
            NOTES="Holds H-007 sandbags. Empty for winter. Not a stone pad. Not poured.",
        ),
        _part(
            PART_ID="F-006",
            PART_NAME="Sujikai base brace",
            PART_CATEGORY="F",
            ASSEMBLY="A-001 BASE",
            QUANTITY=4,
            MATERIAL="solid lumber",
            SPECIES="SPF/SYP",
            PURCHASE="2×6 × 8′",
            ROUGH_THICKNESS=1.5,
            ROUGH_WIDTH=v("brace_w"),
            ROUGH_LENGTH=rnd(ly["brace_len"] + 1.0),
            FINISHED_THICKNESS=1.5,
            FINISHED_WIDTH=v("brace_w"),
            FINISHED_LENGTH=ly["brace_len"],
            BOARD_FEET=0,
            JOINERY="housed half-lap into post and sill; oak peg; NO glue",
            NOTES="Transfers wind moment into ladder. Two garden-side, two driveway-side.",
            TOLERANCE_CLASS="T2",
        ),
        _part(
            PART_ID="H-001",
            PART_NAME="Rubber furniture pad (driveway sill)",
            PART_CATEGORY="H",
            ASSEMBLY="A-001 BASE",
            QUANTITY=8,
            MAKE_OR_BUY="BUY",
            MATERIAL="rubber / composite",
            PURCHASE="4″ furniture / anti-vibration pads",
            ROUGH_THICKNESS=v("furniture_pad_t"),
            ROUGH_WIDTH=4.0,
            ROUGH_LENGTH=4.0,
            FINISHED_THICKNESS=v("furniture_pad_t"),
            FINISHED_WIDTH=4.0,
            FINISHED_LENGTH=4.0,
            JOINERY="n/a",
            NOTES="Under F-001. Protects pavement. No fasteners into driveway.",
            GRAIN_DIRECTION="n/a",
        ),
        _part(
            PART_ID="H-002",
            PART_NAME="Optional oak latch strike (Latch A opt-in)",
            PART_CATEGORY="H",
            ASSEMBLY="A-030 GATE",
            QUANTITY=1,
            MAKE_OR_BUY="MAKE",
            MATERIAL="white oak block",
            PURCHASE="oak offcut",
            ROUGH_LENGTH=6.0,
            FINISHED_LENGTH=6.0,
            ROUGH_THICKNESS=1.5,
            ROUGH_WIDTH=3.5,
            FINISHED_THICKNESS=1.5,
            FINISHED_WIDTH=3.5,
            NOTES="DEFAULT is Latch B (mortise in L-001). Do not epoxy into concrete.",
        ),
        _part(
            PART_ID="H-003",
            PART_NAME="Optional stainless pintle set",
            PART_CATEGORY="H",
            ASSEMBLY="A-030 GATE",
            QUANTITY=1,
            MAKE_OR_BUY="BUY",
            MATERIAL="stainless steel",
            PURCHASE="lift-off pintle hinges, 2-pack",
            NOTES="Replaces W-003 if preferred. Only metal on fence if used.",
            ROUGH_THICKNESS=0,
            ROUGH_WIDTH=0,
            ROUGH_LENGTH=0,
            FINISHED_THICKNESS=0,
            FINISHED_WIDTH=0,
            FINISHED_LENGTH=0,
        ),
        _part(
            PART_ID="H-004",
            PART_NAME="Keyed padlock hasp (optional)",
            PART_CATEGORY="H",
            ASSEMBLY="A-030 GATE",
            QUANTITY=1,
            MAKE_OR_BUY="BUY",
            MATERIAL="stainless / galvanized",
            NOTES="On latch bar — not structural",
            ROUGH_THICKNESS=0,
            ROUGH_WIDTH=0,
            ROUGH_LENGTH=0,
            FINISHED_THICKNESS=0,
            FINISHED_WIDTH=0,
            FINISHED_LENGTH=0,
        ),
        _part(
            PART_ID="H-005",
            PART_NAME="Exterior primer + owner gray enamel",
            PART_CATEGORY="H",
            ASSEMBLY="A-040 FINISH",
            QUANTITY=1,
            MAKE_OR_BUY="BUY",
            MATERIAL="exterior acrylic / alkyd",
            NOTES="Mask wedges, tenons, sill laps, pintle faces",
            ROUGH_THICKNESS=0,
            ROUGH_WIDTH=0,
            ROUGH_LENGTH=0,
            FINISHED_THICKNESS=0,
            FINISHED_WIDTH=0,
            FINISHED_LENGTH=0,
        ),
        _part(
            PART_ID="H-007",
            PART_NAME="Removable sandbag ballast",
            PART_CATEGORY="H",
            ASSEMBLY="A-001 BASE",
            QUANTITY=0,
            MAKE_OR_BUY="BUY",
            MATERIAL="woven poly sandbag + sand (or water jugs)",
            PURCHASE="50 lb bags",
            ROUGH_THICKNESS=0,
            ROUGH_WIDTH=0,
            ROUGH_LENGTH=0,
            FINISHED_THICKNESS=0,
            FINISHED_WIDTH=0,
            FINISHED_LENGTH=0,
            NOTES="Qty from wind/ballast calc. Store dry in winter. NOT poured concrete. NOT a stone pad.",
            GRAIN_DIRECTION="n/a",
        ),
    ]

    allp = posts + rails + [cap, cap_stub] + boards + gate_parts + [wedges, pegs, pintle] + civil
    return allp


# ---------------------------------------------------------------------------
# Joints
# ---------------------------------------------------------------------------
def joints(ly=None):
    ly = ly or layout()
    js = []

    def J(**kw):
        d = {
            "FIT_CLASS": "SNUG",
            "ASSEMBLY_DIRECTION": "+X nuki / −Z tenon",
            "GLUE": "NO — winter removable",
        }
        d.update(kw)
        js.append(d)

    n = 1
    for rail, cl in zip(("R-001", "R-002", "R-003"), ly["rail_cls"]):
        for post in ("L-002", "L-003", "L-004"):
            J(
                JOINT_ID=f"J-{n:03d}",
                JOINT_TYPE="nuki 貫 + kusabi",
                PART_A=post,
                PART_B=rail,
                LOCATION=f"{post} × {rail} @ z_cl={cl}\"",
                MORTISE_WIDTH=v("rail_t") + v("nuki_fit"),
                MORTISE_HEIGHT=v("rail_h"),
                MORTISE_DEPTH="THROUGH (post_x)",
                TENON_WIDTH=v("rail_t"),
                TENON_HEIGHT=v("rail_h"),
                TENON_LENGTH="THROUGH + rail_reveal",
                FIT_CLASS="SLIDING then INTERFERENCE via W-001",
                ASSEMBLY_DIRECTION="+X (rails withdraw toward P3 for winter)",
            )
            n += 1
    for post in ly["posts"]:
        J(
            JOINT_ID=f"J-{n:03d}",
            JOINT_TYPE="foot tenon into cross-tie shoe",
            PART_A=post["id"],
            PART_B="F-003",
            LOCATION=f"{post['mark']} cx={post['cx']}\" into tie at y=0",
            TENON_WIDTH=v("post_tenon_x"),
            TENON_HEIGHT=v("post_tenon_y"),
            TENON_LENGTH=v("post_tenon_h"),
            SHOULDER="0.50″ all around at sill top (datum)",
            FIT_CLASS="CLEARANCE / GRAVITY drop-in — winter lift-out",
            ASSEMBLY_DIRECTION="−Z drop-in",
            GLUE="NO",
        )
        n += 1
    for tie_i, post in enumerate(ly["posts"], 1):
        J(
            JOINT_ID=f"J-{n:03d}",
            JOINT_TYPE="half-lap pegged (sill × tie)",
            PART_A="F-001 / F-002",
            PART_B="F-003",
            LOCATION=f"tie at {post['mark']}",
            FIT_CLASS="SNUG + oak peg",
            GLUE="NO",
            NOTES="Ladder frame sits on grade. No fasteners into pavement.",
        )
        n += 1
    J(
        JOINT_ID=f"J-{n:03d}",
        JOINT_TYPE="sujikai housed half-lap",
        PART_A="F-006",
        PART_B="L-00x / F-001 / F-002",
        LOCATION="post to sill, z≈18″ AFF",
        FIT_CLASS="SNUG + peg",
        GLUE="NO",
    )
    n += 1
    J(
        JOINT_ID=f"J-{n:03d}",
        JOINT_TYPE="kama-tsugi 鎌継ぎ",
        PART_A="C-001-L",
        PART_B="C-001-R",
        LOCATION="centered on L-003",
        DOWEL_DIAMETER=v("peg_d"),
        DRAWBORE_OFFSET=v("drawbore_offset"),
        FIT_CLASS="DRAWBORED",
        GLUE="NO (or hide glue if not disassembling cap)",
    )
    n += 1
    for g_rail in ("G-003", "G-004", "G-005", "G-006", "G-007"):
        for stile in ("G-001", "G-002"):
            J(
                JOINT_ID=f"J-{n:03d}",
                JOINT_TYPE="hozo ほぞ drawbored M&T",
                PART_A=stile,
                PART_B=g_rail,
                LOCATION=f"{stile} × {g_rail}",
                TENON_THICKNESS=rnd(v("leaf_t") / 3.0),
                TENON_LENGTH=1.25,
                DOWEL_DIAMETER=v("peg_d"),
                DRAWBORE_OFFSET=v("drawbore_offset"),
                FIT_CLASS="DRAWBORED",
                GLUE="optional hide glue — gate is a keep-together subassembly",
                NOTES="tenon ≈ 1/3 stock (rule); cheeks remain ≥ 1/3",
            )
            n += 1
    J(
        JOINT_ID=f"J-{n:03d}",
        JOINT_TYPE="half-lap brace",
        PART_A="G-008",
        PART_B="G-003 / G-007",
        LOCATION="compression diagonal",
        FIT_CLASS="GLUE + geometry",
        ASSEMBLY_DIRECTION="in plane of leaf",
    )
    n += 1
    J(
        JOINT_ID=f"J-{n:03d}",
        JOINT_TYPE="floating groove",
        PART_A="R-001..R-003 / C-001",
        PART_B="B-001..B-003",
        LOCATION="rail edges",
        MORTISE_DEPTH=v("groove_d"),
        MORTISE_WIDTH=v("groove_w"),
        FIT_CLASS="CLEARANCE",
        MOVEMENT="FLOATING",
        GLUE="NO",
    )
    n += 1
    J(
        JOINT_ID=f"J-{n:03d}",
        JOINT_TYPE="pintle / gudgeon",
        PART_A="L-002",
        PART_B="G-001",
        LOCATION="two pintles, lift-off +Z",
        FIT_CLASS="LOCATIONAL",
        ASSEMBLY_DIRECTION="+Z to remove",
    )
    n += 1
    J(
        JOINT_ID=f"J-{n:03d}",
        JOINT_TYPE="sliding latch",
        PART_A="G-010",
        PART_B="H-002 or L-001",
        LOCATION=f"z_cl={v('rail_cl_2')}\" (R2)",
        FIT_CLASS="SLIDING",
        NOTES="DEFAULT Latch B mortise in L-001. No epoxy, no house pour.",
    )
    return js


def hardware():
    return [
        {
            "HARDWARE_ID": "H-001",
            "DESCRIPTION": "Rubber / composite furniture pad, 4″ sq × ½″, under driveway sill",
            "STANDARD": "furniture / anti-vibration",
            "SIZE": "4″ × 4″ × 0.50″",
            "QTY": 8,
            "MATERIAL": "rubber",
            "MAKE_OR_BUY": "BUY",
        },
        {
            "HARDWARE_ID": "H-002",
            "DESCRIPTION": "Optional oak latch strike block — Latch B (mortise in L-001) is default; no epoxy into concrete",
            "STANDARD": "site",
            "SIZE": "1.50″ × 3.50″ × 6.00″",
            "QTY": 1,
            "MATERIAL": "white oak",
            "MAKE_OR_BUY": "MAKE",
        },
        {
            "HARDWARE_ID": "H-003",
            "DESCRIPTION": "Optional stainless lift-off pintle hinge set, 2 leaves",
            "STANDARD": "manufacturer",
            "SIZE": "to suit 1.50″ gate + 3.50″ post",
            "QTY": 1,
            "MATERIAL": "stainless steel",
            "MAKE_OR_BUY": "BUY",
        },
        {
            "HARDWARE_ID": "H-004",
            "DESCRIPTION": "Optional keyed padlock hasp for latch bar",
            "STANDARD": "manufacturer",
            "SIZE": "to suit G-010",
            "QTY": 1,
            "MATERIAL": "stainless or galvanized",
            "MAKE_OR_BUY": "BUY",
        },
        {
            "HARDWARE_ID": "H-005",
            "DESCRIPTION": "Exterior primer + owner gray enamel, 2 finish coats",
            "STANDARD": "exterior grade",
            "SIZE": "kit",
            "QTY": 1,
            "MATERIAL": "coating",
            "MAKE_OR_BUY": "BUY",
        },
        {
            "HARDWARE_ID": "H-007",
            "DESCRIPTION": "Removable 50 lb sandbags (or water jugs) in F-005 boxes — wind ballast, not a pad",
            "STANDARD": "woven poly bag",
            "SIZE": "50 lb",
            "QTY": "see ballast.n_bags",
            "MATERIAL": "sand + bag",
            "MAKE_OR_BUY": "BUY",
        },
    ]


def assemblies():
    return {
        "A-000 MASTER": [
            "A-001 BASE",
            "A-010 POSTS",
            "A-020 PRIVACY_FRAME",
            "A-030 GATE",
            "A-040 FINISH",
        ],
        "A-001 BASE": ["F-001", "F-002", "F-003×4", "F-004×4", "F-005×4", "F-006×4", "H-001×8", "H-007"],
        "A-010 POSTS": ["L-001", "L-002", "L-003", "L-004", "C-002"],
        "A-020 PRIVACY_FRAME": [
            "R-001",
            "R-002",
            "R-003",
            "B-001×16",
            "B-002×32",
            "B-003×16",
            "C-001",
            "W-001×17",
        ],
        "A-030 GATE": [
            "G-001",
            "G-002",
            "G-003",
            "G-004",
            "G-005",
            "G-006",
            "G-007",
            "G-008",
            "G-009×n",
            "G-010",
            "W-002",
            "W-003",
        ],
        "A-040 FINISH": ["H-005"],
    }


def operations():
    """Typical routing — posts shown fully; others summarized by family."""
    post_ops = [
        ("OP010", "Rough crosscut", "circular / miter saw", "blank +1″", "T1 ±1/8″"),
        ("OP020", "Joint reference face", "jointer / plane / factory S4S", "FACE A", "T1"),
        ("OP030", "Joint reference edge", "same", "EDGE B", "T1"),
        ("OP040", "Verify section 3.50×5.50", "caliper / combo square", "S4S skip if in-tol", "T1 ±1/32″"),
        ("OP050", "Final length post_blank_l", "stop S-014", "DATUM END A = tenon tip; overall", "T1 ±1/32″"),
        ("OP060", "Shoulder foot tenon 2.50×4.50×3.50", "saw + chisel / router", "measure from sill-shoulder datum", "T2 ±1/32″"),
        ("OP070", "Nuki mortises at CL 10 / 28 / 46 AFF", "chisel / mortiser", "from DATUM END = shoulder (sill top)", "T2"),
        ("OP080", "Kusabi slots (L-002/003/004)", "saw + chisel", "see J-401", "T2"),
        ("OP090", "Pintle mortises (L-002 only)", "drill + chisel", "two, aligned", "T2"),
        ("OP100", "Seal end grain; dry-fit in F-003", "brush", "tenon faces unpainted contact", "—"),
    ]
    return {
        "L-001": [o for o in post_ops if "Kusabi" not in o[1] and "Pintle" not in o[1]]
        + [("OP085", "Latch-B mortise (if used)", "chisel", "CL 28″ AFF", "T2")],
        "L-002": post_ops,
        "L-003": [o for o in post_ops if "Pintle" not in o[1]],
        "L-004": [o for o in post_ops if "Pintle" not in o[1]],
        "R-00x": [
            ("OP010", "Crosscut finished length nuki_len", "stop S-021", "DATUM END = P1 reveal", "T1"),
            ("OP020", "Plow grooves ⅜×⅞ both edges", "router table", "FACE A against fence", "T2"),
            ("OP030", "Mark nuki stations at post CLs", "square", "from DATUM END", "T2"),
            ("OP040", "Ease arrises; do not paint locking faces yet", "block plane", "", "—"),
        ],
        "G-00x": [
            ("OP010", "Mill stiles/rails to finished section", "saw", "", "T1"),
            ("OP020", "Cut hozo; dry fit", "chisel", "tenon ⅓ stock", "T2"),
            ("OP030", "Drawbore ⅛″ toward shoulder", "⅜″ brad point", "offset toward shoulder", "T2"),
            ("OP040", "Half-lap brace", "saw", "", "T2"),
            ("OP050", "Peg, trim, hang on pintles", "mallet", "lift-off check", "T2"),
        ],
    }


def stops():
    ly = layout()
    return [
        {
            "SETUP": "S-014",
            "TOOL": "Miter saw + stop (or circular saw + jig)",
            "STOP": f'{ly["post_blank_l"]:.3f}"',
            "PARTS": ["L-001", "L-002", "L-003", "L-004"],
            "NOTE": "DO NOT MOVE STOP until all four posts are cut.",
        },
        {
            "SETUP": "S-021",
            "TOOL": "Track / circular saw + stop",
            "STOP": f'{ly["nuki_len"]:.3f}"',
            "PARTS": ["R-001", "R-002", "R-003"],
            "NOTE": "Three identical nuki rails.",
        },
        {
            "SETUP": "S-030",
            "TOOL": "Miter saw + stop",
            "STOP": f'{ly["courses"][1]["h"]:.3f}"',
            "PARTS": ["B-002 × 32"],
            "NOTE": "Largest repeating board. Then reset for B-001 and B-003.",
        },
        {
            "SETUP": "S-040",
            "TOOL": "Mortise gauge from FACE A",
            "STOP": "nuki mortise 1.50″ × 7.25″ through",
            "PARTS": ["L-001..L-004"],
            "NOTE": "CL AFF 10.000 / 28.000 / 46.000 from sill-shoulder datum.",
        },
    ]


def inspection():
    ly = layout()
    return [
        {"QC": "QC-01", "CHECK": "Confirm overall opening 143.000″ ± 0.25″ on site", "CLASS": "VERIFIED/TBM", "TOL": "T1"},
        {"QC": "QC-02", "CHECK": "Measure driveway→garden drop; set P.drop_off; stack F-004 packing — do not pour", "CLASS": "TBM", "TOL": "T1"},
        {"QC": "QC-03", "CHECK": "Stock moisture — avoid wet framing; paint-grade OK", "CLASS": "T0", "TOL": "—"},
        {"QC": "QC-04", "CHECK": f'Four posts finished length {ly["post_blank_l"]:.3f}" within ±1/32"', "CLASS": "T2", "TOL": "±0.031"},
        {"QC": "QC-05", "CHECK": "Paired nuki rails R-001..003 identical length and groove", "CLASS": "T2", "TOL": "±0.031"},
        {"QC": "QC-06", "CHECK": "Mortise CL AFF 10.000 / 28.000 / 46.000 from sill-shoulder datum", "CLASS": "T2", "TOL": "±0.062"},
        {"QC": "QC-07", "CHECK": "Foot tenon 2.500×4.500×3.500 enters F-003; lifts out for winter", "CLASS": "T2", "TOL": "+0.03/−0"},
        {"QC": "QC-08", "CHECK": "Dry-assemble privacy: diagonals / plumb / no racking", "CLASS": "T1", "TOL": "plumb 1/8″ in 65″"},
        {"QC": "QC-09", "CHECK": "Gate leaf swings; lift-off pintles; latch bar travels 4″ into receiver", "CLASS": "T2", "TOL": "—"},
        {"QC": "QC-10", "CHECK": "No glue on kusabi or nuki locking faces", "CLASS": "T0", "TOL": "binary"},
        {"QC": "QC-11", "CHECK": "Paint masked on tenons, wedges, sill laps, pintle barrels", "CLASS": "T0", "TOL": "—"},
        {"QC": "QC-12", "CHECK": "Winter knock-down rehearsal before first storm season", "CLASS": "T0", "TOL": "—"},
        {"QC": "QC-13", "CHECK": "Ladder sills sit level; packing matches measured drop; no excavation", "CLASS": "T1", "TOL": "±0.125"},
        {"QC": "QC-14", "CHECK": "Gate vs cap clearance ≥ 0.50″", "CLASS": "T2", "TOL": "min 0.38"},
        {"QC": "QC-15", "CHECK": "Sandbag count ≥ ballast.n_bags in four F-005 boxes; empty for winter", "CLASS": "T1", "TOL": "count"},
        {"QC": "QC-16", "CHECK": "No concrete, no post holes, no gravel pad on this build", "CLASS": "T0", "TOL": "binary"},
    ]


def qa_geometry(ly, parts_list):
    issues = []
    # gate vs cap
    gate_top = v("gate_bottom_clear") + ly["gate_h"]
    cap_bot = v("overall_height") - v("cap_t")
    gap = rnd(cap_bot - gate_top)
    if gap < 0.38:
        issues.append({"level": "CRITICAL", "item": "gate/cap collision", "detail": f"gap={gap}"})
    else:
        issues.append({"level": "OK", "item": "gate/cap clearance", "detail": f"{gap}\" ≥ 0.50\" spec"})
    # nuki cheek
    if ly["nuki_cheek_y"] < 0.75:
        issues.append({"level": "CRITICAL", "item": "nuki cheek too thin", "detail": ly["nuki_cheek_y"]})
    else:
        issues.append({"level": "OK", "item": "nuki cheek", "detail": f'{ly["nuki_cheek_y"]}" each side of 1.50″ rail in 5.50″ post'})
    # tenon cheeks
    if ly["cheek_x"] < 0.375 or ly["cheek_y"] < 0.375:
        issues.append({"level": "WEAK", "item": "foot tenon shoulder", "detail": ly})
    else:
        issues.append({"level": "OK", "item": "foot tenon shoulders", "detail": f'{ly["cheek_x"]}" × {ly["cheek_y"]}"'})
    # bay boards fit
    if ly["used_bay"] > ly["bay_clear"] + 0.01:
        issues.append({"level": "CRITICAL", "item": "boards overflow bay", "detail": ly["used_bay"]})
    else:
        issues.append({"level": "OK", "item": "bay board pack", "detail": f'{ly["n_bay"]} pcs, used {ly["used_bay"]}" in {ly["bay_clear"]}"'})
    # duplicate part ids
    ids = [p["PART_ID"] for p in parts_list]
    if len(ids) != len(set(ids)):
        issues.append({"level": "CRITICAL", "item": "duplicate PART_ID"})
    else:
        issues.append({"level": "OK", "item": "unique PART_IDs", "detail": str(len(ids))})
    return issues


def nest_lumber(parts_list):
    """Greedy first-fit decreasing onto 8′ / 10′ / 12′ purchase lengths."""
    kerf = v("saw_kerf")
    families = {
        "4x6x8": {"nom": (4, 6), "len": 96.0, "parts": []},
        "4x6x16": {"nom": (4, 6), "len": 192.0, "parts": []},
        "2x8x10": {"nom": (2, 8), "len": 120.0, "parts": []},
        "2x8x12": {"nom": (2, 8), "len": 144.0, "parts": []},
        "2x6x8": {"nom": (2, 6), "len": 96.0, "parts": []},
        "1x6x8": {"nom": (1, 6), "len": 96.0, "parts": []},
        "2x4x8": {"nom": (2, 4), "len": 96.0, "parts": []},
        "oak_1x4x4": {"nom": (1, 4), "len": 48.0, "parts": []},
    }
    assign = {
        "L-001": "4x6x8",
        "L-002": "4x6x8",
        "L-003": "4x6x8",
        "L-004": "4x6x8",
        "F-001": "4x6x16",
        "F-002": "4x6x16",
        "F-003": "4x6x8",
        "R-001": "2x8x10",
        "R-002": "2x8x10",
        "R-003": "2x8x10",
        "C-001": "2x8x12",
        "C-002": "2x8x12",
        "G-001": "2x6x8",
        "G-002": "2x6x8",
        "G-003": "2x6x8",
        "G-004": "2x6x8",
        "G-005": "2x6x8",
        "G-006": "2x6x8",
        "G-007": "2x6x8",
        "G-008": "2x6x8",
        "F-004": "2x6x8",
        "F-005": "2x6x8",
        "F-006": "2x6x8",
        "B-001": "1x6x8",
        "B-002": "1x6x8",
        "B-003": "1x6x8",
        "G-009": "1x6x8",
        "W-001": "2x4x8",
        "G-010": "oak_1x4x4",
        "W-002": "oak_1x4x4",
        "W-003": "oak_1x4x4",
    }
    pieces = []
    for p in parts_list:
        fam = assign.get(p["PART_ID"])
        if not fam:
            continue
        q = int(p["QUANTITY"])
        fl = float(p["FINISHED_LENGTH"])
        for i in range(q):
            pieces.append({"PART_ID": p["PART_ID"], "i": i + 1, "len": fl, "fam": fam})

    boards = []
    for fam, spec in families.items():
        fam_pcs = sorted([x for x in pieces if x["fam"] == fam], key=lambda x: -x["len"])
        bins = []  # list of remaining
        contents = []
        for pc in fam_pcs:
            placed = False
            for bi, rem in enumerate(bins):
                if pc["len"] + (kerf if contents[bi] else 0) <= rem + 1e-9:
                    need = pc["len"] + (kerf if contents[bi] else 0)
                    bins[bi] -= need
                    contents[bi].append(pc)
                    placed = True
                    break
            if not placed:
                bins.append(spec["len"] - pc["len"])
                contents.append([pc])
        for i, (rem, cont) in enumerate(zip(bins, contents), 1):
            used = spec["len"] - rem
            boards.append(
                {
                    "BOARD_ID": f"{fam}-{i:02d}",
                    "PURCHASE": fam,
                    "LENGTH": spec["len"],
                    "PARTS": [f"{c['PART_ID']}:{c['len']}" for c in cont],
                    "USED": rnd(used),
                    "REMAINDER": rnd(max(rem, 0)),
                    "YIELD_PCT": rnd(100.0 * used / spec["len"], 1),
                    "BF": bf_nominal(*spec["nom"], spec["len"] / 12.0),
                }
            )
    buy = {}
    for b in boards:
        buy[b["PURCHASE"]] = buy.get(b["PURCHASE"], 0) + 1
    net_bf = rnd(sum(b["BF"] for b in boards), 2)
    proc_bf = rnd(net_bf * (1.0 + v("waste_factor")), 2)
    return {
        "kerf": kerf,
        "boards": boards,
        "buy_counts": buy,
        "net_bf": net_bf,
        "waste_factor": v("waste_factor"),
        "procurement_bf": proc_bf,
        "note": "Nesting uses FINISHED lengths + kerf. Extra waste_factor covers defects/joinery practice.",
    }


def ballast(ly=None):
    """Planning overturning check — not a PE stamp. No concrete volume."""
    ly = ly or layout()
    L = ly["overall_length"]
    H = ly["overall_height"]
    area_sf = rnd((L / 12.0) * (H / 12.0), 2)
    q = v("wind_psf")
    F = rnd(area_sf * q, 1)
    M = rnd(F * (H / 2.0) / 12.0, 1)
    spread_ft = v("base_spread_cl") / 12.0
    fs = v("wind_fs")
    req = rnd(fs * M / max(spread_ft, 0.1), 1)
    bag = v("ballast_bag_lb")
    n_bags = int(math.ceil(req / bag))
    return {
        "wind_area_sf": area_sf,
        "planning_pressure_psf": q,
        "wind_force_lb": F,
        "overturning_ftlb": M,
        "base_spread_in": v("base_spread_cl"),
        "fs": fs,
        "required_lb": req,
        "bag_lb": bag,
        "n_bags": n_bags,
        "concrete_yd3": 0.0,
        "gravel_yd3": 0.0,
        "note": "NO pour, NO post holes, NO stone pad. Removable sandbags in F-005. Planning calc only — not PE certified.",
    }


def concrete_vol(ly=None):
    """Deprecated alias — Rev D has no concrete. Returns ballast() for old callers."""
    return ballast(ly)


def decisions():
    return [
        {
            "ID": "D-001",
            "Decision": "4×6 posts not 4×4 / 2×4",
            "Reason": "nuki cheeks and overturning couple; owner asked to overbuild",
            "Parts": "L-001..004",
        },
        {
            "ID": "D-002",
            "Decision": "2×8 Prairie bands on edge, not 2×4",
            "Reason": "Prairie read + nuki bearing area",
            "Parts": "R-001..003",
        },
        {
            "ID": "D-003",
            "Decision": "No nails/screws in timber",
            "Reason": "owner + winter knock-down + fastener corrosion in Buffalo",
            "Parts": "all MAKE lumber",
        },
        {
            "ID": "D-004",
            "Decision": "Sit-on-grade timber ladder (dodai + cross-ties) instead of poured pad/piers",
            "Reason": "Owner: entirely freestanding — no post holes, no cement, no massive stone pads. Winter: lift timber, empty sandbags.",
            "Parts": "F-001..F-006, H-001, H-007",
        },
        {
            "ID": "D-005",
            "Decision": "Rev C gate_h derived to clear cap by 0.50″",
            "Reason": "Rev B model overlapped cap by 0.50″ (z0=1.0, h=63.0 → top 64.0 vs cap 63.5)",
            "Parts": "G-001..009",
        },
        {
            "ID": "D-006",
            "Decision": "Foot tenon 2.50×4.50×3.50 into F-003 (not 12″ concrete socket)",
            "Reason": "Cross-tie is 5.50″ tall; leave ~2″ below mortise. Overturning resisted by ladder width + ballast, not buried couple.",
            "Parts": "L-001..004, F-003",
        },
        {
            "ID": "D-007",
            "Decision": "Privacy boards FLOATING in grooves",
            "Reason": "seasonal movement; rain-screen; zero fasteners; winter pull-out",
            "Parts": "B-001..003",
        },
        {
            "ID": "D-008",
            "Decision": "Latch B default (mortise in L-001). No epoxy into house concrete.",
            "Reason": "Owner: no cement. Latch A oak strike is opt-in only if a wall exists and they accept fasteners into existing structure — still no pour.",
            "Parts": "G-010, H-002, L-001",
        },
        {
            "ID": "D-009",
            "Decision": "Removable sandbags in timber boxes for wind ballast",
            "Reason": "Freestanding fence in Buffalo wind needs mass × lever. Bags leave in winter. Not a stone pad, not poured.",
            "Parts": "F-005, H-007",
        },
    ]


def fmea():
    return [
        {"MODE": "Wind overturning", "CAUSE": "lake-effect gusts on 64 sf face", "EFFECT": "ladder tips", "SEV": 8, "LKL": 5, "DET": 6, "MIT": "36″ sill spread + F-006 braces + H-007 sandbags (planning FS 1.5); widen base_spread_cl if needed"},
        {"MODE": "Slide on pavement", "CAUSE": "ice / low friction", "EFFECT": "walks off station", "SEV": 5, "LKL": 4, "DET": 7, "MIT": "rubber pads H-001; ballast weight; optional non-marking chocks — still no fasteners into driveway"},
        {"MODE": "Unlevel drop-off", "CAUSE": "5″ estimate", "EFFECT": "racked joints", "SEV": 6, "LKL": 5, "DET": 8, "MIT": "TBM QC-02; F-004 shimmable packing; no pour to lock in a wrong number"},
        {"MODE": "Trapped water on sill", "CAUSE": "sill on grade", "EFFECT": "sill rot", "SEV": 6, "LKL": 5, "DET": 6, "MIT": "pads lift F-001 ½″; paint; annual lift; cedar upgrade optional"},
        {"MODE": "Gate/cap collision", "CAUSE": "Rev B height stack", "EFFECT": "won't close / crushed cap", "SEV": 5, "LKL": 1, "DET": 9, "MIT": "derived gate_h; QC-14"},
        {"MODE": "Glued kusabi", "CAUSE": "habit", "EFFECT": "cannot winter-strip", "SEV": 6, "LKL": 3, "DET": 8, "MIT": "QC-10; labels NEVER GLUE"},
        {"MODE": "Plow berm hit", "CAUSE": "winter leave-in-place", "EFFECT": "broken rails", "SEV": 7, "LKL": 7, "DET": 9, "MIT": "designed knock-down: bags → braces → posts → ladder"},
        {"MODE": "Insufficient ballast", "CAUSE": "bags not placed", "EFFECT": "tip in storm", "SEV": 8, "LKL": 4, "DET": 8, "MIT": "QC-15; label required count on F-005"},
    ]


def tools():
    return {
        "ASSUMED_SHOP": "homeowner / circular saw / chisels / router / drill — not a full millwork shop",
        "REQUIRED": [
            "circular or miter saw",
            "rip capacity (table / track / circular + guide)",
            "chisels ¼–1″ + mallet",
            "marking gauge / knife / combination square",
            "router + ⅜″ and ⅞″ straight bits (dados)",
            "brace of clamps",
            "⅜″ brad-point bits (drawbore)",
            "level + string line",
            "tape 1/16″; square",
        ],
        "OPTIONAL": ["mortiser", "table saw", "drill press", "stainless pintles", "PE review"],
        "DO_NOT_ASSUME": ["CNC", "hollow-chisel mortiser", "post-hole digger", "concrete mixer", "frost auger"],
    }


def sequence():
    return [
        {"phase": "STOCK", "id": "AS-01", "title": "Procure nested lumber + sandbags + rubber pads", "deps": [], "parts": "buy_counts"},
        {"phase": "SITE", "id": "AS-02", "title": "TBM opening + drop-off. Do not dig. Do not pour.", "deps": [], "parts": ""},
        {"phase": "BASE", "id": "AS-03", "title": "Mill F-001..F-003 ladder; half-lap; dry-fit on grade; F-004 pack garden side", "deps": ["AS-01", "AS-02"], "parts": "F-*"},
        {"phase": "MILL", "id": "AS-04", "title": "Posts L-001..004 to S-014; 3.50″ tenons; mortises", "deps": ["AS-01"], "parts": "L-*"},
        {"phase": "MILL", "id": "AS-05", "title": "Rails R-001..003 grooves; boards B-* stop cuts", "deps": ["AS-01"], "parts": "R-*,B-*"},
        {"phase": "MILL", "id": "AS-06", "title": "Gate G-* hozo dry fit; brace; pintles", "deps": ["AS-01"], "parts": "G-*"},
        {"phase": "JOINERY", "id": "AS-07", "title": "Kusabi W-001; pegs W-002; cap scarf C-001", "deps": ["AS-04", "AS-05"], "parts": "W-*,C-001"},
        {"phase": "DRY", "id": "AS-08", "title": "Dry-assemble A-020 on horses; QA QC-08", "deps": ["AS-07"], "parts": "A-020"},
        {"phase": "DRY", "id": "AS-09", "title": "Hang gate on L-002; latch travel", "deps": ["AS-06", "AS-04"], "parts": "A-030"},
        {"phase": "FINISH", "id": "AS-10", "title": "Disassemble paint; mask locking faces", "deps": ["AS-08", "AS-09"], "parts": "H-005"},
        {"phase": "SET", "id": "AS-11", "title": "Set ladder on pads; drop posts in F-003; rails; wedges; boards; cap; gate; fill F-005 with H-007", "deps": ["AS-03", "AS-10"], "parts": "A-000"},
        {"phase": "QA", "id": "AS-12", "title": "QC-08..14; winter rehearsal", "deps": ["AS-11"], "parts": ""},
    ]


def drawing_index():
    return [
        {"DWG": "G-000", "TITLE": "Cover / drawing index / revision", "FILE": "G-000_cover.svg"},
        {"DWG": "GA-100", "TITLE": "General arrangement — elevation + notes", "FILE": "GA-100_arrangement.svg"},
        {"DWG": "GA-110", "TITLE": "Front elevation — datums + overall", "FILE": "GA-110_elevation.svg"},
        {"DWG": "GA-130", "TITLE": "Plan at ladder base / post centers", "FILE": "GA-130_plan.svg"},
        {"DWG": "EX-200", "TITLE": "Exploded assembly — insertion directions", "FILE": "EX-200_exploded.svg"},
        {"DWG": "P-301", "TITLE": "Post typical L-001..004", "FILE": "P-301_post.svg"},
        {"DWG": "P-302", "TITLE": "Nuki rail R-001..003", "FILE": "P-302_rail.svg"},
        {"DWG": "P-303", "TITLE": "Privacy boards B-001..003", "FILE": "P-303_boards.svg"},
        {"DWG": "P-304", "TITLE": "Gate leaf G-001..010", "FILE": "P-304_gate.svg"},
        {"DWG": "J-401", "TITLE": "Nuki + kusabi", "FILE": "J-401_nuki.svg"},
        {"DWG": "J-402", "TITLE": "Foot tenon / cross-tie shoe", "FILE": "J-402_tenon.svg"},
        {"DWG": "J-403", "TITLE": "Kama-tsugi cap scarf", "FILE": "J-403_kama.svg"},
        {"DWG": "J-404", "TITLE": "Gate hozo drawbore", "FILE": "J-404_hozo.svg"},
        {"DWG": "T-501", "TITLE": "Kusabi full-size template", "FILE": "T-501_kusabi.svg"},
        {"DWG": "T-502", "TITLE": "Foot tenon full-size template", "FILE": "T-502_tenon.svg"},
        {"DWG": "S-601", "TITLE": "Master BOM", "FILE": "S-601_bom.svg"},
        {"DWG": "S-602", "TITLE": "Rough cut list", "FILE": "S-602_rough.csv"},
        {"DWG": "S-603", "TITLE": "Finished cut list", "FILE": "S-603_finished.csv"},
        {"DWG": "S-604", "TITLE": "Hardware schedule", "FILE": "S-604_hardware.csv"},
        {"DWG": "S-605", "TITLE": "Board nesting / yield", "FILE": "S-605_nest.csv"},
        {"DWG": "QA-701", "TITLE": "Inspection plan", "FILE": "QA-701_inspection.svg"},
        {"DWG": "L-801", "TITLE": "Part labels", "FILE": "L-801_labels.svg"},
    ]


def unresolved():
    return [
        {"ID": "U-01", "ITEM": "Driveway→garden drop", "CLASS": "TBM", "PARAM": "drop_off", "DEFAULT": 5.0, "IMPACT": "F-004 packing height only — no pour"},
        {"ID": "U-02", "ITEM": "Latch: default B (mortise in L-001). House wall strike is opt-in, no epoxy.", "CLASS": "ASSUMED", "PARAM": "latch mode", "DEFAULT": "B", "IMPACT": "H-002 optional"},
        {"ID": "U-03", "ITEM": "Owner gray exact color", "CLASS": "TBM", "PARAM": "finish hex", "DEFAULT": "#6e7578", "IMPACT": "H-005 only"},
        {"ID": "U-04", "ITEM": "Buffalo Green Code district height / front-yard", "CLASS": "TBM", "PARAM": "overall_height 65″ designed under 6′", "DEFAULT": "verify", "IMPACT": "permit"},
        {"ID": "U-05", "ITEM": "Swing direction (garden vs driveway)", "CLASS": "ASSUMED", "PARAM": "gate swing +Y garden", "DEFAULT": "garden", "IMPACT": "pintle side remains L-002"},
        {"ID": "U-06", "ITEM": "Species upgrade (cedar / locust)", "CLASS": "OPTIONAL", "PARAM": "SPECIES", "DEFAULT": "paint-grade SPF", "IMPACT": "durability / cost, not geometry"},
        {"ID": "U-07", "ITEM": "Licensed PE stamp", "CLASS": "NOT THIS PACKAGE", "PARAM": "n/a", "DEFAULT": "planning design", "IMPACT": "if city requires"},
    ]


def revisions():
    return [
        {"REV": "A", "DATE": "2026-07-18", "NOTE": "Initial geometry + marketing plans M-1…M-6; material-group CAD solids"},
        {"REV": "B", "DATE": "2026-07-18", "NOTE": "Build app + Netlify; same geometry. Gate/cap overlap latent."},
        {"REV": "C", "DATE": "2026-08-13", "NOTE": "Fabrication kernel: semantic parts, joints, BOM, cut lists, nesting, QA; gate_h derived to clear cap; post blank 75.50″ (was documented 77″)."},
        {"REV": "D", "DATE": "2026-08-14", "NOTE": "Sit-on-grade freestanding ladder: timber sills + cross-ties + packing + sandbag ballast. Removed poured pad, piers, gravel, sleeves. Post tenon 3.50″. No digging, no cement."},
    ]


def audit():
    return {
        "MODE": "B — Rev D sit-on-grade (no digging / no cement)",
        "MODEL_ARCHITECTURE": "GOOD — kernel SSOT; FreeCAD App::Part hierarchy; OpenSCAD modules",
        "PARAMETERIZATION_QUALITY": "GOOD — envelope, stock, joinery, kerf, waste, base spread as named parameters",
        "PART_SEPARATION": "GOOD — persistent PART_IDs L/R/B/C/G/W/F/H",
        "METADATA_QUALITY": "GOOD — Fabrication properties on FreeCAD; JSON/CSV registry",
        "ASSEMBLY_STRUCTURE": "GOOD — A000 / A001 ladder base / A010 / A020 / A030",
        "JOINERY_STRUCTURE": "GOOD — joint register with fit class",
        "DRAWING_READINESS": "GOOD — G/GA/EX/P/J/T/S/QA generated from kernel",
        "BOM_READINESS": "GOOD — BOM + nest from parts; ballast count from wind calc",
        "CUT_LIST_READINESS": "GOOD — rough, finished, nest CSV",
        "EXPORT_READINESS": "GOOD — FCStd/STEP/STL/JSON/CSV/SVG/DXF",
        "MAJOR_RISKS": [
            "drop_off ESTIMATED (TBM U-01) — packing only",
            "gate_clear ASSUMED 36″",
            "wind ballast is a planning calc (not PE) — place H-007",
            "Photos still missing: drop-off, gray swatch",
        ],
        "CLOSED_REV_C": [
            "Poured pad / piers / gravel / sleeves removed per owner: no digging, no cement, no stone pads",
        ],
        "REFACTORING": "Kernel is source of truth. FreeCAD/OpenSCAD/drawings/BOM consume it.",
    }


def parameters_flat():
    out = {}
    for k, meta in P.items():
        out[k] = {"value_in": meta["v"], "mm": rnd(inch_mm(meta["v"]), 3), "src": meta["src"], "note": meta.get("note", "")}
    ly = layout()
    for k, val in ly.items():
        if k in ("posts", "courses", "equations", "rail_cls"):
            continue
        if isinstance(val, (int, float)):
            out[k] = {"value_in": val, "mm": rnd(inch_mm(val), 3), "src": "DERIVED", "note": ly["equations"].get(k, "")}
    return out


def build_project() -> dict:
    ly = layout()
    pts = parts(ly)
    jts = joints(ly)
    nest = nest_lumber(pts)
    bal = ballast(ly)
    for p in pts:
        if p["PART_ID"] == "H-007":
            p["QUANTITY"] = bal["n_bags"]
    hw = hardware()
    for h in hw:
        if h["HARDWARE_ID"] == "H-007":
            h["QTY"] = bal["n_bags"]
    return {
        "project": PROJECT,
        "audit": audit(),
        "parameters": parameters_flat(),
        "layout": ly,
        "parts": pts,
        "joints": jts,
        "hardware": hw,
        "assemblies": assemblies(),
        "operations": operations(),
        "stops": stops(),
        "inspection": inspection(),
        "qa_geometry": qa_geometry(ly, pts),
        "nest": nest,
        "ballast": bal,
        "concrete": bal,
        "decisions": decisions(),
        "fmea": fmea(),
        "tools": tools(),
        "sequence": sequence(),
        "drawing_index": drawing_index(),
        "unresolved": unresolved(),
        "revisions": revisions(),
        "tolerance_classes": {
            "T0": "reference / binary",
            "T1": "general woodworking ±1/32 to ±1/8 as noted",
            "T2": "precision joinery ±1/32, mortise/tenon/drawbore",
            "T3": "jig/fixture (templates T-501/T-502)",
            "T4": "not used (mechanical)",
        },
    }


if __name__ == "__main__":
    import json

    proj = build_project()
    ly = proj["layout"]
    print("MARTIN kernel", PROJECT["REVISION"])
    print(" bay_clear", ly["bay_clear"])
    print(" nuki_len", ly["nuki_len"])
    print(" post_blank_l", ly["post_blank_l"])
    print(" gate_h", ly["gate_h"])
    print(" sill_len", ly["sill_len"], "tie_len", ly["tie_len"], "base_width", ly["base_width"])
    print(" parts", len(proj["parts"]), "joints", len(proj["joints"]))
    print(" buy", proj["nest"]["buy_counts"], "net_bf", proj["nest"]["net_bf"], "proc_bf", proj["nest"]["procurement_bf"])
    print(" ballast bags", proj["ballast"]["n_bags"], "req_lb", proj["ballast"]["required_lb"])
    print(" QA", proj["qa_geometry"])
