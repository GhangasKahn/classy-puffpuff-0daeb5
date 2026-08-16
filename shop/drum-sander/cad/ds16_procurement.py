#!/usr/bin/env python3
"""WALTER DS-16 Rev C — itemized McMaster-Carr procurement register.

VERIFICATION STATUS — read this before ordering
-----------------------------------------------
McMaster-Carr part numbers in this file are NOT machine-verified. On 2026-08-15
two automated attempts were made to read live part numbers off mcmaster.com:

  1. plain HTTP fetch of a category page  -> site returns "requires JavaScript"
  2. scripted browser session, category + search pages -> page chrome rendered,
     but the results table did not expose part numbers to extraction

Under WOODWRIGHT PLANFORGE `fasteners_and_hardware` an exact manufacturer part
number may only be stated when verified, so no part number is asserted here.
What IS given for every line is stronger than a part number anyway:

  * the engineering specification that actually controls the design
  * which computed requirement or drawing the spec comes from
  * the mating part IDs
  * a substitution rule written in terms of performance and interface
  * a working McMaster search link for the line
  * the prep/installation note

`part_number` is therefore the literal string "CONFIRM AT ORDER" and is tagged
[A]. Fill it in from the product page, then re-run the validator, which checks
that every safety- or fit-critical line has been confirmed before the package
may advance past FABRICATION REVIEW.

Nothing in this file is a price, availability, or rating claim.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus

try:
    from ds16_mechanics import (
        MECH,
        AXIS,
        bearing_requirement,
        drum_mass,
        drum_rpm,
        dust_requirement,
        micro_adjust,
    )
except ImportError:  # pragma: no cover - direct execution from another cwd
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from ds16_mechanics import (  # type: ignore
        MECH,
        AXIS,
        bearing_requirement,
        drum_mass,
        drum_rpm,
        dust_requirement,
        micro_adjust,
    )

MCMASTER_BASE = "https://www.mcmaster.com/"
UNVERIFIED = "CONFIRM AT ORDER"


def mcmaster_search(query: str) -> str:
    """A real, clickable McMaster search URL.

    Uses the site's own query parameter rather than a guessed catalogue slug, so
    the link cannot rot into a 404 the way an invented part URL would.
    """
    return f"{MCMASTER_BASE}?q={quote_plus(query)}"


def _line(
    pid: str,
    desc: str,
    qty: str,
    spec: str,
    query: str,
    *,
    mates: str = "",
    prep: str = "",
    install: str = "",
    substitute: str = "",
    basis: str = "",
    critical: str = "fit",
    alt_supplier: str = "",
    evidence: str = "D",
) -> dict[str, Any]:
    return {
        "item_id": pid,
        "description": desc,
        "qty": qty,
        "controlling_spec": spec,
        "mating_parts": mates,
        "hole_or_prep": prep,
        "installation": install,
        "substitution_rule": substitute,
        "design_basis": basis,
        "criticality": critical,          # safety | fit | consumable
        "supplier": "McMaster-Carr",
        "part_number": UNVERIFIED,
        "part_number_evidence": "A",
        "link": mcmaster_search(query),
        "search_query": query,
        "alt_supplier": alt_supplier,
        "evidence": evidence,
    }


def procurement(m=MECH) -> list[dict[str, Any]]:
    g = AXIS
    brg = bearing_requirement((drum_mass(m)["total"] + m.force_reference) / 2.0,
                              drum_rpm(m), m)
    adj = micro_adjust(m)
    dust = dust_requirement(m)

    rows: list[dict[str, Any]] = []

    # ---------------- drum axis: the Rev C heart -------------------------
    rows.append(_line(
        "MC-01",
        f'Aluminum round tube, {m.shell_od:g}" OD x {m.shell_wall:g}" wall — drum shell',
        f'1 pc x 18" (finish {m.drum_length:g}")',
        f'6061-T6, {m.shell_od:g}" OD, {m.shell_wall:g}" wall (ID {g.shell_id:g}"). '
        f'Wall is a stiffness requirement, not cosmetic: I = {g.i_shell:.2f} in^4.',
        f'6061 aluminum round tube {m.shell_od:g}" OD {m.shell_wall:g}" wall',
        mates="P-020 shell, P-021 end plugs",
        prep="Cut 1/8 long, face both ends square in a lathe or on a sled. "
             "Bore/turn OD true AFTER assembly to the shaft.",
        install="Bond + pin to P-021 plugs. See J-106.",
        substitute="Any 6061 or 6063 tube with OD 5.000 -0.000/+0.030 and wall "
                   ">= 0.180 in. Do NOT substitute thin-wall decorative tube: "
                   "wall drives the stiffness in CALC-C02.",
        basis="CALC-C02 series-model drum crown",
        critical="safety",
    ))
    rows.append(_line(
        "MC-02",
        f'Precision-ground rotary shaft, {m.shaft_od:g}" dia — drum shaft',
        f'1 pc x {m.shaft_length:g}"',
        f'{m.shaft_od:g}" dia, ground and polished, straightness <= 0.001"/ft, '
        f'surface finish suitable for a set-screw insert.',
        f'precision ground rotary shaft {m.shaft_od:g} inch diameter',
        mates="P-010 shaft, H-001/H-002 bearings, P-021 plugs, H-004 sheave",
        prep="Cut to length, chamfer both ends 0.030 x 45 deg, deburr. Do not "
             "centre-punch the bearing seats.",
        install="Slide through the drum and both panels together — see ST-12.",
        substitute=f"1045 TG&P or 1566 ground shafting, {m.shaft_od:g}\" -0.001/-0.000. "
                   "Hot-rolled bar is NOT acceptable: TIR would consume the whole "
                   "alignment budget.",
        basis="CALC-C01/C02 shaft stiffness sweep",
        critical="safety",
    ))
    rows.append(_line(
        "MC-03",
        f'Mounted ball bearing, {m.shaft_od:g}" bore, self-aligning insert',
        "2 ea (1 fixed drive + 1 floating idler)",
        f'{m.shaft_od:g}" bore, spherical-seat (self-aligning) insert, set-screw or '
        f'eccentric-collar locking, sealed. REQUIRED basic dynamic capacity '
        f'C >= {brg["c_required"]:.0f} lbf for {brg["life_hours"]:.0f} h at '
        f'{brg["rpm"]:.0f} rpm. Static misalignment capability >= '
        f'{adj["required_selfalign_deg"]:.3f} deg.',
        f'mounted ball bearing flange {m.shaft_od:g} inch bore self-aligning',
        mates="P-001L (fixed), P-023 idler adjust plate (floating), P-010 shaft",
        prep=f'Bolt pattern: MEASURE the flange you receive and transfer to P-001L / '
             f'P-023. Do not drill from the drawing — flange bolt circle is [A].',
        install="Drive end LOCKED. Idler end axially FREE. Never lock both — see J-007.",
        substitute="Any 2- or 4-bolt flange or pillow block meeting the bore, the "
                   "C requirement and the self-aligning requirement. Confirm C on "
                   "the vendor page; a bearing chosen by bore alone is not specified.",
        basis="CALC-C11 required C; CALC-C08 misalignment",
        critical="safety",
    ))
    rows.append(_line(
        "MC-04",
        'Aluminum round bar, 4-1/2" dia — drum end plugs',
        f'1 pc x 4" (yields 2 plugs {m.plug_thick:g}" thick)',
        f'6061-T6 round bar, >= {g.shell_id:g}" dia. Turn to a light press/bond fit in '
        f'the shell ID and bore {m.shaft_od:g}" H7-equivalent for the shaft.',
        '6061 aluminum round bar 4-1/2 inch diameter',
        mates="P-021 plug, P-020 shell, P-010 shaft",
        prep=f'Bore {m.shaft_od:g}" on the same setup as the OD turn so bore and OD are '
             f'concentric. Concentricity here becomes drum TIR.',
        install="Bond into shell, cross-pin, then clamp to shaft — see J-106.",
        substitute="Phenolic or hard maple acceptable for Option B only; aluminum "
                   "preferred because it holds the bore under humidity change.",
        basis="ALN-01 drum TIR budget",
        critical="safety",
    ))
    rows.append(_line(
        "MC-05",
        f'Clamping shaft collar, {m.shaft_od:g}" bore',
        "4 ea",
        f'Two-piece or single-piece clamping collar, {m.shaft_od:g}" bore, steel or '
        f'aluminum. Used to locate the plugs axially and to set the fixed-bearing '
        f'shoulder. Clamp type only — set-screw collars mar the ground shaft.',
        f'clamping shaft collar {m.shaft_od:g} inch bore two piece',
        mates="P-010 shaft, P-021 plugs, H-001 bearing",
        prep="None. Do not drill the shaft.",
        install="Tighten opposite-corner sequence to the collar maker's torque.",
        substitute="Any clamp-style collar of the correct bore. Set-screw collars "
                   "are excluded by interface, not by preference.",
        basis="J-106 axial location",
        critical="fit",
    ))

    # ---------------- precision adjustment ------------------------------
    rows.append(_line(
        "MC-06",
        'Socket head cap screw, 1/4-28 — parallelism micro-adjust jack',
        "2 ea (1 live + 1 spare)",
        f'1/4-28 x 1-1/2" alloy socket head cap screw. Fine thread is the '
        f'requirement: lead {adj["lead"]:.5f}" gives '
        f'{adj["at_work_15deg"] * 1000:.2f} mil at the work per 15 deg of knob.',
        '1/4-28 socket head cap screw alloy steel 1-1/2 long',
        mates="P-023 idler adjust plate, P-024 jack block",
        prep="Tap P-024 1/4-28 through. Chase the thread clean; a ragged thread "
             "shows up as backlash in the adjustment.",
        install="Brass or nylon tip pad under the screw point so it does not dig "
                "into the plate and lose calibration.",
        substitute="M6x0.75 acceptable if the lead is recomputed and the sheet is "
                   "revised. Do NOT use 1/4-20: resolution degrades ~40%.",
        basis="CALC-C07 micro-adjust resolution",
        critical="fit",
    ))
    rows.append(_line(
        "MC-07",
        'Brass-tip set screw, 1/4-20 — gib adjusters',
        "6 ea",
        '1/4-20 brass-tipped or nylon-tipped set screw. Brass tip loads the gib '
        'without embedding in it.',
        'brass tipped set screw 1/4-20',
        mates="P-022 gib, P-001R side",
        prep="Tap 3 stations per way, 1/4-20.",
        install=f'Set gib for {m.gib_clearance * 1000:.1f} mil running clearance: table '
                f'slides by hand with no perceptible rock. Q-102 records it.',
        substitute="Any tipped set screw. A bare steel set screw is excluded: it "
                   "brinells the gib and the setting drifts.",
        basis="CALC-C05 way play term; D-032",
        critical="fit",
    ))
    rows.append(_line(
        "MC-08",
        'Hardened dowel pin, 3/8" x 2" — idler plate pivot',
        "2 ea",
        '3/8" x 2" hardened, ground dowel pin. The pivot must not wear oval or '
        'the parallelism setting walks.',
        'hardened precision dowel pin 3/8 x 2',
        mates="P-023 idler adjust plate, P-001R side",
        prep='Ream 3/8" for a light press in the plate, slip fit in the side.',
        install="Press into the plate, retain with a collar or E-clip.",
        substitute="Ground shoulder bolt of the same diameter is acceptable.",
        basis="D-033 pivot-plate architecture",
        critical="fit",
    ))
    rows.append(_line(
        "MC-09",
        'Dial indicator, 1" travel, 0.001" graduations + magnetic base',
        "1 ea",
        'Travel >= 1", resolution 0.001", lug or stem back. Magnetic base with '
        'a fine adjust. This is the instrument that proves ALN-01 and TV-01.',
        'dial indicator 1 inch travel 0.001 graduation magnetic base',
        mates="Q-101 acceptance, indicator pad on P-001L",
        prep="1/4-20 tapped pad already on P-001L.",
        install="Read at station A (drive) and station B (idler), paper on, "
                "spindle perpendicular to the table.",
        substitute="0.0005\" indicator or a digital caliper in wooden blocks. A tape "
                   "measure cannot verify this specification.",
        basis="ALN-01, TV-01 verification method",
        critical="safety",
    ))

    # ---------------- lift ------------------------------------------------
    rows.append(_line(
        "MC-10",
        'Acme lead screw, 1/2"-10, single lead',
        f'2 pc x {12.0:g}"',
        f'1/2-10 single-lead Acme, steel. Lead 0.100"/rev gives '
        f'{0.1 / m.handwheel_divisions * 1000:.2f} mil per handwheel division.',
        '1/2-10 acme threaded rod lead screw',
        mates="P-016 nut block, P-018 thrust block, H-008 chain",
        prep="Cut square, chase the end thread, chamfer.",
        install="Loaded in COMPRESSION under the table. Always approach the final "
                "setting by raising — see D-034.",
        substitute="1/2-10 2-start acme is NOT interchangeable: it doubles the lead "
                   "and halves the resolution. Revise the sheet if used.",
        basis="CALC-C09, CALC-C10",
        critical="fit",
    ))
    rows.append(_line(
        "MC-11",
        'Bronze Acme nut, 1/2"-10',
        "2 ea",
        'Bronze or acetal Acme nut to match MC-10 lead. Flanged preferred so it '
        'can be bolted to P-016.',
        'bronze acme nut 1/2-10',
        mates="P-016 nut block, MC-10 screw",
        prep="Bore P-016 for a press fit; do not rely on adhesive alone.",
        install="Both nuts installed before the chain is fitted so the table "
                "cannot cock.",
        substitute="Any nut matching the screw lead and axial load. Verify the "
                   "thread is the same hand and lead as MC-10.",
        basis="CALC-C09",
        critical="fit",
    ))
    rows.append(_line(
        "MC-12",
        'Roller chain #25 + sprockets, 1/2" bore',
        "1 x 3 ft chain, 2 sprockets, 1 connecting link",
        '#25 roller chain, two matched sprockets 1/2" bore with set screw. Equal '
        'tooth count is mandatory — unequal sprockets tilt the table.',
        'roller chain 25 sprocket 1/2 inch bore',
        mates="MC-10 screws, H-008",
        prep="Key or set-screw flat on each screw end.",
        install="Fit with both screws at the SAME height, verified by indicator "
                "before the chain is closed.",
        substitute="Timing belt and matched pulleys are acceptable and quieter. "
                   "Tooth counts must be equal.",
        basis="D-003 coupled dual-screw lift",
        critical="safety",
    ))
    rows.append(_line(
        "MC-13",
        'Handwheel with graduated dial, 1/2" bore',
        "1 ea",
        f'Handwheel >= 4" dia, 1/2" bore, with a graduated or markable rim. '
        f'{m.handwheel_divisions} divisions -> '
        f'{0.1 / m.handwheel_divisions * 1000:.2f} mil per division.',
        'handwheel graduated dial 1/2 inch bore 4 inch',
        mates="MC-10 screw",
        prep="Set screw flat on the screw end.",
        install="Index the dial to zero at the home dog (P-019).",
        substitute="Plain handwheel plus a shop-made paper dial is acceptable if "
                   "graduation count is recorded on Q-102.",
        basis="CALC-C10",
        critical="fit",
    ))

    # ---------------- ways, table, structure ------------------------------
    rows.append(_line(
        "MC-14",
        'UHMW bar, 3/4" x 2-1/2" — vertical ways and gib',
        '1 pc x 4 ft',
        f'UHMW-PE bar 3/4" x 2-1/2". Two ways plus gib stock plus spare. Dry '
        f'bearing: wax only, never oil.',
        'UHMW polyethylene bar 3/4 x 2-1/2',
        mates="P-007 way, P-022 gib, P-001L/R",
        prep="Machine the gib taper 1:40 on the table saw with a taper jig.",
        install=f'Way stress is only {2.3:.1f} psi, so the way is precision-limited, '
                f'not load-limited. Set the fit, not the tightness.',
        substitute="Acetal or cast nylon acceptable; both move more with humidity "
                   "than UHMW. PTFE is too soft for the gib.",
        basis="CALC-C16 way stress; D-032 gib",
        critical="fit",
    ))
    rows.append(_line(
        "MC-15",
        'Canvas or linen phenolic sheet, 1/2" — table wear face',
        '1 pc 16" x 22"',
        '1/2" canvas-base phenolic. This is DATUM-D, the metrology surface. '
        f'Flatness after bonding must be <= {m.table_flat_spec * 1000:.0f} mil over '
        f'the {m.capacity_width:g}" contact line.',
        'canvas phenolic sheet 1/2 inch thick',
        mates="P-006 wear face, P-004 skins",
        prep="Scuff the bond face; keep the show face clean of adhesive.",
        install="Bond to a FLATTENED torsion box. Check with a straightedge and "
                "feelers before it cures — Q-101.",
        substitute="3/8\" MIC-6 cast aluminum plate is a better metrology surface "
                   "and an acceptable substitute. Ordinary rolled plate is not: "
                   "it is not flat enough.",
        basis="TV-01 table flatness term",
        critical="fit",
    ))

    # ---------------- drive ----------------------------------------------
    rows.append(_line(
        "MC-16",
        f'V-belt sheave, {m.pulley_drum:g}" OD, {m.shaft_od:g}" bore — drum',
        "1 ea",
        f'{m.pulley_drum:g}" pitch dia, A/4L section, {m.shaft_od:g}" bore, keyed or '
        f'set-screw. With the {m.pulley_motor:g}" motor sheave this gives '
        f'{drum_rpm(m):.0f} rpm.',
        f'v-belt pulley {m.pulley_drum:g} inch {m.shaft_od:g} inch bore A section',
        mates="P-010 shaft, MC-18 belt",
        prep="None; do not drill the ground shaft.",
        install="Coplanar with the motor sheave — straightedge across both faces, "
                "QC-09.",
        substitute="Any A/4L sheave of the same pitch diameter and bore. Changing "
                   "diameter changes surface speed — recompute CALC-C12.",
        basis="CALC-C12",
        critical="fit",
    ))
    rows.append(_line(
        "MC-17",
        f'V-belt sheave, {m.pulley_motor:g}" OD — motor',
        "1 ea",
        f'{m.pulley_motor:g}" pitch dia, A/4L section, bore to match the motor shaft '
        f'(MEASURE it — 5/8" is common but not universal).',
        f'v-belt pulley {m.pulley_motor:g} inch A section 5/8 bore',
        mates="Motor shaft, MC-18 belt",
        prep="Measure the motor shaft before ordering. [M] required.",
        install="Set flush and coplanar; lock the set screw on the shaft flat.",
        substitute="Match pitch diameter and the measured motor bore.",
        basis="CALC-C12",
        critical="fit",
    ))
    rows.append(_line(
        "MC-18",
        'V-belt, A/4L section',
        "1 ea (size after the cradle is locked)",
        'A/4L section. Length is measured, not predicted: lock the motor cradle, '
        'then measure the centre distance and compute pitch length.',
        '4L v-belt',
        mates="MC-16, MC-17",
        prep="None.",
        install="Tension by cradle weight, then lock so the belt cannot pump.",
        substitute="Link belt is an acceptable and quieter substitute.",
        basis="M-102 belt length equation",
        critical="fit",
    ))

    # ---------------- hold-downs, guarding, dust -------------------------
    rows.append(_line(
        "MC-19",
        'Compression spring, ~3/4" OD — hold-down rollers',
        "4 ea",
        'Light compression spring, ~3/4" OD, free length ~2". Light is the '
        'requirement: a stiff spring bows thin stock and you sand a banana.',
        'compression spring 3/4 od 2 inch free length light',
        mates="P-014 yoke, H-009 roller",
        prep="Spring pockets bored in P-014.",
        install=f'Set rollers {m.roller_setbelow_ref * 1000:.0f} mil below drum OD, '
                f'paper on — QC-08.',
        substitute="Any spring that lets a 1/16\" board pass without visible bow.",
        basis="QC-08",
        critical="fit",
    ))
    rows.append(_line(
        "MC-20",
        'Shoulder screw, 5/16" — roller yoke pivots',
        "4 ea",
        '5/16" shoulder screw x 1-1/2". Shoulder gives a true pivot; a threaded '
        'bolt in a wood bearing wallows.',
        'shoulder screw 5/16 x 1-1/2',
        mates="P-014 yoke",
        prep="Ream the pivot for the shoulder, tap for the thread.",
        install="Snug, then back off 1/8 turn so the yoke swings free.",
        substitute="Ground dowel plus retaining collar.",
        basis="J-009",
        critical="fit",
    ))
    rows.append(_line(
        "MC-21",
        '4" dust hose, cuff and blast gate',
        "1 set",
        f'4" ID flex hose, one cuff, one blast gate. The collector must deliver '
        f'{dust["required_cfm"]:.0f} CFM AT THE MACHINE — hood face velocity '
        f'{dust["hood_face_fpm"]:.0f} fpm.',
        '4 inch dust collection hose blast gate cuff',
        mates="P-011 hood",
        prep='4" port let into the hood.',
        install="Shortest possible run, minimum elbows.",
        substitute="Any 4\" fitting. A shop vacuum will NOT meet the CFM "
                   "requirement and will clog — this is a capacity requirement, "
                   "not a connector preference.",
        basis="CALC-C15",
        critical="safety",
    ))
    rows.append(_line(
        "MC-22",
        'Structural epoxy adhesive for aluminum',
        "1 kit",
        'Two-part structural epoxy rated for metal-to-metal bonding, with a '
        'published open time long enough to seat the plugs.',
        'two part structural epoxy adhesive metal bonding',
        mates="P-020 shell, P-021 plugs",
        prep="Abrade and solvent-clean both bond faces. Bond area and cure per "
             "the maker's data sheet — read it, do not assume.",
        install="Cross-pin the joint as well: the pins carry torque, the epoxy "
                "seals and shares load. Never adhesive alone on a rotating part.",
        substitute="Any structural metal-bonding epoxy with published shear "
                   "strength and cure schedule. Do not use general-purpose "
                   "5-minute epoxy.",
        basis="J-106; user standard: never glue alone for primary structure",
        critical="safety",
    ))
    rows.append(_line(
        "MC-23",
        'Hook-and-loop PSA strip + abrasive rolls',
        "1 roll hook, 1 set 80/120/180/220",
        f'4" hook strip with pressure-sensitive adhesive; 3" loop-backed abrasive. '
        f'Abrasive thickness variation is 2 mil of the TV-01 budget — buy one '
        f'brand and stay with it.',
        'hook and loop sanding drum wrap abrasive roll 3 inch',
        mates="P-020 shell",
        prep="Degrease the shell OD before applying PSA.",
        install="Spiral wrap, no overlap, no gap. Re-clock ALN-01 after every "
                "grit change.",
        substitute="Any loop-backed abrasive of consistent thickness.",
        basis="TV-01 abrasive term",
        critical="consumable",
    ))
    rows.append(_line(
        "MC-24",
        'Hex bolts, nylock nuts and backing washers — frame through-bolts',
        '12 sets, 1/4-20 x 3 in',
        '1/4-20 hex bolt with a large-OD backing washer under both head and nut. '
        'Through-bolted frame is re-tightenable and knock-down.',
        '1/4-20 hex bolt 3 inch nylock nut fender washer',
        mates="P-001L/R, P-003 stretchers",
        prep="Clamp the joint, then drill through both parts so the holes cannot "
             "disagree.",
        install="Snug in an opposite-corner pattern, check diagonals, then final "
                "tighten. Re-check after the first hour of running — QC-13.",
        substitute="3/8\" bolts acceptable; screws alone are excluded by the user "
                   "joinery standard.",
        basis="D-038; joinery-and-tolerance-standards.md",
        critical="safety",
    ))
    rows.append(_line(
        "MC-25",
        'Adjustable handle / star knob, 3/8-16',
        "6 ea",
        '3/8-16 male adjustable handle or star knob. Way locks and yoke locks.',
        'adjustable handle 3/8-16 star knob',
        mates="P-014 yoke, way lock",
        prep="Tapped inserts or T-nuts.",
        install="Lock the ways BEFORE cutting — this removes the last of the "
                "lift compliance.",
        substitute="Any 3/8-16 knob with a comfortable grip.",
        basis="D-034",
        critical="fit",
    ))
    return rows


def procurement_summary() -> dict[str, Any]:
    rows = procurement()
    return {
        "lines": len(rows),
        "safety_critical": sum(1 for r in rows if r["criticality"] == "safety"),
        "unverified_part_numbers": sum(1 for r in rows if r["part_number"] == UNVERIFIED),
        "verification_note": (
            "McMaster part numbers are UNVERIFIED [A]. Automated verification was "
            "attempted twice on 2026-08-15 and blocked by the site's JavaScript "
            "requirement. Every line carries the controlling specification, a "
            "substitution rule, and a live McMaster search link instead."
        ),
    }


if __name__ == "__main__":
    rows = procurement()
    s = procurement_summary()
    print(f"WALTER DS-16 Rev C — McMaster procurement register: {s['lines']} lines "
          f"({s['safety_critical']} safety-critical)")
    print(f"part numbers unverified: {s['unverified_part_numbers']}/{s['lines']}\n")
    for r in rows:
        print(f"{r['item_id']}  {r['description']}")
        print(f"    qty   {r['qty']}")
        print(f"    spec  {r['controlling_spec'][:110]}")
        print(f"    basis {r['design_basis']}")
        print(f"    link  {r['link']}")
