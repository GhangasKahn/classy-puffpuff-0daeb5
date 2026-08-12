---
name: accuracy-audit
description: Continuous calibration of forecasts, models, and agent outputs against reality. Use when checking hit rates, bias, residual errors, backtests, or whether LPROS recommendations matched subsequent outcomes.
---

# Accuracy Audit Skill

## When to use

- After outcomes realize for prior forecasts or decisions
- Periodic calibration of models, agents, or coach advice
- Before trusting a method in a new regime
- Post-mortems on misses (and on lucky hits)

## Procedure

### 1. Gather the claim set

- Pull stamped predictions/decisions: time, horizon, target, scenario, model version.
- Pull realized outcomes with the same definitions (no definition drift).
- Exclude or separately bucket claims marked exploratory.

### 2. Scorecard

| Metric | Use |
|--------|-----|
| Bias | Mean(error) — systematic over/under |
| MAE / RMSE | Magnitude of error |
| Interval coverage | Did X% intervals cover ~X% of outcomes? |
| Calibration curve | Predicted prob vs realized frequency |
| Decision regret | Outcome vs action rule performance |
| Listings discipline | % of price claims with valid evidence |

### 3. Segment

- Slice by horizon, asset class, regime, agent, or scenario type.
- A global “looks calibrated” can hide catastrophic local failure.

### 4. Update the system

- Feed systematic bias into `bayesian-updating` or model recalibration.
- Failures of process (skipped listings, skipped Engine) → `conditioning-protocol`.
- Method inadequacy → retire or restrict the model’s license to operate.

### 5. Output contract

```text
ACCURACY AUDIT
- Window / n claims / definitions:
- Overall scorecard:
- Segments (best/worst):
- Calibration notes:
- Process breaches (listings, invariants):
- Actions: recalibrate | restrict | retrain | no change
- Next audit date/trigger:
```

## Anti-patterns

- Auditing only wins
- Changing the target definition after seeing errors
- Treating backtest metrics as live calibration
- No link from audit findings back into priors or contracts
