#!/usr/bin/env python3
"""Export MARTIN fabrication package from martin_kernel (single source of truth).

Writes JSON/CSV, shop drawings, 1:1 templates, DXF, OpenSCAD, labels, and
app-facing fab.json. Run from repo root:

  python3 scripts/export_martin_fab.py
"""

from __future__ import annotations

import csv
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "fence", "martin"))

from martin_kernel import PROJECT, MM, build_project, inch_mm, layout, v  # noqa: E402

FAB = os.path.join(ROOT, "fence", "martin", "fab")
SCAD = os.path.join(ROOT, "fence", "martin", "cad", "scad")


def ensure(*paths):
    for p in paths:
        os.makedirs(p, exist_ok=True)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote", os.path.relpath(path, ROOT))


def csv_write(path, rows, fieldnames):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})
    print("wrote", os.path.relpath(path, ROOT))


# ---- SVG sheet --------------------------------------------------------------
W, Hpx = 1680, 1188
INK, DIM, ACC, PAPER, LIGHT = "#1a1f24", "#5a6a4a", "#3d5a4c", "#f3f1ec", "#c5c8c2"
GRAY = "#6e7578"
MONO = "font-family='IBM Plex Mono, Menlo, monospace'"
SER = "font-family='Georgia, serif'"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Sheet:
    def __init__(self, code, title, note):
        self.code, self.title, self.note = code, title, note
        self.b = []

    def add(self, s):
        self.b.append(s)

    def line(self, x1, y1, x2, y2, w=2, color=INK, dash=None):
        d = f" stroke-dasharray='{dash}'" if dash else ""
        self.add(
            f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' "
            f"stroke='{color}' stroke-width='{w}'{d}/>"
        )

    def rect(self, x, y, w, h, fill="none", stroke=INK, sw=2, dash=None):
        d = f" stroke-dasharray='{dash}'" if dash else ""
        self.add(
            f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' "
            f"fill='{fill}' stroke='{stroke}' stroke-width='{sw}'{d}/>"
        )

    def poly(self, pts, fill="none", stroke=INK, sw=2, close=True):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        tag = "polygon" if close else "polyline"
        self.add(f"<{tag} points='{p}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}'/>")

    def text(self, x, y, s, size=16, color=INK, anchor="start", mono=True, bold=False, rot=None):
        f = MONO if mono else SER
        wgt = " font-weight='600'" if bold else ""
        r = f" transform='rotate({rot} {x:.1f} {y:.1f})'" if rot is not None else ""
        self.add(
            f"<text x='{x:.1f}' y='{y:.1f}' {f} font-size='{size}' fill='{color}' "
            f"text-anchor='{anchor}'{wgt}{r}>{esc(s)}</text>"
        )

    def dim_h(self, x1, x2, y, label, offset=28, size=14):
        yy = y + offset
        for x in (x1, x2):
            self.line(x, y, x, yy + 6, 1, DIM)
        self.line(x1, yy, x2, yy, 1.3, DIM)
        self.text((x1 + x2) / 2, yy - 5, label, size, DIM, "middle")

    def dim_v(self, y1, y2, x, label, offset=28, size=14):
        xx = x + offset
        for y in (y1, y2):
            self.line(x, y, xx + 6, y, 1, DIM)
        self.line(xx, y1, xx, y2, 1.3, DIM)
        self.text(xx + 10, (y1 + y2) / 2, label, size, DIM)

    def titleblock(self):
        self.rect(0, 0, W, Hpx, fill=PAPER, stroke=INK, sw=3)
        self.rect(24, 24, W - 48, Hpx - 48, fill="none", stroke=INK, sw=1)
        self.line(24, Hpx - 88, W - 24, Hpx - 88, 1.4)
        self.text(40, Hpx - 56, "MARTIN", 26, ACC, bold=True, mono=False)
        self.text(170, Hpx - 58, f"{self.code}  ·  {self.title}", 16, INK, bold=True)
        self.text(40, Hpx - 34, self.note, 12, DIM)
        self.text(W - 40, Hpx - 56, f"Rev {PROJECT['REVISION']}  ·  inches  ·  kernel 3.0", 13, DIM, "end")
        self.text(W - 40, Hpx - 34, "PARAMETRIC — do not scale. Datum: pad top / latch face x=0", 12, DIM, "end")

    def save(self, folder, filename):
        path = os.path.join(folder, filename)
        svg = (
            f"<?xml version='1.0' encoding='UTF-8'?>\n"
            f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{Hpx}' "
            f"viewBox='0 0 {W} {Hpx}'>\n" + "\n".join(self.b) + "\n</svg>\n"
        )
        write(path, svg)


def dxf_rect(lines, x, y, w, h, layer="0"):
    pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
    for a, b in zip(pts, pts[1:]):
        lines.append(f"0\nLINE\n8\n{layer}\n10\n{a[0]:.4f}\n20\n{a[1]:.4f}\n11\n{b[0]:.4f}\n21\n{b[1]:.4f}\n")


def write_dxf(path, entities_fn):
    body = ["0\nSECTION\n2\nENTITIES\n"]
    entities_fn(body)
    body.append("0\nENDSEC\n0\nEOF\n")
    write(path, "".join(body))


