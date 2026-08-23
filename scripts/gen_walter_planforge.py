#!/usr/bin/env python3
"""WOODWRIGHT PLANFORGE v1.0 guidebook for WALTER Rev C.

Generates sander/walter/planforge/{index.html, DESIGN_BASIS.md, ZERO_GAP.md,
README.md, CHANGELOG.md, CSVs} from walter_project (SSOT for IDs).

Run: python3 scripts/gen_walter_planforge.py
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "sander", "walter", "cad"))

from walter_kernel import REV, drum_rpm, feed_fpm, sfm  # noqa: E402
from walter_project import PROJECT, build_project  # noqa: E402

OUT = os.path.join(ROOT, "sander", "walter", "planforge")


def write(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote", os.path.relpath(path, ROOT))


def csv_write(path, rows, fields):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})
    print("wrote", os.path.relpath(path, ROOT))


def esc(s):
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def rows_html(rows, keys):
    th = "".join(f"<th>{esc(k)}</th>" for k in keys)
    body = []
    for r in rows:
        tds = []
        for k in keys:
            val = r.get(k, "")
            if k == "URL" and val:
                tds.append(
                    f'<td><a class="sku" href="{esc(val)}" rel="noopener" target="_blank">{esc(r.get("PN") or val)}</a></td>'
                )
            else:
                tds.append(f"<td>{esc(val)}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    return f"<table><thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def generate():
    proj = build_project()
    pf = PROJECT
    der = proj["derived"]

    design_basis = f"""# WALTER Design Basis — WOODWRIGHT PLANFORGE v1.0

**Release state:** {pf['RELEASE_STATE']}
**Risk class:** {pf['RISK_CLASS']}
**Project:** {pf['CODE']} · kernel {pf['MODEL_VERSION']} · Rev {REV}
**Units:** {pf['UNITS']}
**Layout:** {pf['LAYOUT']}

## Verdict
This is a shop-built 16-inch closed-frame drum thickness sander. A competent craftsperson can review, prototype, and — after the listed conditions — build it. It is **not** a PE stamp, not UL listed, not a ShopNotes #86 reprint, and not an unconditional FABRICATION-READY machine.

## Conditions (stop-work until closed)
"""
    for c in pf["CONDITIONS"]:
        design_basis += f"- {c}\n"
    design_basis += "\n## Risk triggers\n"
    for t in pf["RISK_TRIGGERS"]:
        design_basis += f"- {t}\n"
    design_basis += f"""
## Controlling geometry [G]/[D]
- envelope 22.00 × 36.00 × 20.00 in benchtop [G]
- capacity 16.00 in wide × 0.06–4.00 in thick [G]
- drum Ø 5.00 × 16.00 face after true [G/T]
- drum axis D2: Z 13.50, Y 18.00 [G]
- RPM = 1725 × 3.00 / 4.75 = {der['drum_rpm']} [D]
- SFM = π × 5.00 × rpm / 12 = {der['sfm']} [D]
- feed at 30 rpm roller = {der['feed_fpm']} FPM [D]
- crown 0.030 in barrel both rollers [G]
- Acme ¾-6 dual, HTD-timed, 4.50 in travel [G]

## Professional review
{pf['PROFESSIONAL_REVIEW']}

## Lineage (observation vs inference)
- Observed [G]: Ron Walters published a ShopNotes-derived drum sander on woodgears.ca and walked the same machine on YouTube W-5Sj6kBVic.
- Observed [G]: dedicated motor, flange bearings, Velcro wrap, dust hood worked; conveyor tracking, MDF drum cracks, Formica platen, gravity belt slack, shim-stock parallelism failed in public.
- Inference: redesign those failure modes. Do not redraw copyrighted magazine art.
"""
    write(os.path.join(OUT, "DESIGN_BASIS.md"), design_basis)

    calc = f"""# WALTER calculations — WOODWRIGHT PLANFORGE

Controlling units: inches. These identities are [D] arithmetic from `walter_kernel.py`.
They are not coupon tests and not a PE analysis.

## CAL-001 Drum speed
`drum_rpm = motor_rpm × pulley_mot / pulley_drm`
= 1725 × 3.00 / 4.75 = **{der['drum_rpm']} r/min**

## CAL-002 Surface speed
`sfm = π × drum_od × drum_rpm / 12`
= π × 5.00 × {der['drum_rpm']} / 12 = **{der['sfm']} ft/min**

## CAL-003 Feed (at 30 r/min roller)
`feed_fpm = π × roller_od / 12 × 30`
= π × 2.00 / 12 × 30 = **{der['feed_fpm']} ft/min**
PWM target band 0–16 FPM [G].

