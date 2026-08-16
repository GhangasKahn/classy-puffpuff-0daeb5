# WALTER DS-16

Modern dedicated **drum thickness sander** — ShopNotes No. 86 lineage via Ron Walters.

- **Rev A:** solid sliding table (no conveyor)
- **Rev B:** dual-end geometry, UHMW ways, hold-downs
- **Fab B.4:** vertical captured ways, stretcher stations that miss the table, both Acme screws on the drum centerline
- **Rev C / fab C.1:** 1¼″ shaft + structural 6061 shell, ALN-01 / TV-01 spec split, tapered gib, idler micro-adjust, bearings specified by required C, McMaster procurement register

**Release: FABRICATION REVIEW · risk class R3.** Not fabrication-ready. Electrical, flange BCD, and bearing C remain holds.

## Live paths

- Design overview: `/shop/drum-sander/` · shortcuts `/walter` · `/drum` · `/shop`
- Build app: `/shop/drum-sander/app/` · `/walter/app` · `/drum/app`
- Pocket field card: `/shop/drum-sander/pocket/` · `/walter/pocket`
- **Viewer app (phone):** `/shop/drum-sander/view/` · `/walter/view` — 3D parts + swipeable plans, Add to Home Screen
- **Master build guide:** `/shop/drum-sander/guide/`
- **Shop pack (ZIP):** `/shop/drum-sander/pack/WALTER-DS16-RevC.zip` · `/walter/pack`
- Plans: `G-001`…`G-005`, `P-001L`…`P-024`, `ST-01`…`ST-18` in `/shop/drum-sander/plans/`
- Interactive 3D: `/shop/drum-sander/model/` · `/walter/model`
- OpenSCAD: `cad/walter_ds16.scad` (includes generated `parameters.scad`)
- Fabrication dump: `cad/fabrication.json` · `pack/parts.csv` · `pack/mcmaster.csv`
- Isometric renders: `renders/iso_assembled.svg` etc.

## Spec (Rev C)

| Item | Value |
|------|-------|
| Capacity | 15.5″ wide · 1/16″–3″ thick |
| ALN-01 | \|A−B\| ≤ 0.003″ no-load, paper-on |
| TV-01 | witness-board spread ≤ 0.005″ |
| Drum TIR | ≤ 0.0015″ paper-off |
| Drum | ⌀5″ × 15.75″ @ ~1208 RPM · 1 HP · 3½″/5″ sheaves |
| Axis | 1¼″ × 24″ shaft + 5.00″ × 0.25″ 6061 shell (Option B disc stack documented) |
| Lift | Dual ½-10 Acme on drum CL, chain-coupled, left clutch + home dog |
| Table | Torsion box, vertical captured UHMW ways + 1:40 gib, phenolic/MIC-6 |
| Hold-downs | Infeed/outfeed rollers 0.030″ below drum |
| Oscillator | Optional ⅛″ @ ~80 cpm (not drum RPM) |
| Ways | Vertical UHMW, 0.52″ rebate, projecting 0.23″, shoes wrap the tongue |
| Stretchers | P-003 housed ¼″ · stand on edge · IN-LO / OUT-LO / OUT-HI · through-bolted |
| Ply note | Keep 16.5″ (419 mm) inner span; 18 mm Euro BB is fine |

SSOT: `cad/walter_ds16.py`. Mechanics: `cad/ds16_mechanics.py`. Procurement: `cad/ds16_procurement.py`. Change a parameter, regenerate. McMaster part numbers are `CONFIRM AT ORDER`.

## Regenerate plans

```bash
python3 scripts/gen_drum_sander_plans.py
python3 scripts/gen_drum_sander_iso.py
python3 scripts/gen_walter_part_sheets.py
python3 scripts/gen_walter_guidebook.py
python3 scripts/qa_walter_package.py
python3 scripts/pack_drum_sander.py
```

## Sources

- https://woodgears.ca/reader/walters/drum_sander.html
- https://youtu.be/W-5Sj6kBVic
- https://woodgears.ca/sander/drum.html
- https://woodgears.ca/sander/plans/
