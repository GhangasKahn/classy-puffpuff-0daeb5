---
name: physics-informed
description: Capital conservation and irreversibility mindset — treat money, inventory, and commitments like physical constraints. Use when modeling cash identities, lockups, fees as entropy, unwind paths, or rejecting impossible financial states under LPROS.
---

# Physics-Informed Skill

## When to use

- Cashflow or inventory accounting that must conserve
- Evaluating lockups, vesting, withdrawal gates, illiquid exits
- Stressing whether a proposed trade/path is physically feasible
- Teaching agents to respect hard constraints over story-fitting

## Core analogies (use carefully, not as decoration)

| Physics idea | Finance analogue |
|--------------|------------------|
| Conservation | Cash/share identities; double-entry |
| Irreversibility / entropy | Fees, taxes, slippage, burned gas — lost work |
| Path dependence | Sequence of margin calls, forced de-risking |
| Barriers / absorbing states | Ruin, default, delisting, account freeze |
| No perpetual motion | No riskless arb after frictions without evidence |

## Procedure

### 1. Write conservation laws

1. Σ sources − Σ uses − Σ fees = Δ cash (exact).
2. Position changes reconcile to trades + corporate actions.
3. Forbid magic: no unexplained residual larger than tolerance.

### 2. Classify actions

| Class | Examples | Rule |
|-------|----------|------|
| Reversible (approx.) | Cancel resting quote, delay buy | Prefer for learning |
| Costly-reversible | Round-trip trade | Model round-trip friction |
| Irreversible | Tax lot sale, expire option, missed vesting | Require higher evidence bar |

### 3. Feasibility filter

Before recommending an action, verify:

- Capital available **after** fees and holds
- Liquidity path (listings, depth, time to exit)
- Timing constraints (settlement, cliffs, notice periods)
- No violated mandate / leverage / regulatory barrier

### 4. Stress irreversibility

- Ask: “If Adverse/Severe hits tomorrow, what cannot be undone?”
- Size exposure to irreversible legs with explicit max-loss.
- Prefer staged commitments with kill switches.

### 5. Output contract

```text
PHYSICS CHECK
- Identities asserted:
- Residuals / leaks (fees):
- Reversibility class of proposed actions:
- Barriers / absorbing risks:
- Feasibility: pass/fail + blockers
- Staging / kill switch:
```

## Anti-patterns

- Plans that require selling illiquid inventory instantly at mid
- Ignoring fees as “small” without cumulative math
- Negative cash without a modeled credit facility
- Treating paper marks as spendable capital