# ---- OpenSCAD ---------------------------------------------------------------
def write_scad(proj):
    ly = proj["layout"]
    p = []
    p.append("// AUTO-GENERATED from martin_kernel.py — do not edit by hand\n")
    p.append("// Units: millimetres\n")
    mapping = {
        "overall_length": ly["overall_length"],
        "overall_height": ly["overall_height"],
        "post_x": v("post_x"),
        "post_y": v("post_y"),
        "rail_t": v("rail_t"),
        "rail_h": v("rail_h"),
        "cap_t": v("cap_t"),
        "cap_w": v("cap_w"),
        "board_t": v("board_t"),
        "board_w": v("board_w"),
        "board_gap": v("board_gap"),
        "gate_clear": v("gate_clear"),
        "nuki_len": ly["nuki_len"],
        "nuki_x0": ly["nuki_x0"],
        "bay_clear": ly["bay_clear"],
        "post_blank_l": ly["post_blank_l"],
        "post_body_h": ly["post_body_h"],
        "post_tenon_x": v("post_tenon_x"),
        "post_tenon_y": v("post_tenon_y"),
        "post_tenon_h": v("post_tenon_h"),
        "gate_h": ly["gate_h"],
        "gate_leaf_w": ly["gate_leaf_w"],
        "gate_bottom_clear": v("gate_bottom_clear"),
        "pad_len": ly["pad_len"],
        "pad_width": v("pad_width"),
        "pad_thick": v("pad_thick"),
        "pier_xy": v("pier_xy"),
        "pier_h": v("pier_h"),
        "drop_off": v("drop_off"),
        "rail_cl_1": v("rail_cl_1"),
        "rail_cl_2": v("rail_cl_2"),
        "rail_cl_3": v("rail_cl_3"),
        "n_bay": ly["n_bay"],
        "board_inset": ly["board_inset"],
        "cap_x0": ly["cap_x0"],
        "cap_len": ly["cap_len"],
    }
    for k, val in mapping.items():
        if k == "n_bay":
            p.append(f"{k} = {int(val)};\n")
        else:
            p.append(f"{k} = {round(inch_mm(val), 2)};\n")
    p.append("post_cx = [%s];\n" % ", ".join(f"{round(inch_mm(x['cx']), 2)}" for x in ly["posts"]))
    p.append("rail_cls = [%s];\n" % ", ".join(f"{round(inch_mm(c), 2)}" for c in ly["rail_cls"]))
    write(os.path.join(SCAD, "parameters.scad"), "".join(p))

    write(
        os.path.join(SCAD, "parts.scad"),
        """// Semantic parts — millimetres. Include parameters.scad first.
include <parameters.scad>;

module L_post(part_id="L-001") {
    // blank standing on tenon tip at z=-post_tenon_h
    cube([post_x, post_y, post_body_h]);
    translate([(post_x-post_tenon_x)/2, (post_y-post_tenon_y)/2, -post_tenon_h])
        cube([post_tenon_x, post_tenon_y, post_tenon_h]);
}

module R_nuki(part_id="R-001") {
    cube([nuki_len, rail_t, rail_h]);
}

module C_cap() { cube([cap_len, cap_w, cap_t]); }

module B_board(h) { cube([board_w, board_t, h]); }

module F_pad() { cube([pad_len, pad_width, pad_thick]); }

module F_pier() { cube([pier_xy, pier_xy, pier_h]); }
""",
    )
    write(
        os.path.join(SCAD, "joinery.scad"),
        """// Joinery cutters (nuki mortise, kusabi slot, sleeve pocket)
include <parameters.scad>;
module nuki_mortise() {
    cube([post_x+2, rail_t+1, rail_h+1], center=true);
}
module kusabi_slot() {
    cube([0.625*25.4, post_y+2, 1.125*25.4], center=true);
}
""",
    )
    write(
        os.path.join(SCAD, "assemblies.scad"),
        """include <parameters.scad>;
include <parts.scad>;

module A010_posts() {
    for (i=[0:3]) {
        translate([post_cx[i]-post_x/2, -post_y/2, 0]) L_post();
    }
}
module A020_rails() {
    for (z=rail_cls)
        translate([nuki_x0, -rail_t/2, z-rail_h/2]) R_nuki();
}
module A001_base() {
    translate([-6*25.4, -pad_width/2, -pad_thick]) F_pad();
    for (i=[0:3])
        translate([post_cx[i]-pier_xy/2, -pier_xy/2, -pier_h]) F_pier();
}
module A000_master() {
    A001_base();
    A010_posts();
    A020_rails();
    translate([cap_x0, -cap_w/2, overall_height-cap_t]) C_cap();
}
""",
    )
    write(
        os.path.join(SCAD, "metadata.scad"),
        f"""// echo metadata for parsers
echo("PROJECT={PROJECT['PROJECT_ID']}");
echo("REVISION={PROJECT['REVISION']}");
echo("UNITS=mm (generated from inch kernel)");
""",
    )
    write(
        os.path.join(SCAD, "main.scad"),
        """// MARTIN — OpenSCAD assembly (generated)
include <parameters.scad>;
use <assemblies.scad>;
A000_master();
""",
    )
    write(
        os.path.join(SCAD, "export.scad"),
        """include <parameters.scad>;
use <assemblies.scad>;
A000_master();
""",
    )


