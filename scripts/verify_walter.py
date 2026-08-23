#!/usr/bin/env python3
"""Deterministic WALTER Planforge checks. Exit 1 on hard fail.

Run: python3 scripts/verify_walter.py
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAD = os.path.join(ROOT, "sander", "walter", "cad")
sys.path.insert(0, CAD)

from walter_kernel import P, drum_rpm, feed_fpm, sfm  # noqa: E402
from walter_project import build_project, sheet_index  # noqa: E402

FAILS = []
WARNS = []


def fail(msg):
    FAILS.append(msg)


def warn(msg):
    WARNS.append(msg)


def exists(rel):
    return os.path.isfile(os.path.join(ROOT, rel))


def main():
    proj = build_project()
    parts = proj["parts"]
    ids = [p["PART_ID"] for p in parts]
    if len(ids) != len(set(ids)):
        fail("duplicate PART_ID in register")

    idset = set(ids)
    for st in proj["steps"]:
        if st["n"] < 1 or st["n"] > 22:
            fail(f"step number out of range {st['n']}")
        for qty, pid, _lab in st["parts"]:
            if pid not in idset:
                fail(f"step {st['n']} references missing part {pid}")
            if qty < 1:
                fail(f"step {st['n']} qty < 1 for {pid}")

    if len(proj["steps"]) != 22:
        fail(f"expected 22 LEGO steps, got {len(proj['steps'])}")
    if len(proj["bags"]) != 6:
        fail(f"expected 6 bags, got {len(proj['bags'])}")

    rpm = P["motor_rpm"] * P["pulley_mot"] / P["pulley_drm"]
    if abs(rpm - drum_rpm) > 1e-9:
        fail("drum_rpm drifted from P")
    if abs(math.pi * P["drum_od"] * drum_rpm / 12.0 - sfm) > 1e-6:
        fail("sfm drifted")
    if abs((math.pi * P["roller_od"] / 12.0) * 30.0 - feed_fpm) > 1e-6:
        fail("feed_fpm drifted")

    # files
    for rel in (
        "sander/walter/planforge/index.html",
        "sander/walter/planforge/DESIGN_BASIS.md",
        "sander/walter/planforge/ZERO_GAP.md",
        "sander/walter/planforge/CALCULATIONS.md",
        "sander/walter/planforge/MCMASTER_SCHEDULE.csv",
        "sander/walter/planforge/PART_REGISTER.csv",
        "sander/walter/planforge/SHEET_INDEX.csv",
        "sander/walter/manual/00-cover.svg",
        "sander/walter/manual/step-22.svg",
        "sander/walter/manual/index.html",
        "sander/walter/fab/07_BOM/master_bom.csv",
        "sander/walter/fab/08_CUT_LISTS/operations.csv",
        "sander/walter/fab/10_TEMPLATES/T-DISC.svg",
        "sander/walter/cad/walter_kernel.py",
        "sander/walter/cad/exports/walter_assembly.stl",
    ):
        if not exists(rel):
            fail(f"missing file {rel}")

    for i in range(1, 23):
        fn = f"sander/walter/manual/step-{i:02d}.svg"
        if not exists(fn):
            fail(f"missing {fn}")

    dwg = os.path.join(ROOT, "sander", "walter", "fab", "06_DRAWINGS")
    for row in sheet_index():
        if row["STATUS"] == "ACTIVE":
            path = os.path.join(dwg, row["FILE"])
            if not os.path.isfile(path):
                fail(f"ACTIVE sheet missing {row['ID']} {row['FILE']}")
            else:
                try:
                    ET.parse(path)
                except ET.ParseError as e:
                    fail(f"XML {row['FILE']}: {e}")
                text = open(path).read()
                if "NOT FOR UNCONDITIONAL FABRICATION" not in text:
                    fail(f"{row['ID']} missing release banner")
                if os.path.getsize(path) < 800:
                    fail(f"{row['ID']} suspiciously small")
        elif row["STATUS"] != "N/A":
            fail(f"{row['ID']} bad STATUS {row['STATUS']}")

    # templates calibration
    tdisc = open(os.path.join(ROOT, "sander/walter/fab/10_TEMPLATES/T-DISC.svg")).read()
    if "1.000 in" not in tdisc or "100 mm" not in tdisc:
        fail("T-DISC missing dual calibration bars")

    # BOM vs parts
    bom_path = os.path.join(ROOT, "sander/walter/fab/07_BOM/master_bom.csv")
    with open(bom_path) as f:
        bom_ids = [r["PART_ID"] for r in csv.DictReader(f)]
    if set(bom_ids) != idset:
        fail(f"master_bom PART_ID mismatch {set(bom_ids) ^ idset}")

    # hardware sourced pair
    src = [h for h in proj["hardware"] if h["EVIDENCE"] == "S"]
    pns = {h["PN"] for h in src}
    if pns != {"6245K47", "6191K37"}:
        fail(f"unexpected [S] PNs {pns}")

    # app assembly synced
    app = open(os.path.join(ROOT, "sander/walter/app/data.js")).read()
    for st in proj["steps"]:
        if st["title"] not in app:
            fail(f"app data.js missing step title: {st['title']}")
    if sum(1 for st in proj["steps"] if f's{st["n"]:02d}' in app) < 22:
        fail("app data.js does not list 22 step ids s01–s22")
    for need in ("M-103_elevation.svg", "M-104_dust.svg"):
        if need not in app:
            fail(f"app data.js missing gallery {need}")

    params = json.load(open(os.path.join(ROOT, "sander/walter/cad/parameters.json")))
    if params.get("rev") != "C":
        fail(f"parameters.json rev {params.get('rev')}")

    if abs(P.get("envelope_z", 0) - 22.00) > 1e-9:
        fail(f"envelope_z {P.get('envelope_z')} != 22.00")
    if abs(P["wall_h"] - 20.00) > 1e-9:
        fail(f"wall_h {P['wall_h']} != 20.00")
    dim001 = next(r for r in proj["requirements"] if r["ID"] == "DIM-001")
    if "22 × 36 × 22" not in dim001["STATEMENT"]:
        fail("DIM-001 envelope is not 22 × 36 × 22″")

    codes = {r["ID"] for r in sheet_index() if r["STATUS"] == "ACTIVE"}
    for need in ("M-103", "M-104", "G-003", "G-004", "A-104", "E-102", "F-102", "Q-101"):
        if need not in codes:
            fail(f"sheet index missing ACTIVE {need}")
    active_n = sum(1 for r in sheet_index() if r["STATUS"] == "ACTIVE")
    if active_n < 33:
        fail(f"expected ≥33 ACTIVE Planforge sheets, got {active_n}")

    print("WALTER verify:")
    for w in WARNS:
        print("  WARN", w)
    if FAILS:
        for x in FAILS:
            print("  FAIL", x)
        print(f"{len(FAILS)} hard fail(s)")
        return 1
    print("  PASS", len(sheet_index()), "sheet-index rows,", len(parts), "parts,", len(proj["steps"]), "steps")
    return 0


if __name__ == "__main__":
    sys.exit(main())
