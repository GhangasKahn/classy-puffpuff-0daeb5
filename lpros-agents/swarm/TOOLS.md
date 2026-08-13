# SWARM — TOOLS.md
# Allowed tools, forbidden actions, rate/ToS rules. No secrets. No API keys.

**Desk JS:** playground `swarm` → `runResearchSwarm` via `lpros-command/src/playground/runner.js` (`runSwarm`). Live import: `lpros-command/src/swarm/research.js`. HTTP: POST `/swarm` in `lpros-command/src/http/router.js`. CLI: `lpros-command/src/cli-swarm.js`. Dry path in runner (`input.dryRun`) returns a dry note **without** calling `runResearchSwarm` — label it; it is not live.

**Allowed**
- `runResearchSwarm` (Scout pipeline + competitorIntel parallel, optional crawlCategory, hardenCandidate, draftListing, Engine helpers)
- `runResearchPipeline` / Browse path inside Scout (`lpros/src/pipeline.js`) — official Browse, not HTML scrape
- `competitorIntel` (`lpros-command/src/intel/competitor.js`)
- `crawlCategory` when deepCrawl+categoryId (`lpros/src/agents/crawl.js`) — still official pagination, not search-HTML scrape
- `hardenCandidate` (`lpros/src/core/evidence.js`) when evidencePack present
- `draftListing` shells (`lpros/src/agents/listing.js`) — publish false
- Engine: `netProfitPerSale`, `expectedDailyProfit`, `listingsNeeded`, `stressForecast` (`lpros/src/core/economics.js`) — cite, do not rewrite
- Watch VM status (Page/Term/Net/Proof) as proof of live research when a Watch exists
- Root law: `AGENTS.md`, `MEUFT.md`, `USER.md`, `GROWTH.md`

**Forbidden**
- HTML scrape of eBay search or Seller Hub
- Inventing sold counts, COGS, tracking, or worker-ran flags
- Unnamed workers / swarm theater / fake consensus
- Dressing dryRun as live Watch
- Publish / auto-order from swarm chat
- Claiming a stub worker or unread markdown pack ran
- Storing API keys in markdown
- Exploits, payloads, unauthorized access, credential stuffing
- Competitor photo copy, replica, retail arbitrage
- Unsolicited crawls spawned because a pulse felt militant
- Treating Quality merge as Verifier PASS

**Rules**
- Prefer reversible probes
- Local `:8790` for marathons; Netlify is short-lived
- Secrets stay in gitignored `.env` (`EBAY_PRD_APP_ID` / cert — never paste here)
- If tools unavailable / credentials missing: say so; structured gaps; HOLD if capital would move
- Official Browse + getItem only
- Dual quotes before Known COGS; Terapeak paste-assistive; 403 is not an invitation to scrape
- Named workersRan on every live output
- Fulfiller HOLD still binds after a swarm brief

**When a tool is missing**
Name the gap. Put the worker in workersSkipped. Do not impersonate them. Do not invent their payload.

End of TOOLS.md
