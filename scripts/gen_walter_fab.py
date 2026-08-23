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

from walter_kernel import FMEA, HARDWARE, PLYWOOD, REV  # noqa: E402
from walter_project import build_project  # noqa: E402


def _mkdirs():
    for sub in ("07_BOM", "08_CUT_LISTS", "09_JOINERY", "10_TEMPLATES", "12_QA", "00_SOURCE", "06_DRAWINGS"):
        os.makedirs(os.path.join(FAB, sub), exist_ok=True)


def _csv(path, rows, fields):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})
    print("wrote", path)


def _cal_bars():
    """1.000 in and 100 mm check bars. Print actual size; disable printer scaling."""
    return """
  <g id='cal' fill='none' stroke='#b4532a' stroke-width='0.35'>
    <rect x='-60' y='68' width='25.4' height='3'/>
    <rect x='-20' y='68' width='100' height='3'/>
  </g>
  <text x='-47.3' y='66' text-anchor='middle' font-family='IBM Plex Mono, monospace' font-size='2.4' fill='#b4532a'>1.000 in</text>
  <text x='30' y='66' text-anchor='middle' font-family='IBM Plex Mono, monospace' font-size='2.4' fill='#b4532a'>100 mm</text>
  <text x='0' y='78' text-anchor='middle' font-family='IBM Plex Mono, monospace' font-size='2.2' fill='#6b5340'>PRINT 100%  ·  actual size  ·  measure BOTH bars  ·  discard if either axis is wrong</text>
"""


def template_disc(path):
    # 1:1 mm. Ø 5.125" = 130.175 mm
    r = 5.125 * 25.4 / 2
    bore = 0.748 * 25.4 / 2
    kw = 0.1875 * 25.4
    svg = f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns='http://www.w3.org/2000/svg' width='160mm' height='170mm' viewBox='-80 -75 160 170'>
  <title>WALTER T-DISC  Ø5.125  1:1</title>
  <circle r='{r:.3f}' fill='none' stroke='#1c1914' stroke-width='0.35'/>
  <circle r='{bore:.3f}' fill='none' stroke='#1c1914' stroke-width='0.35'/>
  <rect x='{-kw/2:.3f}' y='{-bore-3:.3f}' width='{kw:.3f}' height='6' fill='none' stroke='#b4532a' stroke-width='0.35'/>
  <text x='0' y='62' text-anchor='middle' font-family='IBM Plex Mono, monospace' font-size='3.2'>T-DISC  D-001  Ø5.125  BORE 0.748  KEY 3/16  1:1 mm</text>
  {_cal_bars()}
</svg>
"""
    with open(path, "w") as f:
        f.write(svg)
    print("wrote", path)


def template_plate(path):
    s = 6.0 * 25.4
    svg = f"""<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns='http://www.w3.org/2000/svg' width='180mm' height='200mm' viewBox='-10 -10 170 210'>
  <title>WALTER T-PLATE  6x6  1:1</title>
  <rect x='0' y='0' width='{s:.3f}' height='{s:.3f}' fill='none' stroke='#1c1914' stroke-width='0.35'/>
  <circle cx='{s/2:.3f}' cy='{s/2:.3f}' r='{0.55*25.4:.3f}' fill='none' stroke='#1c1914' stroke-width='0.35'/>
  <circle cx='{s/2 - 1.85*25.4:.3f}' cy='{s/2:.3f}' r='{0.17*25.4:.3f}' fill='none' stroke='#b4532a' stroke-width='0.35'/>
  <circle cx='{s/2 + 1.85*25.4:.3f}' cy='{s/2:.3f}' r='{0.17*25.4:.3f}' fill='none' stroke='#b4532a' stroke-width='0.35'/>
  <text x='{s/2:.3f}' y='{s+8:.3f}' text-anchor='middle' font-family='IBM Plex Mono, monospace' font-size='3.2'>T-PLATE  ST-001/002  6.00 x 6.00 x 0.25  1:1 mm</text>
  <g fill='none' stroke='#b4532a' stroke-width='0.35'>
    <rect x='10' y='{s+18:.3f}' width='25.4' height='3'/>
    <rect x='50' y='{s+18:.3f}' width='100' height='3'/>
  </g>
  <text x='22.7' y='{s+16:.3f}' text-anchor='middle' font-family='IBM Plex Mono, monospace' font-size='2.4' fill='#b4532a'>1.000 in</text>
  <text x='100' y='{s+16:.3f}' text-anchor='middle' font-family='IBM Plex Mono, monospace' font-size='2.4' fill='#b4532a'>100 mm</text>
  <text x='{s/2:.3f}' y='{s+28:.3f}' text-anchor='middle' font-family='IBM Plex Mono, monospace' font-size='2.2' fill='#6b5340'>PRINT 100%  ·  measure BOTH bars  ·  ST-001 slot the two copper holes 0.90 vertically</text>
