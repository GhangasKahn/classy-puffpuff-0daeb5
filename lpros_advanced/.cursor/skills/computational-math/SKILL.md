---
name: computational-math
description: Fee algebra, sensitivity analysis, and numerical hygiene for LPROS calculations. Use when deriving identities, checking units, propagating errors, differentiating drivers, or preventing floating-point and rounding bugs in economic math.
---
# Computational Math Skill

## When to use

- Fee, tax, interest, FX, and settlement algebra
- Sensitivity / elasticity of outputs to inputs
- Unit conversions, compounding bases, day-count conventions
- Debugging “numbers that almost add up”

## Procedure

### 1. Identity first

1. Write the exact algebraic relationship before coding.
2. Name every symbol; attach units and time base.
3. Mark conserved quantities (cash, shares) and where leakage (fees) occurs.

### 2. Fee & friction algebra (patterns)

- Always specify whether fees are **inclusive** or **exclusive** of notional.
- Chain: gross → fee → tax → net; never apply in inconsistent order.
- Round only at cash settlement boundaries required by venue rules; keep full precision internally.

### 3. Numerical hygiene

| Rule | Practice |
|------|----------|
| Precision | Use decimal/rational for money when available; avoid binary float for ledger truth |
| Summation | Kahan or sorted summation for long series if needed |
| Cancellation | Reformulate expressions that subtract near-equal quantities |
| Conditioning | Prefer stable formulas (e.g., relative returns carefully) |
| Display | Round at presentation; show significant figures justified by inputs |

### 4. Sensitivity

- Finite differences with step sized to variable scale; check step robustness.
- Where differentiable, report elasticities (∂y/y)/(∂x/x).
- Tornado of top-k drivers for decision docs.

### 5. Verification

- Dual implementation or spot-check against hand calculation.
- Invariants: Σ weights = 1, cash identity, non-negative inventory if required.
- Cross-check Engine output vs spreadsheet for a golden fixture.

### 6. Output contract

```text
COMP MATH
- Identity:
- Units / conventions:
- Fee/tax order:
- Numerics notes:
- Sensitivity table:
- Invariant checks: pass/fail
```

## Anti-patterns

- Mixing APR/APY or 360/365 silently
- Rounding intermediate tax/fee steps differently than the venue
- Reporting 8 decimals from noisy inputs
- “Approximately equal” without tolerance tied to units
