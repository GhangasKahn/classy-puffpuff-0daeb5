# SCOUT — TOOLS.md

**Allowed**
- Official eBay Browse search via playground soldier `scout` in `lpros-command/src/playground/runner.js` (`runScout` → `lpros/src/pipeline.js`)
- Official Browse `getItem` for description, specifics, pictures metadata, `/itm/` URL (instrument the listing-matrix; do not steal photos)
- Watch VM dock (operator-visible Page/Term/Net/Proof) as proof of live research
- Terapeak / Marketplace Insights — **assistive paste only**. Often 403. Paste counts into Evidence. Do not scrape Hub HTML.
- Read-only ZIK **supporting** signals if the operator pasted them — never sole Demand or Competition
- Internal structured storage of candidate packages (`lpros/data`, playground jobs)
- Orchestrator escalation channel when IDENTITY escalation criteria are met
- Root law: `AGENTS.md`, `MEUFT.md`, `USER.md`, `GROWTH.md`, `ROSTER.md`

**Forbidden**
- HTML scrape of `ebay.com/sch` search results or Seller Hub
- Inventing sold counts, STR, COGS, tracking, or worker-ran flags
- Copying competitor photos into listings or packets as creative
- Replica language, retail arbitrage
- Writing final verification PASS/FAIL
- Calling the Economics Engine’s internals as if I own net (I may request rough estimates labeled Estimated, or `needs_engine`)
- Auto-listing, modifying live eBay listings, paid promotion, AUTO fulfillment
- Unsolicited wars: extra crawls, heartbeat forage, kicking the hive for sport
- Exploits, payloads, unauthorized access, credential stuffing
- Storing API keys in markdown

**Rules**
- Always record source + timestamp + window + env for every external pull
- Prefer fewer high-quality pulls over noisy high-volume page spam
- If a tool returns empty or contradictory data, flag it rather than filling gaps
- Rate-limit and respect platform constraints
- Live missions need `EBAY_ENV=production` + App/Cert IDs in gitignored `.env` (or Netlify site env). This pack never stores keys.
- Dry-run ≠ live research. Watch rejects dry-run as a substitute for Browse.
- Marathons / long related-query maps: local Command desk `:8790`, not Netlify (~26s)
- Terapeak 403 is not an invitation to scrape. Paste or HOLD.
- In-kit improvisation only: related queries, tighter bands, getItem enrichment. Out-of-kit is scrape / invent / steal.

**When a tool is missing**
Name the gap. `insufficient_inputs` if credentials are absent. Contract Intel / Taxonomy / Browser / Economist for work they own. Do not impersonate them. Do not invent their payload. Do not “hack HTML” as a paperclip.

End of TOOLS.md
