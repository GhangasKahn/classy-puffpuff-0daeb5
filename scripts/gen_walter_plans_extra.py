#!/usr/bin/env python3
"""WALTER sheets W-9 … W-14. Imported from gen_walter_plans.main()."""

from __future__ import annotations

import math

import gen_walter_plans as G

Sheet, ACC, DIM, INK, LIGHT, PAPER, STEEL, DRUM, BELT, SAFE, WARN = (
    G.Sheet, G.ACC, G.DIM, G.INK, G.LIGHT, G.PAPER, G.STEEL, G.DRUM, G.BELT, G.SAFE, G.WARN
)
P = G.P


def sheet_w9():
    s = Sheet("W-9", "Exploded assembly", "CAD explode = 1.0  ·  print the SVG render at /renders/walter_exploded.svg")
    s.titleblock()
    s.text(40, 62, "GROUP BREAKDOWN  —  BUILD IN THIS ORDER", 15, ACC, bold=True)
    groups = [
        ("1  FRAME", "Base, doubled walls, stretchers, ¼\" steel bearing plates. Square before glue."),
        ("2  DRUM", "Keyed shaft, 21 birch discs, end bells, flange bearings, 4.75\" pulley."),
        ("3  TABLE", "Torsion-box platen, UHMW ways, dual Acme, HTD sync, lock knobs."),
        ("4  CONVEYOR", "Crowned 2\" rollers, 16×60 PVC belt, skew, 24 V gearmotor."),
        ("5  DRIVE", "Hinge plate, 1 HP TEFC, 3.00\" pulley, 4L440, turnbuckle, guard."),
        ("6  HOOD", "¼\" birch hood, 4\" port, brush strip, optional interlock."),
        ("7  STAND (opt.)", "32\" cabinet, shelf for starter / PSU, mobile base."),
    ]
    y = 100
    for t, b in groups:
        s.rect(40, y, 780, 70, fill="#efe8dc", stroke=LIGHT, sw=1)
        s.text(56, y + 28, t, 16, ACC, bold=True)
        s.text(56, y + 52, b, 13, INK)
        y += 78

    s.text(860, 62, "EXPLODE DIRECTIONS (kernel)", 15, ACC, bold=True)
    s.text(860, 92, "frame   (0, 0, 0)", 14, INK)
    s.text(860, 116, "drum    +Z  8\"", 14, INK)
    s.text(860, 140, "table   −Z  6\"", 14, INK)
    s.text(860, 164, "motor   +X  8\"", 14, INK)
    s.text(860, 188, "guard   +X  6\"", 14, INK)
    s.text(860, 212, "hood    +Z 12\"", 14, INK)

    s.note(860, 250, [
        "CAD FILES",
        "sander/walter/cad/walter_kernel.py     geometry (inches)",
        "sander/walter/cad/exports/*.stl        binary STL per group + assembly",
        "sander/walter/cad/exports/walter_assembly.obj",
        "sander/walter/cad/walter_sander.scad   OpenSCAD preview",
        "sander/walter/cad/walter_sander.py     FreeCAD STEP when freecadcmd exists",
        "sander/walter/renders/walter_exploded.svg",
        "python3 scripts/gen_walter_cad.py      regenerates meshes + renders",
    ], width=760)

    s.note(860, 500, [
        "CLEARANCES TO HOLD",
        "• Drum face to wall inner: 0.25\" each side.",
        "• Table ways: 0.02–0.04\" sliding fit in UHMW dados.",
        "• Conveyor belt: 1/32\" above platen, not dragging.",
        "• Hood: 3/8\" off abrasive. Foam weatherstrip to walls.",
        "• Guard: fully enclosed. No finger slot at the belt pinch.",
    ], width=760)

    s.note(40, 680, [
        "ASSEMBLY DATUMS",
        "D1  Base top face = Z0. Walls sit on it. Do not let stretchers lift a wall.",
        "D2  Drum axis = Z 13.50\", Y 18.00\". Drill both bearing plates from one story stick.",
        "D3  Idle jack at zero = plates coplanar. Then true the drum. Then jack for parallelism.",
        "D4  Acme nuts clocked together before the HTD belt goes on. Paint a witness mark.",
    ], width=1600)
    s.save("W9_exploded.svg")


