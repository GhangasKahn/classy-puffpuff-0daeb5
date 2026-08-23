# MARTIN Build Manual — Rev F.2

Source of truth: `fence/martin/martin_kernel.py` → `fab/00_SOURCE/martin_project.json`.

## A. Model status
Semantic fabrication model. Every MAKE part has a Part ID. Joinery is a register, not only booleans.
Gate/cap clearance **0.500″**. Post blank **67.000″**. Sit-on-grade — **no concrete**. Gate against the house.

## B. Controlling parameters (inch)
- overall_length = 143.000 VERIFIED (driveway span)
- overall_height = 65.000 VERIFIED
- gate_clear = 36.000 ASSUMED — gate at house, no planter at P0
- bay_clear = 46.500 DERIVED `(L - 4*post_x - gate_clear)/2`
- nuki_len = 109.500 DERIVED
- slat_top = 63.500 + cap 1.50 = 65.000
- cassette φ pair = 11.263 / 18.224 (L2/L1 = 1.618 ≈ φ)
- drop_off = 0.000 (0 on slab; packing only if outriggers leave)

## C–I. Registers
See `07_BOM/bom.csv`, `08_CUT_LISTS/*.csv`, `09_JOINERY/joints.csv`.

**Nest buy:** `{'4x6x8': 6, '4x6x16': 2, '2x4x10': 2, '2x12x10': 1, '2x12x12': 1, '1x4x8': 12, '1x4x12': 1, '2x6x8': 5, '2x2x8': 3, '2x4x8': 2, 'oak_1x4x4': 2}`  net **314.71 bf**  procurement **361.92 bf** (waste_factor=0.15).
**Ballast:** two live planters, soil 1155.0 lb + in-box stone 366.7 lb = 1521.7 lb vs required 1311.1 lb (planning FS 1.5). Concrete **0**. Gravel pad **0**.

## K. Assembly order
- **AS-01** (STOCK) Procure nested lumber + PT + oak rods 96825K84/K75 + pads 60015K58 + IP67 tape 8836N52/24
- **AS-02** (SITE) TBM 143″ opening on the driveway. Gate at the house. Do not dig. Do not pour.
- **AS-03** (BASE) Mill F-001..F-003 ladder; half-lap; dry-fit on slab pads; build two F-005 troughs (not at house)
- **AS-04** (MILL) Posts L-001..004 to S-014; 3.50″ tenons; through-nuki + housed dados
- **AS-05** (MILL) Water table K-001 + belts R-001/002; mill Tree of Life + nested-rect cassettes Q-*
- **AS-06** (MILL) Gate G-* hozo dry fit; brace; oak pivot sockets
- **AS-07** (JOINERY) Kusabi W-001; pegs W-002; cap scarf C-001 + light dado
- **AS-08** (DRY) Dry-assemble A-020: ribbons, cassettes, 0.75″ dog gauge on Q-001; QA QC-08
- **AS-09** (DRY) Hang gate on oak pivots at P1; latch travel into P0
- **AS-10** (FINISH) Ease, seal, PT dry, prime, two gray coats; extra on planter interiors; mask locking faces
- **AS-11** (SET) Set ladder on pads; drop posts; bands; wedges; cap light; gate; plant troughs + optional in-box stone
- **AS-12** (QA) QC-08..17; winter rehearsal

## L. Drawing index
- G-000 Cover / drawing index / revision
- GA-100 General arrangement — elevation + notes
- GA-110 Front elevation — datums + overall
- GA-130 Plan at ladder base / post centers
- EX-200 Exploded assembly — insertion directions
- P-301 Post typical L-001..004
- P-302 Water table + Prairie belts K-001 / R-001 / R-002
- P-303 Tree of Life + nested-rect cassettes Q-001..003
- P-304 Gate leaf G-001..010
- J-401 Nuki + kusabi / housed dado
- J-402 Foot tenon / cross-tie shoe
- J-403 Kama-tsugi cap scarf
- J-404 Gate hozo drawbore + oak pivot
- T-501 Kusabi full-size template
- T-502 Foot tenon full-size template
- S-601 Master BOM
- S-602 Rough cut list
- S-603 Finished cut list
- S-604 Hardware schedule
- S-605 Board nesting / yield
- QA-701 Inspection plan
- L-801 Part labels
- WPF-G001 WOODWRIGHT PLANFORGE guidebook (G/A/J/E/F/S/Q + McMaster)

## O. Unresolved
- U-01 Outrigger packing only if garden sill leaves the slab (default 0 — photos show driveway run) [VERIFIED/TBM] param `drop_off`
- U-02 Latch: default B (mortise in L-001). House wall strike is opt-in, no epoxy. [ASSUMED] param `latch mode`
- U-03 Owner gray exact color [TBM] param `finish hex`
- U-04 Buffalo Green Code district height / front-yard [TBM] param `overall_height 65″ designed under 6′`
- U-05 Swing direction (garden vs driveway) [ASSUMED] param `gate swing +Y garden`
- U-06 Species upgrade (cedar / locust) [OPTIONAL] param `SPECIES`
- U-07 Licensed PE stamp [NOT THIS PACKAGE] param `n/a`
- U-08 Remeasure 143″ on the driveway (photos confirm span to house siding) [TBM] param `overall_length`

## Completeness tests
1. Craftsperson: critical dims are numeric from datums (P-301, S-014, QC-04..14).
2. Other CAD agent: `martin_project.json` is sufficient to regenerate layout + parts.
3. Change overall_length by 12″: re-run kernel — bay_clear, nuki_len, sills, post CLs, nest, BOM update. Rail CL and stock section stay.

This package is a **planning fabrication model**, not a stamped PE document.
