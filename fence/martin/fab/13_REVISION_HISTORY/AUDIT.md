# MARTIN existing-model audit — Rev D

Per fabrication-model agent MODE B.

## Ratings

| Topic | Rating | Notes |
|---|---|---|
| MODEL ARCHITECTURE | ACCEPTABLE | SSOT Python/JSON is authority. FreeCAD still emits grouped timber/concrete solids. |
| PARAMETERIZATION QUALITY | ACCEPTABLE | Central PARAMS; layout derived. overall_length change updates posts/bays/nuki/pad. |
| PART SEPARATION | GOOD | 26 PART_IDs. CAD object names not yet PART_ID. |
| METADATA QUALITY | GOOD | JSON/CSV Fabrication fields. FreeCAD custom properties not attached. |
| ASSEMBLY STRUCTURE | ACCEPTABLE | A-MASTER tree in data. |
| JOINERY STRUCTURE | GOOD | Explicit Joint IDs, fit class, tooling. |
| DRAWING READINESS | ACCEPTABLE | M-series + G-000, S-402, P-301, QA-700. |
| BOM READINESS | GOOD | Mill buy + parts from registry. |
| CUT-LIST READINESS | GOOD | Rough, finished, stock nests. |
| EXPORT READINESS | ACCEPTABLE | JSON/CSV/SVG. STEP/STL remain grouped. |

## Conflict found and corrected

Docs used post blank **77″ = 65 + 12**. CAD body was already `H − cap_t`. **D-001:** finished post = **75.5″**. Rough remains 77″.

## 2×12 yield correction

“Equal thirds” of 11.25″ = 3.75″ — too narrow for 7.25″ rails. **D-002:** rip 7.25″ from the **outer zone**, remainder ~3.5″ for gate.

## Next refactor (not blocking shop)

Label FreeCAD features from PART_ID when regenerating FCStd.
