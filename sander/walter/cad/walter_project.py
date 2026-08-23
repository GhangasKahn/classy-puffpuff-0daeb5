"""
WALTER PLANFORGE registers — parts, bags, requirements, joinery, hardware, dimensions.

Geometry lives in walter_kernel.py. This module names every fabricated part,
maps bags/steps for the LEGO manual, and carries WOODWRIGHT PLANFORGE v1.0
governance (risk, release, evidence). Downstream generators must import here
rather than inventing IDs in HTML.
"""

from __future__ import annotations

from walter_kernel import (
    FMEA,
    HARDWARE,
    P,
    PLYWOOD,
    REV,
    drum_rpm,
    feed_fpm,
    sfm,
)

PROJECT = dict(
    CODE="WPF-WALTER-16-C",
    NAME="WALTER",
    TITLE="16-inch closed-frame drum thickness sander",
    REVISION=REV,
    MODEL_VERSION="1.2.0",
    PROTOCOL="WOODWRIGHT PLANFORGE v1.0",
    PROTOCOL_DATE="2026-08-03",
    UNITS="inch controlling; millimetre at CAD export only",
    LAYOUT="D1 base top Z0; D2 drum axis Z 13.50 Y 18.00; D3 idle jack zero; D4 Acme nuts clocked",
    RELEASE_STATE="FABRICATION-READY WITH CONDITIONS",
    RISK_CLASS="R3",
    RISK_TRIGGERS=[
        "Powered abrasive drum ~1089 RPM / ~1.4 kSFM with stored rotational energy",
        "Ingoing nip at drum-to-work and conveyor rollers",
        "115 V motor circuit, magnetic starter, E-stop, 24 V feed — electrical [P]",
        "Kickback / ejection of short stock",
        "Combustible fine dust; hood and collector are part of the safeguard",
        "Belt/pulley pinch outboard of the drive wall",
        "Homemade machine — not UL listed, not OSHA-certified, not PE-stamped",
    ],
    CONDITIONS=[
        "Qualified electrician sizes overload heaters to motor FLA and lands 115 V 20 A, grounding, and the magnetic starter [P]",
        "First-run commissioning is staged: collector on, hood on, no workpiece, then poplar 0.010″ [T]",
        "Verify every catalog number on the live McMaster / supplier page before purchase [S]",
        "True the drum OD to 5.000 ±0.010 after glue; do not run an unbalanced blank [T]",
        "Track the PVC conveyor empty 60 s then loaded before any oak [T]",
        "E-stop blink test: restore power — drum must not auto-restart [T]",
        "Do not treat W-sheets, the HTML guidebook, or the Build-app viz as a scaled fabrication drawing — kernel inches control",
        "Not a permit drawing, not a UL listing, not a substitute for machine-guarding review",
    ],
    PROFESSIONAL_REVIEW="Licensed/qualified electrician for 115 V. Competent machinery review of guards and first-run. This package is not PE-stamped and is not FABRICATION-READY (unconditional).",
    DATUMS=[
        "D1 Base top face = Z0. Walls sit on it. Stretchers must not lift a wall.",
        "D2 Drum axis = Z 13.50″, Y 18.00″. Both bearing plates from one story stick.",
        "D3 Idle jack at zero = plates coplanar. True the drum, then jack for parallelism.",
        "D4 Acme nuts clocked together before the HTD belt. Paint a witness mark.",
    ],
)

BAGS = [
    dict(id=1, name="DRUM", blurb="21 discs · keyed shaft · end bells · true the OD"),
    dict(id=2, name="FRAME", blurb="doubled walls · steel plates · square the box"),
    dict(id=3, name="TABLE", blurb="torsion platen · UHMW ways · dual Acme"),
    dict(id=4, name="CONVEYOR", blurb="crowned rollers · PVC belt · skew · PWM"),
    dict(id=5, name="DRIVE", blurb="1 HP · hinge · 4L440 · guard · starter"),
    dict(id=6, name="HOOD / TUNE", blurb="dust · wrap · jack · Q01–Q10 · startup card"),
]


