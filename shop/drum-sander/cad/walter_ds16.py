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

Units: inches internally. Convert only at export.
Evidence: VERIFIED (spec), DERIVED (equation), ASSUMED (layout), ESTIMATED.

PARAMETER → GEOMETRY → METADATA → DRAWINGS → BOM → CUT LIST → BUILD DOCS
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

IN_TO_MM = 25.4
PI = 3.14159265

# ---------------------------------------------------------------------------
# 0. Project
# ---------------------------------------------------------------------------

PROJECT = {
    "project_id": "WALTER-DS16",
    "project_name": "WALTER DS-16 dedicated drum thickness sander",
    "revision": "B",
    "fabrication_rev": "B.2",
    "units": "inch",
    "unit_policy": "Internal inches. Millimetres are interface-only.",
    "design_standard": "Shop woodworking T1 / joinery T2 / metrology T4 on A/B",
    "material_system": "Baltic birch + MDF drum + UHMW ways + phenolic wear",
    "tolerance_class": "T2 joinery, T4 drum/table metrology",
    "author": "WALTER fabrication model",
    "model_version": "B.2",
    "cad_platform": "Python SSOT + OpenSCAD solids + SVG shop drawings",
    "lineage": "ShopNotes 86 → Ron Walters → Rev A solid table → Rev B geometry",
}


