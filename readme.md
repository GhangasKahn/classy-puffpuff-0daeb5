# BEDROCK — Integrated Site

A complete, self-contained website:

- `index.html` — the public **landing page** (the marketing front door)
- `app/` — the **BEDROCK application**, an installable PWA (the terminal you actually use)
- `fence/` — the **fence design suite**: MARTIN (143×65 removable Prairie + Japanese joinery for Buffalo), HASHIRA (joinery guide), STELE (masonry + timber), and the engineering report at `/fence/report/`
- `scripts/` — CAD pipelines (`build_martin.sh`, `build_stele.sh`, `render_hashira_cad.sh`, plan generators)
- `netlify.toml` — server headers + redirects for Netlify (`/martin`, `/stele`, `/report` shortcuts included)

## What this is — and isn't
This is the complete **front-end** product: a marketing site plus an installable, offline-capable
finance app that runs entirely in the browser. Your data stays on your device — no backend, no
database, no account, nothing collected. Features that require a server (bank/brokerage linking via
Plaid, live balance sync, multi-device sync, hardware 2FA) are a separate, future **backend phase**.
Hosting this on Netlify does not add them.

## Deploy — drag & drop (about 60 seconds)
1. Go to https://app.netlify.com/drop
2. Drag this entire `bedrock-deploy` folder (or its contents) onto the page.
3. Netlify returns a live URL like `https://your-name.netlify.app` (HTTPS is automatic).
4. Optional: Site settings → rename the site, or attach a custom domain.

## Deploy — via Git (for ongoing updates)
1. Push this folder to a GitHub repo.
2. Netlify → Add new site → Import from Git → choose the repo.
3. Build command: leave empty. Publish directory: `.` (or the folder name if nested).
4. Every push auto-deploys.

## Install on your phone
1. Open your Netlify URL on the phone; tap **Enter** to reach `/app/`
   (or go directly to `https://your-url.netlify.app/app/`).
2. Android Chrome: menu ⋮ → **Add to Home screen / Install app**.
   iOS Safari: Share → **Add to Home Screen**.
3. It installs as a standalone app and works **offline after the first load**.

## Notes
- First load needs internet (React, GSAP, fonts); the service worker then caches everything for offline use.
- The light/dark theme you choose on the landing page **carries into the app** — same origin, shared setting.
- AI features are bring-your-own-key: paste your provider key in the app's Config. Nothing is sent anywhere else.
- This is research/educational tooling you run yourself. **Not financial advice.**

## PWA Icons (optional)
The manifest and apple-touch-icon references have been cleaned for direct upload (no missing file errors).
To get custom icons on install/home screen:
- Add `icon-192.png` (192x192) and `icon-512.png` (512x512) PNG files to the `app/` folder.
- Re-upload or trigger a new deploy.

This package includes the full optimized front-end with:
- Easy setup (income frequency dropdowns, quick-start templates, progressive help for all skill levels)
- Expanded Vault with live comps support for watches, cards, spirits, cars, metals, and more
- LIVE market data tab with multi-source alt asset comps (WatchCharts-style, PSA/eBay, etc.)
- All previous features (Quant/MC, goals, coach/agents, etc.)

Upload the `bedrock-deploy` folder directly. The landing is at root; the terminal ("Enter the Dojo") is at /app/.