def parts():
    """Fabricated + purchased parts. Finished sizes in inches."""
    return [
        dict(PART_ID="F-001", QTY=1, DESC="Base panel", MAT='¾″ Baltic birch', FINISHED="22.00 × 36.00 × 0.75", GRAIN="length = Y", BAG=2, GROUP="frame", MAKE="MAKE"),
        dict(PART_ID="F-002", QTY=1, DESC="Idle wall, doubled skins grain-crossed", MAT='¾″ BB ×2', FINISHED="20.00 × 36.00 × 1.50", GRAIN="skins crossed", BAG=2, GROUP="frame", MAKE="MAKE"),
        dict(PART_ID="F-003", QTY=1, DESC="Drive wall, doubled skins grain-crossed", MAT='¾″ BB ×2', FINISHED="20.00 × 36.00 × 1.50", GRAIN="skins crossed", BAG=2, GROUP="frame", MAKE="MAKE"),
        dict(PART_ID="F-004", QTY=1, DESC="Infeed stretcher", MAT='¾″ BB', FINISHED="16.50 × 3.50 × 0.75", GRAIN="X", BAG=2, GROUP="frame", MAKE="MAKE"),
        dict(PART_ID="F-005", QTY=1, DESC="Outfeed stretcher", MAT='¾″ BB', FINISHED="16.50 × 3.50 × 0.75", GRAIN="X", BAG=2, GROUP="frame", MAKE="MAKE"),
        dict(PART_ID="F-006", QTY=1, DESC="Base rail idle", MAT="hard maple", FINISHED="33.00 × 1.50 × 1.50", GRAIN="Y", BAG=2, GROUP="frame", MAKE="MAKE"),
        dict(PART_ID="F-007", QTY=1, DESC="Base rail drive", MAT="hard maple", FINISHED="33.00 × 1.50 × 1.50", GRAIN="Y", BAG=2, GROUP="frame", MAKE="MAKE"),
        dict(PART_ID="ST-001", QTY=1, DESC="Idle bearing plate, slotted", MAT="A36 ¼″", FINISHED="6.00 × 6.00 × 0.25", GRAIN="n/a", BAG=2, GROUP="steel", MAKE="MAKE"),
        dict(PART_ID="ST-002", QTY=1, DESC="Drive bearing plate, round holes", MAT="A36 ¼″", FINISHED="6.00 × 6.00 × 0.25", GRAIN="n/a", BAG=2, GROUP="steel", MAKE="MAKE"),
        dict(PART_ID="ST-003", QTY=1, DESC="Motor hinge plate", MAT="A36 ¼″", FINISHED="8.00 × 10.00 × 0.25", GRAIN="n/a", BAG=5, GROUP="steel", MAKE="MAKE"),
        dict(PART_ID="ST-004", QTY=1, DESC="Drum shaft keyed", MAT="1144 Stressproof", FINISHED="Ø0.75 × 22.00", GRAIN="n/a", BAG=1, GROUP="drum", MAKE="BUY/MAKE"),
        dict(PART_ID="ST-005", QTY=2, DESC="Square key", MAT="1045 / 1144", FINISHED="0.1875 × 0.1875 × 4.00", GRAIN="n/a", BAG=1, GROUP="drum", MAKE="MAKE"),
        dict(PART_ID="ST-006", QTY=2, DESC="End bell with retainer slot", MAT="Al ⅛″", FINISHED="Ø5.04 × 0.125", GRAIN="n/a", BAG=1, GROUP="drum", MAKE="MAKE"),
        dict(PART_ID="ST-007", QTY=2, DESC="Acme screw ¾-6", MAT="Acme steel", FINISHED="Ø0.75 × 12.00", GRAIN="n/a", BAG=3, GROUP="steel", MAKE="BUY"),
        dict(PART_ID="ST-008", QTY=1, DESC="Drum 4L pulley", MAT="cast iron", FINISHED="Ø4.75 × 0.75, ¾″ bore", GRAIN="n/a", BAG=5, GROUP="steel", MAKE="BUY"),
        dict(PART_ID="ST-009", QTY=1, DESC="Motor 4L pulley", MAT="cast iron", FINISHED="Ø3.00 × 0.75, ¾″ bore", GRAIN="n/a", BAG=5, GROUP="steel", MAKE="BUY"),
        dict(PART_ID="D-001", QTY=21, DESC="Drum disc blank", MAT='¾″ Baltic birch', FINISHED="Ø5.125 × 0.75, bore 0.748", GRAIN="face ply random ok", BAG=1, GROUP="drum", MAKE="MAKE"),
        dict(PART_ID="T-001", QTY=1, DESC="Platen torsion box", MAT='¼″ skins + ¾″ grid', FINISHED="16.25 × 25.00 × 0.75", GRAIN="skins X", BAG=3, GROUP="table", MAKE="MAKE"),
        dict(PART_ID="T-002", QTY=1, DESC="UHMW / HDPE platen face", MAT="UHMW ⅛″", FINISHED="16.25 × 25.00 × 0.125", GRAIN="n/a", BAG=3, GROUP="table", MAKE="MAKE"),
        dict(PART_ID="T-003", QTY=1, DESC="Table way idle", MAT="maple + UHMW", FINISHED="25.00 × 0.50 × 2.00", GRAIN="Y", BAG=3, GROUP="table", MAKE="MAKE"),
        dict(PART_ID="T-004", QTY=1, DESC="Table way drive", MAT="maple + UHMW", FINISHED="25.00 × 0.50 × 2.00", GRAIN="Y", BAG=3, GROUP="table", MAKE="MAKE"),
        dict(PART_ID="T-005", QTY=2, DESC="Acme nut block", MAT="hard maple + bronze nut", FINISHED="2.00 × 2.00 × 3.00", GRAIN="long grain to screw", BAG=3, GROUP="table", MAKE="MAKE"),
        dict(PART_ID="T-006", QTY=1, DESC="Elevation handwheel", MAT="cast 4″ ¾″ bore", FINISHED="Ø4.00 × 0.45", GRAIN="n/a", BAG=3, GROUP="steel", MAKE="BUY"),
        dict(PART_ID="C-001", QTY=1, DESC="Infeed roller, 0.030″ crown", MAT="Al tube 2.00 OD", FINISHED="Ø2.00 × 16.25", GRAIN="n/a", BAG=4, GROUP="conveyor", MAKE="MAKE"),
        dict(PART_ID="C-002", QTY=1, DESC="Outfeed roller, 0.030″ crown", MAT="Al tube 2.00 OD", FINISHED="Ø2.00 × 16.25", GRAIN="n/a", BAG=4, GROUP="conveyor", MAKE="MAKE"),
        dict(PART_ID="C-003", QTY=2, DESC="Roller shaft", MAT="precision ⅝″", FINISHED="Ø0.625 × 22", GRAIN="n/a", BAG=4, GROUP="conveyor", MAKE="BUY"),
        dict(PART_ID="C-004", QTY=1, DESC="Conveyor belt 2-ply PVC endless", MAT="PVC conveyor", FINISHED="16.00 × 60.00", GRAIN="n/a", BAG=4, GROUP="conveyor", MAKE="BUY"),
        dict(PART_ID="M-001", QTY=1, DESC="Drum motor TEFC 56C", MAT="1 HP 1725 115 V", FINISHED="~Ø6.5 × 8.0", GRAIN="n/a", BAG=5, GROUP="motor", MAKE="BUY"),
        dict(PART_ID="M-002", QTY=1, DESC="Feed worm gearmotor 24 V", MAT="~30 RPM", FINISHED="~3 × 3 × 3", GRAIN="n/a", BAG=4, GROUP="motor", MAKE="BUY"),
        dict(PART_ID="M-003", QTY=1, DESC="Drive belt guard, fully enclosed", MAT='¼″ BB', FINISHED="~17 × 17 × 2.2", GRAIN="face", BAG=5, GROUP="guard", MAKE="MAKE"),
        dict(PART_ID="M-004", QTY=1, DESC="Turnbuckle tensioner", MAT="zinc ¼-20 class", FINISHED="~2.1 body", GRAIN="n/a", BAG=5, GROUP="steel", MAKE="BUY"),
        dict(PART_ID="HD-001", QTY=1, DESC="Dust hood inverted-U", MAT='¼″ BB', FINISHED="~16.3 × 8.4 × 1.6", GRAIN="face", BAG=6, GROUP="hood", MAKE="MAKE"),
        dict(PART_ID="HD-002", QTY=1, DESC="4″ dust flange", MAT="ABS / steel", FINISHED="Ø4.00 port", GRAIN="n/a", BAG=6, GROUP="hood", MAKE="BUY"),
        dict(PART_ID="HD-003", QTY=1, DESC="Nylon brush strip", MAT="nylon", FINISHED="16.00", GRAIN="n/a", BAG=6, GROUP="hood", MAKE="BUY"),
        dict(PART_ID="N-001", QTY=1, DESC="Optional 32″ cabinet stand", MAT='¾″ BB', FINISHED="22 × 32 × 32", GRAIN="vert. sides", BAG=6, GROUP="stand", MAKE="MAKE"),
    ]


