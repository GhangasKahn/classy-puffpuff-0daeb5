# MARTIN fabrication package (Rev D)

Single source of truth: [`martin_ssot.py`](martin_ssot.py) → [`martin.json`](martin.json)

```
PARAMETER → GEOMETRY → METADATA → DRAWINGS → BOM → CUT LIST → BUILD / QA
```

## Audit (existing coded model)

| Area | Rating |
|---|---|
| Architecture | WEAK→ACCEPTABLE (SSOT added; FCStd still grouped solids) |
| Parameterization | ACCEPTABLE |
| Part separation | GOOD in registry |
| Metadata | GOOD in JSON/CSV |
| Joinery | GOOD (Joint IDs) |
| BOM / cut list | GOOD |
| Drawing readiness | ACCEPTABLE |
| Export | ACCEPTABLE |

## Conflict resolved

**D-001** Post finished length is `height − cap_t + tenon_h = 75.5″`, not `65+12=77″`. Rough cut remains 77″.

## Regenerate

```bash
python3 fence/martin/fab/martin_ssot.py
python3 scripts/gen_martin_plans.py
# optional:
./scripts/build_martin.sh
```

Changing `overall_length` in `PARAMS` updates post layout, nuki length, bay clear, pad length, cut lists, and drawings.
