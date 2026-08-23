#!/usr/bin/env python3
"""WALTER fab package: BOM CSVs, cut lists, FMEA, 1:1 template SVGs."""

from __future__ import annotations

import csv
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.join(ROOT, "..", "sander", "walter", "cad")
FAB = os.path.join(ROOT, "..", "sander", "walter", "fab")
sys.path.insert(0, CAD)

from walter_kernel import FMEA, HARDWARE, PLYWOOD  # noqa: E402


def _mkdirs():
    for sub in ("07_BOM", "08_CUT_LISTS", "10_TEMPLATES", "12_QA", "00_SOURCE"):
        os.makedirs(os.path.join(FAB, sub), exist_ok=True)


def _csv(path, rows, fields):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})
    print("wrote", path)


def template_disc(path):
    # 1:1 mm. Ø 5.125" = 130.175 mm
    r = 5.125 * 25.4 / 2
    bore = 0.748 * 25.4 / 2
    kw = 0.1875 * 25.4
    svg = f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns='http://www.w3.org/2000/svg' width='150mm' height='150mm' viewBox='-75 -75 150 150'>
  <title>WALTER T-DISC  Ø5.125  1:1</title>
  <circle r='{r:.3f}' fill='none' stroke='#1c1914' stroke-width='0.35'/>
  <circle r='{bore:.3f}' fill='none' stroke='#1c1914' stroke-width='0.35'/>
  <rect x='{-kw/2:.3f}' y='{-bore-3:.3f}' width='{kw:.3f}' height='6' fill='none' stroke='#b4532a' stroke-width='0.35'/>
  <text x='0' y='62' text-anchor='middle' font-family='IBM Plex Mono, monospace' font-size='3.2'>T-DISC  Ø5.125  BORE 0.748  1:1 mm</text>
</svg>
"""
    with open(path, "w") as f:
        f.write(svg)
    print("wrote", path)


def template_plate(path):
    s = 6.0 * 25.4
    svg = f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns='http://www.w3.org/2000/svg' width='180mm' height='180mm' viewBox='-10 -10 170 170'>
  <title>WALTER T-PLATE  6x6  1:1</title>
  <rect x='0' y='0' width='{s:.3f}' height='{s:.3f}' fill='none' stroke='#1c1914' stroke-width='0.35'/>
  <circle cx='{s/2:.3f}' cy='{s/2:.3f}' r='{0.55*25.4:.3f}' fill='none' stroke='#1c1914' stroke-width='0.35'/>
  <circle cx='{s/2 - 1.85*25.4:.3f}' cy='{s/2:.3f}' r='{0.17*25.4:.3f}' fill='none' stroke='#b4532a' stroke-width='0.35'/>
  <circle cx='{s/2 + 1.85*25.4:.3f}' cy='{s/2:.3f}' r='{0.17*25.4:.3f}' fill='none' stroke='#b4532a' stroke-width='0.35'/>
  <text x='{s/2:.3f}' y='{s+8:.3f}' text-anchor='middle' font-family='IBM Plex Mono, monospace' font-size='3.2'>T-PLATE  6.00 x 6.00 x 0.25  1:1 mm</text>
</svg>
"""
    with open(path, "w") as f:
        f.write(svg)
    print("wrote", path)


def main():
    _mkdirs()
    _csv(
        os.path.join(FAB, "07_BOM", "plywood.csv"),
        PLYWOOD,
        ["id", "name", "size", "qty", "stock", "nest"],
    )
    _csv(
        os.path.join(FAB, "07_BOM", "hardware.csv"),
        HARDWARE,
        ["item", "qty", "search", "mcmaster"],
    )
    _csv(
        os.path.join(FAB, "07_BOM", "mcmaster.csv"),
        [h for h in HARDWARE if h.get("mcmaster")],
        ["item", "qty", "search", "mcmaster"],
    )
    _csv(
        os.path.join(FAB, "08_CUT_LISTS", "finished.csv"),
        PLYWOOD,
        ["id", "name", "size", "qty", "stock", "nest"],
    )
    _csv(
        os.path.join(FAB, "12_QA", "fmea.csv"),
        FMEA,
        ["id", "item", "cause", "effect", "sev", "det", "prev"],
    )
    inspect = [
        dict(id="Q01", check="Walls square and coplanar at bearing plates", tool="framing square + winding sticks"),
        dict(id="Q02", check="Drum OD 5.000 ±0.010 after turning", tool="caliper"),
        dict(id="Q03", check="Drum parallel to platen, 16\" feeler both ends", tool="feeler + 16\" straightedge"),
        dict(id="Q04", check="Conveyor tracks empty 60 s, then with a 16\" board", tool="eyeball + marks"),
        dict(id="Q05", check="Acme screws timed — witness marks aligned", tool="paint pen"),
        dict(id="Q06", check="E-stop kills drum and feed; no auto-restart", tool="blink test"),
        dict(id="Q07", check="Hood on, 4\" hose pulling, no leak at walls", tool="tissue"),
        dict(id="Q08", check="Guard closed; no finger path to belt pinch", tool="visual"),
        dict(id="Q09", check="First passes 0.010\" in poplar, even cut", tool="ear + caliper"),
        dict(id="Q10", check="Idle jack at zero before trusting taper", tool="jack screws"),
    ]
    _csv(os.path.join(FAB, "12_QA", "inspection.csv"), inspect, ["id", "check", "tool"])
    template_disc(os.path.join(FAB, "10_TEMPLATES", "T-DISC.svg"))
    template_plate(os.path.join(FAB, "10_TEMPLATES", "T-PLATE.svg"))
    src = os.path.join(FAB, "00_SOURCE", "README.txt")
    with open(src, "w") as f:
        f.write(
            "WALTER fab package Rev B\n"
            "Geometry: sander/walter/cad/walter_kernel.py\n"
            "Regenerate: python3 scripts/gen_walter_fab.py\n"
            "McMaster catalog numbers in 07_BOM/mcmaster.csv are SEARCH HINTS.\n"
            "Verify every number on the live catalog before you buy. Numbers drift.\n"
            "Do not treat this as a ShopNotes reprint.\n"
        )
    print("wrote", src)


if __name__ == "__main__":
    main()
