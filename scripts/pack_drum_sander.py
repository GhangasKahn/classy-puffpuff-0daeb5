#!/usr/bin/env python3
"""Pack WALTER DS-16 for phone download: ZIP, CSV, spec.json, pocket card, app icon.

Run after plan generators:
  python3 scripts/gen_drum_sander_plans.py
  python3 scripts/gen_drum_sander_iso.py
  python3 scripts/gen_walter_part_sheets.py
  python3 scripts/pack_drum_sander.py
"""

from __future__ import annotations

import csv
import json
import os
import struct
import sys
import zipfile
import zlib
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOP = ROOT / "shop" / "drum-sander"
sys.path.insert(0, str(SHOP / "cad"))

from walter_ds16 import (  # noqa: E402
    SPEC,
    assembly_phases,
    calibration_steps,
    cut_list,
    fastener_schedule,
    hardware,
    hardware_bom,
    inspection,
    joints,
    lumberyard,
    operations,
    parts,
    pass_schedule,
    quality_targets,
    summary,
    surface_fpm,
    write_exports,
)

PACK = SHOP / "pack"
POCKET = SHOP / "pocket"
APP = SHOP / "app"
ZIP_NAME = "WALTER-DS16-RevB.zip"


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def write_png_icon(path: Path, size: int = 180) -> None:
    """Drum-mark PNG so iOS Add to Home Screen has a real icon."""

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    cx = cy = size / 2
    r_outer = size * 0.34
    r_mid = size * 0.16
    r_hub = size * 0.06
    rows = []
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = (dx * dx + dy * dy) ** 0.5
            # dark rounded-rect-ish fill
            r, g, b, a = 20, 24, 28, 255
            if d <= r_outer + 3 and d >= r_outer - 3:
                r, g, b = 196, 165, 116  # wood ring
            elif d <= r_mid:
                r, g, b = 138, 144, 152  # steel hub
                if d <= r_hub:
                    r, g, b = 20, 24, 28
            # table line
            if abs(y - size * 0.78) < 2 and abs(x - cx) < size * 0.32:
                r, g, b = 143, 173, 120
            row.extend((r, g, b, a))
        rows.append(bytes(row))
    raw = b"".join(rows)
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def pocket_html() -> str:
    s = SPEC
    sfpm = round(surface_fpm(s.drum_od, s.drum_rpm))
    cuts = "".join(
        f"<tr><td>{escape(str(r['part_id']))}</td><td>{escape(str(r['qty']))}</td><td>{escape(r['size'])}<br><small>{escape(r.get('size_mm',''))}</small></td>"
        f"<td>{escape(r['stock'])}</td><td>{escape(r['use'])}</td></tr>"
        for r in cut_list()
    )
    lumber = "".join(
        f"<tr><td>{escape(r['where'])}</td><td>{escape(r['item'])}</td><td>{escape(r['qty'])}</td>"
        f"<td>{escape(r['use'])}</td></tr>"
        for r in lumberyard()
    )
    fast = "".join(
        f"<tr><td>{escape(r['qty'])}</td><td>{escape(r['item'])}</td><td>{escape(r['use'])}</td></tr>"
        for r in fastener_schedule()
    )
    hw = "".join(
        f"<tr><td>{escape(r['qty'])}</td><td>{escape(r['item'])}</td></tr>" for r in hardware_bom()
    )
    passes = "".join(
        f"<div class='card'><b>{escape(p['grit'])} grit</b><strong>{escape(p['depth'])}</strong><p>{escape(p['use'])}</p></div>"
        for p in pass_schedule()
    )
    quality = "".join(
        f"<tr><td>{escape(q['check'])}</td><td>{escape(q['spec'])}</td></tr>" for q in quality_targets()
    )
    cal = "".join(
        f"<li><b>{escape(c['title'])}</b> — {escape(c['body'])}</li>" for c in calibration_steps()
    )
    asm = "".join(
        f"<li><b>{escape(a['id'].upper())} {escape(a['title'])}</b> — {escape(a['body'])}</li>"
        for a in assembly_phases()
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"/>
<meta name="theme-color" content="#14181c"/>
<meta name="apple-mobile-web-app-capable" content="yes"/>
<meta name="apple-mobile-web-app-title" content="WALTER"/>
<title>WALTER DS-16 pocket card</title>
<link rel="apple-touch-icon" href="../app/apple-touch-icon.png"/>
<style>
:root{{--ink:#14181c;--ink2:#1c2228;--paper:#f3f1ec;--dim:#a8afb3;--sage:#8fad78;--wood:#c4a574;--line:rgba(243,241,236,.14)}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--ink);color:var(--paper);font:16px/1.45 system-ui,sans-serif;padding:16px 16px 80px}}
h1{{font:600 40px/1 Georgia,serif;margin:8px 0}}
h2{{font:600 22px/1.2 Georgia,serif;margin:28px 0 10px}}
.k{{letter-spacing:.2em;text-transform:uppercase;color:var(--sage);font:600 11px/1 ui-monospace,monospace}}
.lead{{color:var(--dim);max-width:40ch}}
.row{{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}}
a.btn,button.btn{{display:inline-flex;align-items:center;justify-content:center;padding:14px 16px;border-radius:10px;
  border:1px solid var(--line);background:#222a30;color:var(--paper);text-decoration:none;font:600 13px/1 ui-monospace,monospace;
  letter-spacing:.06em;text-transform:uppercase;min-height:48px;cursor:pointer}}
a.btn.primary{{background:#3d5a4c;border-color:#5a6a4a}}
.grid{{display:grid;gap:8px;grid-template-columns:repeat(auto-fit,minmax(140px,1fr))}}
.card{{background:var(--ink2);border:1px solid var(--line);border-radius:12px;padding:12px 14px}}
.card strong{{display:block;font:600 22px/1.1 Georgia,serif;margin:6px 0}}
.ab{{font:600 48px/1 Georgia,serif;color:var(--wood)}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th,td{{text-align:left;padding:8px 6px;border-bottom:1px solid var(--line);vertical-align:top}}
th{{color:var(--dim);font:600 10px/1 ui-monospace,monospace;letter-spacing:.12em;text-transform:uppercase}}
small{{color:var(--dim)}}
ol,ul{{padding-left:1.2em;color:var(--dim)}}
li{{margin:8px 0}}
.hint{{color:var(--dim);font-size:14px}}
@media print{{body{{background:#fff;color:#111}} a.btn{{display:none}} .card{{border-color:#ccc}}}}
</style>
</head>
<body>
<p class="k">WALTER · DS-16 · Rev {escape(s.revision)}</p>
<h1>Pocket card</h1>
<p class="lead">Shop-floor numbers for the phone. Save the ZIP to Files, then keep this page on the Home Screen.</p>
<div class="row">
  <a class="btn primary" href="../pack/{ZIP_NAME}" download="{ZIP_NAME}">Download shop pack</a>
  <button class="btn" type="button" id="sharePack">Share to Files</button>
  <a class="btn" href="../app/">Build app</a>
  <a class="btn" href="../">Design</a>
</div>
<p class="hint">iPhone: Share to Files. Android: Download pack. Then Share this page → Add to Home Screen, or Print → Save PDF.</p>

<div class="grid">
  <div class="card"><span class="k">Capacity</span><strong>{s.capacity_width:g}″</strong><p>1/16″–3″ thick · {s.capacity_width * 25.4:.0f} mm</p></div>
  <div class="card"><span class="k">Drum</span><strong>⌀{s.drum_od:g}″</strong><p>{s.drum_rpm:g} RPM · ~{sfpm:g} sfpm</p></div>
  <div class="card"><span class="k">A/B spec</span><div class="ab">±{s.parallel_tol:.3f}″</div><p>paper on · {(s.parallel_tol * 25.4):.2f} mm</p></div>
  <div class="card"><span class="k">TIR</span><strong>≤ {s.drum_tir:.3f}″</strong><p>paper off, then wrap, then re-clock</p></div>
</div>

<h2>Pass schedule</h2>
<div class="grid">{passes}</div>

<h2>Clock A/B (paper on)</h2>
<ol>{cal}</ol>
<table>{quality}</table>

<h2>Lumberyard</h2>
<p class="hint">Keep 16.5″ (419 mm) clear between inner faces even if the birch is 18 mm.</p>
<table><thead><tr><th>Aisle</th><th>Buy</th><th>Qty</th><th>For</th></tr></thead><tbody>{lumber}</tbody></table>

<h2>Fasteners</h2>
<table><thead><tr><th>Qty</th><th>Item</th><th>Use</th></tr></thead><tbody>{fast}</tbody></table>

<h2>Cut list (inch / mm)</h2>
<table><thead><tr><th>ID</th><th>Qty</th><th>Size</th><th>Stock</th><th>Part</th></tr></thead><tbody>{cuts}</tbody></table>

<h2>Specialty hardware</h2>
<table><thead><tr><th>Qty</th><th>Item</th></tr></thead><tbody>{hw}</tbody></table>

<h2>Assembly</h2>
<ol>{asm}</ol>

<p class="hint">Lineage: ShopNotes 86 → Ron Walters → Rev B geometry. woodgears.ca/reader/walters/drum_sander.html</p>
<script>
(function(){{
  const zip = new URL("../pack/{ZIP_NAME}", location.href).href;
  const btn = document.getElementById("sharePack");
  if (!btn) return;
  btn.onclick = async function(){{
    try {{
      const res = await fetch(zip);
      const blob = await res.blob();
      const file = new File([blob], "{ZIP_NAME}", {{ type: "application/zip" }});
      if (navigator.canShare && navigator.canShare({{ files: [file] }})) {{
        await navigator.share({{ files: [file], title: "WALTER DS-16 shop pack" }});
        return;
      }}
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "{ZIP_NAME}";
      a.click();
    }} catch (e) {{
      if (e && e.name === "AbortError") return;
      location.href = zip;
    }}
  }};
}})();
</script>
</body>
</html>
"""


def pack_zip() -> Path:
    PACK.mkdir(parents=True, exist_ok=True)
    zpath = PACK / ZIP_NAME
    files: list[tuple[Path, str]] = []

    def add(src: Path, arc: str) -> None:
        if src.is_file():
            files.append((src, arc))

    add(PACK / "README.txt", "README.txt")
    add(PACK / "BOM.csv", "BOM.csv")
    add(PACK / "parts.csv", "parts.csv")
    add(PACK / "joints.csv", "joints.csv")
    add(PACK / "operations.csv", "operations.csv")
    add(PACK / "qa.csv", "qa.csv")
    add(PACK / "fasteners.csv", "fasteners.csv")
    add(PACK / "lumberyard.csv", "lumberyard.csv")
    add(PACK / "spec.json", "spec.json")
    add(PACK / "fabrication.json", "fabrication.json")
    add(POCKET / "index.html", "pocket.html")
    add(SHOP / "guide" / "index.html", "guide/index.html")
    add(SHOP / "guide" / "DESIGN_BASIS.md", "guide/DESIGN_BASIS.md")
    add(SHOP / "view" / "index.html", "view/index.html")
    add(SHOP / "view" / "view.css", "view/view.css")
    add(SHOP / "view" / "view.js", "view/view.js")
    add(SHOP / "cad" / "walter_ds16.py", "cad/walter_ds16.py")
    add(SHOP / "cad" / "walter_ds16.scad", "cad/walter_ds16.scad")
    add(SHOP / "cad" / "parameters.scad", "cad/parameters.scad")
    add(SHOP / "cad" / "fabrication.json", "cad/fabrication.json")
    for p in sorted((SHOP / "planforge").glob("*.md")):
        add(p, f"planforge/{p.name}")
    for p in sorted((SHOP / "plans").glob("*.svg")):
        add(p, f"plans/{p.name}")
    for p in sorted((SHOP / "renders").glob("*.svg")):
        add(p, f"renders/{p.name}")

    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for src, arc in files:
            zf.write(src, arc)
    return zpath


def main() -> None:
    PACK.mkdir(parents=True, exist_ok=True)
    POCKET.mkdir(parents=True, exist_ok=True)
    write_exports(str(SHOP))

    write_csv(
        PACK / "parts.csv",
        [
            {
                "part_id": p["part_id"],
                "part_name": p["part_name"],
                "qty": str(p["qty"]),
                "make_or_buy": p["make_or_buy"],
                "material": p["material"],
                "finished_size": p["finished_size"],
                "finished_size_mm": p["finished_size_mm"],
                "rough_size": p["rough_size"],
                "handed": p["handed"],
                "joinery": p["joinery"],
                "sheet": p["sheet"],
                "notes": p["notes"],
            }
            for p in parts()
        ],
        ["part_id", "part_name", "qty", "make_or_buy", "material", "finished_size", "finished_size_mm", "rough_size", "handed", "joinery", "sheet", "notes"],
    )
    write_csv(
        PACK / "BOM.csv",
        [
            {
                "item": p["part_id"],
                "description": p["part_name"],
                "qty": str(p["qty"]),
                "make_or_buy": p["make_or_buy"],
                "material": p["material"],
                "finished_size": p["finished_size"],
                "purchase_size": p["purchase_size"],
                "rev": p["revision"],
            }
            for p in parts()
        ]
        + [
            {
                "item": h["hardware_id"],
                "description": h["description"],
                "qty": str(h.get("qty", 1)),
                "make_or_buy": h["make_or_buy"],
                "material": "purchased",
                "finished_size": h.get("size", ""),
                "purchase_size": h.get("purchase", ""),
                "rev": SPEC.fabrication_rev,
            }
            for h in hardware()
        ],
        ["item", "description", "qty", "make_or_buy", "material", "finished_size", "purchase_size", "rev"],
    )
    write_csv(
        PACK / "joints.csv",
        [
            {
                "joint_id": j["joint_id"],
                "joint_type": j["joint_type"],
                "part_a": j["part_a"],
                "part_b": j["part_b"],
                "fit_class": j.get("fit_class", ""),
                "notes": j.get("notes", ""),
            }
            for j in joints()
        ],
        ["joint_id", "joint_type", "part_a", "part_b", "fit_class", "notes"],
    )
    write_csv(
        PACK / "operations.csv",
        [
            {
                "op": o["op"],
                "title": o["title"],
                "tool": o.get("tool", ""),
                "setting": o.get("setting", ""),
                "parts": ", ".join(o.get("parts", [])),
                "rule": o.get("rule", ""),
            }
            for o in operations()
        ],
        ["op", "title", "tool", "setting", "parts", "rule"],
    )
    write_csv(
        PACK / "qa.csv",
        inspection(),
        ["qc", "check", "spec", "class", "gate"],
    )
    write_csv(
        PACK / "fasteners.csv",
        fastener_schedule(),
        ["aisle", "qty", "item", "use"],
    )
    write_csv(
        PACK / "lumberyard.csv",
        lumberyard(),
        ["where", "item", "qty", "alt", "use"],
    )
    fab = json.dumps(summary(), indent=2) + "\n"
    (PACK / "spec.json").write_text(fab, encoding="utf-8")
    (PACK / "fabrication.json").write_text(fab, encoding="utf-8")
    (PACK / "README.txt").write_text(
        "\n".join(
            [
                f"WALTER DS-16  ·  Rev B geometry  ·  fabrication {SPEC.fabrication_rev}",
                "",
                "Phone: Share this ZIP → Save to Files (iPhone) or it lands in Downloads (Android).",
                "Pocket field card: open pocket.html, then Add to Home Screen or Print → PDF.",
                "",
                f"Capacity {SPEC.capacity_width:g}\" · drum ⌀{SPEC.drum_od:g}\" @ {SPEC.drum_rpm:g} RPM",
                f"|A−B| ≤ {SPEC.parallel_tol:.3f}\" paper-on · TIR ≤ {SPEC.drum_tir:.3f}\" paper-off",
                "Keep 16.5\" (419 mm) clear between inner faces (18 mm BB is fine).",
                "Vertical captured ways; stretchers IN-LO/OUT-LO/OUT-HI miss the table; Acme on drum CL.",
                "",
                "START HERE: guide/index.html \u2014 the master build guide, 14 steps in order.",
                "  (open it in a browser; Print \u2192 PDF gives you the book)",
                "  guide/DESIGN_BASIS.md \u2014 release state, layout protocol, mechanics.",
                "",
                "plans/ G-001…G-004 · M-101 kinematics · J-001/002/006/007/011 · F-101 · S-101",
                "plans/ E-101 exploded · ST-01…ST-14 steps · Q-101 commissioning · Q-102 zero-gap",
                "plans/ IDX + P-001L…P-019 individual sheets + A-01…A-05 + H-01 hardware",
                "plans/ D-1…D-12 overviews   renders/ isometric solids",
                "cad/ Python SSOT + OpenSCAD   planforge/ shop standards",
                "BOM.csv parts.csv joints.csv operations.csv qa.csv fasteners.csv lumberyard.csv",
                "fabrication.json = machine-readable source dump",
                "",
                "FABRICATION REVIEW · R3. Cut from the P-sheets. Confirm flange bolt circle against the bearing you bought.",
                "Electrical is not released. Commission hood-on, no stock.",
                "",
                "Sources: woodgears.ca/reader/walters/drum_sander.html  ·  youtu.be/W-5Sj6kBVic",
                "ShopNotes No. 86  ·  Heslop / Hawley  ·  Jet/Grizzly roller practice",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (POCKET / "index.html").write_text(pocket_html(), encoding="utf-8")
    write_png_icon(APP / "apple-touch-icon.png", 180)
    zpath = pack_zip()
    print("wrote", PACK / "BOM.csv")
    print("wrote", POCKET / "index.html")
    print("wrote", APP / "apple-touch-icon.png")
    print("wrote", zpath, f"({zpath.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