def sheet_w10():
    s = Sheet("W-10", "1:1 templates — disc, plate, key", "Print at 100% on Letter/A4 and check the 1.00\" scale bar")
    s.titleblock()

    # 1" scale bar
    s.text(40, 62, "SCALE CHECK  —  THIS BAR MUST MEASURE 1.00\" ON PAPER", 15, ACC, bold=True)
    bar = 72  # 1 inch at 72 px/in... our sheet is ~4 px/mm = 101.6 px/in. Use 101.6
    px_in = 101.6
    s.rect(40, 80, px_in, 18, fill=ACC, stroke=INK, sw=1)
    s.text(40 + px_in + 12, 94, '1.00"', 14, INK)

    # disc 1:1  — Ø 5.125" = 520.7 px
    s.text(40, 130, "DRUM DISC  J  —  Ø 5.125\" BLANK  ·  BORE 0.748\"  ·  3/16\" KEYWAY", 15, ACC, bold=True)
    cx, cy, r = 320, 430, (5.125 / 2) * px_in
    s.circle(cx, cy, r, fill="#c4b49a", stroke=INK, sw=2)
    s.circle(cx, cy, (0.748 / 2) * px_in, fill=PAPER, stroke=INK, sw=1.6)
    kw, kh = 0.1875 * px_in, 0.10 * px_in
    s.rect(cx - kw / 2, cy - (0.374 * px_in) - kh, kw, kh + 4, fill=ACC, stroke=INK, sw=1)
    s.text(cx, cy + r + 24, "21 REQUIRED  ·  bandsaw oversize, sand to line after glue-up", 13, DIM, "middle")

    # bearing plate 1:1 6x6
    s.text(720, 130, "BEARING PLATE  —  ¼\" STEEL  6.00 × 6.00", 15, ACC, bold=True)
    ox, oy = 760, 180
    side = 6.0 * px_in
    s.rect(ox, oy, side, side, fill=STEEL, stroke=INK, sw=2)
    s.circle(ox + side / 2, oy + side / 2, 0.55 * px_in, fill=PAPER, stroke=INK, sw=1.6)
    for dy in (-1.85, 1.85):
        s.circle(ox + side / 2 + dy * px_in, oy + side / 2, 0.17 * px_in, fill=PAPER, stroke=INK, sw=1.2)
    s.text(ox + side / 2, oy + side + 22, "IDLE PLATE: slot these two holes vertically 0.90\"", 13, ACC, "middle")
    s.text(ox + side / 2, oy + side + 42, "DRIVE PLATE: round holes, fixed", 13, DIM, "middle")

    s.note(40, 780, [
        "KEY  —  3/16\" SQ × 4.00\"  (two required, 1045 or 1144)",
        "Do not use piano wire. File a slight chamfer so it starts in the disc stack.",
        "Disc bore is 0.002\" under shaft: freeze the shaft, warm the discs, or ream the last thou.",
        "After the stack is glued, turn the OD to 5.000\" between centers or in the machine.",
    ], width=1600)
    s.save("W10_templates.svg")


def sheet_w11():
    s = Sheet("W-11", "Optional stand / cabinet", "32\" cabinet  ·  working height ≈ 36\" to platen  ·  mobile base")
    s.titleblock()
    s.text(40, 62, "CABINET  —  ¾\" BALTIC BIRCH  ·  NOT REQUIRED TO RUN THE MACHINE", 15, ACC, bold=True)

    S = 14.0
    ox, oy = 80, 820

    def X(v):
        return ox + v * S

    def Z(v):
        return oy - v * S

    # stand
    s.rect(X(0), Z(32), 22 * S, 32 * S, fill="#c4b49a", stroke=INK, sw=2)
    s.rect(X(0.75), Z(32), 0.75 * S, 32 * S, fill="#8a6a42", stroke=INK, sw=1.2)
    s.rect(X(20.5), Z(32), 0.75 * S, 32 * S, fill="#8a6a42", stroke=INK, sw=1.2)
    s.rect(X(0.75), Z(8.75), 20.5 * S, 0.75 * S, fill=LIGHT, stroke=INK, sw=1.2)
    # machine ghost
    s.rect(X(0), Z(32 + 20), 22 * S, 20 * S, fill="none", stroke=ACC, sw=1.6, dash="8 4")
    s.text(X(11), Z(42), "MACHINE", 12, ACC, "middle")
    s.dim_v(Z(32), Z(0), X(0), '32.00" cabinet', offset=-36)
    s.dim_v(Z(52), Z(0), X(22), '≈ 52" overall', offset=28)
    s.dim_h(X(0), X(22), Z(0) + 6, '22.00"', offset=24)

    s.note(520, 100, [
        "WHY A STAND",
        "• Platen at ~36–40\" AFF is kinder on a long session than a bench.",
        "• Shelf holds the magnetic starter, 24 V PSU, and extra abrasive rolls.",
        "• 4\" hose can drop inside the cabinet to a collector behind.",
        "• Mobile base (Rockler / Shop Fox pattern) — lock the casters to sand.",
        "• Do not store finishing rags in here. Fine dust is fuel.",
    ], width=700)

    s.note(520, 320, [
        "CUT LIST (optional)",
        "N  Stand sides     32.00 × 32.00 × ¾\"  ×2",
        "P  Shelf           20.50 × 32.00 × ¾\"  ×1",
        "P  Back            22.00 × 32.00 × ¾\"  ×1",
        "   Bottom stretcher 20.50 × 4.00 × ¾\"  ×2",
        "   Bolt machine through base rails into cabinet top with 5/16\" + fender washers.",
    ], width=700)

    s.note(520, 540, [
        "OPEN C-FRAME OPTION  (Todd Hunt)",
        "If you need >16\" width, do not stretch this closed frame. Design a C-frame",
        "with a thicker idle bearing wall (two ¾\" + ¼\" plate) and a 1.5–2 HP motor.",
        "That is a different machine. WALTER stays closed-frame on purpose.",
    ], width=700)
    s.save("W11_stand.svg")