def hardware_planforge():
    """Hardware schedule with evidence class. Catalog numbers are lookup hints."""
    rows = []
    n = 1
    for h in HARDWARE:
        pn = h.get("mcmaster") or ""
        ev = "S" if pn in ("6245K47", "6191K37") else ("E" if pn else "E")
        if pn in ("6245K47", "6191K37"):
            note = "Published in public ShopNotes #86 hardware notes — still verify live catalog"
        elif pn:
            note = "Search-hint PN. Open the live catalog; measure the part in hand."
        else:
            note = "No PN. Buy by search term / rating."
        url = f"https://www.mcmaster.com/{pn}/" if pn else ""
        rows.append(
            dict(
                LINE=f"MC-{n:03d}",
                HARDWARE_ID=f"H-{n:03d}",
                ROLE="REQUIRED",
                PN=pn or "VERIFY",
                URL=url,
                DESCRIPTION=h["item"],
                QTY=h["qty"],
                UNIT="ea",
                WHERE=h.get("search", ""),
                FAMILY="buy",
                EVIDENCE=ev,
                SUBSTITUTE="Match interface + rating, not the SKU string",
                NOTE=note,
            )
        )
        n += 1
    return rows


def requirements():
    return [
        dict(ID="FUN-001", PRI="MUST", STATEMENT="Sand stock 16.00″ wide × 0.06–4.00″ thick in light passes", VERIFY="Q09 first poplar 0.010″ even cut", STATUS="PROPOSED", EVIDENCE="G"),
        dict(ID="FUN-002", PRI="MUST", STATEMENT="Powered feed 0–16 FPM that tracks a 16″ PVC conveyor", VERIFY="Q04 empty 60 s then loaded", STATUS="PROPOSED", EVIDENCE="G"),
        dict(ID="FUN-003", PRI="MUST", STATEMENT="Dedicated 1 HP TEFC drive — not a table-saw parasite", VERIFY="M-001 nameplate + 3.00/4.75 pulleys", STATUS="PROPOSED", EVIDENCE="G"),
        dict(ID="FUN-004", PRI="SHOULD", STATEMENT="Optional 32″ cabinet stand, platen ~36–40″ AFF", VERIFY="N-001 or omit", STATUS="PROPOSED", EVIDENCE="A"),
        dict(ID="DIM-001", PRI="MUST", STATEMENT="Envelope 22 × 36 × 20″ benchtop; drum Ø 5.00 × 16.00 face", VERIFY="F-001 + D-001 after turning", STATUS="PROPOSED", EVIDENCE="G/D"),
        dict(ID="DIM-002", PRI="MUST", STATEMENT="Datums D1–D4 controlling; inches primary", VERIFY="story stick + winding sticks", STATUS="PROPOSED", EVIDENCE="G"),
        dict(ID="LOAD-001", PRI="MUST", STATEMENT="Drum ~1089 RPM / ~1427 SFM from 1725 × 3.00/4.75", VERIFY="tach or pulley ratio [D]", STATUS="PROPOSED", EVIDENCE="D"),
        dict(ID="MAT-001", PRI="MUST", STATEMENT="Baltic birch drum and walls. No MDF. No Formica platen. No sanding-belt conveyor.", VERIFY="BOM contains none of the excluded items", STATUS="PROPOSED", EVIDENCE="G"),
        dict(ID="JNT-001", PRI="MUST", STATEMENT="Keyed ¾″ shaft, 0.5 mm expansion gaps every 4 discs", VERIFY="dry-stack before glue", STATUS="PROPOSED", EVIDENCE="G"),
        dict(ID="JNT-002", PRI="MUST", STATEMENT="Dual ¾-6 Acme HTD-timed; no independent corner screws", VERIFY="D4 witness marks", STATUS="PROPOSED", EVIDENCE="G"),
        dict(ID="SAFE-001", PRI="MUST", STATEMENT="Magnetic starter / no-volt release + mushroom E-stop; no auto-restart", VERIFY="Q06 blink test", STATUS="OPEN", EVIDENCE="P"),
        dict(ID="SAFE-002", PRI="MUST", STATEMENT="Fully enclosed drive guard; 4″ hood @ ≥400 CFM; 12″ min stock or carrier", VERIFY="Q07 Q08 + startup card", STATUS="PROPOSED", EVIDENCE="G"),
        dict(ID="SAFE-003", PRI="MUST", STATEMENT="Risk R3 powered machine. Release FABRICATION-READY WITH CONDITIONS. Not PE-stamped.", VERIFY="G-001 banner on every affected sheet", STATUS="PROPOSED", EVIDENCE="P"),
        dict(ID="DOC-001", PRI="MUST", STATEMENT="WOODWRIGHT PLANFORGE guidebook + LEGO manual + kernel CAD + W-1…W-14 + fab CSVs", VERIFY="/sander/walter/planforge/ + /manual/ + /cad/", STATUS="PROPOSED", EVIDENCE="G"),
        dict(ID="MAINT-001", PRI="MUST", STATEMENT="Replaceable wrap (hook tape + end-bell slots), replaceable UHMW face, accessible bearings", VERIFY="W-13 wrap; T-002 screws", STATUS="PROPOSED", EVIDENCE="G"),
        dict(ID="EXCL-001", PRI="EXCLUDED", STATEMENT="MDF drum/walls; sanding belt as conveyor; PVC-pipe rollers; gravity motor on a dowel; Formica platen; light-switch-only disconnect; ShopNotes #86 reprint", VERIFY="BOM + lineage note", STATUS="VERIFIED", EVIDENCE="G"),
    ]


