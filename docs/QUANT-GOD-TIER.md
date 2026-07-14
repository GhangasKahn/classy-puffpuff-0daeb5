# BEDROCK Quant Lab — God-Tier Capability Map

Research/education mathematics running **on-device** in `site/app/quant-engine.js`, surfaced in the PWA **LAB** tab. Not a brokerage. Moves no money. Not financial advice.

## Stack

| Domain | Implemented |
|---|---|
| **Portfolio engineering** | Mean-variance (min-var), max-Sharpe (tangency), risk parity, fractional Kelly, historical VaR/CVaR, Cholesky correlated returns, Shannon entropy / effective bets |
| **Stochastic calculus** | GBM (Itô), Merton jump-diffusion, Ornstein–Uhlenbeck, Heston stochastic volatility |
| **Options / hedge legs** | Black–Scholes price + Δ Γ Θ ν ρ, delta-hedge share leg |
| **Convexity** | Bond Macaulay / modified duration + convexity |
| **Entropy / LLN** | Shannon + Rényi entropy, KL divergence, LLN running-mean experiment + Chebyshev sample-size bound |
| **Chaos** | Logistic map, Lyapunov exponent, Lorenz attractor |
| **Game theory** | 2×2 mixed Nash, Hawk–Dove ESS, Aggressive/Defensive vs Bull/Bear |
| **Capital rotation** | Regime heuristic sleeves + **beat BTC∧SPX** rotation (RS score, cycle-capped alt budget) |
| **4y crypto cycle** | Halving calendar, phase/risk, progress since last / to next |
| **Mid/long cycles** | DFT periodogram bands, 50/200 trend, ACF, AR(1) half-life |
| **Cointegration** | Engle–Granger hedge β, ADF residual test, z-score, residual half-life |
| **Relative strength** | Cumulative + rolling RS vs BTC and SPX |
| **ML / DL** | OLS, L2-logistic GD, 1-hidden-layer tanh MLP |
| **RL** | UCB1 multi-armed bandit, tabular Q-learning capital posture MDP |

## How to use

1. Open the PWA → **LAB**
2. Set a seed → **Rebuild Book** for portfolio suite
3. Flip sub-tabs: BOOK · **CYCLES** · STOCH · ENTROPY · OPTIONS · CHAOS · GAME · ML/RL · ROTATE

**CYCLES desk:** 4-year BTC halving phase → mid/long periodogram on BTC → RS vs BTC/SPX → Engle–Granger pairs → weights into names beating both benchmarks (alt budget shrinks late-cycle).

## Tests

```bash
cd backend && npm test
```

Includes `tests/quant-engine.test.ts` loading the browser engine in Node via `vm`.

## Honest limits

- Demo universe is synthetic (4 assets). Wire real return matrices when recon/Phase 3 lands.
- MLP/RL are pedagogical-scale, not production training clusters.
- No live options chain, no borrow, no margin engine, no execution.
- Survival floor in FLOOR/QUANT still outranks elegance in LAB.
