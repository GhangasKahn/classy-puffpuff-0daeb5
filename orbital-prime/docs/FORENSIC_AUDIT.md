# FORENSIC AUDIT — Orbital Prime / OP-01

**Status:** NOT complete at an igloo.inc / Abeto+Bureaux bar.  
**Date:** 2026-08-16  
**Method:** Zero-trust. Claims checked against files on disk, git, live HTTP, and WCAG contrast math. No self-score. Prior `docs/AUDIT.md` is **void** — it grades an olive-black HUD that is no longer the CSS.

This document exists because “done / god-tier / production for everyone” was overclaimed.

---

## 0. Verdict in one paragraph

OP-01 is a **single-page vanilla JS field instrument** (~3.4k lines of first-party code, one SVG favicon, no 3D, no Blender, no game, no CI, not on `main`). It **does** talk to real public ephemeris and weather. It is **not** a multi-month multi-studio interactive product. Comparing it to [Igloo Inc](https://www.awwwards.com/igloo-inc-case-study.html) (Abeto + Bureaux: Houdini, Blender, Three.js, Svelte, GSAP, Vite, custom VDB exporter, procedural ice, WebGL UI, DaVinci sound) is a **category miss**. We are not at that level. We are not finished if that is the bar.

---

## 1. Comparison bar (retrieved, not invented)

**Igloo Inc (igloo.inc)** — parent of Pudgy Penguins. Landing built by **Abeto** with **Bureaux**. Public case study 2024-10-31 (Awwwards).

| Layer | Igloo Inc (case study) | OP-01 (this repo) |
|---|---|---|
| Studios | Abeto + Bureaux + client moodboards/renders | One agent, ~10 commits on `orbital-prime/` |
| 3D | Houdini + Blender; procedural ice growth; volume/VDB | **Zero** `.blend` / `.glb` / `.gltf` / `.fbx` |
| Runtime 3D | Three.js, custom shaders, mesh BHV, WebGL UI | **2D canvas only** (`getContext("2d")`) |
| Motion | GSAP + in-engine realtime intro + particle sim | One CSS `@keyframes` (disc spin) + rAF sweep |
| App shell | Svelte + Vite | One `index.html`, no bundler, no TS |
| Sound | DaVinci-authored music/SFX | Optional WebAudio blips, muted by default |
| Design source | Figma, Photoshop, Affinity | No Figma/PSD in repo |
| Game | Abeto builds web games; Igloo has interactive volumes | **Not a game.** No loop, no levels, no engine |

Sources: Awwwards “Igloo Inc: Case Study”; Okay Dev / Abeto credit list. Not independently re-run as a lab.

---

## 2. Inventory (files on disk)

First-party (excluding `vendor/satellite.min.js`):

| Path | Role | Lines (approx) |
|---|---|---|
| `js/render.js` | UI bind + canvas + feeds paint | 1134 |
| `styles/orbital.css` | Entire visual system | 824 |
| `index.html` | One page | 353 |
| `js/astro.js` | Look angles, SGP4 helpers, TLE parse | 301 |
| `js/main.js` | Boot | 162 |
| `js/feeds.js` | Public HTTP client | 109 |
| `js/motion.js` | Scroll/IO/rAF | 99 |
| `js/score.js` | Hand logistic | 95 |
| `js/audio.js` | Click tones | 50 |
| `netlify/functions/op-feed.js` | Allowlisted proxy | 125 |
| `netlify/functions/op-health.js` | Upstream ping | 45 |
| `test/*.mjs` | 11 assertions | 126 |
| **Total first-party** | | **~3423** |

**Absent:** TypeScript, bundler, lockfile of app deps (none), Storybook, Chromatic, Playwright in CI, `.github/workflows`, design tokens file, icon set beyond one 32×32 SVG, raster brand kit, 3D, video, Lottie, game assets.

**Git:** `orbital-prime/` is **not on `origin/main`**. Production Netlify of `main` does not ship this app until PR #11 merges.

---

## 3. Claim ledger (zero-lie)

| ID | Claim that was made or implied | Type | Verdict | Evidence |
|---|---|---|---|---|
| C1 | “God-tier / igloo.inc complete” | aspirational | **FALSE** | See §1. No Houdini/Blender/Three/GSAP/Svelte. |
| C2 | “Months of work, dozens of devs” equivalent | inference | **FALSE** | ~10 commits touching `orbital-prime/`. One working tree. |
| C3 | “Full stack production” | mixed | **PARTIAL** | Static PWA + two Netlify functions. No DB, no auth, no queue, no observability. |
| C4 | “ML/AI integration” | overclaim | **FALSE as ML product** | `score.js` is a **hand-set logistic prior**. Coefficients are comments, not fitted on a dataset. No training loop, no model file, no eval set. |
| C5 | “Usable by other users” | capability | **PARTIAL** | Deploy preview URLs are public. **Not on production `main`.** No accounts (intentional). Share `?lat&lon&sat` exists. |
| C6 | “Live feeds, no mock data” | demonstrated | **TRUE with gaps** | Live tests hit ISS, Celestrak TLE, Open-Meteo, RainViewer, SWPC. Starship NAME query **404 is real empty**. Browser CORS can delay/fail Celestrak until `op-feed` is on Netlify. |
| C7 | `docs/AUDIT.md` rubric mean 8.6 | stale / false | **VOID** | Text describes “olive void, serif FACE, horizon hairline” — **not** current cream TE CSS. Scoring a deleted design. |
| C8 | Motion grammar fully implemented | docs vs CSS | **FALSE** | `--ease-settle`, `--dur-*` are **only in markdown**. CSS has no those tokens. JS adds `.is-settle` / `.is-pending` / `.is-in` — **no CSS rules** for those classes. Section reveal is a no-op. |
| C9 | “™” on OP-01 | graphic | **Unverified mark** | Decorative. No trademark filing in repo. Do not imply registered IP. |
| C10 | Blender / game design / generated animation studio | user ask | **ABSENT** | `find` for blend/glb/gltf/fbx/mp4/webm/lottie: **none** under the project. |
| C11 | Orange as signal ≤10% (constitution P6) | policy | **UNMEASURED** | No pixel budget script. TE disc is orange fill. Not counted. |
| C12 | Accessibility “design requirement” (P9) | policy | **PARTIAL FAIL** | Skip link exists. `#ff5a00` on `#f2ede4` contrast **2.68:1** (fails AA for text). Mute `#6b6458` on paper **5.02:1** (AA ok). Gate green **4.63:1** (AA large only). No `focus-visible` ring on most controls (`outline: none` on inputs). Google Fonts third-party. |

---

## 4. Source code (hostile)

**What is real**

- WGS-84 look angles, SGP4 via vendored satellite.js 5, TLE parse, eclipse cylinder, magnitude estimate, 36h ≥10° passes.
- ISS lock from `api.wheretheiss.at` (CORS `*`). Residual vs SGP4 when TLE loads.
- Weather classification from Open-Meteo numbers, not copy.
- Allowlisted proxy (not an open proxy). SW does not cache live hosts.

**What is weak**

- No TypeScript, no module graph test in CI, no visual regression.
- `import "...?v=4"` cache-bust is a smell: the SW/module cache was already a production defect.
- `findPasses` is O(hours × 30s) on main thread — can hitch on low-end phones. Not profiled.
- Magnitude formula is an **estimate** labeled EST. Honest. Not photometry.
- Logistic score will happily output 79 on a **DAY** pass — it is not a calibrated P(naked-eye). Calling it “ML” is a lie.
- Error handling is `catch` + status text. No retry budget UI, no offline ISS (correctly refused), no OpenTelemetry.
- `loc-status` historically assumed west longitude; hemisphere helper exists now — not fuzz-tested for ±180.

**Tech stack (literal)**

HTML + CSS + ES modules + Canvas 2D + Netlify Functions (Node CJS) + public HTTP.  
Not: React, Svelte, Three, WASM, Python backend, GPU compute, Blender pipeline.

---

## 5. Graphic / industrial design

**Intent (current freeze):** Teenage Engineering catalog × Off-White quotation graphics × brutalist rules. Cream `#F2EDE4`, ink `#111`, TE orange `#FF5A00`, yellow `#FFE600`, Archivo Black + Inter + Space Mono.

**Craft gaps vs that intent**

- No custom type, no drawn logotype, no hardware photography, no print grid spec beyond CSS.
- Encoder disc is an inline SVG, not a photographed OP-1, not a 3D turntable.
- Grain is a CSS noise SVG data-URI, not a graded plate.
- Google-hosted Inter/Archivo/Space Mono — not a licensed catalog face, not self-hosted `font-display` strategy beyond the Google CSS.
- Art direction freeze and `AUDIT.md` **contradict** each other (cream vs olive). Freeze is the later law; audit file was not rewritten to match.

**Color theory (computed, not vibes)**

| Pair | Contrast | AA normal text |
|---|---|---|
| ink on paper | 16.19 | Pass |
| yellow on ink | 14.90 | Pass |
| mute on paper | 5.02 | Pass |
| orange `#FF5A00` on paper | **2.68** | **Fail** |
| ok green on paper | 4.63 | Fail for small text |

Orange module numbers on cream fail WCAG for 10–12px labels.

---

## 6. Motion / animation / “generations”

| Documented (MOTION_AND_COMPOSITION.md) | Implemented |
|---|---|
| 12 named moments | Functions exist in JS |
| Easing tokens | **Missing from CSS** |
| M02 section settle | Class toggle **without CSS** → no animation |
| M06 value settle | `.is-settle` **without CSS** → no animation |
| M03 sweep | **Yes** (rAF, skipped if reduced-motion / hidden / offscreen) |
| M01 hero parallax | **Yes** (8% scroll, cap 28px) |
| TE disc spin | **Yes** (`te-spin` 48s linear); killed by `prefers-reduced-motion` blanket |
| Generated film / Lottie / Rive / Blender previs | **None** |

There is no animation “generation” pipeline. No Runway, no After Effects, no in-engine cinematic. Canvas redraws are instruments, not a motion system of igloo.inc class.

---

## 7. Game design

**Not a game.** No player, no fail state, no economy, no tick besides telemetry intervals (4s ISS, 10min weather, 1s clock). AR is a camera + heading overlay, not a spatial game. Do not list “game design” as shipped.

---

## 8. Tests & deploy

- `node --test`: 11 tests (6 unit + 5 live HTTP). **No CI** to run them on PR.
- Live tests can flake (Open-Meteo `fetch failed` observed once; retry added).
- No Lighthouse gate, no bundle budget, no 320/375/430/768/1024/1280/1440/1920 ledger as Siteforge requires.
- PR #11 can be used by anyone on **deploy preview**. **`main` does not contain this app.**

---

## 9. What would have to be true to call this “igloo.inc complete”

This is a gap list, not a promise of calendar time:

1. Real 3D/motion pipeline **or** an explicit product decision that OP-01 **refuses** WebGL spectacle (constitution currently forbids 3D Earth hero). Cannot have both “igloo ice shard” and “nothing tech / industrial paper” without a new freeze.
2. Design source of truth (Figma or equivalent) + token file that matches CSS + contrast AA on every color use.
3. Motion tokens in CSS; no dead classes.
4. Self-hosted fonts; `focus-visible`; keyboard audit; reduced-motion that still measures.
5. CI: unit + live canaries + visual snapshots + Lighthouse.
6. Merged to production domain.
7. Performance profile on a mid phone (pass search off main thread).
8. If “ML” remains in scope: a **fitted** model with a held-out set of real pass outcomes — or stop using the word ML.
9. If “game / Blender” remains in scope: that is a **different product** (cinematic or interactive 3D). It is not a CSS restyle of this page.

---

## 10. Honest remaining product

A **usable public ISS/station observer** on a PR preview, with live connectors and an industrial catalog look.

It is **not** finished as an igloo.inc-class interactive studio piece. Claiming otherwise was a lie. This file is the correction.

---

## 11. Kitchen-sink pass (same day, after this file)

Work that **did** ship after §0–10, checked against the tree — still not igloo:

| Gap from §9 | Status after this pass |
|---|---|
| Instrument-as-object 3D (not 3D Earth) | **Shipped.** `js/gl/unit.js` raymarches a cream-plastic encoder. Live AZ rotates the disc. Live EL sizes the orange sector. Pointer tilt is camera only. 2D canvas fallback of the same object. |
| Motion tokens + dead classes | **Shipped.** `--ease-settle` / `--dur-*` and `.is-pending` / `.is-in` / `.is-settle` are in `styles/orbital.css`. |
| Contrast of orange-as-text | **Mitigated.** Module numbers are ink on yellow. Imminent T-minus is ink on yellow. Orange remains fill (unit sector, scrub, quotation graphics). Quotation marks are decorative. |
| focus-visible + self-hosted fonts | **Shipped.** WOFF2 under `fonts/`. Google Fonts links removed. |
| Pass search hitch | **Mitigated.** `findPassesAsync` yields every 480 steps. Still main-thread SGP4, not a worker. |
| CI | **Shipped.** `.github/workflows/orbital-prime.yml` runs deterministic tests; live HTTP is `continue-on-error`. No Chromatic / Lighthouse gate. |
| Merged to `main` | **Still false.** |
| Fitted ML | **Still false.** `score.js` is a hand prior. |
| Houdini / Blender / GSAP / Svelte / Figma | **Still absent.** A compact raymarcher is not a studio pipeline. |

Do not read this section as “igloo-complete.” It is the list of closable holes that were closed, and the studio holes that were not.