def joinery():
    return [
        dict(JOINT_ID="J-DRUM", TYPE="Keyed disc stack", PART_A="D-001 ×21", PART_B="ST-004 + ST-005", FUNCTION="Transmit torque; stay round", GEOMETRY="bore 0.748, key 3/16, gap 0.5 mm / 4 discs", FIT="0.002 under shaft; freeze/warm or ream", ADHESIVE="PVA on faces; no glue in keyway", DRAWING="J-201 / W-3", INSPECTION="Q02 OD 5.000±0.010"),
        dict(JOINT_ID="J-WALL", TYPE="Crossed-grain laminate", PART_A="F-002 skins", PART_B="F-003 skins", FUNCTION="Stiff closed frame", GEOMETRY="¾+¾, grain crossed", FIT="glue-flat on a door", ADHESIVE="PVA, cauls", DRAWING="P-202 / W-2", INSPECTION="Q01 square + winding sticks"),
        dict(JOINT_ID="J-PLATE", TYPE="Bolted steel to birch", PART_A="ST-001/002", PART_B="F-002/003", FUNCTION="Bearing seats; idle jack travel", GEOMETRY="6×6×¼; idle slots 0.90 vertical", FIT="plate is the drill jig", ADHESIVE="none — mechanical", DRAWING="P-203 / W-2", INSPECTION="story stick D2"),
        dict(JOINT_ID="J-WAY", TYPE="UHMW dado slide", PART_A="T-003/004", PART_B="F-002/003 dados", FUNCTION="Parallel elevation", GEOMETRY="0.50 × 2.00 ways, 0.02–0.04 slide", FIT="sliding", ADHESIVE="UHMW mechanical / epoxy spots", DRAWING="J-202 / W-4", INSPECTION="4.50 travel parallel"),
        dict(JOINT_ID="J-ACME", TYPE="Bronze nut in maple block", PART_A="ST-007", PART_B="T-005", FUNCTION="Timed lift", GEOMETRY="¾-6, HTD 5 mm 16T", FIT="clock nuts D4 before belt", ADHESIVE="nut captured, not Loctite on Acme", DRAWING="J-202 / W-4", INSPECTION="Q05 witness"),
        dict(JOINT_ID="J-CROWN", TYPE="Belt on crowned rollers", PART_A="C-004", PART_B="C-001/C-002", FUNCTION="Track feed", GEOMETRY="0.030 barrel, idle skew ¼-20", FIT="1/32 above platen", ADHESIVE="endless splice from supplier", DRAWING="J-203 / W-5", INSPECTION="Q04"),
        dict(JOINT_ID="J-WRAP", TYPE="Spiral abrasive on hook tape", PART_A="3″ roll", PART_B="D-001 stack + ST-006 slots", FUNCTION="Cutting face, replaceable", GEOMETRY="θ≈17°, start idle slot", FIT="no lumps", ADHESIVE="PSA hook only", DRAWING="J-204 / W-13", INSPECTION="carrier board full-face cut"),
        dict(JOINT_ID="J-HINGE", TYPE="Hinged motor plate + turnbuckle", PART_A="ST-003 + M-001", PART_B="F-003", FUNCTION="Belt tension without gravity slack", GEOMETRY="¼ plate, 4L440", FIT="turnbuckle lock", ADHESIVE="none", DRAWING="M-101 / W-6", INSPECTION="Q08 guard + belt tracking"),
    ]


