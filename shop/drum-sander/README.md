# WALTER DS-16

Modern dedicated **drum thickness sander** — ShopNotes No. 86 lineage via Ron Walters.

- **Rev A:** solid sliding table (no conveyor)
- **Rev B:** dual-end geometry, UHMW ways, hold-downs, paper-on A/B spec ±0.003″
- **Fab B.1:** part/joint IDs, housed stretchers, way rebate so the 16″ table actually fits the 16.5″ span, JSON/CSV SSOT

## Live paths

- Design overview: `/shop/drum-sander/` · shortcuts `/walter` · `/drum` · `/shop`
- Build app: `/shop/drum-sander/app/` · `/walter/app` · `/drum/app`
- Pocket field card: `/shop/drum-sander/pocket/` · `/walter/pocket`
- **Viewer app (phone):** `/shop/drum-sander/view/` · `/walter/view` — 3D parts + swipeable plans, Add to Home Screen
- **Shop pack (ZIP):** `/shop/drum-sander/pack/WALTER-DS16-RevB.zip` · `/walter/pack`
- Plans: `D1` … `D12` in `/shop/drum-sander/plans/`
- Interactive 3D: `/shop/drum-sander/model/` · `/walter/model`
- OpenSCAD: `cad/walter_ds16.scad` (includes generated `parameters.scad`)
- Fabrication dump: `cad/fabrication.json` · `pack/parts.csv` · `pack/joints.csv`
- Isometric renders: `renders/iso_assembled.svg` etc.

On this branch a Netlify deploy of the **repo** opens WALTER at `/` (not the old BEDROCK finance homepage). Bookmark `/walter/view` for the phone viewer.

## Spec (Rev B)

| Item | Value |
|------|-------|
| Capacity | 15.5″ wide · 1/16″–3″ thick |
| Quality | \|A−B\| ≤ 0.003″ paper-on · TIR ≤ 0.002″ |
| Drum | ⌀5″ × 15.75″ @ ~1035 RPM |
| Lift | Dual ½-10 Acme, chain-coupled, left clutch + home dog |
| Table | Torsion box in UHMW ways + phenolic/MIC-6 |
| Hold-downs | Infeed/outfeed rollers 0.030″ below drum |
| Oscillator | Optional ⅛″ @ ~80 cpm (not drum RPM) |
| Ways | UHMW let into a 0.52″ rebate, projecting 0.23″ (table fits) |
| Stretchers | P-003 housed ¼″ · finished 17″ |
| Ply note | Keep 16.5″ (419 mm) inner span; 18 mm Euro BB is fine |

SSOT: `cad/walter_ds16.py`. Change a parameter, regenerate. Do not duplicate 16.5 / 18.5 / 14 in drawings.

## Regenerate plans

```bash
python3 scripts/gen_drum_sander_plans.py
python3 scripts/gen_drum_sander_iso.py
python3 scripts/pack_drum_sander.py
```

Parametric source: `cad/walter_ds16.py` · OpenSCAD: `cad/walter_ds16.scad`

## Sources

- https://woodgears.ca/reader/walters/drum_sander.html
- https://youtu.be/W-5Sj6kBVic
- https://woodgears.ca/sander/drum.html
- https://woodgears.ca/sander/plans/
