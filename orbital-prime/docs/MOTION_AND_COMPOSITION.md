# MOTION AND COMPOSITION — Orbital Prime

Binding. Inventory is the law. Nothing else may move.

## A. Motion personality

Precise, mechanical, weighted. The plate has mass. Values settle like a needle finding a stop. The only continuous system is the radar sweep on the sky plot — a scan, not a celebration. Everything else is discrete: appear, settle, hold. No bounce. No elastic. No stagger of twenty fades.

## B. Easing tokens

| Name | cubic-bezier | When |
|---|---|---|
| `--ease-settle` | `0.16, 1, 0.3, 1` | Gauges, FACE, compass, section reveal, depth toast |
| `--ease-track` | `0.4, 0, 0.2, 1` | Hero depth, AR path length |
| `--ease-linear` | `linear` | Radar sweep only |

## C. Duration tokens

| Name | ms | When |
|---|---|---|
| `--dur-xs` | 80 | Tick, gate pip |
| `--dur-sm` | 160 | Depth toast, focus |
| `--dur-md` | 280 | Gauge settle, FACE, compass |
| `--dur-lg` | 480 | Section reveal, hero depth, AR path |

## D. Allowed animated properties

`transform` and `opacity` only, plus `canvas` redraws for plot/track/AR (those are measurement, not CSS motion).

Forbidden: `top/left` animation, blur, filter, box-shadow pulses, width/height tweens, bounce easings.

## E. Motion inventory (12)

| id | trigger | element | purpose | reduced-motion fallback |
|---|---|---|---|---|
| M01 | scroll | `.hero-plate` | Keep the nameplate behind the incoming cluster (depth, not decoration) | Static plate; no translate |
| M02 | section enter | `.surface` | Orient: the next job (measure/decide) arrives as a settle | Instant opacity 1; no transform |
| M03 | plot visible | sky-plot sweep | Measurement: the plot is live and scanning | Static 12-o’clock hairline; no rAF |
| M04 | ISS sample | lock pip | Measurement: station position on the plot | Snap to new coordinates |
| M05 | heading / AZ | compass needle | Orientation: where to turn | Snap rotation |
| M06 | ISS lock | AZ / EL / RANGE / MAG | Measurement: values find their stop | Instant text update |
| M07 | depth change | `#depth-toast` | Orientation: density mode named | Instant text; no slide |
| M08 | weather class | gate pip | Decision: go / caution / no-go changed | Instant class swap |
| M09 | next pass < 10 min | next-pass row | Orientation: imminent window | Instant “IMMINENT” label |
| M10 | AR ready + ISS | HUD path | Measurement: trajectory on glass | Static polyline, no dash offset |
| M11 | ISS sample | ground-track pip | Measurement: sub-satellite point | Snap; no trail tween |
| M12 | look-angle update | FACE line | Orientation: the spoken command | Instant text; no fade |

If any of these were removed, orientation or measurement would suffer. No thirteenth moment.

## F. Signature interaction storyboard

1. Observer sets location (GPS, manual, or Buffalo). Plate shows GATE from weather.
2. ISS lock arrives. AZ / EL / RANGE / MAG settle. Sky-plot pip appears.
3. FACE line states the bearing in words (cardinal + elevation + fist rule).
4. Compass needle eases to the FACE azimuth. Observer turns to match.
5. If HTTPS camera is available, AR path draws the same bearing on the glass; otherwise HUD-only copy remains the source of truth.

## G. Composition rules

**390px**

- Header is a single rail: wordmark left, depth 1–4 right. Location sits under the rail, not in a hamburger.
- Hero is a nameplate, not a 100vh takeover. Max ~72vh. Horizon hairline. One sentence. One jump control to `#cluster`.
- Cluster is the object. Full width minus 16px gutter. FACE is the largest verbal element on the plate.
- Sky plot is square-ish, min 280px, width 100% of plate. Canvas = parent client size.
- Page sections (Physics, Starship, Live, Manifest, AR) stack as full-width plates, not a card grid.
- No sticky overlay that covers FACE.

**900px+**

- Header rail can include location inline.
- Cluster becomes the three-zone instrument in the freeze (command | plot | secondary).
- Plot is the large center well (min 420px).
- Page sections become a 2-column reading layout (display stamp + body/data). Never 3 equal cards.

## H. Depth 1–4 (exact)

| Depth | Visible | Hidden |
|---|---|---|
| 1 Signal | Header, hero, GATE, NEXT pass, FACE, footer | All `.d2`, `.d3`, `.d4` |
| 2 Measure | Depth 1 + AZ, EL, RANGE, MAG, sky plot | All `.d3`, `.d4` |
| 3 Decide | Depth 2 + compass, hourly, pass list, radar | All `.d4` |
| 4 Full | Everything: Kp, ground track, Physics, Starship, Live, Manifest, AR | Nothing in-scope |

Default: depth 2 (enough to measure without drowning a phone). Persist in `localStorage` key `op-depth`.