def dimensions():
    return [
        dict(DIM_ID="DIM-ENV-X", NOMINAL="22.00", TOL="±0.03", UNIT="in", DATUM="D1", FEATURE="Base width X", CLASS="G", EQ="P.base_x", SHEET="A-102 / W-1", INSPECT="tape"),
        dict(DIM_ID="DIM-ENV-Y", NOMINAL="36.00", TOL="±0.03", UNIT="in", DATUM="D1", FEATURE="Base depth Y", CLASS="G", EQ="P.base_y", SHEET="A-102 / W-1", INSPECT="tape"),
        dict(DIM_ID="DIM-WALL-T", NOMINAL="1.50", TOL="±0.02", UNIT="in", DATUM="D1", FEATURE="Doubled wall", CLASS="D", EQ="2×0.75", SHEET="P-202", INSPECT="caliper"),
        dict(DIM_ID="DIM-INNER", NOMINAL="16.50", TOL="±0.03", UNIT="in", DATUM="idle inner", FEATURE="Clear between walls", CLASS="G", EQ="P.inner_w", SHEET="A-102", INSPECT="inside stick"),
        dict(DIM_ID="DIM-FACE", NOMINAL="16.00", TOL="±0.02", UNIT="in", DATUM="D2", FEATURE="Drum face", CLASS="G", EQ="P.drum_face", SHEET="P-201", INSPECT="caliper"),
        dict(DIM_ID="DIM-OD", NOMINAL="5.000", TOL="±0.010", UNIT="in", DATUM="shaft axis", FEATURE="Turned drum OD", CLASS="T", EQ="true after glue", SHEET="J-201", INSPECT="Q02"),
        dict(DIM_ID="DIM-AXIS-Z", NOMINAL="13.50", TOL="±0.02", UNIT="in", DATUM="D1", FEATURE="Drum axis height", CLASS="G", EQ="P.drum_z", SHEET="A-103", INSPECT="story stick"),
        dict(DIM_ID="DIM-AXIS-Y", NOMINAL="18.00", TOL="±0.02", UNIT="in", DATUM="infeed face", FEATURE="Drum axis Y", CLASS="G", EQ="P.drum_y", SHEET="A-102", INSPECT="story stick"),
        dict(DIM_ID="DIM-BORE", NOMINAL="0.748", TOL="+0.000/−0.002", UNIT="in", DATUM="disc center", FEATURE="Disc bore", CLASS="G", EQ="shaft − 0.002", SHEET="P-201 / T-DISC", INSPECT="pin gauge"),
        dict(DIM_ID="DIM-CROWN", NOMINAL="0.030", TOL="±0.005", UNIT="in", DATUM="roller CL", FEATURE="Barrel crown", CLASS="G", EQ="P.roller_crown", SHEET="J-203", INSPECT="caliper mid vs end"),
        dict(DIM_ID="DIM-CD", NOMINAL="26.86", TOL="±0.05", UNIT="in", DATUM="infeed roller", FEATURE="Roller centers", CLASS="D", EQ="P.roller_cd", SHEET="A-102", INSPECT="tape"),
        dict(DIM_ID="DIM-ACME", NOMINAL="0.1667", TOL="REF", UNIT="in/rev", DATUM="n/a", FEATURE="Elevation pitch", CLASS="D", EQ="1/6 TPI", SHEET="M-103", INSPECT="count revs"),
        dict(DIM_ID="DIM-TRAVEL", NOMINAL="4.50", TOL="±0.05", UNIT="in", DATUM="D1", FEATURE="Table travel", CLASS="G", EQ="P.travel", SHEET="W-4", INSPECT=" DRO"),
        dict(DIM_ID="DIM-JACK", NOMINAL="±0.040", TOL="range", UNIT="in", DATUM="D3", FEATURE="Idle jack", CLASS="G", EQ="¼-20", SHEET="J-202", INSPECT="feeler 16″ board"),
        dict(DIM_ID="DIM-RPM", NOMINAL=f"{drum_rpm:.0f}", TOL="REF", UNIT="rpm", DATUM="n/a", FEATURE="Drum speed", CLASS="D", EQ="1725×3.00/4.75", SHEET="G-002", INSPECT="tach optional"),
        dict(DIM_ID="DIM-SFM", NOMINAL=f"{sfm:.0f}", TOL="REF", UNIT="sfm", DATUM="n/a", FEATURE="Surface speed", CLASS="D", EQ="π×5×rpm/12", SHEET="G-002", INSPECT="calc"),
        dict(DIM_ID="DIM-FEED", NOMINAL=f"{feed_fpm:.1f}", TOL="REF", UNIT="fpm", DATUM="n/a", FEATURE="Feed at 30 rpm roller", CLASS="D", EQ="π×2/12×30", SHEET="M-102", INSPECT="mark & clock"),
    ]


