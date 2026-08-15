#!/usr/bin/env python3
"""Deterministic QA for the WALTER DS-16 drawing package.

These are file-and-geometry checks, not opinions about the design. They catch
the failure modes that are easy to miss by eye:

  * a sheet registered in the index but never written, empty, or malformed
  * content that runs off the page or collides with the title block
  * a build step pointing at a sheet code that does not exist
  * a part that appears in no drawing, or a cut-list/part-drawing size conflict
  * duplicate IDs anywhere in the registers

Exit code is non-zero if any check fails, so this can gate a commit.

Run:  python3 scripts/qa_walter_package.py
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOP = os.path.join(ROOT, "shop", "drum-sander")
sys.path.insert(0, os.path.join(SHOP, "cad"))

from walter_ds16 import (  # noqa: E402
    build_steps,
    cut_list,
    hardware,
    inspection,
    joints,
    parts,
    shop_drawings,
    validate,
)

PAGE_W, PAGE_H = 1680, 1188
# Two generators draw the frame: the overview sheets rule the footer at
# Hpx-90 and the part/guide sheets at Hpx-78. Body content must stay above the
# earlier of the two. Title-block text legitimately sits below y=1120; the gap
# between the footer rule and that band is where overflow shows up.
BODY_MAX_Y = 1098.0
TITLEBLOCK_MIN_Y = 1120.0
MAX_TITLEBLOCK_TEXTS = 10
SVG = "{http://www.w3.org/2000/svg}"

failures: list[str] = []
notes: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def check_ssot() -> None:
    errs = validate()
    if errs:
        for e in errs:
            fail(f"SSOT: {e}")


def check_unique_ids() -> None:
    for name, ids in (
        ("part", [p["part_id"] for p in parts()]),
        ("hardware", [h["hardware_id"] for h in hardware()]),
        ("joint", [j["joint_id"] for j in joints()]),
        ("qc", [q["qc"] for q in inspection()]),
        ("sheet code", [d["code"] for d in shop_drawings()]),
        ("sheet file", [d["file"] for d in shop_drawings()]),
        ("step", [s["id"] for s in build_steps()]),
    ):
        dupes = [k for k, n in Counter(ids).items() if n > 1]
        if dupes:
            fail(f"duplicate {name} IDs: {', '.join(map(str, dupes))}")


def check_files() -> tuple[int, int]:
    ok = 0
    for d in shop_drawings():
        sub = d.get("dir", "plans")
        path = os.path.join(SHOP, sub, d["file"])
        if not os.path.isfile(path):
            fail(f'{d["code"]}: file missing — {sub}/{d["file"]}')
            continue
        if os.path.getsize(path) < 400:
            fail(f'{d["code"]}: file suspiciously small ({os.path.getsize(path)} bytes)')
            continue
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            fail(f'{d["code"]}: malformed SVG — {exc}')
            continue
        if root.get("width") is None or root.get("viewBox") is None:
            fail(f'{d["code"]}: missing width/viewBox')
        ok += 1
        check_bounds(d["code"], root)
    return ok, len(shop_drawings())


def check_bounds(code: str, root: ET.Element) -> None:
    """Text must stay inside the frame and out of the title-block band."""
    overflow: list[str] = []
    outside = 0
    tb = 0
    for el in root.iter(f"{SVG}text"):
        try:
            x = float(el.get("x", "0"))
            y = float(el.get("y", "0"))
        except ValueError:
            continue
        if x < 8 or x > PAGE_W - 8 or y < 8 or y > PAGE_H - 8:
            outside += 1
        if el.get("transform"):  # rotated dimension text, skip the band test
            continue
        if y >= TITLEBLOCK_MIN_Y:
            tb += 1
        elif y > BODY_MAX_Y:
            overflow.append(f'y={y:.0f} "{(el.text or "")[:34]}"')
    if overflow:
        fail(f"{code}: {len(overflow)} text item(s) below the footer rule — " + "; ".join(overflow[:3]))
    if outside:
        fail(f"{code}: {outside} text item(s) outside the page")
    if tb > MAX_TITLEBLOCK_TEXTS:
        fail(f"{code}: {tb} text items in the title-block band, expected at most {MAX_TITLEBLOCK_TEXTS}")


def check_step_references() -> None:
    codes = {d["code"] for d in shop_drawings()}
    # step sheets cite short codes like "P-001L", "A-01", "D-6", "IDX", "Q-101"
    for st in build_steps():
        for ref in st["sheets"]:
            if ref not in codes:
                fail(f'{st["id"]}: cites sheet {ref}, which is not in the register')


def check_part_coverage() -> None:
    """Every fabricated part needs its own drawing, a cut-list row, and a step."""
    by_id = {p["part_id"]: p for p in parts()}
    sheet_files = {d["file"] for d in shop_drawings()}
    cut_ids = {r["part_id"] for r in cut_list()}
    step_parts = {pid for st in build_steps() for pid in st["parts"]}
    for pid, p in by_id.items():
        if p["sheet"] not in sheet_files:
            fail(f'{pid}: drawing {p["sheet"]} is not a registered sheet')
        if pid not in cut_ids:
            notes.append(f"{pid}: no cut-list row (may be BUY or jig stock)")
        if pid not in step_parts:
            fail(f"{pid}: never appears in a build step")


def check_cutlist_agreement() -> None:
    """Rough stock must never be smaller than the finished part."""
    by_id = {p["part_id"]: p for p in parts()}
    for r in cut_list():
        p = by_id.get(r["part_id"])
        if not p:
            fail(f'cut list references unknown part {r["part_id"]}')
            continue
        for dim in ("t", "w", "l"):
            fin, rough = p.get(f"finished_{dim}"), p.get(f"rough_{dim}")
            if isinstance(fin, (int, float)) and isinstance(rough, (int, float)):
                if rough + 1e-9 < fin:
                    fail(f'{p["part_id"]}: rough {dim}={rough} smaller than finished {dim}={fin}')


def check_step_sequence() -> None:
    steps = build_steps()
    nums = [s["step"] for s in steps]
    if nums != list(range(1, len(steps) + 1)):
        fail(f"build steps are not numbered 1..n: {nums}")
    for st in steps:
        if not st["actions"]:
            fail(f'{st["id"]}: no actions')
        if not st["gate"]:
            fail(f'{st["id"]}: no completion gate')
        if st["of"] != len(steps):
            fail(f'{st["id"]}: stale step total {st["of"]}')


def main() -> int:
    check_ssot()
    check_unique_ids()
    check_step_sequence()
    check_step_references()
    check_part_coverage()
    check_cutlist_agreement()
    ok, total = check_files()

    print(f"WALTER package QA — {ok}/{total} registered sheets present and parseable")
    print(f"  parts {len(parts())} · hardware {len(hardware())} · joints {len(joints())} · steps {len(build_steps())}")
    for n in notes:
        print(f"  note: {n}")
    if failures:
        print(f"\n{len(failures)} FAILURE(S):")
        for f in failures:
            print(f"  ✗ {f}")
        return 1
    print("\nAll deterministic checks pass.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
