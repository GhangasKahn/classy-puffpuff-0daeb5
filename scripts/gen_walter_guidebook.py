#!/usr/bin/env python3
"""WALTER DS-16 master build guide book (PLANFORGE structure).

Generates the sheets that turn a drawing set into a followable book:

  G-001  cover, release state, risk class, how to use the book
  G-002  design basis: parameters, equations, datums, decisions
  G-003  evidence classes, calculation register, revisions
  G-004  safety, risk triggers, FMEA, what is NOT released
  E-101  exploded isometric with BOM balloons
  ST-01…ST-14  step sheets: parts tray, actions, QC gate, illustration
  Q-101  commissioning and acceptance

Drawing primitives are shared with gen_walter_part_sheets so line weights,
colors, and the title block stay identical across the whole package.

Run:  python3 scripts/gen_walter_guidebook.py
"""

from __future__ import annotations

import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "shop", "drum-sander", "cad"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from walter_ds16 import GEOM as G  # noqa: E402
from walter_ds16 import PROJECT, RELEASE_STATE  # noqa: E402
from walter_ds16 import SPEC as S  # noqa: E402
from walter_ds16 import (  # noqa: E402
    build_steps,
    calibration_steps,
    datums,
    decisions,
    fmea,
    hardware,
    inspection,
    parts,
    pass_schedule,
    quality_targets,
    revisions,
    shop_drawings,
    validate,
)

from gen_walter_part_sheets import (  # noqa: E402
    ACC,
    BRONZE,
    DIM,
    GREEN,
    INK,
    KNOB,
    LIGHT,
    MDF,
    NOTE,
    PAPER,
    PHEN,
    STEEL,
    TAN,
    UHMW,
    W,
    Hpx,
    Mesh,
    Sheet,
    _wrap,
    box,
    cyl_x,
    inch,
    iso_group,
)

OUT = os.path.join(ROOT, "shop", "drum-sander", "plans")
os.makedirs(OUT, exist_ok=True)

MUTE = "#d8d8d4"  # already-built geometry, LEGO-style ghosting
FLAG = "#a8342a"  # release blocker / hazard


# ---------------------------------------------------------------------------
# Isometric view for multi-part assemblies
# ---------------------------------------------------------------------------
#
# Screen mapping is the classic y-up isometric: +x fans up-right, +z fans
# up-left, +y is straight up. With that mapping the corner nearest the viewer
# is the one with the SMALLEST x and z, so the painter's depth must be
# (y - x - z). The single-part sheets get away with a different sort because a
# convex solid is resolved by backface culling alone; an assembly does not,
# and a mismatched sort paints the far side panel over the drum.

COS30 = math.cos(math.radians(30))
SIN30 = math.sin(math.radians(30))


