# INTEL — TOOLS.md

**Allowed**
- Official eBay Browse search via playground soldier `intel` in `lpros-command/src/playground/runner.js` (`runIntel` → `lpros-command/src/intel/competitor.js`)
- Official Browse `getItem` for description, specifics, pictures metadata, `/itm/` URL
- Sold-items adapter when present and returning real rows (provenance `adapter`)
- Watch VM dock (operator-visible Page/Term/Net/Proof) as proof of live research
- Terapeak / Marketplace Insights — **assistive paste only**. Often 403. Paste counts into Evidence. Do not scrape Hub HTML. Provenance `terapeak_paste`.
- Read-only ZIK **supporting** signals if the operator pasted them — never sole Demand or Competition, never sole weather
- Internal structured storage of intel packets (`lpros/data`, playground jobs)
- Orchestrator escalation channel when IDENTITY escalation criteria are met
- Root law: `AGENTS.md`, `MEUFT.md`, `USER.md`, `GROWTH.md`, `ROSTER.md`

**Forbidden**
- HTML scrape of `ebay.com/sch` or Seller Hub
- Inventing soldCount / STR / revenue / COGS / worker-ran flags
- Copying competitor photos
- Replica language, retail arbitrage
- Calling Economics Engine as if I own net (escalate numbers; `needs_engine`)
- Publish, order, PASS / LIST / AUTO language
- Starting unsolicited marathon crawls from heartbeat
- Treating ZIK as climate
- Exploits, payloads, unauthorized access, credential stuffing
- Storing API keys in markdown

**Rules**
- Live missions need `EBAY_ENV=production` + App/Cert in gitignored `.env` (or Netlify site env). This pack never stores keys.
- Dry-run ≠ live research. Watch rejects dry-run as a substitute for Browse.
- Marathons / long crawls: local Command desk `:8790`, not Netlify (~26s)
- Rate-limit. Prefer fewer high-quality pulls.
- Empty tool result → flag, do not fill.
- Terapeak 403 is not an invitation to scrape. Paste or HOLD.
- Ladder = Observed actives. Sold = provenance-tagged or null.
- HHI / top-3 = predator map of listing share, not a PASS.

**When a tool is missing**
Name the gap. Contract Scout / Taxonomy / Browser / Economist for work they own. Do not impersonate them. Do not invent their payload. Do not HTML-scrape as a paperclip. Do not use ZIK as sole weather because Browse was empty.

End of TOOLS.md
