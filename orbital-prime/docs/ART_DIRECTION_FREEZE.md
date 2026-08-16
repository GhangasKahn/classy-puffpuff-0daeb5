# ART DIRECTION FREEZE — Orbital Prime

Binding. Not a moodboard. Implement against this document.

## 1. Governing concept

The instrument between you and the sky.

## 2. Emotional register

Nocturnal. Mechanical. Consequential.

## 3. Anti-references

- Dark SaaS dashboards (charcoal cards, purple/cyan accents, “LIVE” pill farms)
- Space-agency comms sites and Earth-from-orbit wallpaper
- Consumer planetarium apps (candy constellations, playful globes)
- Cyberpunk HUD cosplay (scanlines, glitch, neon grids)
- AI-generated “space” heroes (gradient orbs, particle starfields, glassmorphism)

## 4. Color tokens

| Token | Hex | Usage rule |
|---|---|---|
| `--void` | `#070806` | Page ground. Olive-black, never blue-black. |
| `--ink` | `#10110E` | Instrument plate. |
| `--steel` | `#1C1E16` | Recessed wells only (gauges, plot). |
| `--hairline` | `#2E3026` | Engraved rules. 1px. No soft shadows as structure. |
| `--paper` | `#E6E1D4` | Primary reading text. |
| `--dim` | `#9A9486` | Secondary labels. Must remain AA on `--ink`. |
| `--faint` | `#6E6A5E` | Captions, inactive ticks. Not body copy. |
| `--phosphor` | `#D4C48A` | Gauge numerals only. |
| `--signal` | `#FF6A00` | Signal only. Lock pip, active depth, PERFECT tick, focus ring. Never a fill larger than a control. |
| `--perfect` | `#C8D4A4` | Weather/pass go. Dusty optic, not neon green. |
| `--marginal` | `#D4B46A` | Weather/pass caution. |
| `--obstructed` | `#B45A48` | Weather/pass no-go. |
| `--focus` | `#FF6A00` | 2px offset ring on interactive controls. |

Orange budget is a hard cap, not a brand wash. If a surface is orange, it is wrong.

## 5. Type system

**Roles**

- Display — instrument nameplate. Big Shoulders Display. Weight 800. Uppercase allowed only for the wordmark and section stamps. Never for paragraphs.
- Body — field notes. Source Serif 4. Weight 400 / 600. Sentence case. This is the human voice.
- Data — measured values. IBM Plex Mono. Weight 400 / 500. Tabular lining figures. Never for marketing sentences.

**Families (web + system-safe)**

- `"Big Shoulders Display", "Arial Narrow", "Helvetica Neue Condensed", Impact, sans-serif`
- `"Source Serif 4", "Iowan Old Style", "Palatino Linotype", Palatino, serif`
- `"IBM Plex Mono", ui-monospace, "Cascadia Mono", Menlo, monospace`

**Scale**

| Role | 390px | 1200px |
|---|---|---|
| Display hero | 64px / 0.86 lh / -0.02em | 120px / 0.82 lh / -0.03em |
| Display section | 36px / 0.92 lh | 56px / 0.9 lh |
| Body | 17px / 1.5 / 0 | 19px / 1.5 / 0 |
| Label (display at small size) | 11px / 1.2 / 0.16em | 12px / 1.2 / 0.18em |
| Data primary (AZ/EL) | 40px / 1 / 0 | 56px / 1 / 0 |
| Data secondary | 15px / 1.25 / 0 | 16px / 1.25 / 0 |

**Tracking / measure**

- Body measure: 36–58ch. Never full-bleed paragraphs.
- Data: tracking 0. Labels: +0.16em to +0.22em.
- No italic display. Body italic only for formula names and source credits.

## 6. Grid & spacing

- Base unit: 8px.
- Page gutter: 16px at 390 / 32px at 1200.
- Section padding-block: 48px at 390 / 80px at 1200.
- Cluster internal rhythm: 8px between engraved zones; 16px before FACE command.
- Max page width: 1120px. Cluster may go full-bleed to 1200.
- Radius: 0 on the plate. 2px only on tiny status chips. No 16px “cards.”

## 7. Cluster geometry

One plate. Not three cards. Shared rails. Recessed wells.

**390px**

```
┌─────────────────────────────────┐
│ GATE  [PERFECT|MARGINAL|OBSTR.] │  weather now
│ NEXT  21:14  ·  NAKED-EYE       │  next pass
├─────────────────────────────────┤
│ FACE                            │
│ SOUTHWEST · EL 41° · FOUR FISTS │  command line
├──────────────┬──────────────────┤
│ AZ  247.3°   │ EL   41.0°       │  d2+
├──────────────┴──────────────────┤
│           SKY PLOT              │  d2+  full width
│        (never collapsed)        │
├──────────────┬──────────────────┤
│ RANGE  890km │ MAG  −1.8 EST    │  d2+
├──────────────┴──────────────────┤
│ COMPASS  +  Kp                  │  d3+
├─────────────────────────────────┤
│ HOURLY CROSS-CHECK              │  d3+
│ PASS LIST                       │  d3+
│ RADAR WELL                      │  d3+
│ GROUND TRACK                    │  d4
└─────────────────────────────────┘
```

**900px+**

```
┌────────────┬──────────────────────┬────────────┐
│ GATE       │                      │ RANGE      │
│ FACE       │      SKY PLOT        │ MAG        │
│ AZ    EL   │      + sweep         │ COMPASS    │
│ NEXT       │                      │ Kp         │
├────────────┴──────────────────────┴────────────┤
│ HOURLY · PASSES · RADAR · GROUND TRACK (d3/d4) │
└────────────────────────────────────────────────┘
```

Sky plot and ground track size from the parent. Never a 0×0 canvas. Never a third equal card.

## 8. Orange budget rule

Count orange pixels after paint. They must be ≤10% of the viewport.

Allowed orange: lock pip on the plot, active depth numeral, PERFECT pip (not the whole gate bar), focus ring, the single hero hairline tick.

Forbidden orange: backgrounds, hero washes, button fills, decorative rules, logo marks larger than 24px.

## 9. Imagery rule

- Hero subject: the instrument plate itself against void — a horizon hairline, stamped type, one lock pip. The sky is implied by darkness and the horizon, not illustrated.
- No photograph required. If an asset is added later, it must be a real night horizon (rights-cleared), cropped as a working surface, not a poster.
- Forbidden subjects: Earth globe, nebula, rocket launch, astronaut visor, CGI ISS, particle starfields, gradient orbs.

## 10. What “done” looks like (binary)

- [ ] Logo removed: still recognizably this instrument (serif notes + condensed plate + FACE command).
- [ ] Orange occupies signal marks only; no orange panel fills.
- [ ] Cluster is one plate; no three-equal-card stack.
- [ ] 390px authored: no horizontal scroll; FACE readable without pinch-zoom.
- [ ] No blue-black, no purple, no glass blur, no particle field.

---

Self-critique (closed in this freeze, not left as homework):

1. Dark + orange is every crypto UI → closed by olive-black void, serif body, orange cap.
2. Mono-everything reads as hacker HUD → closed by serif notes; mono is numerals only.
3. Gauge “cards” recreate a dashboard → closed by one plate + recessed wells.
4. Space photo hero is NASA wallpaper → closed by typographic instrument, no poster image.
5. Pulsing LIVE dots are template residue → closed; liveness is a mechanical tick and a timestamp, not a blob.
