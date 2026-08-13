# FACTORY — TOOLS.md
# Allowed tools, forbidden actions, rate/ToS rules. No secrets. No API keys.

**Desk JS:** playground `factory` → `runFactory` in `lpros-command/src/playground/runner.js`. Requires `orchJobId` or throws 400. Downstream: `packagesForJob` / assemble path in `lpros-command/src/orchestrate/factory.js` and `buildListingPackages` in `lpros/src/core/listing_factory.js` (which may call `draftListing` as a part, not as publish).

**Allowed**
1. `packagesForJob` / assemble — `lpros-command/src/orchestrate/factory.js`
2. `buildListingPackages` — `lpros/src/core/listing_factory.js`
3. Copywriter drafts / `draftListing` (`lpros/src/agents/listing.js`) as input parts only
4. CSV/Seller Hub export payload (not live publish)
5. Operator promote path with HOLD
6. Read Verifier / Compliance status — do not soft-pass
7. Read Engine numbers already on the job — cite, do not rewrite `economics.js`
8. Taxonomy cluster keys / duplicate notes
9. Root law: `AGENTS.md`, `MEUFT.md`, `USER.md`, `GROWTH.md`
10. Image *presence* flags from orch products — not competitor URL ingest as ours

**Forbidden**
- Publishing live listings from this role (default)
- Competitor photo copy (including “placeholder” hotlink)
- Assembling without orchJobId
- Beautifying FAIL packets into LIST-ready rows
- Inventing sold counts on package rows
- HTML scrape of eBay search, Hub, or competitor listing HTML
- Silent AUTO inventory / silent promote
- Storing API keys in this pack
- Exploits, payloads, unauthorized access
- Unsolicited package mills from heartbeat
- Replica / qty-spam farms
- Treating packageCount as demand

**Rules**
- Original photos only — shot list for *our* camera
- Engine prices or Assumed; never freelance fees
- Cluster clones; do not kick the hive
- Rate/ToS: no mass-list spam; account health > volume
- Secrets stay in gitignored `.env`
- If tools unavailable (job not found → 404): say so; do not invent a catalog
- Local desk for long jobs; Netlify is short-lived
- Promote is HOLD until operator path is explicit

**When a tool is missing**
Name the gap. Do not impersonate Copywriter. Do not steal a photo to fill imageStats. Do not fake orchJobId.

End of TOOLS.md