def sheet_w12():
    s = Sheet("W-12", "Wiring ladder (not a permit drawing)", "115 V 20 A dedicated  ·  extra-low-voltage feed  ·  have an electrician sign off")
    s.titleblock()
    s.text(40, 62, "LADDER  —  MAGNETIC STARTER = NO-VOLT RELEASE", 15, ACC, bold=True)

    rungs = [
        ("L1 / N", "NEMA 5-20 plug  ·  12 AWG SJ  ·  strain relief at the cabinet"),
        ("E-STOP", "40 mm NC mushroom, left-hand infeed corner, in series with starter coil"),
        ("HOOD SW", "Optional NC. Machine will not pick up with the hood off."),
        ("OL", "Heater sized to motor FLA (typically ~13 A at 115 V 1 HP)."),
        ("M1", "Drum motor 1 HP TEFC. Never a light switch."),
        ("24 V", "Meanwell-class PSU on the load side of M1 aux, fused 5 A."),
        ("PWM", "0–16 FPM. Knob on the infeed cheek. Off is full CCW."),
        ("M2", "Feed gearmotor. E-stop drops 24 V as well as 115 V."),
        ("PE", "Green ground to motor frames, plates, and the stand. Bond it."),
    ]
    y = 100
    for i, (k, v) in enumerate(rungs):
        s.rect(40, y, 1600, 56, fill="#efe8dc" if i % 2 == 0 else PAPER, stroke=LIGHT, sw=1)
        s.rect(40, y, 140, 56, fill=ACC if k != "PE" else SAFE, stroke=INK, sw=1)
        s.text(110, y + 34, k, 13, PAPER, "middle", bold=True)
        s.text(200, y + 34, v, 14, INK)
        y += 56

    s.note(40, 640, [
        "STARTUP  —  POST THIS NEXT TO THE SWITCH",
        "1 Dust collector ON and pulling.   2 Hood latched.   3 Table locked.   4 Hands clear.",
        "5 Drum ON — wait for speed.   6 Feed ON, slow.   7 Board in, light pass.",
        "Stall: feed OFF first, then drum. Never start the drum with a board already under it.",
        "This sheet is a design intent, not an NEC drawing, not a UL listing, not a substitute for a license.",
    ], width=1600)
    s.save("W12_wiring.svg")


def sheet_w13():
    s = Sheet("W-13", "Abrasive wrap development", "3\" roll on 4\" hook tape  ·  15–20° spiral  ·  end-bell slots")
    s.titleblock()
    s.text(40, 62, "DEVELOPED WRAP  —  CUT THE FIRST ONE CAREFULLY; TRACE THE REST", 15, ACC, bold=True)

    # rectangle representing unwrapped drum: πd × face
    wrap_l = math.pi * 5.00  # 15.708"
    wrap_w = 16.00
    S = 38.0
    ox, oy = 80, 200
    s.rect(ox, oy, wrap_l * S, wrap_w * S * 0.55, fill=DRUM, stroke=INK, sw=2)
    # spiral lines
    for i in range(8):
        x0 = ox + i * 70
        s.line(x0, oy + 10, x0 + 90, oy + wrap_w * S * 0.55 - 10, 2, ACC)
    s.dim_h(ox, ox + wrap_l * S, oy + wrap_w * S * 0.55, 'π × 5.00" = 15.71" circumference', offset=28)
    s.dim_v(oy, oy + wrap_w * S * 0.55, ox, '16.00" face (drawn 55%)', offset=-36)

    s.note(80, 620, [
        "CUTTING",
        "• Hook tape: 4\" PSA, wrapped so joints stagger vs the paper. Burnish. No bubbles.",
        "• Paper: 3\" roll, 80 / 120 / 150. Cut a parallelogram: long side = 16\" / sin(θ), θ ≈ 17°.",
        "• Start in the idle-end bell slot. Keep tension. Tuck the drive end. No lumps.",
        "• Replacement pieces: trace the first wrap. Number the grit on the idle bell with a paint pen.",
        "• True after every wrap change: carrier board + sanding block until the whole face cuts.",
        "• Loaded paper (paint, pitch, glue) comes off. Do not run hot. Dull paper is a fire.",
    ], width=1520)
    s.save("W13_wrap.svg")