@dataclass(frozen=True)
class Spec:
    """Controlling inputs. Dependent sizes live in Geom, not here."""

    revision: str = "B"
    fabrication_rev: str = "B.2"

    # Capacity — VERIFIED design intent
    capacity_width: float = 15.5
    min_stock_thickness: float = 0.0625
    max_stock_thickness: float = 3.0
    min_stock_length: float = 12.0
    table_margin_each: float = 0.25  # table wider than work, each side

    # Quality — VERIFIED Rev B spec
    parallel_tol: float = 0.003
    table_flat_tol: float = 0.004
    drum_tir: float = 0.002
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

    # Shaft — VERIFIED
    shaft_od: float = 0.75
    shaft_length: float = 22.5
    shaft_spec: str = "Precision-ground CRS or TG&P, ¾″, 0.0005″ TIR"
    key_wire_od: float = 0.125
    bearing_drive: str = '4-bolt flange, ¾″ bore, sealed — FIXED'
    bearing_idler: str = '4-bolt flange, ¾″ bore, sealed — FLOATING (axial)'
    bearing_count: int = 2
    idler_float_slot: float = 0.25  # axial slot, ASSUMED shopable

    # Drive — VERIFIED
    motor_hp: float = 0.5
    motor_rpm: float = 1725.0
    pulley_motor_od: float = 3.0
    pulley_drum_od: float = 5.0
    belt: str = "4L / A-section V-belt (size to center distance)"
    drum_rpm: float = 1035.0

    # Frame — inner span is the constraint, even with 18 mm Euro BB
    ply_nominal: float = 0.75
    ply_actual: float = 0.75  # USER_MEASURE; 18 mm Euro ≈ 0.709
    side_height: float = 30.0
    side_depth: float = 22.0
    clear_between_sides: float = 16.5
    base_thick: float = 0.75
    stretcher_count: int = 3
    stretcher_height: float = 4.0
    stretcher_housing: float = 0.25  # dado into each side, DERIVED joinery
    stretcher_z: tuple = (6.0, 12.0, 20.0)

    # Ways — stock vs projecting (table must actually fit)
    way_stock: float = 0.75
    slide_clearance: float = 0.020  # T1 sliding, UHMW
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
    acme_inset_y: float = 4.0  # from infeed / outfeed edges
    acme_inset_x: float = 2.4  # from inner face toward center

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
    way_z: float = 10.0  # bottom of UHMW from floor
    way_end_inset: float = 1.0  # rebate stops short of infeed/outfeed edges
    display_gap_under_drum: float = 0.50  # viz opening, not min capacity

    # Hole / cut patterns on P-001 (ASSUMED until flange BCD is USER_CONFIRM)
    flange_bolt_square: float = 2.05  # 4-bolt square CTC, typical ¾″ 4-bolt flange
    flange_bolt_clr: float = 0.344  # 11/32″ for 5/16-18
    ply_shaft_clear_dia: float = 1.125  # shaft must not rub the plywood
    motor_pivot_dia: float = 0.266  # F / 17/64 for ¼-20
    indicator_pad_y: float = 8.0  # drive side only, from infeed
    indicator_pad_z: float = 16.0
    indicator_pad_dia: float = 0.201  # #7 tap-drill for ¼-20
    stretcher_dado_y0: float = 2.0  # inner-face housing, from infeed (matches OpenSCAD)
    stretcher_screw_inset: float = 0.75  # from dado Y ends, through from outside
    idler_float_pad: float = 0.25  # UHMW pad under H-002; axial, not YZ slots

    # Jigs
    cradle_w: float = 12.0
    cradle_h: float = 8.0
    sled_depth: float = 8.0
    bore_jig: float = 12.0

    modernizations: tuple[str, ...] = (
        "Dual ½-10 Acme table screws, chain-coupled — coarse lift stays coplanar",
        "Left screw uncouples for taper; dog stop returns to parallel home",
        "UHMW ways let into side rebates — table cannot rack, and still fits",
        "Housed stretchers (¼″ dados) + through-screws for racking stiffness",
        "Stack-drill side panels as a pair; floating idler bearing (axial pad, not YZ slots)",
        "Torsion-box table + phenolic / tooling-plate wear face",
        "Spring hold-down rollers infeed + outfeed — kills snipe and chatter",
        "Full-width truing sled; re-clock after paper wrap to ±0.003″",
        "Dial-indicator pad on drive side; 0.001″ pass schedule",
        "Optional ⅛″ slow oscillation (gear motor) to erase spiral tracks",
        "Pack-bore disc jig + static balance of end discs",
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
    acme_y_infeed: float
    acme_y_outfeed: float
    acme_x_left: float
    acme_x_right: float
    acme_per_turn: float
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
    roller_len = drum_length
    roller_z = table_z_display + table_thick + s.roller_od / 2.0 + s.roller_setbelow
    drum_end_gap = (s.clear_between_sides - drum_length) / 2.0
    sfpm = (PI * s.drum_od / 12.0) * s.drum_rpm
    eqs = {
        "overall_width": "clear_between_sides + 2 × ply_actual",
        "table_width": "capacity_width + 2 × table_margin_each",
        "way_project": "(clear_between_sides − table_width) / 2 − slide_clearance",
        "way_rebate": "way_stock − way_project  (let into inner face so table fits)",
        "stretcher_length": "clear_between_sides + 2 × stretcher_housing",
        "drum_length": "(disc_count_core + disc_count_ends) × disc_thick",
        "bearing_cl_y": "side_depth / 2  (datum: infeed edge of side)",
        "drum_bottom_z": "bearing_cl_z − drum_od / 2",
        "table_z_at_max_stock": "drum_bottom_z − max_stock − table_thick",
        "table_z_at_min_stock": "drum_bottom_z − min_stock − table_thick",
        "acme_y_outfeed": "side_depth − acme_inset_y",
        "acme_per_turn": "1 / acme_tpi",
        "surface_fpm": "π × drum_od / 12 × drum_rpm",
        "drum_end_gap": "(clear_between_sides − drum_length) / 2",
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
        acme_y_infeed=s.acme_inset_y,
        acme_y_outfeed=s.side_depth - s.acme_inset_y,
        acme_x_left=acme_x_left,
        acme_x_right=acme_x_right,
        acme_per_turn=1.0 / s.acme_tpi,
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
            "y0": s.stretcher_dado_y0,
            "y1": s.stretcher_dado_y0 + s.stretcher_height,
            "z0": z,
            "z1": z + s.ply_actual,
            "depth": s.stretcher_housing,
        }
        for i, z in enumerate(s.stretcher_z)
    ]
    way = {
        "id": "J-002",
        "y0": s.way_end_inset,
        "y1": s.side_depth - s.way_end_inset,
        "z0": s.way_z,
        "z1": s.way_z + s.way_stock,
        "depth": g.way_rebate,
        "project": g.way_project,
    }
    screws = []
    for i, d in enumerate(dados):
        for j, y in enumerate((d["y0"] + s.stretcher_screw_inset, d["y1"] - s.stretcher_screw_inset)):
            screws.append({
                "id": f"SS{i+1}{chr(97+j)}",
                "y": y,
                "z": (d["z0"] + d["z1"]) / 2.0,
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
            "dados": "DERIVED from stretcher_z / stretcher_dado_y0",
            "way": "DERIVED J-002",
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
            handed="IDENTICAL", viz="base", sheet="P003_stretcher.svg",
            notes="Do not use stretchers as the table datum — ways are the datum.",
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
            material="UHMW-PE", t=s.way_stock, w=s.way_stock, l=s.side_depth,
            purchase='¾" × ¾" UHMW bar, 48" buys both + spare',
            process="Cut to side depth; let into J-002 rebate; bond + wax",
            joinery="J-002 rebate + glue; optional #8 flush screws from outer face",
            handed="IDENTICAL", viz="ways", sheet="P007_uhmw_way.svg",
            notes=f"Projects {g.way_project:.3f}″ past inner face. Rebate {g.way_rebate:.3f}″.",
            evidence="DERIVED project/rebate so 16″ table fits in 16.5″ span",
        ),
        _part(
            "P-008", "Drum disc, core", s.disc_count_core,
            category="disc", assembly="A-DRUM", make="MAKE",
            material="MDF", t=s.disc_thick, w=g.drum_oversize_od, l=g.drum_oversize_od,
            purchase='¾" MDF, bandsaw ⌀5⅛″',
            process="Bandsaw oversize, pack-bore ⌀¾″, true on sled to ⌀5″",
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
            purchase='¾" TG&P × 24", cut to 22.5"',
            process="Cut to length; ⅛″ key slots; TIR ≤ 0.0005″ incoming",
            joinery="J-005 discs; J-006 fixed drive flange; J-007 floating idler",
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
            process="Fence + clamp wall; drill/ream ⌀¾″ through the pack",
            joinery="none", handed="IDENTICAL", viz="drum", sheet="P015_pack_bore.svg",
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
    ]


def hardware(s: Spec = SPEC, g: Geom = GEOM) -> list[dict[str, Any]]:
    return [
        {"hardware_id": "H-001", "description": '4-bolt flange bearing, ¾″ bore, sealed, FIXED (drive)', "standard": "2-bolt/4-bolt flange", "size": '¾" bore', "qty": 1, "make_or_buy": "BUY", "assembly": "A-DRUM", "notes": "Lock to P-001L. No axial float."},
        {"hardware_id": "H-002", "description": '4-bolt flange bearing, ¾″ bore, sealed, FLOATING (idler)', "standard": "4-bolt flange", "size": '¾" bore', "qty": 1, "make_or_buy": "BUY", "assembly": "A-DRUM", "notes": f"Axial float on a {s.idler_float_pad:g}″ UHMW pad (J-007). Do not elongate flange holes in the plywood face."},
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
    ]


def joints(s: Spec = SPEC, g: Geom = GEOM) -> list[dict[str, Any]]:
    return [
        {
            "joint_id": "J-001",
            "joint_type": "housed dado + screw",
            "part_a": "P-001L / P-001R",
            "part_b": "P-003",
            "qty": 6,
            "location": f"Inner faces; Y {s.stretcher_dado_y0:g}–{s.stretcher_dado_y0 + s.stretcher_height:g}″ from infeed; Z bottoms {s.stretcher_z}",
            "dado_width": s.ply_actual,
            "dado_depth": s.stretcher_housing,
            "fit_class": "GLUE",
            "assembly_direction": "stretchers into dados, then through-screws from outside",
            "grain": "Plywood — no seasonal panel lock",
            "notes": "Racking stiffness. Ways, not stretchers, locate the table.",
        },
        {
            "joint_id": "J-002",
            "joint_type": "rebate + bond",
            "part_a": "P-001L / P-001R",
            "part_b": "P-007",
            "qty": 2,
            "location": f"Inner face, way bottom Z = {s.way_z:g}″, full depth",
            "rebate_depth": g.way_rebate,
            "rebate_width": s.way_stock,
            "project": g.way_project,
            "fit_class": "GLUE",
            "constraint": "FIXED to side; table is SLIDING on way",
            "notes": "Without the rebate a ¾″ way would steal 1.5″ and the 16″ table would not fit.",
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
            "notes": "Both nuts; chain-coupled rotation.",
        },
    ]


def assemblies() -> list[dict[str, Any]]:
    return [
        {"assembly_id": "A-MASTER", "name": "WALTER DS-16", "children": ["A-FRAME", "A-DRUM", "A-DRIVE", "A-TABLE", "A-HOOD", "A-JIG"]},
        {"assembly_id": "A-FRAME", "name": "Box + ways", "parts": ["P-001L", "P-001R", "P-002", "P-003", "P-007"], "stage": "glue-up"},
        {"assembly_id": "A-DRUM", "name": "Drum + shaft + bearings", "parts": ["P-008", "P-009", "P-010", "H-001", "H-002"]},
        {"assembly_id": "A-DRIVE", "name": "Motor + pulleys", "parts": ["P-012", "H-003", "H-004", "H-005", "H-006"]},
        {"assembly_id": "A-TABLE", "name": "Table + lift + hold-downs", "parts": ["P-004", "P-005", "P-006", "P-014", "P-016", "H-007", "H-008", "H-009"]},
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
        {"op": "S-006", "title": "Dado: stretcher housing", "tool": "Dado / router", "setting": f'depth {s.stretcher_housing:g}" · width {s.ply_actual:g}"', "parts": ["P-001L", "P-001R"], "ref": "Inner face. Datum Y0 = infeed edge."},
        {"op": "S-007", "title": "Rebate: way", "tool": "Router + edge guide", "setting": f'depth {g.way_rebate:.3f}" · width {s.way_stock:g}"', "parts": ["P-001L", "P-001R"], "ref": "Inner face. Way bottom from floor datum."},
        {"op": "S-008", "title": "Stack-drill bearing CL", "tool": "Drill press, sides clamped face-to-face", "setting": f'Y {g.bearing_cl_y:g}" from infeed · Z {g.bearing_cl_z:g}" from bottom', "parts": ["P-001L+R"], "rule": "One stack. Then split for inner-face dados."},
        {"op": "S-009", "title": "Pack-bore discs", "tool": "P-015 jig + drill/ream", "setting": f'⌀{s.shaft_od:g}"', "parts": ["P-008", "P-009"]},
        {"op": "S-010", "title": "True drum", "tool": "P-013 sled on ways", "setting": f'TIR ≤ {s.drum_tir:.3f}"', "parts": ["A-DRUM"]},
        {"op": "S-011", "title": "A/B clock", "tool": "H-021 indicator", "setting": f'|A−B| ≤ {s.parallel_tol:.3f}" paper on', "parts": ["A-TABLE", "A-DRUM"]},
    ]


def inspection(s: Spec = SPEC, g: Geom = GEOM) -> list[dict[str, Any]]:
    return [
        {"qc": "QC-01", "check": "Ply thickness", "spec": f"Measure ply_actual (default {s.ply_actual:g}\"). Keep inner span {s.clear_between_sides:g}″.", "class": "T1", "gate": "M0"},
        {"qc": "QC-02", "check": "Paired sides", "spec": "P-001L/R identical hole pattern after stack-drill", "class": "T2", "gate": "M4"},
        {"qc": "QC-03", "check": "Box diagonals", "spec": "Base diagonals equal; no rack", "class": "T2", "gate": "M5"},
        {"qc": "QC-04", "check": "Way coplanar", "spec": "Winding sticks / indicator on both UHMW — no twist", "class": "T3", "gate": "M5"},
        {"qc": "QC-05", "check": "Table flatness", "spec": f"≤ {s.table_flat_tol:.3f}″ on both diagonals of P-006", "class": "T3", "gate": "M7"},
        {"qc": "QC-06", "check": "Drum TIR paper off", "spec": f"≤ {s.drum_tir:.3f}″ mid-span", "class": "T4", "gate": "M7"},
        {"qc": "QC-07", "check": "Drum ∥ table paper on", "spec": f"|A−B| ≤ {s.parallel_tol:.3f}″ over {s.capacity_width:g}″", "class": "T4", "gate": "M7"},
        {"qc": "QC-08", "check": "Hold-down set", "spec": f"Rollers {s.roller_setbelow:.3f}″ below drum OD, paper on", "class": "T2", "gate": "M7"},
        {"qc": "QC-09", "check": "Pulley coplanar", "spec": "Straightedge across both pulley faces", "class": "T2", "gate": "M5"},
        {"qc": "QC-10", "check": "Thickness scatter", "spec": f"≤ {s.parallel_tol:.3f}″ on four corners of witness board", "class": "T4", "gate": "M7"},
        {"qc": "QC-11", "check": "Idler float", "spec": "Shaft can grow axially; no banana preload", "class": "T2", "gate": "M3"},
        {"qc": "QC-12", "check": "Way/table fit", "spec": f"Table slides; project {g.way_project:.3f}″; clearance {s.slide_clearance:.3f}″/side", "class": "T2", "gate": "M4"},
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
    ]


def revisions() -> list[dict[str, str]]:
    return [
        {"rev": "A", "note": "Solid sliding table, no conveyor, adjustable idler, precision shaft"},
        {"rev": "B", "note": "Dual-end lift, UHMW ways, hold-downs, floating bearing, paper-on A/B ±0.003″"},
        {"rev": "B.1", "note": "Fabrication model: part/joint IDs, housed stretchers, way rebate so table fits, derived geometry, JSON/CSV SSOT"},
        {"rev": "B.2", "note": "Individual Wandel-style part/assembly/hardware sheets; named hole patterns; idler axial pad (not YZ slots)"},
    ]


def datums(s: Spec = SPEC, g: Geom = GEOM) -> list[dict[str, str]]:
    return [
        {"id": "DATUM-A", "on": "P-001L/R", "what": "Bottom edge", "use": "Z = 0 floor / base top after install"},
        {"id": "DATUM-B", "on": "P-001L/R", "what": "Infeed edge", "use": "Y = 0; bearing_cl_y measured from here"},
        {"id": "DATUM-C", "on": "P-001L/R", "what": "Inner face", "use": "X local; dados and way rebate"},
        {"id": "DATUM-D", "on": "P-006", "what": "Wear-face top", "use": "Table plane; A/B indicator reference"},
        {"id": "DATUM-E", "on": "P-010", "what": "Drum axis", "use": "Fixed by H-001; TIR and parallel"},
    ]


# ---------------------------------------------------------------------------
# 3. Shop lists (derived from registry — do not independently hard-code sizes)
# ---------------------------------------------------------------------------

def quality_targets() -> list[dict[str, str]]:
    s, g = SPEC, GEOM
    return [
        {"check": "Table flatness", "tool": "Straightedge + feelers on wear face", "spec": f"≤ {s.table_flat_tol:.3f}″ on both diagonals", "qc": "QC-05"},
        {"check": "Drum TIR (paper off)", "tool": "Dial indicator on drum OD, mid-span", "spec": f"≤ {s.drum_tir:.3f}″ TIR", "qc": "QC-06"},
        {"check": "Drum ∥ table (paper on)", "tool": "Indicator at A (drive) and B (idler)", "spec": f"|A−B| ≤ {s.parallel_tol:.3f}″ over {s.capacity_width}″", "qc": "QC-07"},
        {"check": "Way coplanar", "tool": "Winding sticks / indicator on both UHMW", "spec": "No twist; table slides without bind", "qc": "QC-04"},
        {"check": "Pulley coplanar", "tool": "Straightedge across both pulley faces", "spec": "Faces flush; belt tracks center", "qc": "QC-09"},
        {"check": "Hold-down set", "tool": "Feeler under roller vs drum (paper on)", "spec": f"Rollers {s.roller_setbelow:.3f}″ below drum OD", "qc": "QC-08"},
        {"check": "Thickness scatter", "tool": "Caliper 4 corners of test panel", "spec": f"≤ {s.parallel_tol:.3f}″ after finish pass", "qc": "QC-10"},
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
        {"where": "Plastics", "item": "UHMW bar ¾″ × ¾″", "qty": "48″", "alt": "Two 24″ sticks", "use": "P-007 ways, let into J-002 rebate"},
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
        {"id": "a2", "phase": "frame", "title": "Dados, way rebates, box + UHMW",
         "body": f"Split the pair. Dado J-001 ({SPEC.stretcher_housing:g}″) and rebate J-002 ({GEOM.way_rebate:.3f}″) on inner faces only. Glue P-003, square diagonals, bond P-007."},
        {"id": "a3", "phase": "drum", "title": "Pack-bore discs & laminate drum",
         "body": "Bandsaw P-008/P-009 oversize. Stack in P-015; ream ⌀¾″ as a pack (J-005). Key, 1 mm MDF relief, static-balance P-009."},
        {"id": "a4", "phase": "drum", "title": "Fixed drive bearing, floating idler",
         "body": "H-001 locked on P-001L (J-006). H-002 on axial-float slots on P-001R (J-007)."},
        {"id": "a5", "phase": "drive", "title": "Motor cradle, coplanar pulleys, lock",
         "body": "Straightedge across H-003/H-004. Gravity tension, lock P-012 (J-008)."},
        {"id": "a6", "phase": "table", "title": "Torsion-box table + wear face",
         "body": f"P-004 + P-005 @ {SPEC.table_rib_oc:g}″ o.c., glue. Flatten. Bond P-006. Diagonals ≤ {SPEC.table_flat_tol:.3f}″."},
        {"id": "a7", "phase": "table", "title": "Dual Acme lift + chain couple",
         "body": "P-016 + H-007. H-008 chain. Left clutch + home dog. Table must rise in the ways without twist."},
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


def calibration_steps() -> list[dict[str, str]]:
    s = SPEC
    return [
        {"id": "c1", "title": "Disconnect power", "body": "Unplug. Hood off. Paper off for TIR; paper on for A/B parallel."},
        {"id": "c2", "title": "Seat the table in the ways", "body": "Raise/lower through full travel. No bind, no rock. Winding sticks on wear face — no twist."},
        {"id": "c3", "title": "Drum TIR", "body": f"Indicator on mid-span OD. Rotate by hand. If > {s.drum_tir:.3f}″, re-true on P-013 before wrapping."},
        {"id": "c4", "title": "Wrap & re-clock", "body": "Velcro then spiral paper. Paper is not uniform — A/B will change. This is the measurement that matters."},
        {"id": "c5", "title": "A/B parallel", "body": f"Same indicator height, drive then idler. Uncouple left Acme; 1/{s.acme_tpi:g} turn ≈ {GEOM.acme_per_turn:.4f}″. Recouple. Set home dog."},
        {"id": "c6", "title": "Hold-down height", "body": f"Feelers under each roller vs drum. {s.roller_setbelow:.3f}″ below. Leading snipe → ease outfeed spring; trailing → ease infeed."},
        {"id": "c7", "title": "Witness board", "body": "6″ × 16″ maple, 80 grit, one pass. Ridge at overlap = idler high/low. Caliper corners. Log in the Build app."},
        {"id": "c8", "title": "Taper mode (optional)", "body": "Uncouple left, drop idler a few thousandths, sand, then return to home dog — do not re-invent parallel each time."},
    ]


def fmea() -> list[dict[str, str]]:
    return [
        {"mode": "Table rack under feed", "cause": "Butt stretchers / proud ways", "effect": "Tapered cut, bind", "mitigation": "J-001 housing + J-002 rebate ways", "sev": "H"},
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
    spec_d.pop("stretcher_z", None)
    spec_d["stretcher_z"] = list(s.stretcher_z)
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
        f"way_z = {s.way_z};",
        f"stretcher_h = {s.stretcher_height};",
        f"stretcher_len = {g.stretcher_length};",
        f"stretcher_housing = {s.stretcher_housing};",
        f"stretcher_dado_y0 = {s.stretcher_dado_y0};",
        f"flange_bolt_square = {s.flange_bolt_square};",
        f"flange_bolt_clr = {s.flange_bolt_clr};",
        f"ply_shaft_clear_dia = {s.ply_shaft_clear_dia};",
        f"motor_pivot_y = {s.motor_pivot_y};",
        f"motor_pivot_z = {s.motor_pivot_z};",
        f"way_end_inset = {s.way_end_inset};",
        f"idler_float_pad = {s.idler_float_pad};",
        f"acme_y0 = {g.acme_y_infeed};",
        f"acme_y1 = {g.acme_y_outfeed};",
        f"acme_x0 = {g.acme_x_left};",
        f"acme_x1 = {g.acme_x_right};",
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
        "wayZ": s.way_z,
        "stretcherLen": g.stretcher_length,
        "stretcherH": s.stretcher_height,
        "stretcherZ": list(s.stretcher_z),
        "acmeX0": g.acme_x_left,
        "acmeX1": g.acme_x_right,
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
        {"code": "A-01", "file": "A01_frame.svg", "title": "A-01 Frame assembly", "kind": "assembly", "group": "assembly"},
        {"code": "A-02", "file": "A02_drum.svg", "title": "A-02 Drum assembly", "kind": "assembly", "group": "assembly"},
        {"code": "A-03", "file": "A03_table.svg", "title": "A-03 Table assembly", "kind": "assembly", "group": "assembly"},
        {"code": "A-04", "file": "A04_drive.svg", "title": "A-04 Drive assembly", "kind": "assembly", "group": "assembly"},
        {"code": "A-05", "file": "A05_holddowns.svg", "title": "A-05 Hold-downs", "kind": "assembly", "group": "assembly"},
        {"code": "H-01", "file": "H01_hardware.svg", "title": "H-01 Hardware", "kind": "hardware", "group": "hardware"},
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
            {"id": "ways", "fabIds": ["P-007"], "group": "frame", "label": "UHMW ways P-007", "detail": f"Rebate {g.way_rebate:.3f}″ · project {g.way_project:.3f}″ · J-002", "color": "#d9dcde", "sheet": "P007_uhmw_way.svg"},
            {"id": "base", "fabIds": ["P-002", "P-003"], "group": "frame", "label": "Base + stretchers", "detail": f"P-003 housed {g.stretcher_length:g}″ · J-001", "color": "#a89070", "sheet": "A01_frame.svg"},
            {"id": "drum", "fabIds": ["P-008", "P-009"], "group": "drum", "label": "Sanding drum", "detail": f"⌀{s.drum_od:g}″ × {g.drum_length:g}″ · pack-bored · P-008/P-009", "color": "#b8a990", "sheet": "A02_drum.svg"},
            {"id": "shaft", "fabIds": ["P-010", "H-001", "H-002"], "group": "drum", "label": "Shaft + bearings", "detail": "P-010 · J-006 fixed · J-007 float", "color": "#8a9098", "sheet": "P010_shaft.svg"},
            {"id": "table", "fabIds": ["P-004", "P-005", "P-006"], "group": "table", "label": "Torsion-box table", "detail": "P-004/P-005/P-006 · J-003/J-004", "color": "#cfd3d5", "sheet": "A03_table.svg"},
            {"id": "elev", "fabIds": ["P-016", "H-007", "H-008"], "group": "table", "label": "Dual Acme lift", "detail": "H-007/H-008 · left clutch · home dog", "color": "#6e7578", "sheet": "P016_nut_block.svg"},
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
            {"href": "../pack/WALTER-DS16-RevB.zip", "label": "Shop pack (ZIP)", "note": "Plans, BOM, CAD — Save to Files", "download": "WALTER-DS16-RevB.zip", "share": True, "primary": True},
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
