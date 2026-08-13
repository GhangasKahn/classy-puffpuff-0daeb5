# TAXONOMY — TOOLS.md

## Allowed
1. Official eBay Browse pagination (`lpros/src/agents/crawl.js` via playground `crawler`).
2. `getItem` enrichment on a watch sample (images, specifics, `/itm/`).
3. Internal storage of leaf packets (`lpros/data`, playground jobs).
4. Warn: long crawls on local `:8790`, not Netlify.

## Forbidden
- HTML scrape of `ebay.com/sch`
- Inventing sold counts to decorate a leaf
- Unsolicited marathon crawls
- Treating n as demand
- Copying competitor photos
- Auto-list / capital

## Rules
- Record pages, delay, env, timestamp
- THIN and SWAMP are labels, not insults to cover with fake n
- Rate-limit Browse
- Missing App/Cert → insufficient_inputs

End of TOOLS.md
