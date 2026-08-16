# WALTER DS-16 — Design basis (fab C.1)

**Release state: FABRICATION REVIEW · risk class R3.**

This is a powered shop machine with a ⌀5″ drum at ~1208 RPM. Geometry and
joinery are internally reconciled. The package is **not** fabrication-ready:
mains electrical work is not released, the flange bolt circle is ASSUMED until
the purchased bearing is transferred, bearing dynamic capacity C must be read
off vendor data, and McMaster-Carr part numbers are `CONFIRM AT ORDER`.

## Controlling dimensions (do not “fix” these to suit the ply)

| Parameter | Value | Evidence |
|---|---|---|
| Capacity width | 15.5″ | VERIFIED |
| Inner span | 16.5″ / 419 mm | VERIFIED — keep even if ply is 18 mm |
| Drum | ⌀5″ × 15.75″ @ ~1208 RPM | VERIFIED / CALC-001 |
| Shaft | 1¼″ × 24″ precision-ground | DERIVED — CALC-C01 failed ¾″ |
| Shell | 5.00″ OD × 0.25″ wall 6061 | DERIVED — CALC-C02 |
| Table | 16″ × 22″ torsion box | DERIVED |
| ALN-01 | \|A−B\| ≤ 0.003″ no-load, paper-on | DERIVED — D-040 |
| TV-01 | witness-board spread ≤ 0.005″ | DERIVED — CALC-C06 |
| Drum TIR | ≤ 0.0015″ paper-off | DERIVED |

`ply_actual` is USER_MEASURE. Change it in `cad/walter_ds16.py` and regenerate.
Do not shrink the inner span.

## Why Rev C exists

Rev B specified \|A−B\| ≤ 0.003″ and a ¾″ drum shaft. Beam numbers show those
two statements are incompatible: the ¾″ shaft spends the entire 0.001″
allowance at 4.25 lbf of sanding force (CALC-C01). Rev B also used one number,
0.003″, for two physically different quantities — a no-load **alignment** check
and a delivered **thickness variation**. Rev C splits them (ALN-01 / TV-01),
then makes the structure stiff enough that neither is governed by the shaft.

Rev C series-model crown at 20 lbf is ~0.22 mil (~21× stiffer than Rev B).

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
   shoes (P-017) constrain X and Y. Tapered gib (P-022) sets running clearance.
   Dual ½-10 Acme on the drum centerline lift in Z. Operator feeds the
   workpiece. There is no conveyor.
2. **Drum axis** — Option A: structural 6061 shell + turned plugs (J-106),
   drive flange FIXED (J-006), idler on a micro-adjust plate (J-105 / J-007).
   Option B: pack-bored disc stack, documented with an accuracy penalty.
3. **Feed** — hold-down rollers 0.030″ below the drum, paper on.

## Joinery on this machine

This is a Baltic birch box, not a timber frame. Housed dados (J-001) plus
**through-bolts (H-034)** carry racking — glue is not primary structure. See
`planforge/joinery-and-tolerance-standards.md` and Q-102. 3D-print P-023 at 1:1
before cutting metal.

## Conditions before real work

1. Transfer the purchased flange before drilling. BCD is ASSUMED.
2. Measure `ply_actual` and regenerate. Keep 16.5″ inner span.
3. Confirm purchased bearing C on the vendor page (CALC-C11). Bore alone is
   not a specification.
4. Motor circuit, switch, grounding, cord: qualified electrician and local
   code. Not released by this package.
5. Commission with the hood on and no stock, standing clear of the drum ends.
6. Pass ALN-01 then TV-01 before using real work.
7. Collector ≥ CALC-C15 CFM at the machine. A shop vacuum will not.
8. Fill McMaster part numbers from the product page (H-02 / H-03).
