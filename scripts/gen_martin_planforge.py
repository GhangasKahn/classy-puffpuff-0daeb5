#!/usr/bin/env python3
"""WOODWRIGHT PLANFORGE v1.0 guidebook for MARTIN Rev F.

Generates the master build-plans book from martin_kernel (SSOT):
  fence/martin/planforge/index.html
  DESIGN_BASIS.md, ZERO_GAP.md, MCMASTER_SCHEDULE.csv, REQUIREMENTS.csv

Run: python3 scripts/gen_martin_planforge.py
"""

from __future__ import annotations

import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "fence", "martin"))

from martin_kernel import PROJECT, build_project, v  # noqa: E402

OUT = os.path.join(ROOT, "fence", "martin", "planforge")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote", os.path.relpath(path, ROOT))


def csv_write(path, rows, fields):
    os.makedirs(os.path.dirname(path), exist_ok=True)
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


def rows_html(rows, keys, link_key=None):
    th = "".join(f"<th>{esc(k)}</th>" for k in keys)
    body = []
    for r in rows:
        tds = []
        for k in keys:
            val = r.get(k, "")
            if k == link_key and val:
                tds.append(f'<td><a href="{esc(val)}" rel="noopener" target="_blank">{esc(val)}</a></td>')
            elif k == "URL" and val:
                tds.append(
                    f'<td><a class="sku" href="{esc(val)}" rel="noopener" target="_blank">{esc(r.get("PN") or val)}</a></td>'
                )
            else:
                tds.append(f"<td>{esc(val)}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    return f"<table><thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def md_table(rows, keys):
    head = "| " + " | ".join(keys) + " |"
    sep = "| " + " | ".join("---" for _ in keys) + " |"
    lines = [head, sep]
    for r in rows:
        lines.append("| " + " | ".join(str(r.get(k, "")).replace("|", "/") for k in keys) + " |")
    return "\n".join(lines)


def generate():
    proj = build_project()
    ly = proj["layout"]
    pf = proj["planforge"]
    nest = proj["nest"]
    bal = proj["ballast"]
    posts = ", ".join(f"{p['mark']}@{p['cx']}\"" for p in ly["posts"])

    # ---- markdown companions ------------------------------------------------
    design_basis = f"""# MARTIN Design Basis — WOODWRIGHT PLANFORGE v1.0

**Release state:** {pf['RELEASE_STATE']}
**Risk class:** {pf['RISK_CLASS']}
**Project:** {pf['PROJECT_CODE']} · kernel {PROJECT['MODEL_VERSION']} · Rev {PROJECT['REVISION']}
**Units:** inch controlling. Native CAD export is millimetre.
**Layout system:** {pf['LAYOUT_SYSTEM']}

## Verdict
This is a sit-on-grade Darwin Martin Tree of Life light-screen across a Buffalo driveway. It is a planning fabrication package a competent craftsperson can review, prototype, and — after the listed conditions — build. It is **not** a PE stamp, not a licensed Wright reproduction, and not a Home Depot ranch fence.

## Conditions (stop-work until closed)
"""
    for c in pf["CONDITIONS"]:
        design_basis += f"- {c}\n"
    design_basis += "\n## Risk triggers\n"
    for t in pf["RISK_TRIGGERS"]:
        design_basis += f"- {t}\n"
    design_basis += f"""
## Controlling geometry [G]/[D]
- overall_length = {ly['overall_length']}\" [G/TBM]
- overall_height = {ly['overall_height']}\" [G]
- gate_clear = {ly['gate_clear']}\" [A]
- bay_clear = {ly['bay_clear']}\" [D] `(L - 4·post_x - gate_clear)/2`
- nuki_len = {ly['nuki_len']}\" [D]
- post_blank_l = {ly['post_blank_l']}\" [D]
- cassette φ pair = {ly['light_minor']} / {ly['light_major']}\" [D]
- post CLs: {posts}

## Ballast (planning, not PE)
Provided {bal['provided_lb']} lb vs required {bal['required_lb']} lb (FS {bal['fs']}). Ratio {bal['ratio']}. Concrete 0. Gravel pad 0.

## Professional review
{pf['PROFESSIONAL_REVIEW']}
"""
    write(os.path.join(OUT, "DESIGN_BASIS.md"), design_basis)

    zg = """# Zero-Gap Verification Checklist — MARTIN Rev F.1

Protocol: WOODWRIGHT PLANFORGE v1.0. Fail any item → do not claim an unconditional fabrication release.

| Item | Result | Evidence |
|---|---|---|
| All primary structural members in part register with finished sizes | PASS | `fab/07_BOM/bom.csv` L/F/K/R/C |
| Secondary parts (cassettes, muntins, caps, pins, lights, pads) listed | PASS | Q-001..003, T-001, W-001..003, H-001, H-006 |
| Quantities match geometry | PASS | kernel `parts()` + nest |
| Consumable fasteners specified or custom alternative | PASS | No structural screws. Oak pegs 96825K75. Optional hasp 1304A42. |
| Every critical joint has a detail sheet | PASS | J-401 nuki/kusabi, J-402 foot tenon, J-403 kama-tsugi, J-404 hozo/pivot |
| Geometry, cut sequence, acceptance, water/movement on joints | PASS | J sheets + `09_JOINERY/joints.csv` + QC-08..17 |
| Layout system declared and consistent | PASS | Face/edge: x=0 latch face, z=0 sill top; post CLs derived |
| Japanese / hand-tool sequences specified | PASS | nuki/kusabi, hozo drawbore, kama-tsugi; Bridge City / Zenwu / Japanese saws |
| 3D-print prototype recommendation | PASS WITH CONDITION | Print T-501 kusabi, T-502 tenon, pivot socket 1:1 PLA before milling |
| Load path shown or described | PASS | S-101 in guidebook; wind via planters + ladder spread |
| Moments/forces bounded | PASS WITH CONDITION | Planning FS 1.5; PE if AHJ requires |
| Assumptions and limitations on structural sheet | PASS | G-001 banner; not PE-stamped |
| Foundations fully detailed OR explicit hold point | PASS | Sit-on-grade; no foundation. Pads 60015K58. No pour. |
| Hardware exact make/model or custom geometry | PASS | McMaster schedule; oak pivots mill from 96825K84 |
| Threshold, drainage, service clearances | PASS | Gate bottom 0.375″; kick 2×12; planter drainage slots |
| Seasonal removable components have retention/removal | PASS | Kusabi reverse; winter sequence in manual |
| Numerical tolerances for critical fits | PASS | T1 general / T2 joinery; nuki sliding; pivot locational |
| Inspection methods and acceptance | PASS | QA-701 + Q-101 |
| Irreversible hold points identified | PASS | Never glue kusabi/nuki faces; paint after dry-fit |
| Assembly sequence present | PASS | LEGO `/martin/manual/` 24 steps + AS-01..12 |
| Solo-handling rules | PASS | Two-person nuki slide; posts lift individually from F-003 |
| Stock prep / grain / finish rules | PASS | F-102 in guidebook; H-005 Buffalo paint |
| Self-containment: skilled builder + this package + listed materials | PASS WITH CONDITION | Close TBM 143″, Green Code, electrician for 120 V, plant troughs |

**Release recommendation:** FABRICATION-READY WITH CONDITIONS. Do not mark FABRICATION-READY (unconditional). Do not mark PE-approved.
"""
    write(os.path.join(OUT, "ZERO_GAP.md"), zg)

    csv_write(
        os.path.join(OUT, "MCMASTER_SCHEDULE.csv"),
        proj["mcmaster"],
        ["LINE", "HARDWARE_ID", "ROLE", "PN", "URL", "DESCRIPTION", "QTY", "UNIT", "WHERE", "FAMILY", "EVIDENCE", "SUBSTITUTE"],
    )
    csv_write(
        os.path.join(OUT, "REQUIREMENTS.csv"),
        proj["requirements"],
        ["ID", "PRI", "STATEMENT", "VERIFY", "STATUS", "EVIDENCE"],
    )

    # ---- HTML book ----------------------------------------------------------
    mc_rows = []
    for r in proj["mcmaster"]:
        mc_rows.append(
            "<tr class='%s'>"
            "<td>%s</td><td>%s</td><td>%s</td>"
            "<td><a class='sku' href='%s' rel='noopener' target='_blank'>%s</a></td>"
            "<td>%s</td><td>%s</td><td>%s</td></tr>"
            % (
                "opt" if r["ROLE"] == "OPTIONAL" else "req",
                esc(r["LINE"]),
                esc(r["HARDWARE_ID"]),
                esc(r["ROLE"]),
                esc(r["URL"]),
                esc(r["PN"]),
                esc(r["DESCRIPTION"]),
                esc(r["QTY"]),
                esc(r["WHERE"]),
            )
        )

    req_html = rows_html(
        proj["requirements"], ["ID", "PRI", "STATEMENT", "VERIFY", "STATUS", "EVIDENCE"]
    )
    ev_html = rows_html(proj["evidence"], ["ID", "DESC", "CLASS", "RELIABILITY", "VERIFY"])
    fmea_html = rows_html(proj["fmea"], ["MODE", "CAUSE", "EFFECT", "SEV", "LKL", "DET", "MIT"])
    joint_html = rows_html(
        proj["joints"][:18],
        ["JOINT_ID", "JOINT_TYPE", "PART_A", "PART_B", "LOCATION", "FIT_CLASS", "GLUE"],
    )
    seq_html = "<ol class='seq'>" + "".join(
        f"<li><b>{esc(s['id'])}</b> <i>{esc(s['phase'])}</i> — {esc(s['title'])}</li>"
        for s in proj["sequence"]
    ) + "</ol>"
    unres = "<ul>" + "".join(
        f"<li><b>{esc(u['ID'])}</b> [{esc(u['CLASS'])}] {esc(u['ITEM'])}</li>"
        for u in proj["unresolved"]
    ) + "</ul>"
    cond = "<ul>" + "".join(f"<li>{esc(c)}</li>" for c in pf["CONDITIONS"]) + "</ul>"
    dec = "<ul>" + "".join(
        f"<li><b>{esc(d['ID'])}</b> {esc(d['Decision'])} <span class='dim'>{esc(d['Reason'])}</span></li>"
        for d in proj["decisions"]
    ) + "</ul>"

    make_parts = [p for p in proj["parts"] if p.get("MAKE_OR_BUY", "MAKE") != "BUY" or p["PART_CATEGORY"] in "LFRCKGQWTC"]
    # show fabricated lumber/joinery, not every BUY
    fab_parts = [p for p in proj["parts"] if str(p.get("PART_ID", "")).split("-")[0] in {"L", "R", "K", "C", "G", "W", "F", "Q", "T"}]
    part_rows = []
    for p in fab_parts:
        part_rows.append(
            "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s × %s × %s</td><td>%s</td></tr>"
            % (
                esc(p["PART_ID"]),
                esc(p["PART_NAME"]),
                esc(p.get("QUANTITY", "")),
                esc(p.get("PURCHASE", "")),
                esc(p.get("FINISHED_THICKNESS", "")),
                esc(p.get("FINISHED_WIDTH", "")),
                esc(p.get("FINISHED_LENGTH", "")),
                esc(p.get("JOINERY", "")[:80]),
            )
        )

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>MARTIN · WOODWRIGHT PLANFORGE v1.0 · Master Build Guide</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Newsreader:opsz,wght@6..72,500;6..72,600&display=swap" rel="stylesheet"/>
<style>
:root{{--ink:#1a1f24;--paper:#f3f1ec;--sage:#3d5a4c;--sage-hi:#8fad78;--dim:#6e7578;--line:#c5c8c2;--warn:#8a3a2a;--banner:#3a1814}}
*{{box-sizing:border-box}}
html,body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 Newsreader,Georgia,serif}}
code,.mono,table,nav,th,td,.k{{font-family:"IBM Plex Mono",Menlo,monospace}}
a{{color:var(--sage)}}
.banner{{background:var(--banner);color:#f3e6dc;padding:10px 22px;font:600 12px/1.4 "IBM Plex Mono",monospace;letter-spacing:.04em}}
.banner b{{color:#e8c4a8}}
header.hero{{padding:36px 28px 12px;max-width:1100px}}
.k{{font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:var(--sage);font-weight:600}}
h1{{font-size:clamp(36px,6vw,64px);margin:8px 0 6px;font-weight:600}}
.lead{{max-width:70ch;color:var(--dim);font-size:18px}}
nav.toc{{position:sticky;top:0;z-index:5;background:rgba(243,241,236,.94);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);padding:10px 20px;display:flex;gap:10px;flex-wrap:wrap}}
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
th{{color:var(--sage);font-weight:600;letter-spacing:.06em;font-size:10px;text-transform:uppercase}}
tr.opt td{{color:var(--dim)}}
a.sku{{font-weight:600;letter-spacing:.04em}}
.elev{{width:100%;border:1px solid var(--line);background:#fff}}
.seq{{padding-left:22px}}
.seq i{{color:var(--dim);font-style:normal;font-size:12px}}
.dim{{color:var(--dim);display:block;font-size:13px;margin-top:4px}}
.warn{{color:var(--warn);font-weight:600}}
.links{{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}}
.links a{{display:inline-block;padding:8px 12px;border:1px solid var(--sage);text-decoration:none;font:600 11px/1 "IBM Plex Mono",monospace;letter-spacing:.08em;text-transform:uppercase}}
ul{{padding-left:20px}}
footer{{padding:24px 28px;color:var(--dim);font-size:13px;border-top:1px solid var(--line)}}
@media print{{nav.toc,.banner{{position:static}} a.sku{{color:#000}}}}
</style>
</head>
<body>
<div class="banner">
  RELEASE: <b>{esc(pf['RELEASE_STATE'])}</b>
  · RISK <b>{esc(pf['RISK_CLASS'])}</b>
  · NOT A PE STAMP · NOT FOR UNOBSERVED BUILD
  · VERIFY 143″ ON SITE · BUFFALO GREEN CODE TBM
  · {esc(pf['PROJECT_CODE'])}
</div>
<header class="hero">
  <p class="k">WOODWRIGHT PLANFORGE v1.0 · Kernel {esc(PROJECT['MODEL_VERSION'])} · Rev {esc(PROJECT['REVISION'])}.1</p>
  <h1>The Martin Line</h1>
  <p class="lead">Master build-plans guidebook: Darwin Martin Tree of Life light-screen, Japanese nuki/kusabi/kama-tsugi, sit-on-grade ladder across the driveway, LEGO assembly, sourced McMaster-Carr buy list. If you don’t build it, it never exists — but you still do not skip the conditions below.</p>
  <div class="links">
    <a href="../manual/">LEGO build manual</a>
    <a href="../fab/">Fab package</a>
    <a href="../app/">Build app</a>
    <a href="../plans/M1_general.svg">M-1 elevation</a>
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
  <a href="#f101">F Fabrication</a>
  <a href="#h101">H McMaster</a>
  <a href="#s101">S Structural</a>
  <a href="#q101">Q Quality</a>
</nav>
<main>

<section id="g001">
  <p class="k">G-001 · Governance / cover</p>
  <h2>Release, datums, thesis</h2>
  <div class="grid">
    <div class="card"><p class="k">Release</p><p>{esc(pf['RELEASE_STATE'])}</p></div>
    <div class="card"><p class="k">Risk</p><p>{esc(pf['RISK_CLASS'])} — {esc(', '.join(pf['RISK_TRIGGERS']))}</p></div>
    <div class="card"><p class="k">Layout</p><p>{esc(pf['LAYOUT_SYSTEM'])}</p></div>
    <div class="card"><p class="k">Units</p><p>{esc(pf['UNITS'])}</p></div>
  </div>
  <h3>Design thesis</h3>
  <p>Wright at a distance is eave + belt courses + brick piers + patterned lights — not five fat horizontal slats. The garden face is a Darwin Martin Tree of Life wood light-screen: 2×12 PT water table, nested-rect cassette, projecting 2×10 belt, three-tree cassette, belt at latch CL, nested-rect cassette, cantilevered 2×12 eave with 1×4 fascia. Gate flush to the house. Live planters ballast the two privacy bays only.</p>
  <h3>Conditions — close these before cutting finish stock</h3>
  {cond}
  <p class="warn">Do not treat a rendering, this HTML book, or the Build app viz as a scaled fabrication drawing. Controlling numbers live in <code>martin_kernel.py</code> and the dimensioned SVG sheets.</p>
</section>

<section id="g002">
  <p class="k">G-002 · Requirements traceability</p>
  <h2>MUST / SHOULD / EXCLUDED</h2>
  {req_html}
  <p>Vague adjectives are not specs. “Jaw-dropping” maps to AESTH-001 (Tree of Life motifs on GA-110, no Z-brace garden face) plus J-series joinery that is cuttable with the owner’s hand tools.</p>
</section>

<section id="g003">
  <p class="k">G-003 · Evidence / assumptions / revision</p>
  <h2>What is known vs assumed</h2>
  <p>Evidence classes: <b>G</b> given · <b>M</b> measured · <b>S</b> sourced · <b>D</b> derived · <b>A</b> assumed · <b>E</b> estimated · <b>T</b> test · <b>P</b> professional-verify · <b>TBM</b> to be measured.</p>
  {ev_html}
  <h3>Decisions that freeze the face</h3>
  {dec}
  {unres}
</section>

<section id="g004">
  <p class="k">G-004 · Safety / FMEA / professional review</p>
  <h2>Hazards in proportion to R2</h2>
  <p>{esc(pf['PROFESSIONAL_REVIEW'])}</p>
  <p>120 V to driver <b>8836N24</b> is electrician work. Tape in the soffit is 24 V. Do not stand the empty fence in a Buffalo gale — plant the troughs (QC-15) first. Never glue kusabi. Never pour. Never fasten the ladder into the driveway.</p>
  {fmea_html}
</section>

<section id="a101">
  <p class="k">A-101 / A-102 · Architecture</p>
  <h2>General arrangement — garden face</h2>
  <p>143″ overall · 65″ high · posts {esc(posts)} · bay_clear {ly['bay_clear']}″ · nuki_len {ly['nuki_len']}″ · cassette φ {ly['light_minor']} / {ly['light_major']}″. Print M-1 at 100% on A3; do not scale this screenshot.</p>
  <img class="elev" src="../plans/M1_general.svg" alt="Sheet M-1 general arrangement — Tree of Life elevation"/>
  <div class="links">
    <a href="../fab/06_DRAWINGS/GA-110_elevation.svg">GA-110 datums</a>
    <a href="../fab/06_DRAWINGS/GA-130_plan.svg">GA-130 plan</a>
    <a href="../fab/06_DRAWINGS/EX-200_exploded.svg">EX-200 explode</a>
    <a href="../plans/M2_elevation.svg">M-2 bay</a>
    <a href="../cad/exports/martin.FCStd">FreeCAD</a>
    <a href="../cad/exports/martin_assembly.step">STEP</a>
  </div>
  <h3>What you should see (anti Home Depot)</h3>
  <ul>
    <li>Solid 2×12 water table at grade — dog crawl stop, Wright earth line.</li>
    <li>Two projecting 2×10 belts past Roman-brick piers — not a flush ranch face.</li>
    <li>Three recessed lights: nested squares / three trees / nested squares.</li>
    <li>Thin-wide 2×12 eave + hanging fascia + soffit light. Gate is the same language, no Z-brace on the garden face.</li>
  </ul>
</section>

<section id="j101">
  <p class="k">J-101 · Joinery map</p>
  <h2>Japanese mechanical joints — no glue on locking faces</h2>
  <p>Primary layout is face/edge (x=0, z=0). Transfer post CLs with a story stick. Through-nuki only K-001 + R-001 + R-002 so the 4×6 web survives. Cassettes are kumiko-style muntin frames that drop into nuki-edge grooves and withdraw toward P3 for winter.</p>
  {joint_html}
  <div class="links">
    <a href="../fab/06_DRAWINGS/J-401_nuki.svg">J-401 Nuki + kusabi</a>
    <a href="../fab/06_DRAWINGS/J-402_tenon.svg">J-402 Foot tenon</a>
    <a href="../fab/06_DRAWINGS/J-403_kama.svg">J-403 Kama-tsugi</a>
    <a href="../fab/06_DRAWINGS/J-404_hozo.svg">J-404 Hozo + oak pivot</a>
    <a href="../fab/10_TEMPLATES/T-501_kusabi.svg">T-501 1:1 kusabi</a>
    <a href="../fab/10_TEMPLATES/T-502_tenon.svg">T-502 1:1 tenon</a>
  </div>
  <h3>3D-print before you mill (PLA / PETG, 1:1)</h3>
  <ul>
    <li>T-501 kusabi — confirm taper, cheek clearance, reverse-drive.</li>
    <li>T-502 foot tenon 2.50×4.50×3.50 into F-003 mortise.</li>
    <li>W-003 ⌀1.25″ pivot in sill + soffit sockets (locational, lift-off +Z).</li>
    <li>Kama-tsugi half at P2 — drawbore offset 0.125″.</li>
  </ul>
  <p>Hand-tool sequence: knife walls → Japanese saw cheeks → Zenwu pare → Bridge City kerf/tenon for repeat rails → dry-fit under raking light → drawbore last. Never glue nuki or kusabi faces.</p>
</section>

<section id="e101">
  <p class="k">E-101 / E-102 · Exploded assembly (LEGO)</p>
  <h2>Twenty-four steps, six bags</h2>
  <p>The step-by-step manual is generated from the same kernel. Orange arrows are this-step motion. Numbered balloons match the BOM.</p>
  <div class="links">
    <a href="../manual/">Open LEGO manual</a>
    <a href="../fab/06_DRAWINGS/EX-200_exploded.svg">EX-200</a>
    <a href="../app/#assembly">App checklist</a>
  </div>
  {seq_html}
  <p><b>Solo handling:</b> mill and dry-fit as modules. Slide nuki belts with two people (109.5″ × 2×10). Lift posts one at a time out of F-003. Do not ask one person to carry the assembled 143″ frame.</p>
  <p><b>Irreversible hold points:</b> (1) do not glue kusabi; (2) do not paint locking faces; (3) do not plant empty troughs after a wind warning without QC-15; (4) do not pour.</p>
</section>

<section id="f101">
  <p class="k">F-101 / F-102 · Fabrication</p>
  <h2>Part register (MAKE) · nest {nest['net_bf']} bf net / {nest['procurement_bf']} bf buy</h2>
  <table>
    <thead><tr><th>ID</th><th>Name</th><th>Qty</th><th>Buy</th><th>Finished T×W×L</th><th>Joinery</th></tr></thead>
    <tbody>{''.join(part_rows)}</tbody>
  </table>
  <div class="links">
    <a href="../fab/07_BOM/bom.csv">BOM CSV</a>
    <a href="../fab/08_CUT_LISTS/finished.csv">Finished cuts</a>
    <a href="../fab/08_CUT_LISTS/nest.csv">Nest</a>
    <a href="../plans/M6_cutlist.svg">M-6</a>
  </div>
  <h3>Stock prep</h3>
  <ul>
    <li>Acclimate paint-grade SPF/SYP and PT kick/planters. Re-measure after rest.</li>
    <li>Grain: posts vertical; nuki length along the run; muntins as came (face grain to garden).</li>
    <li>Reject pith, loose knots, and short grain at tenon shoulders and nuki cheeks.</li>
    <li>Do not rip 2×10 belts to force φ — 9.25 / 5.5 is already near φ; cassettes take the φ pair.</li>
    <li>Finish: ease 1/16″, end-grain sealer, PT dry then prime, two owner-gray coats, extra in planter interiors. Mask joinery.</li>
  </ul>
</section>

<section id="h101">
  <p class="k">H-101 · McMaster-Carr itemized buy</p>
  <h2>Linkable products — lighting, pads, oak rods, optional hasp</h2>
  <p>Opened on mcmaster.com 2026-08-15. Allowed metal is lighting + optional latch hardware. <b>No structural screws into timber.</b> Paint and landscape stone are not McMaster. Optional rows are grey.</p>
  <table>
    <thead><tr><th>Line</th><th>ID</th><th>Role</th><th>McMaster PN</th><th>Description</th><th>Qty</th><th>Where</th></tr></thead>
    <tbody>{''.join(mc_rows)}</tbody>
  </table>
  <p>Family pages:
    <a href="https://www.mcmaster.com/products/vibration-damping-pads/">pads</a> ·
    <a href="https://www.mcmaster.com/products/tape-lights/">tape lights</a> ·
    <a href="https://www.mcmaster.com/products/wood-dowel-rods/">oak rods</a> ·
    <a href="https://www.mcmaster.com/products/straight-bar-hasps/">hasps</a>.
    Confirm each PN is still current before ordering — catalogs move.
  </p>
  <p>Primary hinge remains mill oak from <a class="sku" href="https://www.mcmaster.com/96825K84/">96825K84</a>. No McMaster pintle is specified; H-003 is an unselected backup.</p>
  <p>Download: <a href="MCMASTER_SCHEDULE.csv">MCMASTER_SCHEDULE.csv</a></p>
</section>

<section id="s101">
  <p class="k">S-101 · Structural / site</p>
  <h2>Load path (planning)</h2>
  <ol>
    <li>Wind on the ~64 sf light-screen face → nuki belts + water table → 4×6 posts.</li>
    <li>Posts drop 3.50″ tenons into F-003 shoes on the dodai ladder.</li>
    <li>Ladder sits on eight 60015K58 pads on the existing driveway — no overturning foundation.</li>
    <li>Restoring moment: 36″ sill spread + F-006 braces + wet soil/stone in two garden troughs ({bal['provided_lb']} lb provided vs {bal['required_lb']} lb required at FS {bal['fs']}, ratio {bal['ratio']}).</li>
    <li>Gate leaf weight in compression to the driveway sill through oak pivots at P1 — not a pintle cantilever off P0.</li>
  </ol>
  <p class="warn">This wind calc is a planning check, not NDS design and not a PE stamp. If Buffalo requires a stamped fence drawing, stop and hire a New York design professional. Do not occupy the driveway side during a proof load.</p>
</section>

<section id="q101">
  <p class="k">Q-101 · Inspection, commissioning, zero-gap</p>
  <h2>Hold points</h2>
  <ul>
    <li>QC-08 — 1.50″ max muntin aperture gauge through every Tree of Life / nested-rect opening.</li>
    <li>QC-10 — kusabi dry, labeled NEVER GLUE.</li>
    <li>QC-14 — gate clears eave 0.50″; bottom 0.375″.</li>
    <li>QC-15 — ballast ratio after planting ≥ 1.0.</li>
    <li>QC-17 — 8836N52 in dado; 8836N24 in P3 planter, not the house.</li>
  </ul>
  <div class="links">
    <a href="../fab/12_QA/QA-701_inspection.svg">QA-701</a>
    <a href="ZERO_GAP.md">Zero-gap checklist (filled)</a>
    <a href="../fab/09_JOINERY/joints.csv">Joints CSV</a>
  </div>
  <h3>Zero-gap result</h3>
  <p>Primary/secondary parts, joints, hardware SKUs, tolerances, assembly, and layout system <b>PASS</b>. Structural PE stamp, Green Code, 143″ TBM, electrician, and 1:1 PLA joint coupons are <b>PASS WITH CONDITION</b>. Unconditional FABRICATION-READY is withheld.</p>
  <h3>Builder’s next action</h3>
  <ol>
    <li>Remeasure the driveway opening. If it is not 143″, change <code>overall_length</code> in the kernel and regenerate — do not fudge boards.</li>
    <li>Order McMaster lines MC-001 through MC-006 (required). Add MC-007/008 only if you want the channel or hasp.</li>
    <li>Print T-501 / T-502 / pivot socket. Fit. Then mill.</li>
    <li>Walk the LEGO manual bag by bag. Paint after dry-fit. Plant before storm season.</li>
  </ol>
</section>
</main>
<footer>
  MARTIN · WOODWRIGHT PLANFORGE v1.0 · {esc(pf['PROJECT_CODE'])} · kernel {esc(PROJECT['MODEL_VERSION'])} ·
  generated from martin_kernel.py · sit-on-grade · no nails in timber · Buffalo NY
</footer>
</body>
</html>
"""
    write(os.path.join(OUT, "index.html"), html)

    readme = f"""# MARTIN WOODWRIGHT PLANFORGE v1.0

Release: **{pf['RELEASE_STATE']}** · Risk **{pf['RISK_CLASS']}** · Kernel {PROJECT['MODEL_VERSION']}

- [Guidebook](index.html) — G/A/J/E/F/H/S/Q sheets
- [Design basis](DESIGN_BASIS.md)
- [Zero-gap checklist](ZERO_GAP.md)
- [McMaster-Carr schedule](MCMASTER_SCHEDULE.csv)
- [Requirements](REQUIREMENTS.csv)
- LEGO assembly: `/fence/martin/manual/`
- Shop drawings: `/fence/martin/fab/`
- CAD: `/fence/martin/cad/exports/`

Print the guidebook from the browser at 100%. Controlling geometry is in `martin_kernel.py`, not in a screenshot.
"""
    write(os.path.join(OUT, "README.md"), readme)


if __name__ == "__main__":
    generate()
