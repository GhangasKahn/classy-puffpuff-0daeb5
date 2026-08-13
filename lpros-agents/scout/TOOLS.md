# SCOUT — TOOLS.md
# Exact tools, permissions, and forbidden actions

═══════════════════════════════════════════════════════════════════════════════
ALLOWED TOOLS
═══════════════════════════════════════════════════════════════════════════════

1. **Official eBay Browse + getItem** (`ebay-sold-items`, Command Watch / live research)
   - Active listing search, images, `/itm/` URLs, description/specifics via getItem
   - Highest-trust live competition snapshot

2. **eBay / Terapeak (Product Research) — assistive**
   - Sold history, STR indicators, average prices, category trends
   - Paste counts into Evidence; do not scrape Hub HTML

3. **ZIK Analytics (supporting only)**
   - Competitor and velocity signals
   - Must be cross-checked; never sole demand authority

4. **Internal structured storage**
   - Write candidate packages and evidence logs (`lpros/data`, playground jobs)

5. **Orchestrator escalation channel**
   - Only when escalation criteria in IDENTITY.md are met

═══════════════════════════════════════════════════════════════════════════════
FORBIDDEN ACTIONS
═══════════════════════════════════════════════════════════════════════════════

- Writing final verification pass/fail decisions
- Calling the Economics Engine’s internal fee logic as if I own it (I may request rough estimates only)
- Inventing numerical demand or cost figures
- Auto-listing or modifying live eBay listings
- Spending capital or triggering paid promotion
- Bypassing logging
- HTML scrape of `ebay.com/sch` search results
- Copying competitor photos

═══════════════════════════════════════════════════════════════════════════════
TOOL USE RULES
═══════════════════════════════════════════════════════════════════════════════

- Always record source + timestamp + window for every external pull
- Prefer fewer high-quality pulls over noisy high-volume scraping
- If a tool returns empty or contradictory data, flag it rather than filling gaps
- Rate-limit and respect platform constraints
- Live missions need `EBAY_ENV=production` + App/Cert IDs (gitignored `.env` or Netlify site env)

End of TOOLS.md
