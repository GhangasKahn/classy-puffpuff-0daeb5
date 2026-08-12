# LPROS — Lean Product Research OS

Zero-based eBay product research runtime: **Economics Engine** (cash is truth), Bayesian-lite demand, provisional psychological *feature proxies*, and **zero-trust multi-factor verification**. MEUFT-inspired principles kept; heavy theory discarded until empirically earned.

Built from the Grok design thread (ZBPDP → statistical hardening → low-compute Hermes agents) and wired to `ebay-sold-items/`.

## What is sound vs inspiration

| Keep (operational) | Inspiration only until calibrated |
|--------------------|-------------------------------------|
| Fee / net / listings-needed math | Greene / Jung / Adler / Voss as *feature ideas* |
| Sell-through + Gamma-Poisson velocity | Full MEUFT geometry / Gödel formalisms |
| Hard gates + fail-closed verify | Treating PsychFit as a probability |
| Closed-loop outcome logging | ARC-AGI-3 conditioning (Phase later) |

## Quick start

```bash
# 1) eBay keys (gitignored)
cp ../ebay-sold-items/.env.example ../ebay-sold-items/.env
# set EBAY_ENV=production and App/Cert IDs

# 2) Economics (no network)
npm run econ -- --price 40 --cost 22
npm run forecast -- --listings 300 --str 0.018 --net 9.4 --target 120

# 3) Zero-trust verify (no network)
npm run verify -- --price 40 --cost 18 --sold 12 --altCost 19

# 4) Live research pipeline
npm run pipeline -- --category Watch --q 126610LN --cost-ratio 0.55
```

## Agents (Hermes-style, sequential)

1. **Data** — Taxonomy / Browse / comps  
2. **Feature** — STR, velocity posterior, density  
3. **Psychology** — provisional proxies (not validated probabilities)  
4. **Margin & Gate** — Economics Engine + 8-factor verify  
5. **Ranking** — uncertainty-shrunk expected net × psychFit  
6. **Outcome** — JSONL log + tiny weight nudges  

Orchestration is a plain sequential pipeline (`src/pipeline.js`) — LangGraph/Paperclip optional later. Prefer local Hermes/Ollama for copy agents when added; no mandatory paid LLM.

## Zero-trust factors

Supply · Demand (no ZIK-only) · Competition · Economics · Compliance (retail arbitrage = FAIL) · Remorse · Listing feasibility · Forecast sensitivity  

Critical: Supply, Economics, Compliance. Fail-closed.

## Paid data (optional, one slot)

**ZIK Analytics** may be added later as a *cross-check only* — never sole demand authority (see verify rules).

## Roadmap → Sep 3 (MVP production)

| Phase | Window | Status |
|-------|--------|--------|
| 1 Foundation — econ + verify + eBay data | Aug 11–15 | **In progress (this package)** |
| 2 Research & listing MVP | Aug 16–22 | Next |
| 3 Fulfillment (DSers/AutoDS wrap) | Aug 23–28 | Later |
| 4 Integration & hardening | Aug 29–Sep 2 | Later |

Deferred: full ARC-AGI-3 conditioning loop, Paperclip org chart, advanced image gen.

## Cursor skills

See `../lpros_advanced/` for agent rules/skills (forecasting, Bayesian, conditioning-protocol, ebay-listings, etc.).

## Tests

```bash
npm test
```