</svg>
"""
    with open(path, "w") as f:
        f.write(svg)
    print("wrote", path)


OPERATIONS = [
    dict(STEP="OP-01", PART="D-001", DATUM="template T-DISC", OP="Bandsaw 21 blanks", TOOL="bandsaw", JIG="T-DISC", TARGET="Ø 5.125", HAZARD="kickback — keep disc on the table", INSPECT="template line", HOLD=""),
    dict(STEP="OP-02", PART="D-001", DATUM="drill-press fence", OP="Bore 0.748 and keyway", TOOL="drill press + file", JIG="fence + pin", TARGET="0.748 +0/−0.002", HAZARD="breakout — backer", INSPECT="pin gauge", HOLD=""),
    dict(STEP="OP-03", PART="ST-004", DATUM="shaft ends", OP="Dry-stack + glue column", TOOL="clamps", JIG="keyed shaft", TARGET="16.00 face", HAZARD="no glue in keyway", INSPECT="gaps every 4", HOLD="HOLD: wipe keyway"),
    dict(STEP="OP-04", PART="D-001", DATUM="centers", OP="True OD", TOOL="lathe or in-machine", JIG="carrier", TARGET="5.000 ±0.010", HAZARD="unbalanced blank", INSPECT="Q02", HOLD="HOLD: do not run unbalanced"),
    dict(STEP="OP-05", PART="F-002", DATUM="flat door", OP="Glue doubled walls grain-crossed", TOOL="cauls", JIG="door", TARGET="1.50 thick", HAZARD="wind", INSPECT="winding sticks", HOLD=""),
    dict(STEP="OP-06", PART="ST-001", DATUM="plate as jig", OP="Drill walls from plates", TOOL="drill press", JIG="ST-001/002", TARGET="D2 story stick", HAZARD="slot idle only", INSPECT="story stick", HOLD="HOLD: do not slot drive plate"),
    dict(STEP="OP-07", PART="F-001", DATUM="D1", OP="Square the box", TOOL="square", JIG="stretchers", TARGET="diagonals agree", HAZARD="glue grab", INSPECT="Q01", HOLD="HOLD: winding sticks on plates"),
    dict(STEP="OP-08", PART="T-001", DATUM="straightedge", OP="Torsion platen + UHMW", TOOL="glue + screws", JIG="grid cauls", TARGET="flat 0.010", HAZARD="hump prints stripe", INSPECT="straightedge", HOLD=""),
    dict(STEP="OP-09", PART="ST-007", DATUM="D4", OP="Clock Acme nuts, fit HTD", TOOL="paint pen", JIG="nut blocks", TARGET="witness aligned", HAZARD="rack if independent", INSPECT="Q05", HOLD="HOLD: clock before belt"),
    dict(STEP="OP-10", PART="C-001", DATUM="roller CL", OP="Turn 0.030 crown both rollers", TOOL="lathe", JIG="centers", TARGET="0.030 ±0.005", HAZARD="flying tube", INSPECT="caliper mid vs end", HOLD=""),
    dict(STEP="OP-11", PART="C-004", DATUM="platen", OP="Fit PVC belt, skew, PWM", TOOL="¼-20 skew", JIG="idle slots", TARGET="track empty 60 s", HAZARD="nip at rollers", INSPECT="Q04", HOLD="HOLD: not a sanding belt"),
    dict(STEP="OP-12", PART="M-001", DATUM="hinge plate", OP="Motor, pulleys, 4L440, guard", TOOL="turnbuckle", JIG="ST-003", TARGET="guard closed", HAZARD="belt pinch", INSPECT="Q08", HOLD="HOLD: electrician before 115 V"),
    dict(STEP="OP-13", PART="HD-001", DATUM="walls", OP="Hood, 4″ port, brush", TOOL="foam", JIG="collector", TARGET="tissue pull", HAZARD="dust / fire load", INSPECT="Q07", HOLD="HOLD: collector on before spin"),
    dict(STEP="OP-14", PART="ALL", DATUM="D3", OP="Wrap, jack parallel, Q01–Q10, first poplar", TOOL="carrier", JIG="16″ board", TARGET="0.010 even cut", HAZARD="kickback / restart", INSPECT="Q06 Q09", HOLD="HOLD: blink test; no board under drum at start"),
]


def write_fab_index():
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/><title>WALTER fab — Rev {REV}</title>
<style>
body{{margin:0;background:#1c1914;color:#f4efe6;font:16px/1.5 "IBM Plex Mono",monospace;padding:48px 28px}}
a{{color:#d47248}} h1{{font-family:Georgia,serif;font-size:42px}}
ul{{line-height:1.8}} .warn{{color:#e8c4a8}}
</style></head><body>
<p>WALTER · Rev {REV} · WOODWRIGHT PLANFORGE v1.0</p>
<h1>Fab package</h1>
<p class="warn">FABRICATION-READY WITH CONDITIONS · R3 · not PE · not UL · not a ShopNotes reprint</p>
<ul>
<li><a href="06_DRAWINGS/">06_DRAWINGS</a> — G/A/E/P/J/M/F/Q family</li>
<li><a href="07_BOM/master_bom.csv">07_BOM/master_bom.csv</a> · <a href="07_BOM/hardware.csv">hardware.csv</a> · <a href="07_BOM/plywood.csv">plywood.csv</a></li>
<li><a href="08_CUT_LISTS/finished.csv">08_CUT_LISTS/finished.csv</a> · <a href="08_CUT_LISTS/operations.csv">operations.csv</a></li>
<li><a href="09_JOINERY/joints.csv">09_JOINERY/joints.csv</a></li>
<li><a href="10_TEMPLATES/T-DISC.svg">T-DISC 1:1</a> · <a href="10_TEMPLATES/T-PLATE.svg">T-PLATE 1:1</a></li>
<li><a href="12_QA/inspection.csv">12_QA/inspection.csv</a> · <a href="12_QA/fmea.csv">fmea.csv</a></li>
<li><a href="../planforge/">Planforge guidebook</a> · <a href="../manual/">LEGO manual</a></li>
</ul>
<p>Geometry: <code>cad/walter_kernel.py</code>. IDs: <code>cad/walter_project.py</code>.</p>
</body></html>
"""
    path = os.path.join(FAB, "index.html")
    with open(path, "w") as f:
        f.write(html)
    print("wrote", path)


