# MARTIN Build App

Interactive visual front end for the 143″ × 65″ Prairie removable fence.

**Live (after Netlify deploy):** `/fence/martin/app/` · shortcuts `/martin/app` · `/build`

## Features

- **Walk** — visual 5-phase journey (Mill → Base → Timber → Gate → Finish) with SVG scenes
- Exploded fence visualization with part inspector
- End-to-end checklist synced to Walk progress (localStorage)
- Mill-stock BOM (~322 bf buy) + finished cut list after re-dimension
- Japanese no-nail joinery vocabulary
- Gallery lightbox for renders + M-1…M-8 blueprints
- Owner tool list, tolerances, and grain/warpage rules
- Site drafts (drop-off, gray swatch, latch mode) + JSON export
- Downloads: FreeCAD, STEP, STL, plans, report
- Installable PWA (manifest + service worker)

## Local

```bash
# from repo root
python3 -m http.server 8080
# open http://localhost:8080/fence/martin/app/
```

## Stack

Static HTML/CSS/JS — no build step, no backend. Same Netlify publish root as the rest of the monorepo.
