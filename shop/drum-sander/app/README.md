# DS-18 Shop Drum Sander — Build App

Interactive front end for an 18″ open drum sander (6″ OD drum, 36×22×28″ plywood cabinet, 1.5 HP).

**Live (after Netlify deploy):** `/shop/drum-sander/app/` · `#overview` · shortcuts `/shop` · `/drum-sander`

The live URL that 401'd (`/shop/drum-sander/app/#overview`) had no files in the repo. This app is that page.

## Features

- Overview is **visible without JavaScript** (`class="panel on"` + `<noscript>` shows every panel)
- Hash routing: `#overview` `#viz` `#assembly` `#cutlist` `#shop` `#plans` `#files`
- Three.js parametric model (orbit, explode, pick, spinning drum, table height) from the jsDelivr CDN
- Isometric SVG fallback if the CDN is blocked
- 12-step assembly checklist (localStorage)
- Nested plywood cut list + hardware shopping list with running totals
- DS-1…DS-6 SVG plan sheets
- OpenSCAD parametric CAD (`cad/drum_sander.scad`)
- Installable PWA (manifest + service worker)

## Local

```bash
# from repo root
python3 -m http.server 8080
# open http://localhost:8080/shop/drum-sander/app/#overview
```

Regenerate plan sheets:

```bash
python3 scripts/gen_ds_plans.py
```

## Stack

Static HTML/CSS/JS — no build step, no backend. Three.js loaded as ES modules via import map. Same Netlify publish root as the rest of the monorepo.

## Safety

Hobby machine, not UL listed. Magnetic switch, dust collection ≥ 350 CFM, 1/32″ max hardwood take.
