---
name: simulation-engine
description: Monte Carlo and scenario simulation for risk distributions, runway, portfolio paths, and stress outcomes. Use when uncertainty must be propagated through a model under LPROS, especially with correlated shocks or path dependence.
---

# Simulation Engine Skill

## When to use

- Need a full loss/return/runway **distribution**, not a single scenario line
- Path dependence (sequence of cashflows, margin calls, vesting, fees)
- Correlated asset shocks or factor-driven portfolios
- Stress testing beyond the Adverse case narrative

## Procedure

### 1. Define the state and drivers

1. State vector S_t (cash, positions, liabilities, KPIs).
2. Stochastic drivers (returns, volumes, defaults, delays) with distributions.
3. Deterministic overlays from the **Economics Engine** (fees, taxes, constraints).
4. Horizon, step size, and number of paths N (justify N for stable percentiles).

### 2. Dependence & realism

- Specify correlation / copula / factor structure; default independence is a strong claim.
- Include frictions: spreads, fees, borrow, liquidation rules.
- Bound paths with physical constraints (`physics-informed`): non-negative cash unless credit line modeled, conservation of shares, etc.

### 3. Run protocol

1. Fix seeds for reproducibility; record seed + version.
2. Simulate N paths; store terminal and pathwise risk metrics.
3. Report distribution: mean/median, p05/p25/p75/p95, P(breach), expected shortfall if relevant.
4. Map percentiles onto **Base / Adverse / Severe** labels when used for decisions.

### 4. Sensitivity & checks

- One-at-a-time and/or important-driver tornado for top assumptions.
- Martingale / conservation checks where applicable (cash accounting identity).
- Compare median path to deterministic Engine projection; explain gaps.

### 5. Output contract

```text
SIMULATION
- State / horizon / dt / N / seed:
- Drivers + dependence:
- Frictions included:
- Results: percentiles + breach probs
- Triad mapping: Base≈p50 | Adverse≈p10–p20 | Severe≈p05 or ES
- Fragile assumptions:
- Planning vs prediction label: PLANNING DISTRIBUTION (default)
```

## Anti-patterns

- N too small for claimed percentile precision
- GBM-everything without justifying dynamics
- Ignoring absorbing barriers (ruin, margin call)
- Presenting a single pretty path as “the” simulation result
