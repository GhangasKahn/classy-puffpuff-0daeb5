# LPROS Rank & Filters

## Filter stages (hard → soft)

1. `price_band` — default $35–$200  
2. `scam_kill` — qty spam, lots, clickbait, replicas  
3. `compliance` — retail arbitrage FAIL  
4. `margin_floor` — fee-true net & margin  
5. `perceived_value` — materials / problem-solve / upgrade  
6. `evidence_soft` — sold missing / single-source cost → CONDITIONAL  

## LPROS_Rank_v1 weights

| Component | Default weight | Notes |
|-----------|----------------|-------|
| cash (uncertainty-shrunk net) | 0.32 | Economics Engine |
| sellThrough | 0.18 | sold/(sold+active); weak if synthetic |
| perceivedValue | 0.16 | heuristic, not calibrated ML |
| popularity | 0.12 | watches + STR + velocity + PV |
| competition (inverse density) | 0.10 | |
| ctrProxy | 0.08 | **Not official eBay CTR** |
| evidence bonus | 0.04 | sold comps present |

Penalties: ×0.85 if `sold_evidence_missing`; ×0.92 if single-source cost.

## API honesty

| Metric | Availability |
|--------|----------------|
| Product images | Browse `image` / thumbnails |
| Purchase history | Insights sold comps (often gated) or Terapeak pack |
| Official CTR | **Not available** via Browse — proxy only |
| Watch count | Often App-Check restricted |
| STR | Requires sold evidence for strength |

## Code

- `lpros/src/core/filters.js`
- `lpros/src/core/market_metrics.js`
- `lpros/src/core/ranker.js`
- Desk viz: Command UI after swarm/intel
