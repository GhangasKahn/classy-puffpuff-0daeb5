# WALTER DS-16 — Design basis (fab B.4)

**Release state: FABRICATION REVIEW · risk class R3.**

This is a powered shop machine with a ⌀5″ drum at ~1035 RPM. Geometry and
joinery are internally reconciled. Two things are deliberately not released:
mains electrical work, and the flange bolt circle (ASSUMED until the purchased
bearing is transferred to the panel).

## Controlling dimensions (do not “fix” these to suit the ply)

| Parameter | Value | Evidence |
|---|---|---|
| Capacity width | 15.5″ | VERIFIED |
| Inner span | 16.5″ / 419 mm | VERIFIED — keep even if ply is 18 mm |
| Drum | ⌀5″ × 15.75″ @ ~1035 RPM | VERIFIED / CALC-001 |
| Table | 16″ × 22″ torsion box | DERIVED |
| Parallel spec | \|A−B\| ≤ 0.003″ paper-on | VERIFIED |
| Drum TIR | ≤ 0.002″ paper-off | VERIFIED |

`ply_actual` is USER_MEASURE. Change it in `cad/walter_ds16.py` and regenerate.
Do not shrink the inner span.

## Layout protocol — HYBRID

Primary layout system: **HYBRID**.

- **Face/edge** on the plywood panels: DATUM-A bottom, DATUM-B infeed,
  DATUM-C inner face. Dados, screw pilots, and panel size originate here.
- **Centerline** for the three working planes: drum axis, both Acme screws,
  vertical ways, table midplane. All share Y = side_depth/2 from DATUM-B.
  Vertical locations originate from DATUM-A.

Do not mix a face measurement with a centerline measurement without converting.
See `planforge/centerline-layout-protocol.md`.

## Three planes

1. **Table** — lifting carriage. Vertical captured UHMW ways (P-007) plus
   shoes (P-017) constrain X and Y. Dual ½-10 Acme on the drum centerline
   (left/right X, one Y) lift in Z. Operator feeds the workpiece. There is
   no conveyor.
2. **Drum axis** — pack-bored discs, drive flange FIXED (J-006), idler
   FLOATING axial on a UHMW pad (J-007). True, wrap, re-clock.
3. **Feed** — hold-down rollers 0.030″ below the drum, paper on.

## Mechanics that B.4 repaired

- Stretchers at Z = 6 / 12 / 20 put a rail through the table at max opening.
  Stations are now IN-LO, OUT-LO, OUT-HI. Rails stand on edge. CALC-004
  requires ≥ 0.25″ Z clearance to the table envelope.
- Horizontal ways at Z = 10 never supported the table at operating height
  (11.5–15.9″). Ways are now a vertical strip covering table travel.
- “Dual-end” Acme was drawn as infeed/outfeed Y. Dual-end means left/right
  X, both at drum CL Y, so cutting force goes through the nuts.

`validate_mechanics()` runs on every regeneration.

## Joinery on this machine

This is a Baltic birch box, not a timber frame. Housed dados (J-001) plus
screws carry racking. Japanese mortise-and-tenon / drawbore from the
Planforge timber standards is **not** applied to plywood sides. See
`planforge/joinery-and-tolerance-standards.md` and Q-102.

## Conditions before real work

1. Transfer the purchased 4-bolt flange before drilling. BCD is ASSUMED.
2. Measure `ply_actual` and regenerate. Keep 16.5″ inner span.
3. Motor circuit, switch, grounding, cord: qualified electrician and local
   code. Not released by this package.
4. Commission with the hood on and no stock, standing clear of the drum ends.
5. Confirm TIR, \|A−B\|, and witness-board scatter before using real work.