# ---- drawings ---------------------------------------------------------------
def drawings(proj):
    ddir = os.path.join(FAB, "06_DRAWINGS")
    tdir = os.path.join(FAB, "10_TEMPLATES")
    qdir = os.path.join(FAB, "12_QA")
    ensure(ddir, tdir, qdir)
    ly = proj["layout"]
    S = 8.0
    OX, OY = 80, 820

    def X(xin):
        return OX + xin * S

    def Y(zin):
        return OY - zin * S

    # G-000
    s = Sheet("G-000", "Cover / index", "Rev C fabrication model · Buffalo NY")
    s.titleblock()
    s.text(40, 70, "MARTIN — DIGITAL MANUFACTURING DEFINITION", 22, ACC, bold=True, mono=False)
    s.text(40, 100, "Prairie removable fence  ·  143″ × 65″  ·  Japanese joinery  ·  no nails in timber", 14, DIM)
    rows = [
        "WHAT  Freestanding winter-removable privacy fence + locking gate",
        "FROM  Dimensional lumber (paint-grade) + 4000 psi AE concrete + sleeves",
        "SIZE  overall_length=143.000  overall_height=65.000  gate_clear=36.000 (ASSUMED)",
        "QTY   One run; part quantities in S-601",
        "CONNECT  nuki+kusabi, hozo drawbore, foot tenon/sleeve, floating grooves",
        "MAKE  See routings + AS-01..12  ·  MEASURE from pad-shoulder datum",
        "ASSEMBLE  Base → posts → rails → boards → cap → gate → latch",
        "CHECK  QA-701  ·  CHANGE  edit kernel P[] then re-export",
    ]
    for i, r in enumerate(rows):
        s.text(40, 140 + i * 28, r, 14)
    s.text(40, 390, "DRAWING INDEX", 16, ACC, bold=True)
    y = 420
    for d in proj["drawing_index"]:
        s.text(40, y, f"{d['DWG']:7}  {d['TITLE']}", 13)
        y += 18
        if y > 980:
            break
    s.text(900, 390, "UNRESOLVED (TBM)", 16, ACC, bold=True)
    y = 420
    for u in proj["unresolved"]:
        s.text(900, y, f"{u['ID']}  {u['ITEM']}  [{u['CLASS']}]", 13)
        y += 22
    s.save(ddir, "G-000_cover.svg")

    # GA-110 elevation
    s = Sheet("GA-110", "Front elevation", "Scale ~1:16  ·  datums at pad top / x=0")
    s.titleblock()
    L, H = ly["overall_length"], ly["overall_height"]
    s.rect(X(-v("pad_overhang")), Y(0), (L + 2 * v("pad_overhang")) * S, v("pad_thick") * S, fill=LIGHT)
    for p in ly["posts"]:
        s.rect(X(p["cx"] - v("post_x") / 2), Y(ly["post_body_h"]), v("post_x") * S, ly["post_body_h"] * S, fill="#d9dcde")
        s.text(X(p["cx"]), Y(H) - 16, p["id"], 12, ACC, "middle", bold=True)
    for cl in ly["rail_cls"]:
        s.rect(X(ly["nuki_x0"]), Y(cl + v("rail_h") / 2), ly["nuki_len"] * S, v("rail_h") * S, fill=GRAY)
    s.rect(X(ly["cap_x0"]), Y(H), ly["cap_len"] * S, v("cap_t") * S, fill="#8a9094")
    s.rect(X(v("post_x") + v("gate_gap")), Y(v("gate_bottom_clear") + ly["gate_h"]),
           ly["gate_leaf_w"] * S, ly["gate_h"] * S, fill="#e8eaeb", stroke=ACC, dash="5 4")
    s.dim_h(X(0), X(L), Y(0), '143.000" OVERALL  VERIFIED', offset=50)
    s.dim_h(X(v("post_x")), X(v("post_x") + v("gate_clear")), Y(0), '36.000" GATE CLEAR  ASSUMED', offset=78)
    s.dim_h(X(ly["posts"][1]["cx"] + v("post_x") / 2), X(ly["posts"][2]["cx"] - v("post_x") / 2),
            Y(H), f'{ly["bay_clear"]:.3f}" BAY  DERIVED', offset=-32)
    s.dim_v(Y(0), Y(H), X(L), '65.000"', offset=36)
    s.text(40, 70, "DATUM A: pad top  ·  DATUM B: latch-side outer face x=0  ·  grain: posts vertical, rails long", 13, DIM)
    s.save(ddir, "GA-110_elevation.svg")

    # copy as GA-100
    s2 = Sheet("GA-100", "General arrangement", "Same geometry as GA-110 with assembly notes")
    s2.titleblock()
    s2.text(40, 70, "See GA-110 for dimensions. Assemblies: A-001 BASE · A-010 POSTS · A-020 FRAME · A-030 GATE", 14)
    s2.text(40, 100, "Insertion: posts −Z into sleeves; rails +X through nuki; gate +Z onto pintles; boards drop −Z into grooves.", 14)
    for i, p in enumerate(ly["posts"]):
        s2.text(40, 150 + i * 24, f"{p['id']}  {p['mark']}  cx={p['cx']:.3f}\"  {p['role']}", 14)
    s2.text(40, 280, "Rev C: gate_h = H - cap_t - bottom_clear - top_clear = 62.000\" → 0.500\" cap clearance.", 14, ACC)
    s2.save(ddir, "GA-100_arrangement.svg")

    # GA-130 plan
    s = Sheet("GA-130", "Plan at pad", "Scale ~1:16  ·  looking down")
    s.titleblock()
    ps = 8.0
    px, py = 80, 400
    s.rect(px, py, (L + 12) * ps * 0.55, v("pad_width") * ps * 0.55, fill=LIGHT, stroke=INK)
    # simpler 1:20
    sc = 6.5
    s.rect(80, 200, ly["pad_len"] * sc, v("pad_width") * sc, fill=LIGHT)
    for p in ly["posts"]:
        s.rect(80 + (v("pad_overhang") + p["cx"] - v("post_x") / 2) * sc,
               200 + (v("pad_width") / 2 - v("post_y") / 2) * sc,
               v("post_x") * sc, v("post_y") * sc, fill="#d9dcde")
        s.text(80 + (v("pad_overhang") + p["cx"]) * sc, 188, p["id"], 12, ACC, "middle", bold=True)
    s.dim_h(80, 80 + ly["pad_len"] * sc, 200 + v("pad_width") * sc, f'PAD {ly["pad_len"]:.1f}" × {v("pad_width"):.1f}"')
    s.text(40, 70, "Garden +Y (top of sheet)  ·  Driveway −Y  ·  House / latch at left (x=0)", 14, DIM)
    s.save(ddir, "GA-130_plan.svg")

    # EX-200 exploded
    s = Sheet("EX-200", "Exploded assembly", "Insertion directions — not decorative")
    s.titleblock()
    s.text(40, 70, "WINTER / ASSEMBLY LOGIC  (reverse for knock-down)", 16, ACC, bold=True)
    steps = [
        "1  F-004 gravel  →  F-001 pad (LEVEL)  →  F-003 piers  →  H-001 sleeves (drain down)",
        "2  L-001..004 drop −Z into sleeves (shoulder on pad = DATUM)",
        "3  R-001..003 slide +X through nuki mortises (P1→P3)",
        "4  B-001..003 drop −Z into rail grooves",
        "5  C-001 cap +Z onto posts; kama-tsugi peg at L-003",
        "6  W-001 kusabi driven in cheeks (lock); NEVER glue",
        "7  A-030 gate +Z onto L-002 pintles; G-010 slides to H-002 or L-001",
    ]
    for i, t in enumerate(steps):
        s.text(40, 110 + i * 36, t, 15)
    s.text(40, 400, "BALLOONS", 16, ACC, bold=True)
    y = 430
    for p in proj["parts"][:18]:
        s.text(40, y, f"{p['PART_ID']:6}  {p['PART_NAME'][:48]:48}  qty {p['QUANTITY']}", 13)
        y += 18
    s.save(ddir, "EX-200_exploded.svg")

    # P-301 post
    s = Sheet("P-301", "Post typical L-001..004", "Scale ~1:8  ·  T2  ·  qty 4")
    s.titleblock()
    sc = 10.0
    x0, y0 = 120, 900
    body = ly["post_body_h"] * sc
    ten = v("post_tenon_h") * sc
    s.rect(x0, y0 - body, 3.5 * sc, body, fill="#d9dcde")
    s.rect(x0 + 0.5 * sc, y0, 2.5 * sc, ten, fill="#c5cbcf")
    s.dim_v(y0 - body, y0, x0 + 3.5 * sc, f'{ly["post_body_h"]:.3f}" BODY', offset=40)
    s.dim_v(y0, y0 + ten, x0 + 3.5 * sc, f'{v("post_tenon_h"):.3f}" TENON', offset=40)
    s.dim_h(x0, x0 + 3.5 * sc, y0 - body, '3.500"', offset=-24)
    s.text(400, 80, "DATUM: tenon shoulder = pad top. Measure mortise CL AFF from this shoulder, not from tenon tip.", 14, ACC)
    s.text(400, 120, f'FINISHED LENGTH {ly["post_blank_l"]:.3f}"   SETUP S-014 — do not move stop.', 14)
    s.text(400, 160, "Nuki mortises THROUGH 1.50×7.25 at CL 10.000 / 28.000 / 46.000 AFF", 14)
    s.text(400, 200, "Foot tenon 2.500 × 4.500  ·  shoulders 0.500 all around  ·  T2 ±0.031", 14)
    s.text(400, 240, "L-001: omit kusabi; add Latch-B mortise if used.  L-002: add 2 pintle seats.", 14)
    s.text(400, 280, "GRAIN: length vertical. FACE A = garden. END A = shoulder.", 14)
    s.text(400, 320, "Rev C: blank is 75.500″ not 77″ (cap is separate C-001/C-002).", 14, ACC)
    s.save(ddir, "P-301_post.svg")

    # P-302 rail
    s = Sheet("P-302", "Nuki rail R-001..003", f'FINISHED {ly["nuki_len"]:.3f}" × 1.500 × 7.250  ·  qty 3  ·  S-021')
    s.titleblock()
    s.rect(80, 200, 1200, 90, fill=GRAY)
    s.dim_h(80, 1280, 290, f'{ly["nuki_len"]:.3f}" nuki_len  DERIVED')
    s.text(80, 80, "Groove both long edges: 0.375″ deep × 0.875″ wide. FACE A against fence. Boards FLOAT — no glue.", 14)
    s.text(80, 110, "Stations: through L-002, L-003, L-004. Withdraw toward P3 for winter.", 14)
    s.text(80, 140, "Fit class SLIDING in mortise (nuki_fit 0.030″) then INTERFERENCE via W-001 kusabi.", 14)
    s.save(ddir, "P-302_rail.svg")

    # P-303 boards
    s = Sheet("P-303", "Privacy boards", "Stop setups  ·  FLOATING  ·  ¼″ gaps")
    s.titleblock()
    s.text(40, 80, f'Bay clear {ly["bay_clear"]:.3f}"  ·  {ly["n_bay"]} boards/bay × 2 bays  ·  inset {ly["board_inset"]:.3f}"', 14)
    y = 130
    for p in proj["parts"]:
        if p["PART_ID"].startswith("B-"):
            s.text(40, y, f'{p["PART_ID"]}  qty {p["QUANTITY"]:2}  {p["FINISHED_THICKNESS"]:.3f} × {p["FINISHED_WIDTH"]:.3f} × {p["FINISHED_LENGTH"]:.3f}"  {p["PART_NAME"]}', 14)
            y += 28
    s.text(40, y + 20, "Grain vertical. End grain sealed. Do not caulk gaps.", 14, DIM)
    s.save(ddir, "P-303_boards.svg")

    # P-304 gate
    s = Sheet("P-304", "Gate leaf", f'leaf {ly["gate_leaf_w"]:.3f}" × {ly["gate_h"]:.3f}"  ·  36" clear  ·  T2')
    s.titleblock()
    sc = 12
    s.rect(80, 160, ly["gate_leaf_w"] * sc, ly["gate_h"] * sc * 0.55, fill="#e8eaeb")
    s.text(40, 80, "G-001 hinge stile  ·  G-002 latch stile  ·  G-003/004/005 prairie-aligned rails  ·  G-006/007 bottom/top", 13)
    s.text(40, 108, "Hozo tenon thickness ≈ leaf_t/3 = 0.500″  ·  tenon length 1.250″  ·  drawbore 0.125″ toward shoulder", 13)
    s.text(40, 136, "Lift-off pintles: assembly +Z. Brace G-008 half-lap compression (hinge-bottom → latch-top).", 13)
    s.save(ddir, "P-304_gate.svg")

    # Joinery sheets
    for code, title, lines, fn in [
        ("J-401", "Nuki + kusabi", [
            "Mortise THROUGH post: 1.50″ (rail_t + fit) × 7.25″ (rail_h).",
            "Cheeks: 2.00″ of 5.50″ post each side of rail — OK (QA).",
            "Kusabi W-001 0.625 × 1.125 × 5.500 through cheek slot. Drive to lock; reverse to release.",
            "NEVER glue. Bag wedges labeled by joint ID for winter.",
            "Assembly +X. Winter withdraw rails toward P3 after knocking wedges.",
        ], "J-401_nuki.svg"),
        ("J-402", "Foot tenon / sleeve", [
            "Tenon 2.500 × 4.500 × 12.000 from pad-shoulder datum (END A).",
            "Shoulders 0.500 all around. Sleeve ID = tenon + 0.250 clearance.",
            "Drain ⌀0.500 at sleeve BOTTOM. Do not seal the drain.",
            "Fit CLEARANCE; lock by gravity + optional storm cross-wedge.",
            "Paint: mask tenon faces that enter sleeve.",
        ], "J-402_tenon.svg"),
        ("J-403", "Kama-tsugi cap", [
            "Sickle scarf in C-001 centered on L-003.",
            "Drawbore 0.125″ offset, oak peg W-002 ⌀0.375.",
            "Dry fit before peg. Cap may be two labeled halves (LH/RH) after cut.",
            "Grain along run. Does not lock wide panel across grain (cap is narrow).",
        ], "J-403_kama.svg"),
        ("J-404", "Gate hozo drawbore", [
            "Tenon thickness ≈ 1/3 of 1.50″ leaf = 0.50″. Cheeks remain ≈ 0.50″.",
            "Tenon length 1.25″ into stile. Haunch on prairie rails if needed for groove.",
            "Peg hole in stile on CL; tenon hole offset 0.125″ TOWARD shoulder.",
            "Fit DRAWBORED. Gate is a keep-together subassembly (hide glue optional).",
        ], "J-404_hozo.svg"),
    ]:
        s = Sheet(code, title, "Joinery register — see JSON joints[]")
        s.titleblock()
        for i, line in enumerate(lines):
            s.text(40, 80 + i * 32, line, 15)
        s.save(ddir, fn)

    # S-601 BOM sheet (human)
    s = Sheet("S-601", "Master BOM (excerpt)", "Full table: 07_BOM/bom.csv  ·  quantities from kernel")
    s.titleblock()
    y = 70
    s.text(40, y, "ID         QTY  M/B   FINISHED T×W×L                     NAME", 12, DIM)
    y = 95
    for p in proj["parts"]:
        if y > 1000:
            s.text(40, y, "… remainder in CSV", 12, DIM)
            break
        s.text(40, y, f'{p["PART_ID"]:6} {int(p["QUANTITY"]):4}  {p["MAKE_OR_BUY"][:4]:4}  {p["FINISHED_THICKNESS"]:.2f}×{p["FINISHED_WIDTH"]:.2f}×{p["FINISHED_LENGTH"]:.2f}"   {p["PART_NAME"][:42]}', 12)
        y += 16
    s.save(ddir, "S-601_bom.svg")

    # QA
    s = Sheet("QA-701", "Inspection plan", "Do not ship a part that fails its class")
    s.titleblock()
    y = 70
    for q in proj["inspection"]:
        s.text(40, y, f'{q["QC"]}  [{q["CLASS"]}]  {q["CHECK"]}  tol {q["TOL"]}', 13)
        y += 22
    y += 10
    s.text(40, y, "GEOMETRY GATE (kernel)", 16, ACC, bold=True)
    y += 28
    for g in proj["qa_geometry"]:
        s.text(40, y, f'{g["level"]:8}  {g["item"]}  —  {g.get("detail","")}', 13)
        y += 22
    s.save(qdir, "QA-701_inspection.svg")

    # labels
    s = Sheet("L-801", "Part labels", "Print, cut, tape to FACE A  ·  grain ↑")
    s.titleblock()
    x, y = 40, 70
    labels = [p for p in proj["parts"] if p["MAKE_OR_BUY"] == "MAKE" and p["PART_CATEGORY"] in "LRCBGW"]
    for p in labels:
        s.rect(x, y, 250, 88, fill="#fff", stroke=INK, sw=1)
        s.text(x + 8, y + 22, p["PART_ID"], 16, ACC, bold=True)
        s.text(x + 8, y + 42, p["PART_NAME"][:28], 11)
        s.text(x + 8, y + 60, f'TOP ↑  FACE A →  REV {PROJECT["REVISION"]}', 10, DIM)
        s.text(x + 8, y + 78, f'qty {p["QUANTITY"]}  {p["FINISHED_LENGTH"]:.2f}"', 10)
        x += 260
        if x > 1400:
            x = 40
            y += 100
    s.save(os.path.join(FAB, "11_BUILD_MANUAL"), "L-801_labels.svg")

    # templates 1:1 — SVG in mm with 100mm check
    def template(code, title, fn, draw):
        # letter landscape-ish 1100×850 px ~ 11×8.5 at 100px/in but we use mm viewBox
        vw, vh = 280, 200  # mm
        b = [
            f"<svg xmlns='http://www.w3.org/2000/svg' width='{vw}mm' height='{vh}mm' viewBox='0 0 {vw} {vh}'>",
            f"<rect x='0' y='0' width='{vw}' height='{vh}' fill='#fff' stroke='#000' stroke-width='0.4'/>",
            f"<text x='8' y='10' font-family='monospace' font-size='4'>{code}  {title}  MARTIN Rev {PROJECT['REVISION']}  PRINT 1:1</text>",
            "<rect x='8' y='14' width='100' height='10' fill='none' stroke='#000' stroke-width='0.35'/>",
            "<text x='8' y='28' font-family='monospace' font-size='3.2'>CHECK BOX = 100.000 mm  ·  measure before cutting  ·  if ≠100mm, abort print scale</text>",
        ]
        draw(b)
        b.append("</svg>")
        write(os.path.join(tdir, fn), "\n".join(b) + "\n")

    def kusabi(b):
        # inches to mm, place at 20,40
        t, w, l = v("kusabi_t") * MM, v("kusabi_w") * MM, v("kusabi_l") * MM
        b.append(f"<rect x='20' y='40' width='{l}' height='{w}' fill='none' stroke='#000' stroke-width='0.4'/>")
        b.append(f"<text x='20' y='38' font-family='monospace' font-size='3'>W-001  {v('kusabi_l'):.3f}\" × {v('kusabi_w'):.3f}\" × {v('kusabi_t'):.3f}\" thick  GRAIN →</text>")
        b.append("<text x='20' y='90' font-family='monospace' font-size='3'>DATUM: long edge = REFERENCE EDGE. Taper in thickness when fitting — template is rectangular blank.</text>")

    def tenon(b):
        tx, ty = v("post_tenon_x") * MM, v("post_tenon_y") * MM
        px, py = v("post_x") * MM, v("post_y") * MM
        b.append(f"<rect x='20' y='40' width='{px}' height='{py}' fill='none' stroke='#000' stroke-width='0.35'/>")
        ox, oy = 20 + (px - tx) / 2, 40 + (py - ty) / 2
        b.append(f"<rect x='{ox}' y='{oy}' width='{tx}' height='{ty}' fill='none' stroke='#000' stroke-width='0.5'/>")
        b.append("<text x='20' y='38' font-family='monospace' font-size='3'>L-* foot tenon SECTION (looking +Z from below)  outer 3.50×5.50  inner 2.50×4.50</text>")
        b.append("<text x='20' y='120' font-family='monospace' font-size='3'>Shoulder 0.500″ all around. GRAIN ⊙ (post axis). FACE A = bottom of this view toward garden when post stands.</text>")

    template("T-501", "Kusabi blank 1:1", "T-501_kusabi.svg", kusabi)
    template("T-502", "Foot tenon section 1:1", "T-502_tenon.svg", tenon)

    # DXF same profiles in inches
    def dxf_kusabi(lines):
        dxf_rect(lines, 0, 0, v("kusabi_l"), v("kusabi_w"), "W-001")
        dxf_rect(lines, 0, -2, 100 / MM, 10 / MM, "CHECK_100MM")

    def dxf_tenon(lines):
        dxf_rect(lines, 0, 0, v("post_x"), v("post_y"), "POST")
        dxf_rect(lines, 0.5, 0.5, v("post_tenon_x"), v("post_tenon_y"), "TENON")

    write_dxf(os.path.join(tdir, "T-501_kusabi.dxf"), dxf_kusabi)
    write_dxf(os.path.join(tdir, "T-502_tenon.dxf"), dxf_tenon)


