# Zero-Gap Verification Checklist

Run this checklist against every package before declaring it complete. Fail any item → revise until it passes.

## Completeness
- [ ] All primary structural members appear in the part register with finished dimensions and material.
- [ ] All secondary parts (slats, cassettes, mesh, caps, pins, lights) appear with finished dimensions.
- [ ] Quantities are correct and match the geometry.
- [ ] Consumable fasteners are either fully specified or a complete custom alternative is detailed.

## Joinery & Details
- [ ] Every critical joint has a dedicated detail sheet.
- [ ] Geometry, cut sequence, acceptance criteria, and water/movement control are present.
- [ ] Layout system (face/edge or centerline) is declared and consistently applied to joint geometry.
- [ ] Japanese or hand-tool sequences, when used, are fully specified.
- [ ] 3D-print prototype recommendation is stated for complex or irreversible joints.

## Structural & Foundation
- [ ] Load path is shown or clearly described.
- [ ] Moments, forces, or interaction ratios are calculated or conservatively bounded.
- [ ] All assumptions and limitations are stated on the structural sheet.
- [ ] Foundations / post bases are either fully detailed (rebar, cover, concrete, connector) or carry an explicit hold point listing exactly what data is still required.

## Hardware & Interfaces
- [ ] Hinges, latches, and specialty hardware are either exact make/model + geometry or a fully detailed custom solution.
- [ ] Threshold, drainage, and service clearances are defined.
- [ ] Seasonal or removable components have clear retention and removal methods.

## Tolerances & Quality
- [ ] Numerical tolerances exist for every critical fit and geometric characteristic.
- [ ] Inspection methods and acceptance criteria are defined (Q-series).
- [ ] Irreversible hold points are identified in the assembly sequence.

## Fabrication Practicality
- [ ] Assembly sequence is present and logical.
- [ ] Solo-handling rules and temporary support methods are defined where needed.
- [ ] Module masses or handling difficulties are acknowledged.
- [ ] Stock preparation, grain, and finish rules are stated.

## Self-Containment Test
Ask: “Could a skilled craftsperson who has never seen this project produce a correct, strong, weather-resistant result using only this package, basic shop tools (or the specified hand tools), and the materials listed?”

If the answer is not a clear yes, the package is not yet complete under Planforge standards.

Document the checklist results at the end of the package or in the release notes.
