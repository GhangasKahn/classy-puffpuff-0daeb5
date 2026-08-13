# MEUFT — Orchestration Geometry

Kept as the **how** Brain stages work. The swarm constitution (`AGENTS.md`) is the **law**. When they conflict, **AGENTS.md wins** on capital, verification, and ToS; MEUFT still shapes the brief.

| Letter | Layer | Job |
|--------|--------|-----|
| **M** | Mission & Mandate | Own the goal, constraints, acceptance tests. No mandate drift. |
| **E** | Economics Engine | Cash is truth. Deterministic fee/net/listings math outranks narrative. |
| **U** | Uncertainty & Evidence | Every numeric claim is Known / Estimated / Assumed. Missing comps → `listings-needed`. |
| **F** | Factor Verification | Fail-closed zero-trust gates. |
| **T** | Task Contracts & Conditioning | Typed Brain→Soldier contracts; cue→response loops; accuracy audit. |

**Invariant:** Soldiers never invent economics. Brain never skips Factor Verification on capital-touching advice.

## TASK CONTRACT (mandatory template)

```text
TASK CONTRACT
- id / parent goal:
- role: Brain | Soldier:<specialty>
- inputs (schema + provenance):
- tools allowed:
- outputs (schema):
- constraints (capital, time, data, ToS):
- done when (acceptance tests):
- on failure (retry | narrow | escalate | HOLD):
- MEUFT checks: M☐ E☐ U☐ F☐ T☐
```

## Output contract (Brain action advice)

```text
MEUFT BRIEF
- Mission (M):
- Economics (E): [computed | needs_engine | N/A] — figures + units
- Uncertainty (U): Known / Estimated / Assumed + gaps
- Factors (F): PASS | CONDITIONAL | FAIL — flags
- Contracts / next (T): who does what; cue for next turn
- Recommendation:
- Refusal / HOLD (if any):
- Accuracy audit: [ran | deferred: reason]
```

PrimeAgent Brain prompt cards remain in `brain/SYSTEM_PROMPT.md` and `brain/CONDITIONING.md`.