def schedules(proj):
    bom_dir = os.path.join(FAB, "07_BOM")
    cut_dir = os.path.join(FAB, "08_CUT_LISTS")
    jdir = os.path.join(FAB, "09_JOINERY")
    ensure(bom_dir, cut_dir, jdir)
    fields = [
        "PART_ID", "PART_NAME", "PART_CATEGORY", "ASSEMBLY", "QUANTITY", "MAKE_OR_BUY",
        "MATERIAL", "SPECIES", "PURCHASE", "ROUGH_THICKNESS", "ROUGH_WIDTH", "ROUGH_LENGTH",
        "FINISHED_THICKNESS", "FINISHED_WIDTH", "FINISHED_LENGTH", "GRAIN_DIRECTION",
        "JOINERY", "HANDED", "FIT", "MOVEMENT", "TOLERANCE_CLASS", "NOTES", "REVISION",
    ]
    csv_write(os.path.join(bom_dir, "bom.csv"), proj["parts"], fields)
    csv_write(
        os.path.join(cut_dir, "rough.csv"),
        proj["parts"],
        ["PART_ID", "PART_NAME", "QUANTITY", "ROUGH_THICKNESS", "ROUGH_WIDTH", "ROUGH_LENGTH", "MATERIAL", "PURCHASE", "NOTES"],
    )
    csv_write(
        os.path.join(cut_dir, "finished.csv"),
        proj["parts"],
        ["PART_ID", "PART_NAME", "QUANTITY", "FINISHED_THICKNESS", "FINISHED_WIDTH", "FINISHED_LENGTH", "JOINERY", "TOLERANCE_CLASS"],
    )
    csv_write(os.path.join(FAB, "07_BOM", "hardware.csv"), proj["hardware"],
              ["HARDWARE_ID", "DESCRIPTION", "STANDARD", "SIZE", "QTY", "MATERIAL", "MAKE_OR_BUY"])
    csv_write(os.path.join(cut_dir, "nest.csv"), proj["nest"]["boards"],
              ["BOARD_ID", "PURCHASE", "LENGTH", "PARTS", "USED", "REMAINDER", "YIELD_PCT", "BF"])
    csv_write(os.path.join(jdir, "joints.csv"), proj["joints"],
              ["JOINT_ID", "JOINT_TYPE", "PART_A", "PART_B", "LOCATION", "FIT_CLASS", "GLUE", "ASSEMBLY_DIRECTION"])
    csv_write(os.path.join(FAB, "12_QA", "inspection.csv"), proj["inspection"],
              ["QC", "CHECK", "CLASS", "TOL"])

    # lumber buy from nest
    buy_rows = [{"PURCHASE": k, "QTY": n, "NOTE": "from nest + explicit waste_factor on bf"} for k, n in proj["nest"]["buy_counts"].items()]
    csv_write(os.path.join(bom_dir, "lumber_buy.csv"), buy_rows, ["PURCHASE", "QTY", "NOTE"])


