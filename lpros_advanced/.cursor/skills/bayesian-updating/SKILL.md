---
name: bayesian-updating
description: Sequential Bayesian belief updates from real outcomes — priors, likelihoods, posteriors, and decision thresholds. Use when new data arrives and prior forecasts, hit rates, or parameter beliefs must be revised under LPROS.
---

# Bayesian Updating Skill

## When to use

- A prior forecast or parameter belief exists and new outcomes arrived
- Calibrating hit rates, conversion, default rates, edge estimates
- Combining expert prior with observed likelihood
- Replacing ad-hoc “I feel more bullish now” with an explicit update

## Procedure

### 1. State the belief object

- Parameter or hypothesis Θ (e.g., mean return, win rate, elasticity, delay days).
- Prior π(Θ): source, strength (pseudo-counts / variance), and date.
- If no prior exists, choose a **weakly informative** prior and say why — do not pretend flat ignorance when domain bounds exist.

### 2. Specify the likelihood

- Observation model p(data | Θ).
- Independence / exchangeability assumptions.
- Outliers and data-quality filters (pre-declare; do not cherry-pick after seeing results).

### 3. Update

- Compute posterior π(Θ | data) ∝ p(data | Θ) π(Θ).
- Closed form when conjugate; otherwise approximate (grid, Laplace, MCMC) and state the method.
- Report posterior mean/median and **credible interval**; show prior → posterior shift.

### 4. Decision mapping

- Define action thresholds on posterior functionals (e.g., P(Θ > θ*) > α).
- If posterior is too wide for action → recommend information-gathering, not forcefulness.
- Log the update for `accuracy-audit` (timestamp, data ids, prior version, posterior summary).

### 5. Output contract

```text
BAYES UPDATE
- Object Θ:
- Prior: summary + source + strength
- Data: n, window, filters
- Likelihood model:
- Posterior: summary + interval
- Shift: what moved and how much
- Decision: act / wait / gather | threshold used
- Next update trigger:
```

## Conjugate quick reference (use when valid)

| Likelihood | Prior | Posterior |
|------------|-------|-----------|
| Bernoulli/Binomial | Beta(α,β) | Beta(α+#success, β+#fail) |
| Poisson rate | Gamma | Gamma |
| Normal mean (known σ²) | Normal | Normal |
| Exponential rate | Gamma | Gamma |

## Anti-patterns

- Replacing the prior with the latest observation (maximum forgetfulness)
- Double-counting the same data across updates
- Reporting only a point posterior without interval
- Changing the hypothesis after seeing data without calling it exploratory
