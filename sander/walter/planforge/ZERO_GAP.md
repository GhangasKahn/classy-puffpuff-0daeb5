# Zero-Gap Verification Checklist — WALTER Rev C

Protocol: WOODWRIGHT PLANFORGE v1.0. Fail any item → do not claim an unconditional fabrication release.

| Item | Result | Evidence |
|---|---|---|
| All fabricated parts in part register with finished sizes | PASS | `walter_project.parts()` F/ST/D/T/C/M/HD/N |
| Quantities match geometry (21 discs, 2 walls, 2 Acme) | PASS | kernel `P.n_discs` + BOM |
| Consumable fasteners specified or kit alternative | PASS | hardware schedule H-001…; kit line for #8/¼-20 |
| Every critical joint has a detail sheet | PASS | J-201 drum, J-202 ways/Acme, J-203 crown, J-204 wrap |
| Geometry, cut sequence, acceptance on joints | PASS | J sheets + `JOINERY_SCHEDULE.csv` + Q01–Q10 |
| Layout system declared and consistent | PASS | D1–D4 on G-001 / G-002 |
| Wood movement at drum stack | PASS | 0.5 mm gaps every 4 discs; birch not MDF |
| Load path / energy described | PASS WITH CONDITION | R3 abrasive drum; no NDS member design; machinery review [P] |
| Assumptions and limitations on cover | PASS | G-001 banner; not PE; not UL |
| Hardware exact make/model or search term | PASS WITH CONDITION | 6245K47 / 6191K37 [S]; other PNs [E] verify live |
| Electrical one-line | PASS WITH CONDITION | W-12 design intent; electrician [P] |
| Guards, nips, dust, E-stop, no auto-restart | PASS WITH CONDITION | M-101 / M-104 / Q06 / Q08; first-run [T] |
| Numerical tolerances for critical fits | PASS | bore 0.748 +0/−0.002; OD 5.000±0.010; crown 0.030±0.005 |
| Inspection methods and acceptance | PASS | Q-101 + `fab/12_QA/inspection.csv` |
| Irreversible hold points identified | PASS | no glue in keyway; no paint on ways; no sanding-belt conveyor |
| Assembly sequence present | PASS | LEGO `/manual/` 22 steps + bags 1–6 |
| Solo-handling rules | PASS | disc stack and walls are solo; 1 HP motor is a two-hand lift ~30–40 lb |
| Stock prep / grain / finish rules | PASS | F-101 nest; crossed-grain walls; oil ways |
| 1:1 templates with two calibration bars | PASS WITH CONDITION | T-DISC / T-PLATE — builder must verify print scale |
| Self-containment: skilled builder + this package + listed materials | PASS WITH CONDITION | Close electrician, first-run, live catalog, true the drum |

**Release recommendation:** FABRICATION-READY WITH CONDITIONS. Do not mark FABRICATION-READY (unconditional). Do not mark PE-approved or UL-listed.