## CAL-004 Elevation
`pitch = 1 / acme_tpi = 1/6 = 0.1667 in/rev` on ¾-6 Acme.
Travel 4.50 in [G].

## CAL-005 Face gap
`(inner_w − drum_face) / 2 = (16.50 − 16.00) / 2 = 0.25 in` each side.

## Limitations
Do not treat these as allowable loads, heat-build, or tracking guarantees.
Q02 / Q04 / Q09 are the shop tests. Electrical FLA is [P] from the nameplate.
"""
    write(os.path.join(OUT, "CALCULATIONS.md"), calc)

    csv_write(
        os.path.join(OUT, "SHEET_INDEX.csv"),
        proj["sheets"],
        ["ID", "FILE", "STATUS", "PURPOSE"],
    )

    zg = f"""# Zero-Gap Verification Checklist — WALTER Rev {REV}

Protocol: WOODWRIGHT PLANFORGE v1.0. Fail any item → do not claim an unconditional fabrication release.

| Item | Result | Evidence |
|---|---|---|
| All fabricated parts in part register with finished sizes | PASS | `walter_project.parts()` F/ST/D/T/C/M/HD/N |
| Quantities match geometry (21 discs, 2 walls, 2 Acme) | PASS | kernel `P.n_discs` + BOM |
| Consumable fasteners specified or kit alternative | PASS | hardware schedule H-001…; kit line for #8/¼-20 |
| Every critical joint has a detail sheet | PASS | J-201 drum, J-202 ways/Acme, J-203 crown, J-204 wrap |
| Geometry, cut sequence, acceptance on joints | PASS | J sheets + `JOINERY_SCHEDULE.csv` + Q01–Q10 |
| Layout system declared and consistent | PASS | D1–D4 on G-001 / G-002 |
| Wood movement at drum stack | PASS | 0.5 mm gaps every 4 discs; birch not MDF |
| Load path / energy described | PASS WITH CONDITION | R3 abrasive drum; no NDS member design; machinery review [P] |
| Assumptions and limitations on cover | PASS | G-001 banner; not PE; not UL |
| Hardware exact make/model or search term | PASS WITH CONDITION | 6245K47 / 6191K37 [S]; other PNs [E] verify live |
| Electrical one-line | PASS WITH CONDITION | W-12 design intent; electrician [P] |
| Guards, nips, dust, E-stop, no auto-restart | PASS WITH CONDITION | M-101 / Q06 / Q08; first-run [T] |
| Numerical tolerances for critical fits | PASS | bore 0.748 +0/−0.002; OD 5.000±0.010; crown 0.030±0.005 |
| Inspection methods and acceptance | PASS | Q-101 + `fab/12_QA/inspection.csv` |
| Irreversible hold points identified | PASS | no glue in keyway; no paint on ways; no sanding-belt conveyor |
| Assembly sequence present | PASS | LEGO `/manual/` 22 steps + bags 1–6 |
| Solo-handling rules | PASS | disc stack and walls are solo; 1 HP motor is a two-hand lift ~30–40 lb |
| Stock prep / grain / finish rules | PASS | F-101 nest; crossed-grain walls; oil ways |
| 1:1 templates with two calibration bars | PASS WITH CONDITION | T-DISC / T-PLATE — builder must verify print scale |
| Self-containment: skilled builder + this package + listed materials | PASS WITH CONDITION | Close electrician, first-run, live catalog, true the drum |