def json_exports(proj):
    src = os.path.join(FAB, "00_SOURCE")
    ensure(src, os.path.join(FAB, "13_REVISION_HISTORY"))
    write(os.path.join(src, "martin_project.json"), json.dumps(proj, indent=2, default=str))
    write(os.path.join(ROOT, "fence", "martin", "app", "fab.json"), json.dumps({
        "project": proj["project"],
        "layout": proj["layout"],
        "parts": proj["parts"],
        "joints": proj["joints"],
        "nest": {k: proj["nest"][k] for k in ("buy_counts", "net_bf", "procurement_bf", "waste_factor", "kerf", "note")},
        "inspection": proj["inspection"],
        "qa_geometry": proj["qa_geometry"],
        "sequence": proj["sequence"],
        "drawing_index": proj["drawing_index"],
        "unresolved": proj["unresolved"],
        "revisions": proj["revisions"],
        "hardware": proj["hardware"],
        "stops": proj["stops"],
        "assemblies": proj["assemblies"],
        "concrete": proj["concrete"],
        "decisions": proj["decisions"],
        "fmea": proj["fmea"],
    }, indent=2, default=str))
    write(os.path.join(FAB, "13_REVISION_HISTORY", "revisions.json"), json.dumps(proj["revisions"], indent=2))
    write(os.path.join(FAB, "13_REVISION_HISTORY", "decisions.json"), json.dumps(proj["decisions"], indent=2))
    write(os.path.join(FAB, "13_REVISION_HISTORY", "audit.json"), json.dumps(proj["audit"], indent=2))