def steps():
    """LEGO manual steps. bag, title, note, parts [(qty, pid, label)], groups to highlight."""
    return [
        dict(n=1, bag=1, title="Bandsaw 21 disc blanks", note="Template T-DISC at 100%. Check the 1.00″ bar.", parts=[(21, "D-001", "Ø 5.125 blank")], groups=["drum"], key="CUT"),
        dict(n=2, bag=1, title="Bore 0.748″ and file the keyway", note="Drill-press fence. Every hole shares a center.", parts=[(21, "D-001", "bored discs"), (2, "ST-005", "3/16 keys")], groups=["drum"], key="BORE"),
        dict(n=3, bag=1, title="Dry-stack on the keyed shaft", note="0.5 mm gaps every four discs. Number 1–21.", parts=[(1, "ST-004", "¾″ × 22 shaft"), (21, "D-001", "discs")], groups=["drum"], key="STACK"),
        dict(n=4, bag=1, title="Glue the column · fit end bells", note="Clamp as a column. No glue in the keyway.", parts=[(2, "ST-006", "⅛″ Al bells")], groups=["drum"], key="GLUE"),
        dict(n=5, bag=1, title="True the OD to 5.000″", note="Between centers, or later in the machine on a carrier.", parts=[(1, "D-001", "turned stack")], groups=["drum"], key="TRUE"),
        dict(n=6, bag=2, title="Glue doubled walls, grain crossed", note="On a flat door. Cauls. This is the machine’s stiffness.", parts=[(1, "F-002", "idle wall"), (1, "F-003", "drive wall")], groups=["frame"], key="WALLS"),
        dict(n=7, bag=2, title="Steel plates as drill jigs", note="Idle plate: slot two holes 0.90″. Drive plate: round, fixed.", parts=[(1, "ST-001", "idle plate"), (1, "ST-002", "drive plate")], groups=["frame", "steel"], key="PLATES"),
        dict(n=8, bag=2, title="Square the box on datum D1", note="Stretchers, maple rails, base. Winding sticks on plate faces.", parts=[(1, "F-001", "base"), (1, "F-004", "stretcher in"), (1, "F-005", "stretcher out"), (1, "F-006", "rail idle"), (1, "F-007", "rail drive")], groups=["frame"], key="BOX"),
        dict(n=9, bag=2, title="Idle jack screws at D3 zero", note="¼-20 under UCFL204. Jacks at mid-slot = plates coplanar.", parts=[(2, "ST-001", "idle plate + UCFL204-12")], groups=["steel"], key="JACK"),
        dict(n=10, bag=3, title="Build the torsion-box platen", note="¼″ skins, ¾″ grid. Flat to a straightedge.", parts=[(1, "T-001", "platen")], groups=["table"], key="PLATEN"),
        dict(n=11, bag=3, title="UHMW face and dados for ways", note="0.02–0.04″ sliding fit. Oil the ways, never paint them.", parts=[(1, "T-002", "UHMW face"), (1, "T-003", "way idle"), (1, "T-004", "way drive")], groups=["table"], key="WAYS"),
        dict(n=12, bag=3, title="Clock Acme nuts · HTD · handwheel", note="Datum D4. Witness paint before the belt.", parts=[(2, "ST-007", "¾-6 × 12"), (2, "T-005", "nut blocks"), (1, "T-006", "4″ handwheel")], groups=["table", "steel"], key="ACME"),
        dict(n=13, bag=4, title="Turn 0.030″ crowns · mount rollers", note="Both rollers. Flat rollers will not self-center.", parts=[(1, "C-001", "infeed roller"), (1, "C-002", "outfeed roller"), (2, "C-003", "⅝″ shafts")], groups=["conveyor"], key="ROLL"),
        dict(n=14, bag=4, title="Endless PVC belt · skew · PWM", note="Not a sanding belt. Track empty, then loaded.", parts=[(1, "C-004", "16×60 PVC"), (1, "M-002", "24 V gearmotor")], groups=["conveyor", "motor"], key="BELT"),
        dict(n=15, bag=5, title="Hinge plate, 1 HP, pulleys", note="Turnbuckle tension — not motor weight on a dowel.", parts=[(1, "ST-003", "hinge plate"), (1, "M-001", "1 HP TEFC"), (1, "ST-008", "4.75 pulley"), (1, "ST-009", "3.00 pulley"), (1, "M-004", "turnbuckle")], groups=["motor", "steel"], key="MOTOR"),
        dict(n=16, bag=5, title="4L440 · full guard · starter", note="No finger slot at the pinch. Magnetic starter + E-stop.", parts=[(1, "M-003", "belt guard")], groups=["guard", "motor"], key="GUARD"),
        dict(n=17, bag=6, title="Hood, 4″ port, brush strip", note="Foam to the walls. Collector on before any test cut.", parts=[(1, "HD-001", "hood"), (1, "HD-002", "4″ port"), (1, "HD-003", "brush")], groups=["hood"], key="HOOD"),
        dict(n=18, bag=6, title="Hook tape and spiral wrap", note="Start in the idle-end bell slot. Trace the first wrap.", parts=[(1, "D-001", "wrapped drum")], groups=["drum"], key="WRAP"),
        dict(n=19, bag=6, title="Jack parallelism on a 16″ board", note="Kiss both ends. Then ¼-20 ±0.040″.", parts=[], groups=["steel", "drum", "table"], key="PARA"),
        dict(n=20, bag=6, title="Inspection Q01–Q10", note="Blink test. Guard closed. Hood pulling. Witness marks.", parts=[], groups=["frame"], key="QA"),
        dict(n=21, bag=6, title="Post the startup card", note="Collector → hood → lock → drum → feed. Never start with a board under the drum.", parts=[], groups=["frame", "drum", "table", "hood"], key="CARD"),
        dict(n=22, bag=6, title="First 0.010″ pass in poplar", note="Then oak. If the motor note changes, you took too much. This is not a planer.", parts=[], groups=["frame", "drum", "table", "conveyor", "motor", "hood"], key="FIRST"),
    ]


