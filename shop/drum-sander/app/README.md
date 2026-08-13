# WALTER DS-16

Modern dedicated **drum thickness sander** build plans — ShopNotes No. 86 lineage via Ron Walters, redesigned as Rev A with a solid sliding table (no conveyor).

## Live paths

- Design overview: `/shop/drum-sander/`
- Build app: `/shop/drum-sander/app/` · shortcuts `/walter` · `/drum`
- Plans: `/shop/drum-sander/plans/D1_general.svg` … `D6_cutlist.svg`

## Spec (Rev A)

| Item | Value |
|------|-------|
| Capacity | 15.5″ wide · 1/16″–3″ thick |
| Drum | ⌀5″ × 15.75″ @ ~1035 RPM |
| Motor | ½ HP 1725 RPM · 3″/5″ pulleys |
| Frame | ¾″ Baltic birch · flange bearings |
| Feed | Solid laminated table + push sticks |
| Dust | Kerf-bent hood · 4″ port |

## Regenerate plans

```bash
python3 scripts/gen_drum_sander_plans.py
```

Parametric source: `cad/walter_ds16.py` · OpenSCAD preview: `cad/walter_ds16.scad`

## Sources

- https://woodgears.ca/reader/walters/drum_sander.html
- https://youtu.be/W-5Sj6kBVic
- https://woodgears.ca/sander/drum.html
- https://woodgears.ca/sander/plans/