def build_manual(proj):
    ly = proj["layout"]
    nest = proj["nest"]
    lines = [
        f"# MARTIN Build Manual — Rev {PROJECT['REVISION']}",
        "",
        "Source of truth: `fence/martin/martin_kernel.py` → `fab/00_SOURCE/martin_project.json`.",
        "",
        "## A. Model status",
        "Semantic fabrication model. Every MAKE part has a Part ID. Joinery is a register, not only booleans.",
        f"Gate/cap clearance **{0.5:.3f}″** (Rev C). Post blank **{ly['post_blank_l']:.3f}″** (not 77″).",
        "",
        "## B. Controlling parameters (inch)",
        f"- overall_length = 143.000 VERIFIED",
        f"- overall_height = 65.000 VERIFIED",
        f"- gate_clear = 36.000 ASSUMED",
        f"- bay_clear = {ly['bay_clear']:.3f} DERIVED `(L - 4*post_x - gate_clear)/2`",
        f"- nuki_len = {ly['nuki_len']:.3f} DERIVED",
        f"- drop_off = 5.000 ESTIMATED **TBM**",
        "",
        "## C–I. Registers",
        "See `07_BOM/bom.csv`, `08_CUT_LISTS/*.csv`, `09_JOINERY/joints.csv`.",
        "",
        f"**Nest buy:** `{nest['buy_counts']}`  net **{nest['net_bf']} bf**  procurement **{nest['procurement_bf']} bf** (waste_factor={nest['waste_factor']}).",
        f"Concrete **{proj['concrete']['concrete_yd3']} yd³**  gravel **{proj['concrete']['gravel_yd3']} yd³** (drop_off estimated).",
        "",
        "## K. Assembly order",
    ]
    for s in proj["sequence"]:
        lines.append(f"- **{s['id']}** ({s['phase']}) {s['title']}")
    lines += [
        "",
        "## L. Drawing index",
    ]
    for d in proj["drawing_index"]:
        lines.append(f"- {d['DWG']} {d['TITLE']}")
    lines += [
        "",
        "## O. Unresolved",
    ]
    for u in proj["unresolved"]:
        lines.append(f"- {u['ID']} {u['ITEM']} [{u['CLASS']}] param `{u['PARAM']}`")
    lines += [
        "",
        "## Completeness tests",
        "1. Craftsperson: critical dims are numeric from datums (P-301, S-014, QC-04..14).",
        "2. Other CAD agent: `martin_project.json` is sufficient to regenerate layout + parts.",
        "3. Change overall_length by 12″: re-run kernel — bay_clear, nuki_len, pad, post CLs, nest, BOM update. Rail CL and stock section stay.",
        "",
        "This package is a **planning fabrication model**, not a stamped PE document.",
    ]
    write(os.path.join(FAB, "11_BUILD_MANUAL", "BUILD_MANUAL.md"), "\n".join(lines) + "\n")


