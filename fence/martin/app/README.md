# MARTIN Build App

Interactive front end for the 143″ × 65″ Prairie removable fence.

**Live (after Netlify deploy):** `/fence/martin/app/` · shortcuts `/martin/app` · `/build`

## Features

- Overview + winter knock-down sequence
- Exploded SVG visualization with part inspector
- End-to-end assembly checklist with mill phase (localStorage progress)
- Mill-stock BOM (~322 bf buy) + finished cut list after re-dimension
- Japanese no-nail joinery vocabulary
- Gallery lightbox for renders + M-1…M-8 blueprints
- Owner tool list, tolerances, and grain/warpage rules (Festool / Bridge City / Zenwu)
- Site drafts (drop-off, gray swatch, latch mode) + JSON export
- Downloads: FreeCAD, STEP, STL, plans (incl. M-7 shop method), report
- Installable PWA (manifest + service worker)

## Local

```bash
# from repo root
python3 -m http.server 8080
# open http://localhost:8080/fence/martin/app/
```

## Stack

Static HTML/CSS/JS — no build step, no backend. Same Netlify publish root as the rest of the monorepo.
