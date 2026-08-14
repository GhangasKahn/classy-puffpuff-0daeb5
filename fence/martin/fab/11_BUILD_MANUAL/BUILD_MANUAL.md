# MARTIN Build Manual — Rev D

Source of truth: `fence/martin/martin_kernel.py` → `fab/00_SOURCE/martin_project.json`.

## A. Model status
Semantic fabrication model. Every MAKE part has a Part ID. Joinery is a register, not only booleans.
Gate/cap clearance **0.500″**. Post blank **67.000″**. Sit-on-grade — **no concrete**.

## B. Controlling parameters (inch)
- overall_length = 143.000 VERIFIED
- overall_height = 65.000 VERIFIED
- gate_clear = 36.000 ASSUMED
- bay_clear = 46.500 DERIVED `(L - 4*post_x - gate_clear)/2`
- nuki_len = 104.500 DERIVED
- drop_off = 5.000 ESTIMATED **TBM**

## C–I. Registers
See `07_BOM/bom.csv`, `08_CUT_LISTS/*.csv`, `09_JOINERY/joints.csv`.

**Nest buy:** `{'4x6x8': 6, '4x6x16': 2, '2x8x10': 3, '2x8x12': 1, '2x6x8': 8, '1x6x8': 9, '2x4x8': 1, 'oak_1x4x4': 2}`  net **323.98 bf**  procurement **372.58 bf** (waste_factor=0.15).
**Ballast:** 27 × 50 lb bags (planning 1311.1 lb). Concrete **0**. Gravel **0**.

## K. Assembly order
- **AS-01** (STOCK) Procure nested lumber + sandbags + rubber pads
- **AS-02** (SITE) TBM opening + drop-off. Do not dig. Do not pour.
- **AS-03** (BASE) Mill F-001..F-003 ladder; half-lap; dry-fit on grade; F-004 pack garden side
- **AS-04** (MILL) Posts L-001..004 to S-014; 3.50″ tenons; mortises
- **AS-05** (MILL) Rails R-001..003 grooves; boards B-* stop cuts
- **AS-06** (MILL) Gate G-* hozo dry fit; brace; pintles
- **AS-07** (JOINERY) Kusabi W-001; pegs W-002; cap scarf C-001
- **AS-08** (DRY) Dry-assemble A-020 on horses; QA QC-08
- **AS-09** (DRY) Hang gate on L-002; latch travel
- **AS-10** (FINISH) Disassemble paint; mask locking faces
- **AS-11** (SET) Set ladder on pads; drop posts in F-003; rails; wedges; boards; cap; gate; fill F-005 with H-007
- **AS-12** (QA) QC-08..14; winter rehearsal

## L. Drawing index
- G-000 Cover / drawing index / revision
- GA-100 General arrangement — elevation + notes
- GA-110 Front elevation — datums + overall
- GA-130 Plan at ladder base / post centers
- EX-200 Exploded assembly — insertion directions
- P-301 Post typical L-001..004
- P-302 Nuki rail R-001..003
- P-303 Privacy boards B-001..003
- P-304 Gate leaf G-001..010
- J-401 Nuki + kusabi
- J-402 Foot tenon / cross-tie shoe
- J-403 Kama-tsugi cap scarf
- J-404 Gate hozo drawbore
- T-501 Kusabi full-size template
- T-502 Foot tenon full-size template
- S-601 Master BOM
- S-602 Rough cut list
- S-603 Finished cut list
- S-604 Hardware schedule
- S-605 Board nesting / yield
- QA-701 Inspection plan
- L-801 Part labels

## O. Unresolved
- U-01 Driveway→garden drop [TBM] param `drop_off`
- U-02 Latch: default B (mortise in L-001). House wall strike is opt-in, no epoxy. [ASSUMED] param `latch mode`
- U-03 Owner gray exact color [TBM] param `finish hex`
- U-04 Buffalo Green Code district height / front-yard [TBM] param `overall_height 65″ designed under 6′`
- U-05 Swing direction (garden vs driveway) [ASSUMED] param `gate swing +Y garden`
- U-06 Species upgrade (cedar / locust) [OPTIONAL] param `SPECIES`
- U-07 Licensed PE stamp [NOT THIS PACKAGE] param `n/a`

## Completeness tests
1. Craftsperson: critical dims are numeric from datums (P-301, S-014, QC-04..14).
2. Other CAD agent: `martin_project.json` is sufficient to regenerate layout + parts.
3. Change overall_length by 12″: re-run kernel — bay_clear, nuki_len, sills, post CLs, nest, BOM update. Rail CL and stock section stay.

This package is a **planning fabrication model**, not a stamped PE document.
