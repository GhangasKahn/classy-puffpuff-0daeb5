---
name: forecasting
description: Produce base/adverse/severe forecasts with listings-needed discipline, horizons, triggers, and decision-linked actions. Use when forecasting prices, cash runway, demand, liquidity, KPIs, or scenario paths under LPROS standards.
---

# Forecasting Skill

## When to use

- Any request for a forward path, range, or “what happens if”
- Runway, portfolio value, revenue, comps, or risk KPIs over a horizon
- Stress or planning scenarios that must remain decision-coupled

## Procedure

### 1. Frame the forecast

1. Define the **target variable**, units, and **horizon** (and time resolution).
2. List drivers and which are observed vs assumed.
3. Check evidence: market data, listings/comps, ledger facts, external series.
4. If critical price/liquidity inputs lack fresh listings → flag **listings-needed** and either:
   - widen intervals materially, or
   - refuse a precise Base path until evidence arrives.

### 2. Build the triad

Construct **Base / Adverse / Severe** with explicit assumptions for each:

| Field | Required |
|-------|----------|
| Path or end-state value | Yes |
| Key assumptions | Yes |
| Probability mass (if model-based) or qualitative likelihood | Preferred |
| Trigger conditions | Yes |
| Linked action | Yes |

### 3. Model choice (pick the lightest that fits)

- **Deterministic drivers known** → Economics Engine / closed-form projection first.
- **Uncertainty dominant** → Monte Carlo or scenario tree (`simulation-engine` skill).
- **Beliefs updating over time** → seed with prior, then `bayesian-updating`.
- **Expert judgment only** → elicit ranges; do not fake model precision.

### 4. Validation hooks

- Backcheck against recent outcomes if history exists (`accuracy-audit`).
- Sensitivity: show which 1–2 assumptions move the result most (`computational-math`).
- Irreversibility: call out lockups, fees, and forced sellers (`physics-informed`).

### 5. Output contract

```text
FORECAST
- Target / horizon / resolution:
- Evidence status: [ok | listings-needed | partial]
- Model class:
- Base: value/path | assumptions | action
- Adverse: ... | triggers | action
- Severe: ... | triggers | action
- Uncertainty note:
- What would change this forecast:
```

## Anti-patterns

- Single-point “my target is $X”
- Mixing planning MC with claimed predictive accuracy
- Ignoring fees, slippage, or tax in exit paths
- Averaging Base/Adverse/Severe into a fake expected value for the headline
