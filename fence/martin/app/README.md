# MARTIN Build App

Interactive front end for the 143″ × 65″ Prairie removable fence.

**Live (after Netlify deploy):** `/fence/martin/app/` · shortcuts `/martin/app` · `/build` · fabrication `/fence/martin/fab/` (`/martin/fab`)

## Features

- Overview + winter knock-down sequence
- Exploded SVG visualization with part inspector
- 12-step assembly checklist (localStorage progress)
- Materials / board-feet shopping checklist (196 bf net / 225 bf procurement from kernel nest)
- Fabrication tab: Part IDs, joints, QA, shop drawings (`fab.json`)
- Japanese joinery vocabulary
- Gallery lightbox for renders + M-1…M-6 blueprints
- Site drafts (drop-off, gray swatch, latch mode) + JSON export
- Downloads: FreeCAD, STEP, STL, plans, report, fabrication package
- Installable PWA (manifest + service worker)

## Source of truth

`../martin_kernel.py` generates `fab.json` and `../fab/` via `scripts/export_martin_fab.py`. Do not hand-edit those outputs.

## Local

```bash
# from repo root
python3 -m http.server 8080
# open http://localhost:8080/fence/martin/app/
```

## Stack

Static HTML/CSS/JS — no build step, no backend. Same Netlify publish root as the rest of the monorepo.
