#!/usr/bin/env python3
"""WALTER DS-16 — parametric engineering source for the modern drum thickness sander.

Lineage:
  ShopNotes No. 86 thickness sander (table-saw drive, conveyor feed)
  → Ron Walters dedicated-motor rebuild (Baltic birch + flange bearings)
  → This Rev A: solid sliding table, adjustable idler bearing, precision shaft,
     birch or spaced-MDF drum, lockable gravity motor mount, printable plans.

Units: inches unless noted. Mirror these constants in gen_drum_sander_plans.py
and shop/drum-sander/app/data.js.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Spec:
    # Capacity
    capacity_width: float = 15.5
    min_stock_thickness: float = 0.0625  # 1/16"
    max_stock_thickness: float = 3.0
    min_stock_length: float = 12.0  # manual push — keep hands clear

    # Drum
    drum_od: float = 5.0
    drum_length: float = 15.75  # 21 × 0.75" discs
    disc_thick: float = 0.75
    disc_count_core: int = 19  # MDF or Baltic birch
    disc_count_ends: int = 2  # Baltic birch retainers (screwed or glued)
    spacer_every_n: int = 4  # 1 mm relief every N discs (MDF crack control)
    spacer_mm: float = 1.0
    velcro_width: float = 4.0
    sandpaper_width: float = 3.0  # spiral wrap; overlap hides gaps

    # Shaft & bearings
    shaft_od: float = 0.75
    shaft_length: float = 22.0  # drum + bearings + pulley overhang
    shaft_spec: str = "Precision-ground CRS or TG&P, ¾″"
    key_wire_od: float = 0.125  # piano wire cross-pins
    bearing_type: str = "4-bolt flange, ¾″ bore, sealed"
    bearing_count: int = 2

    # Drive
    motor_hp: float = 0.5  # bumped from Walters ⅓ HP for headroom
    motor_rpm: float = 1725.0
    pulley_motor_od: float = 3.0
    pulley_drum_od: float = 5.0
    belt: str = "4L / A-section V-belt (size to center distance)"
    drum_rpm: float = 1035.0  # 1725 × 3/5

    # Frame (Baltic birch)
    side_thick: float = 0.75
    side_height: float = 30.0
    side_depth: float = 22.0
    clear_between_sides: float = 16.5  # drum + clearance
    base_thick: float = 0.75
    stretchers: int = 3

    # Table (solid — no conveyor)
    table_thick: float = 1.5  # two ¾″ ply laminated
    table_width: float = 16.0
    table_depth: float = 20.0
    table_top: str = "Phenolic / Formica / HDPE — low friction"
    elev_screw: str = "¾″-6 Acme or wood-threaded oak dowel"
    elev_travel: float = 3.25
    lock_knobs: int = 2  # star knobs + elongated washers

    # Dust / guard
    hood_ply: float = 0.25
    dust_port_od: float = 4.0
    hood_method: str = "Kerf-bent ¼″ pine/birch ply, sawdust-glue filled"

    # Modern deltas vs Walters build
    modernizations: tuple[str, ...] = (
        "Solid laminated sliding table — conveyor abandoned (Walters failed 3×)",
        "Adjustable idler-side flange bearing for parallelism / light taper",
        "½ HP dedicated motor (was ⅓ HP) with lockable gravity tension mount",
        "Precision-ground ¾″ shaft (was plain cold-rolled)",
        "1 mm disc relief every 4 MDF discs OR all-birch drum option",
        "Phenolic/Formica wear surface replaceable without rebuilding table",
        "4″ dust port + removable hood doubles as drum guard",
        "Printable D-1…D-6 sheets + interactive Build Walk",
    )


SPEC = Spec()


def surface_fpm(drum_od: float, rpm: float) -> float:
    return (3.14159265 * drum_od / 12.0) * rpm


def cut_list() -> list[dict[str, Any]]:
    """Primary plywood / lumber cut list for shopping."""
    s = SPEC
    span = s.clear_between_sides
    return [
        {"qty": 2, "size": f'{s.side_depth}" × {s.side_height}" × ¾"', "stock": "Baltic birch", "use": "Side panels"},
        {"qty": 1, "size": f'{span + 2 * s.side_thick}" × {s.side_depth}" × ¾"', "stock": "Baltic birch", "use": "Base deck"},
        {"qty": 3, "size": f'{span}" × 4" × ¾"', "stock": "Baltic birch", "use": "Front / mid / rear stretchers"},
        {"qty": 2, "size": f'{s.table_width}" × {s.table_depth}" × ¾"', "stock": "Baltic birch or void-free ply", "use": "Table laminate (glue face-to-face)"},
        {"qty": 1, "size": f'{s.table_width}" × {s.table_depth}"', "stock": "Phenolic / Formica", "use": "Table wear surface"},
        {"qty": s.disc_count_core + s.disc_count_ends, "size": f'⌀{s.drum_od + 0.125}" × ¾" (true to ⌀{s.drum_od}")', "stock": "MDF core + BB ends (or all BB)", "use": "Drum discs"},
        {"qty": 1, "size": f'{s.shaft_length}" × ⌀¾"', "stock": s.shaft_spec, "use": "Drum shaft"},
        {"qty": 1, "size": '~18" × 12" × ¼"', "stock": "Pine or birch ply", "use": "Kerf-bent dust hood blank"},
        {"qty": 1, "size": '12" × 8" × ¾"', "stock": "Baltic birch", "use": "Motor pivot cradle"},
        {"qty": 2, "size": '2×4 scrap blocks', "stock": "Construction lumber", "use": "Bearing locator / elev nut block"},
    ]


def hardware_bom() -> list[dict[str, str]]:
    s = SPEC
    return [
        {"item": f"{s.bearing_type}", "qty": str(s.bearing_count)},
        {"item": f'{s.pulley_motor_od}" × ¾" (or motor shaft) 4L pulley', "qty": "1"},
        {"item": f'{s.pulley_drum_od}" × ¾" bore 4L pulley', "qty": "1"},
        {"item": s.belt, "qty": "1"},
        {"item": f'{s.motor_hp:g} HP {s.motor_rpm:g} RPM TEFC motor, 115 V', "qty": "1"},
        {"item": "Star knobs ⅜-16 through + fender washers", "qty": "4"},
        {"item": s.elev_screw + " + matching nut / tapped block", "qty": "1 set"},
        {"item": 'Hook Velcro 4" wide (PSA) for drum', "qty": "~5 ft"},
        {"item": 'Loop-backed sandpaper roll 3" (80 / 120 / 180)', "qty": "as needed"},
        {"item": '⅛" piano wire for shaft keys', "qty": "12 in"},
        {"item": "Polyurethane or Titebond III for disc lamination", "qty": "1 bottle"},
        {"item": '4" dust hose adapter + blast gate', "qty": "1"},
        {"item": "On/off switch in metal box + 14–16 AWG cord 15 ft", "qty": "1"},
        {"item": "Machine screws / T-nuts for flange bearings", "qty": "8–16"},
        {"item": "Optional: shim stock / jack screws for idler bearing", "qty": "1 kit"},
    ]


def assembly_phases() -> list[dict[str, str]]:
    return [
        {"id": "a1", "phase": "frame", "title": "Cut & dry-fit sides / base / stretchers",
         "body": "Lay out flange-bearing centers, table slots, and motor cradle on both sides as a matched pair. Confirm clear span 16.5″."},
        {"id": "a2", "phase": "frame", "title": "Assemble rigid box frame",
         "body": "Glue + screw stretchers between Baltic birch sides. Square diagonals before the glue sets. Add base deck."},
        {"id": "a3", "phase": "drum", "title": "Turn / bandsaw drum discs",
         "body": "Bore ⌀¾″ centers (drill press + fence). Stack on shaft with piano-wire keys. Glue; leave 1 mm relief every 4 MDF discs."},
        {"id": "a4", "phase": "drum", "title": "Mount flange bearings & true drum",
         "body": "Install drive-side bearing fixed. Idler side on adjustable pad. Run drum; true OD with abrasive on a sled against the table plane."},
        {"id": "a5", "phase": "drive", "title": "Fit motor cradle, pulleys, belt",
         "body": "Pivot motor on hardwood dowel; belt tension from motor weight. Add lock screw so the running belt cannot pump the mount."},
        {"id": "a6", "phase": "table", "title": "Laminate table + wear surface",
         "body": "Glue two ¾″ panels face-to-face for torsion. Apply phenolic/Formica. Fit elevating screw and dual star-knob locks with elongated washers."},
        {"id": "a7", "phase": "hood", "title": "Kerf-bend dust hood",
         "body": "Kerf ¼″ ply, wet outer face, glue to form, fill kerfs with sawdust-glue. Add 4″ port. Fit as guard + collector."},
        {"id": "a8", "phase": "wrap", "title": "Apply Velcro + spiral sandpaper",
         "body": "Wrap hook Velcro tight with no bubbles. Cut spiral sandpaper from the first template; loop side mates to hooks."},
        {"id": "a9", "phase": "tune", "title": "Parallelism & first passes",
         "body": "Shim/jack idler bearing until feeler gauges match both ends under paper. Light passes only — this is not a planer."},
        {"id": "a10", "phase": "tune", "title": "Safety check & dust test",
         "body": "Verify hood lock, cord routing, switch placement, push-stick reach. Vacuum must catch before freehand use."},
    ]


def summary() -> dict[str, Any]:
    s = SPEC
    return {
        "name": "WALTER DS-16",
        "revision": "A",
        "lineage": "ShopNotes 86 → Ron Walters → modern dedicated solid-table redesign",
        "capacity": f'{s.capacity_width}" wide · {s.min_stock_thickness}"–{s.max_stock_thickness}" thick',
        "drum_rpm": s.drum_rpm,
        "surface_fpm": round(surface_fpm(s.drum_od, s.drum_rpm), 0),
        "spec": asdict(s),
        "cut_list": cut_list(),
        "hardware": hardware_bom(),
        "assembly": assembly_phases(),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(summary(), indent=2))
