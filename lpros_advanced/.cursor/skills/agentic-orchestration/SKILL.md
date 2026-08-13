---
name: agentic-orchestration
description: Brain/Soldier routing and contracts for multi-agent LPROS workflows. Use when designing, running, or debugging agent swarms — planning, task delegation, tool permissions, verification gates, and handoff protocols.
---

# Agentic Orchestration Skill

## When to use

- Multi-agent analysis (research, risk, allocation, verification)
- Splitting planning from execution
- Defining tool permissions and I/O contracts
- Debugging agent loops, loops without verification, or conflicting Soldiers

## Roles

### Brain

- Owns goals, constraints, routing, and acceptance criteria.
- Decomposes work into Soldier tasks with typed contracts.
- Verifies outputs against Economics Engine + accuracy gates.
- May refuse to proceed when listings-needed or invariants fail.

### Soldier

- Executes one scoped task; no mandate expansion.
- Returns structured results; does not redefine objectives.
- May call approved tools only; cannot invent economic truth.

## Procedure

### 1. Contract template

```text
TASK CONTRACT
- id / parent goal:
- role: Brain | Soldier:<specialty>
- inputs (schema):
- tools allowed:
- outputs (schema):
- constraints (capital, time, data):
- done when (acceptance tests):
- on failure:
```

### 2. Routing rules

1. **Facts & arithmetic** → Engine / `computational-math`, never freeform LLM math for ledger truth.
2. **Uncertainty propagation** → `simulation-engine` or `forecasting`.
3. **Belief revision** → `bayesian-updating`.
4. **Allocation choice** → `optimization` under Brain constraints.
5. **Behavior/drift** → `behavior-analysis` + `conditioning-protocol`.
6. **Final check** → `accuracy-audit` before user-facing recommendation.

### 3. Execution loop

1. Brain drafts plan + contracts.
2. Soldiers run in parallel when independent; serialize when state conflicts.
3. Brain merges, resolves conflicts, runs invariants.
4. If acceptance fails → retry with narrowed contract or escalate with gap report.
5. Emit decision package with uncertainties and actions.

### 4. Safety rails

- Hard stop on irreversible capital actions without explicit human/Brain approval gate.
- Budget tool calls and wall time; prevent infinite research loops.
- Log every plan revision and override.

### 5. Output contract

```text
ORCHESTRATION
- Goal:
- Plan graph (Brain → Soldiers):
- Contracts summary:
- Results merge:
- Invariant / audit status:
- Residual risks / open listings-needed:
- Recommendation + next trigger:
```

## Anti-patterns

- Soldiers rewriting the objective mid-flight
- Parallel Soldiers mutating the same state without locking/merge rules
- “Swarm theater” without acceptance tests
- Skipping verification because the prose sounds confident