def main():
    _mkdirs()
    proj = build_project()
    _csv(
        os.path.join(FAB, "07_BOM", "master_bom.csv"),
        proj["parts"],
        ["PART_ID", "QTY", "DESC", "MAT", "FINISHED", "GRAIN", "BAG", "GROUP", "MAKE"],
    )
    _csv(
        os.path.join(FAB, "09_JOINERY", "joints.csv"),
        proj["joinery"],
        ["JOINT_ID", "TYPE", "PART_A", "PART_B", "FUNCTION", "GEOMETRY", "FIT", "ADHESIVE", "DRAWING", "INSPECTION"],
    )
    _csv(
        os.path.join(FAB, "08_CUT_LISTS", "cut_list.csv"),
        proj["parts"],
        ["PART_ID", "QTY", "DESC", "MAT", "FINISHED", "GRAIN", "BAG"],
    )
    _csv(
        os.path.join(FAB, "08_CUT_LISTS", "operations.csv"),
        OPERATIONS,
        ["STEP", "PART", "DATUM", "OP", "TOOL", "JIG", "TARGET", "HAZARD", "INSPECT", "HOLD"],
    )
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
            f"WALTER fab package Rev {REV}\n"
            "Geometry: sander/walter/cad/walter_kernel.py\n"
            "IDs/bags: sander/walter/cad/walter_project.py\n"
            "Regenerate: python3 scripts/gen_walter_fab.py\n"
            "McMaster catalog numbers in 07_BOM/mcmaster.csv are SEARCH HINTS except 6245K47 / 6191K37 [S].\n"
            "Verify every number on the live catalog before you buy. Numbers drift.\n"
            "Release: FABRICATION-READY WITH CONDITIONS. Not PE. Not UL. Not a ShopNotes reprint.\n"
            "Print T-DISC and T-PLATE at 100% and measure BOTH calibration bars.\n"
        )
    print("wrote", src)
    write_fab_index()


if __name__ == "__main__":
    main()
