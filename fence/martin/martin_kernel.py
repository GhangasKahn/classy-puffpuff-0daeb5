"""
MARTIN fabrication kernel — single source of dimensional truth.

Native unit: inch. Convert to millimetres only at CAD / export interfaces.
FreeCAD, OpenSCAD, drawings, BOM, cut lists, and the Build app all derive
from build_project(). Do not duplicate controlling dimensions elsewhere.

Rev F — Darwin Martin Tree of Life light-screen: cantilevered eave, projecting
belt courses, brick-pier texture, art-glass muntins in wood. Not a ranch fence.
Gate against the house. No post holes, no cement, no stone pads.
"""

from __future__ import annotations

import math
from copy import deepcopy

MM = 25.4
PHI = (1.0 + 5.0 ** 0.5) / 2.0  # 1.618… — used where it does not thin structure

# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------
PROJECT = {
    "PROJECT_ID": "MARTIN",
    "PROJECT_NAME": "Prairie removable fence — Buffalo NY",
    "REVISION": "F",
    "UNITS": "inch",
    "DESIGN_STANDARD": "Prairie / Darwin Martin House Tree of Life + Japanese joinery; Buffalo Green Code verify",
    "MATERIAL_SYSTEM": "dimensional lumber + live planters (optional drainage stone in boxes only)",
    "TOLERANCE_CLASS": "T1 general woodworking; T2 nuki / hozo / drawbore / muntin cassettes",
    "AUTHOR": "MARTIN fabrication model",
    "MODEL_VERSION": "6.0.0",
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
    "cap_t": {"v": 1.5, "src": "DERIVED", "note": "2×12 flat — Wright eave (thin and wide, not a lid)"},
    "cap_w": {"v": 11.25, "src": "DERIVED", "note": "2×12 actual — cantilevers past 5.5″ pier ~2.9″ each side"},
    "board_t": {"v": 0.75, "src": "DERIVED", "note": "1× muntin / cassette thickness, recessed behind nuki face"},
    "board_w": {"v": 9.25, "src": "DERIVED", "note": "2×10 actual — projecting Prairie belt course"},
    "board_gap": {"v": 0.75, "src": "ASSUMED", "note": "shadow reveal between belts and cassettes"},
    "band_minor_h": {"v": 8.085, "src": "DERIVED", "note": "upper/lower light cassette; φ pair with middle 13.08"},
    "kick_h": {"v": 11.25, "src": "DERIVED", "note": "2×12 PT water table — solid earth line; dog crawl stop"},
    "muntin_t": {"v": 0.75, "src": "DERIVED", "note": "1×2 face — Wright came, in wood"},
    "pattern_gap": {"v": 1.50, "src": "ASSUMED", "note": "max aperture in Tree of Life; kick is the crawl seal"},
    "fascia_h": {"v": 3.5, "src": "DERIVED", "note": "1×4 hanging fascia under eave — shadow line"},
    "stile_w": {"v": 3.5, "src": "DERIVED", "note": "2×4 / ripped 2×6 face"},
    "leaf_t": {"v": 1.5, "src": "DERIVED", "note": "2× stock gate thickness"},
    "rail_gate_h": {"v": 5.5, "src": "DERIVED", "note": "2×6 gate rail"},
    "brace_w": {"v": 3.5, "src": "DERIVED"},

    # joinery
    "post_tenon_x": {"v": 2.5, "src": "ASSUMED", "note": "shoulder 0.5″ each side of 3.5"},
    "post_tenon_y": {"v": 4.5, "src": "ASSUMED", "note": "shoulder 0.5″ each side of 5.5"},
    "post_tenon_h": {"v": 3.5, "src": "ASSUMED", "note": "into 5.5″ cross-tie; leave ~2″ below mortise"},
    "rail_reveal": {"v": 3.00, "src": "ASSUMED", "note": "belt courses cantilever past piers like Wright planes"},
    "cap_overhang": {"v": 3.50, "src": "ASSUMED", "note": "eave past outer pier faces along the run"},
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
    "gate_clear": {"v": 36.0, "src": "ASSUMED", "note": "clear walk-through; gate against house (P0)"},
    "gate_gap": {"v": 0.50, "src": "ASSUMED", "note": "each side of leaf"},
    "gate_bottom_clear": {"v": 0.375, "src": "ASSUMED", "note": "dog seal — swing clearance above threshold"},
    "gate_top_clear": {"v": 0.50, "src": "ASSUMED", "note": "under cap"},
    "latch_bar_l": {"v": 18.0, "src": "ASSUMED"},
    "latch_bar_t": {"v": 1.50, "src": "DERIVED", "note": "2× stock"},
    "latch_bar_w": {"v": 3.50, "src": "DERIVED", "note": "2×4 actual"},
    "house_receiver_depth": {"v": 4.0, "src": "ASSUMED", "note": "Latch A opt-in only — default is Latch B"},
    "pivot_d": {"v": 1.25, "src": "ASSUMED", "note": "oak pivot pin — structurally better than pintles on a freestanding P1"},
    "pivot_l": {"v": 4.0, "src": "ASSUMED"},
    "slat_housing_d": {"v": 0.75, "src": "ASSUMED", "note": "housed dado in post; do NOT through-mortise all 7 bands (0.75″ web would fail)"},

    # sit-on-grade ladder base (NO digging, NO cement, NO stone pads)
    "sill_overhang": {"v": 6.0, "src": "ASSUMED", "note": "dodai past outer post faces"},
    "sill_t": {"v": 3.5, "src": "DERIVED", "note": "4×6 actual thickness (across Y)"},
    "sill_h": {"v": 5.5, "src": "DERIVED", "note": "4×6 on edge — Prairie base beam"},
    "base_spread_cl": {"v": 36.0, "src": "ASSUMED", "note": "driveway-sill CL to garden-sill CL; wind lever"},
    "tie_reveal": {"v": 1.0, "src": "ASSUMED", "note": "cross-tie past outer sill faces"},
    "drop_off": {"v": 0.0, "src": "VERIFIED", "note": "run sits on driveway slab (photos). Packing only if outriggers leave the slab"},
    "pack_w": {"v": 5.5, "src": "DERIVED", "note": "packing crib if drop_off > 0"},
    "pack_len": {"v": 12.0, "src": "ASSUMED", "note": "crib length along sill at each tie"},
    "planter_x": {"v": 44.0, "src": "DERIVED", "note": "one trough per privacy bay, garden side — NOT at house/gate"},
    "planter_y": {"v": 18.0, "src": "ASSUMED", "note": "depth into yard; sized for wind mass, not φ (shrinking height would under-ballast)"},
    "planter_h": {"v": 18.0, "src": "ASSUMED", "note": "deep Prairie trough — live plants + watering; φ not applied (would cut soil volume)"},
    "planter_stone_h": {"v": 4.0, "src": "ASSUMED", "note": "drainage / ballast stone IN the box only — not a pad"},
    "planter_soil_pcf": {"v": 90.0, "src": "ASSUMED", "note": "wet potting mix planning density"},
    "planter_stone_pcf": {"v": 100.0, "src": "ASSUMED", "note": "pea gravel in box"},
    "n_planters": {"v": 2.0, "src": "ASSUMED", "note": "bays P1–P2 and P2–P3 only; zero at P0/house"},
    "wind_psf": {"v": 15.0, "src": "ASSUMED", "note": "planning pressure, not PE; Buffalo ~90 mph simplified"},
    "wind_fs": {"v": 1.5, "src": "ASSUMED", "note": "planning factor of safety on overturning"},
    "furniture_pad_t": {"v": 0.5, "src": "ASSUMED", "note": "wood or rubber pads under driveway sill — protect pavement"},
    "brace_z": {"v": 18.0, "src": "ASSUMED", "note": "sujikai meets post above sill top"},
    "light_dado_w": {"v": 0.50, "src": "ASSUMED", "note": "cap soffit channel for 12V IP65 tape"},
    "light_dado_d": {"v": 0.375, "src": "ASSUMED"},
    "block_l": {"v": 7.0, "src": "ASSUMED", "note": "tectonic 2×2 block — Darwin Martin pier texture"},
    "block_s": {"v": 1.5, "src": "DERIVED", "note": "2×2 actual"},

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


def motif_tree_of_life(x0, z0, w, h, t=None):
    """Darwin Martin Tree of Life — three stylized trees in a cassette.
    z0 is the BOTTOM of the panel. Returns JSON-safe rects + lines in inches.
    """
    t = float(t if t is not None else v("muntin_t"))
    rects, lines = [], []
    n = 3
    cw = w / n
    h_root = h * 0.22
    h_fol = h * 0.38
    h_trunk = h - h_root - h_fol
    for i in range(n):
        left = x0 + i * cw
        cx = left + cw / 2.0
        # pot / root square (Wright gold squares at the base)
        ps = min(cw * 0.42, h_root * 0.82)
        rects.append({"x": rnd(cx - ps / 2), "z": rnd(z0 + (h_root - ps) / 2), "w": rnd(ps), "h": rnd(ps), "role": "pot"})
        # satellite squares
        ss = t * 1.6
        for sx, sz in (
            (left + t, z0 + t),
            (left + cw - t - ss, z0 + t),
            (cx - ss / 2, z0 + h_root - ss - t * 0.2),
        ):
            rects.append({"x": rnd(sx), "z": rnd(sz), "w": rnd(ss), "h": rnd(ss), "role": "root-sq"})
        # three trunks
        span = cw * 0.22
        for dx in (-span, 0.0, span):
            rects.append({
                "x": rnd(cx + dx - t / 2), "z": rnd(z0 + h_root),
                "w": rnd(t), "h": rnd(h_trunk), "role": "trunk",
            })
        # chevron branches — V pointing UP, three rows (foliage)
        z_fol = z0 + h_root + h_trunk
        n_rows = 3
        rh = h_fol / n_rows
        for r in range(n_rows):
            z_meet = z_fol + (r + 0.82) * rh
            z_tip = z_fol + (r + 0.12) * rh
            half = cw * (0.36 - r * 0.05)
            lines.append({"x1": rnd(cx - half), "z1": rnd(z_tip), "x2": rnd(cx), "z2": rnd(z_meet), "t": t, "role": "branch"})
            lines.append({"x1": rnd(cx + half), "z1": rnd(z_tip), "x2": rnd(cx), "z2": rnd(z_meet), "t": t, "role": "branch"})
            ls = t * 1.8
            for lx in (cx - half, cx + half):
                rects.append({"x": rnd(lx - ls / 2), "z": rnd(z_tip - ls / 2), "w": rnd(ls), "h": rnd(ls), "role": "leaf"})
        # cassette frame
        for fr in (
            (x0 if i == 0 else left, z0, t if i == 0 else t * 0.6, h),
            (left + cw - (t if i == n - 1 else t * 0.6), z0, t if i == n - 1 else t * 0.6, h),
        ):
            rects.append({"x": rnd(fr[0]), "z": rnd(fr[1]), "w": rnd(fr[2]), "h": rnd(fr[3]), "role": "frame"})
    rects.append({"x": rnd(x0), "z": rnd(z0), "w": rnd(w), "h": rnd(t), "role": "frame"})
    rects.append({"x": rnd(x0), "z": rnd(z0 + h - t), "w": rnd(w), "h": rnd(t), "role": "frame"})
    return {"kind": "tree-of-life", "x0": rnd(x0), "z0": rnd(z0), "w": rnd(w), "h": rnd(h), "rects": rects, "lines": lines}


def motif_nested_rects(x0, z0, w, h, t=None):
    """Wright nested squares / ribbon-window grid — upper and lower lights."""
    t = float(t if t is not None else v("muntin_t"))
    rects, lines = [], []
    # outer + inner frames
    for inset, role in ((0.0, "frame"), (t + 1.5, "inner"), (2 * t + 3.0, "jewel")):
        if w - 2 * inset < 3 or h - 2 * inset < 2:
            continue
        x, z, ww, hh = x0 + inset, z0 + inset, w - 2 * inset, h - 2 * inset
        rects.append({"x": rnd(x), "z": rnd(z), "w": rnd(ww), "h": rnd(t), "role": role})
        rects.append({"x": rnd(x), "z": rnd(z + hh - t), "w": rnd(ww), "h": rnd(t), "role": role})
        rects.append({"x": rnd(x), "z": rnd(z), "w": rnd(t), "h": rnd(hh), "role": role})
        rects.append({"x": rnd(x + ww - t), "z": rnd(z), "w": rnd(t), "h": rnd(hh), "role": role})
    # φ verticals
    for f in (1 / (PHI + 1), PHI / (PHI + 1)):
        vx = x0 + w * f - t / 2
        rects.append({"x": rnd(vx), "z": rnd(z0), "w": rnd(t), "h": rnd(h), "role": "mullion"})
    # corner jewels
    js = t * 2.2
    for jx, jz in (
        (x0 + t + 1.6, z0 + t + 1.6),
        (x0 + w - t - 1.6 - js, z0 + t + 1.6),
        (x0 + t + 1.6, z0 + h - t - 1.6 - js),
        (x0 + w - t - 1.6 - js, z0 + h - t - 1.6 - js),
    ):
        rects.append({"x": rnd(jx), "z": rnd(jz), "w": rnd(js), "h": rnd(js), "role": "leaf"})
    return {"kind": "nested-rects", "x0": rnd(x0), "z0": rnd(z0), "w": rnd(w), "h": rnd(h), "rects": rects, "lines": lines}


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

    # Elevation — Wright ribbon window, not a ranch fence.
    # Water table + 2 projecting belts + 3 light cassettes (φ: 8.085 / 13.080 / 8.085) + eave.
    # 11.25 + 2*9.25 + 1.50 + 6*0.75 + 29.25 = 65.000  (5 inter-layer gaps + 1 under eave)
    gap = v("board_gap")
    kick_h = v("kick_h")
    belt = v("board_w")
    L1 = (H - kick_h - cap_t - 2 * belt - 6 * gap) / (2.0 + PHI)
    L2 = L1 * PHI
    z = 0.0
    slats = []
    layers = [
        ("K-001", "WATER", "2x12 PT", kick_h, True, "water table / dog seal / earth line"),
        ("Q-001", "L1", "cassette", rnd(L1), False, "nested-rects light (roots)"),
        ("R-001", "BELT1", "2x10", belt, True, "projecting Prairie belt"),
        ("Q-002", "L2", "cassette", rnd(L2), False, "Tree of Life light (three trees)"),
        ("R-002", "BELT2", "2x10", belt, True, "projecting Prairie belt / latch CL"),
        ("Q-003", "L3", "cassette", rnd(L1), False, "nested-rects light (foliage)"),
    ]
    for i, (pid, mark, stock, h, is_nuki, role) in enumerate(layers):
        slats.append({
            "id": pid, "mark": mark, "stock": stock, "h": h,
            "z0": rnd(z), "z1": rnd(z + h), "cl": rnd(z + h / 2.0),
            "nuki": is_nuki, "role": role,
        })
        z = z + h
        if i < len(layers) - 1:
            z = z + gap
    z = z + gap  # shadow reveal under the eave
    slat_top = rnd(z)
    rail_cls = tuple(s["cl"] for s in slats if s["nuki"] and s["id"].startswith("R-"))
    latch_cl = next(s["cl"] for s in slats if s["id"] == "R-002")

    # Light-screen motifs — one per privacy bay per cassette, plus the gate leaf
    lights = [s for s in slats if s["id"].startswith("Q-")]
    motifs = []
    for bay_i, (la, rb) in enumerate(((1, 2), (2, 3))):
        x0 = posts[la]["cx"] + fx / 2.0
        ww = bay_clear
        for s in lights:
            kind = "tree-of-life" if s["id"] == "Q-002" else "nested-rects"
            fn = motif_tree_of_life if kind == "tree-of-life" else motif_nested_rects
            m = fn(x0, s["z0"], ww, s["h"])
            m["bay"] = bay_i
            m["part"] = s["id"]
            motifs.append(m)
    # gate — Tree of Life as the hero next to the house
    gx0 = fx + v("gate_gap") + v("stile_w")
    gw = (gate - 2.0 * v("gate_gap")) - 2.0 * v("stile_w")
    for s in lights:
        kind = "tree-of-life" if s["id"] == "Q-002" else "nested-rects"
        fn = motif_tree_of_life if kind == "tree-of-life" else motif_nested_rects
        # gate lights align in z with screen lights
        m = fn(gx0, s["z0"], gw, s["h"])
        m["bay"] = "gate"
        m["part"] = s["id"]
        motifs.append(m)

    courses = [{"id": s["id"], "z0": s["z0"], "z1": s["z1"], "h": s["h"]} for s in slats]
    n_bay = 2
    used = bay_clear
    board_inset = 0.0

    gate_leaf_w = gate - 2.0 * v("gate_gap")
    gate_h = H - cap_t - v("gate_bottom_clear") - v("gate_top_clear")
    gate_inner = gate_leaf_w - 2.0 * v("stile_w")
    n_gate_b = 3

    sill_len = L + 2.0 * v("sill_overhang")
    spread = v("base_spread_cl")
    sill_t = v("sill_t")
    tie_len = spread + sill_t + 2.0 * v("tie_reveal")
    base_width = spread + sill_t  # outer sill face to outer sill face
    garden_sill_cy = spread / 2.0
    drive_sill_cy = -spread / 2.0
    brace_len = math.hypot(spread / 2.0, v("brace_z"))
    pack_layers = 0 if v("drop_off") <= 0 else max(1, int(math.ceil(v("drop_off") / 1.5)))
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
        "slats": slats,
        "lights": lights,
        "motifs": motifs,
        "slat_top": slat_top,
        "latch_cl": latch_cl,
        "phi": rnd(PHI, 5),
        "band_ratio": rnd(L2 / L1, 3),
        "light_minor": rnd(L1),
        "light_major": rnd(L2),
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
        joinery = "foot tenon into F-003; through-nuki K-001 + R-001 + R-002; cassette dados for Q-001/002/003"
        if p["mark"] == "P0":
            joinery += "; latch-bar mortise (Latch B); no kusabi (gate side); NO planter"
        elif p["mark"] == "P1":
            joinery += "; kusabi slots on nuki; oak pivot sockets top+bottom"
        elif p["mark"] == "P2":
            joinery += "; kusabi slots; cap scarf bearing"
        else:
            joinery += "; kusabi slots; slats withdraw toward P3"
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

    rails = []
    for s in ly["slats"]:
        if not s["id"].startswith("R-"):
            continue
        is10 = s["stock"] == "2x10"
        rails.append(
            _part(
                PART_ID=s["id"],
                PART_NAME=f'{s["mark"]} {s["role"]}',
                PART_CATEGORY="R",
                ASSEMBLY="A-020 PRIVACY_FRAME",
                QUANTITY=1,
                MATERIAL="solid lumber",
                SPECIES="SPF/SYP paint-grade",
                PURCHASE="2×10 × 10′" if is10 else "2×6 × 10′",
                ROUGH_THICKNESS=1.5,
                ROUGH_WIDTH=s["h"],
                ROUGH_LENGTH=rnd(ly["nuki_len"] + 1.0),
                FINISHED_THICKNESS=1.5,
                FINISHED_WIDTH=s["h"],
                FINISHED_LENGTH=ly["nuki_len"],
                BOARD_FEET=bf_nominal(2, 10 if is10 else 6, 10),
                JOINERY=("nuki through L-002/003/004; kusabi" if s["nuki"]
                         else f'housed {v("slat_housing_d")}" dado in posts; lock batten / friction'),
                PROCESS="OP010–OP080 slat routing",
                TOLERANCE_CLASS="T2",
                FIT="SLIDING in mortise/dado",
                MOVEMENT="FLOATING along length; locked by kusabi at nuki posts",
                cl=s["cl"],
                nuki=s["nuki"],
            )
        )
    kick = _part(
        PART_ID="K-001",
        PART_NAME="Water table nuki (earth line / dog seal)",
        PART_CATEGORY="R",
        ASSEMBLY="A-020 PRIVACY_FRAME",
        QUANTITY=1,
        MATERIAL="PT UC4A 2×12 (paint after dry)",
        SPECIES="southern yellow pine",
        PURCHASE="2×12 PT × 10′",
        ROUGH_THICKNESS=1.5,
        ROUGH_WIDTH=11.25,
        ROUGH_LENGTH=rnd(ly["nuki_len"] + 1.0),
        FINISHED_THICKNESS=1.5,
        FINISHED_WIDTH=11.25,
        FINISHED_LENGTH=ly["nuki_len"],
        BOARD_FEET=bf_nominal(2, 12, 10),
        JOINERY="nuki through L-002/003/004; projects 3″ past piers",
        NOTES="Wright earth line. Solid. Dog cannot crawl. PT because splash. Cassette Q-001 sits in the top edge groove.",
        TOLERANCE_CLASS="T2",
        cl=ly["slats"][0]["cl"],
    )
    cassettes = []
    for s in ly["slats"]:
        if not s["id"].startswith("Q-"):
            continue
        cassettes.append(
            _part(
                PART_ID=s["id"],
                PART_NAME=f'{s["mark"]} {s["role"]}',
                PART_CATEGORY="Q",
                ASSEMBLY="A-020 PRIVACY_FRAME",
                QUANTITY=2,
                MATERIAL="1×2 / 1×3 ripped muntins in a 1× frame",
                SPECIES="SPF/SYP paint-grade",
                PURCHASE="1×4 × 8′ (rip to ¾″ muntins)",
                ROUGH_THICKNESS=0.75,
                ROUGH_WIDTH=3.5,
                ROUGH_LENGTH=rnd(ly["bay_clear"] + 1.0),
                FINISHED_THICKNESS=0.75,
                FINISHED_WIDTH=s["h"],
                FINISHED_LENGTH=ly["bay_clear"],
                BOARD_FEET=0,
                JOINERY="framed cassette; drops into nuki grooves; winter pull toward P3",
                NOTES="Recessed behind belt courses. Tree of Life (Q-002) or nested squares (Q-001/003). Max aperture 1.50″.",
                TOLERANCE_CLASS="T2",
                MOVEMENT="FLOATING cassette",
                cl=s["cl"],
            )
        )

    cap = _part(
        PART_ID="C-001",
        PART_NAME="Prairie eave (kama-tsugi pair)",
        PART_CATEGORY="C",
        ASSEMBLY="A-020 PRIVACY_FRAME",
        QUANTITY=1,
        MATERIAL="solid lumber",
        SPECIES="SPF/SYP paint-grade",
        PURCHASE="2×12 × 12′",
        ROUGH_THICKNESS=1.5,
        ROUGH_WIDTH=11.25,
        ROUGH_LENGTH=rnd(ly["cap_len"] + 1.0),
        FINISHED_THICKNESS=1.5,
        FINISHED_WIDTH=11.25,
        FINISHED_LENGTH=ly["cap_len"],
        BOARD_FEET=bf_nominal(2, 12, 12),
        JOINERY="kama-tsugi scarf at L-003 centerline, drawbored; soffit dado for H-006 tape light",
        NOTES="Wright eave — thin and wide. Cantilevers past the 4×6 piers. Light channel on yard soffit. 1×4 fascia C-003 hangs on the garden edge.",
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
        PURCHASE="from C-001 offcut / 2×12",
        ROUGH_THICKNESS=1.5,
        ROUGH_WIDTH=11.25,
        ROUGH_LENGTH=rnd(ly["cap_stub_len"] + 0.5),
        FINISHED_THICKNESS=1.5,
        FINISHED_WIDTH=11.25,
        FINISHED_LENGTH=ly["cap_stub_len"],
        BOARD_FEET=0,
        JOINERY="hozo to L-001 top",
        NOTES="Does not bridge gate",
    )
    fascia = _part(
        PART_ID="C-003",
        PART_NAME="Eave fascia (garden shadow)",
        PART_CATEGORY="C",
        ASSEMBLY="A-020 PRIVACY_FRAME",
        QUANTITY=1,
        MATERIAL="solid lumber",
        SPECIES="SPF/SYP",
        PURCHASE="1×4 × 12′",
        ROUGH_THICKNESS=0.75,
        ROUGH_WIDTH=3.5,
        ROUGH_LENGTH=rnd(ly["cap_len"] + 1.0),
        FINISHED_THICKNESS=0.75,
        FINISHED_WIDTH=v("fascia_h"),
        FINISHED_LENGTH=ly["cap_len"],
        BOARD_FEET=bf_nominal(1, 4, 12),
        JOINERY="housed under C-001 garden edge; oak pegs",
        NOTES="The shadow line that makes the cap read as a Wright eave, not a 2× lid.",
    )

    boards = [
        _part(
            PART_ID="T-001",
            PART_NAME="Tectonic block (Darwin Martin pier texture)",
            PART_CATEGORY="B",
            ASSEMBLY="A-020 PRIVACY_FRAME",
            QUANTITY=36,
            MATERIAL="solid lumber",
            SPECIES="SPF 2×2",
            PURCHASE="2×2 × 8′ / ripped 2×4",
            ROUGH_THICKNESS=v("block_s"),
            ROUGH_WIDTH=v("block_s"),
            ROUGH_LENGTH=rnd(v("block_l") + 0.5),
            FINISHED_THICKNESS=v("block_s"),
            FINISHED_WIDTH=v("block_s"),
            FINISHED_LENGTH=v("block_l"),
            BOARD_FEET=0,
            JOINERY="¼″ retention pegs — ½″ will split the 2×2",
            NOTES="Roman-brick wrapping on P1/P2/P3 — stacked 2×2 with ⅜″ raked shadow joints. Darwin Martin pier texture. Ornament + shadow, not structure.",
            TOLERANCE_CLASS="T1",
        ),
    ]

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
            JOINERY="hozo mortises for gate bands; oak pivot gudgeons top+bottom (not pintles)",
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
            PART_NAME="Gate rail aligned to BELT1",
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
            PART_NAME="Gate rail aligned to BELT2 (latch)",
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
            PART_NAME="Gate top belt rail",
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
            JOINERY="half-lap into G-003 and G-007 (compression, hinge-bottom to latch-top)",
            FIT="GLUE optional on laps; still mechanically captured",
            NOTES="Shop-side compression only — sits on the driveway face. Not the garden elevation. Do not let this read as a ranch Z-brace.",
        ),
        _part(
            PART_ID="G-009",
            PART_NAME="Gate Tree of Life / nested-rect cassettes",
            PART_CATEGORY="Q",
            ASSEMBLY="A-030 GATE",
            QUANTITY=ly["n_gate_boards"],
            MATERIAL="1×2 / 1×3 ripped muntins in a 1× frame",
            SPECIES="SPF/SYP paint-grade",
            PURCHASE="1×4 × 8′ (rip to ¾″ muntins)",
            ROUGH_THICKNESS=0.75,
            ROUGH_WIDTH=3.5,
            ROUGH_LENGTH=rnd(ly["gate_inner"] + 0.5),
            FINISHED_THICKNESS=0.75,
            FINISHED_WIDTH=ly["light_major"],
            FINISHED_LENGTH=ly["gate_inner"],
            JOINERY="framed cassettes; groove in gate stiles — FLOATING",
            MOVEMENT="FLOATING",
            NOTES="Garden face is Darwin Martin Tree of Life (middle light) + nested squares. Matches Q-001/002/003. Max aperture 1.50″.",
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
        QUANTITY=12,  # 3 nuki × 3 posts + extras
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
        NOTES="9 nuki (K-001 + R-001 + R-002 × P1/P2/P3) + 3 spare. Label bag for winter. NEVER glue.",
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
        PART_NAME="Oak gate pivot pin",
        PART_CATEGORY="W",
        ASSEMBLY="A-030 GATE",
        QUANTITY=2,
        MAKE_OR_BUY="MAKE",
        MATERIAL="white oak",
        PURCHASE="oak 5/4 or 1-1/4″ dowel",
        ROUGH_THICKNESS=v("pivot_d"),
        ROUGH_WIDTH=v("pivot_d"),
        ROUGH_LENGTH=rnd(v("pivot_l") + 0.5),
        FINISHED_THICKNESS=v("pivot_d"),
        FINISHED_WIDTH=v("pivot_d"),
        FINISHED_LENGTH=v("pivot_l"),
        JOINERY="waxed pin: bottom socket in threshold/sill at P1; top in cap soffit",
        FIT="LOCATIONAL / lift-off +Z",
        NOTES="Structurally best on a freestanding hinge post: leaf weight goes into the sill, not a cantilever pintle. P0 (house) has no planter.",
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
            QUANTITY=0 if ly["pack_layers"] == 0 else 4,
            MATERIAL="solid lumber",
            SPECIES="SPF/SYP 2×6 stacked",
            PURCHASE="2×6 × 8′",
            ROUGH_THICKNESS=1.5,
            ROUGH_WIDTH=v("pack_w"),
            ROUGH_LENGTH=v("pack_len"),
            FINISHED_THICKNESS=max(ly["pack_h"], 1.5),
            FINISHED_WIDTH=v("pack_w"),
            FINISHED_LENGTH=v("pack_len"),
            BOARD_FEET=0,
            JOINERY="dry-stacked layers; no glue; shims to TBM drop_off",
            NOTES="Qty 0 while the run sits on the driveway slab (photos). Use only if outriggers leave the slab.",
            MOVEMENT="SLOTTED / shimmable",
        ),
        _part(
            PART_ID="F-005",
            PART_NAME="Live planter trough (garden side)",
            PART_CATEGORY="F",
            ASSEMBLY="A-001 BASE",
            QUANTITY=int(v("n_planters")),
            MATERIAL="PT UC4A 2×6 / 2×8 (paint after dry)",
            SPECIES="southern yellow pine",
            PURCHASE="2×6 × 8′",
            ROUGH_THICKNESS=1.5,
            ROUGH_WIDTH=5.5,
            ROUGH_LENGTH=rnd(v("planter_x") + 4.0),
            FINISHED_THICKNESS=v("planter_h"),
            FINISHED_WIDTH=v("planter_y"),
            FINISHED_LENGTH=v("planter_x"),
            BOARD_FEET=0,
            JOINERY="dovetail corners; drainage slots in bottom slats; ½″ air gap from posts",
            NOTES="P1–P2 and P2–P3 only. NOT at the house/gate. Live plants + watering. Optional stone in the bottom 4″ for drainage and mass — inside the box, not a pad. Winter: empty or lift with the ladder.",
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
            NOTES="Ease arrises 1/16″; end-grain sealer; PT dry then prime; 2 finish coats owner gray; extra coat on planter interiors; mask joinery faces and oak pivot sockets",
            ROUGH_THICKNESS=0,
            ROUGH_WIDTH=0,
            ROUGH_LENGTH=0,
            FINISHED_THICKNESS=0,
            FINISHED_WIDTH=0,
            FINISHED_LENGTH=0,
        ),
        _part(
            PART_ID="H-006",
            PART_NAME="12V IP65 LED tape + driver (cap soffit)",
            PART_CATEGORY="H",
            ASSEMBLY="A-040 FINISH",
            QUANTITY=1,
            MAKE_OR_BUY="BUY",
            MATERIAL="low-voltage LED",
            PURCHASE="outdoor tape 16′ + 60W driver + wood cover slat",
            NOTES="Sits in C-001 soffit dado. Driver in a dry niche of the P3 planter — not at the house. Allowed metal: lighting only.",
            ROUGH_THICKNESS=0,
            ROUGH_WIDTH=0,
            ROUGH_LENGTH=0,
            FINISHED_THICKNESS=0,
            FINISHED_WIDTH=0,
            FINISHED_LENGTH=0,
        ),
        _part(
            PART_ID="H-007",
            PART_NAME="Planter drainage stone (in-box only)",
            PART_CATEGORY="H",
            ASSEMBLY="A-001 BASE",
            QUANTITY=1,
            MAKE_OR_BUY="BUY",
            MATERIAL="pea gravel / lava rock",
            PURCHASE="bags to fill 4″ in two troughs",
            NOTES="INSIDE F-005 only — drainage + mass. Not a pad, not on the driveway, not poured. Live soil goes on top. Winter empty or store.",
            GRAIN_DIRECTION="n/a",
            ROUGH_THICKNESS=0,
            ROUGH_WIDTH=0,
            ROUGH_LENGTH=0,
            FINISHED_THICKNESS=0,
            FINISHED_WIDTH=0,
            FINISHED_LENGTH=0,
        ),
    ]

    allp = posts + rails + [kick, cap, cap_stub, fascia] + cassettes + boards + gate_parts + [wedges, pegs, pintle] + civil
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
    for s in ly["slats"]:
        if not s["nuki"]:
            continue
        for post in ("L-002", "L-003", "L-004"):
            J(
                JOINT_ID=f"J-{n:03d}",
                JOINT_TYPE="nuki 貫 + kusabi" if s["id"].startswith("R-") else "kick nuki 貫",
                PART_A=post,
                PART_B=s["id"],
                LOCATION=f"{post} × {s['id']} @ z_cl={s['cl']}\"",
                MORTISE_WIDTH=v("rail_t") + v("nuki_fit"),
                MORTISE_HEIGHT=s["h"],
                MORTISE_DEPTH="THROUGH (post_x)",
                TENON_WIDTH=v("rail_t"),
                TENON_HEIGHT=s["h"],
                TENON_LENGTH="THROUGH + rail_reveal",
                FIT_CLASS="SLIDING then INTERFERENCE via W-001",
                ASSEMBLY_DIRECTION="+X (withdraw toward P3 for winter)",
            )
            n += 1
    for s in ly["slats"]:
        if s["nuki"]:
            continue
        J(
            JOINT_ID=f"J-{n:03d}",
            JOINT_TYPE="cassette groove / housed dado",
            PART_A="L-002/003/004 + nuki edges",
            PART_B=s["id"],
            LOCATION=f"{s['id']} @ z_cl={s['cl']}\"",
            MORTISE_WIDTH=v("board_t") + v("nuki_fit"),
            MORTISE_HEIGHT=s["h"],
            MORTISE_DEPTH=v("groove_d"),
            FIT_CLASS="SLIDING",
            NOTES="Q cassettes drop into grooves in the nuki edges and shallow dados in the posts. Recessed behind belt courses. Winter withdraw toward P3.",
            ASSEMBLY_DIRECTION="+X from P3",
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
        PART_A="R-001 / R-002 / C-001",
        PART_B="T-001 / G-009",
        LOCATION="pier wrapping (T-001) / gate cassette grooves (G-009)",
        MORTISE_DEPTH=v("groove_d"),
        MORTISE_WIDTH=v("groove_w"),
        FIT_CLASS="CLEARANCE",
        MOVEMENT="FLOATING",
        GLUE="NO",
    )
    n += 1
    J(
        JOINT_ID=f"J-{n:03d}",
        JOINT_TYPE="oak pivot / socket",
        PART_A="L-002 / F-003 / C-001",
        PART_B="G-001 / W-003",
        LOCATION="bottom in sill at P1; top in cap soffit — lift-off +Z",
        FIT_CLASS="LOCATIONAL",
        ASSEMBLY_DIRECTION="+Z to remove",
        NOTES="Leaf weight in compression to the driveway sill. No planter at P0/house.",
    )
    n += 1
    J(
        JOINT_ID=f"J-{n:03d}",
        JOINT_TYPE="sliding latch",
        PART_A="G-010",
        PART_B="H-002 or L-001",
        LOCATION=f"z_cl={ly['latch_cl']}\" (R-002 belt / latch CL)",
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
            "DESCRIPTION": "Exterior primer + owner gray enamel, 2 finish coats (ease, seal, PT dry first)",
            "STANDARD": "exterior grade",
            "SIZE": "kit",
            "QTY": 1,
            "MATERIAL": "coating",
            "MAKE_OR_BUY": "BUY",
        },
        {
            "HARDWARE_ID": "H-006",
            "DESCRIPTION": "12V IP65 LED tape + driver in cap soffit dado",
            "STANDARD": "low-voltage outdoor",
            "SIZE": "16′ tape + 60W driver",
            "QTY": 1,
            "MATERIAL": "LED + wood cover slat",
            "MAKE_OR_BUY": "BUY",
        },
        {
            "HARDWARE_ID": "H-007",
            "DESCRIPTION": "Pea gravel / lava in F-005 troughs — 4″ drainage layer, in-box only",
            "STANDARD": "landscape stone",
            "SIZE": "see ballast.stone_cuft",
            "QTY": "2 troughs",
            "MATERIAL": "stone",
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
        "A-001 BASE": ["F-001", "F-002", "F-003×4", "F-005×2 planters (not at house)", "F-006×4", "H-001", "H-007 stone in-box"],
        "A-010 POSTS": ["L-001", "L-002", "L-003", "L-004", "C-002"],
        "A-020 PRIVACY_FRAME": [
            "K-001 water table 2×12 PT",
            "Q-001 nested-rects cassette ×2",
            "R-001 belt nuki 2×10",
            "Q-002 Tree of Life cassette ×2",
            "R-002 belt nuki 2×10 (latch CL)",
            "Q-003 nested-rects cassette ×2",
            "C-001 2×12 eave + C-003 fascia",
            "T-001×36 Roman-brick pier wrap",
            "W-001 kusabi",
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
        "A-040 FINISH": ["H-005", "H-006 lighting"],
    }


def operations():
    """Typical routing — posts shown fully; others summarized by family."""
    ly = layout()
    nuki_cls = ", ".join(f'{s["cl"]:.2f}' for s in ly["slats"] if s["nuki"])
    post_ops = [
        ("OP010", "Rough crosscut", "track / miter / table saw", "blank +1″", "T1 ±1/8″"),
        ("OP020", "Joint reference face", "hand plane / factory S4S", "FACE A", "T1"),
        ("OP030", "Joint reference edge", "same", "EDGE B", "T1"),
        ("OP040", "Verify section 3.50×5.50", "caliper / combo square", "S4S skip if in-tol", "T1 ±1/32″"),
        ("OP050", "Final length post_blank_l", "stop S-014", "DATUM END A = tenon tip; overall", "T1 ±1/32″"),
        ("OP060", "Shoulder foot tenon 2.50×4.50×3.50", "Bridge City kerf/tenon + Zenwu chisels", "measure from sill-shoulder datum", "T2 ±1/32″"),
        ("OP070", f"Through-nuki at CL {nuki_cls} AFF (K-001 + R-001 + R-002 only)", "chisel / Japanese saw", "from DATUM END = shoulder (sill top)", "T2"),
        ("OP075", "Cassette dados + nuki-edge grooves for Q-001/002/003", "router + chisel", "do NOT through-mortise cassettes — keep post web", "T2"),
        ("OP080", "Kusabi slots (L-002/003/004)", "saw + chisel", "see J-401", "T2"),
        ("OP090", "Oak pivot sockets (L-002 / F-003 / C-001)", "brace + chisel", "bottom in sill, top in cap soffit", "T2"),
        ("OP100", "Ease 1/16″; seal end grain; dry-fit in F-003", "block plane + brush", "tenon faces unpainted contact", "—"),
    ]
    return {
        "L-001": [o for o in post_ops if "Kusabi" not in o[1] and "Oak pivot" not in o[1]]
        + [("OP085", "Latch-B mortise", "chisel", f'CL {ly["latch_cl"]:.2f}" AFF (R-002 belt)', "T2")],
        "L-002": post_ops,
        "L-003": [o for o in post_ops if "Oak pivot" not in o[1]],
        "L-004": [o for o in post_ops if "Oak pivot" not in o[1]],
        "R-00x": [
            ("OP010", "Crosscut finished length nuki_len", "stop S-021", "DATUM END = P1 reveal", "T1"),
            ("OP020", "Ease arrises 1/16″; do not paint locking faces yet", "block plane", "", "—"),
            ("OP030", "Mark nuki stations at post CLs", "square", "from DATUM END", "T2"),
        ],
        "G-00x": [
            ("OP010", "Mill stiles/rails to finished section", "table / track saw", "", "T1"),
            ("OP020", "Cut hozo; dry fit", "Bridge City tenon + Zenwu chisels", "tenon ⅓ stock", "T2"),
            ("OP030", "Drawbore ⅛″ toward shoulder", "⅜″ brad point", "offset toward shoulder", "T2"),
            ("OP040", "Half-lap brace", "saw", "", "T2"),
            ("OP050", "Peg, trim, hang on oak pivots W-003", "mallet", "lift-off +Z check", "T2"),
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
            "PARTS": ["K-001", "R-001", "R-002"],
            "NOTE": "Through-nuki share nuki_len. Cassettes Q-* are bay_clear, not nuki_len.",
        },
        {
            "SETUP": "S-030",
            "TOOL": "Track saw + Bridge City kerf/tenon + Zenwu chisels",
            "STOP": "nuki mortise 1.50″ × 9.25″ (belts) or 11.25″ (2×12 water table)",
            "PARTS": ["L-002..004"],
            "NOTE": "Through-mortise ONLY K-001, R-001, R-002. Cassettes groove into nuki edges.",
        },
        {
            "SETUP": "S-040",
            "TOOL": "Mortise gauge from FACE A",
            "STOP": f'latch CL {ly["latch_cl"]:.3f}" AFF (R-002 belt)',
            "PARTS": ["L-001", "G-002", "G-010"],
            "NOTE": "Latch B into P0. Gate against the house. No planter at P0.",
        },
    ]


def inspection():
    ly = layout()
    return [
        {"QC": "QC-01", "CHECK": "Confirm overall opening 143.000″ ± 0.25″ on site", "CLASS": "VERIFIED/TBM", "TOL": "T1"},
        {"QC": "QC-02", "CHECK": "Run sits on driveway slab; pack only if outriggers leave slab (drop_off default 0)", "CLASS": "VERIFIED", "TOL": "T1"},
        {"QC": "QC-03", "CHECK": "Stock moisture — PT for kick + planters dry before prime; SPF acclimate", "CLASS": "T0", "TOL": "—"},
        {"QC": "QC-04", "CHECK": f'Four posts finished length {ly["post_blank_l"]:.3f}" within ±1/32"', "CLASS": "T2", "TOL": "±0.031"},
        {"QC": "QC-05", "CHECK": "K-001 + R-001 + R-002 identical nuki_len; cassettes = bay_clear", "CLASS": "T2", "TOL": "±0.031"},
        {"QC": "QC-06", "CHECK": "Through-nuki only K-001/R-001/R-002; Q cassettes in grooves; 1.50″ max aperture", "CLASS": "T2", "TOL": "binary"},
        {"QC": "QC-07", "CHECK": "Foot tenon 2.500×4.500×3.500 enters F-003; lifts out for winter", "CLASS": "T2", "TOL": "+0.03/−0"},
        {"QC": "QC-08", "CHECK": "Dry-assemble: plumb / no racking; Tree of Life + nested-rect cassettes seat; 1.50″ gauge must not pass pattern", "CLASS": "T1", "TOL": "plumb 1/8″ in 65″"},
        {"QC": "QC-09", "CHECK": "Gate against house; oak pivots lift-off; latch into P0; no planter at P0", "CLASS": "T2", "TOL": "—"},
        {"QC": "QC-10", "CHECK": "No glue on kusabi or nuki locking faces", "CLASS": "T0", "TOL": "binary"},
        {"QC": "QC-11", "CHECK": "Paint: ease arrises, end-grain sealer, PT dry then prime, 2 finish coats; mask joinery", "CLASS": "T0", "TOL": "—"},
        {"QC": "QC-12", "CHECK": "Winter knock-down rehearsal before first storm season", "CLASS": "T0", "TOL": "—"},
        {"QC": "QC-13", "CHECK": "Ladder sills sit on driveway; two planters garden-side of privacy bays only", "CLASS": "T1", "TOL": "±0.125"},
        {"QC": "QC-14", "CHECK": "Gate vs cap clearance ≥ 0.50″; gate bottom ≤ 0.375″ (dog)", "CLASS": "T2", "TOL": "min 0.38 cap / max 0.50 bottom"},
        {"QC": "QC-15", "CHECK": "Planters planted + optional in-box stone; air gap from posts; drainage slots", "CLASS": "T1", "TOL": "—"},
        {"QC": "QC-16", "CHECK": "No concrete, no post holes, no gravel/stone PAD; stone only inside planters", "CLASS": "T0", "TOL": "binary"},
        {"QC": "QC-17", "CHECK": "Cap soffit light dado + IP65 tape; driver not at house wall", "CLASS": "T1", "TOL": "—"},
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
    # elevation stack: slat_top + cap = overall_height
    stack = rnd(ly["slat_top"] + v("cap_t"))
    if abs(stack - v("overall_height")) > 0.01:
        issues.append({"level": "CRITICAL", "item": "elevation stack", "detail": f"slat_top+cap={stack} vs H={v('overall_height')}"})
    else:
        issues.append({"level": "OK", "item": "elevation stack", "detail": f'{ly["slat_top"]}" slats + {v("cap_t")}" cap = {stack}"'})
    if abs(ly["band_ratio"] - PHI) > 0.15:
        issues.append({"level": "NOTE", "item": "band ratio vs φ", "detail": ly["band_ratio"]})
    else:
        issues.append({"level": "OK", "item": "Prairie cassette ratio ≈ φ", "detail": f'{ly["band_ratio"]} (L2/L1 lights; belts stay full 2×10)'})
    # duplicate part ids
    ids = [p["PART_ID"] for p in parts_list]
    if len(ids) != len(set(ids)):
        issues.append({"level": "CRITICAL", "item": "duplicate PART_ID"})
    else:
        issues.append({"level": "OK", "item": "unique PART_IDs", "detail": str(len(ids))})
    bal = ballast(ly)
    if bal["provided_lb"] + 1e-6 < bal["required_lb"]:
        issues.append({"level": "WEAK", "item": "planter ballast short of planning FS", "detail": f'{bal["provided_lb"]} lb < {bal["required_lb"]} lb'})
    else:
        issues.append({"level": "OK", "item": "planter ballast vs wind (planning)", "detail": f'{bal["provided_lb"]} lb / {bal["required_lb"]} lb  ratio {bal["ratio"]}'})
    return issues


def nest_lumber(parts_list):
    """Greedy first-fit decreasing onto 8′ / 10′ / 12′ purchase lengths."""
    kerf = v("saw_kerf")
    families = {
        "4x6x8": {"nom": (4, 6), "len": 96.0, "parts": []},
        "4x6x16": {"nom": (4, 6), "len": 192.0, "parts": []},
        "2x10x10": {"nom": (2, 10), "len": 120.0, "parts": []},
        "2x12x10": {"nom": (2, 12), "len": 120.0, "parts": []},
        "2x12x12": {"nom": (2, 12), "len": 144.0, "parts": []},
        "1x4x8": {"nom": (1, 4), "len": 96.0, "parts": []},
        "1x4x12": {"nom": (1, 4), "len": 144.0, "parts": []},
        "2x6x10": {"nom": (2, 6), "len": 120.0, "parts": []},
        "2x6x8": {"nom": (2, 6), "len": 96.0, "parts": []},
        "2x2x8": {"nom": (2, 2), "len": 96.0, "parts": []},
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
        "R-001": "2x10x10",
        "R-002": "2x10x10",
        "K-001": "2x12x10",
        "C-001": "2x12x12",
        "C-002": "2x12x12",
        "C-003": "1x4x12",
        "Q-001": "1x4x8",
        "Q-002": "1x4x8",
        "Q-003": "1x4x8",
        "G-001": "2x6x8",
        "G-002": "2x6x8",
        "G-003": "2x6x8",
        "G-004": "2x6x8",
        "G-005": "2x6x8",
        "G-006": "2x6x8",
        "G-007": "2x6x8",
        "G-008": "2x6x8",
        "G-009": "1x4x8",
        "F-004": "2x6x8",
        "F-005": "2x6x8",
        "F-006": "2x6x8",
        "T-001": "2x2x8",
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
    """Planning overturning check — not a PE stamp. Live planters, not bags."""
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
    n = int(v("n_planters"))
    vx = v("planter_x") * v("planter_y") * (v("planter_h") - v("planter_stone_h")) / 1728.0
    vs = v("planter_x") * v("planter_y") * v("planter_stone_h") / 1728.0
    soil_lb = rnd(n * vx * v("planter_soil_pcf"), 1)
    stone_lb = rnd(n * vs * v("planter_stone_pcf"), 1)
    provided = rnd(soil_lb + stone_lb, 1)
    return {
        "wind_area_sf": area_sf,
        "planning_pressure_psf": q,
        "wind_force_lb": F,
        "overturning_ftlb": M,
        "base_spread_in": v("base_spread_cl"),
        "fs": fs,
        "required_lb": req,
        "n_planters": n,
        "soil_cuft": rnd(n * vx, 2),
        "stone_cuft": rnd(n * vs, 2),
        "soil_lb": soil_lb,
        "stone_lb": stone_lb,
        "provided_lb": provided,
        "ratio": rnd(provided / req, 2) if req else 0,
        "n_bags": 0,
        "bag_lb": 0,
        "concrete_yd3": 0.0,
        "gravel_yd3": 0.0,
        "note": "NO pour, NO post holes, NO stone pad. Mass is wet soil + in-box drainage stone in two garden-side troughs (not at the house). Planning calc only — not PE certified.",
    }


def concrete_vol(ly=None):
    """Deprecated alias — Rev D has no concrete. Returns ballast() for old callers."""
    return ballast(ly)


def decisions():
    return [
        {
            "ID": "D-001",
            "Decision": "4×6 posts not 4×4",
            "Reason": "nuki cheeks + housed-slat web; owner asked to overbuild",
            "Parts": "L-001..004",
        },
        {
            "ID": "D-002",
            "Decision": "Darwin Martin Tree of Life light-screen: 2×12 water table + two projecting 2×10 belts + three recessed muntin cassettes (φ 8.085 / 13.080 / 8.085).",
            "Reason": "Stacked 2×10/2×6 boards read as a Home Depot ranch fence. Wright at a distance is eave + belts + piers + patterned lights. φ sizes the cassette pair, not ripped 2×10.",
            "Parts": "K-001, Q-001/002/003, R-001/002, C-001, C-003",
        },
        {
            "ID": "D-003",
            "Decision": "No nails/screws in timber. Allowed metal: lighting + optional latch hardware.",
            "Reason": "owner + winter knock-down + fastener corrosion in Buffalo",
            "Parts": "all MAKE lumber",
        },
        {
            "ID": "D-004",
            "Decision": "Sit-on-grade timber ladder on the driveway slab. No packing unless outriggers leave the slab.",
            "Reason": "Photos: run crosses the driveway. No post holes, no cement, no stone pads.",
            "Parts": "F-001..F-006, H-001",
        },
        {
            "ID": "D-005",
            "Decision": "Gate flush to the house (P0). No planter at the gate.",
            "Reason": "Owner: planter next to gate is unwanted. Latch B into P0. Driver lives in P3 planter.",
            "Parts": "G-001..010, L-001, F-005",
        },
        {
            "ID": "D-006",
            "Decision": "Foot tenon 2.50×4.50×3.50 into F-003",
            "Reason": "Cross-tie is 5.50″ tall; leave ~2″ below mortise. Overturning resisted by ladder + live planters.",
            "Parts": "L-001..004, F-003",
        },
        {
            "ID": "D-007",
            "Decision": "Through-nuki only K-001 + R-001 + R-002. Cassettes groove into nuki edges; three mortises keep the post web.",
            "Reason": "Seven through-mortises would shred the 4×6. Belts + water table are the structure. Lights are withdrawable cassettes.",
            "Parts": "R-001, R-002, K-001, Q-001/002/003, L-002..004",
        },
        {
            "ID": "D-008",
            "Decision": "Latch B default (mortise in L-001). No epoxy into house.",
            "Reason": "Owner: wood + lighting + a gate latch. Latch A oak strike is opt-in only.",
            "Parts": "G-010, H-002, L-001",
        },
        {
            "ID": "D-009",
            "Decision": "Live planters (P1–P2 and P2–P3) as wind ballast. Stone inside boxes only.",
            "Reason": "Owner: planters are planters with watering. Mass = wet soil + optional drainage stone. Not bags, not a pad.",
            "Parts": "F-005, H-007",
        },
        {
            "ID": "D-010",
            "Decision": "1.25″ oak pivots (W-003): bottom in sill at P1, top in cap soffit.",
            "Reason": "Structurally best on a freestanding hinge post: leaf weight in compression to the driveway sill, not a cantilever pintle off P0 (no planter at house).",
            "Parts": "W-003, G-001, L-002, F-003, C-001",
        },
        {
            "ID": "D-011",
            "Decision": "Solid 2×12 PT water table + 1.50″ max pattern apertures + 0.375″ gate bottom clear.",
            "Reason": "100% dog containment. Kick is the crawl stop. Pattern is a Wright light-screen, not a radiator of ¾″ gaps.",
            "Parts": "K-001, Q-001/002/003, G-009",
        },
        {
            "ID": "D-012",
            "Decision": "Buffalo painted finish: ease 1/16″, end-grain sealer, PT dry then prime, 2 coats, extra on planter interiors.",
            "Reason": "Four-season Erie County. Mask joinery faces. Paint is the weather system.",
            "Parts": "H-005",
        },
    ]


def fmea():
    return [
        {"MODE": "Wind overturning", "CAUSE": "lake-effect gusts on ~64 sf face", "EFFECT": "ladder tips", "SEV": 8, "LKL": 5, "DET": 6, "MIT": "36″ sill spread + F-006 braces + wet soil/stone in two garden troughs (planning FS 1.5); deepen planters if QC-15 ratio < 1"},
        {"MODE": "Slide on pavement", "CAUSE": "ice / low friction", "EFFECT": "walks off station", "SEV": 5, "LKL": 4, "DET": 7, "MIT": "rubber pads H-001; planter weight; optional non-marking chocks — still no fasteners into driveway"},
        {"MODE": "Dog crawl", "CAUSE": "gap under gate or kick, or pattern aperture > 1.50″", "EFFECT": "containment fail", "SEV": 7, "LKL": 3, "DET": 8, "MIT": "K-001 2×12 nuki at z=0; 1.50″ max muntin gap; gate bottom 0.375″"},
        {"MODE": "Post web failure", "CAUSE": "through-mortising every layer", "EFFECT": "split post", "SEV": 8, "LKL": 2, "DET": 9, "MIT": "through-nuki only water table + two belts; cassettes groove in"},
        {"MODE": "Planter rot / wet posts", "CAUSE": "live watering against timber", "EFFECT": "post / box decay", "SEV": 6, "LKL": 5, "DET": 6, "MIT": "PT boxes; ½″ air gap; drainage slots; extra interior paint; kick is PT"},
        {"MODE": "Gate/cap collision", "CAUSE": "height stack", "EFFECT": "won't close / crushed cap", "SEV": 5, "LKL": 1, "DET": 9, "MIT": "derived gate_h; QC-14"},
        {"MODE": "Glued kusabi", "CAUSE": "habit", "EFFECT": "cannot winter-strip", "SEV": 6, "LKL": 3, "DET": 8, "MIT": "QC-10; labels NEVER GLUE"},
        {"MODE": "Plow berm hit", "CAUSE": "winter leave-in-place", "EFFECT": "broken rails", "SEV": 7, "LKL": 7, "DET": 9, "MIT": "designed knock-down: empty planters → braces → posts → ladder"},
        {"MODE": "Insufficient ballast", "CAUSE": "empty planters in a storm", "EFFECT": "tip", "SEV": 8, "LKL": 4, "DET": 8, "MIT": "QC-15; plant + optional in-box stone before wind season"},
        {"MODE": "Hinge cantilever", "CAUSE": "pintles on unbraced P0", "EFFECT": "post rack / latch bind", "SEV": 7, "LKL": 3, "DET": 8, "MIT": "oak pivots: leaf weight into sill at P1, not off P0"},
    ]


def tools():
    return {
        "ASSUMED_SHOP": "owner millwork: track saw, miter, table saw, hand planes, Japanese saws, Bridge City kerf/tenon, Zenwu pairing chisels, layout tools",
        "REQUIRED": [
            "track saw",
            "miter saw",
            "table saw",
            "hand planes",
            "Japanese saws",
            "Bridge City kerf and tenon makers",
            "Zenwu pairing chisels",
            "layout tools (gauge, knife, square)",
            "⅜″ brad-point bits (drawbore)",
            "level + string line",
            "tape 1/16″",
        ],
        "OPTIONAL": ["mortiser", "router + ¾″ straight bit (housed dados)", "drill press", "stainless pintle upgrade", "PE review"],
        "DO_NOT_ASSUME": ["CNC", "post-hole digger", "concrete mixer", "frost auger", "patio-stone pad"],
    }


def sequence():
    return [
        {"phase": "STOCK", "id": "AS-01", "title": "Procure nested lumber + PT for kick/planters + oak + rubber pads + IP65 tape", "deps": [], "parts": "buy_counts"},
        {"phase": "SITE", "id": "AS-02", "title": "TBM 143″ opening on the driveway. Gate at the house. Do not dig. Do not pour.", "deps": [], "parts": ""},
        {"phase": "BASE", "id": "AS-03", "title": "Mill F-001..F-003 ladder; half-lap; dry-fit on slab pads; build two F-005 troughs (not at house)", "deps": ["AS-01", "AS-02"], "parts": "F-*"},
        {"phase": "MILL", "id": "AS-04", "title": "Posts L-001..004 to S-014; 3.50″ tenons; through-nuki + housed dados", "deps": ["AS-01"], "parts": "L-*"},
        {"phase": "MILL", "id": "AS-05", "title": "Water table K-001 + belts R-001/002; mill Tree of Life + nested-rect cassettes Q-*", "deps": ["AS-01"], "parts": "R-*,K-001,Q-*,T-001"},
        {"phase": "MILL", "id": "AS-06", "title": "Gate G-* hozo dry fit; brace; oak pivot sockets", "deps": ["AS-01"], "parts": "G-*,W-003"},
        {"phase": "JOINERY", "id": "AS-07", "title": "Kusabi W-001; pegs W-002; cap scarf C-001 + light dado", "deps": ["AS-04", "AS-05"], "parts": "W-*,C-001"},
        {"phase": "DRY", "id": "AS-08", "title": "Dry-assemble A-020: belts, cassettes, 1.50″ aperture gauge; QA QC-08", "deps": ["AS-07"], "parts": "A-020"},
        {"phase": "DRY", "id": "AS-09", "title": "Hang gate on oak pivots at P1; latch travel into P0", "deps": ["AS-06", "AS-04"], "parts": "A-030"},
        {"phase": "FINISH", "id": "AS-10", "title": "Ease, seal, PT dry, prime, two gray coats; extra on planter interiors; mask locking faces", "deps": ["AS-08", "AS-09"], "parts": "H-005"},
        {"phase": "SET", "id": "AS-11", "title": "Set ladder on pads; drop posts; bands; wedges; cap light; gate; plant troughs + optional in-box stone", "deps": ["AS-03", "AS-10"], "parts": "A-000"},
        {"phase": "QA", "id": "AS-12", "title": "QC-08..17; winter rehearsal", "deps": ["AS-11"], "parts": ""},
    ]


def drawing_index():
    return [
        {"DWG": "G-000", "TITLE": "Cover / drawing index / revision", "FILE": "G-000_cover.svg"},
        {"DWG": "GA-100", "TITLE": "General arrangement — elevation + notes", "FILE": "GA-100_arrangement.svg"},
        {"DWG": "GA-110", "TITLE": "Front elevation — datums + overall", "FILE": "GA-110_elevation.svg"},
        {"DWG": "GA-130", "TITLE": "Plan at ladder base / post centers", "FILE": "GA-130_plan.svg"},
        {"DWG": "EX-200", "TITLE": "Exploded assembly — insertion directions", "FILE": "EX-200_exploded.svg"},
        {"DWG": "P-301", "TITLE": "Post typical L-001..004", "FILE": "P-301_post.svg"},
        {"DWG": "P-302", "TITLE": "Water table + Prairie belts K-001 / R-001 / R-002", "FILE": "P-302_rail.svg"},
        {"DWG": "P-303", "TITLE": "Tree of Life + nested-rect cassettes Q-001..003", "FILE": "P-303_boards.svg"},
        {"DWG": "P-304", "TITLE": "Gate leaf G-001..010", "FILE": "P-304_gate.svg"},
        {"DWG": "J-401", "TITLE": "Nuki + kusabi / housed dado", "FILE": "J-401_nuki.svg"},
        {"DWG": "J-402", "TITLE": "Foot tenon / cross-tie shoe", "FILE": "J-402_tenon.svg"},
        {"DWG": "J-403", "TITLE": "Kama-tsugi cap scarf", "FILE": "J-403_kama.svg"},
        {"DWG": "J-404", "TITLE": "Gate hozo drawbore + oak pivot", "FILE": "J-404_hozo.svg"},
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
        {"ID": "U-01", "ITEM": "Outrigger packing only if garden sill leaves the slab (default 0 — photos show driveway run)", "CLASS": "VERIFIED/TBM", "PARAM": "drop_off", "DEFAULT": 0.0, "IMPACT": "F-004 qty"},
        {"ID": "U-02", "ITEM": "Latch: default B (mortise in L-001). House wall strike is opt-in, no epoxy.", "CLASS": "ASSUMED", "PARAM": "latch mode", "DEFAULT": "B", "IMPACT": "H-002 optional"},
        {"ID": "U-03", "ITEM": "Owner gray exact color", "CLASS": "TBM", "PARAM": "finish hex", "DEFAULT": "#6e7578", "IMPACT": "H-005 only"},
        {"ID": "U-04", "ITEM": "Buffalo Green Code district height / front-yard", "CLASS": "TBM", "PARAM": "overall_height 65″ designed under 6′", "DEFAULT": "verify", "IMPACT": "permit"},
        {"ID": "U-05", "ITEM": "Swing direction (garden vs driveway)", "CLASS": "ASSUMED", "PARAM": "gate swing +Y garden", "DEFAULT": "garden", "IMPACT": "pivot remains at P1"},
        {"ID": "U-06", "ITEM": "Species upgrade (cedar / locust)", "CLASS": "OPTIONAL", "PARAM": "SPECIES", "DEFAULT": "paint-grade SPF + PT splash", "IMPACT": "durability / cost, not geometry"},
        {"ID": "U-07", "ITEM": "Licensed PE stamp", "CLASS": "NOT THIS PACKAGE", "PARAM": "n/a", "DEFAULT": "planning design", "IMPACT": "if city requires"},
        {"ID": "U-08", "ITEM": "Remeasure 143″ on the driveway (photos confirm span to house siding)", "CLASS": "TBM", "PARAM": "overall_length", "DEFAULT": 143.0, "IMPACT": "all derived X"},
    ]


def revisions():
    return [
        {"REV": "A", "DATE": "2026-07-18", "NOTE": "Initial geometry + marketing plans M-1…M-6; material-group CAD solids"},
        {"REV": "B", "DATE": "2026-07-18", "NOTE": "Build app + Netlify; same geometry. Gate/cap overlap latent."},
        {"REV": "C", "DATE": "2026-08-13", "NOTE": "Fabrication kernel: semantic parts, joints, BOM, cut lists, nesting, QA; gate_h derived to clear cap; post blank 75.50″ (was documented 77″)."},
        {"REV": "D", "DATE": "2026-08-14", "NOTE": "Sit-on-grade freestanding ladder: timber sills + cross-ties + packing + sandbag ballast. Removed poured pad, piers, gravel, sleeves. Post tenon 3.50″. No digging, no cement."},
        {"REV": "E", "DATE": "2026-08-14", "NOTE": "Darwin Martin Prairie screen: φ-adjacent 2×10/2×6 bands, ¾″ dog gaps, PT kick, live planters (not at house), oak pivots, cap soffit lighting. Gate against the house. No sandbags, no patio-stone pad."},
        {"REV": "F", "DATE": "2026-08-14", "NOTE": "Tree of Life light-screen: cantilevered 2×12 eave + fascia, projecting belts, Roman-brick piers, recessed muntin cassettes (nested-rects / three trees / nested-rects), solid 2×12 water table, Tree of Life gate. Not a ranch fence."},
    ]


def audit():
    return {
        "MODE": "B — Rev F Darwin Martin Tree of Life light-screen on sit-on-grade ladder (no digging / no cement)",
        "MODEL_ARCHITECTURE": "GOOD — kernel SSOT; FreeCAD App::Part hierarchy; OpenSCAD modules",
        "PARAMETERIZATION_QUALITY": "GOOD — envelope, stock, joinery, kerf, waste, planter mass as named parameters",
        "PART_SEPARATION": "GOOD — persistent PART_IDs L/R/K/C/G/W/F/H/T/Q",
        "METADATA_QUALITY": "GOOD — Fabrication properties on FreeCAD; JSON/CSV registry",
        "ASSEMBLY_STRUCTURE": "GOOD — A000 / A001 ladder+planters / A010 / A020 / A030",
        "JOINERY_STRUCTURE": "GOOD — joint register with fit class; nuki vs cassette groove rule",
        "DRAWING_READINESS": "GOOD — G/GA/EX/P/J/T/S/QA generated from kernel; elevation paints motifs",
        "BOM_READINESS": "GOOD — BOM + nest from parts; planter mass from wind calc",
        "CUT_LIST_READINESS": "GOOD — rough, finished, nest CSV",
        "EXPORT_READINESS": "GOOD — FCStd/STEP/STL/JSON/CSV/SVG/DXF",
        "MAJOR_RISKS": [
            "overall_length TBM remeasure on driveway",
            "gate_clear ASSUMED 36″",
            "wind ballast is a planning calc (not PE) — plant F-005 + optional in-box stone",
            "Photos confirm driveway span and house-side gate; gray swatch still TBM",
            "Tree of Life is an original wood interpretation — not a licensed reproduction of Wright glass",
        ],
        "CLOSED_REV_F": [
            "Stacked 2×10/2×6 ranch-fence face replaced by Wright light-screen (eave, belts, piers, patterned cassettes)",
            "¾″ radiator gaps replaced by 1.50″ max muntin apertures + solid 2×12 water table",
            "Gate face is Tree of Life, not a Z-brace panel",
            "Cap is a 2×12 cantilevered eave with hanging fascia",
            "No concrete, no post holes, no gravel/stone PAD",
        ],
        "REFACTORING": "Kernel is source of truth. FreeCAD/OpenSCAD/drawings/BOM consume it.",
    }


def parameters_flat():
    out = {}
    for k, meta in P.items():
        out[k] = {"value_in": meta["v"], "mm": rnd(inch_mm(meta["v"]), 3), "src": meta["src"], "note": meta.get("note", "")}
    ly = layout()
    for k, val in ly.items():
        if k in ("posts", "courses", "equations", "rail_cls", "slats", "lights", "motifs"):
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
            p["NOTES"] = f'In-box stone {bal["stone_cuft"]} cu ft / {bal["stone_lb"]} lb. Soil {bal["soil_lb"]} lb. Provided {bal["provided_lb"]} vs required {bal["required_lb"]} lb (planning).'
    hw = hardware()
    for h in hw:
        if h["HARDWARE_ID"] == "H-007":
            h["QTY"] = f'{bal["stone_cuft"]} cu ft'
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
    print(" slat_top", ly["slat_top"], "band_ratio", ly["band_ratio"], "lights", ly["light_minor"], ly["light_major"])
    print(" motifs", len(ly["motifs"]), "nuki_cls", ly["rail_cls"])
    print(" buy", proj["nest"]["buy_counts"], "net_bf", proj["nest"]["net_bf"], "proc_bf", proj["nest"]["procurement_bf"])
    print(" ballast soil+stone", proj["ballast"]["provided_lb"], "req_lb", proj["ballast"]["required_lb"], "ratio", proj["ballast"]["ratio"])
    print(" QA", proj["qa_geometry"])
