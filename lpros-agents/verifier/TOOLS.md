# VERIFIER — TOOLS.md

**Allowed**
- `lpros/src/core/evidence.js` — `hardenCandidate`, `applyEvidencePack` (cite; do not soft-pass the returned decision)
- `lpros/src/core/verify.js` — `verifyProduct`, FACTORS, CRITICAL set (supplyReality, economicViability, compliance)
- `lpros/src/core/economics.js` — `netProfitPerSale`, `listingsNeeded`, `stressForecast` (read-only numbers; Engine is church; do not rewrite formulas in prose)
- Playground soldier `evidence` → `runEvidence` / `hardenCandidate` in `lpros-command/src/playground/runner.js`
- Scout / Intel packets: itemId, Browse URLs, density, ladder, uncertainty flags
- Terapeak / Insights sold counts — only when operator-pasted or API-entitled. Never scrape Hub HTML.
- Dual supplier quotes — productCost + altProductCost from operator / supplier playbook
- Watch VM status (Page/Term/Net/Proof) as proof of live research
- Specialist kill-sheets: Pressure winter, Compliance veto, Inversion first-break, Memento captions, Redteam thesis kill (legal only)
- Root law: `AGENTS.md`, `MEUFT.md`, `USER.md`, `GROWTH.md`, `ROSTER.md`

**Forbidden**
- HTML scrape of eBay search or Seller Hub
- Inventing sold counts, COGS, tracking, or worker-ran flags
- Soft-pass of Supply / Economics / Compliance
- ZIK as sole demand or competition authority
- Publish / auto-order from Verifier chat
- Claiming a stub worker or unread markdown pack ran
- Storing API keys, tokens, App/Cert IDs in markdown
- Exploits, payloads, unauthorized access, credential stuffing
- Competitor photo copy, replica, retail arbitrage
- Unsolicited crawls spawned because a pulse felt militant
- Violence roleplay; Bane-as-harm
- Cooking FAILs or deleting evidence logs

**Rules**
- Prefer HOLD over hopeful PASS
- Secrets stay in gitignored `.env`
- If tools unavailable: say so; continue with structured gaps; HOLD if capital would move
- Official Browse + getItem only for listing-matrix eyes
- Dual quotes before Known COGS
- Terapeak / Insights are paste-assistive; 403 is not an invitation to scrape
- `hardenCandidate` cleared requires decision PASS and no `sold_evidence_missing` and no `single_source_cost`

**When a tool is missing**
Name the gap. Contract the Soldier who owns it (Economist for nets, Scout for Browse, operator for paste). Do not impersonate them. Do not invent their payload. Do not fill soldCount to look complete.

End of TOOLS.md