**Release recommendation:** FABRICATION-READY WITH CONDITIONS. Do not mark FABRICATION-READY (unconditional). Do not mark PE-approved or UL-listed.
"""
    write(os.path.join(OUT, "ZERO_GAP.md"), zg)

    csv_write(
        os.path.join(OUT, "MCMASTER_SCHEDULE.csv"),
        proj["hardware"],
        ["LINE", "HARDWARE_ID", "ROLE", "PN", "URL", "DESCRIPTION", "QTY", "UNIT", "WHERE", "FAMILY", "EVIDENCE", "SUBSTITUTE", "NOTE"],
    )
    csv_write(
        os.path.join(OUT, "REQUIREMENTS.csv"),
        proj["requirements"],
        ["ID", "PRI", "STATEMENT", "VERIFY", "STATUS", "EVIDENCE"],
    )
    csv_write(
        os.path.join(OUT, "DIMENSION_REGISTER.csv"),
        proj["dimensions"],
        ["DIM_ID", "NOMINAL", "TOL", "UNIT", "DATUM", "FEATURE", "CLASS", "EQ", "SHEET", "INSPECT"],
    )
    csv_write(
        os.path.join(OUT, "JOINERY_SCHEDULE.csv"),
        proj["joinery"],
        ["JOINT_ID", "TYPE", "PART_A", "PART_B", "FUNCTION", "GEOMETRY", "FIT", "ADHESIVE", "DRAWING", "INSPECTION"],
    )
    csv_write(
        os.path.join(OUT, "PART_REGISTER.csv"),
        proj["parts"],
        ["PART_ID", "QTY", "DESC", "MAT", "FINISHED", "GRAIN", "BAG", "GROUP", "MAKE"],
    )

    fmea_rows = [
        dict(ID=f["id"], MODE=f["item"], CAUSE=f["cause"], EFFECT=f["effect"], SEV=f["sev"], DET=f["det"], MIT=f["prev"])
        for f in proj["fmea"]
    ]
    csv_write(
        os.path.join(OUT, "FMEA.csv"),
        fmea_rows,
        ["ID", "MODE", "CAUSE", "EFFECT", "SEV", "DET", "MIT"],
    )

    req_html = rows_html(proj["requirements"], ["ID", "PRI", "STATEMENT", "VERIFY", "STATUS", "EVIDENCE"])
    ev_html = rows_html(proj["evidence"], ["ID", "DESC", "CLASS", "RELIABILITY", "VERIFY"])
    fmea_html = rows_html(fmea_rows, ["ID", "MODE", "CAUSE", "EFFECT", "SEV", "DET", "MIT"])
    joint_html = rows_html(
        proj["joinery"],
        ["JOINT_ID", "TYPE", "PART_A", "PART_B", "FUNCTION", "FIT", "DRAWING"],
    )
    dim_html = rows_html(
        proj["dimensions"],
        ["DIM_ID", "NOMINAL", "TOL", "UNIT", "DATUM", "FEATURE", "CLASS", "SHEET"],
    )
    part_html = rows_html(
        proj["parts"],
        ["PART_ID", "QTY", "DESC", "MAT", "FINISHED", "GRAIN", "BAG", "MAKE"],
    )

    mc_rows = []
    for r in proj["hardware"]:
        cls = "src" if r["EVIDENCE"] == "S" else "est"
        pn_cell = (
            f"<a class='sku' href='{esc(r['URL'])}' rel='noopener' target='_blank'>{esc(r['PN'])}</a>"
            if r["URL"]
            else esc(r["PN"])
        )
        mc_rows.append(
            "<tr class='%s'><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
            % (
                cls,
                esc(r["LINE"]),
                esc(r["HARDWARE_ID"]),
                esc(r["EVIDENCE"]),
                pn_cell,
                esc(r["DESCRIPTION"]),
                esc(r["QTY"]),
                esc(r["WHERE"]),
                esc(r["NOTE"][:80]),
            )
        )

    cond = "<ul>" + "".join(f"<li>{esc(c)}</li>" for c in pf["CONDITIONS"]) + "</ul>"
    trig = "<ul>" + "".join(f"<li>{esc(t)}</li>" for t in pf["RISK_TRIGGERS"]) + "</ul>"
    dats = "<ul>" + "".join(f"<li>{esc(d)}</li>" for d in pf["DATUMS"]) + "</ul>"
    bags = "".join(
        f"<div class='card'><p class='k'>BAG {b['id']}</p><p><b>{esc(b['name'])}</b></p><p>{esc(b['blurb'])}</p></div>"
        for b in proj["bags"]
    )
    seq = "<ol class='seq'>" + "".join(
        f"<li><b>Step {st['n']:02d}</b> <i>Bag {st['bag']}</i> — {esc(st['title'])}</li>"
        for st in proj["steps"]
    ) + "</ol>"

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>WALTER · WOODWRIGHT PLANFORGE v1.0 · Master Build Guide</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Newsreader:opsz,wght@6..72,500;6..72,600&display=swap" rel="stylesheet"/>
<style>
:root{{--ink:#1c1914;--paper:#f4efe6;--copper:#b4532a;--copper-hi:#d47248;--dim:#6b5340;--line:#d4cbb8;--warn:#8a3a2a;--banner:#3a1814}}
*{{box-sizing:border-box}}
html,body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 Newsreader,Georgia,serif}}
code,.mono,table,nav,th,td,.k{{font-family:"IBM Plex Mono",Menlo,monospace}}
a{{color:var(--copper)}}
.banner{{background:var(--banner);color:#f3e6dc;padding:10px 22px;font:600 12px/1.4 "IBM Plex Mono",monospace;letter-spacing:.04em}}
.banner b{{color:#e8c4a8}}
header.hero{{padding:36px 28px 12px;max-width:1100px}}
.k{{font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:var(--copper);font-weight:600}}
h1{{font-size:clamp(36px,6vw,64px);margin:8px 0 6px;font-weight:600}}
.lead{{max-width:70ch;color:var(--dim);font-size:18px}}
nav.toc{{position:sticky;top:0;z-index:5;background:rgba(244,239,230,.94);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);padding:10px 20px;display:flex;gap:10px;flex-wrap:wrap}}
nav.toc a{{font-size:11px;letter-spacing:.08em;text-transform:uppercase;text-decoration:none;color:var(--dim);border:1px solid var(--line);padding:6px 8px}}
nav.toc a:hover{{color:var(--ink);border-color:var(--ink)}}
main{{max-width:1100px;padding:12px 28px 80px}}
section{{padding:28px 0;border-top:1px solid var(--line)}}
h2{{font-size:28px;margin:0 0 12px}}
h3{{font-size:18px;margin:18px 0 8px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;margin:16px 0}}
.card{{border:1px solid var(--line);padding:14px;background:#fff}}
.card .k{{margin-bottom:6px}}
table{{border-collapse:collapse;width:100%;font-size:12px;margin:12px 0}}
th,td{{border-bottom:1px solid var(--line);padding:7px 6px;text-align:left;vertical-align:top}}
th{{color:var(--copper);font-weight:600;letter-spacing:.06em;font-size:10px;text-transform:uppercase}}
tr.est td{{color:var(--dim)}}
tr.src td{{background:#f7efe6}}
a.sku{{font-weight:600;letter-spacing:.04em}}
.elev{{width:100%;border:1px solid var(--line);background:#fff}}
.seq{{padding-left:22px}}
.seq i{{color:var(--dim);font-style:normal;font-size:12px}}
.warn{{color:var(--warn);font-weight:600}}
.links{{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}}
.links a{{display:inline-block;padding:8px 12px;border:1px solid var(--copper);text-decoration:none;font:600 11px/1 "IBM Plex Mono",monospace;letter-spacing:.08em;text-transform:uppercase}}
ul{{padding-left:20px}}
footer{{padding:24px 28px;color:var(--dim);font-size:13px;border-top:1px solid var(--line)}}
@media print{{nav.toc,.banner{{position:static}} a.sku{{color:#000}}}}
</style>
</head>
<body>
<div class="banner">
  RELEASE: <b>{esc(pf['RELEASE_STATE'])}</b>
  · RISK <b>{esc(pf['RISK_CLASS'])}</b>
  · NOT A PE STAMP · NOT UL · NOT A SHOPNOTES REPRINT
  · ELECTRICIAN [P] · FIRST-RUN [T]
  · {esc(pf['CODE'])}
</div>
<header class="hero">
  <p class="k">WOODWRIGHT PLANFORGE v1.0 · Kernel {esc(pf['MODEL_VERSION'])} · Rev {esc(REV)}</p>
  <h1>WALTER</h1>
  <p class="lead">Master build-plans guidebook for a 16-inch closed-frame drum thickness sander. Traditional joinery discipline joined to parametric CAD, LEGO assembly, and honest release boundaries. If a competent builder still has to guess, the plan is not finished.</p>
  <div class="links">
    <a href="../manual/">LEGO build manual</a>
    <a href="../fab/06_DRAWINGS/">G/A/E/P/J drawings</a>
    <a href="../fab/">Fab CSVs</a>
    <a href="../app/">Build app</a>
    <a href="../plans/W1_general.svg">W-1 shop blueprint</a>
    <a href="MCMASTER_SCHEDULE.csv">McMaster CSV</a>
    <a href="DESIGN_BASIS.md">Design basis</a>
    <a href="ZERO_GAP.md">Zero-gap</a>
  </div>
</header>
<nav class="toc" aria-label="Sheet families">
  <a href="#g001">G-001 Cover</a>
  <a href="#g002">G-002 Requirements</a>
  <a href="#g003">G-003 Evidence</a>
  <a href="#g004">G-004 Safety</a>
  <a href="#a101">A Architecture</a>
  <a href="#j101">J Joinery</a>
  <a href="#e101">E Assembly</a>
  <a href="#p101">P Parts</a>
  <a href="#m101">M Mechanism</a>
  <a href="#f101">F Fabrication</a>
  <a href="#h101">H McMaster</a>
  <a href="#q101">Q Quality</a>
</nav>
<main>

<section id="g001">
  <p class="k">G-001 · Governance / cover</p>
  <h2>Release, datums, thesis</h2>
  <div class="grid">
    <div class="card"><p class="k">Release</p><p>{esc(pf['RELEASE_STATE'])}</p></div>
    <div class="card"><p class="k">Risk</p><p>{esc(pf['RISK_CLASS'])} powered abrasive machine</p></div>
    <div class="card"><p class="k">Layout</p><p>{esc(pf['LAYOUT'])}</p></div>
    <div class="card"><p class="k">Units</p><p>{esc(pf['UNITS'])}</p></div>
  </div>
  <h3>Design thesis</h3>
  <p>Keep what Walters got right: a dedicated motor, flange bearings, a wrap drum, a hood that actually collects. Throw out what failed in public: a sanding belt used as a conveyor, PVC-pipe rollers, MDF discs, Formica platen, gravity belt slack, shim-stock parallelism, a light switch for 115 V. This package is original engineering from those notes — not a copy of copyrighted ShopNotes art.</p>
  <h3>Conditions — close these before a first board</h3>
  {cond}
  <p class="warn">Do not treat a rendering, this HTML book, or the Build-app viz as a scaled fabrication drawing. Controlling numbers live in <code>walter_kernel.py</code>, the dimension register, and the P-sheets. Do not scale A-101.</p>
  <h3>Datums</h3>
  {dats}
</section>

<section id="g002">
  <p class="k">G-002 · Requirements traceability</p>
  <h2>MUST / SHOULD / EXCLUDED</h2>
  {req_html}
  <p>Vague adjectives are not specs. “Strong” maps to dual Acme + closed birch frame + 1 HP, not a number pulled from a photograph. “Accurate” maps to Q02 Ø 5.000±0.010 and Q03 16″ feeler both ends.</p>
</section>

<section id="g003">
  <p class="k">G-003 · Evidence / dimensions / revision</p>
  <h2>What is known vs assumed</h2>
  <p>Evidence classes: <b>G</b> given · <b>M</b> measured · <b>S</b> sourced · <b>D</b> derived · <b>A</b> assumed · <b>E</b> estimated · <b>T</b> test · <b>P</b> professional-verify.</p>
  {ev_html}
  <h3>Dimension register</h3>
  {dim_html}
  <p>Critical speeds [D]: drum {der['drum_rpm']} RPM · {der['sfm']} SFM · feed {der['feed_fpm']} FPM at 30 rpm roller. Recalculate from nameplates if your pulleys differ.</p>
</section>

<section id="g004">
  <p class="k">G-004 · Safety / FMEA / professional review</p>
  <h2>Hazards in proportion to R3</h2>
  <p>{esc(pf['PROFESSIONAL_REVIEW'])}</p>
  <h3>Risk triggers</h3>
  {trig}
  <p class="warn">PPE and a warning label are last layers. Point of operation, ingoing nips, belt pinch, dust, and unexpected restart are designed in M-101 / W-7 / W-12 and verified on Q-101. This package does not certify OSHA 1910.212 / 1910.213 compliance.</p>
  {fmea_html}
</section>

<section id="a101">
  <p class="k">A-101 / A-102 / A-103 · Architecture</p>
  <h2>General arrangement</h2>
  <p>22 × 36 × 20″ benchtop · 16″ face · Ø 5.00 drum · D2 at Z 13.50 / Y 18.00. Print A-102 at 100% on A3; do not scale the isometric.</p>
  <img class="elev" src="../fab/06_DRAWINGS/A-102_ortho.svg" alt="A-102 orthographic general arrangement"/>
  <div class="links">
    <a href="../fab/06_DRAWINGS/G-001_cover.svg">G-001</a>
    <a href="../fab/06_DRAWINGS/A-101_isometric.svg">A-101 iso</a>
    <a href="../fab/06_DRAWINGS/A-102_ortho.svg">A-102 ortho</a>
    <a href="../fab/06_DRAWINGS/A-103_section.svg">A-103 section</a>
    <a href="../fab/06_DRAWINGS/A-104_envelope.svg">A-104 envelope</a>
    <a href="../fab/06_DRAWINGS/E-101_exploded.svg">E-101 explode</a>
    <a href="../fab/06_DRAWINGS/E-102_sequence.svg">E-102 bags</a>
    <a href="../plans/W1_general.svg">W-1 shop sheet</a>
    <a href="../cad/exports/walter_assembly.stl">assembly.stl</a>
  </div>
</section>

<section id="j101">
  <p class="k">J-101 · Joinery map</p>
  <h2>Joints that carry load, movement, or tracking</h2>
  <p>Primary layout is D1/D2. Transfer the drum axis with one story stick onto both plates. Never glue the keyway. Never paint the ways. Never clock Acme nuts independently after the HTD belt is on.</p>
  {joint_html}
  <div class="links">
    <a href="../fab/06_DRAWINGS/J-201_drum.svg">J-201 Drum stack</a>
    <a href="../fab/06_DRAWINGS/J-202_ways.svg">J-202 Ways + Acme</a>
    <a href="../fab/06_DRAWINGS/J-203_crown.svg">J-203 Crown</a>
    <a href="../fab/06_DRAWINGS/J-204_wrap.svg">J-204 Wrap</a>
    <a href="../fab/10_TEMPLATES/T-DISC.svg">T-DISC 1:1</a>
    <a href="../fab/10_TEMPLATES/T-PLATE.svg">T-PLATE 1:1</a>
    <a href="JOINERY_SCHEDULE.csv">Joinery CSV</a>
  </div>
</section>

<section id="e101">
  <p class="k">E-101 · Exploded assembly (LEGO)</p>
  <h2>Twenty-two steps, six bags</h2>
  <p>The step-by-step manual is generated from the same part register. Orange arrows are this-step motion. Numbered balloons on E-101 match the BOM.</p>
  <div class="grid">{bags}</div>
  <div class="links">
    <a href="../manual/">Open LEGO manual</a>
    <a href="../fab/06_DRAWINGS/E-101_exploded.svg">E-101</a>
    <a href="../app/#assembly">App checklist</a>
  </div>
  {seq}
  <p><b>Solo handling:</b> mill discs and walls alone. The 1 HP 56C motor is a two-hand lift; set the hinge plate first. Do not ask one person to true an unguarded drum at speed — use a carrier and the hood.</p>
  <p><b>Irreversible hold points:</b> (1) no glue in the keyway; (2) no paint on UHMW ways; (3) do not substitute a sanding belt for the conveyor; (4) do not energize 115 V before the electrician; (5) do not skip Q06.</p>
</section>

<section id="p101">
  <p class="k">P-201 … P-211 · Part drawings</p>
  <h2>Part register</h2>
  {part_html}
  <div class="links">
    <a href="../fab/06_DRAWINGS/P-201_disc.svg">P-201 Disc</a>
    <a href="../fab/06_DRAWINGS/P-202_wall.svg">P-202 Walls</a>
    <a href="../fab/06_DRAWINGS/P-203_plate.svg">P-203 Plates</a>
    <a href="../fab/06_DRAWINGS/P-204_platen.svg">P-204 Platen</a>
    <a href="../fab/06_DRAWINGS/P-205_frame.svg">P-205 Frame</a>
    <a href="../fab/06_DRAWINGS/P-206_shaft.svg">P-206 Shaft</a>
    <a href="../fab/06_DRAWINGS/P-207_hinge.svg">P-207 Hinge</a>
    <a href="../fab/06_DRAWINGS/P-208_rollers.svg">P-208 Rollers</a>
    <a href="../fab/06_DRAWINGS/P-209_hood_guard.svg">P-209 Hood/guard</a>
    <a href="../fab/06_DRAWINGS/P-210_stand.svg">P-210 Stand</a>
    <a href="../fab/06_DRAWINGS/P-211_ways.svg">P-211 Ways</a>
    <a href="PART_REGISTER.csv">Part CSV</a>
    <a href="SHEET_INDEX.csv">Sheet index</a>
  </div>
</section>

<section id="m101">
  <p class="k">M-101 / M-102 · Mechanism</p>
  <h2>Drive, feed, guards</h2>
  <p>Drum {der['drum_rpm']:.0f} RPM / {der['sfm']:.0f} SFM from 3.00/4.75 on 1725. Feed {der['feed_fpm']:.1f} FPM at 30 rpm roller, PWM 0–16 FPM. Hinge + turnbuckle, not motor weight on a dowel. Full belt guard. 24 V feed isolated from 115 V drum.</p>
  <div class="links">
    <a href="../fab/06_DRAWINGS/M-101_drive.svg">M-101 Drive</a>
    <a href="../fab/06_DRAWINGS/M-102_conveyor.svg">M-102 Conveyor</a>
    <a href="../fab/06_DRAWINGS/M-105_electrics.svg">M-105 Electrics [P]</a>
    <a href="../plans/W12_wiring.svg">W-12 Wiring intent</a>
  </div>
  <p class="warn">W-12 is not a permit drawing and not NEC. Magnetic starter / no-volt release is mandatory. A consumer light switch is not an E-stop.</p>
</section>

<section id="f101">
  <p class="k">F-101 / F-102 · Fabrication</p>
  <h2>Stock, nest, routing</h2>
  <p>Three ¾″ Baltic birch 5×5 sheets, one ¼″ sheet, maple for rails/ways/nuts. Do not substitute MDF. Grain-cross the wall skins. Leave a spare disc if the sheet allows.</p>
  <div class="links">
    <a href="../fab/06_DRAWINGS/F-101_nest.svg">F-101 Nest</a>
    <a href="../fab/06_DRAWINGS/F-102_routing.svg">F-102 Routing</a>
    <a href="../fab/07_BOM/master_bom.csv">Master BOM</a>
    <a href="../fab/08_CUT_LISTS/finished.csv">Cut list</a>
    <a href="../fab/08_CUT_LISTS/operations.csv">Operations routing</a>
    <a href="../plans/W8_bom.svg">W-8</a>
    <a href="../plans/W14_buylist.svg">W-14</a>
  </div>
  <h3>Finish</h3>
  <ul>
    <li>Oil or wipe-on poly on the box after glue-up. Mask dados and way faces.</li>
    <li>Never finish the UHMW. Oil the ways.</li>
    <li>End-grain sealer on wall tops. Hood interior can stay raw.</li>
    <li>Sample-board the finish on scrap birch; do not experiment on F-002.</li>
  </ul>
</section>

<section id="h101">
  <p class="k">H-101 · McMaster-Carr and buy list</p>
  <h2>Linkable products — verify live before you order</h2>
  <p>Highlighted rows are [S] from public ShopNotes hardware notes (6245K47, 6191K37) and still need a live-page check. Grey rows are [E] search hints. Catalogs move. Measure the part in hand against the interface, not the SKU string.</p>
  <table>
    <thead><tr><th>Line</th><th>ID</th><th>Ev</th><th>PN</th><th>Description</th><th>Qty</th><th>Search</th><th>Note</th></tr></thead>
    <tbody>{''.join(mc_rows)}</tbody>
  </table>
  <p>Download: <a href="MCMASTER_SCHEDULE.csv">MCMASTER_SCHEDULE.csv</a> · shop sheet <a href="../plans/W14_buylist.svg">W-14</a></p>
</section>

<section id="q101">
  <p class="k">Q-101 · Inspection, commissioning, zero-gap</p>
  <h2>Hold points</h2>
  <ul>
    <li>Q02 — drum OD 5.000 ±0.010 after turning.</li>
    <li>Q04 — conveyor tracks empty 60 s, then loaded.</li>
    <li>Q05 — Acme witness marks aligned (D4).</li>
    <li>Q06 — E-stop; restore power; drum must not auto-restart.</li>
    <li>Q09 — first 0.010″ poplar, then oak. If the motor note changes, you took too much.</li>
  </ul>
  <div class="links">
    <a href="../fab/06_DRAWINGS/Q-101_inspect.svg">Q-101</a>
    <a href="../fab/12_QA/inspection.csv">Inspection CSV</a>
    <a href="ZERO_GAP.md">Zero-gap checklist (filled)</a>
    <a href="FMEA.csv">FMEA CSV</a>
  </div>
  <h3>Zero-gap result</h3>
  <p>Parts, joints, datums, LEGO sequence, and movement gaps <b>PASS</b>. Electrical, live catalog numbers, first-run, and machinery-guard review are <b>PASS WITH CONDITION</b>. Unconditional FABRICATION-READY is withheld.</p>
  <h3>Builder’s next action</h3>
  <ol>
    <li>Print T-DISC and T-PLATE at 100%. Measure both calibration bars. If either axis is wrong, stop and reprint — do not scale a photograph of a disc.</li>
    <li>Order plywood and the [S] belt/pulley pair after opening the live McMaster pages. Treat every other PN as a search term.</li>
    <li>Walk the LEGO manual bag by bag. True the drum before you trust a board. Call the electrician before you land 115 V.</li>
    <li>Commission with the collector on, hood on, no workpiece, then poplar 0.010″.</li>
  </ol>
</section>
</main>
<footer>
  WALTER · WOODWRIGHT PLANFORGE v1.0 · {esc(pf['CODE'])} · kernel {esc(pf['MODEL_VERSION'])} · Rev {esc(REV)} ·
  generated from walter_kernel.py + walter_project.py · not a ShopNotes reprint
</footer>
</body>
</html>
"""
    write(os.path.join(OUT, "index.html"), html)

    readme = f"""# WALTER WOODWRIGHT PLANFORGE v1.0

Release: **{pf['RELEASE_STATE']}** · Risk **{pf['RISK_CLASS']}** · Kernel {pf['MODEL_VERSION']} · Rev {REV}

- [Guidebook](index.html) — G/A/J/E/P/M/F/H/Q
- [Design basis](DESIGN_BASIS.md)
- [Zero-gap checklist](ZERO_GAP.md)
- [Calculations](CALCULATIONS.md)
- [Sheet index](SHEET_INDEX.csv)
- [McMaster-Carr schedule](MCMASTER_SCHEDULE.csv)
- [Requirements](REQUIREMENTS.csv)
- [Dimension register](DIMENSION_REGISTER.csv)
- [Joinery schedule](JOINERY_SCHEDULE.csv)
- [Part register](PART_REGISTER.csv)
- LEGO assembly: `/sander/walter/manual/`
- Planforge drawings: `/sander/walter/fab/06_DRAWINGS/`
- Shop blueprints W-1…W-14: `/sander/walter/plans/`
- CAD: `/sander/walter/cad/`

Print the guidebook from the browser at 100%. Controlling geometry is in `walter_kernel.py`, not in a screenshot.
"""
    write(os.path.join(OUT, "README.md"), readme)

    changelog = f"""# CHANGELOG — WALTER Planforge

## 1.2.1 / Rev {REV} — 2026-08-23

- G-003/G-004, A-104, E-102, M-105, P-205…P-211, F-102 added; N/A sheets recorded on G-001.
- App assembly checklist synced to 22 LEGO steps from `walter_project.steps()`.
- `verify_walter.py` reconciles parts, sheets, banners, BOM, and derived speeds.
- CALCULATIONS.md + SHEET_INDEX.csv.

## 1.2.0 / Rev {REV} — 2026-08-23

- WOODWRIGHT PLANFORGE v1.0 guidebook (this folder).
- LEGO-style 22-step A3 build manual (`/manual/`), six bags.
- Drawing family G/A/E/P/J/M/F/Q in `fab/06_DRAWINGS/`.
- Part / joinery / dimension / McMaster registers in `walter_project.py`.
- Release remains **FABRICATION-READY WITH CONDITIONS** (R3). Not PE, not UL, not a ShopNotes reprint.

## 1.1.0 / Rev B — 2026-08-22

- Kernel CAD, fourteen W-sheets, fab CSVs, PWA build app, report.

## 1.0.0 / Rev A — 2026-08-22

- Initial WALTER package.
"""
    write(os.path.join(OUT, "CHANGELOG.md"), changelog)

    sync_app_assembly(proj)


