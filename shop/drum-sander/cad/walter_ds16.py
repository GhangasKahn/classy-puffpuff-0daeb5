#!/usr/bin/env python3
"""WALTER DS-16 — parametric engineering source for the modern drum thickness sander.

Lineage:
  ShopNotes No. 86 thickness sander (table-saw drive, conveyor feed)
  → Ron Walters dedicated-motor rebuild (Baltic birch + flange bearings)
  → Rev A: solid sliding table, adjustable idler bearing, precision shaft
  → Rev B: dual-end parallelogram lift, ways, hold-downs, floating bearing,
           indicator calibration, optional slow oscillation.

Units: inches unless noted. Mirror these constants in gen_drum_sander_plans.py
and shop/drum-sander/app/data.js.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Spec:
    revision: str = "B"

    # Capacity
    capacity_width: float = 15.5
    min_stock_thickness: float = 0.0625  # 1/16"
    max_stock_thickness: float = 3.0
    min_stock_length: float = 12.0  # with hold-downs; sled for shorter

    # Geometry targets (Rev B quality spec)
    parallel_tol: float = 0.003  # drum-to-table, side-to-side over capacity
    table_flat_tol: float = 0.004  # table wear face, diagonal
    drum_tir: float = 0.002  # TIR after truing, paper off
    paper_on_delta: float = 0.002  # max extra after wrap — re-clock
    pass_rough: float = 0.008
    pass_medium: float = 0.004
    pass_finish: float = 0.001

    # Drum
    drum_od: float = 5.0
    drum_length: float = 15.75  # 21 × 0.75" discs
    disc_thick: float = 0.75
    disc_count_core: int = 19
    disc_count_ends: int = 2
    spacer_every_n: int = 4
    spacer_mm: float = 1.0
    velcro_width: float = 4.0
    sandpaper_width: float = 3.0

    # Shaft & bearings
    shaft_od: float = 0.75
    shaft_length: float = 22.5  # extra for oscillator cam / indicator
    shaft_spec: str = "Precision-ground CRS or TG&P, ¾″, 0.0005″ TIR"
    key_wire_od: float = 0.125
    bearing_drive: str = "4-bolt flange, ¾″ bore, sealed — FIXED"
    bearing_idler: str = "4-bolt flange, ¾″ bore, sealed — FLOATING (axial)"
    bearing_count: int = 2

    # Drive
    motor_hp: float = 0.5
    motor_rpm: float = 1725.0
    pulley_motor_od: float = 3.0
    pulley_drum_od: float = 5.0
    belt: str = "4L / A-section V-belt (size to center distance)"
    drum_rpm: float = 1035.0

    # Frame
    side_thick: float = 0.75
    side_height: float = 30.0
    side_depth: float = 22.0
    clear_between_sides: float = 16.5
    base_thick: float = 0.75
    stretchers: int = 3

    # Table — dual-end lift + ways (Rev B)
    table_thick: float = 1.5
    table_width: float = 16.0
    table_depth: float = 22.0  # longer for hold-down run-out
    table_core: str = "Torsion box: ¾″ skins + ½″ grid, full glue"
    table_top: str = "½″ phenolic or ⅜″ MIC-6 / cast tooling plate"
    elev_screw: str = 'Two ½″-10 Acme × 12″, bronze nuts, #25 chain couple'
    elev_travel: float = 3.25
    way_stock: str = '¾″ × ¾″ UHMW strips, inner faces of sides'
    taper_uncouple: str = "Left sprocket clutch + parallel-home stop"

    # Hold-downs
    roller_od: float = 1.25
    roller_len: float = 15.75
    roller_setbelow: float = 0.030  # below drum OD, paper on
    roller_spring: str = "Light compression; too much = snipe"

    # Oscillation (optional)
    osc_stroke: float = 0.125
    osc_cpm: float = 80.0  # independent slow drive — not drum RPM

    # Dust / guard
    hood_ply: float = 0.25
    dust_port_od: float = 4.0
    hood_method: str = "Kerf-bent ¼″ pine/birch ply, sawdust-glue filled"

    modernizations: tuple[str, ...] = (
        "Dual ½-10 Acme table screws, chain-coupled — coarse lift stays coplanar",
        "Left screw uncouples for taper; dog stop returns to parallel home",
        "UHMW ways on inner sides — table cannot rack while feeding",
        "Stack-drill side panels as a pair; floating idler bearing (axial growth)",
        "Torsion-box table + phenolic / tooling-plate wear face",
        "Spring hold-down rollers infeed + outfeed — kills snipe and chatter",
        "Full-width truing sled; re-clock after paper wrap to ±0.003″",
        "Dial-indicator pad on drive side; 0.001″ pass schedule",
        "Optional ⅛″ slow oscillation (gear motor) to erase spiral tracks",
        "Pack-bore disc jig + static balance of end discs",
    )


SPEC = Spec()


def surface_fpm(drum_od: float, rpm: float) -> float:
    return (3.14159265 * drum_od / 12.0) * rpm


def quality_targets() -> list[dict[str, str]]:
    s = SPEC
    return [
        {"check": "Table flatness", "tool": "Straightedge + feelers on wear face", "spec": f"≤ {s.table_flat_tol:.3f}″ on both diagonals"},
        {"check": "Drum TIR (paper off)", "tool": "Dial indicator on drum OD, mid-span", "spec": f"≤ {s.drum_tir:.3f}″ TIR"},
        {"check": "Drum ∥ table (paper on)", "tool": "Indicator at A (drive) and B (idler)", "spec": f"|A−B| ≤ {s.parallel_tol:.3f}″ over {s.capacity_width}″"},
        {"check": "Way coplanar", "tool": "Winding sticks / indicator on both UHMW", "spec": "No twist; table slides without bind"},
        {"check": "Pulley coplanar", "tool": "Straightedge across both pulley faces", "spec": "Faces flush; belt tracks center"},
        {"check": "Hold-down set", "tool": "Feeler under roller vs drum (paper on)", "spec": f"Rollers {s.roller_setbelow:.3f}″ below drum OD"},
        {"check": "Thickness scatter", "tool": "Caliper 4 corners of test panel", "spec": f"≤ {s.parallel_tol:.3f}″ after finish pass"},
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
    s = SPEC
    span = s.clear_between_sides
    return [
        {"qty": 2, "size": f'{s.side_depth}" × {s.side_height}" × ¾"', "stock": "Baltic birch", "use": "Side panels — stack-drill as a pair"},
        {"qty": 1, "size": f'{span + 2 * s.side_thick}" × {s.side_depth}" × ¾"', "stock": "Baltic birch", "use": "Base deck"},
        {"qty": 3, "size": f'{span}" × 4" × ¾"', "stock": "Baltic birch", "use": "Front / mid / rear stretchers"},
        {"qty": 2, "size": f'{s.table_width}" × {s.table_depth}" × ¾"', "stock": "Baltic birch skins", "use": "Table torsion-box skins"},
        {"qty": 1, "size": '½" grid offcuts', "stock": "BB / MDF", "use": "Torsion-box ribs @ 4″ o.c."},
        {"qty": 1, "size": f'{s.table_width}" × {s.table_depth}" × ½"', "stock": "Phenolic or MIC-6", "use": "Replaceable wear face"},
        {"qty": 2, "size": f'¾" × ¾" × {s.side_depth}"', "stock": "UHMW", "use": "Table ways (inner faces)"},
        {"qty": s.disc_count_core + s.disc_count_ends, "size": f'⌀{s.drum_od + 0.125}" × ¾" (true to ⌀{s.drum_od}")', "stock": "MDF core + BB ends (or all BB)", "use": "Drum discs — pack-bore"},
        {"qty": 1, "size": f'{s.shaft_length}" × ⌀¾"', "stock": s.shaft_spec, "use": "Drum shaft"},
        {"qty": 1, "size": '~18" × 12" × ¼"', "stock": "Pine or birch ply", "use": "Kerf-bent dust hood blank"},
        {"qty": 1, "size": '12" × 8" × ¾"', "stock": "Baltic birch", "use": "Motor pivot cradle"},
        {"qty": 1, "size": f'{s.table_width}" × 8" × ¾"', "stock": "MDF / BB", "use": "Full-width truing sled"},
        {"qty": 2, "size": f'yoke 18" × 3" × ¾"', "stock": "Hardwood / alum angle", "use": "Hold-down roller yokes"},
        {"qty": 1, "size": '12" × 12" × ¾"', "stock": "MDF", "use": "Disc pack-bore jig"},
    ]


def hardware_bom() -> list[dict[str, str]]:
    s = SPEC
    return [
        {"item": s.bearing_drive, "qty": "1"},
        {"item": s.bearing_idler, "qty": "1"},
        {"item": f'{s.pulley_motor_od}" motor + {s.pulley_drum_od}" drum 4L pulleys', "qty": "1 set"},
        {"item": s.belt, "qty": "1"},
        {"item": f'{s.motor_hp:g} HP {s.motor_rpm:g} RPM TEFC motor, 115 V', "qty": "1"},
        {"item": '½″-10 Acme rod 12″ + bronze nut + flange', "qty": "2"},
        {"item": "#25 sprockets (½″ bore) + chain + master link", "qty": "2 + loop"},
        {"item": "Left sprocket clutch / set-screw dog for parallel-home", "qty": "1"},
        {"item": f'Rubber rollers ⌀{s.roller_od}" × ~{s.roller_len}" + ⅜″ axles', "qty": "2"},
        {"item": "Compression springs + shoulder bolts for yokes", "qty": "4"},
        {"item": "Star knobs ⅜-16 + washers (way locks / yokes)", "qty": "6"},
        {"item": 'Hook Velcro 4" PSA + 3" loop sandpaper (80/120/180/220)', "qty": "as needed"},
        {"item": '⅛" piano wire for shaft keys', "qty": "12 in"},
        {"item": '4" dust adapter + blast gate', "qty": "1"},
        {"item": "Switch box + 15 ft cord", "qty": "1"},
        {"item": "Dial indicator 0.001″ + mag base (or ⅜-16 pad)", "qty": "1"},
        {"item": "Optional: 60–90 RPM gearmotor + scotch yoke (oscillator)", "qty": "1 kit"},
    ]


def assembly_phases() -> list[dict[str, str]]:
    return [
        {"id": "a1", "phase": "frame", "title": "Template & stack-drill sides",
         "body": "Clamp both side panels face-to-face. Drill bearing CLs, way screw holes, and indicator pad as one stack so left and right are identical."},
        {"id": "a2", "phase": "frame", "title": "Assemble box + UHMW ways",
         "body": "Glue + screw stretchers. Square diagonals. Bond UHMW ways to inner faces; they are the table’s only vertical reference."},
        {"id": "a3", "phase": "drum", "title": "Pack-bore discs & laminate drum",
         "body": "Bandsaw oversize. Stack all discs in the bore jig; drill/ream ⌀¾″ as a pack. Key with piano wire. 1 mm relief every 4 MDF discs. Static-balance end discs."},
        {"id": "a4", "phase": "drum", "title": "Fixed drive bearing, floating idler",
         "body": "Lock the drive flange. Idler flange sits on an axial-float pad (slots or liner) so the shaft cannot banana from over-constraint or heat."},
        {"id": "a5", "phase": "drive", "title": "Motor cradle, coplanar pulleys, lock",
         "body": "Straightedge across pulley faces. Gravity tension, then lock the cradle so the belt cannot pump."},
        {"id": "a6", "phase": "table", "title": "Torsion-box table + wear face",
         "body": "Skins + 4″ rib grid, continuous glue. Flatten the top, then bond phenolic or tooling plate. Check diagonals to 0.004″."},
        {"id": "a7", "phase": "table", "title": "Dual Acme lift + chain couple",
         "body": "Bronze nuts in table. Chain both ½-10 screws. Fit left clutch and parallel-home dog. Table must rise without twist in the ways."},
        {"id": "a8", "phase": "table", "title": "Hold-down roller yokes",
         "body": "Infeed and outfeed rollers on spring yokes. Set 0.030″ below drum OD (paper on). Too much spring = snipe."},
        {"id": "a9", "phase": "hood", "title": "Kerf-bend dust hood",
         "body": "Kerf ¼″ ply, wet, glue to form, fill kerfs. 4″ port. Hood must clear oscillator stroke if fitted."},
        {"id": "a10", "phase": "wrap", "title": "True drum on full-width sled",
         "body": "Abrasive face-up on the truing sled that rides the ways. Light passes until TIR ≤ 0.002″. Then Velcro + spiral paper."},
        {"id": "a11", "phase": "tune", "title": "Indicator clock A/B — parallel home",
         "body": "Paper on. Indicator at drive (A) and idler (B). Uncouple left screw until |A−B| ≤ 0.003″. Lock home dog. Record the reading."},
        {"id": "a12", "phase": "tune", "title": "Test panel + pass schedule",
         "body": "80 / 120 / 180. Caliper four corners. If scatter > 0.003″, re-clock. Finish at 0.001″. Optional oscillator last."},
    ]


def calibration_steps() -> list[dict[str, str]]:
    return [
        {"id": "c1", "title": "Disconnect power", "body": "Unplug. Hood off. Paper off for TIR; paper on for A/B parallel."},
        {"id": "c2", "title": "Seat the table in the ways", "body": "Raise/lower through full travel. No bind, no rock. Winding sticks on wear face — no twist."},
        {"id": "c3", "title": "Drum TIR", "body": "Indicator on mid-span OD. Rotate by hand. If > 0.002″, re-true on the sled before wrapping paper."},
        {"id": "c4", "title": "Wrap & re-clock", "body": "Velcro then spiral paper. Paper is not uniform — A/B will change. This is the measurement that matters."},
        {"id": "c5", "title": "A/B parallel", "body": "Same indicator height, drive end then idler. Uncouple left Acme; 1/40 turn ≈ 0.0025″. Recouple. Set home dog."},
        {"id": "c6", "title": "Hold-down height", "body": "Feelers under each roller vs drum. 0.030″ below. Leading snipe → ease outfeed spring; trailing snipe → ease infeed."},
        {"id": "c7", "title": "Witness board", "body": "6″ × 16″ maple, 80 grit, one pass. Ridge at overlap = idler high/low. Caliper corners. Log in the Build app."},
        {"id": "c8", "title": "Taper mode (optional)", "body": "Uncouple left, drop idler a few thousandths, sand, then return to home dog — do not re-invent parallel each time."},
    ]


def summary() -> dict[str, Any]:
    s = SPEC
    return {
        "name": "WALTER DS-16",
        "revision": s.revision,
        "lineage": "ShopNotes 86 → Ron Walters → Rev A solid table → Rev B geometry",
        "capacity": f'{s.capacity_width}" wide · {s.min_stock_thickness}"–{s.max_stock_thickness}" thick',
        "drum_rpm": s.drum_rpm,
        "surface_fpm": round(surface_fpm(s.drum_od, s.drum_rpm), 0),
        "parallel_tol": s.parallel_tol,
        "spec": asdict(s),
        "quality": quality_targets(),
        "passes": pass_schedule(),
        "cut_list": cut_list(),
        "hardware": hardware_bom(),
        "assembly": assembly_phases(),
        "calibration": calibration_steps(),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(summary(), indent=2))