def _project(p: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = p
    return (x - z) * COS30, y + (x + z) * SIN30, y - x - z


def assembly_iso(
    meshes: list[Mesh], x: float, y: float, w: float, h: float, pad: float = 16
) -> tuple[str, tuple[float, float, float]]:
    """Render meshes isometrically. Returns (svg, (ox, oy, scale)).

    The transform is handed back so callers can place balloons and leaders on
    the real projected position of a part instead of a guessed coordinate.
    """
    tris: list[tuple[float, str, list[tuple[float, float]]]] = []
    for m in meshes:
        for verts, lit in m.faces:
            proj = [_project(v) for v in verts]
            area = 0.0
            for i, p in enumerate(proj):
                q = proj[(i + 1) % len(proj)]
                area += p[0] * q[1] - q[0] * p[1]
            if area <= 0:  # backface
                continue
            depth = sum(p[2] for p in proj) / len(proj)
            k = 0.55 + 0.45 * lit
            hh = m.color.lstrip("#")
            r, g, b = (int(hh[i : i + 2], 16) for i in (0, 2, 4))
            col = "#%02x%02x%02x" % (
                max(0, min(255, int(r * k))),
                max(0, min(255, int(g * k))),
                max(0, min(255, int(b * k))),
            )
            tris.append((depth, col, [(p[0], p[1]) for p in proj]))
    if not tris:
        return "", (x, y, 1.0)
    tris.sort(key=lambda t: t[0])  # far (small depth) first
    xs = [px for _, _, pts in tris for px, _ in pts]
    ys = [py for _, _, pts in tris for _, py in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    sc = min((w - 2 * pad) / max(maxx - minx, 1e-6), (h - 2 * pad) / max(maxy - miny, 1e-6))
    ox = x + pad + (w - 2 * pad - (maxx - minx) * sc) / 2 - minx * sc
    oy = y + h - pad - (h - 2 * pad - (maxy - miny) * sc) / 2 + miny * sc
    out = [f"<g stroke='{INK}' stroke-width='1.0' stroke-linejoin='round'>"]
    for _, col, pts in tris:
        poly = " ".join(f"{ox + px * sc:.1f},{oy - py * sc:.1f}" for px, py in pts)
        out.append(f"<polygon points='{poly}' fill='{col}'/>")
    out.append("</g>")
    return "\n".join(out), (ox, oy, sc)


def assembly_frame(
    sh: Sheet, x: float, y: float, w: float, h: float, caption: str, meshes: list[Mesh]
) -> tuple[float, float, float]:
    sh.rect(x, y, w, h, fill=LIGHT, stroke=INK, sw=1.0)
    svg, tf = assembly_iso(meshes, x, y, w, h)
    sh.add(svg)
    sh.text(x + 10, y + 18, caption, 11, DIM, bold=True)
    return tf


def group_anchor(meshes: list[Mesh], tf: tuple[float, float, float]) -> tuple[float, float]:
    """Screen position of a group's visual centre, using the render transform."""
    ox, oy, sc = tf
    pts = [_project(v) for m in meshes for verts, _ in m.faces for v in verts]
    if not pts:
        return ox, oy
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    cx = (min(xs) + max(xs)) / 2
    cy = (min(ys) + max(ys)) / 2
    return ox + cx * sc, oy - cy * sc


# ---------------------------------------------------------------------------
# Full-machine solids, filtered by viz group
# ---------------------------------------------------------------------------


def machine_groups(
    shows: list[str], highlight: list[str] | None = None, explode: float = 0.0
) -> dict[str, list[Mesh]]:
    """Same solids as machine_meshes, kept per viz group for balloon anchors."""
    groups: dict[str, list[Mesh]] = {}
    for gid in shows:
        meshes = machine_meshes([gid], highlight=highlight, explode=explode)
        if meshes:
            groups[gid] = meshes
    return groups


def machine_meshes(shows: list[str], highlight: list[str] | None = None, explode: float = 0.0) -> list[Mesh]:
    """Build the machine from viz groups.

    `shows` selects which groups appear. Groups in `highlight` keep their
    material color; everything else is muted so the new work in a step reads
    at a glance. `explode` separates major groups along their install axis.
    """
    hi = set(highlight or shows)
    t = G.side_thick
    Wbox = G.overall_width
    D = S.side_depth
    H = S.side_height
    e = explode
    out: list[Mesh] = []

    def col(group: str, real: str) -> str:
        return real if group in hi else MUTE

    def want(group: str) -> bool:
        return group in shows

    if want("base"):
        out.append(box(col("base", GREEN), 0, -e * 7.0, 0, Wbox, S.base_thick, D))
    if want("sides"):
        dx = e * 10.0
        out.append(box(col("sides", GREEN), -dx, S.base_thick, 0, t, H - S.base_thick, D))
        out.append(box(col("sides", GREEN), Wbox - t + dx, S.base_thick, 0, t, H - S.base_thick, D))
    if want("stretch"):
        for z in S.stretcher_z:
            out.append(
                box(
                    col("stretch", TAN),
                    t - S.stretcher_housing,
                    z,
                    S.stretcher_dado_y0 - e * 11.0,
                    G.stretcher_length,
                    S.ply_actual,
                    S.stretcher_height,
                )
            )
    if want("ways"):
        wl = D - 2 * S.way_end_inset
        out.append(box(col("ways", UHMW), t - G.way_rebate, S.way_z, S.way_end_inset, S.way_stock, S.way_stock, wl))
        out.append(box(col("ways", UHMW), Wbox - t - G.way_project, S.way_z, S.way_end_inset, S.way_stock, S.way_stock, wl))
    if want("table"):
        tw, td, tt = G.table_width, G.table_depth, G.table_thick
        tx = t + (S.clear_between_sides - tw) / 2
        ty = G.table_z_display - e * 9.0
        out.append(box(col("table", GREEN), tx, ty, 0, tw, tt - 0.25, td))
        out.append(box(col("table", PHEN), tx, ty + tt - 0.25, 0, tw, 0.25, td))
    if want("elev"):
        for x in (G.acme_x_left, G.acme_x_right):
            out.append(box(col("elev", STEEL), x - 0.25, S.base_thick - e * 4.0, G.acme_y_infeed - 0.25, 0.5, 12.0, 0.5))
            out.append(box(col("elev", BRONZE), x - 0.6, G.table_z_display - 1.0, G.acme_y_infeed - 0.6, 1.2, 1.0, 1.2))
    if want("drum"):
        dy = G.bearing_cl_z + e * 9.0
        out.append(cyl_x(col("drum", MDF), Wbox / 2, dy, G.bearing_cl_y, G.drum_length, S.drum_od / 2, 22))
    if want("shaft"):
        dy = G.bearing_cl_z + e * 9.0
        out.append(cyl_x(col("shaft", STEEL), Wbox / 2, dy, G.bearing_cl_y, S.shaft_length, S.shaft_od / 2, 14))
        for x in (t / 2, Wbox - t / 2):
            out.append(box(col("shaft", STEEL), x - 0.35, dy - 1.4, G.bearing_cl_y - 1.4, 0.7, 2.8, 2.8))
    if want("motor"):
        mz = -6.5 - e * 10.0
        out.append(box(col("motor", KNOB), t + 1.5, S.motor_pivot_z, mz + 8.0, 6.0, 6.0, 7.0))
        out.append(cyl_x(col("motor", STEEL), Wbox + 1.1, G.bearing_cl_z + e * 3.0, G.bearing_cl_y, 0.9, S.pulley_drum_od / 2, 16))
    if want("rollers"):
        ry = G.table_z_display + G.table_thick + S.roller_od / 2 + e * 7.0
        for zoff in (-3.6, 3.6):
            out.append(cyl_x(col("rollers", KNOB), Wbox / 2, ry, G.bearing_cl_y + zoff, G.roller_len, S.roller_od / 2, 12))
            out.append(box(col("rollers", TAN), t, ry + 0.5, G.bearing_cl_y + zoff - 0.4, S.clear_between_sides, 0.4, 0.8))
    if want("hood"):
        dy = G.bearing_cl_z + e * 9.0
        for i in range(7):
            u = i / 6
            y = dy + 2.4 + math.sin(u * math.pi) * 2.6 + e * 9.0
            z = G.bearing_cl_y - 4.2 + u * 8.4
            out.append(box(col("hood", GREEN), t + 0.5, y, z - 0.7, S.clear_between_sides - 1.0, 0.35, 1.4))
    return out


# ---------------------------------------------------------------------------
# Shared page furniture
# ---------------------------------------------------------------------------


def release_banner(sh: Sheet, x: int = 36, y: int = 96) -> None:
    st = RELEASE_STATE
    label = f'{st["state"]}  ·  RISK {st["risk_class"]}'
    wpx = max(360, len(label) * 12 + 40)
    sh.rect(x, y, wpx, 34, fill=FLAG, stroke=INK, sw=1.2, rx=4)
    sh.text(x + 16, y + 24, label, 17, PAPER, bold=True)
    sh.text(x + wpx + 14, y + 23, "NOT FOR UNSUPERVISED ELECTRICAL WORK · VERIFY FLANGE BCD", 12, FLAG, bold=True)


def guide_titleblock(sh: Sheet, right: str = "", note: str = "") -> None:
    sh.titleblock(qty=right, material=note, evidence=RELEASE_STATE["state"])


def table_block(
    sh: Sheet,
    x: float,
    y: float,
    width: float,
    headers: list[tuple[str, float]],
    rows: list[list[str]],
    row_h: float = 20,
    size: int = 12,
    title: str = "",
) -> float:
    """Simple ruled table. Returns the y below the last row."""
    yy = y
    if title:
        sh.text(x, yy, title, 13, ACC, bold=True)
        yy += 22
    for label, dx in headers:
        sh.text(x + dx, yy, label, 11, DIM, bold=True)
    yy += 6
    sh.line(x, yy, x + width, yy, 1.0, INK)
    yy += row_h - 6
    for r in rows:
        for (_, dx), cell in zip(headers, r):
            sh.text(x + dx, yy, cell, size, INK, mono=False)
        yy += row_h
    return yy


# ---------------------------------------------------------------------------
# G-001 … G-004
# ---------------------------------------------------------------------------


def sheet_g001() -> None:
    sh = Sheet("G-001", "Master build guide — cover and release", "Read this page before cutting anything")
    guide_titleblock(sh, right=f"fab {S.fabrication_rev}", note=PROJECT["project_name"])
    release_banner(sh)

    sh.text(36, 168, "WALTER DS-16", 62, INK, bold=True, mono=False)
    sh.text(36, 202, "Dedicated drum thickness sander · master build plans", 18, DIM, mono=False)

    meshes = machine_meshes(
        ["base", "sides", "stretch", "ways", "table", "elev", "drum", "shaft", "motor", "rollers", "hood"]
    )
    assembly_frame(sh, 36, 226, 900, 520, "General arrangement — assembled", meshes)

    rows = [
        ["Capacity", f'{inch(S.capacity_width)}" wide · {S.min_stock_thickness:g}"–{S.max_stock_thickness:g}" thick'],
        ["Drum", f'⌀{inch(S.drum_od)}" × {inch(G.drum_length)}" @ ~{S.drum_rpm:g} RPM'],
        ["Motor", f'{S.motor_hp:g} HP {S.motor_rpm:g} RPM · {inch(S.pulley_motor_od)}"/{inch(S.pulley_drum_od)}" pulleys'],
        ["Quality spec", f'|A−B| ≤ {S.parallel_tol:.3f}" paper-on · TIR ≤ {S.drum_tir:.3f}"'],
        ["Table", f'{inch(G.table_width)}" × {inch(G.table_depth)}" torsion box in UHMW ways'],
        ["Inner span", f'{inch(S.clear_between_sides)}" (419 mm) — the controlling dimension'],
        ["Build steps", f"{len(build_steps())} numbered steps, ST-01 to ST-{len(build_steps()):02d}"],
        ["Units", "Inches controlling · millimetres reference only"],
    ]
    table_block(sh, 980, 250, 640, [("", 0), ("", 190)], rows, row_h=26, title="THE MACHINE")

    y = 500
    sh.text(980, y, "HOW TO USE THIS BOOK", 13, ACC, bold=True)
    yy = y + 22
    howto = [
        "Work the ST sheets in order. Each one is a single session with its own parts tray.",
        "A step sheet tells you what to fetch, what to do, and what must be true before you move on.",
        "When a step names a part, open that part's P-sheet for the full hole chart and dimensions.",
        "Grey geometry on a step illustration is already built. Colored geometry is what you add.",
        "Do not skip a QC gate. They are placed where a mistake is still cheap to fix.",
    ]
    for line in howto:
        for i, row in enumerate(_wrap(line, 58)):
            sh.text(980, yy, ("• " if i == 0 else "  ") + row, 12, NOTE, mono=False)
            yy += 16
        yy += 4

    yy += 10
    sh.text(980, yy, "RELEASE CONDITIONS — ALL MUST BE MET", 13, FLAG, bold=True)
    yy += 22
    for c in RELEASE_STATE["conditions"]:
        for i, row in enumerate(_wrap(c, 58)):
            sh.text(980, yy, ("☐ " if i == 0 else "   ") + row, 12, NOTE, mono=False)
            yy += 16
        yy += 4

    # The index lives under the isometric only. The right-hand column runs to
    # roughly y=830, so keeping the index inside x=36..940 avoids a collision.
    sh.text(36, 776, "SHEET INDEX", 13, ACC, bold=True)

    def idx(*want: str) -> list[tuple[str, str]]:
        return [
            (d["code"], d["title"].replace(d["code"], "").strip())
            for d in shop_drawings()
            if d["group"] in want
        ]

    columns = [
        (36, "Guide", idx("guide")),
        (268, "Build steps", [(st["id"], st["chapter"]) for st in build_steps()]),
        (500, "Parts", idx("part")),
        (732, "Assembly & overview", idx("assembly", "hardware", "index", "overview")),
    ]
    for xx, name, rows_g in columns:
        sh.text(xx, 798, name, 11, DIM, bold=True)
        yy = 816
        for code, label in rows_g:
            sh.text(xx, yy, code, 10, ACC, bold=True)
            sh.text(xx + 54, yy, label[:20], 10, INK, mono=False)
            yy += 13
            if yy > 1074:
                sh.text(xx, yy, "…", 10, DIM)
                break

    sh.text(36, Hpx - 96, PROJECT["lineage"], 12, DIM, mono=False)
    sh.save("G001_cover.svg")


def sheet_g002() -> None:
    sh = Sheet("G-002", "Design basis, parameters, and datums", "Everything downstream is computed from this page")
    guide_titleblock(sh, right="Python SSOT", note="cad/walter_ds16.py")
    release_banner(sh)

    sh.text(36, 160, "CONTROLLING PARAMETERS", 13, ACC, bold=True)
    rows = [
        ["capacity_width", f'{inch(S.capacity_width)}"', "VERIFIED", "Design intent"],
        ["clear_between_sides", f'{inch(S.clear_between_sides)}"', "VERIFIED", "Keep at 419 mm even with 18 mm ply"],
        ["ply_actual", f'{S.ply_actual:g}"', "USER_MEASURE", "Measure before cutting (ST-01)"],
        ["drum_od", f'⌀{inch(S.drum_od)}"', "VERIFIED", "Sets surface speed"],
        ["disc_thick × count", f'{S.disc_thick:g}" × {S.disc_count_core + S.disc_count_ends}', "VERIFIED", "Gives drum length"],
        ["bearing_cl_z", f'{inch(S.bearing_cl_z)}"', "VERIFIED layout", "From floor datum"],
        ["way_z", f'{inch(S.way_z)}"', "VERIFIED layout", "Way bottom from floor"],
        ["flange_bolt_square", f'{S.flange_bolt_square:g}"', "ASSUMED", "Transfer the bearing you buy"],
        ["slide_clearance", f'{S.slide_clearance:.3f}"', "DERIVED", "Per side, table in ways"],
        ["stretcher_housing", f'{S.stretcher_housing:g}"', "DERIVED", "Dado depth each end"],
    ]
    y = table_block(
        sh,
        36,
        184,
        900,
        [("PARAMETER", 0), ("VALUE", 250), ("EVIDENCE", 360), ("NOTE", 500)],
        rows,
        row_h=22,
    )

    sh.text(36, y + 16, "DERIVED GEOMETRY — do not edit these by hand", 13, ACC, bold=True)
    eq_rows = [
        ["overall_width", f'{inch(G.overall_width)}"', "clear + 2 × ply_actual"],
        ["table_width", f'{inch(G.table_width)}"', "capacity + 2 × margin"],
        ["way_project", f'{G.way_project:.3f}"', "(clear − table_width)/2 − slide_clearance"],
        ["way_rebate", f'{G.way_rebate:.3f}"', "way_stock − way_project"],
        ["stretcher_length", f'{inch(G.stretcher_length)}"', "clear + 2 × housing"],
        ["drum_length", f'{inch(G.drum_length)}"', "disc count × disc_thick"],
        ["surface_fpm", f"{G.surface_fpm:g} sfpm", "π × drum_od / 12 × drum_rpm"],
        ["acme_per_turn", f'{G.acme_per_turn:.4f}"', "1 / acme_tpi"],
    ]
    y2 = table_block(
        sh,
        36,
        y + 40,
        900,
        [("VALUE", 0), ("RESULT", 250), ("EQUATION", 360)],
        eq_rows,
        row_h=22,
    )

    sh.text(36, y2 + 16, "DATUMS", 13, ACC, bold=True)
    yy = y2 + 40
    for d in datums():
        sh.text(36, yy, d["id"], 12, ACC, bold=True)
        sh.text(146, yy, f'{d["on"]} · {d["what"]}', 12, INK, mono=False)
        sh.text(470, yy, d["use"][:52], 12, DIM, mono=False)
        yy += 20

    sh.text(980, 160, "WHY THE GEOMETRY IS WHAT IT IS", 13, ACC, bold=True)
    yy = 184
    for d in decisions():
        sh.text(980, yy, d["id"], 12, ACC, bold=True)
        yy += 16
        for row in _wrap(d["decision"], 56):
            sh.text(1046, yy, row, 12, INK, mono=False)
            yy += 15
        for row in _wrap("Because: " + d["reason"], 56):
            sh.text(1046, yy, row, 11, DIM, mono=False)
            yy += 14
        yy += 8
        if yy > 1010:
            break

    sh.text(980, 1040, "Change a parameter, regenerate, and every sheet, CSV, and", 12, DIM, mono=False)
    sh.text(980, 1056, "the 3D model follow. Never edit a number on a drawing.", 12, DIM, mono=False)
    sh.save("G002_design_basis.svg")


def sheet_g003() -> None:
    sh = Sheet("G-003", "Evidence, calculations, and revisions", "What is measured, derived, assumed, or still to verify")
    guide_titleblock(sh, right="Audit trail")
    release_banner(sh)

    sh.text(36, 160, "EVIDENCE CLASSES USED IN THIS PACKAGE", 13, ACC, bold=True)
    ev = [
        ["VERIFIED", "Stated design intent or a dimension fixed by the spec", "Capacity, drum OD, inner span"],
        ["DERIVED", "Computed from parameters by a shown equation", "way_project, stretcher_length, drum_length"],
        ["USER_MEASURE", "You must measure it in your shop and regenerate", "ply_actual"],
        ["ASSUMED", "Placeholder until the real component is in hand", "flange bolt square, nut block size"],
        ["ESTIMATED", "Sized from practice, trim on first fit", "Hood blank, rib quantity"],
        ["TEST-BASED", "Established by a measurement on the built machine", "TIR, |A−B|, witness scatter"],
        ["PROFESSIONAL", "Requires a qualified person before use", "Motor circuit, switch, grounding"],
    ]
    y = table_block(
        sh,
        36,
        184,
        920,
        [("CLASS", 0), ("MEANING", 150), ("WHERE IT APPEARS", 560)],
        ev,
        row_h=24,
    )

    sh.text(36, y + 20, "CALCULATION REGISTER", 13, ACC, bold=True)
    calc = [
        [
            "C-01",
            "Will the table fit between the ways?",
            f'clear {inch(S.clear_between_sides)}" − table {inch(G.table_width)}" = {inch(S.clear_between_sides - G.table_width)}" total',
            f'{G.way_project:.3f}" project + {S.slide_clearance:.3f}"/side — PASS',
        ],
        [
            "C-02",
            "Drum surface speed",
            f"π × {S.drum_od:g}/12 × {S.drum_rpm:g}",
            f"{G.surface_fpm:g} sfpm — in the sanding band",
        ],
        [
            "C-03",
            "Does the lift cover the thickness range?",
            f'{S.max_stock_thickness:g}" − {S.min_stock_thickness:g}" = {S.max_stock_thickness - S.min_stock_thickness:g}" needed',
            f'{S.elev_travel:g}" travel available — PASS',
        ],
        [
            "C-04",
            "Fine adjustment resolution",
            f"1 / {S.acme_tpi:g} TPI",
            f'{G.acme_per_turn:.4f}"/turn — finer than the {S.parallel_tol:.3f}" spec',
        ],
        [
            "C-05",
            "Does the drum clear the side panels?",
            f'drum {inch(G.drum_length)}" in {inch(S.clear_between_sides)}" span',
            f'{G.drum_end_gap:.3f}" per end — PASS',
        ],
        [
            "C-06",
            "Is the housing shallow enough for the ply?",
            f'2 × {S.stretcher_housing:g}" + 0.25" vs {S.ply_actual:g}"',
            "PASS — validated on every regeneration",
        ],
    ]
    y2 = table_block(
        sh,
        36,
        y + 44,
        1600,
        [("ID", 0), ("QUESTION", 60), ("SUBSTITUTION", 480), ("RESULT", 1000)],
        calc,
        row_h=24,
    )

    sh.text(36, y2 + 20, "AUTOMATED CHECKS RUN ON EVERY REGENERATION", 13, ACC, bold=True)
    yy = y2 + 44
    checks = [
        "Table narrower than the inner span, and way projection greater than zero.",
        "Way rebate does not cut through the side panel.",
        "Drum shorter than the inner span; drum length still the 21-disc pack.",
        "Lift travel covers the full thickness range.",
        "Every part and hardware ID named in a build step exists in the registry.",
        "Every fabricated part is used by at least one build step.",
        "Every QC gate referenced by a step exists in the inspection plan.",
    ]
    for c in checks:
        sh.text(36, yy, "✓ " + c, 12, NOTE, mono=False)
        yy += 17
    errs = validate()
    sh.text(36, yy + 10, ("ALL CHECKS PASS" if not errs else "FAILING: " + "; ".join(errs)), 13, ACC if not errs else FLAG, bold=True)

    sh.text(980, y2 + 20, "REVISION HISTORY", 13, ACC, bold=True)
    yy = y2 + 44
    for r in revisions():
        sh.text(980, yy, r["rev"], 12, ACC, bold=True)
        for i, row in enumerate(_wrap(r["note"], 56)):
            sh.text(1046, yy, row, 11, INK, mono=False)
            yy += 15
        yy += 6
    sh.save("G003_registers.svg")


def sheet_g004() -> None:
    sh = Sheet("G-004", "Safety, risk, and what is not released", "Read before the first powered run")
    guide_titleblock(sh, right=f'RISK {RELEASE_STATE["risk_class"]}')
    release_banner(sh)

    sh.text(36, 162, "WHY THIS IS AN R3 MACHINE", 13, ACC, bold=True)
    yy = 186
    for trig in RELEASE_STATE["risk_triggers"]:
        for i, row in enumerate(_wrap(trig, 58)):
            sh.text(36, yy, ("▲ " if i == 0 else "   ") + row, 12, NOTE, mono=False)
            yy += 17
        yy += 5

    yy += 10
    sh.text(36, yy, "NOT RELEASED BY THIS PACKAGE", 13, FLAG, bold=True)
    yy += 24
    for nr in RELEASE_STATE["not_released"]:
        for i, row in enumerate(_wrap(nr, 58)):
            sh.text(36, yy, ("✕ " if i == 0 else "   ") + row, 12, FLAG, mono=False)
            yy += 17
        yy += 5

    yy += 12
    sh.text(36, yy, "STANDING RULES", 13, ACC, bold=True)
    yy += 24
    rules = [
        "Hood on is the primary guard. Open it only stopped and unplugged.",
        "Hands never under the drum or between the hold-down rollers.",
        "Minimum stock ~12″ long, or carry it on the sled.",
        "Light passes. If the motor bogs, back off — do not push harder.",
        "Respirator, eye, and hearing protection. MDF truing is the worst of it.",
        "Dust extraction running before the drum spins.",
        "Unplug before any adjustment behind the hood.",
    ]
    for r in rules:
        for i, row in enumerate(_wrap(r, 58)):
            sh.text(36, yy, ("• " if i == 0 else "  ") + row, 12, NOTE, mono=False)
            yy += 17
        yy += 3

    rows = [[f["mode"], f["cause"], f["effect"], f["mitigation"], f["sev"]] for f in fmea()]
    table_block(
        sh,
        740,
        170,
        880,
        [("FAILURE MODE", 0), ("CAUSE", 210), ("EFFECT", 430), ("DESIGNED MITIGATION", 590), ("SEV", 850)],
        rows,
        row_h=34,
        size=11,
        title="FAILURE MODES DESIGNED AGAINST",
    )

    sh.text(740, 480, "FIRST POWERED RUN — IN THIS ORDER", 13, ACC, bold=True)
    yy = 504
    first = [
        "Hood fitted. Dust hose connected. No stock on the table.",
        "Table lowered well clear of the drum.",
        "Spin the drum by hand one full turn. Listen for contact.",
        "Stand clear of both drum ends, hand on the switch, and start it.",
        "Let it come up to speed. Listen for imbalance or rubbing. Shut down.",
        "Only then true the drum, wrap paper, and clock A/B (ST-14).",
    ]
    for i, f in enumerate(first, 1):
        for j, row in enumerate(_wrap(f, 58)):
            sh.text(740, yy, (f"{i}. " if j == 0 else "   ") + row, 12, NOTE, mono=False)
            yy += 17
        yy += 4

    sh.text(740, yy + 14, "PPE AT EVERY STEP", 13, ACC, bold=True)
    sh.text(740, yy + 38, "Eyes · ears · respirator · no gloves near the drum · no loose sleeves.", 12, NOTE, mono=False)
    sh.save("G004_safety.svg")


# ---------------------------------------------------------------------------
# E-101 exploded with balloons
# ---------------------------------------------------------------------------


def sheet_e101() -> None:
    sh = Sheet("E-101", "Exploded assembly with item balloons", "Balloon numbers resolve to the BOM on this sheet")
    guide_titleblock(sh, right="Explosion 1 axis")
    release_banner(sh)

    # Balloon order is the order a builder meets the parts, not drawing order.
    balloons = [
        (1, "sides", "P-001L/R", "Side panels"),
        (2, "base", "P-002", "Base deck"),
        (3, "stretch", "P-003", "Stretchers ×3"),
        (4, "ways", "P-007", "UHMW ways ×2"),
        (5, "drum", "P-008", "Drum discs"),
        (6, "shaft", "P-010", "Shaft + bearings"),
        (7, "motor", "P-012", "Motor, cradle, pulleys"),
        (8, "table", "P-004", "Table box + wear face"),
        (9, "elev", "P-016", "Acme lift + nut blocks"),
        (10, "rollers", "P-014", "Hold-down yokes"),
        (11, "hood", "P-011", "Dust hood"),
    ]
    order = [b[1] for b in balloons]
    per_group = machine_groups(order, explode=1.0)
    flat = [m for gid in order for m in per_group.get(gid, [])]
    fx, fy, fw, fh = 36, 150, 1020, 800
    tf = assembly_frame(
        sh, fx, fy, fw, fh, "Exploded — parts held in assembly orientation, separation exaggerated", flat
    )

    # Place each balloon just outside its part, nudged until it stops colliding
    # with a balloon already placed. Every balloon gets a leader to real geometry.
    placed: list[tuple[float, float]] = []
    ccx, ccy = fx + fw / 2, fy + fh / 2
    for num, gid, pid, label in balloons:
        meshes = per_group.get(gid)
        if not meshes:
            continue
        ax, ay = group_anchor(meshes, tf)
        vx, vy = ax - ccx, ay - ccy
        mag = math.hypot(vx, vy) or 1.0
        bx, by = ax + vx / mag * 92, ay + vy / mag * 92
        for _ in range(28):
            bx = min(max(bx, fx + 22), fx + fw - 22)
            by = min(max(by, fy + 30), fy + fh - 22)
            if all(math.hypot(bx - px, by - py) > 42 for px, py in placed):
                break
            by += 40
            if by > fy + fh - 22:
                by = fy + 40
                bx += 46
        placed.append((bx, by))
        sh.line(ax, ay, bx, by, 0.9, INK)
        sh.circle(ax, ay, 2.6, fill=INK, stroke=INK, sw=0.5)
        sh.circle(bx, by, 15, fill=PAPER, stroke=INK, sw=1.6)
        sh.text(bx, by + 5, str(num), 14, INK, "middle", bold=True)

    sh.text(1090, 170, "BOM — BALLOON ORDER", 13, ACC, bold=True)
    rows = []
    by_id = {p["part_id"]: p for p in parts()}
    for num, gid, pid, label in balloons:
        p = by_id.get(pid, {})
        qty = p.get("qty", "")
        size = (p.get("finished_size") or p.get("purchase_size") or "")[:26]
        rows.append([str(num), pid, label, str(qty), size])
    table_block(
        sh,
        1090,
        196,
        530,
        [("#", 0), ("ID", 34), ("PART", 130), ("QTY", 300), ("FINISHED", 350)],
        rows,
        row_h=26,
        size=11,
    )

    y = 520
    sh.text(1090, y, "HARDWARE STACK ORDER", 13, ACC, bold=True)
    yy = y + 24
    stacks = [
        "Flange bearing: bolt → washer → panel → flange → nylock. Drive side torqued, idler side snug.",
        "Roller yoke: shoulder bolt → yoke → spring → washer → star knob.",
        "Acme: screw → bronze nut in block → block bolted up into the table underside.",
        "Stretcher: screw from OUTSIDE the panel into the housed rail end.",
    ]
    for s_ in stacks:
        for i, row in enumerate(_wrap(s_, 56)):
            sh.text(1090, yy, ("• " if i == 0 else "  ") + row, 12, NOTE, mono=False)
            yy += 16
        yy += 6

    yy += 8
    sh.text(1090, yy, "ASSEMBLY ORDER", 13, ACC, bold=True)
    yy += 24
    for st in build_steps():
        if st["parts"]:
            sh.text(1090, yy, st["id"], 11, ACC, bold=True)
            sh.text(1152, yy, ", ".join(st["parts"])[:44], 11, INK, mono=False)
            yy += 16
    sh.text(1090, yy + 14, "Full sequence on the ST sheets. This page is the map.", 12, DIM, mono=False)
    sh.save("E101_exploded.svg")


# ---------------------------------------------------------------------------
# ST-01 … ST-14 step sheets
# ---------------------------------------------------------------------------


def part_tray(sh: Sheet, x: float, y: float, width: float, st: dict) -> float:
    """LEGO-style parts tray: what to have on the bench before you start."""
    by_id = {p["part_id"]: p for p in parts()}
    hw_id = {h["hardware_id"]: h for h in hardware()}
    sh.rect(x, y, width, 30, fill=ACC, stroke=INK, sw=1.2)
    sh.text(x + 12, y + 21, "PARTS TRAY — fetch these before you start", 13, PAPER, bold=True)
    yy = y + 30
    box_h = 0
    rows: list[tuple[str, list[str], str, str]] = []
    for pid in st["parts"]:
        p = by_id.get(pid, {})
        rows.append(
            (
                pid,
                _wrap(p.get("part_name", ""), 34),
                str(p.get("qty", "")),
                (p.get("finished_size") or p.get("purchase_size") or "")[:22],
            )
        )
    for hid in st["hardware"]:
        h = hw_id.get(hid, {})
        rows.append((hid, _wrap(h.get("description", ""), 34), str(h.get("qty", "")), ""))
    if not rows:
        rows = [("—", ["No parts. This is a measure and plan step."], "", "")]
    body_h = sum(max(1, len(r[1])) * 17 for r in rows) + 20
    sh.rect(x, yy, width, body_h, fill=LIGHT, stroke=INK, sw=1.0)
    yy += 22
    for pid, name_rows, qty, size in rows:
        is_hw = pid.startswith("H-")
        sh.text(x + 12, yy, pid, 12, BRONZE if is_hw else ACC, bold=True)
        for i, row in enumerate(name_rows):
            sh.text(x + 92, yy + i * 17, row, 12, INK, mono=False)
        if qty:
            sh.text(x + 452, yy, f"x{qty}", 12, DIM, bold=True)
        if size:
            sh.text(x + 500, yy, size, 11, DIM)
        yy += max(1, len(name_rows)) * 17
    yy += 12
    if st["tools"]:
        for i, row in enumerate(_wrap("TOOLS: " + " · ".join(st["tools"]), 74)):
            sh.text(x + 12, yy, row, 11, DIM, mono=False)
            yy += 16
    if st["sheets"]:
        for i, row in enumerate(_wrap("OPEN THESE SHEETS: " + " · ".join(st["sheets"]), 74)):
            sh.text(x + 12, yy, row, 11, ACC, mono=False)
            yy += 16
    return yy + box_h


def sheet_step(st: dict) -> None:
    sh = Sheet(
        st["id"],
        st["title"],
        f'Step {st["step"]} of {st["of"]}  ·  {st["chapter"]}',
        subtitle=st["goal"],
    )
    guide_titleblock(sh, right=f'STEP {st["step"]} / {st["of"]}', note=st["chapter"])

    # progress pips across the top — where you are in the book
    px, py = 36, 104
    for i in range(1, st["of"] + 1):
        cx = px + (i - 1) * 26
        done = i < st["step"]
        now = i == st["step"]
        sh.circle(cx + 8, py + 8, 9, fill=ACC if now else (MUTE if done else PAPER), stroke=INK, sw=1.1)
        sh.text(cx + 8, py + 12, str(i), 10, PAPER if now else DIM, "middle", bold=now)
    sh.text(px + st["of"] * 26 + 20, py + 13, f'{st["chapter"]}', 12, DIM, bold=True)

    # illustration: already-built geometry ghosted grey, this step's work in colour
    built = st["shows"]
    new_groups = st["adds"] or built
    meshes = machine_meshes(built, highlight=new_groups)
    if meshes:
        caption = (
            "Grey = already built · colour = this step"
            if st["adds"] and len(st["adds"]) < len(built)
            else "This step"
        )
        assembly_frame(sh, 36, 150, 820, 560, caption, meshes)
    else:
        sh.rect(36, 150, 820, 560, fill=LIGHT, stroke=INK, sw=1.0)
        sh.text(446, 420, "STOCK PREPARATION — NO ASSEMBLY YET", 15, DIM, "middle", bold=True)
        sh.text(446, 448, "Measure and label. The machine starts at ST-03.", 12, DIM, "middle", mono=False)

    # actions
    sh.text(36, 748, "DO THIS", 14, ACC, bold=True)
    yy = 774
    for i, act in enumerate(st["actions"], 1):
        sh.circle(46, yy - 5, 11, fill=ACC, stroke=INK, sw=1.0)
        sh.text(46, yy - 1, str(i), 11, PAPER, "middle", bold=True)
        for j, row in enumerate(_wrap(act, 84)):
            sh.text(68, yy, row, 13, NOTE, mono=False)
            yy += 18
        yy += 8

    # right column: tray, gate, warnings
    ty = part_tray(sh, 900, 150, 720, st)

    ty += 6
    sh.rect(900, ty, 720, 30, fill=GREEN, stroke=INK, sw=1.2)
    gate_label = "BEFORE YOU MOVE ON" + (f'   ({st["qc"]})' if st["qc"] else "")
    sh.text(912, ty + 21, gate_label, 13, PAPER, bold=True)
    yy = ty + 52
    for row in _wrap(st["gate"], 62):
        sh.text(912, yy, row, 13, INK, mono=False)
        yy += 18
    yy += 6
    if st["hold"]:
        for i, row in enumerate(_wrap("HOLD POINT: " + st["hold"], 62)):
            sh.text(912, yy, row, 12, ACC, mono=False, bold=(i == 0))
            yy += 17
        yy += 6
    if st["correctable"]:
        for i, row in enumerate(_wrap("Still correctable after this step: " + st["correctable"], 62)):
            sh.text(912, yy, row, 12, DIM, mono=False)
            yy += 17
        yy += 6
    if st["warn"]:
        wh = 26 + 18 * len(_wrap(st["warn"], 60))
        sh.rect(900, yy, 720, wh, fill="#f6e7e4", stroke=FLAG, sw=1.4)
        yy += 20
        for i, row in enumerate(_wrap(st["warn"], 60)):
            sh.text(914, yy, ("⚠ " if i == 0 else "   ") + row, 12, FLAG, mono=False, bold=(i == 0))
            yy += 18

    sh.save(f'ST{st["step"]:02d}_step.svg')


# ---------------------------------------------------------------------------
# Q-101 commissioning
# ---------------------------------------------------------------------------


def sheet_q101() -> None:
    sh = Sheet("Q-101", "Commissioning and acceptance", "Sign this page off before the machine does real work")
    guide_titleblock(sh, right="Record the numbers")
    release_banner(sh)

    rows = [[q["qc"], q["check"], q["spec"][:58], q["class"], q["gate"], "☐"] for q in inspection()]
    y = table_block(
        sh,
        36,
        166,
        1580,
        [("QC", 0), ("CHECK", 70), ("SPECIFICATION", 250), ("CLASS", 900), ("GATE", 980), ("PASS", 1070)],
        rows,
        row_h=26,
        size=11,
        title="INSPECTION PLAN — every gate must be signed",
    )

    sh.text(36, y + 24, "CALIBRATION SEQUENCE", 13, ACC, bold=True)
    yy = y + 48
    for i, c in enumerate(calibration_steps(), 1):
        sh.text(36, yy, f'{i}. {c["title"]}', 12, ACC, bold=True)
        yy += 17
        for row in _wrap(c["body"], 74):
            sh.text(56, yy, row, 11, NOTE, mono=False)
            yy += 15
        yy += 6

    sh.text(900, y + 24, "RECORD YOUR MEASUREMENTS", 13, ACC, bold=True)
    yy = y + 48
    fields = [
        ("Measured ply thickness", 'in'),
        ("Inner span, top / mid / bottom", 'in'),
        ("Table flatness, both diagonals", 'in'),
        ("Drum TIR, paper off", 'in'),
        ("A reading (drive), paper on", 'in'),
        ("B reading (idler), paper on", 'in'),
        ("|A − B|", 'in'),
        ("Witness board, four corners", 'in'),
        ("Roller set below drum", 'in'),
        ("Date commissioned", ''),
        ("Built and checked by", ''),
    ]
    for label, unit in fields:
        sh.text(900, yy, label, 12, NOTE, mono=False)
        sh.line(1330, yy + 4, 1560, yy + 4, 1.0, INK)
        if unit:
            sh.text(1570, yy, unit, 11, DIM)
        yy += 30

    yy += 10
    sh.text(900, yy, "PASS SCHEDULE — after acceptance", 13, ACC, bold=True)
    yy += 24
    for p in pass_schedule():
        sh.text(900, yy, f'{p["grit"]} grit', 12, ACC, bold=True)
        sh.text(990, yy, f'{p["depth"]} per pass', 12, INK, mono=False)
        sh.text(1150, yy, p["use"][:40], 12, DIM, mono=False)
        yy += 20

    # No separate targets block here: every acceptance figure is already in the
    # inspection plan above. Restating it would be a second place to disagree.
    sh.text(900, yy + 18, f"Acceptance figures are the QC rows above. {len(quality_targets())} of them", 12, DIM, mono=False)
    sh.text(900, yy + 34, "are measured on the machine, not taken from the drawing.", 12, DIM, mono=False)

    sh.save("Q101_commissioning.svg")


def main() -> None:
    errs = validate()
    if errs:
        raise SystemExit("SSOT invalid, refusing to draw: " + "; ".join(errs))
    sheet_g001()
    sheet_g002()
    sheet_g003()
    sheet_g004()
    sheet_e101()
    for st in build_steps():
        sheet_step(st)
    sheet_q101()
    print("done →", OUT, f"({6 + len(build_steps())} guide sheets)")


if __name__ == "__main__":
    main()