def sync_app_assembly(proj):
    """Keep the PWA checklist identical to LEGO steps()."""
    path = os.path.join(ROOT, "sander", "walter", "app", "data.js")
    text = open(path, encoding="utf-8").read()
    phase = {1: "drum", 2: "frame", 3: "table", 4: "conveyor", 5: "drive", 6: "tune"}
    lines = ["  assembly: ["]
    for st in proj["steps"]:
        lines.append(
            "    { id: %s, phase: %s, title: %s, body: %s },"
            % (
                json.dumps(f"s{st['n']:02d}"),
                json.dumps(phase[st["bag"]]),
                json.dumps(st["title"], ensure_ascii=False),
                json.dumps(st["note"], ensure_ascii=False),
            )
        )
    lines.append("  ],")
    block = "\n".join(lines)
    new, n = re.subn(r"  assembly: \[.*?\n  \],", lambda _m: block, text, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"app assembly sync failed (replacements={n})")
    # gallery: ensure new drawings are listed
    extra = [
        '    { src: "../fab/06_DRAWINGS/G-004_safety.svg", title: "G-004 Safety", kind: "plan" },',
        '    { src: "../fab/06_DRAWINGS/A-104_envelope.svg", title: "A-104 Envelope", kind: "plan" },',
        '    { src: "../fab/06_DRAWINGS/M-105_electrics.svg", title: "M-105 Electrics [P]", kind: "plan" },',
        '    { src: "../fab/06_DRAWINGS/P-205_frame.svg", title: "P-205 Frame parts", kind: "plan" },',
        '    { src: "../fab/06_DRAWINGS/E-102_sequence.svg", title: "E-102 Bags", kind: "plan" },',
    ]
    if "G-004_safety.svg" not in new:
        new = new.replace(
            '    { src: "../fab/06_DRAWINGS/G-001_cover.svg", title: "G-001 Cover", kind: "plan" },',
            '    { src: "../fab/06_DRAWINGS/G-001_cover.svg", title: "G-001 Cover", kind: "plan" },\n'
            + "\n".join(extra),
        )
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    print("synced", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    generate()
