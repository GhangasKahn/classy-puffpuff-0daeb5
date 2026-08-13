# BROWSER — TOOLS.md

**Allowed**
- Playground soldier `browser` in `lpros-command/src/playground/browser.js`: `runBrowserJob`, `fetchAllowed`, `createSession`, `advanceSession`, `addCapture`, `parseItemId`, `hostnameAllowed`
- Dispatch via `lpros-command/src/playground/runner.js` case `"browser"`
- Catalog playbooks (`lpros-command/src/playground/catalog.js` `PLAYBOOKS`): `terapeak`, `supplier`, `ops-pass`, `getitem`
- Official Browse getItem for eBay **item** URLs / ids (`ebay-sold-items` getBrowseItem) — listing-matrix eyes, not photo theft
- Allowlisted HTTPS fetch of hosts in `ALLOWED_HOSTS` (example.com, developer.ebay.com, apidocs.ebay.com, github.com, raw.githubusercontent.com, wikipedia) within timeout/byte cap
- Operator paste into Evidence / mission form (Terapeak n, dual COGS)
- Watch VM dock (Page/Term/Net/Proof) as proof of live research when contracted
- Root law: `AGENTS.md`, `MEUFT.md`, `USER.md`, `GROWTH.md`, `ROSTER.md`

**Forbidden**
- HTML scrape of `ebay.com/sch` search results
- HTML scrape of Seller Hub / Terapeak / Marketplace Insights (403 is not an invitation)
- Inventing sold counts, COGS, tracking, captures, or worker-ran flags
- Copying competitor photos into listings or packets as creative
- Replica language, retail arbitrage
- SSRF: localhost, private, link-local, metadata IPs
- Expanding `ALLOWED_HOSTS` from this pack
- Exploits, payloads, unauthorized access, credential stuffing, malware
- Publish / AUTO / PASS verdict from this desk
- Unsolicited fetches or playbooks from heartbeat
- Storing API keys in markdown

**Rules**
- HTTPS only. Timeout ~8s. Max bytes capped. Truncation is flagged, not bypassed
- eBay hostname → item-only. Missing item id on an eBay URL → 403 with message to paste `/itm/` or id
- Terapeak playbook caveat: assistive — Insights often 403. Paste counts; do not scrape Hub HTML
- Supplier: dual quotes before Known COGS. No orders without HOLD_REVIEW
- Ops-pass: CSV/Seller Hub works without Sell OAuth; live Inventory needs user token. Original photos only
- getItem caveat: use Browse getItem — not HTML scrape of search results
- Live getItem needs production App/Cert in gitignored `.env`. This pack never stores keys
- Dry session ≠ live getItem. Name the mode
- Rate-limit. Prefer contracted URLs over volume
- Empty tool result → flag, do not fill

**When a tool is missing**
Name the gap. `insufficient_inputs` if getItem creds are absent. Contract Scout / Intel / Taxonomy / Economist / Verifier for work they own. Do not impersonate them. Do not invent their payload. Do not HTML-scrape as a paperclip. Do not probe blocked hosts.

End of TOOLS.md
