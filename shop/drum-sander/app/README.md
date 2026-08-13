# WALTER DS-16 Build app

PWA for the shop: assembly checklist, calibration, materials, plan sheets, and phone downloads.

## Phone save

Safari often opens SVG instead of downloading. Use:

- **ZIP** in the top bar, or Files → Download ZIP / Share to Files
- Pocket card at `/walter/pocket` — Add to Home Screen or Print → PDF
- After one visit on Wi-Fi, the service worker caches D-1…D-10 for offline

## Regenerate

From the repo root:

```bash
python3 scripts/gen_drum_sander_plans.py
python3 scripts/gen_drum_sander_iso.py
python3 scripts/pack_drum_sander.py
```
