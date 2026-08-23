# Zero-Gap Verification Checklist — MARTIN Rev F.2

Protocol: WOODWRIGHT PLANFORGE v1.0. Fail any item → do not claim an unconditional fabrication release.

| Item | Result | Evidence |
|---|---|---|
| All primary structural members in part register with finished sizes | PASS | `fab/07_BOM/bom.csv` L/F/K/R/C |
| Secondary parts (cassettes, muntins, caps, pins, lights, pads) listed | PASS | Q-001..003, Q-010 muntin stock, T-001, W-001..003, H-001, H-006 |
| Quantities match geometry | PASS | kernel `parts()` + nest |
| Consumable fasteners specified or custom alternative | PASS | No structural screws. Oak pegs 96825K75. Optional hasp 1304A42. |
| Every critical joint has a detail sheet | PASS | J-401 nuki/kusabi, J-402 foot tenon, J-403 kama-tsugi, J-404 hozo/pivot |
| Geometry, cut sequence, acceptance, water/movement on joints | PASS | J sheets + `09_JOINERY/joints.csv` + QC-08..17 |
| Layout system declared and consistent | PASS | CENTERLINE for posts P0–P3; Datum A = sill top z=0; x=0 latch face |
| Japanese / hand-tool sequences specified | PASS | nuki/kusabi, hozo drawbore, kama-tsugi; Bridge City / Zenwu / Japanese saws |
| 3D-print prototype recommendation | PASS WITH CONDITION | Print T-501 kusabi, T-502 tenon, pivot socket 1:1 PLA before milling |
| Load path shown or described | PASS | S-101 in guidebook; wind via planters + ladder spread |
| Moments/forces bounded | PASS WITH CONDITION | Planning FS 1.5; PE if AHJ requires |
| Assumptions and limitations on structural sheet | PASS | G-001 banner; not PE-stamped |
| Foundations fully detailed OR explicit hold point | PASS | Sit-on-grade; no foundation. Pads 60015K58. No pour. |
| Hardware exact make/model or custom geometry | PASS | McMaster schedule; oak pivots mill from 96825K84 |
| Threshold, drainage, service clearances | PASS | Gate bottom 0.375″; kick 2×12; planter drainage slots |
| Seasonal removable components have retention/removal | PASS | Kusabi reverse; winter sequence in manual |
| Numerical tolerances for critical fits | PASS | T1 general / T2 joinery; nuki sliding; pivot locational |
| Inspection methods and acceptance | PASS | QA-701 + Q-101 |
| Irreversible hold points identified | PASS | Never glue kusabi/nuki faces; paint after dry-fit |
| Assembly sequence present | PASS | LEGO `/martin/manual/` 24 steps + AS-01..12 |
| Solo-handling rules | PASS | Two-person nuki slide; posts lift individually from F-003 |
| Stock prep / grain / finish rules | PASS | F-102 in guidebook; H-005 Buffalo paint |
| Self-containment: skilled builder + this package + listed materials | PASS WITH CONDITION | Close TBM 143″, Green Code, electrician for 120 V, plant troughs |

**Release recommendation:** FABRICATION-READY WITH CONDITIONS. Do not mark FABRICATION-READY (unconditional). Do not mark PE-approved.
