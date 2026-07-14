# BEDROCK — Integrated Site

Deployable web root for the monorepo (`site/`).

- `index.html` — public landing page
- `app/` — installable PWA (the terminal)
- `netlify.toml` — headers + redirects (also mirrored at repo root)

For the full project map, see the root `README.md`. Backend sync is optional and lives
in `../backend/` — this front-end runs fully offline without it.

## Deploy

**From monorepo root (preferred):** Netlify publish directory = `site`.

**From this folder:** publish directory = `.` (drag-and-drop or Git subdirectory).

## Install on phone

Open `/app/` → Add to Home Screen. Works offline after the first load.

Research/educational tooling. **Not financial advice.** The app never moves money.
