# ECONOMIST — TOOLS.md

**Allowed**
- `lpros/src/core/economics.js` — `netProfitPerSale`, `expectedDailyProfit`, `listingsNeeded`, `stressForecast`
- Read-only candidate fields from Scout/Verifier packages
- Playground `economics` soldier

**Forbidden**
- Inventing STR, soldCount, COGS
- Rewriting fee law in prose as if it were the Engine
- Publish, order, scrape
- Treating ZIK revenue as Known cash

**Rules**
- Cite function names in logs
- If Engine throws or inputs NaN → INSUFFICIENT_INPUTS, do not interpolate
- Secrets never in markdown; eBay keys stay in gitignored `.env`

End of TOOLS.md
