#!/usr/bin/env python3
"""WALTER DS-16 — parametric fabrication source of truth.

Lineage:
  ShopNotes No. 86 thickness sander (table-saw drive, conveyor feed)
  → Ron Walters dedicated-motor rebuild (Baltic birch + flange bearings)
  → Rev A: solid sliding table, adjustable idler bearing, precision shaft
  → Rev B: dual-end lift, ways, hold-downs, floating bearing, A/B clock
  → Fab B.1: part IDs, housed stretchers, way rebate (table actually fits),
             joinery/ops/QA registries. Machine geometry (capacity, drum,
             16.5″ inner span) is unchanged.
  → Fab B.2: Wandel-style individual part / assembly / hardware sheets.
  → Fab B.3: WOODWRIGHT PLANFORGE master build guide — design-basis sheets,
             ballooned exploded view, step-by-step assembly (LEGO-style parts
             trays), commissioning checklist, printable guide book.
  → Fab B.4: mechanics. Vertical captured UHMW ways (table is a lifting
             carriage, not a Y-slide in use). Stretchers relocated so they
             never occupy the table envelope. Both ½-10 Acme screws sit on
             the drum centerline so cutting force goes through the nuts.

Units: inches internally. Convert only at export.
Evidence: VERIFIED (spec), DERIVED (equation), ASSUMED (layout), ESTIMATED.

PARAMETER → GEOMETRY → METADATA → DRAWINGS → BOM → CUT LIST → BUILD DOCS
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ds16_mechanics import (  # noqa: E402
    MECH,
    alignment_budget,
    bearing_requirement,
    drum_mass,
    drum_rpm as mech_drum_rpm,
    drum_crown,
    drum_crown_revb,
    drive_options,
    dust_requirement,
    mech_calculations,
    mech_decisions,
    micro_adjust,
    module_masses,
    surface_fpm as mech_surface_fpm,
    thickness_variation_budget,
    unbalance_allowance,
)
from ds16_procurement import procurement, procurement_summary  # noqa: E402

IN_TO_MM = 25.4
PI = 3.14159265

# Rev C requirements pulled from the mechanics register so the hardware schedule
# cannot drift away from the calculation that justifies it.
MECH_C_REQUIRED = bearing_requirement(
    (drum_mass(MECH)["total"] + MECH.force_reference) / 2.0, mech_drum_rpm(MECH), MECH
)["c_required"]
SPEC_HANDWHEEL_DIV = MECH.handwheel_divisions
MECH_ADJ_AT_WORK = micro_adjust(MECH)["per_rev_at_work"]
AXIS_I_SHELL = __import__("ds16_mechanics").AXIS.i_shell
MECH_UNBALANCE_OZIN = unbalance_allowance(mech_drum_rpm(MECH), 1.0)["u_oz_in"]
MECH_CFM = dust_requirement(MECH)["required_cfm"]
MECH_DRUM_MASS = drum_mass(MECH)["total"]

# ---------------------------------------------------------------------------
# 0. Project
# ---------------------------------------------------------------------------

PROJECT = {
    "project_id": "WALTER-DS16",
    "project_name": "WALTER DS-16 dedicated drum thickness sander",
    "revision": "C",
    "fabrication_rev": "C.1",
    "units": "inch",
    "unit_policy": "Internal inches. Millimetres are interface-only.",
    "design_standard": "Shop woodworking T1 / joinery T2 / metrology T4 on ALN-01 / TV-01",
    "material_system": "Baltic birch + 6061 drum shell + UHMW ways + phenolic wear",
    "tolerance_class": "T2 joinery, T4 drum/table metrology",
    "author": "WALTER fabrication model",
    "model_version": "C.1",
    "cad_platform": "Python SSOT + OpenSCAD solids + SVG shop drawings",
    "lineage": "ShopNotes 86 → Ron Walters → Rev A solid table → Rev B geometry → Rev C precision axis",
}

# Release state for the whole package. A powered machine with a 5" drum at
# ~1208 RPM is R3: the geometry and joinery are resolved and internally
# reconciled, but several things are deliberately NOT released here — mains
# electrical work, the flange bolt circle (ASSUMED until transferred), and
# the purchased bearing's actual dynamic capacity C (read off vendor data).
RELEASE_STATE = {
    "state": "FABRICATION REVIEW",
    "risk_class": "R3",
    "risk_triggers": [
        "Powered spindle: 5\u2033 drum at ~1208 RPM with stored rotational energy",
        "Mains-voltage motor, switch, and cord require qualified electrical work",
        "Ingoing nip between drum and feed rollers; workpiece ejection path",
        "Abrasive dust generation, worst when truing the drum OD",
    ],
    "conditions": [
        "Transfer the purchased flange to the panel before drilling. The bolt square on the drawings is ASSUMED.",
        "Measure ply_actual and regenerate. Keep the 16.5\u2033 inner span; do not shrink it to suit 18 mm stock.",
        "Confirm the purchased bearing's basic dynamic capacity C on the vendor page (CALC-C11). Bore alone is not a specification.",
        "Motor circuit, switch, grounding, and cord: qualified electrician and local code. Not released by this package.",
        "Commission with the hood on and no stock, standing clear of the drum ends.",
        "Pass ALN-01 (no-load |A\u2212B|) then TV-01 (witness-board scatter) before the machine is used on real work.",
        "3D-print P-023 at 1:1 before cutting metal.",
        "Collector must deliver the CALC-C15 airflow at the machine; a shop vacuum will not.",
    ],
    "not_released": [
        "Electrical installation and any code-dependent wiring",
        "Any use as a metal-working or thickness-planing machine",
        "Stock shorter than ~12\u2033 without the sled",
        "McMaster-Carr catalogue part numbers (CONFIRM AT ORDER \u2014 see H-02 / H-03)",
    ],
}

# HYBRID layout (Planforge centerline protocol): face/edge datums on the
# plywood panels, centerline for the three working planes (drum axis, Acme
# pair, table midplane). Declared on G-002 / A-01 / M-101. Do not mix a
# face measurement with a centerline measurement without converting.
LAYOUT_PROTOCOL = {
    "mode": "HYBRID",
    "face_edge": (
        "DATUM-A bottom edge, DATUM-B infeed edge, DATUM-C inner face. "
        "Panel size, dado locations, and screw pilots originate here."
    ),
    "centerline": (
        "Drum axis (DATUM-E), both Acme screws, vertical ways, and the table "
        "midplane all share Y = side_depth/2 from DATUM-B. Vertical locations "
        "originate from DATUM-A."
    ),
    "declaration": (
        "Primary layout system: HYBRID. Panel joinery is face/edge. "
        "Drum, lift, and ways are centerline from DATUM-B / DATUM-A."
    ),
}


@dataclass(frozen=True)
class Spec:
    """Controlling inputs. Dependent sizes live in Geom, not here."""

    revision: str = "C"
    fabrication_rev: str = "C.1"

    # Capacity — VERIFIED design intent
    capacity_width: float = 15.5
    min_stock_thickness: float = 0.0625
    max_stock_thickness: float = 3.0
    min_stock_length: float = 12.0
    table_margin_each: float = 0.25  # table wider than work, each side

    # Quality — Rev C SPLITS the single Rev B number into two measurable specs.
    # Rev B quoted 0.003″ for both a no-load alignment check and the delivered
    # thickness variation of a board. Those are different quantities with
    # different error budgets (CALC-C06); no machine can make them equal.
    aln_spec: float = 0.003    # ALN-01 no-load |A−B| alignment, indicator
    tv_spec: float = 0.005     # TV-01 delivered thickness variation, witness board
    parallel_tol: float = 0.003  # retained alias = ALN-01
    table_flat_tol: float = 0.003  # over the 15.5″ contact line, not the diagonal
    drum_tir: float = 0.0015
    paper_on_delta: float = 0.002
    pass_rough: float = 0.008
    pass_medium: float = 0.004
    pass_finish: float = 0.001

    # Drum — VERIFIED
    drum_od: float = 5.0
    disc_thick: float = 0.75
    disc_count_core: int = 19
    disc_count_ends: int = 2
    spacer_every_n: int = 4
    spacer_mm: float = 1.0
    velcro_width: float = 4.0
    sandpaper_width: float = 3.0
    disc_bandsaw_oversize: float = 0.125

    # Shaft — Rev C: ¾″ FAILED the accuracy spec (CALC-C01). See D-041.
    shaft_od: float = 1.25
    shaft_length: float = 24.0
    shaft_spec: str = "Precision-ground rotary shaft, 1¼″, straightness ≤ 0.001″/ft"
    key_wire_od: float = 0.125
    bearing_drive: str = 'Mounted ball bearing, 1¼″ bore, self-aligning — FIXED'
    bearing_idler: str = 'Mounted ball bearing, 1¼″ bore, self-aligning — FLOATING (axial)'
    bearing_count: int = 2
    idler_float_slot: float = 0.25  # axial slot, ASSUMED shopable

    # Rev C structural drum shell — replaces the MDF disc stack as baseline.
    # The disc stack survives as documented Option B (D-047).
    shell_od: float = 5.0
    shell_wall: float = 0.25
    plug_inset: float = 0.25
    plug_thick: float = 1.5
    bearing_offset: float = 0.35  # ball CL outboard of the side face — MEASURE
    drum_option: str = "A"  # A = aluminium shell (baseline) · B = MDF disc stack

    # Precision adjustment — Rev C
    gib_clearance: float = 0.0015
    jack_thread_tpi: float = 28.0
    jack_arm_l1: float = 6.0
    jack_arm_l2: float = 1.25

    # Drive — Rev C re-sheave for surface speed (D-046)
    motor_hp: float = 1.0
    motor_rpm: float = 1725.0
    pulley_motor_od: float = 3.5
    pulley_drum_od: float = 5.0
    belt: str = "4L / A-section V-belt (size to center distance)"
    drum_rpm: float = 1207.5

    # Frame — inner span is the constraint, even with 18 mm Euro BB
    ply_nominal: float = 0.75
    ply_actual: float = 0.75  # USER_MEASURE; 18 mm Euro ≈ 0.709
    side_height: float = 30.0
    side_depth: float = 22.0
    clear_between_sides: float = 16.5
    base_thick: float = 0.75
    stretcher_count: int = 3
    stretcher_height: float = 4.0  # Z extent — rails stand on edge
    stretcher_housing: float = 0.25  # dado into each side, DERIVED joinery
    # B.4 stations: (id, y0 from infeed, z0 from bottom). Rail is ply thick
    # in Y and stretcher_height in Z. Placed to miss the table envelope,
    # the drum, and the motor. Do not put a rail at Z ≈ 12 — that is the table.
    stretcher_stations: tuple = (
        ("IN-LO", 0.25, 1.00),    # infeed low, above the base, infeed of the motor
        ("OUT-LO", 21.00, 1.00),  # outfeed low
        ("OUT-HI", 21.00, 22.00), # outfeed high, above the drum OD
    )

    # Ways — stock vs projecting (table must actually fit)
    way_stock: float = 0.75
    way_width: float = 2.5  # Y extent of the vertical strip, centered on drum CL
    way_z_margin: float = 0.50  # extra way above/below the table travel
    slide_clearance: float = 0.020  # T1 sliding, UHMW (X gap, table to tongue)
    kerf: float = 0.125
    sheet_bb: float = 60.0
    waste_factor_sheet: float = 0.12
    waste_factor_lumber: float = 0.30

    # Table construction
    table_skin: float = 0.75
    table_rib: float = 0.50
    table_wear: float = 0.25  # model wear; purchase ½″ phenolic or ⅜″ MIC-6
    table_rib_oc: float = 4.0
    elev_travel: float = 3.25
    acme_od: float = 0.5
    acme_tpi: float = 10.0
    acme_length: float = 12.0
    acme_inset_x: float = 2.4  # from inner face toward center; Y is drum CL
    # Table shoes wrap the 0.23″ UHMW tongue so the table can only move in Z
    shoe_h: float = 4.0
    shoe_t: float = 1.25  # X, hangs under the table edge
    shoe_groove_extra: float = 0.010  # groove deeper than tongue, X
    shoe_side_clear: float = 0.008  # per Y face of the 2.5″ way
    thrust_l: float = 3.0
    thrust_w: float = 3.0
    thrust_h: float = 1.5
    dog_l: float = 2.0
    dog_w: float = 1.0
    dog_h: float = 0.5

    # Hold-downs
    roller_od: float = 1.25
    roller_setbelow: float = 0.030
    roller_spring: str = "Light compression; too much = snipe"
    yoke_thick: float = 0.75
    yoke_width: float = 3.0
    yoke_length: float = 18.0

    # Oscillation
    osc_stroke: float = 0.125
    osc_cpm: float = 80.0

    # Dust
    hood_ply: float = 0.25
    dust_port_od: float = 4.0
    hood_blank_w: float = 18.0
    hood_blank_h: float = 12.0
    hood_method: str = "Kerf-bent ¼″ pine/birch ply, sawdust-glue filled"

    # Layout datums on the side panel (ASSUMED from Rev B drawings, now named)
    bearing_cl_z: float = 18.5  # from floor datum (base bottom)
    motor_pivot_y: float = 4.0
    motor_pivot_z: float = 6.0
    display_gap_under_drum: float = 0.50  # viz opening, not min capacity

    # Hole / cut patterns on P-001 (ASSUMED until flange BCD is USER_CONFIRM)
    flange_bolt_square: float = 3.00  # 1¼″-bore flange CTC — MEASURE YOURS
    flange_bolt_clr: float = 0.406  # 13/32″ for ⅜-16
    ply_shaft_clear_dia: float = 1.625  # shaft must not rub the plywood
    motor_pivot_dia: float = 0.266  # F / 17/64 for ¼-20
    indicator_pad_y: float = 8.0  # drive side only, from infeed
    indicator_pad_z: float = 16.0
    indicator_pad_dia: float = 0.201  # #7 tap-drill for ¼-20
    stretcher_screw_inset: float = 0.75  # from dado Z ends, through from outside
    idler_float_pad: float = 0.25  # UHMW pad under H-002; axial, not YZ slots

    # Jigs
    cradle_w: float = 12.0
    cradle_h: float = 8.0
    sled_depth: float = 8.0
    bore_jig: float = 12.0

    modernizations: tuple[str, ...] = (
        "Dual ½-10 Acme table screws on the drum centerline, chain-coupled",
        "Left screw uncouples for taper; dog stop returns to parallel home",
        "Vertical captured UHMW ways — table is a lifting carriage, not a Y-slide",
        "Housed stretchers (¼″ dados) + through-screws for racking stiffness",
        "Stack-drill side panels as a pair; floating idler bearing (axial pad, not YZ slots)",
        "Torsion-box table + phenolic / tooling-plate wear face",
        "Spring hold-down rollers infeed + outfeed — kills snipe and chatter",
        "Full-width truing sled; re-clock after paper wrap (ALN-01)",
        "Dial-indicator pad on drive side; 0.001″ pass schedule",
        "Optional ⅛″ slow oscillation (gear motor) to erase spiral tracks",
        "Structural 6061 drum shell + turned plugs (Option B disc stack documented)",
        "Tapered UHMW gib + ¼-28 idler jack for ALN-01",
        "Frame housed dados through-bolted (H-034) — glue is not primary structure",
    )


SPEC = Spec()


@dataclass(frozen=True)
class Geom:
    """Every number here is an equation of Spec. Change Spec, this follows."""

    side_thick: float
    overall_width: float
    overall_depth: float
    overall_height: float
    table_width: float
    table_depth: float
    table_thick: float
    way_project: float
    way_rebate: float
    stretcher_length: float
    drum_length: float
    disc_count: int
    drum_oversize_od: float
    bearing_cl_y: float
    bearing_cl_z: float
    drum_bottom_z: float
    table_z_at_max_stock: float
    table_z_at_min_stock: float
    table_z_display: float
    acme_y: float
    acme_y_infeed: float  # alias of acme_y — both screws share drum CL
    acme_y_outfeed: float
    acme_x_left: float
    acme_x_right: float
    acme_per_turn: float
    way_y0: float
    way_y1: float
    way_z0: float
    way_z1: float
    way_len: float
    way_width: float
    shoe_h: float
    shoe_w: float
    shoe_t: float
    shoe_groove_depth: float
    shoe_groove_width: float
    thrust_l: float
    thrust_w: float
    thrust_h: float
    dog_l: float
    dog_w: float
    dog_h: float
    stretcher_stations: tuple
    drum_top_z: float
    min_stretcher_table_clear: float
    roller_len: float
    roller_z: float
    surface_fpm: float
    drum_end_gap: float
    base_width: float
    base_depth: float
    ply_actual: float
    clear: float
    equations: dict[str, str]


def build_geom(s: Spec = SPEC) -> Geom:
    side_thick = s.ply_actual
    overall_width = s.clear_between_sides + 2 * side_thick
    table_width = s.capacity_width + 2 * s.table_margin_each
    remain_each = (s.clear_between_sides - table_width) / 2.0
    way_project = remain_each - s.slide_clearance
    way_rebate = s.way_stock - way_project
    stretcher_length = s.clear_between_sides + 2 * s.stretcher_housing
    disc_count = s.disc_count_core + s.disc_count_ends
    drum_length = disc_count * s.disc_thick  # 21 × 0.75 = 15.75
    bearing_cl_y = s.side_depth / 2.0
    drum_bottom_z = s.bearing_cl_z - s.drum_od / 2.0
    wear = s.table_wear
    core = s.table_skin * 2 + s.table_rib  # 0.75+0.75+0.5 = 2.0; wear sits on top
    # Finished table stack: two ¾″ skins + ½″ ribs, then wear face on top.
    # Spec historically used 1.5″ overall; skins+ribs crush to ~1.5 if ribs
    # are inside the skins (torsion box), wear is extra. Keep torsion-box
    # overall = 1.5″ including a 0.25″ wear (skins ¾+¾ with ½ rib inset).
    table_thick = s.table_skin + s.table_skin  # 1.5 torsion box; wear modeled 0.25 of that
    table_z_at_max = drum_bottom_z - s.max_stock_thickness - table_thick
    table_z_at_min = drum_bottom_z - s.min_stock_thickness - table_thick
    table_z_display = drum_bottom_z - s.display_gap_under_drum - table_thick
    acme_x_left = side_thick + s.acme_inset_x
    acme_x_right = overall_width - side_thick - s.acme_inset_x
    acme_y = bearing_cl_y  # both screws under the drum — cutting force through the nuts
    way_z0 = round(table_z_at_max - s.way_z_margin, 3)
    way_z1 = round(table_z_at_min + table_thick + s.way_z_margin, 3)
    way_len = round(way_z1 - way_z0, 3)
    way_y0 = round(bearing_cl_y - s.way_width / 2.0, 3)
    way_y1 = round(bearing_cl_y + s.way_width / 2.0, 3)
    shoe_groove_depth = round(way_project + s.shoe_groove_extra, 3)
    shoe_groove_width = round(s.way_width + 2.0 * s.shoe_side_clear, 3)
    stations = []
    table_z_lo = table_z_at_max
    table_z_hi = table_z_at_min + table_thick
    min_clear = 1e9
    for sid, y0, z0 in s.stretcher_stations:
        y1 = y0 + side_thick
        z1 = z0 + s.stretcher_height
        # clearance in Z to the table envelope (full-depth table, so Y always overlaps)
        if z1 <= table_z_lo:
            clear_z = table_z_lo - z1
        elif z0 >= table_z_hi:
            clear_z = z0 - table_z_hi
        else:
            clear_z = -min(z1 - table_z_lo, table_z_hi - z0)  # overlap, negative
        min_clear = min(min_clear, clear_z)
        stations.append((sid, round(y0, 3), round(z0, 3), round(y1, 3), round(z1, 3)))
    roller_len = drum_length
    roller_z = table_z_display + table_thick + s.roller_od / 2.0 + s.roller_setbelow
    drum_end_gap = (s.clear_between_sides - drum_length) / 2.0
    drum_top_z = s.bearing_cl_z + s.drum_od / 2.0
    sfpm = (PI * s.drum_od / 12.0) * s.drum_rpm
    eqs = {
        "overall_width": "clear_between_sides + 2 × ply_actual",
        "table_width": "capacity_width + 2 × table_margin_each",
        "way_project": "(clear_between_sides − table_width) / 2 − slide_clearance",
        "way_rebate": "way_stock − way_project  (let into inner face so table fits)",
        "way_z0": "table_z_at_max_stock − way_z_margin",
        "way_z1": "table_z_at_min_stock + table_thick + way_z_margin",
        "way_y0": "bearing_cl_y − way_width / 2",
        "stretcher_length": "clear_between_sides + 2 × stretcher_housing",
        "drum_length": "(disc_count_core + disc_count_ends) × disc_thick",
        "bearing_cl_y": "side_depth / 2  (datum: infeed edge of side)",
        "drum_bottom_z": "bearing_cl_z − drum_od / 2",
        "drum_top_z": "bearing_cl_z + drum_od / 2",
        "table_z_at_max_stock": "drum_bottom_z − max_stock − table_thick",
        "table_z_at_min_stock": "drum_bottom_z − min_stock − table_thick",
        "acme_y": "bearing_cl_y  (both screws — not infeed/outfeed)",
        "acme_per_turn": "1 / acme_tpi",
        "surface_fpm": "π × drum_od / 12 × drum_rpm",
        "drum_end_gap": "(clear_between_sides − drum_length) / 2",
        "shoe_groove_depth": "way_project + shoe_groove_extra",
        "shoe_groove_width": "way_width + 2 × shoe_side_clear",
        "roller_len": "drum_length",
        "elev_travel_needed": "max_stock − min_stock  (≤ elev_travel)",
    }
    return Geom(
        side_thick=side_thick,
        overall_width=overall_width,
        overall_depth=s.side_depth,
        overall_height=s.side_height,
        table_width=table_width,
        table_depth=s.side_depth,
        table_thick=table_thick,
        way_project=round(way_project, 3),
        way_rebate=round(way_rebate, 3),
        stretcher_length=stretcher_length,
        drum_length=drum_length,
        disc_count=disc_count,
        drum_oversize_od=s.drum_od + s.disc_bandsaw_oversize,
        bearing_cl_y=bearing_cl_y,
        bearing_cl_z=s.bearing_cl_z,
        drum_bottom_z=drum_bottom_z,
        table_z_at_max_stock=round(table_z_at_max, 3),
        table_z_at_min_stock=round(table_z_at_min, 3),
        table_z_display=round(table_z_display, 3),
        acme_y=acme_y,
        acme_y_infeed=acme_y,
        acme_y_outfeed=acme_y,
        acme_x_left=acme_x_left,
        acme_x_right=acme_x_right,
        acme_per_turn=1.0 / s.acme_tpi,
        way_y0=way_y0,
        way_y1=way_y1,
        way_z0=way_z0,
        way_z1=way_z1,
        way_len=way_len,
        way_width=s.way_width,
        shoe_h=s.shoe_h,
        shoe_w=s.way_width,
        shoe_t=s.shoe_t,
        shoe_groove_depth=shoe_groove_depth,
        shoe_groove_width=shoe_groove_width,
        thrust_l=s.thrust_l,
        thrust_w=s.thrust_w,
        thrust_h=s.thrust_h,
        dog_l=s.dog_l,
        dog_w=s.dog_w,
        dog_h=s.dog_h,
        stretcher_stations=tuple(stations),
        drum_top_z=drum_top_z,
        min_stretcher_table_clear=round(min_clear, 3),
        roller_len=roller_len,
        roller_z=round(roller_z, 3),
        surface_fpm=round(sfpm, 0),
        drum_end_gap=round(drum_end_gap, 3),
        base_width=overall_width,
        base_depth=s.side_depth,
        ply_actual=side_thick,
        clear=s.clear_between_sides,
        equations=eqs,
    )


GEOM = build_geom(SPEC)


def stretcher_records(g: Geom = GEOM) -> list[dict[str, Any]]:
    """Named stretcher stations with AABBs in shop YZ (inner-face layout)."""
    rows = []
    for sid, y0, z0, y1, z1 in g.stretcher_stations:
        rows.append({"id": sid, "y0": y0, "z0": z0, "y1": y1, "z1": z1})
    return rows


def fmt_in(v: float, nd: int = 2) -> str:
    """Shop dimension: drop trailing zeros, keep a readable decimal."""
    if abs(v - round(v)) < 1e-9:
        return f"{int(round(v))}.00" if nd else f"{int(round(v))}"
    s = f"{v:.{nd}f}".rstrip("0").rstrip(".")
    if "." not in s:
        s += ".00"
    return s


def side_features(s: Spec = SPEC, g: Geom = GEOM, hand: str = "L") -> dict[str, Any]:
    """Named holes and cuts on P-001 inner face. Y from infeed, Z from bottom.

    Flange bolt square is ASSUMED — confirm against the purchased 4-bolt flange
    (USER_CONFIRM) before drilling. Stack-drill L+R as a pair first; inner-face
    dados and the way rebate are mirrored after the pair is split.
    """
    half = s.flange_bolt_square / 2.0
    by, bz = g.bearing_cl_y, g.bearing_cl_z
    bolts = [
        {"y": by + dy, "z": bz + dz, "dia": s.flange_bolt_clr, "id": f"FB{i+1}"}
        for i, (dy, dz) in enumerate(((-half, -half), (half, -half), (-half, half), (half, half)))
    ]
    dados = [
        {
            "id": f"J-001.{i+1}",
            "station": sid,
            "y0": y0,
            "y1": y1,
            "z0": z0,
            "z1": z1,
            "depth": s.stretcher_housing,
        }
        for i, (sid, y0, z0, y1, z1) in enumerate(g.stretcher_stations)
    ]
    way = {
        "id": "J-002",
        "y0": g.way_y0,
        "y1": g.way_y1,
        "z0": g.way_z0,
        "z1": g.way_z1,
        "depth": g.way_rebate,
        "project": g.way_project,
        "orientation": "vertical",
    }
    screws = []
    for i, d in enumerate(dados):
        mid_y = (d["y0"] + d["y1"]) / 2.0
        for j, z in enumerate((d["z0"] + s.stretcher_screw_inset, d["z1"] - s.stretcher_screw_inset)):
            screws.append({
                "id": f"SS{i+1}{chr(97+j)}",
                "y": mid_y,
                "z": z,
                "dia": 0.125,  # pilot; expand from outside after clamp-up
            })
    feats = {
        "hand": hand,
        "datums": "Y0 = infeed edge · Z0 = bottom edge · inner face toward drum",
        "bearing_cl": {"y": by, "z": bz, "shaft_clear_dia": s.ply_shaft_clear_dia},
        "flange_bolts": bolts,
        "flange_bolt_square": s.flange_bolt_square,
        "dados": dados,
        "way": way,
        "stretcher_screws": screws,
        "motor_pivot": None,
        "indicator_pad": None,
        "idler_pad": None,
        "evidence": {
            "outline": "VERIFIED",
            "bearing_cl": "VERIFIED layout",
            "flange_bcd": "ASSUMED — USER_CONFIRM vs purchased flange",
            "dados": "DERIVED from stretcher_stations (B.4, miss table envelope)",
            "way": "DERIVED J-002 vertical, centered on drum CL",
        },
    }
    if hand == "L":
        feats["motor_pivot"] = {
            "y": s.motor_pivot_y,
            "z": s.motor_pivot_z,
            "dia": s.motor_pivot_dia,
            "note": "¼-20 pivot for P-012. Drill after stack so L and R stay a pair; tap this hole on the drive side only.",
        }
        feats["indicator_pad"] = {
            "y": s.indicator_pad_y,
            "z": s.indicator_pad_z,
            "dia": s.indicator_pad_dia,
            "note": "¼-20 pad for H-021 mag-base / stem. Drive side is the A-clock datum.",
        }
    else:
        feats["idler_pad"] = {
            "note": (
                f"H-002 floats on a {s.idler_float_pad:g}″ UHMW pad (J-007). "
                "Do not elongate the flange holes in the YZ plane — that lets the drum axis wander. "
                "Bolts snug, not torqued; shaft must be able to grow axially."
            ),
            "pad_thick": s.idler_float_pad,
        }
    return feats


def in_mm(inches: float, nd: int = 1) -> str:
    return f'{inches:g}" / {inches * IN_TO_MM:.{nd}f} mm'


def size3(t: float, w: float, l: float, nd: int = 3) -> str:
    def fmt(v: float) -> str:
        if abs(v - round(v)) < 1e-9:
            return f"{v:g}"
        return f"{v:.{nd}f}".rstrip("0").rstrip(".")

    return f'{fmt(l)}" × {fmt(w)}" × {fmt(t)}"'


def size3_mm(t: float, w: float, l: float) -> str:
    return f"{l * IN_TO_MM:.0f} × {w * IN_TO_MM:.0f} × {t * IN_TO_MM:.0f} mm"


def surface_fpm(drum_od: float, rpm: float) -> float:
    return (PI * drum_od / 12.0) * rpm


def board_feet(t: float, w: float, l: float, qty: int = 1) -> float:
    return qty * t * w * l / 144.0


# ---------------------------------------------------------------------------
# 1. Validation
# ---------------------------------------------------------------------------

def validate(s: Spec = SPEC, g: Geom = GEOM) -> list[str]:
    errors: list[str] = []
    if g.table_width >= s.clear_between_sides:
        errors.append("Table wider than inner span")
    if g.way_project <= 0:
        errors.append("Way projection ≤ 0 — table/ways collision")
    if g.way_rebate >= s.ply_actual - 0.20:
        errors.append("Way rebate cuts through the side")
    if g.drum_length >= s.clear_between_sides:
        errors.append("Drum longer than inner span")
    if (s.max_stock_thickness - s.min_stock_thickness) > s.elev_travel + 1e-6:
        errors.append("Elev travel less than thickness range")
    if g.table_z_at_max_stock < s.base_thick + 0.5:
        errors.append("Table would hit the base at 3″ opening")
    if abs(g.drum_length - 15.75) > 1e-6:
        errors.append("Drum length drifted from 15.75″ pack")
    if abs(g.table_width - 16.0) > 1e-6:
        errors.append("Table width drifted from 16.0″")
    if s.stretcher_housing * 2 + 0.25 > s.ply_actual:
        errors.append("Stretcher housing too deep for ply")
    travel_need = s.max_stock_thickness - s.min_stock_thickness
    if travel_need > s.elev_travel:
        errors.append("Need more Acme travel")
    errors.extend(validate_mechanics(s, g))
    errors.extend(validate_steps())
    return errors


def _aabb_overlap(a: dict[str, float], b: dict[str, float], axes: str = "xyz") -> bool:
    for ax in axes:
        if a[f"{ax}1"] <= b[f"{ax}0"] or a[f"{ax}0"] >= b[f"{ax}1"]:
            return False
    return True


def validate_mechanics(s: Spec = SPEC, g: Geom = GEOM) -> list[str]:
    """Kinematic checks: stretchers miss the table, ways capture travel, Acme under the drum.

    These are the B.4 regressions. A stretcher at Z=12 used to occupy the same
    volume as a 3″-open table. Horizontal ways at Z=10 never supported the
    table at operating height. Dual-end Acme was drawn as infeed/outfeed Y
    instead of left/right X on the drum centerline.
    """
    errors: list[str] = []
    table_env = {
        "x0": s.ply_actual + (s.clear_between_sides - g.table_width) / 2.0,
        "x1": s.ply_actual + (s.clear_between_sides - g.table_width) / 2.0 + g.table_width,
        "y0": 0.0,
        "y1": g.table_depth,
        "z0": g.table_z_at_max_stock,
        "z1": g.table_z_at_min_stock + g.table_thick,
    }
    drum = {
        "x0": s.ply_actual + g.drum_end_gap,
        "x1": s.ply_actual + g.drum_end_gap + g.drum_length,
        "y0": g.bearing_cl_y - s.drum_od / 2.0,
        "y1": g.bearing_cl_y + s.drum_od / 2.0,
        "z0": g.drum_bottom_z,
        "z1": g.drum_top_z,
    }
    # Motor as modeled: OpenSCAD translate([side_t+2.2, 3, 2]) cube([6, 8, 6])
    motor = {
        "x0": s.ply_actual + 2.2,
        "x1": s.ply_actual + 8.2,
        "y0": 3.0,
        "y1": 11.0,
        "z0": 2.0,
        "z1": 8.0,
    }
    for rec in stretcher_records(g):
        st = {
            "x0": s.ply_actual - s.stretcher_housing,
            "x1": s.ply_actual - s.stretcher_housing + g.stretcher_length,
            "y0": rec["y0"],
            "y1": rec["y1"],
            "z0": rec["z0"],
            "z1": rec["z1"],
        }
        if rec["z1"] > s.side_height - 0.25:
            errors.append(f"Stretcher {rec['id']} exceeds side height")
        if rec["y0"] < 0 or rec["y1"] > s.side_depth:
            errors.append(f"Stretcher {rec['id']} exceeds side depth")
        if _aabb_overlap(st, table_env, "xyz"):
            errors.append(
                f"Stretcher {rec['id']} intersects the table envelope "
                f"Y {rec['y0']:g}–{rec['y1']:g} Z {rec['z0']:g}–{rec['z1']:g}"
            )
        if _aabb_overlap(st, drum, "xyz"):
            errors.append(f"Stretcher {rec['id']} intersects the drum")
        if _aabb_overlap(st, motor, "xyz"):
            errors.append(f"Stretcher {rec['id']} intersects the motor envelope")
    if g.min_stretcher_table_clear < 0.25:
        errors.append(
            f"Stretcher-to-table Z clearance {g.min_stretcher_table_clear:.3f}″ is under 0.25″"
        )
    if g.way_z0 > g.table_z_at_max_stock + 1e-6:
        errors.append("Ways start above the table at max opening — table is unsupported")
    if g.way_z1 < g.table_z_at_min_stock + g.table_thick - 1e-6:
        errors.append("Ways end below the table at min opening — table walks off the way")
    if abs((g.way_y0 + g.way_y1) / 2.0 - g.bearing_cl_y) > 1e-6:
        errors.append("Vertical ways are not centered on the drum centerline")
    if abs(g.acme_y - g.bearing_cl_y) > 1e-6:
        errors.append("Acme Y is not on the drum centerline")
    if abs(g.acme_y_infeed - g.acme_y) > 1e-6 or abs(g.acme_y_outfeed - g.acme_y) > 1e-6:
        errors.append("Acme Y aliases drifted — both screws must share drum CL")
    if g.shoe_groove_depth <= g.way_project:
        errors.append("Shoe groove does not clear the way tongue")
    if g.shoe_groove_width <= g.way_width:
        errors.append("Shoe groove is tighter than the way in Y")
    ids = {p["part_id"] for p in parts()}
    for pid in ("P-017", "P-018", "P-019"):
        if pid not in ids:
            errors.append(f"Missing mechanical part {pid}")
    calc_ids = {c["id"] for c in calculations(s, g)}
    for cid in ("CALC-001", "CALC-002", "CALC-003", "CALC-004", "CALC-005"):
        if cid not in calc_ids:
            errors.append(f"Missing calculation {cid}")
    if LAYOUT_PROTOCOL.get("mode") != "HYBRID":
        errors.append("Layout protocol must declare HYBRID")
    return errors


def calculations(s: Spec = SPEC, g: Geom = GEOM) -> list[dict[str, Any]]:
    """Numbered calcs for G-003. Evidence: [D] derived, [E] estimated bound."""
    belt_rpm = s.motor_rpm * s.pulley_motor_od / s.pulley_drum_od
    turns_3in = 3.0 / g.acme_per_turn
    # Table sag bound: simply supported 16″ span, 50 lbf mid-span, torsion-box I.
    # Two ¾″ skins 22″ wide, effective I ≈ 2 × b t (d/2)² with d=1.5, t=0.75, b=22
    # → I ≈ 18.6 in⁴. E_ply ≈ 1.5e6 psi. δ = P L³ / 48 E I.
    sag_p, sag_l, sag_e, sag_i = 50.0, g.table_width, 1.5e6, 18.6
    sag = sag_p * sag_l ** 3 / (48.0 * sag_e * sag_i)
    # Drum KE: MDF cylinder, 48 pcf, plus birch ends. ESTIMATED.
    vol = PI * (s.drum_od / 2.0) ** 2 * g.drum_length
    mass_lb = vol * 0.0278 + 1.5  # MDF + birch ends / flanges
    r_ft = (s.drum_od / 2.0) / 12.0
    mass_slug = mass_lb / 32.174
    inertia = 0.5 * mass_slug * r_ft ** 2
    omega = s.drum_rpm * 2.0 * PI / 60.0
    ke = 0.5 * inertia * omega ** 2
    return [
        {
            "id": "CALC-001",
            "name": "Belt ratio → drum RPM",
            "expr": f"{s.motor_rpm:g} × {s.pulley_motor_od:g} / {s.pulley_drum_od:g}",
            "result": f"{belt_rpm:g} RPM",
            "value": belt_rpm,
            "evidence": "D",
            "ok": abs(belt_rpm - s.drum_rpm) < 1.0,
        },
        {
            "id": "CALC-002",
            "name": "Drum surface speed",
            "expr": f"π × {s.drum_od:g} / 12 × {s.drum_rpm:g}",
            "result": f"{g.surface_fpm:g} sfpm",
            "value": g.surface_fpm,
            "evidence": "D",
            "ok": 800 <= g.surface_fpm <= 1800,
        },
        {
            "id": "CALC-003",
            "name": "Acme lead and 3″ travel",
            "expr": f"1/{s.acme_tpi:g} TPI; 3″ / {g.acme_per_turn:.3f}″",
            "result": f"{g.acme_per_turn:.3f}″/rev · {turns_3in:g} turns for 3″",
            "value": turns_3in,
            "evidence": "D",
            "ok": abs(turns_3in - 30.0) < 1e-6,
        },
        {
            "id": "CALC-004",
            "name": "Stretcher vs table envelope",
            "expr": "min Z gap, all three rails, table at every opening",
            "result": f"{g.min_stretcher_table_clear:.3f}″ minimum clearance",
            "value": g.min_stretcher_table_clear,
            "evidence": "D",
            "ok": g.min_stretcher_table_clear >= 0.25,
        },
        {
            "id": "CALC-005",
            "name": "Way capture / shoe clearance",
            "expr": f"tongue {g.way_project:.3f}″ in groove {g.shoe_groove_depth:.3f}″; Y {g.way_width:g}″ + {2 * s.shoe_side_clear:.3f}″",
            "result": f"X play {g.shoe_groove_depth - g.way_project:.3f}″ · Y play {g.shoe_groove_width - g.way_width:.3f}″",
            "value": g.shoe_groove_depth - g.way_project,
            "evidence": "D",
            "ok": 0.008 <= (g.shoe_groove_depth - g.way_project) <= 0.020,
        },
        {
            "id": "CALC-006",
            "name": "Table sag bound (50 lbf mid-span)",
            "expr": f"P L³ / 48 E I · L={sag_l:g}″ E={sag_e:g} I≈{sag_i:g} in⁴",
            "result": f"{sag:.4f}″ estimated · spec flat ≤ {s.table_flat_tol:.3f}″",
            "value": sag,
            "evidence": "E",
            "ok": sag < s.table_flat_tol,
        },
        {
            "id": "CALC-007",
            "name": "Drum rotational energy",
            "expr": f"½ I ω² · m≈{mass_lb:.1f} lb · {s.drum_rpm:g} RPM",
            "result": f"{ke:.0f} ft·lbf estimated",
            "value": ke,
            "evidence": "E",
            "ok": True,
        },
    ] + [
        # Rev C mechanics register (CALC-C01…C18) computed in ds16_mechanics.py.
        # Mapped onto the same row shape so one table renders both generations.
        {
            "id": c["id"],
            "name": c["question"],
            "expr": c["equation"],
            "result": c["result"],
            "value": 0.0,
            "evidence": c["evidence"][:1],
            "ok": not c["verdict"].startswith("FAIL"),
            "criterion": c["criterion"],
            "margin": c["margin"],
            "verdict": c["verdict"],
            "inputs": c["inputs"],
            "method": c["method"],
            # CALC-C01 is a RESOLVED finding about Rev B, not an open defect. It is
            # kept in the register because deleting the evidence would hide why the
            # drum axis was redesigned.
            "historical": c["id"] == "CALC-C01",
        }
        for c in mech_calculations(MECH)
    ]


def accuracy_budgets() -> dict[str, Any]:
    """The two Rev C specifications, as auditable tables."""
    return {
        "ALN-01": alignment_budget(MECH),
        "TV-01-revC": thickness_variation_budget(MECH, "C"),
        "TV-01-revB": thickness_variation_budget(MECH, "B"),
    }


def superseded_by_rev_c() -> list[dict[str, str]]:
    """Every Rev B artefact that Rev C changes. Revision control, not a footnote.

    PLANFORGE forbids patching only the visible drawing. Anything listed here is
    regenerated from this file; nothing needs hand-editing. The list exists so a
    reviewer can see the blast radius of D-041 at a glance.
    """
    return [
        {"artefact": "P-010 shaft", "was": '¾″ × 22.5″', "now": '1¼″ × 24″', "driver": "D-041 / CALC-C01"},
        {"artefact": "P-008 / P-009 discs", "was": "baseline drum", "now": "Option B alternative only", "driver": "D-047"},
        {"artefact": "P-015 pack-bore jig", "was": "baseline", "now": "Option B only", "driver": "D-047"},
        {"artefact": "P-020 / P-021", "was": "did not exist", "now": "baseline drum shell + plugs", "driver": "D-041"},
        {"artefact": "P-022 gib", "was": "did not exist", "now": "sets way clearance", "driver": "D-042"},
        {"artefact": "P-023 / P-024", "was": "did not exist", "now": "parallelism micro-adjust", "driver": "D-043"},
        {"artefact": "H-001 / H-002 bearings", "was": '¾″ bore, unspecified rating', "now": f'1¼″ bore, C ≥ {MECH_C_REQUIRED:.0f} lbf, self-aligning', "driver": "D-045 / CALC-C11"},
        {"artefact": "H-003 motor sheave", "was": '3″', "now": '3½″', "driver": "D-046 / CALC-C12"},
        {"artefact": "Motor", "was": "½ HP", "now": "1 HP", "driver": "D-046"},
        {"artefact": "ply_shaft_clear_dia", "was": '1.125″', "now": '1.625″', "driver": "D-041 shaft size"},
        {"artefact": "flange_bolt_square", "was": '2.05″ [A]', "now": '3.00″ [A] — MEASURE YOURS', "driver": "D-041"},
        {"artefact": "Spec 0.003″", "was": "one number for two quantities", "now": "ALN-01 0.003″ and TV-01 0.005″", "driver": "D-040 / CALC-C06"},
        {"artefact": "QC-07 / QC-10", "was": "conflated parallel and scatter", "now": "QC-15 ALN-01 and QC-16 TV-01", "driver": "D-040"},
        {"artefact": "Frame joinery", "was": "screws", "now": "housed dado + through-bolts", "driver": "D-048"},
        {"artefact": "Build steps", "was": "14 steps", "now": f"{len(build_steps())} steps", "driver": "Rev C drum + gib + micro-adjust"},
    ]


def validate_steps() -> list[str]:
    """Every ID named in a build step must exist, and every part must be used.

    This is the check that stops the guide book from telling a builder to fetch
    a part number that no drawing defines, or from silently orphaning a part.
    """
    errors: list[str] = []
    part_ids = {p["part_id"] for p in parts()}
    hw_ids = {h["hardware_id"] for h in hardware()}
    qc_ids = {q["qc"] for q in inspection()}
    viz_ids = {
        "sides", "base", "stretch", "ways", "table", "elev",
        "drum", "shaft", "motor", "rollers", "hood",
    }
    used: set[str] = set()
    for st in build_steps():
        w = st["id"]
        for pid in st["parts"]:
            if pid not in part_ids:
                errors.append(f"{w}: unknown part {pid}")
        for hid in st["hardware"]:
            if hid not in hw_ids:
                errors.append(f"{w}: unknown hardware {hid}")
        for qc in (st.get("qc") or "").replace("\u00b7", " ").split():
            if qc.startswith("QC-") and qc not in qc_ids:
                errors.append(f"{w}: unknown QC gate {qc}")
        for g in list(st["shows"]) + list(st["adds"]):
            if g not in viz_ids:
                errors.append(f"{w}: unknown viz group {g}")
        for g in st["adds"]:
            if g not in st["shows"]:
                errors.append(f"{w}: adds {g} but does not show it")
        used.update(st["parts"])
    orphan = sorted(part_ids - used)
    if orphan:
        errors.append("Parts never used in a build step: " + ", ".join(orphan))
    return errors


# ---------------------------------------------------------------------------
# 2. Part registry
# ---------------------------------------------------------------------------

def _part(
    pid: str,
    name: str,
    qty: int,
    *,
    category: str,
    assembly: str,
    make: str,
    material: str,
    species: str = "",
    t: float = 0,
    w: float = 0,
    l: float = 0,
    rough_t: float | None = None,
    rough_w: float | None = None,
    rough_l: float | None = None,
    grain: str = "",
    ref_face: str = "",
    ref_edge: str = "",
    ref_end: str = "",
    process: str = "",
    joinery: str = "",
    handed: str = "IDENTICAL",
    viz: str = "",
    sheet: str = "",
    notes: str = "",
    purchase: str = "",
    evidence: str = "DERIVED",
) -> dict[str, Any]:
    rt, rw, rl = rough_t if rough_t is not None else t, rough_w if rough_w is not None else (w + 0.125 if w else 0), rough_l if rough_l is not None else (l + 0.5 if l else 0)
    return {
        "part_id": pid,
        "part_name": name,
        "part_category": category,
        "assembly": assembly,
        "qty": qty,
        "make_or_buy": make,
        "material": material,
        "species": species,
        "finished_t": t,
        "finished_w": w,
        "finished_l": l,
        "rough_t": rt,
        "rough_w": rw,
        "rough_l": rl,
        "finished_size": size3(t, w, l) if t and w and l else purchase or "",
        "finished_size_mm": size3_mm(t, w, l) if t and w and l else "",
        "rough_size": size3(rt, rw, rl) if rt and rw and rl else "",
        "purchase_size": purchase,
        "grain_direction": grain,
        "reference_face": ref_face,
        "reference_edge": ref_edge,
        "reference_end": ref_end,
        "process": process,
        "joinery": joinery,
        "handed": handed,
        "viz_id": viz,
        "sheet": sheet,
        "notes": notes,
        "evidence": evidence,
        "revision": SPEC.fabrication_rev,
    }


def parts(s: Spec = SPEC, g: Geom = GEOM) -> list[dict[str, Any]]:
    """Persistent IDs. Do not renumber because a drawing order changed."""
    t = g.side_thick
    return [
        _part(
            "P-001L", "Side panel, drive (left)", 1,
            category="panel", assembly="A-FRAME", make="MAKE",
            material="Baltic birch plywood", species="Birch",
            t=t, w=s.side_depth, l=s.side_height,
            rough_t=t, rough_w=s.side_depth + 0.125, rough_l=s.side_height + 0.25,
            grain="face grain vertical", ref_face="Inner face (ways/dados)",
            ref_edge="Bottom (sits on base)", ref_end="Infeed edge = Datum Y0",
            process="Cut, pair-stack drill, then dado inner face",
            joinery="J-001 housed stretchers; J-002 way rebate; through holes for bearings",
            handed="LEFT-HAND", viz="sides", sheet="P001L_side_drive.svg",
            notes="Stack-drill with P-001R as a pair, then split for inner-face work.",
            evidence="VERIFIED overall; dados B.1",
        ),
        _part(
            "P-001R", "Side panel, idler (right)", 1,
            category="panel", assembly="A-FRAME", make="MAKE",
            material="Baltic birch plywood", species="Birch",
            t=t, w=s.side_depth, l=s.side_height,
            rough_t=t, rough_w=s.side_depth + 0.125, rough_l=s.side_height + 0.25,
            grain="face grain vertical", ref_face="Inner face (ways/dados)",
            ref_edge="Bottom", ref_end="Infeed edge = Datum Y0",
            process="Cut, pair-stack drill, then dado inner face (mirror of L)",
            joinery="J-001; J-002; idler flange on axial-float slots J-007",
            handed="RIGHT-HAND / MIRROR", viz="sides", sheet="P001R_side_idler.svg",
            notes="Identical hole pattern to L after stack-drill. Ways and dados on inner face only.",
            evidence="VERIFIED overall; dados B.1",
        ),
        _part(
            "P-002", "Base deck", 1,
            category="panel", assembly="A-FRAME", make="MAKE",
            material="Baltic birch plywood", species="Birch",
            t=s.base_thick, w=g.base_depth, l=g.base_width,
            grain="face grain across drum", ref_face="Top", ref_edge="Infeed",
            ref_end="Drive edge", process="Cut to overall footprint; screw to sides",
            joinery="J-010 screws up into sides", handed="IDENTICAL", viz="base",
            sheet="P002_base.svg", notes="Width follows ply_actual so 18 mm BB still keeps 16.5″ clear.",
        ),
        _part(
            "P-003", "Stretcher", 3,
            category="rail", assembly="A-FRAME", make="MAKE",
            material="Baltic birch plywood", species="Birch",
            t=t, w=s.stretcher_height, l=g.stretcher_length,
            grain="length along X (across drum)", ref_face="Top",
            ref_edge="Front long edge", ref_end="Drive end",
            process="Rip 4″, crosscut to housed length, one stop for all three",
            joinery="J-001 ¼″ housing in sides + #8 × 2″ through-screws",
            handed="IDENTICAL", viz="stretch", sheet="P003_stretcher.svg",
            notes="Stand on edge (4″ is Z). Stations IN-LO / OUT-LO / OUT-HI miss the table. Ways locate the table.",
            purchase='¾" BB off sheet 1',
        ),
        _part(
            "P-004", "Table torsion-box skin", 2,
            category="panel", assembly="A-TABLE", make="MAKE",
            material="Baltic birch plywood", species="Birch",
            t=s.table_skin, w=g.table_depth, l=g.table_width,
            grain="length across drum", ref_face="Show face outboard",
            process="Cut pair; glue to rib grid; flatten before wear face",
            joinery="J-003 continuous glue to P-005", handed="IDENTICAL",
            viz="table", sheet="P004_table_skin.svg",
        ),
        _part(
            "P-005", "Torsion-box ribs", 8,
            category="rib", assembly="A-TABLE", make="MAKE",
            material="Baltic birch or MDF", species="",
            t=s.table_rib, w=g.table_thick - 0.25, l=g.table_width - 0.5,
            rough_t=s.table_rib, rough_w=2.0, rough_l=g.table_width,
            process="Rip ½″, grid @ 4″ o.c., full glue",
            joinery="J-003", handed="IDENTICAL", viz="table", sheet="P005_table_ribs.svg",
            notes="Qty is typical for 4″ o.c. in 22″ depth; cut from offcuts.",
            evidence="ESTIMATED qty from spacing",
        ),
        _part(
            "P-006", "Table wear face", 1,
            category="wear", assembly="A-TABLE", make="MAKE",
            material="Phenolic sheet or MIC-6 / cast tooling plate",
            t=0.5, w=g.table_depth, l=g.table_width,
            purchase='½" phenolic or ⅜" MIC-6, 16" × 22"',
            ref_face="Top = metrology surface", process="Bond to flattened box; check diagonals",
            joinery="J-004 bond, replaceable", handed="IDENTICAL", viz="table",
            sheet="P006_wear_face.svg", notes="This is the inspection plane. Keep a spare.",
            evidence="VERIFIED size; thickness is BUY option ½″ or ⅜″",
        ),
        _part(
            "P-007", "UHMW way", 2,
            category="way", assembly="A-FRAME", make="MAKE",
            material="UHMW-PE", t=s.way_stock, w=s.way_width, l=g.way_len,
            purchase='¾" × 2½" UHMW bar, 12" buys both',
            process="Cut to way_len; let into vertical J-002 rebate; bond + wax",
            joinery="J-002 vertical rebate + glue; optional #8 flush screws from outer face",
            handed="IDENTICAL", viz="ways", sheet="P007_uhmw_way.svg",
            notes=f"Vertical strip, {g.way_len:g}″ Z × {s.way_width:g}″ Y, centered on drum CL. Projects {g.way_project:.3f}″. Rebate {g.way_rebate:.3f}″.",
            evidence="DERIVED project/rebate so 16″ table fits in 16.5″ span; length follows table travel",
        ),
        _part(
            "P-008", "Drum disc, core", s.disc_count_core,
            category="disc", assembly="A-DRUM", make="MAKE",
            material="MDF", t=s.disc_thick, w=g.drum_oversize_od, l=g.drum_oversize_od,
            purchase='¾" MDF, bandsaw ⌀5⅛″',
            process=f"Bandsaw oversize, pack-bore ⌀{s.shaft_od:g}″ (Option B only), true on sled to ⌀5″",
            joinery="J-005 pack-bore + piano-wire keys; 1 mm relief every 4",
            handed="IDENTICAL", viz="drum", sheet="P008_disc_core.svg",
        ),
        _part(
            "P-009", "Drum disc, end", s.disc_count_ends,
            category="disc", assembly="A-DRUM", make="MAKE",
            material="Baltic birch plywood", species="Birch",
            t=s.disc_thick, w=g.drum_oversize_od, l=g.drum_oversize_od,
            process="Same pack as P-008; static-balance these two",
            joinery="J-005", handed="IDENTICAL", viz="drum", sheet="P009_disc_end.svg",
            notes="BB ends resist crushing at the flanges.",
        ),
        _part(
            "P-010", "Drum shaft", 1,
            category="shaft", assembly="A-DRUM", make="BUY-CUT",
            material="Precision-ground CRS / TG&P",
            t=s.shaft_od, w=s.shaft_od, l=s.shaft_length,
            purchase=f'{s.shaft_od:g}" TG&P × {s.shaft_length:g}" (MC-02)',
            process="Cut square, chamfer 0.030 × 45°, deburr. Do not centre-punch the bearing seats.",
            joinery="J-106 plugs; J-006 fixed drive flange; J-007 floating idler",
            handed="IDENTICAL", viz="shaft", sheet="P010_shaft.svg",
            notes=s.shaft_spec, evidence="VERIFIED",
        ),
        _part(
            "P-011", "Dust hood blank", 1,
            category="hood", assembly="A-HOOD", make="MAKE",
            material="Birch or pine plywood", t=s.hood_ply, w=s.hood_blank_h, l=s.hood_blank_w,
            process="Kerf-bend, glue to form, fill kerfs, 4″ port",
            joinery="Friction on sides; paraffin at paint rubs",
            handed="IDENTICAL", viz="hood", sheet="P011_hood.svg",
            notes=s.hood_method, evidence="ESTIMATED blank; trim to drum arc",
        ),
        _part(
            "P-012", "Motor pivot cradle", 1,
            category="jig", assembly="A-DRIVE", make="MAKE",
            material="Baltic birch plywood", t=t, w=s.cradle_h, l=s.cradle_w,
            process="Cut, T-nuts for pivot/lock", joinery="J-008 ¼-20 T-nuts",
            handed="IDENTICAL", viz="motor", sheet="P012_motor_cradle.svg",
        ),
        _part(
            "P-013", "Full-width truing sled", 1,
            category="jig", assembly="A-JIG", make="MAKE",
            material="MDF or Baltic birch", t=t, w=s.sled_depth, l=g.table_width,
            process="Abrasive face-up; rides the ways",
            joinery="none — fixture", handed="IDENTICAL", viz="table",
            sheet="P013_truing_sled.svg", notes="As wide as the drum so you cannot dish the middle.",
        ),
        _part(
            "P-014", "Hold-down roller yoke", 2,
            category="yoke", assembly="A-TABLE", make="MAKE",
            material="Hardwood or 1½″ aluminum angle",
            t=s.yoke_thick, w=s.yoke_width, l=s.yoke_length,
            process="Cut pair; shoulder-bolt pivots; spring pockets",
            joinery="J-009 shoulder bolts + springs",
            handed="IDENTICAL", viz="rollers", sheet="P014_roller_yoke.svg",
            notes=f"Board feet net {board_feet(s.yoke_thick, s.yoke_width, s.yoke_length, 2):.2f}; buy with {s.waste_factor_lumber:.0%} waste.",
        ),
        _part(
            "P-015", "Disc pack-bore jig", 1,
            category="jig", assembly="A-JIG", make="MAKE",
            material="MDF", t=t, w=s.bore_jig, l=s.bore_jig,
            process=f"Fence + clamp wall; drill/ream ⌀{s.shaft_od:g}″ through the pack (Option B)",
            joinery="none", handed="IDENTICAL", viz="drum", sheet="P015_pack_bore.svg",
        ),
        _part(
            "P-020", "Drum shell, aluminium tube", 1,
            category="drum", assembly="A-DRUM", make="MAKE",
            material=f"6061-T6 aluminium tube {s.shell_od:g}″ OD × {s.shell_wall:g}″ wall",
            t=s.shell_wall, w=s.shell_od, l=g.drum_length,
            purchase=f'{s.shell_od:g}" OD × {s.shell_wall:g}" wall × 18" (H-027 / MC-01)',
            grain="n/a — isotropic", ref_face="OD after final truing",
            ref_end="Drive end",
            process="Cut 1/8″ long, face both ends square, bond+pin to P-021, "
                    "then true the OD with the shaft in its own bearings",
            joinery="J-106 shell → plug → shaft",
            handed="IDENTICAL", viz="drum", sheet="P020_drum_shell.svg",
            notes=f"Wall is the stiffness requirement: I = {AXIS_I_SHELL:.2f} in⁴. "
                  f"This part is why Rev C holds the accuracy spec (CALC-C02).",
            evidence="DERIVED from CALC-C02",
        ),
        _part(
            "P-021", "Drum end plug", 2,
            category="drum", assembly="A-DRUM", make="MAKE",
            material="6061-T6 aluminium",
            t=s.plug_thick, w=s.shell_od - 2 * s.shell_wall, l=s.shell_od - 2 * s.shell_wall,
            purchase='4½" dia bar × 4" (H-028 / MC-04)',
            ref_face="OD (bonds to shell ID)", ref_end="Outboard face",
            process=f"Turn OD to a light bond fit in the shell ID and bore "
                    f"{s.shaft_od:g}″ ON THE SAME SETUP so bore and OD are concentric",
            joinery="J-106; cross-pinned to shell, clamp-collared to shaft",
            handed="IDENTICAL", viz="drum", sheet="P021_drum_plug.svg",
            notes="Concentricity of bore to OD becomes drum TIR directly. One setup, "
                  "two operations. Lightening holes optional.",
            evidence="DERIVED from ALN-01 TIR budget",
        ),
        _part(
            "P-022", "Way gib, tapered", 1,
            category="way", assembly="A-FRAME", make="MAKE",
            material="UHMW-PE",
            t=s.way_stock, w=s.way_width, l=s.side_depth,
            purchase='¾" × 2½" UHMW bar (H-014 stock / MC-14)',
            ref_face="Tapered face bears on the shoe",
            process="Taper 1:40 on a taper jig; three ¼-20 brass-tip adjusters",
            joinery="J-105 adjustable gib",
            handed="IDLER SIDE ONLY", viz="ways", sheet="P022_gib.svg",
            notes=f"Replaces the Rev B {0.020:.3f}″ sliding clearance with "
                  f"{s.gib_clearance:.4f}″ set clearance. Largest single term removed "
                  f"from the thickness budget (D-042).",
            evidence="DERIVED from CALC-C05",
        ),
        _part(
            "P-023", "Idler bearing micro-adjust plate", 1,
            category="precision", assembly="A-DRUM", make="MAKE",
            material="6061 aluminium plate or steel plate, ⅜″",
            t=0.375, w=4.0, l=8.0,
            ref_face="Bearing mounting face", ref_edge="Pivot axis",
            process="Drill the bearing pattern FROM THE BEARING, ream the pivot, "
                    "then tap nothing — the jack bears on a pad",
            joinery="J-105 pivot + jack; H-032 pin; H-030 jack screw",
            handed="IDLER SIDE ONLY", viz="shaft", sheet="P023_idler_plate.svg",
            notes=f"Pivot-to-jack {s.jack_arm_l1:g}″, pivot-to-bearing {s.jack_arm_l2:g}″ → "
                  f"{MECH_ADJ_AT_WORK * 1000:.2f} mil at the work per screw turn. "
                  f"3D-print at 1:1 before cutting metal (user standard).",
            evidence="DERIVED from CALC-C07",
        ),
        _part(
            "P-024", "Jack screw block", 1,
            category="precision", assembly="A-DRUM", make="MAKE",
            material="Steel or aluminium bar",
            t=0.75, w=1.25, l=2.0,
            process=f"Tap ¼-{s.jack_thread_tpi:g} through; chase the thread clean",
            joinery="J-105", handed="IDLER SIDE ONLY", viz="shaft",
            sheet="P024_jack_block.svg",
            notes="A ragged thread reads as backlash in the parallelism adjustment.",
        ),
        _part(
            "P-016", "Acme bronze nut block", 2,
            category="lift", assembly="A-TABLE", make="MAKE",
            material="Hardwood or aluminum + bronze nut",
            t=1.5, w=2.0, l=2.5,
            process="Bore for bronze nut; bolt to table underside",
            joinery="J-011 nut to table", handed="IDENTICAL", viz="elev",
            sheet="P016_nut_block.svg", evidence="ASSUMED block size; nut is BUY",
        ),
        _part(
            "P-017", "Table way shoe", 2,
            category="way", assembly="A-TABLE", make="MAKE",
            material="UHMW-PE or hardwood + UHMW liner",
            t=g.shoe_t, w=g.shoe_w, l=g.shoe_h,
            purchase='UHMW offcut or 5/4 hardwood, 2½" × 4"',
            process="Groove the outboard face to wrap the vertical tongue; bolt under the table edge",
            joinery="J-012 captured wrap on P-007; screws into table underside",
            handed="MIRROR PAIR", viz="ways", sheet="P017_table_shoe.svg",
            notes=(
                f"Groove {g.shoe_groove_depth:.3f}″ deep × {g.shoe_groove_width:.3f}″ wide captures the "
                f"{g.way_project:.3f}″ × {g.way_width:g}″ tongue. Table moves in Z only."
            ),
            evidence="DERIVED from way_project / way_width + clearance",
        ),
        _part(
            "P-018", "Acme thrust block", 2,
            category="lift", assembly="A-FRAME", make="MAKE",
            material="Baltic birch plywood or hardwood",
            t=g.thrust_h, w=g.thrust_w, l=g.thrust_l,
            process="Bore ⌀½″ through; counterbore for thrust washer; screw to P-002 on drum CL",
            joinery="J-013 screw to base; H-007 thrust",
            handed="IDENTICAL", viz="elev", sheet="P018_thrust_block.svg",
            notes="Takes axial load from the screw. Both blocks at Y = bearing_cl_y, left and right X.",
            evidence="ASSUMED block size; hole follows Acme OD",
        ),
        _part(
            "P-019", "Parallel home dog", 1,
            category="lift", assembly="A-TABLE", make="MAKE",
            material="Aluminum bar or hardwood",
            t=g.dog_h, w=g.dog_w, l=g.dog_l,
            process="Bolt to base beside the left screw; pin stops the left sprocket at last parallel",
            joinery="J-014 dog to P-002 / left clutch",
            handed="LEFT-HAND", viz="elev", sheet="P019_home_dog.svg",
            notes="Last known |A−B| home. Uncouple left for taper; recouple against this stop.",
            evidence="ASSUMED size; function is the stop, not the block",
        ),
    ]


def hardware(s: Spec = SPEC, g: Geom = GEOM) -> list[dict[str, Any]]:
    return [
        {"hardware_id": "H-001", "description": 'Mounted ball bearing, 1¼″ bore, self-aligning, FIXED (drive)', "standard": "2-bolt/4-bolt flange or pillow block", "size": '1¼" bore', "qty": 1, "make_or_buy": "BUY", "assembly": "A-DRUM", "mcmaster": "MC-03", "notes": f"Lock to P-001L. No axial float. REQUIRED C ≥ {MECH_C_REQUIRED:.0f} lbf (CALC-C11); self-align ≥ 0.011° (CALC-C08). Confirm both on the vendor page."},
        {"hardware_id": "H-002", "description": 'Mounted ball bearing, 1¼″ bore, self-aligning, FLOATING (idler)', "standard": "2-bolt/4-bolt flange or pillow block", "size": '1¼" bore', "qty": 1, "make_or_buy": "BUY", "assembly": "A-DRUM", "mcmaster": "MC-03", "notes": f"Mounts on P-023 micro-adjust plate. Axial float on a {s.idler_float_pad:g}″ UHMW pad (J-007). Never lock both bearings."},
        {"hardware_id": "H-003", "description": f'{s.pulley_motor_od:g}″ motor 4L pulley', "size": f'{s.pulley_motor_od:g}"', "qty": 1, "make_or_buy": "BUY", "assembly": "A-DRIVE"},
        {"hardware_id": "H-004", "description": f'{s.pulley_drum_od:g}″ drum 4L pulley', "size": f'{s.pulley_drum_od:g}"', "qty": 1, "make_or_buy": "BUY", "assembly": "A-DRIVE"},
        {"hardware_id": "H-005", "description": s.belt, "qty": 1, "make_or_buy": "BUY", "assembly": "A-DRIVE", "notes": "Size to measured center distance after cradle lock."},
        {"hardware_id": "H-006", "description": f'{s.motor_hp:g} HP {s.motor_rpm:g} RPM TEFC motor, 115 V', "qty": 1, "make_or_buy": "BUY", "assembly": "A-DRIVE", "notes": "Follow local electrical code."},
        {"hardware_id": "H-007", "description": '½″-10 Acme rod × 12″ + bronze nut + flange', "size": "½-10 × 12″", "thread": "½-10 Acme", "qty": 2, "make_or_buy": "BUY", "assembly": "A-TABLE"},
        {"hardware_id": "H-008", "description": "#25 chain + ½″-bore sprockets + master link + left clutch/dog", "qty": 1, "make_or_buy": "BUY", "assembly": "A-TABLE", "notes": "Couple screws; uncouple left for taper; home dog = last parallel."},
        {"hardware_id": "H-009", "description": f'Rubber roller ⌀{s.roller_od}" × ~{g.roller_len}"', "qty": 2, "make_or_buy": "BUY", "assembly": "A-TABLE"},
        {"hardware_id": "H-010", "description": '⅜″ drill rod / bolts × 17″ (roller axles)', "qty": 2, "make_or_buy": "BUY", "assembly": "A-TABLE"},
        {"hardware_id": "H-011", "description": "Light compression springs ~¾″ OD", "qty": 4, "make_or_buy": "BUY", "assembly": "A-TABLE", "notes": "Too stiff = snipe."},
        {"hardware_id": "H-012", "description": "Shoulder bolts 5/16 × 1½″", "qty": 4, "make_or_buy": "BUY", "assembly": "A-TABLE"},
        {"hardware_id": "H-013", "description": "Star knobs ⅜-16 + 1½″ studs + washers", "qty": 6, "make_or_buy": "BUY", "assembly": "A-TABLE", "notes": "Way locks and yokes."},
        {"hardware_id": "H-014", "description": "#8 × 1¼″ coarse cabinet screws", "qty": 100, "make_or_buy": "BUY", "assembly": "A-FRAME"},
        {"hardware_id": "H-015", "description": "#8 × 2″ coarse screws (sides into stretchers)", "qty": 50, "make_or_buy": "BUY", "assembly": "A-FRAME"},
        {"hardware_id": "H-016", "description": "¼-20 T-nuts + 1¼″ hex bolts + washers", "qty": 8, "make_or_buy": "BUY", "assembly": "A-DRIVE"},
        {"hardware_id": "H-017", "description": "5/16-18 × 1″ hex + nylock + washer (flange bearings)", "qty": 8, "make_or_buy": "BUY", "assembly": "A-DRUM", "notes": "Confirm flange hole."},
        {"hardware_id": "H-018", "description": "⅛″ piano wire", "qty": 1, "purchase": "12″", "make_or_buy": "BUY", "assembly": "A-DRUM", "notes": "Disc keys."},
        {"hardware_id": "H-019", "description": '4″ dust adapter + blast gate', "qty": 1, "make_or_buy": "BUY", "assembly": "A-HOOD"},
        {"hardware_id": "H-020", "description": "Switch box + 14/3 SJ cord + plug", "qty": 1, "make_or_buy": "BUY", "assembly": "A-DRIVE", "notes": "Code."},
        {"hardware_id": "H-021", "description": "Dial indicator 0.001″ + mag base", "qty": 1, "make_or_buy": "BUY", "assembly": "A-QA"},
        {"hardware_id": "H-022", "description": "Hook Velcro 4″ PSA + 3″ loop paper 80/120/180/220", "qty": 1, "make_or_buy": "BUY", "assembly": "A-DRUM"},
        {"hardware_id": "H-023", "description": "Titebond III + thin CA", "qty": 1, "make_or_buy": "BUY", "assembly": "A-FRAME"},
        {"hardware_id": "H-024", "description": "Paste wax (UHMW dry lube — no oil)", "qty": 1, "make_or_buy": "BUY", "assembly": "A-FRAME"},
        {"hardware_id": "H-025", "description": "Optional 60–90 RPM gearmotor + scotch yoke oscillator", "qty": 1, "make_or_buy": "BUY", "assembly": "A-OSC", "notes": "Optional. Not drum RPM."},
        {"hardware_id": "H-026", "description": "½″ thrust washer + e-clip (Acme lower end)", "qty": 2, "make_or_buy": "BUY", "assembly": "A-TABLE", "notes": "Under P-018. Sanding load tries to pull the screw up."},
        {"hardware_id": "H-027", "description": f'Aluminium round tube {s.shell_od:g}″ OD × {s.shell_wall:g}″ wall — drum shell stock', "size": f'{s.shell_od:g}" OD × {s.shell_wall:g}" wall × 18"', "qty": 1, "make_or_buy": "BUY", "assembly": "A-DRUM", "mcmaster": "MC-01", "notes": "Wall is a stiffness requirement (CALC-C02), not cosmetic. Becomes P-020."},
        {"hardware_id": "H-028", "description": 'Aluminium round bar 4½″ dia — drum end plug stock', "size": '4½" dia × 4"', "qty": 1, "make_or_buy": "BUY", "assembly": "A-DRUM", "mcmaster": "MC-04", "notes": "Becomes P-021 ×2. Turn OD and bore on one setup — concentricity here becomes drum TIR."},
        {"hardware_id": "H-029", "description": f'Clamping shaft collar, {s.shaft_od:g}″ bore', "qty": 4, "make_or_buy": "BUY", "assembly": "A-DRUM", "mcmaster": "MC-05", "notes": "Clamp type only. Set-screw collars mar the ground shaft."},
        {"hardware_id": "H-030", "description": '¼-28 socket head cap screw — parallelism jack', "size": '¼-28 × 1½"', "qty": 2, "make_or_buy": "BUY", "assembly": "A-DRUM", "mcmaster": "MC-06", "notes": "Fine thread is the requirement (CALC-C07). ¼-20 degrades resolution ~40%."},
        {"hardware_id": "H-031", "description": '¼-20 brass-tip set screw — gib adjusters', "qty": 6, "make_or_buy": "BUY", "assembly": "A-FRAME", "mcmaster": "MC-07", "notes": "Brass tip loads the gib without embedding. Bare steel brinells it and the setting drifts."},
        {"hardware_id": "H-032", "description": '⅜″ × 2″ hardened dowel pin — idler plate pivot', "qty": 2, "make_or_buy": "BUY", "assembly": "A-DRUM", "mcmaster": "MC-08", "notes": "Pivot must not wear oval or the parallelism setting walks."},
        {"hardware_id": "H-033", "description": 'Two-part structural epoxy for aluminium', "qty": 1, "make_or_buy": "BUY", "assembly": "A-DRUM", "mcmaster": "MC-22", "notes": "Read the data sheet for open time and cure. Cross-pin as well — never adhesive alone on a rotating part."},
        {"hardware_id": "H-034", "description": '¼-20 × 3″ hex bolt + nylock + backing washers — frame through-bolts', "qty": 12, "make_or_buy": "BUY", "assembly": "A-FRAME", "mcmaster": "MC-24", "notes": "D-048: screws alone are excluded by the user joinery standard. Re-check torque after the first hour (QC-19)."},
        {"hardware_id": "H-035", "description": 'Graduated handwheel, ½″ bore', "qty": 1, "make_or_buy": "BUY", "assembly": "A-TABLE", "mcmaster": "MC-13", "notes": f"{SPEC_HANDWHEEL_DIV} divisions → 0.0025″ per division (CALC-C10)."},
    ]


def joints(s: Spec = SPEC, g: Geom = GEOM) -> list[dict[str, Any]]:
    return [
        {
            "joint_id": "J-001",
            "joint_type": "housed dado + screw",
            "part_a": "P-001L / P-001R",
            "part_b": "P-003",
            "qty": 6,
            "location": "Inner faces; three stations IN-LO / OUT-LO / OUT-HI — rails stand on edge (¾″ in Y, 4″ in Z)",
            "dado_width": s.ply_actual,
            "dado_depth": s.stretcher_housing,
            "fit_class": "GLUE",
            "assembly_direction": "stretchers into dados, then through-screws from outside",
            "grain": "Plywood — no seasonal panel lock",
            "notes": "Racking triangle. Ways, not stretchers, locate the table. Stations miss the table envelope (CALC-004).",
            "stations": [f"{r['id']} Y {r['y0']:g}–{r['y1']:g} Z {r['z0']:g}–{r['z1']:g}" for r in stretcher_records(g)],
        },
        {
            "joint_id": "J-002",
            "joint_type": "rebate + bond",
            "part_a": "P-001L / P-001R",
            "part_b": "P-007",
            "qty": 2,
            "location": f"Inner face, vertical, Y {g.way_y0:g}–{g.way_y1:g}″ (drum CL ± {s.way_width/2:g}″), Z {g.way_z0:g}–{g.way_z1:g}″",
            "rebate_depth": g.way_rebate,
            "rebate_width": s.way_width,
            "rebate_height": g.way_len,
            "project": g.way_project,
            "fit_class": "GLUE",
            "constraint": "FIXED to side; table shoes SLIDE in Z",
            "notes": "Vertical captured way. Without the rebate a ¾″ way would steal 1.5″ and the 16″ table would not fit.",
        },
        {
            "joint_id": "J-003",
            "joint_type": "glue torsion box",
            "part_a": "P-004",
            "part_b": "P-005",
            "qty": 1,
            "fit_class": "GLUE",
            "notes": "Continuous glue. Flatten before J-004.",
        },
        {
            "joint_id": "J-004",
            "joint_type": "bonded wear face",
            "part_a": "P-004",
            "part_b": "P-006",
            "qty": 1,
            "fit_class": "GLUE",
            "constraint": "FIXED to box; box FLOATING in ways",
            "notes": "Replaceable metrology surface.",
        },
        {
            "joint_id": "J-005",
            "joint_type": "pack-bore + keyed stack",
            "part_a": "P-008 / P-009",
            "part_b": "P-010",
            "qty": 1,
            "bore": s.shaft_od,
            "key": s.key_wire_od,
            "fit_class": "LOCATIONAL / GLUE",
            "notes": "Bore as a pack. 1 mm relief every 4 MDF discs. Balance ends.",
        },
        {
            "joint_id": "J-006",
            "joint_type": "flange bearing, fixed",
            "part_a": "P-001L",
            "part_b": "H-001 / P-010",
            "fit_class": "LOCATIONAL",
            "constraint": "FIXED",
            "notes": "Drive-side axial lock. Datum for drum axis.",
        },
        {
            "joint_id": "J-007",
            "joint_type": "flange bearing, floating axial",
            "part_a": "P-001R",
            "part_b": "H-002 / P-010",
            "fit_class": "SLIDING (axial only)",
            "constraint": "FLOATING",
            "notes": (
                f"{s.idler_float_pad:g}″ UHMW pad under the flange. Bolts snug, not torqued. "
                "Do not slot the plywood in Y or Z — that lets the drum axis wander. Over-constraint bananas the shaft."
            ),
        },
        {
            "joint_id": "J-008",
            "joint_type": "pivoting T-nut cradle",
            "part_a": "P-012",
            "part_b": "H-016 / P-001L",
            "fit_class": "SNUG then LOCKED",
            "notes": "Gravity tension, then lock so the belt cannot pump.",
        },
        {
            "joint_id": "J-009",
            "joint_type": "spring yoke pivot",
            "part_a": "P-014",
            "part_b": "H-009 / H-011 / H-012",
            "fit_class": "CLEARANCE pivot, SPRING down",
            "notes": f"Set rollers {s.roller_setbelow:.3f}″ below drum OD, paper on.",
        },
        {
            "joint_id": "J-010",
            "joint_type": "screw base to sides",
            "part_a": "P-002",
            "part_b": "P-001L / P-001R",
            "fit_class": "GLUE + SCREW",
        },
        {
            "joint_id": "J-011",
            "joint_type": "bronze nut to table",
            "part_a": "P-016",
            "part_b": "P-004 / H-007",
            "fit_class": "LOCATIONAL",
            "notes": "Both nuts on the drum-CL screws; chain-coupled rotation. Cutting force goes through the nuts.",
        },
        {
            "joint_id": "J-105",
            "joint_type": "adjustable tapered gib + pivot plate",
            "part_a": "P-022 gib / P-023 idler plate",
            "part_b": "P-001R side / P-017 shoe",
            "qty": 1,
            "location": "Idler side only. Gib behind the shoe; plate pinned at the drum CL.",
            "taper": "1:40",
            "fit_class": "ADJUSTABLE SLIDING",
            "target_clearance": SPEC.gib_clearance,
            "adjusters": "3 × ¼-20 brass-tip (H-031)",
            "jack": f"¼-{SPEC.jack_thread_tpi:g} at L1 {SPEC.jack_arm_l1:g}″ / L2 {SPEC.jack_arm_l2:g}″",
            "resolution_at_work": MECH_ADJ_AT_WORK,
            "assembly_direction": "Taper wedges down: tightening closes clearance",
            "inspection": "QC-17 gib clearance; QC-15 ALN-01 after the jack is set",
            "notes": "Two adjustments that must not be confused: the GIB sets running "
                     "clearance (fit), the JACK sets drum parallelism (alignment). "
                     "Set the gib first and leave it alone while clocking ALN-01.",
        },
        {
            "joint_id": "J-106",
            "joint_type": "bonded + cross-pinned shell to plug to shaft",
            "part_a": "P-020 shell",
            "part_b": "P-021 plugs / P-010 shaft",
            "qty": 2,
            "location": f"Each end, plug seated {SPEC.plug_inset:g}″ inboard of the shell end",
            "bore": SPEC.shaft_od,
            "fit_class": "BONDED + PINNED (shell↔plug); CLAMPED (plug↔shaft)",
            "adhesive": "H-033 two-part structural epoxy for aluminium",
            "pins": "2 per plug, 90° apart, through the shell wall",
            "constraint": "Plugs axially located by H-029 clamp collars",
            "assembly_direction": "Plugs in from each end; shaft last, through both",
            "inspection": "QC-06 TIR after truing; QC-18 unbalance",
            "notes": "The pins carry torque; the epoxy seals and shares load. Never "
                     "adhesive alone on a rotating part. Bore and OD of the plug must "
                     "be cut in ONE lathe setup or the drum runs true at only one angle.",
        },
        {
            "joint_id": "J-012",
            "joint_type": "captured shoe wrap",
            "part_a": "P-017",
            "part_b": "P-007 / P-004",
            "qty": 2,
            "fit_class": "SLIDING (Z only)",
            "constraint": "FLOATING in Z, CAPTURED in X and Y",
            "groove_depth": g.shoe_groove_depth,
            "groove_width": g.shoe_groove_width,
            "notes": (
                f"Shoe hangs under the table edge and wraps the {g.way_project:.3f}″ tongue. "
                f"X play {g.shoe_groove_depth - g.way_project:.3f}″, Y play {g.shoe_groove_width - g.way_width:.3f}″ (CALC-005)."
            ),
        },
        {
            "joint_id": "J-013",
            "joint_type": "thrust block on base",
            "part_a": "P-018",
            "part_b": "P-002 / H-007",
            "qty": 2,
            "fit_class": "LOCATIONAL",
            "location": f"Y = {g.acme_y:g}″ (drum CL), X left/right",
            "notes": "Thrust washer + e-clip under the screw. Sanding load tries to pull the screw out of the base.",
        },
        {
            "joint_id": "J-014",
            "joint_type": "home dog stop",
            "part_a": "P-019",
            "part_b": "P-002 / H-008",
            "qty": 1,
            "fit_class": "ADJUSTABLE then LOCKED",
            "notes": "Set after paper-on |A−B|. Left clutch hits this stop to recover parallel.",
        },
    ]


def assemblies() -> list[dict[str, Any]]:
    return [
        {"assembly_id": "A-MASTER", "name": "WALTER DS-16", "children": ["A-FRAME", "A-DRUM", "A-DRIVE", "A-TABLE", "A-HOOD", "A-JIG"]},
        {"assembly_id": "A-FRAME", "name": "Box + ways", "parts": ["P-001L", "P-001R", "P-002", "P-003", "P-007", "P-018", "P-022"], "stage": "glue-up"},
        {"assembly_id": "A-DRUM", "name": "Drum + shaft + bearings", "parts": ["P-020", "P-021", "P-010", "P-023", "P-024", "H-001", "H-002", "H-029"], "alt_parts": ["P-008", "P-009", "P-015"], "note": "Option A shell baseline; Option B disc stack alternative (D-047)"},
        {"assembly_id": "A-DRIVE", "name": "Motor + pulleys", "parts": ["P-012", "H-003", "H-004", "H-005", "H-006"]},
        {"assembly_id": "A-TABLE", "name": "Table + lift + hold-downs", "parts": ["P-004", "P-005", "P-006", "P-014", "P-016", "P-017", "P-019", "H-007", "H-008", "H-009"]},
        {"assembly_id": "A-HOOD", "name": "Dust hood", "parts": ["P-011", "H-019"]},
        {"assembly_id": "A-JIG", "name": "Truing sled + pack-bore jig", "parts": ["P-013", "P-015"]},
        {"assembly_id": "A-QA", "name": "Metrology", "parts": ["H-021"]},
        {"assembly_id": "A-OSC", "name": "Optional oscillator", "parts": ["H-025"]},
    ]


def operations(s: Spec = SPEC, g: Geom = GEOM) -> list[dict[str, Any]]:
    return [
        {"op": "S-001", "title": "Stop: side height", "tool": "Track saw / table saw + stop", "setting": f'{s.side_height:g}"', "parts": ["P-001L", "P-001R"], "rule": "DO NOT MOVE STOP"},
        {"op": "S-002", "title": "Stop: side depth", "tool": "Same", "setting": f'{s.side_depth:g}"', "parts": ["P-001L", "P-001R"], "rule": "DO NOT MOVE STOP"},
        {"op": "S-003", "title": "Stop: stretcher length (housed)", "tool": "Miter gauge + stop", "setting": f'{g.stretcher_length:g}"', "parts": ["P-003 ×3"], "rule": "DO NOT MOVE STOP until all three are cut"},
        {"op": "S-004", "title": "Stop: stretcher width", "tool": "Rip fence", "setting": f'{s.stretcher_height:g}"', "parts": ["P-003 ×3"]},
        {"op": "S-005", "title": "Stop: table skins", "tool": "Fence + stop", "setting": f'{g.table_width:g}" × {g.table_depth:g}"', "parts": ["P-004 ×2"]},
        {"op": "S-006", "title": "Dado: stretcher housing", "tool": "Dado / router", "setting": f'depth {s.stretcher_housing:g}" · width {s.ply_actual:g}" · height {s.stretcher_height:g}"', "parts": ["P-001L", "P-001R"], "ref": "Inner face. Three stations IN-LO / OUT-LO / OUT-HI. Datum Y0 = infeed."},
        {"op": "S-007", "title": "Rebate: vertical way", "tool": "Router + edge guide", "setting": f'depth {g.way_rebate:.3f}" · width {s.way_width:g}" · Z {g.way_z0:g}–{g.way_z1:g}"', "parts": ["P-001L", "P-001R"], "ref": "Inner face. Centered on drum CL."},
        {"op": "S-008", "title": "Stack-drill bearing CL", "tool": "Drill press, sides clamped face-to-face", "setting": f'Y {g.bearing_cl_y:g}" from infeed · Z {g.bearing_cl_z:g}" from bottom', "parts": ["P-001L+R"], "rule": "One stack. Then split for inner-face dados."},
        {"op": "S-009", "title": "Pack-bore discs", "tool": "P-015 jig + drill/ream", "setting": f'⌀{s.shaft_od:g}"', "parts": ["P-008", "P-009"]},
        {"op": "S-010", "title": "True drum", "tool": "P-013 sled on ways", "setting": f'TIR ≤ {s.drum_tir:.3f}"', "parts": ["A-DRUM"]},
        {"op": "S-011", "title": "ALN-01 clock", "tool": "H-021 indicator + P-023 jack", "setting": f'|A−B| ≤ {s.aln_spec:.3f}" paper on, no load', "parts": ["A-TABLE", "A-DRUM"], "rule": "Set the gib FIRST and leave it. Then clock with the jack only."},
        {"op": "S-012", "title": "Turn plug OD + bore", "tool": "Metal lathe", "setting": f'OD to shell ID · bore ⌀{s.shaft_od:g}"', "parts": ["P-021"], "rule": "ONE SETUP — do not re-chuck between OD and bore."},
        {"op": "S-013", "title": "Taper the gib", "tool": "Taper jig", "setting": "1:40", "parts": ["P-022"]},
        {"op": "S-014", "title": "Set gib clearance", "tool": "Brass-tip adjusters + feelers", "setting": f'{s.gib_clearance:.4f}"', "parts": ["P-022"], "rule": "No rock, no bind, through FULL travel."},
        {"op": "S-015", "title": "TV-01 witness board", "tool": "Calipers", "setting": f'spread ≤ {s.tv_spec:.3f}" across {s.capacity_width:g}"', "parts": ["A-MASTER"], "rule": "Finish pass only. Different number from ALN-01."},
    ]


def inspection(s: Spec = SPEC, g: Geom = GEOM) -> list[dict[str, Any]]:
    return [
        {"qc": "QC-01", "check": "Ply thickness", "spec": f"Measure ply_actual (default {s.ply_actual:g}\"). Keep inner span {s.clear_between_sides:g}″.", "class": "T1", "gate": "M0"},
        {"qc": "QC-02", "check": "Paired sides", "spec": "P-001L/R identical hole pattern after stack-drill", "class": "T2", "gate": "M4"},
        {"qc": "QC-03", "check": "Box diagonals", "spec": "Base diagonals equal; no rack", "class": "T2", "gate": "M5"},
        {"qc": "QC-04", "check": "Way plumb + capture", "spec": "Both vertical ways plumb and coplanar in X; shoes wrap without bind through full travel", "class": "T3", "gate": "M5"},
        {"qc": "QC-05", "check": "Table flatness", "spec": f"≤ {s.table_flat_tol:.3f}″ on both diagonals of P-006", "class": "T3", "gate": "M7"},
        {"qc": "QC-06", "check": "Drum TIR paper off", "spec": f"≤ {s.drum_tir:.3f}″ mid-span", "class": "T4", "gate": "M7"},
        {"qc": "QC-07", "check": "Drum ∥ table paper on (alias of QC-15)", "spec": f"Use QC-15 ALN-01. |A−B| ≤ {s.aln_spec:.3f}″ over {s.capacity_width:g}″, no load.", "class": "T4", "gate": "M7"},
        {"qc": "QC-08", "check": "Hold-down set", "spec": f"Rollers {s.roller_setbelow:.3f}″ below drum OD, paper on", "class": "T2", "gate": "M7"},
        {"qc": "QC-09", "check": "Pulley coplanar", "spec": "Straightedge across both pulley faces", "class": "T2", "gate": "M5"},
        {"qc": "QC-10", "check": "Thickness scatter (alias of QC-16)", "spec": f"Use QC-16 TV-01. Witness-board spread ≤ {s.tv_spec:.3f}″.", "class": "T4", "gate": "M7"},
        {"qc": "QC-11", "check": "Idler float", "spec": "Shaft can grow axially; no banana preload", "class": "T2", "gate": "M3"},
        {"qc": "QC-12", "check": "Way/table capture", "spec": f"Shoes wrap tongue; project {g.way_project:.3f}″; X play {g.shoe_groove_depth - g.way_project:.3f}″; table moves in Z only", "class": "T2", "gate": "M4"},
        {"qc": "QC-13", "check": "Stretcher clearance", "spec": f"No rail in the table envelope; min Z gap {g.min_stretcher_table_clear:.3f}″ (CALC-004)", "class": "T2", "gate": "M5"},
        {"qc": "QC-14", "check": "Acme on drum CL", "spec": f"Both screws at Y {g.acme_y:g}″; |left−right| travel match through 3″", "class": "T3", "gate": "M7"},
        {"qc": "QC-15", "check": "ALN-01 alignment, NO LOAD", "spec": f"Indicator at station A (drive) and B (idler), drum stopped, paper on, no workpiece: |A−B| ≤ {s.aln_spec:.3f}″ over {s.capacity_width:g}″. Set with the P-023 jack.", "class": "T4", "gate": "M7"},
        {"qc": "QC-16", "check": "TV-01 delivered thickness variation", "spec": f"Witness board {s.capacity_width:g}″ wide, finish pass: caliper 4 corners + centre, spread ≤ {s.tv_spec:.3f}″. This is the user-facing number, NOT the same as QC-15.", "class": "T4", "gate": "M8"},
        {"qc": "QC-17", "check": "Gib running clearance", "spec": f"Set gib to {s.gib_clearance:.4f}″: table slides by hand through full travel with no perceptible rock at either end. Record the feeler used.", "class": "T3", "gate": "M5"},
        {"qc": "QC-18", "check": "Drum residual unbalance", "spec": f"Knife-edge test: drum comes to rest in a random position over 5 releases. Allowance U ≤ {MECH_UNBALANCE_OZIN:.2f} oz·in (CALC-C13).", "class": "T3", "gate": "M6"},
        {"qc": "QC-19", "check": "Frame bolt re-torque", "spec": "Re-check all H-034 through-bolts after the first hour of running. Wood relaxes; a loose frame reads as taper.", "class": "T2", "gate": "M9"},
        {"qc": "QC-20", "check": "Collector delivers CFM", "spec": f"Measured or vendor-curve airflow ≥ {MECH_CFM:.0f} CFM at the machine (CALC-C15). A shop vacuum will not meet this.", "class": "T2", "gate": "M8"},
    ]


def decisions() -> list[dict[str, str]]:
    return [
        {"id": "D-001", "decision": "Delete conveyor; solid sliding table", "reason": "Walters: conveyor is the failure point", "rev": "A"},
        {"id": "D-002", "decision": "Keep 16.5″ inner span even if ply is 18 mm", "reason": "Capacity and drum length are the constraint, not outer width", "rev": "B"},
        {"id": "D-003", "decision": "Dual ½-10 Acme + chain + left clutch/home dog", "reason": "One screw cannot hold coplanarity after paper wrap", "rev": "B"},
        {"id": "D-004", "decision": "Fixed drive bearing, floating idler", "reason": "Two locked flanges banana the shaft", "rev": "B"},
        {"id": "D-020", "decision": "UHMW let into a rebate; project only ~0.23″", "reason": "¾″ proud ways steal 1.5″ and a 16″ table cannot enter a 16.5″ span", "rev": "B.1", "affected": "P-001L/R, P-007, table_width equation"},
        {"id": "D-021", "decision": "¼″ housed stretchers, not butt joints", "reason": "Racking stiffness without using stretchers as the table datum", "rev": "B.1", "affected": "P-003 length, J-001, S-003"},
        {"id": "D-022", "decision": "Persistent part IDs P/H/J/A; Python is SSOT", "reason": "Drawings, BOM, viewer, and OpenSCAD were duplicating 16.5 / 14 / 18.5", "rev": "B.1"},
        {"id": "D-023", "decision": "Wandel-style individual part, assembly, and hardware sheets", "reason": "Overview D-sheets are not enough to fabricate P-001 from; each make part needs its own isometric + hole chart + callouts", "rev": "B.2", "affected": "plans/P*.svg, A*.svg, H01, IDX"},
        {"id": "D-024", "decision": "Idler float is an axial pad, not YZ slots in the side panel", "reason": "Face-plane slots let the drum axis wander; shaft growth is through the bearing", "rev": "B.2", "affected": "J-007, H-002, P-001R"},
        {"id": "D-025", "decision": "Master build guide: release state on every sheet, ballooned explosion, numbered step sheets with parts trays", "reason": "A builder should follow numbered steps with per-step parts and QC gates, not reverse-engineer the order from overview sheets", "rev": "B.3", "affected": "G-001…G-004, E-101, ST-01…ST-14, Q-101"},
        {"id": "D-027", "decision": "Vertical captured UHMW ways; table is a lifting carriage", "reason": "Horizontal ways at Z=10 never supported the table at operating height (11.5–15.9″). Capture in X/Y, Acme in Z.", "rev": "B.4", "affected": "P-007, P-017, J-002, J-012"},
        {"id": "D-028", "decision": "Three stretcher stations IN-LO / OUT-LO / OUT-HI, rails on edge", "reason": "A stretcher at Z=12 occupied the same volume as a 3″-open table. Triangle in the YZ plane fights racking without crossing the table.", "rev": "B.4", "affected": "P-001, P-003, J-001"},
        {"id": "D-029", "decision": "Both Acme screws on the drum centerline (left/right X, one Y)", "reason": "Infeed/outfeed Y put the nuts off the cutting-force line and the 3D model only drew two screws at one Y anyway. Force through the nuts; chain couples them.", "rev": "B.4", "affected": "P-016, P-018, P-019, H-007, H-008"},
        {"id": "D-030", "decision": "Layout protocol is HYBRID: face/edge on panels, centerline on drum/Acme/ways", "reason": "Planforge centerline protocol. Mixing a face measurement with a CL measurement without converting is how the drum axis drifts.", "rev": "B.4", "affected": "G-002, A-01, M-101"},
    ] + mech_decisions()


def revisions() -> list[dict[str, str]]:
    return [
        {"rev": "A", "note": "Solid sliding table, no conveyor, adjustable idler, precision shaft"},
        {"rev": "B", "note": "Dual-end lift, UHMW ways, hold-downs, floating bearing, paper-on A/B ±0.003″"},
        {"rev": "B.1", "note": "Fabrication model: part/joint IDs, housed stretchers, way rebate so table fits, derived geometry, JSON/CSV SSOT"},
        {"rev": "B.2", "note": "Individual Wandel-style part/assembly/hardware sheets; named hole patterns; idler axial pad (not YZ slots)"},
        {"rev": "B.3", "note": "Master build guide book: G-001…G-004 design basis, E-101 ballooned explosion, ST-01…ST-14 step sheets with parts trays, Q-101 commissioning"},
        {"rev": "B.4", "note": "Mechanics: vertical captured ways, stretcher stations clear of the table, both Acme screws on the drum CL, P-017 shoes / P-018 thrust / P-019 home dog, Planforge J/M/F/S sheets, validate_mechanics()"},
        {"rev": "C", "note": "Precision rebuild. Rev B's ¾″ shaft failed its own accuracy spec at 4.25 lbf (CALC-C01), and one 0.003″ figure was being used for two different quantities. Rev C: 1¼″ shaft + structural aluminium shell (21× stiffer), adjustable gib, parallelism micro-adjust plate, bearings specified by required dynamic capacity, spec split into ALN-01 and TV-01, frame through-bolted, 18-step build with an Option B drum, McMaster procurement register."},
    ]


def datums(s: Spec = SPEC, g: Geom = GEOM) -> list[dict[str, str]]:
    return [
        {"id": "DATUM-A", "on": "P-001L/R", "what": "Bottom edge", "use": "Z = 0 floor / base top after install"},
        {"id": "DATUM-B", "on": "P-001L/R", "what": "Infeed edge", "use": "Y = 0; bearing_cl_y measured from here"},
        {"id": "DATUM-C", "on": "P-001L/R", "what": "Inner face", "use": "X local; dados and way rebate"},
        {"id": "DATUM-D", "on": "P-006", "what": "Wear-face top", "use": "Table plane; A/B indicator reference"},
        {"id": "DATUM-E", "on": "P-010", "what": "Drum axis", "use": "Fixed by H-001; TIR and parallel"},
        {"id": "DATUM-F", "on": "P-023", "what": "Idler pivot pin axis", "use": "Rotation centre for the parallelism micro-adjust. ALN-01 is set about this line."},
    ]


# ---------------------------------------------------------------------------
# 3. Shop lists (derived from registry — do not independently hard-code sizes)
# ---------------------------------------------------------------------------

def quality_targets() -> list[dict[str, str]]:
    s, g = SPEC, GEOM
    return [
        {"check": "Table flatness", "tool": "Straightedge + feelers on wear face", "spec": f"≤ {s.table_flat_tol:.3f}″ on both diagonals", "qc": "QC-05"},
        {"check": "Drum TIR (paper off)", "tool": "Dial indicator on drum OD, mid-span", "spec": f"≤ {s.drum_tir:.3f}″ TIR", "qc": "QC-06"},
        {"check": "ALN-01 no-load alignment", "tool": "Indicator at A (drive) and B (idler), paper on, no workpiece", "spec": f"|A−B| ≤ {s.aln_spec:.3f}″ over {s.capacity_width}″ (QC-15)", "qc": "QC-15"},
        {"check": "Way plumb + capture", "tool": "Square + indicator on both UHMW; table through travel", "spec": "Plumb; shoes wrap; no twist", "qc": "QC-04"},
        {"check": "Pulley coplanar", "tool": "Straightedge across both pulley faces", "spec": "Faces flush; belt tracks center", "qc": "QC-09"},
        {"check": "Hold-down set", "tool": "Feeler under roller vs drum (paper on)", "spec": f"Rollers {s.roller_setbelow:.3f}″ below drum OD", "qc": "QC-08"},
        {"check": "TV-01 delivered thickness variation", "tool": "Caliper 4 corners + centre of witness board", "spec": f"≤ {s.tv_spec:.3f}″ after finish pass (QC-16)", "qc": "QC-16"},
    ]


def pass_schedule() -> list[dict[str, str]]:
    s = SPEC
    return [
        {"grit": "80", "depth": f"{s.pass_rough:.3f}″", "use": "Flatten / mill marks / glue"},
        {"grit": "120", "depth": f"{s.pass_medium:.3f}″", "use": "Thickness to +0.008″ of final"},
        {"grit": "180", "depth": f"{s.pass_finish:.3f}″", "use": "Finish pass; optional 90° cross"},
        {"grit": "220", "depth": f"{s.pass_finish:.3f}″", "use": "Veneer / figured maple — hold-downs on"},
    ]


def cut_list() -> list[dict[str, Any]]:
    """Finished cut list from the part register (MAKE + BUY-CUT)."""
    rows = []
    for p in parts():
        if p["make_or_buy"] not in ("MAKE", "BUY-CUT"):
            continue
        rows.append({
            "part_id": p["part_id"],
            "qty": p["qty"],
            "size": p["finished_size"],
            "size_mm": p["finished_size_mm"],
            "stock": p["material"],
            "use": p["part_name"] + (f" — {p['notes'][:48]}" if p["notes"] else ""),
            "rough": p["rough_size"],
            "handed": p["handed"],
        })
    return rows


def lumberyard() -> list[dict[str, str]]:
    return [
        {"where": "Plywood", "item": "¾″ Baltic birch (18 mm Euro BB is the usual substitute)", "qty": "2 sheets 5′×5′", "alt": "One 4′×8′ + one 5′×5′ if that’s what is stocked", "use": "P-001L/R, P-002, P-003, P-004, P-012, P-014"},
        {"where": "MDF", "item": "¾″ MDF", "qty": "24″ × 48″", "alt": "Half a 4′×8′ sheet", "use": "P-008 ×19 + P-015 + P-005 if no ½″ offcuts"},
        {"where": "Plywood", "item": "¼″ birch or pine ply", "qty": "24″ × 24″", "alt": "Door-skin offcut is enough", "use": "P-011 hood blank"},
        {"where": "Plastics / order", "item": "½″ phenolic or ⅜″ MIC-6 / cast tooling plate", "qty": "16″ × 22″", "alt": "UHMW sheet if phenolic is a wait", "use": "P-006 wear face — metrology surface"},
        {"where": "Plastics", "item": "UHMW bar ¾″ × 2½″", "qty": "12″", "alt": "Two 6″ offcuts + a shoe blank", "use": "P-007 vertical ways + P-017 shoes"},
        {"where": "Hardwood / metal", "item": "Hardwood ¾″ or 1½″ aluminum angle", "qty": "36″", "alt": "BB offcuts from sheet 2", "use": "P-014 yokes"},
        {"where": "Abrasives", "item": "Hook Velcro 4″ PSA + 3″ loop paper 80/120/180/220", "qty": "1 roll + 4 grits", "alt": "PSA paper if you skip Velcro (harder to change)", "use": "H-022 spiral wrap after truing"},
        {"where": "Glue", "item": "Titebond III + thin CA", "qty": "1 qt + 1 oz", "alt": "Any Type I PVA for the box", "use": "H-023 torsion box, drum, Velcro edges"},
    ]


def fastener_schedule() -> list[dict[str, str]]:
    mapping = [
        ("H-014", "Screws"), ("H-015", "Screws"), ("H-016", "Fasteners"), ("H-017", "Fasteners"),
        ("H-013", "Knobs"), ("H-012", "Fasteners"), ("H-011", "Springs"), ("H-010", "Rod"),
        ("H-018", "Wire"), ("H-024", "Wax"), ("H-019", "Dust"), ("H-020", "Electrical"),
        ("H-001", "Specialty"), ("H-002", "Specialty"),
    ]
    hw = {h["hardware_id"]: h for h in hardware()}
    extra = [
        {"aisle": "Specialty", "item": "¾″ TG&P / precision-ground shaft × 24″", "qty": "1", "use": "P-010 drum shaft (cut to 22.5″)"},
        {"aisle": "Specialty", "item": "½-10 Acme rod 12″ + bronze nut + flange", "qty": "2", "use": "H-007 dual table lift"},
        {"aisle": "Specialty", "item": "#25 chain + ½″-bore sprockets + master + left clutch/dog", "qty": "1 kit", "use": "H-008 couple screws; taper uncouple"},
        {"aisle": "Specialty", "item": "3″ + 5″ 4L pulleys + A-section belt", "qty": "1 set", "use": "H-003/H-004/H-005 coplanar 3:5"},
        {"aisle": "Specialty", "item": "½ HP 1725 RPM TEFC 115 V", "qty": "1", "use": "H-006 drum drive"},
        {"aisle": "Specialty", "item": "Dial indicator 0.001″ + mag base", "qty": "1", "use": "H-021 TIR and A/B clock"},
        {"aisle": "Specialty", "item": "Rubber rollers ⌀1.25″ × ~15.75″", "qty": "2", "use": "H-009 hold-downs"},
        {"aisle": "Optional", "item": "60–90 RPM gearmotor + scotch yoke", "qty": "1 kit", "use": "H-025 ⅛″ slow oscillator"},
    ]
    rows = []
    for hid, aisle in mapping:
        h = hw[hid]
        rows.append({"aisle": aisle, "item": h["description"], "qty": str(h.get("qty", "")), "use": h.get("notes") or h["hardware_id"]})
    # H-001 and H-002 both mapped — collapse bearings into one shop line
    rows = [r for r in rows if "FLOATING" not in r["item"]]
    rows.append({"aisle": "Specialty", "item": "4-bolt flange bearing ¾″ bore, sealed", "qty": "2", "use": "H-001 FIXED · H-002 FLOATING"})
    rows.extend(extra)
    return rows


def nest_sheets() -> list[dict[str, Any]]:
    s, g = SPEC, GEOM
    k = s.kerf
    return [
        {
            "name": "Sheet 1 — 5′×5′ × ¾″ BB (frame)",
            "sheet_w": 60.0,
            "sheet_h": 60.0,
            "parts": [
                {"part_id": "P-001L", "label": "P-001L", "x": 0.25, "y": 0.25, "w": s.side_depth, "h": s.side_height},
                {"part_id": "P-001R", "label": "P-001R", "x": 0.25 + s.side_depth + k, "y": 0.25, "w": s.side_depth, "h": s.side_height},
                {"part_id": "P-002", "label": "P-002", "x": 0.25, "y": 0.25 + s.side_height + k, "w": g.base_width, "h": g.base_depth},
                {"part_id": "P-003", "label": "P-003a", "x": 0.25 + g.base_width + k, "y": 0.25 + s.side_height + k, "w": g.stretcher_length, "h": s.stretcher_height},
                {"part_id": "P-003", "label": "P-003b", "x": 0.25 + g.base_width + k, "y": 0.25 + s.side_height + k + s.stretcher_height + k, "w": g.stretcher_length, "h": s.stretcher_height},
                {"part_id": "P-003", "label": "P-003c", "x": 0.25 + g.base_width + k, "y": 0.25 + s.side_height + k + 2 * (s.stretcher_height + k), "w": g.stretcher_length, "h": s.stretcher_height},
                {"part_id": "P-012", "label": "P-012", "x": 0.25 + g.base_width + k, "y": 0.25 + s.side_height + k + 3 * (s.stretcher_height + k), "w": s.cradle_w, "h": s.cradle_h},
            ],
            "note": "Stack-drill P-001L/R as a pair after cut. Then dado inner faces (mirror).",
        },
        {
            "name": "Sheet 2 — 5′×5′ × ¾″ BB (table & jigs)",
            "sheet_w": 60.0,
            "sheet_h": 60.0,
            "parts": [
                {"part_id": "P-004", "label": "P-004A", "x": 0.25, "y": 0.25, "w": g.table_width, "h": g.table_depth},
                {"part_id": "P-004", "label": "P-004B", "x": 0.25 + g.table_width + k, "y": 0.25, "w": g.table_width, "h": g.table_depth},
                {"part_id": "P-013", "label": "P-013", "x": 0.25, "y": 0.25 + g.table_depth + k, "w": g.table_width, "h": s.sled_depth},
                {"part_id": "P-014", "label": "P-014a", "x": 0.25 + g.table_width + k, "y": 0.25 + g.table_depth + k, "w": s.yoke_length, "h": s.yoke_width},
                {"part_id": "P-014", "label": "P-014b", "x": 0.25 + g.table_width + k, "y": 0.25 + g.table_depth + k + s.yoke_width + k, "w": s.yoke_length, "h": s.yoke_width},
                {"part_id": "P-015", "label": "P-015", "x": 0.25, "y": 0.25 + g.table_depth + k + s.sled_depth + k, "w": s.bore_jig, "h": s.bore_jig},
            ],
            "note": "P-005 ribs are ½″ stock. Leftover ¾″ is insurance.",
        },
        {
            "name": "Sheet 3 — 24″×48″ × ¾″ MDF (discs)",
            "sheet_w": 24.0,
            "sheet_h": 48.0,
            "parts": [
                {"part_id": "P-008" if i < s.disc_count_core else "P-009", "label": f"D{i + 1}", "x": (i % 4) * 6.0 + 0.2, "y": (i // 4) * 6.0 + 0.2, "w": 5.5, "h": 5.5}
                for i in range(g.disc_count)
            ],
            "note": "Bandsaw oversize ⌀5⅛″, pack-bore. Two end discs preferably BB (P-009) from sheet-2 leftover.",
        },
    ]


def nest_yield() -> list[dict[str, Any]]:
    rows = []
    for sheet in nest_sheets():
        area = sheet["sheet_w"] * sheet["sheet_h"]
        used = sum(p["w"] * p["h"] for p in sheet["parts"])
        rows.append({
            "sheet": sheet["name"],
            "area_in2": area,
            "used_in2": round(used, 1),
            "yield_pct": round(100 * used / area, 1),
            "waste_pct": round(100 * (1 - used / area), 1),
            "part_count": len(sheet["parts"]),
        })
    return rows


def hardware_bom() -> list[dict[str, str]]:
    """Compact specialty list for D-6 (purchased)."""
    return [
        {"item": h["description"], "qty": str(h.get("qty", 1)), "id": h["hardware_id"]}
        for h in hardware()
        if h["hardware_id"] in ("H-001", "H-002", "H-003", "H-004", "H-005", "H-006", "H-007", "H-008", "H-009", "H-021", "H-025")
    ]


def assembly_phases() -> list[dict[str, str]]:
    return [
        {"id": "a1", "phase": "frame", "title": "Template & stack-drill sides",
         "body": f"Clamp P-001L/R face-to-face. Drill bearing CL at Y {GEOM.bearing_cl_y:g}″ / Z {GEOM.bearing_cl_z:g}″, Acme holes, indicator pad as one stack (S-008)."},
        {"id": "a2", "phase": "frame", "title": "Dados, vertical way rebates, box + UHMW",
         "body": f"Split the pair. Dado J-001 stations IN-LO/OUT-LO/OUT-HI and rebate vertical J-002 ({GEOM.way_rebate:.3f}″) on inner faces only. Glue P-003, square diagonals, bond P-007."},
        {"id": "a3", "phase": "drum", "title": "Option A shell (baseline) or Option B discs",
         "body": f"Option A: turn P-021 plugs in one setup, bond+pin into P-020 (J-106). Option B: bandsaw P-008/P-009, pack-bore ⌀{SPEC.shaft_od:g}″ in P-015 (J-005). True in the machine's own bearings."},
        {"id": "a4", "phase": "drum", "title": "Fixed drive bearing, floating idler on micro-adjust plate",
         "body": "H-001 locked on P-001L (J-006). H-002 on P-023 jack plate (J-105 / J-007). Transfer the purchased flange BCD. Do not lock both bearings."},
        {"id": "a5", "phase": "drive", "title": "Motor cradle, coplanar pulleys, lock",
         "body": "Straightedge across H-003/H-004. Gravity tension, lock P-012 (J-008)."},
        {"id": "a6", "phase": "table", "title": "Torsion-box table + wear face + shoes",
         "body": f"P-004 + P-005 @ {SPEC.table_rib_oc:g}″ o.c., glue. Flatten. Bond P-006. Fit P-017 shoes. Diagonals ≤ {SPEC.table_flat_tol:.3f}″."},
        {"id": "a7", "phase": "table", "title": "Dual Acme lift on drum CL + chain couple",
         "body": "P-018 thrust on base, P-016 nuts, both screws at drum CL Y. H-008 chain. Left clutch + P-019 home dog. Table rises in Z; shoes stay wrapped."},
        {"id": "a8", "phase": "table", "title": "Hold-down roller yokes",
         "body": f"P-014 + H-009. Set {SPEC.roller_setbelow:.3f}″ below drum OD, paper on. Too much spring = snipe."},
        {"id": "a9", "phase": "hood", "title": "Kerf-bend dust hood",
         "body": "P-011 kerf, wet, glue, fill. H-019 4″ port. Clear oscillator stroke if fitted."},
        {"id": "a10", "phase": "wrap", "title": "True drum on full-width sled",
         "body": f"P-013 abrasive face-up on the ways. TIR ≤ {SPEC.drum_tir:.3f}″. Then H-022 Velcro + spiral paper."},
        {"id": "a11", "phase": "tune", "title": "Indicator clock A/B — parallel home",
         "body": f"Paper on. |A−B| ≤ {SPEC.parallel_tol:.3f}″. Lock home dog. Record the reading."},
        {"id": "a12", "phase": "tune", "title": "Test panel + pass schedule",
         "body": "80 / 120 / 180. Caliper four corners. If scatter > 0.003″, re-clock. Finish at 0.001″."},
    ]


def build_steps(s: Spec = SPEC, g: Geom = GEOM) -> list[dict[str, Any]]:
    """Numbered build steps for the master guide book.

    Each step is one sitting: what to put on the bench (parts tray), what to
    do, what must be true before the glue cures (QC gate), and what is still
    correctable afterwards. `shows` names the viz groups drawn in that step's
    illustration; `adds` is the subset that is new work, drawn in colour while
    everything already built is ghosted grey.
    """
    steps: list[dict[str, Any]] = [
        {
            "step": 1,
            "chapter": "01 Stock",
            "title": "Buy, acclimate, and measure the plywood",
            "goal": "Know your real ply thickness before a single dado is cut.",
            "parts": [],
            "hardware": [],
            "tools": ["Calipers", "Moisture meter (optional)", "Flat floor"],
            "sheets": ["D-10", "IDX"],
            "actions": [
                "Stand the sheets on edge in the shop for at least 48 hours. Euro BB arrives at 18 mm, not ¾″.",
                f"Caliper the ply in six places. Record the number as ply_actual (model default {s.ply_actual:g}″).",
                f"If it is not {s.ply_actual:g}″, edit ply_actual in cad/walter_ds16.py and regenerate every sheet. Do not shave the {s.clear_between_sides:g}″ inner span to make the old numbers work.",
            ],
            "qc": "QC-01",
            "gate": f"Measured ply thickness recorded. Inner span stays {s.clear_between_sides:g}″ (419 mm).",
            "hold": "Nothing is cut yet. This is the cheapest place to catch the 18 mm surprise.",
            "warn": "",
            "shows": [],
            "adds": [],
            "correctable": "Everything.",
        },
        {
            "step": 2,
            "chapter": "02 Breakdown",
            "title": "Rough-cut the panels oversize",
            "goal": "Flat, labelled, manageable blanks out of full sheets.",
            "parts": ["P-001L", "P-001R", "P-002", "P-003", "P-004"],
            "hardware": [],
            "tools": ["Track saw or table saw", "Straightedge", "Sawhorses"],
            "sheets": ["D-6", "D-10"],
            "actions": [
                "Cut every panel about ⅛″ over width and ¼″ over length. Final size comes off one stop later.",
                "Write the part ID on each blank in pencil the moment it leaves the sheet.",
                "Keep the two side blanks as a matched pair — they get drilled together in ST-04.",
            ],
            "qc": "",
            "gate": "All blanks labelled, oversize, and stacked flat.",
            "hold": "",
            "warn": "Full sheets are heavy and awkward. Support the offcut so it cannot drop onto the blade or onto you.",
            "shows": [],
            "adds": [],
            "correctable": "Sizes — everything is still oversize.",
        },
        {
            "step": 3,
            "chapter": "03 Sides",
            "title": "Cut both sides to final size on one stop",
            "goal": "Two panels that ARE the same size, not two panels that measure the same.",
            "parts": ["P-001L", "P-001R"],
            "hardware": [],
            "tools": ["Table saw + stop block", "Framing square"],
            "sheets": ["P-001L", "P-001R", "D-12"],
            "actions": [
                f"Set the stop for {s.side_height:g}″ and cut both panels (S-001). Do not move the stop between cuts.",
                f"Reset for {s.side_depth:g}″ depth and cut both (S-002).",
                "Mark the INNER face and the INFEED edge on each panel. Those two marks are Datum C and Datum B for the rest of the build.",
            ],
            "qc": "QC-02",
            "gate": "Panels identical within a pencil line; inner face and infeed edge marked on both.",
            "hold": "",
            "warn": "",
            "shows": ["sides"],
            "adds": ["sides"],
            "correctable": "Nothing about panel size after this — the drum and table depend on it.",
        },
        {
            "step": 4,
            "chapter": "03 Sides",
            "title": "Stack-drill the pair: bearing, flange, pilots",
            "goal": "One hole pattern, drilled once, so the drum axis cannot be crooked.",
            "parts": ["P-001L", "P-001R"],
            "hardware": ["H-001", "H-002"],
            "tools": ["Drill press", "Forstner bits", "Clamps", "Awl"],
            "sheets": ["P-001L", "P-001R"],
            "actions": [
                "Clamp the panels face-to-face, inner faces together, infeed edges flush.",
                f"Lay out the bearing centreline at Y {g.bearing_cl_y:g}″ from the infeed edge and Z {g.bearing_cl_z:g}″ up from the bottom.",
                f"Set the actual flange on the panel and transfer its bolt holes. The drawing shows {s.flange_bolt_square:g}″ square as a placeholder — your bearing decides.",
                f"Drill the ⌀{s.ply_shaft_clear_dia:g}″ shaft clearance and the four bolt holes through both panels at once (S-008).",
                f"Drive side only: pilot the motor pivot at Y {s.motor_pivot_y:g}″ / Z {s.motor_pivot_z:g}″ and the indicator pad at Y {s.indicator_pad_y:g}″ / Z {s.indicator_pad_z:g}″.",
            ],
            "qc": "QC-02",
            "gate": "Panels separated; hole patterns line up when the panels are flipped face-to-face.",
            "hold": "Stop here until the flange is in your hand. Do not drill this pattern from the drawing alone.",
            "warn": "Clamp hard. A panel that shifts mid-drill gives you two different machines.",
            "shows": ["sides"],
            "adds": ["sides"],
            "correctable": "Almost nothing. This pattern is the datum for the whole machine.",
        },
        {
            "step": 5,
            "chapter": "03 Sides",
            "title": "Dado the stretcher housings and way rebates",
            "goal": "Inner-face joinery, mirrored — the one operation where the panels are NOT identical.",
            "parts": ["P-001L", "P-001R"],
            "hardware": [],
            "tools": ["Dado stack or router + edge guide", "Test offcut"],
            "sheets": ["P-001L", "P-001R", "D-12"],
            "actions": [
                "Split the pair. From here the panels are mirror images — work only on the marked inner faces.",
                f"Cut three stretcher housings {s.stretcher_housing:g}″ deep × {s.ply_actual:g}″ wide × {s.stretcher_height:g}″ tall at stations IN-LO, OUT-LO, OUT-HI (J-001, S-006). Rails stand on edge. None of these dados may sit at Z ≈ 12 — that is the table.",
                f"Rout the vertical way rebate {g.way_rebate:.3f}″ deep × {s.way_width:g}″ wide, Y {g.way_y0:g}–{g.way_y1:g}″ (drum CL), Z {g.way_z0:g}–{g.way_z1:g}″ (J-002, S-007).",
                "Test the dado width on an offcut of the same ply first. A sloppy housing is a racking frame.",
            ],
            "qc": "QC-12 · QC-13",
            "gate": f"Rebate {g.way_rebate:.3f}″ deep ±0.010″; a scrap of way stock sits {g.way_project:.3f}″ proud. Dados at IN-LO / OUT-LO / OUT-HI only.",
            "hold": "",
            "warn": "Do not dado the panels while they are still stacked. You will get two left-hand sides.",
            "shows": ["sides", "ways"],
            "adds": ["ways"],
            "correctable": "A rebate can go deeper, never shallower.",
        },
        {
            "step": 6,
            "chapter": "04 Frame",
            "title": "Glue the box: stretchers, base, diagonals",
            "goal": "A square, stiff carcase that will not rack when a board is pushed through it.",
            "parts": ["P-001L", "P-001R", "P-002", "P-003"],
            "hardware": ["H-014", "H-015", "H-023", "H-034"],
            "tools": ["Long clamps", "Framing square", "Tape measure", "Glue brush", "Drill"],
            "sheets": ["A-01", "P-003", "P-002"],
            "actions": [
                f"Dry-fit all three stretchers ({g.stretcher_length:g}″, housed {s.stretcher_housing:g}″ each end) into IN-LO, OUT-LO, OUT-HI. Check the inner span reads {s.clear_between_sides:g}″. Confirm no rail sits in the table's Z range ({g.table_z_at_max_stock:g}–{g.table_z_at_min_stock + g.table_thick:.2f}″).",
                "Glue and clamp. Measure both diagonals and pull them equal before the glue grabs.",
                "With the joint clamped, drill through the side into each stretcher end and fit H-034 ¼-20 through-bolts with backing washers and nylocks (D-048). Glue is not primary structure on this machine.",
                "Screw the base deck on, then measure the diagonals again.",
            ],
            "qc": "QC-03",
            "gate": f"Diagonals equal within 1/32″. Inner span {s.clear_between_sides:g}″ at top, middle, and bottom.",
            "hold": "Let the glue cure before hanging anything heavy on the box.",
            "warn": "",
            "shows": ["sides", "base", "stretch"],
            "adds": ["base", "stretch"],
            "correctable": "Squareness — for about ten minutes.",
        },
        {
            "step": 7,
            "chapter": "04 Frame",
            "title": "Bond the vertical UHMW ways and wax them",
            "goal": "Two plumb rails for the table shoes to wrap. These, not the stretchers, locate the table in X and Y.",
            "parts": ["P-007"],
            "hardware": ["H-023", "H-024"],
            "tools": ["Square", "Dial indicator", "Clamps"],
            "sheets": ["P-007", "A-01", "J-002"],
            "actions": [
                f"Cut two UHMW strips {g.way_len:g}″ × {s.way_width:g}″ and set them into the vertical rebates. They should project {g.way_project:.3f}″.",
                "Bond and clamp. Optional: #8 flush screws from the outer face.",
                "Square both ways to the base. An indicator riding a tall square should read the same on left and right.",
                "Paste wax only. Never oil — oil migrates into the wood and into your finish.",
            ],
            "qc": "QC-04",
            "gate": f"Ways plumb. Projection {g.way_project:.3f}″ ±0.010″. Centered on drum CL at Y {g.bearing_cl_y:g}″.",
            "hold": "",
            "warn": "",
            "shows": ["sides", "base", "stretch", "ways"],
            "adds": ["ways"],
            "correctable": "UHMW can be planed down; it cannot be built back up.",
        },
        {
            "step": 8,
            "chapter": "04 Frame",
            "title": "Make the tapered gib and tap the adjuster stations",
            "goal": "Have the gib ready before the table exists. Running clearance is set later, after the shoes are on.",
            "parts": ["P-022"],
            "hardware": ["H-031"],
            "tools": ["Taper jig", "Hand plane or belt sander", "Tap ¼-20"],
            "sheets": ["P-022", "J-105"],
            "actions": [
                f"Taper one face of P-022 at 1:40 over its {s.side_depth:g}″ length. Mark the thick end so it cannot go in backwards.",
                f"Drill and tap three ¼-20 stations in the idler-side panel for the H-031 brass-tip adjusters (S-013).",
                "Dry-fit the gib in the rebate behind where the idler shoe will sit. Taper wedges DOWN: tightening a screw will close the clearance.",
                "Do not set the running clearance yet — there is no table to rock against. That happens in the table chapter after the shoes are on.",
            ],
            "qc": "",
            "gate": "Gib tapered, thick end marked, three adjuster stations tapped, dry-fit confirmed.",
            "hold": "",
            "warn": "A gib installed thick-end-up opens when you tighten. Mark the thick end before it leaves the taper jig.",
            "shows": ["sides", "base", "stretch", "ways"],
            "adds": ["ways"],
            "correctable": "Taper and length — the gib is still a loose part.",
        },
        {
            "step": 9,
            "chapter": "05 Drum",
            "title": "Turn the two end plugs — one setup, two operations",
            "goal": "Bore and OD concentric, because that error becomes drum TIR directly.",
            "parts": ["P-021"],
            "hardware": ["H-028"],
            "tools": ["Metal lathe (or a machinist friend)", "Boring bar", "Calipers", "Bore gauge"],
            "sheets": ["P-021", "J-106", "A-02"],
            "actions": [
                f"Face and turn the OD to a light bond fit in the shell ID ({s.shell_od - 2 * s.shell_wall:g}″ nominal — measure YOUR tube).",
                f"WITHOUT unchucking, bore {s.shaft_od:g}″ for the shaft. One setup is the whole trick: it makes bore and OD concentric.",
                f"Part off at {s.plug_thick:g}″ thick. Repeat for the second plug.",
                "Deburr both, then check the bore on the actual shaft — light push fit, no rock.",
            ],
            "qc": "QC-06",
            "gate": "Bore-to-OD runout under 0.001″ on each plug, checked in the lathe before parting off.",
            "hold": "",
            "warn": "If you re-chuck between the OD and the bore you will add eccentricity that no amount of truing removes, because the drum will run true only at one angular position.",
            "shows": ["drum"],
            "adds": ["drum"],
            "correctable": "Nothing after parting off. Make a spare plug from the same bar.",
        },
        {
            "step": 10,
            "chapter": "05 Drum",
            "title": "Bond and cross-pin the shell to the plugs",
            "goal": "A structural drum, not a stack of discs.",
            "parts": ["P-020", "P-021"],
            "hardware": ["H-027", "H-033", "H-018"],
            "tools": ["Solvent + abrasive pad", "Drill press", "Clamps", "Square"],
            "sheets": ["P-020", "P-021", "J-106", "A-02"],
            "actions": [
                f"Cut the shell to {g.drum_length:g}″ and face both ends square.",
                "Abrade and solvent-clean the shell ID and both plug ODs. Contamination is the usual cause of a failed metal bond.",
                f"Mix H-033 structural epoxy, coat both faces, and seat each plug {s.plug_inset:g}″ inboard of the shell end. Check square to the shell axis.",
                "After cure, cross-drill and pin each plug through the shell wall in two places 90° apart. The pins carry torque; the epoxy seals and shares load.",
            ],
            "qc": "",
            "gate": "Both plugs seated at the specified inset, square, fully cured, and pinned.",
            "hold": f"FULL CURE per the adhesive data sheet before the drum turns under power. This is a {MECH_DRUM_MASS:.0f} lb rotating assembly.",
            "warn": "Never rely on adhesive alone on a rotating part. The cross-pins are not optional.",
            "shows": ["drum"],
            "adds": ["drum"],
            "correctable": "The OD — that is what truing is for. Not the plug position.",
        },
        {
            "step": 11,
            "chapter": "05 Drum",
            "title": "OPTION B — laminated disc drum for a shop with no lathe",
            "goal": "A buildable drum without turned metal, with its accuracy penalty stated.",
            "alt_of": "ST-09 + ST-10",
            "parts": ["P-008", "P-009", "P-015"],
            "hardware": ["H-018", "H-023"],
            "tools": ["Bandsaw", "Drill press + reamer", "Clamps", "Scale"],
            "sheets": ["P-008", "P-009", "P-015", "A-02"],
            "actions": [
                f"Choose this path ONLY if you cannot get the plugs turned. It replaces steps ST-09 and ST-10.",
                f"Bandsaw {s.disc_count_core} MDF discs and {s.disc_count_ends} birch ends at ⌀{g.drum_oversize_od:g}″ — oversize on purpose.",
                f"Stack the whole pack in the P-015 jig and ream ⌀{s.shaft_od:g}″ straight through (J-005, S-009). Never bore discs one at a time.",
                f"Glue the stack with a {s.spacer_mm:g} mm relief every {s.spacer_every_n} MDF discs. Birch ends outboard for flange crush.",
                "Weigh the two end discs against each other and balance them before assembly.",
            ],
            "qc": "QC-06 · QC-18",
            "gate": f"Bore accepts the shaft with light friction. Stack length {g.drum_length:g}″.",
            "hold": "Full cure before the drum ever spins. A delaminated disc at speed is a projectile.",
            "warn": f"ACCEPT THE PENALTY KNOWINGLY: a disc stack is not structural in bending, so the drum crowns under load and MDF moves with humidity, so TIR drifts between seasons. Expect to re-true more often and to hold a looser TV-01 than {s.tv_spec:.3f}″.",
            "shows": ["drum", "shaft"],
            "adds": ["drum"],
            "correctable": "Outside diameter — that is what truing is for.",
        },
        {
            "step": 12,
            "chapter": "05 Drum",
            "title": "Hang the shaft: drive FIXED, idler on the micro-adjust plate",
            "goal": "One bearing defines the axis; the other adjusts parallelism and lets the shaft grow.",
            "parts": ["P-010", "P-023", "P-024"],
            "hardware": ["H-001", "H-002", "H-029", "H-030", "H-032"],
            "tools": ["Wrenches", "Dial indicator", "Feeler gauges", "Reamer"],
            "sheets": ["P-010", "P-023", "P-024", "J-105", "J-106", "A-02"],
            "actions": [
                "Transfer the bearing bolt pattern FROM THE BEARING YOU BOUGHT onto P-001L and P-023. Do not drill from the drawing — that pattern is an assumption.",
                f"Slide the {s.shaft_length:g}″ shaft through the drum and both panels, then set the H-029 clamp collars against the plugs.",
                "Bolt H-001 to the drive side and torque it. That bearing is now DATUM-E, the drum-axis datum (J-006).",
                f"Pin P-023 to the idler side with H-032, mount H-002 on it, and set the H-030 jack screw against P-024. Snug the bearing only — the shaft must still slide axially (J-007).",
                "Spin the drum by hand through several turns. It should coast, not bind and not ring.",
            ],
            "qc": "QC-11",
            "gate": "Shaft turns freely; measurable axial float at the idler end; jack screw makes contact with a witness mark.",
            "hold": "",
            "warn": "Locking both bearings bends the shaft and kills both of them. Do not do it because it feels tighter.",
            "shows": ["sides", "base", "stretch", "ways", "drum", "shaft"],
            "adds": ["shaft"],
            "correctable": "Bearing position, while the bolts are still loose.",
        },
        {
            "step": 12,
            "chapter": "05 Drum",
            "title": "True the drum in its own bearings, then balance it",
            "goal": "A cylinder that is round about the axis it will actually run on.",
            "parts": ["P-013", "P-020"],
            "hardware": ["H-021"],
            "tools": ["Truing sled P-013", "Dial indicator", "Knife edges or two level rails"],
            "sheets": ["P-013", "A-02", "Q-101"],
            "actions": [
                "True the OD with the drum running in its OWN bearings, using the full-width P-013 sled. Truing it in a lathe and then moving it re-introduces the error.",
                f"Work down until the indicator reads ≤ {s.drum_tir:.4f}″ TIR at mid-span, paper off (QC-06).",
                f"Lift the drum onto knife edges and release it from five different angular positions. It must stop somewhere different each time. Allowance U ≤ {MECH_UNBALANCE_OZIN:.2f} oz·in (CALC-C13).",
                "If it always settles the same way, add tape to the light side until it does not, then make that correction permanent.",
            ],
            "qc": "QC-06",
            "gate": f"TIR ≤ {s.drum_tir:.4f}″ paper off, and the knife-edge test passes over five releases.",
            "hold": "Do not fit the abrasive until both checks pass. Paper hides TIR; it does not fix it.",
            "warn": "Extraction and a respirator for truing. Eye protection — you are cutting metal or MDF at speed.",
            "shows": ["sides", "base", "stretch", "ways", "drum", "shaft"],
            "adds": ["drum"],
            "correctable": "Balance, any time. TIR only by truing again.",
        },
        {
            "step": 10,
            "chapter": "06 Drive",
            "title": "Mount the motor, align the pulleys, lock the cradle",
            "goal": "Belt tension by gravity, then locked so it cannot pump.",
            "parts": ["P-012"],
            "hardware": ["H-003", "H-004", "H-005", "H-006", "H-016"],
            "tools": ["Straightedge", "Wrenches", "Level"],
            "sheets": ["P-012", "A-04"],
            "actions": [
                f"Pivot P-012 on the drive-side hole and hang the {s.motor_hp:g} HP motor on it.",
                f"Fit the {s.pulley_motor_od:g}″ motor pulley and the {s.pulley_drum_od:g}″ drum pulley. Lay a straightedge across both faces and shim until they are coplanar.",
                "Let the cradle hang to tension the belt, measure the centre distance, then buy the belt to that number.",
                "Lock the cradle. A cradle that still swings will pump the belt and chirp.",
            ],
            "qc": "QC-09",
            "gate": "Pulley faces coplanar; belt tracks centred when the drum is turned by hand.",
            "hold": "Do not connect power yet.",
            "warn": "Mains wiring, switch, and grounding belong to a qualified electrician and your local code. This package does not release electrical work.",
            "shows": ["sides", "base", "stretch", "ways", "drum", "shaft", "motor"],
            "adds": ["motor"],
            "correctable": "Belt length, before you buy it.",
        },
        {
            "step": 11,
            "chapter": "07 Table",
            "title": "Build the torsion-box table and bond the wear face",
            "goal": "A flat plate that stays flat. This is the surface you measure against forever.",
            "parts": ["P-004", "P-005", "P-006", "P-017"],
            "hardware": ["H-023"],
            "tools": ["Clamps and cauls", "Straightedge", "Feeler gauges", "Flat bench"],
            "sheets": ["P-004", "P-005", "P-006", "P-017", "A-03"],
            "actions": [
                f"Glue the rib grid at {s.table_rib_oc:g}″ o.c. between the two skins. Full glue, clamped on a flat reference.",
                "Check the box flat in both directions and on both diagonals. Flatten it before going further.",
                "Bond the phenolic or tooling-plate wear face on top (J-004).",
                f"Groove and bolt P-017 shoes under each long edge, centered on Y {g.bearing_cl_y:g}″. Groove {g.shoe_groove_depth:.3f}″ × {g.shoe_groove_width:.3f}″ wraps the way tongue (J-012).",
                f"Confirm the finished plan size is {g.table_width:g}″ × {g.table_depth:g}″ so the wear face still carries {s.capacity_width:g}″ of work.",
            ],
            "qc": "QC-05",
            "gate": f"Wear face flat within {s.table_flat_tol:.3f}″ on both diagonals.",
            "hold": "Cure fully. Every later measurement trusts this plane.",
            "warn": "",
            "shows": ["table"],
            "adds": ["table"],
            "correctable": "Flatness, while the box is still open.",
        },
        {
            "step": 12,
            "chapter": "07 Table",
            "title": "Fit the dual Acme lift on the drum centerline",
            "goal": "Both nuts sit under the cut. The table rises in Z without racking in X or Y.",
            "parts": ["P-016", "P-018", "P-019", "P-022"],
            "hardware": ["H-007", "H-008", "H-013", "H-026", "H-031", "H-024", "H-035"],
            "tools": ["Wrenches", "Drill", "Tape measure", "Square"],
            "sheets": ["P-016", "P-018", "P-019", "P-022", "A-03", "M-101", "J-105"],
            "actions": [
                f"Screw both P-018 thrust blocks to the base at Y {g.acme_y:g}″ (drum CL), X left and right. Fit thrust washers and e-clips (J-013).",
                "Bolt a bronze nut block under the table, each nut on the same Y as its screw — not at the infeed and outfeed ends.",
                f"Fit both ½-10 Acme screws. One turn is {g.acme_per_turn:.4f}″. Thirty turns is 3″ (CALC-003).",
                "Chain-couple the two screws. Fit the left clutch and P-019 home dog (J-014).",
                f"Run the table through the full {s.elev_travel:g}″ of travel. Shoes must stay wrapped; the table must not yaw.",
                f"Now set the P-022 gib: slide it behind the idler shoe, taper down, and run the H-031 adjusters up in equal steps until the table slides by hand with no rock. Target {s.gib_clearance:.4f}″ (QC-17, S-014). Wax. Never oil.",
            ],
            "qc": "QC-12 · QC-14 · QC-17",
            "gate": f"Table rises and falls freely through full travel; both ends move the same amount; shoes stay captured; gib clearance {s.gib_clearance:.4f}″ with no rock.",
            "hold": "",
            "warn": "",
            "shows": ["sides", "base", "stretch", "ways", "drum", "shaft", "motor", "table", "elev"],
            "adds": ["table", "elev"],
            "correctable": "Nut block position, before the holes are final.",
        },
        {
            "step": 13,
            "chapter": "08 Hood & hold-downs",
            "title": "Kerf-bend the hood and set the roller yokes",
            "goal": "The guard that is also the dust hood, plus the rollers that kill snipe.",
            "parts": ["P-011", "P-014"],
            "hardware": ["H-009", "H-010", "H-011", "H-012", "H-013", "H-019"],
            "tools": ["Table saw (kerfing)", "Feeler gauges", "Drill"],
            "sheets": ["P-011", "P-014", "A-05"],
            "actions": [
                "Kerf-bend the hood blank around the drum arc, glue the form, fill the kerfs, and fit the 4″ port.",
                "Hang both roller yokes on shoulder-bolt pivots with light compression springs.",
                f"Set each roller {s.roller_setbelow:.3f}″ below the drum OD with paper on, using feeler gauges.",
                "Check the hood clears the drum, the rollers, and the oscillator stroke if you fitted one.",
            ],
            "qc": "QC-08",
            "gate": f"Both rollers {s.roller_setbelow:.3f}″ below drum OD, paper on. Hood seats without touching the drum.",
            "hold": "",
            "warn": "Hood ON is the primary guard. Open it only with the machine stopped and unplugged.",
            "shows": ["sides", "base", "stretch", "ways", "drum", "shaft", "motor", "table", "elev", "rollers", "hood"],
            "adds": ["rollers", "hood"],
            "correctable": "Spring rate and roller height, any time.",
        },
        {
            "step": 14,
            "chapter": "09 Commissioning",
            "title": "True, wrap, re-clock, and cut a witness board",
            "goal": "Turn an assembled machine into a calibrated one.",
            "parts": ["P-013"],
            "hardware": ["H-021", "H-022"],
            "tools": ["Dial indicator + mag base", "Calipers", "Test panel", "Respirator"],
            "sheets": ["Q-101", "Q-103", "P-013", "A-02"],
            "actions": [
                f"Paper off: true the drum with the full-width sled until TIR ≤ {s.drum_tir:.3f}″ mid-span (S-010).",
                "Wrap Velcro, then spiral the paper. Paper thickness is not uniform, so parallel changes here.",
                f"ALN-01: paper on, drum stopped, no workpiece. Indicate the drum at station A (drive) and station B (idler). Bring |A−B| ≤ {s.aln_spec:.3f}″ using the P-023 jack screw — {MECH_ADJ_AT_WORK * 1000:.2f} mil at the work per full turn, so work in small fractions of a turn. Set the home dog (S-011).",
                f"TV-01: sand a witness board {s.capacity_width:g}″ wide at the finish pass. Caliper four corners and the centre. Spread must be ≤ {s.tv_spec:.3f}″. This is a different and larger number than ALN-01 — see CALC-C06.",
                f"Then work the pass schedule: {s.pass_rough:.3f}″ rough, {s.pass_medium:.3f}″ medium, {s.pass_finish:.3f}″ finish. Always approach the setting by RAISING the table, then lock the ways.",
            ],
            "qc": "QC-06 · QC-15 · QC-16 · QC-20",
            "gate": f"TIR ≤ {s.drum_tir:.4f}″ paper-off · ALN-01 |A−B| ≤ {s.aln_spec:.3f}″ paper-on · TV-01 witness spread ≤ {s.tv_spec:.3f}″.",
            "hold": "First powered run: hood on, no stock, stand clear of the drum ends, hand on the switch.",
            "warn": "Do not sand stock shorter than about 12″ without the sled. Hands never under the drum or the hold-downs.",
            "shows": ["sides", "base", "stretch", "ways", "drum", "shaft", "motor", "table", "elev", "rollers", "hood"],
            "adds": [],
            "correctable": "Everything that matters — which is why you re-clock after every paper change.",
        },
    ]
    # Renumber programmatically so inserting a step can never leave two steps
    # sharing a number, or a sheet name pointing at the wrong step.
    total = len(steps)
    for n, st in enumerate(steps, start=1):
        st["step"] = n
        st["id"] = f"ST-{n:02d}"
        st["of"] = total
    return steps


def calibration_steps() -> list[dict[str, str]]:
    s = SPEC
    return [
        {"id": "c1", "title": "Disconnect power", "body": "Unplug. Hood off. Paper off for TIR; paper on for A/B parallel."},
        {"id": "c2", "title": "Seat the table on the vertical ways", "body": "Raise/lower through full travel. Shoes stay wrapped. No bind, no yaw. Square on the wear face — no twist."},
        {"id": "c3", "title": "Drum TIR", "body": f"Indicator on mid-span OD. Rotate by hand. If > {s.drum_tir:.3f}″, re-true on P-013 before wrapping."},
        {"id": "c4", "title": "Wrap & re-clock", "body": "Velcro then spiral paper. Paper is not uniform — A/B will change. This is the measurement that matters."},
        {"id": "c5", "title": "A/B parallel", "body": f"Same indicator height, drive then idler. Uncouple left Acme; 1/{s.acme_tpi:g} turn ≈ {GEOM.acme_per_turn:.4f}″. Recouple. Set home dog."},
        {"id": "c6", "title": "Hold-down height", "body": f"Feelers under each roller vs drum. {s.roller_setbelow:.3f}″ below. Leading snipe → ease outfeed spring; trailing → ease infeed."},
        {"id": "c7", "title": "Witness board", "body": "6″ × 16″ maple, 80 grit, one pass. Ridge at overlap = idler high/low. Caliper corners. Log in the Build app."},
        {"id": "c8", "title": "Taper mode (optional)", "body": "Uncouple left, drop idler a few thousandths, sand, then return to home dog — do not re-invent parallel each time."},
    ]


def fmea() -> list[dict[str, str]]:
    return [
        {"mode": "Table rack under feed", "cause": "Butt stretchers / uncaptured table / stretcher in the table path", "effect": "Tapered cut, bind, or a rail hitting the table", "mitigation": "J-001 triangle stations + J-012 captured shoes + CALC-004", "sev": "H"},
        {"mode": "Banana shaft", "cause": "Both flanges locked", "effect": "TIR and bearing death", "mitigation": "J-007 axial float", "sev": "H"},
        {"mode": "Snipe", "cause": "Hold-down springs too stiff / missing", "effect": "End thickness scatter", "mitigation": "Light H-011; 0.030″ set", "sev": "M"},
        {"mode": "Helical tracks", "cause": "Spiral wrap, no osc", "effect": "Visible stripes", "mitigation": "Optional H-025; or 90° finish pass", "sev": "L"},
        {"mode": "Lost parallel after wrap", "cause": "Paper thickness not uniform", "effect": "|A−B| opens", "mitigation": "Re-clock paper-on; home dog", "sev": "H"},
        {"mode": "Drum dish", "cause": "Narrow truing block", "effect": "Center thin", "mitigation": "P-013 full-width sled", "sev": "M"},
    ]


# ---------------------------------------------------------------------------
# 4. Exports
# ---------------------------------------------------------------------------

def summary() -> dict[str, Any]:
    s, g = SPEC, GEOM
    errs = validate(s, g)
    spec_d = asdict(s)
    spec_d.pop("stretcher_stations", None)
    spec_d["stretcher_stations"] = [list(row) for row in s.stretcher_stations]
    return {
        "project": PROJECT,
        "parameters": spec_d,
        "geometry": {k: v for k, v in asdict(g).items() if k != "equations"},
        "equations": g.equations,
        "validation": {"ok": not errs, "errors": errs},
        "datums": datums(),
        "parts": parts(),
        "joints": joints(),
        "hardware": hardware(),
        "assemblies": assemblies(),
        "operations": operations(),
        "inspection": inspection(),
        "decisions": decisions(),
        "revisions": revisions(),
        "fmea": fmea(),
        "quality": quality_targets(),
        "passes": pass_schedule(),
        "cut_list": cut_list(),
        "lumberyard": lumberyard(),
        "fasteners": fastener_schedule(),
        "nesting": nest_sheets(),
        "drawings": shop_drawings(),
        "build_steps": build_steps(),
        "calculations": calculations(),
        "procurement": procurement(),
        "procurement_summary": procurement_summary(),
        "accuracy_budgets": accuracy_budgets(),
        "superseded": superseded_by_rev_c(),
        "layout_protocol": LAYOUT_PROTOCOL,
        "drawings": shop_drawings(),
        "assembly": assembly_phases(),
        "calibration": calibration_steps(),
        "name": PROJECT["project_name"],
        "revision": s.revision,
        "fabrication_rev": s.fabrication_rev,
        "lineage": PROJECT["lineage"],
        "capacity": f'{s.capacity_width}" wide · {s.min_stock_thickness}"–{s.max_stock_thickness}" thick',
        "drum_rpm": s.drum_rpm,
        "surface_fpm": g.surface_fpm,
        "parallel_tol": s.parallel_tol,
        "spec": spec_d,
        "notes": [
            "Keep 16.5″ (419 mm) clear between inner faces even if ply is 18 mm Euro BB instead of ¾″.",
            f"Way rebate {g.way_rebate:.3f}″ / project {g.way_project:.3f}″ so the {g.table_width:g}″ table fits the span.",
            f"Stretcher finished length {g.stretcher_length:g}″ (housed {s.stretcher_housing:g}″ each end).",
            "iPhone: share the ZIP → Save to Files. Pocket card: Share → Add to Home Screen or Print → PDF.",
        ],
    }


def parameters_scad(s: Spec = SPEC, g: Geom = GEOM) -> str:
    lines = [
        "// AUTO-GENERATED from walter_ds16.py — do not edit",
        f"// WALTER DS-16 Rev {s.revision} fab {s.fabrication_rev} · inches",
        f"side_t = {g.side_thick};",
        f"side_h = {s.side_height};",
        f"side_d = {s.side_depth};",
        f"clear  = {s.clear_between_sides};",
        f"W = {g.overall_width};",
        f"drum_od = {s.drum_od};",
        f"drum_len = {g.drum_length};",
        f"shaft_od = {s.shaft_od};",
        f"shaft_len = {s.shaft_length};",
        f"table_w = {g.table_width};",
        f"table_d = {g.table_depth};",
        f"table_t = {g.table_thick};",
        f"table_z = {g.table_z_display};",
        f"drum_z = {g.bearing_cl_z};",
        f"drum_y = {g.bearing_cl_y};",
        f"roller_od = {s.roller_od};",
        f"roller_len = {g.roller_len};",
        f"way_project = {g.way_project};",
        f"way_stock = {s.way_stock};",
        f"way_rebate = {g.way_rebate};",
        f"way_width = {g.way_width};",
        f"way_y0 = {g.way_y0};",
        f"way_z0 = {g.way_z0};",
        f"way_len = {g.way_len};",
        f"stretcher_h = {s.stretcher_height};",
        f"stretcher_len = {g.stretcher_length};",
        f"stretcher_housing = {s.stretcher_housing};",
        f"stretcher_y = [{', '.join(str(r[1]) for r in g.stretcher_stations)}];",
        f"stretcher_z = [{', '.join(str(r[2]) for r in g.stretcher_stations)}];",
        f"flange_bolt_square = {s.flange_bolt_square};",
        f"flange_bolt_clr = {s.flange_bolt_clr};",
        f"ply_shaft_clear_dia = {s.ply_shaft_clear_dia};",
        f"motor_pivot_y = {s.motor_pivot_y};",
        f"motor_pivot_z = {s.motor_pivot_z};",
        f"idler_float_pad = {s.idler_float_pad};",
        f"acme_y = {g.acme_y};",
        f"acme_y0 = {g.acme_y};",
        f"acme_y1 = {g.acme_y};",
        f"acme_x0 = {g.acme_x_left};",
        f"acme_x1 = {g.acme_x_right};",
        f"shoe_h = {g.shoe_h};",
        f"shoe_t = {g.shoe_t};",
        f"thrust_h = {g.thrust_h};",
        f"dust_port_od = {s.dust_port_od};",
        "",
    ]
    return "\n".join(lines)


def geometry_js(s: Spec = SPEC, g: Geom = GEOM) -> str:
    body = {
        "sideT": g.side_thick,
        "sideH": s.side_height,
        "sideD": s.side_depth,
        "clear": s.clear_between_sides,
        "drumOd": s.drum_od,
        "drumLen": g.drum_length,
        "shaftOd": s.shaft_od,
        "shaftLen": s.shaft_length,
        "tableW": g.table_width,
        "tableD": g.table_depth,
        "tableT": g.table_thick,
        "tableY": g.table_z_display,
        "drumY": g.bearing_cl_z,
        "drumFeedY": g.bearing_cl_y,
        "rollerOd": s.roller_od,
        "rollerLen": g.roller_len,
        "wayProject": g.way_project,
        "wayStock": s.way_stock,
        "wayWidth": g.way_width,
        "wayY0": g.way_y0,
        "wayZ0": g.way_z0,
        "wayLen": g.way_len,
        "stretcherLen": g.stretcher_length,
        "stretcherH": s.stretcher_height,
        "stretcherStations": [
            {"id": r[0], "y0": r[1], "z0": r[2], "y1": r[3], "z1": r[4]}
            for r in g.stretcher_stations
        ],
        "acmeX0": g.acme_x_left,
        "acmeX1": g.acme_x_right,
        "acmeY": g.acme_y,
        "shoeH": g.shoe_h,
        "shoeT": g.shoe_t,
        "shoeGroove": g.shoe_groove_depth,
        "thrustL": g.thrust_l,
        "thrustW": g.thrust_w,
        "thrustH": g.thrust_h,
    }
    return (
        "/* AUTO-GENERATED from cad/walter_ds16.py — do not edit */\n"
        f"export const P = {json.dumps(body, indent=2)};\n"
        "P.W = P.clear + 2 * P.sideT;\n"
        "P.hx = P.W / 2;\n"
        "P.hz = P.sideD / 2;\n"
    )


def shop_drawings() -> list[dict[str, str]]:
    """Every printable sheet. kind drives the phone viewer rails."""
    rows: list[dict[str, str]] = [
        {"code": "G-001", "file": "G001_cover.svg", "title": "G-001 Cover & release", "kind": "guide", "group": "guide"},
        {"code": "G-002", "file": "G002_design_basis.svg", "title": "G-002 Design basis", "kind": "guide", "group": "guide"},
        {"code": "G-003", "file": "G003_registers.svg", "title": "G-003 Evidence & calcs", "kind": "guide", "group": "guide"},
        {"code": "G-004", "file": "G004_safety.svg", "title": "G-004 Safety & risk", "kind": "guide", "group": "guide"},
        {"code": "G-005", "file": "G005_revision_c.svg", "title": "G-005 Rev C supersession", "kind": "guide", "group": "guide"},
        {"code": "M-106", "file": "M106_accuracy.svg", "title": "M-106 Accuracy budget", "kind": "guide", "group": "guide"},
        {"code": "M-107", "file": "M107_drum_axis.svg", "title": "M-107 Drum axis stiffness", "kind": "guide", "group": "guide"},
        {"code": "M-108", "file": "M108_adjust.svg", "title": "M-108 Micro-adjust & lift", "kind": "guide", "group": "guide"},
        {"code": "J-105", "file": "J105_gib.svg", "title": "J-105 Gib & pivot plate", "kind": "guide", "group": "guide"},
        {"code": "J-106", "file": "J106_shell_plug.svg", "title": "J-106 Shell→plug→shaft", "kind": "guide", "group": "guide"},
        {"code": "Q-103", "file": "Q103_acceptance.svg", "title": "Q-103 ALN-01 / TV-01 tests", "kind": "guide", "group": "guide"},
        {"code": "H-02", "file": "H02_mcmaster.svg", "title": "H-02 McMaster procurement", "kind": "hardware", "group": "hardware"},
        {"code": "H-03", "file": "H03_mcmaster2.svg", "title": "H-03 McMaster procurement (2)", "kind": "hardware", "group": "hardware"},
        {"code": "E-101", "file": "E101_exploded.svg", "title": "E-101 Exploded + BOM", "kind": "guide", "group": "guide"},
        {"code": "M-101", "file": "M101_kinematics.svg", "title": "M-101 Kinematics", "kind": "guide", "group": "guide"},
        {"code": "J-001", "file": "J001_stretcher.svg", "title": "J-001 Housed stretcher", "kind": "guide", "group": "guide"},
        {"code": "J-002", "file": "J002_way.svg", "title": "J-002 Vertical way", "kind": "guide", "group": "guide"},
        {"code": "J-006", "file": "J006_drive_bearing.svg", "title": "J-006 Drive bearing", "kind": "guide", "group": "guide"},
        {"code": "J-007", "file": "J007_idler_float.svg", "title": "J-007 Idler float", "kind": "guide", "group": "guide"},
        {"code": "J-011", "file": "J011_lift.svg", "title": "J-011 Lift & capture", "kind": "guide", "group": "guide"},
        {"code": "F-101", "file": "F101_routing.svg", "title": "F-101 Part register", "kind": "guide", "group": "guide"},
        {"code": "S-101", "file": "S101_load_path.svg", "title": "S-101 Load path", "kind": "guide", "group": "guide"},
        {"code": "Q-101", "file": "Q101_commissioning.svg", "title": "Q-101 Commissioning", "kind": "guide", "group": "guide"},
        {"code": "Q-102", "file": "Q102_zero_gap.svg", "title": "Q-102 Zero-gap", "kind": "guide", "group": "guide"},
        {"code": "IDX", "file": "IDX_drawings.svg", "title": "Drawing index", "kind": "plan", "group": "index"},
        {"code": "D-1", "file": "D1_general.svg", "title": "D-1 General", "kind": "plan", "group": "overview"},
        {"code": "D-2", "file": "D2_frame.svg", "title": "D-2 Frame", "kind": "plan", "group": "overview"},
        {"code": "D-3", "file": "D3_drum.svg", "title": "D-3 Drum", "kind": "plan", "group": "overview"},
        {"code": "D-4", "file": "D4_drive.svg", "title": "D-4 Drive", "kind": "plan", "group": "overview"},
        {"code": "D-5", "file": "D5_hood.svg", "title": "D-5 Hood", "kind": "plan", "group": "overview"},
        {"code": "D-6", "file": "D6_cutlist.svg", "title": "D-6 Cut list", "kind": "plan", "group": "overview"},
        {"code": "D-7", "file": "D7_geometry.svg", "title": "D-7 Geometry", "kind": "plan", "group": "overview"},
        {"code": "D-8", "file": "D8_holddowns.svg", "title": "D-8 Hold-downs", "kind": "plan", "group": "overview"},
        {"code": "D-9", "file": "D9_model.svg", "title": "D-9 3D views", "kind": "plan", "group": "overview"},
        {"code": "D-10", "file": "D10_lumberyard.svg", "title": "D-10 Lumberyard", "kind": "plan", "group": "overview"},
        {"code": "D-11", "file": "D11_register.svg", "title": "D-11 Part register", "kind": "plan", "group": "overview"},
        {"code": "D-12", "file": "D12_joinery.svg", "title": "D-12 Joinery & QA", "kind": "plan", "group": "overview"},
        {"code": "P-001L", "file": "P001L_side_drive.svg", "title": "P-001L Side, drive", "kind": "part", "group": "part"},
        {"code": "P-001R", "file": "P001R_side_idler.svg", "title": "P-001R Side, idler", "kind": "part", "group": "part"},
        {"code": "P-002", "file": "P002_base.svg", "title": "P-002 Base deck", "kind": "part", "group": "part"},
        {"code": "P-003", "file": "P003_stretcher.svg", "title": "P-003 Stretcher", "kind": "part", "group": "part"},
        {"code": "P-004", "file": "P004_table_skin.svg", "title": "P-004 Table skin", "kind": "part", "group": "part"},
        {"code": "P-005", "file": "P005_table_ribs.svg", "title": "P-005 Table ribs", "kind": "part", "group": "part"},
        {"code": "P-006", "file": "P006_wear_face.svg", "title": "P-006 Wear face", "kind": "part", "group": "part"},
        {"code": "P-007", "file": "P007_uhmw_way.svg", "title": "P-007 UHMW way", "kind": "part", "group": "part"},
        {"code": "P-008", "file": "P008_disc_core.svg", "title": "P-008 Disc, core", "kind": "part", "group": "part"},
        {"code": "P-009", "file": "P009_disc_end.svg", "title": "P-009 Disc, end", "kind": "part", "group": "part"},
        {"code": "P-010", "file": "P010_shaft.svg", "title": "P-010 Shaft", "kind": "part", "group": "part"},
        {"code": "P-011", "file": "P011_hood.svg", "title": "P-011 Dust hood", "kind": "part", "group": "part"},
        {"code": "P-012", "file": "P012_motor_cradle.svg", "title": "P-012 Motor cradle", "kind": "part", "group": "part"},
        {"code": "P-013", "file": "P013_truing_sled.svg", "title": "P-013 Truing sled", "kind": "part", "group": "part"},
        {"code": "P-014", "file": "P014_roller_yoke.svg", "title": "P-014 Roller yoke", "kind": "part", "group": "part"},
        {"code": "P-015", "file": "P015_pack_bore.svg", "title": "P-015 Pack-bore jig", "kind": "part", "group": "part"},
        {"code": "P-016", "file": "P016_nut_block.svg", "title": "P-016 Nut block", "kind": "part", "group": "part"},
        {"code": "P-017", "file": "P017_table_shoe.svg", "title": "P-017 Table shoe", "kind": "part", "group": "part"},
        {"code": "P-018", "file": "P018_thrust_block.svg", "title": "P-018 Thrust block", "kind": "part", "group": "part"},
        {"code": "P-019", "file": "P019_home_dog.svg", "title": "P-019 Home dog", "kind": "part", "group": "part"},
        {"code": "P-020", "file": "P020_drum_shell.svg", "title": "P-020 Drum shell", "kind": "part", "group": "part"},
        {"code": "P-021", "file": "P021_drum_plug.svg", "title": "P-021 Drum end plug", "kind": "part", "group": "part"},
        {"code": "P-022", "file": "P022_gib.svg", "title": "P-022 Way gib", "kind": "part", "group": "part"},
        {"code": "P-023", "file": "P023_idler_plate.svg", "title": "P-023 Idler adjust plate", "kind": "part", "group": "part"},
        {"code": "P-024", "file": "P024_jack_block.svg", "title": "P-024 Jack screw block", "kind": "part", "group": "part"},
        {"code": "A-01", "file": "A01_frame.svg", "title": "A-01 Frame assembly", "kind": "assembly", "group": "assembly"},
        {"code": "A-02", "file": "A02_drum.svg", "title": "A-02 Drum assembly", "kind": "assembly", "group": "assembly"},
        {"code": "A-03", "file": "A03_table.svg", "title": "A-03 Table assembly", "kind": "assembly", "group": "assembly"},
        {"code": "A-04", "file": "A04_drive.svg", "title": "A-04 Drive assembly", "kind": "assembly", "group": "assembly"},
        {"code": "A-05", "file": "A05_holddowns.svg", "title": "A-05 Hold-downs", "kind": "assembly", "group": "assembly"},
        {"code": "H-01", "file": "H01_hardware.svg", "title": "H-01 Hardware", "kind": "hardware", "group": "hardware"},
        *(
            {
                "code": st["id"],
                "file": f"ST{st['step']:02d}_step.svg",
                "title": f"{st['id']} {st['title']}",
                "kind": "step",
                "group": "step",
            }
            for st in build_steps()
        ),
        {"src_kind": "render", "code": "ISO-A", "file": "iso_assembled.svg", "title": "Iso assembled", "kind": "render", "group": "render", "dir": "renders"},
        {"src_kind": "render", "code": "ISO-E", "file": "iso_exploded.svg", "title": "Iso exploded", "kind": "render", "group": "render", "dir": "renders"},
        {"src_kind": "render", "code": "ORTHO-F", "file": "ortho_front.svg", "title": "Front solid", "kind": "render", "group": "render", "dir": "renders"},
        {"src_kind": "render", "code": "ORTHO-S", "file": "ortho_side.svg", "title": "Drive side", "kind": "render", "group": "render", "dir": "renders"},
    ]
    return rows


def viewer_data() -> dict[str, Any]:
    s, g = SPEC, GEOM
    return {
        "meta": {
            "name": "WALTER",
            "code": "DS-16",
            "subtitle": f"Dedicated drum thickness sander · {s.capacity_width:g}″ · geometry Rev {s.revision} · fab {s.fabrication_rev}",
            "revision": s.revision,
            "fabricationRev": s.fabrication_rev,
            "capacity": s.capacity_width,
            "drumOd": s.drum_od,
            "drumRpm": s.drum_rpm,
            "motorHp": s.motor_hp,
            "surfaceFpm": g.surface_fpm,
            "parallelTol": s.parallel_tol,
            "lineage": PROJECT["lineage"],
        },
        "modernizations": list(s.modernizations),
        "parts": [
            {"id": "sides", "fabIds": ["P-001L", "P-001R"], "group": "frame", "label": "Side panels P-001L/R", "detail": f"{s.ply_actual:g}″ BB · stack-drill then inner-face dado/rebate", "color": "#c4a574", "sheet": "P001L_side_drive.svg"},
            {"id": "ways", "fabIds": ["P-007", "P-017"], "group": "frame", "label": "Vertical ways + shoes", "detail": f"P-007 rebate {g.way_rebate:.3f}″ · P-017 wrap · J-002/J-012", "color": "#d9dcde", "sheet": "P007_uhmw_way.svg"},
            {"id": "base", "fabIds": ["P-002", "P-003", "P-018"], "group": "frame", "label": "Base + stretchers + thrust", "detail": f"P-003 housed {g.stretcher_length:g}″ · IN-LO/OUT-LO/OUT-HI · J-001", "color": "#a89070", "sheet": "A01_frame.svg"},
            {"id": "drum", "fabIds": ["P-020", "P-021", "P-008", "P-009"], "group": "drum", "label": "Sanding drum", "detail": f"⌀{s.drum_od:g}″ × {g.drum_length:g}″ · Option A shell P-020/P-021 · Option B discs P-008/P-009", "color": "#b8a990", "sheet": "A02_drum.svg"},
            {"id": "shaft", "fabIds": ["P-010", "P-023", "P-024", "H-001", "H-002"], "group": "drum", "label": "Shaft + bearings", "detail": f"P-010 ⌀{s.shaft_od:g}″ · J-006 fixed · J-007 float · P-023 jack", "color": "#8a9098", "sheet": "P010_shaft.svg"},
            {"id": "table", "fabIds": ["P-004", "P-005", "P-006"], "group": "table", "label": "Torsion-box table", "detail": "P-004/P-005/P-006 · J-003/J-004", "color": "#cfd3d5", "sheet": "A03_table.svg"},
            {"id": "elev", "fabIds": ["P-016", "P-018", "P-019", "H-007", "H-008"], "group": "table", "label": "Dual Acme lift", "detail": f"Both screws at Y {g.acme_y:g}″ · left clutch · P-019 dog", "color": "#6e7578", "sheet": "P016_nut_block.svg"},
            {"id": "rollers", "fabIds": ["P-014", "H-009"], "group": "table", "label": "Hold-down rollers", "detail": f"P-014 · {s.roller_setbelow:.3f}″ below drum", "color": "#5a6068", "sheet": "A05_holddowns.svg"},
            {"id": "motor", "fabIds": ["P-012", "H-006"], "group": "drive", "label": "Motor + pulleys", "detail": f"{s.motor_hp:g} HP · coplanar {s.pulley_motor_od:g}″/{s.pulley_drum_od:g}″", "color": "#4a5058", "sheet": "A04_drive.svg"},
            {"id": "hood", "fabIds": ["P-011"], "group": "hood", "label": "Dust hood", "detail": "P-011 kerf-bent · 4″ port", "color": "#9aa8a0", "sheet": "P011_hood.svg"},
        ],
        "cutList": [
            {"qty": r["qty"], "size": r["size"], "sizeMm": r["size_mm"], "stock": r["stock"], "use": r["part_id"] + " " + r["use"][:42], "partId": r["part_id"]}
            for r in cut_list()
        ],
        "hardware": hardware_bom(),
        "assembly": assembly_phases(),
        "steps": build_steps(),
        "release": RELEASE_STATE,
        "phases": [
            {"id": "frame", "label": "01 Frame"},
            {"id": "drum", "label": "02 Drum"},
            {"id": "drive", "label": "03 Drive"},
            {"id": "table", "label": "04 Table"},
            {"id": "hood", "label": "05 Hood"},
            {"id": "wrap", "label": "06 Wrap"},
            {"id": "tune", "label": "07 Tune"},
        ],
        "quality": [{"check": q["check"], "spec": q["spec"], "tool": q["tool"]} for q in quality_targets()],
        "calibration": calibration_steps(),
        "passes": pass_schedule(),
        "safety": [
            "Hood ON is the primary guard — open only when stopped and unplugged.",
            "Hold-downs on. Hands never under the drum. ~12″ min length or a sled.",
            "Small parts ride a longer sled (kickback risk).",
            "Light passes only. Back off if the motor bogs.",
            "Eye, hearing, respirator when truing MDF.",
        ],
        "gallery": [
            {
                "src": f"../{d.get('dir', 'plans')}/{d['file']}",
                "title": d["title"],
                "kind": d["kind"],
                "group": d["group"],
                "code": d["code"],
            }
            for d in shop_drawings()
        ],
        "lumberyard": [{"where": r["where"], "item": r["item"], "qty": r["qty"], "use": r["use"]} for r in lumberyard()],
        "fasteners": [{"qty": r["qty"], "item": r["item"], "use": r["use"]} for r in fastener_schedule()[:8]],
        "downloads": [
            {"href": "../pack/WALTER-DS16-RevC.zip", "label": "Shop pack (ZIP)", "note": "Plans, BOM, CAD — Save to Files", "download": "WALTER-DS16-RevC.zip", "share": True, "primary": True},
            {"href": "../guide/", "label": "Master build guide", "note": "The whole book, in order · Print → PDF", "primary": True},
            {"href": "../pocket/", "label": "Pocket field card", "note": "Phone shop floor · Add to Home Screen"},
            {"href": "../pack/BOM.csv", "label": "BOM.csv", "note": "Make + buy with part IDs", "download": "WALTER-DS16-BOM.csv"},
            {"href": "../pack/parts.csv", "label": "parts.csv", "note": "Fabrication register", "download": "WALTER-DS16-parts.csv"},
            {"href": "../pack/joints.csv", "label": "joints.csv", "note": "Joinery schedule", "download": "WALTER-DS16-joints.csv"},
            {"href": "../pack/fasteners.csv", "label": "fasteners.csv", "note": "Hardware-aisle list", "download": "WALTER-DS16-fasteners.csv"},
            {"href": "../pack/lumberyard.csv", "label": "lumberyard.csv", "note": "Store-trip sheet goods", "download": "WALTER-DS16-lumberyard.csv"},
            {"href": "../pack/fabrication.json", "label": "fabrication.json", "note": "Machine-readable SSOT", "download": "WALTER-DS16-fabrication.json"},
            {"href": "../cad/walter_ds16.py", "label": "walter_ds16.py", "note": "Parametric engineering source", "download": "walter_ds16.py"},
            {"href": "../cad/walter_ds16.scad", "label": "walter_ds16.scad", "note": "OpenSCAD solid model", "download": "walter_ds16.scad"},
            {"href": "../model/", "label": "3D viewer", "note": "Orbit / explode"},
            {"href": "../plans/IDX_drawings.svg", "label": "IDX SVG", "note": "Drawing index", "download": "IDX_drawings.svg"},
            {"href": "../plans/P001L_side_drive.svg", "label": "P-001L SVG", "note": "Drive side panel", "download": "P001L_side_drive.svg"},
            {"href": "../plans/H01_hardware.svg", "label": "H-01 SVG", "note": "Illustrated hardware", "download": "H01_hardware.svg"},
            {"href": "../plans/H02_mcmaster.svg", "label": "H-02 SVG", "note": "McMaster procurement", "download": "H02_mcmaster.svg"},
            {"href": "../plans/D11_register.svg", "label": "D-11 SVG", "note": "Part register", "download": "D11_register.svg"},
            {"href": "../plans/D12_joinery.svg", "label": "D-12 SVG", "note": "Joinery & QA", "download": "D12_joinery.svg"},
            {"href": "../", "label": "Design page", "note": "Overview"},
        ],
        "sources": [
            {"label": "Ron Walters drum sander (woodgears)", "href": "https://woodgears.ca/reader/walters/drum_sander.html"},
            {"label": "Walters build walkthrough (YouTube)", "href": "https://youtu.be/W-5Sj6kBVic"},
            {"label": "Simon Heslop variant", "href": "https://woodgears.ca/sander/drum.html"},
            {"label": "Pat Hawley / Wandel free plans", "href": "https://woodgears.ca/sander/plans/"},
        ],
        "tools": [
            "Table saw / track saw",
            "Dado stack or router (J-001, J-002)",
            "Drill press + pack-bore jig P-015",
            "Metal lathe for P-021 plugs (or a machinist). Option B skips the lathe.",
            "Dial indicator 0.001″ + mag base",
            "Feelers / winding sticks / calipers",
            "Clamps · squares",
            "Dust collector 4″",
        ],
    }


def write_exports(shop_root: str | None = None) -> None:
    """Write parameters.scad, geometry.js, data.js, fabrication.json."""
    from pathlib import Path

    cad = Path(__file__).resolve().parent
    shop = Path(shop_root) if shop_root else cad.parent
    errs = validate()
    if errs:
        raise SystemExit("WALTER geometry invalid: " + "; ".join(errs))
    (cad / "parameters.scad").write_text(parameters_scad(), encoding="utf-8")
    (cad / "fabrication.json").write_text(json.dumps(summary(), indent=2) + "\n", encoding="utf-8")
    (shop / "app" / "geometry.js").write_text(geometry_js(), encoding="utf-8")
    js = "/* AUTO-GENERATED from cad/walter_ds16.py — do not edit */\nwindow.WALTER_DATA = "
    js += json.dumps(viewer_data(), indent=2)
    js += ";\n"
    (shop / "app" / "data.js").write_text(js, encoding="utf-8")


if __name__ == "__main__":
    errs = validate()
    if errs:
        raise SystemExit("invalid: " + "; ".join(errs))
    print(json.dumps({
        "ok": True,
        "revision": SPEC.revision,
        "fab": SPEC.fabrication_rev,
        "overall_width": GEOM.overall_width,
        "table_width": GEOM.table_width,
        "way_project": GEOM.way_project,
        "way_rebate": GEOM.way_rebate,
        "stretcher_length": GEOM.stretcher_length,
        "bearing_cl_y": GEOM.bearing_cl_y,
        "table_z_display": GEOM.table_z_display,
        "parts": len(parts()),
        "joints": len(joints()),
        "hardware": len(hardware()),
    }, indent=2))
