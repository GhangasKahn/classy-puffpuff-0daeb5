# Aegis Air — Cinematic Landing (source)

The front door for the Aegis Air instrument app, built with the Atelier Protocol
(`prompts/ATELIER-PROTOCOL.md`): React 19 + Vite + Tailwind 3.4 + GSAP/ScrollTrigger.

- **Brand psyche:** Sage primary (evidence-forward, measured), Ruler shadow
  (control over an uncontrollable sky). Emotions: Trust-Calm, then Power-Control.
- **Signature moment:** the hero smoke field is a canvas particle system whose
  drift follows the *real* current wind and whose density follows the *real*
  PM2.5 (same Open-Meteo/CAMS models the app reads). The cursor parts the smoke.
- **Persuasion arc:** desire (hero) → evidence (live readouts, artifacts, record)
  → belief (manifesto) → objections (accusation audit) → honesty (confession)
  → the ask. All claims trace to the real app's real behavior.

## Develop

```bash
cd aegis-landing
npm install
npm run dev
```

## Build & deploy

```bash
npm run build   # outputs to ../aegis/ (committed — Netlify serves it at /aegis)
```

The live page fetches current conditions for the app's default location
(Buffalo, NY) directly from Open-Meteo; no keys, no backend.
