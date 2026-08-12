---
name: optimization
description: Price, quantity, and portfolio optimization under constraints — objectives, feasible sets, and risk-aware decisions. Use when sizing positions, allocating capital, setting prices/quantities, or choosing portfolios subordinate to the LPROS Economics Engine.
---

# Optimization Skill

## When to use

- Position sizing, budget allocation, inventory/quantity choices
- Pricing under elasticity or competitive constraints
- Portfolio construction with risk/return/constraint tradeoffs
- Choosing among discrete actions with capital consequences

## Procedure

### 1. Write the formal problem

1. **Decision variables** x (prices, weights, quantities, binary choices).
2. **Objective** J(x) — what is maximized/minimized (utility, after-fee P&L, growth, shortfall).
3. **Constraints** g(x) ≤ 0 — capital, leverage, lot sizes, mandates, liquidity, regulatory.
4. **Uncertainty** — if present, optimize expectation / CVaR / robust worst-case; state which.

### 2. Respect the Economics Engine

- Fee, tax, financing, and settlement algebra come from deterministic Engine identities.
- Do not optimize pre-friction fantasy P&L.
- Enforce conservation and irreversibility checks (`physics-informed`).

### 3. Method selection

| Problem shape | Method |
|---------------|--------|
| Smooth convex | Analytic / convex solver |
| Low-dimensional | Grid / line search with Engine evals |
| Discrete small set | Exhaustive + ranked table |
| Simulation-coupled | Optimize over MC metrics (`simulation-engine`) |
| Multi-objective | Pareto frontier; do not hide weights |

### 4. Robustness

- Stress the optimum under Adverse/Severe scenarios.
- Report local sensitivity ∂J/∂assumptions for top drivers.
- Prefer solutions with flat neighborhoods over knife-edge optima when uncertainty is high.

### 5. Output contract

```text
OPTIMIZATION
- Variables / objective / constraints:
- Frictions included (fees, tax, slip):
- Uncertainty treatment:
- Solution x*:
- Objective value + risk metrics:
- Stress under Adverse/Severe:
- Sensitivities:
- Implementation notes (lots, timing, unwind):
```

## Anti-patterns

- Maximizing return while ignoring drawdown, liquidity, and fees
- Presenting an unconstrained “optimal” weight that violates real mandates
- Overfitting to one historical path
- Silent scalarization of multi-objective problems
