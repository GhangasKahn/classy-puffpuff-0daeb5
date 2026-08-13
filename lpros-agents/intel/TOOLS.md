# INTEL — TOOLS.md

**Allowed**
- Official eBay Browse search (`ebay-sold-items` / Command live research)
- Official Trading `getItem` (description, specifics, pictures, `/itm/` URL)
- Sold-items adapter when present and returning real rows
- Watch VM dock (operator-visible Page/Term/Net/Proof)
- Playground soldier `intel` in `lpros-command/src/playground/runner.js`
- Read-only ZIK **supporting** signals if the operator pasted them — never sole Demand

**Forbidden**
- HTML scrape of `ebay.com/sch` or Hub
- Inventing soldCount / STR / revenue
- Copying competitor photos
- Calling Economics Engine as if I own net (escalate numbers)
- Publish, order, PASS language
- Starting unsolicited marathon crawls from heartbeat

**Rules**
- Live missions need `EBAY_ENV=production` + App/Cert in gitignored `.env` (or Netlify site env). This pack never stores keys.
- Dry-run ≠ live research. Watch rejects dry-run as a substitute for Browse.
- Marathons / long crawls: local Command desk `:8790`, not Netlify (~26s).
- Rate-limit. Prefer fewer high-quality pulls.
- Empty tool result → flag, do not fill.

End of TOOLS.md
