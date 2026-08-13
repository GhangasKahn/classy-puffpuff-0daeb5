# MARTIN Build App

Interactive visual front end for the 143″ × 65″ Prairie removable fence.

**Live (after Netlify deploy):** `/fence/martin/app/` · shortcuts `/martin/app` · `/build` · fabrication `/fence/martin/fab/` (`/martin/fab`)

## Features

- **Walk** — visual 5-phase journey (Mill → Base → Timber → Gate → Finish) with SVG scenes
- Exploded fence visualization with part inspector
- End-to-end checklist synced to Walk progress (localStorage)
- Mill-stock BOM (~322 bf buy) + finished cut list after re-dimension
- Japanese no-nail joinery vocabulary
- Gallery lightbox for renders + M-1…M-8 blueprints
- Owner tool list, tolerances, and grain/warpage rules
- Fabrication tab: kernel Part IDs, joints, QA, shop drawings (`fab.json`) — parallel package from `main`
- Site drafts (drop-off, gray swatch, latch mode) + JSON export
- Downloads: FreeCAD, STEP, STL, plans, report, fabrication package
- Installable PWA (manifest + service worker)

## Sources of truth (unresolved dual SSOT)

This branch’s **shop authority** for mill-stock / owner-tool plans is:

`../fab/martin_ssot.py` → `martin.json` and mill CSVs. Do not hand-edit those outputs.

`main` independently added `../martin_kernel.py` (hardware-store SPF nest) which generates `fab.json` and additional `../fab/` drawings via `scripts/export_martin_fab.py`. Do not treat the two BOMs as one list (≈322 bf mill buy vs ≈196/225 bf kernel nest). Unify before running both exporters in one pass — they share CSV paths.

## Local

```bash
# from repo root
python3 -m http.server 8080
# open http://localhost:8080/fence/martin/app/
```

## Stack

Static HTML/CSS/JS — no build step, no backend. Same Netlify publish root as the rest of the monorepo.