def evidence():
    return [
        dict(ID="EV-001", DESC="Capacity 16″ × 0.06–4.00″, envelope 22×36×20″", CLASS="G", RELIABILITY="high", VERIFY="kernel P dict"),
        dict(ID="EV-002", DESC="Ron Walters woodgears write-up + YouTube W-5Sj6kBVic (same machine)", CLASS="G", RELIABILITY="high as failure modes", VERIFY="open sources; do not scan ShopNotes #86"),
        dict(ID="EV-003", DESC="Drum RPM = 1725 × 3.00 / 4.75", CLASS="D", RELIABILITY="arithmetic", VERIFY="nameplates + pulley stamps"),
        dict(ID="EV-004", DESC="SFM = π × 5.00 × rpm / 12", CLASS="D", RELIABILITY="arithmetic", VERIFY="recalc"),
        dict(ID="EV-005", DESC="4L pulley 4.75 / 4L440 link (6245K47 / 6191K37)", CLASS="S", RELIABILITY="public hardware notes; catalog drifts", VERIFY="live McMaster page"),
        dict(ID="EV-006", DESC="Other McMaster PNs in hardware.csv", CLASS="E", RELIABILITY="search hints", VERIFY="open catalog; measure in hand"),
        dict(ID="EV-007", DESC="Crown 0.030″ barrel as tracking geometry", CLASS="A/G", RELIABILITY="craft practice + Walters failure", VERIFY="Q04 belt track"),
        dict(ID="EV-008", DESC="115 V starter / FLA / OL heaters", CLASS="P", RELIABILITY="unverified here", VERIFY="electrician + motor nameplate"),
        dict(ID="EV-009", DESC="USDA FPL Wood Handbook moisture/movement (general birch)", CLASS="S", RELIABILITY="handbook", VERIFY="acclimate BB; 0.5 mm gaps"),
        dict(ID="EV-010", DESC="OSHA 1910.212 / 1910.213 machine guarding (U.S.)", CLASS="P/S", RELIABILITY="adopted code varies", VERIFY="competent machinery review; this is not a compliance cert"),
    ]


def build_project():
    return dict(
        project=PROJECT,
        P=P,
        bags=BAGS,
        parts=parts(),
        hardware=hardware_planforge(),
        requirements=requirements(),
        joinery=joinery(),
        dimensions=dimensions(),
        steps=steps(),
        evidence=evidence(),
        fmea=FMEA,
        plywood=PLYWOOD,
        derived=dict(drum_rpm=round(drum_rpm, 2), sfm=round(sfm, 1), feed_fpm=round(feed_fpm, 2)),
    )
