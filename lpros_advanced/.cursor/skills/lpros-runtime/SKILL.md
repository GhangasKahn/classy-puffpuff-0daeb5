---
name: lpros-runtime
description: Lean Product Research OS runtime — economics engine, zero-trust verification, Hermes-style eBay research pipeline. Use when ranking products, computing fees/net/listings-needed, or running npm scripts under lpros/.
---

# LPROS Runtime Skill

## Commands

```bash
cd lpros
npm run econ -- --price 40 --cost 22
npm run forecast -- --listings 300 --str 0.018 --net 9.4 --target 120
npm run verify -- --price 40 --cost 18 --sold 12 --altCost 19
npm run pipeline -- --category "Home" --q "cable organizer" --cost-ratio 0.4
```

## Authority

- **Economics Engine** (`src/core/economics.js`) outranks narrative.
- Zero-trust verify is fail-closed (`src/core/verify.js`).
- PsychFit is a **provisional proxy** — never present as calibrated probability.
- Retail arbitrage → compliance FAIL.

## Agent order

Data → Feature → Psychology → Margin/Gate → Rank → Outcome log

See `lpros/README.md` for Sep 3 roadmap and MEUFT lean mapping.