def sheet_w14():
    s = Sheet("W-14", "Buy list · McMaster search terms", "Verify every catalog number before you click buy  ·  2026 hobby-shop")
    s.titleblock()
    s.text(40, 58, "HARDWARE  —  SEARCH TERMS, NOT A BLIND CART", 14, ACC, bold=True)

    rows = [
        ("UCFL204-12", "¾\" 2-bolt flange bearing ×2", "6661K13"),
        ("UCFL201-10", "⅝\" 2-bolt flange bearing ×4", "6661K11"),
        ("1144 0.75 rod 24\"", "Stressproof shaft, then cut/key 22\"", "verify grind"),
        ("aluminum tube 2.000 OD", "Roller blanks ×2, 16.25\" face", "9056K44"),
        ("acme 3/4-6 12\"", "Elevation screws ×2", "99030A460"),
        ("acme nut 3/4-6 bronze", "Nut blocks ×2", "6350K15"),
        ("4L pulley 3.0 3/4", "Motor pulley", "6245K27"),
        ("4L pulley 4.75 3/4", "Drum pulley (ShopNotes published 6245K47)", "6245K47"),
        ("4L440 link", "Drive belt", "6191K37"),
        ("handwheel 4 inch 3/4", "Elevation crank", "6086K52"),
        ("A36 1/4 plate", "Bearing + hinge plates", "8910K713"),
        ("UHMW 1/8 sheet", "Ways + platen face", "8752K111"),
        ("1 HP TEFC 1725 56C", "Drum motor 115 V", "Grainger / surplus"),
        ("24V worm 30 rpm", "Feed gearmotor + PWM + 5 A PSU", "—"),
        ("NEMA 0 starter 115V", "Magnetic starter + OL + E-stop", "—"),
        ("PVC conveyor 16×60", "Endless 2-ply, not a sanding belt", "belt supplier"),
        ("hook tape 4\" PSA", "5 yd + 3\" abrasive rolls 80/120/150", "Klingspor"),
    ]
    y = 80
    s.text(48, y, "SEARCH", 11, DIM, bold=True)
    s.text(420, y, "USE", 11, DIM, bold=True)
    s.text(1100, y, "HINT", 11, DIM, bold=True)
    y = 100
    for i, (a, b, c) in enumerate(rows):
        if i % 2 == 0:
            s.rect(40, y - 14, 1600, 22, fill="#efe8dc", stroke="none", sw=0)
        s.text(48, y, a, 12, ACC, bold=True)
        s.text(420, y, b, 12, INK)
        s.text(1100, y, c, 12, DIM)
        y += 22

    s.note(40, 500, [
        "PLYWOOD  —  THREE 5×5 (OR 5×10) ¾\" BALTIC BIRCH + ONE ¼\"",
        "Idle/drive walls are doubled, grain crossed. Drum discs come out of sheet 3.",
        "Buy one extra ¾\" if your sheet has a void — voids become vibration.",
        "Hard maple for base rails and nut blocks. Do not use construction 2× for the Acme nuts.",
    ], width=1600)

    s.note(40, 660, [
        "WHAT NOT TO BUY",
        "• MDF for drum or walls.  • A 16×48 sanding belt as a conveyor.  • PVC pipe rollers.",
        "• Pillow blocks on a single ¾\" wall with no plate.  • An open-drip motor in this dust.",
        "• A light switch as the only disconnect.  • Formica for the platen.",
        "Catalog numbers drift. The search term is the spec. Measure the part in your hand.",
    ], width=1600)

    s.note(40, 840, [
        "CSV  —  SAME LIST, IMPORTABLE",
        "sander/walter/fab/07_BOM/hardware.csv",
        "sander/walter/fab/07_BOM/mcmaster.csv",
        "sander/walter/fab/08_CUT_LISTS/finished.csv",
        "sander/walter/fab/12_QA/fmea.csv",
    ], width=1600)
    s.save("W14_buylist.svg")


def emit():
    sheet_w9()
    sheet_w10()
    sheet_w11()
    sheet_w12()
    sheet_w13()
    sheet_w14()