def fab_index(proj):
    nest = proj["nest"]
    ly = proj["layout"]
    cards = "".join(
        f"<tr><td><a href='06_DRAWINGS/{d['FILE']}'>{d['DWG']}</a></td><td>{d['TITLE']}</td></tr>"
        if d["FILE"].endswith(".svg") and d["DWG"].startswith(("G", "GA", "EX", "P", "J", "S-601"))
        else f"<tr><td>{d['DWG']}</td><td>{d['TITLE']} — see CSV/JSON</td></tr>"
        for d in proj["drawing_index"]
    )
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>MARTIN Fabrication Package — Rev {PROJECT['REVISION']}</title>
<style>
body{{font-family:Georgia,serif;background:#f3f1ec;color:#1a1f24;margin:0;padding:32px;line-height:1.5}}
a{{color:#3d5a4c}} table{{border-collapse:collapse;width:100%;font-size:14px}}
td,th{{border-bottom:1px solid #c5c8c2;padding:8px 6px;text-align:left}}
.k{{font:600 11px/1 "IBM Plex Mono",monospace;letter-spacing:.16em;color:#5a6a4a}}
h1{{font-size:42px;margin:8px 0 12px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px;margin:18px 0}}
.grid a{{display:block;padding:12px;background:#fff;border:1px solid #c5c8c2;text-decoration:none;color:inherit}}
</style></head><body>
<p class="k">REV {PROJECT['REVISION']} · KERNEL 3.0 · INCHES</p>
<h1>MARTIN fabrication package</h1>
<p>Single source of truth: <code>martin_kernel.py</code>. Geometry, BOM, cut lists, joinery, and drawings are generated — not hand-copied.</p>
<p><b>bay_clear</b> {ly['bay_clear']}\" · <b>nuki_len</b> {ly['nuki_len']}\" · <b>post blank</b> {ly['post_blank_l']}\" · <b>gate_h</b> {ly['gate_h']}\" · nest <b>{nest['net_bf']} bf</b> net / <b>{nest['procurement_bf']} bf</b> buy</p>
<div class="grid">
<a href="00_SOURCE/martin_project.json">JSON project</a>
<a href="07_BOM/bom.csv">BOM CSV</a>
<a href="08_CUT_LISTS/finished.csv">Finished cut list</a>
<a href="08_CUT_LISTS/nest.csv">Board nest</a>
<a href="09_JOINERY/joints.csv">Joints</a>
<a href="11_BUILD_MANUAL/BUILD_MANUAL.md">Build manual</a>
<a href="12_QA/QA-701_inspection.svg">QA-701</a>
<a href="10_TEMPLATES/T-501_kusabi.svg">T-501 1:1</a>
<a href="../app/">Build app</a>
</div>
<h2>Drawings</h2>
<table><thead><tr><th>DWG</th><th>Title</th></tr></thead><tbody>{cards}</tbody></table>
<p style="margin-top:28px;color:#6e7578;font-size:13px">Not a stamped engineering document. drop_off is ESTIMATED. Call 811. Verify Green Code.</p>
</body></html>"""
    write(os.path.join(FAB, "index.html"), html)


def main():
    proj = build_project()
    ensure(FAB, SCAD)
    json_exports(proj)
    schedules(proj)
    drawings(proj)
    write_scad(proj)
    build_manual(proj)
    fab_index(proj)
    # pointer in 01_MASTER_CAD
    write(
        os.path.join(FAB, "01_MASTER_CAD", "README.md"),
        "FreeCAD: `../cad/martin_fence.py` (imports kernel).\n"
        "OpenSCAD: `../cad/scad/main.scad`.\n"
        "Copied here when present: `martin.FCStd`.\n",
    )
    write(
        os.path.join(FAB, "02_STEP", "README.md"),
        "STEP assembly: `martin_assembly.step` (copied from `../cad/exports/`).\n",
    )
    write(
        os.path.join(FAB, "03_STL", "README.md"),
        "STL meshes copied from `../cad/exports/` (timber / concrete / gravel / sleeve).\n",
    )
    copy_cad_exports()
    print("FAB package complete. parts", len(proj["parts"]), "drawings", len(proj["drawing_index"]))


def copy_cad_exports():
    src = os.path.join(ROOT, "fence", "martin", "cad", "exports")
    pairs = [
        ("martin.FCStd", os.path.join(FAB, "01_MASTER_CAD")),
        ("martin_assembly.step", os.path.join(FAB, "02_STEP")),
        ("martin_timber.stl", os.path.join(FAB, "03_STL")),
        ("martin_concrete.stl", os.path.join(FAB, "03_STL")),
        ("martin_gravel.stl", os.path.join(FAB, "03_STL")),
        ("martin_sleeve.stl", os.path.join(FAB, "03_STL")),
    ]
    for name, dest in pairs:
        ensure(dest)
        p = os.path.join(src, name)
        if os.path.isfile(p):
            shutil.copy2(p, os.path.join(dest, name))
            print("copied", name, "→", os.path.relpath(dest, ROOT))
    ksrc = os.path.join(ROOT, "fence", "martin", "martin_kernel.py")
    shutil.copy2(ksrc, os.path.join(FAB, "00_SOURCE", "martin_kernel.py"))
    print("copied martin_kernel.py → fab/00_SOURCE")


if __name__ == "__main__":
    main()
