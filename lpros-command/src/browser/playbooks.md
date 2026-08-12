# Browser playbooks (assistive — not a replacement for APIs)

Use Cursor Browser / Open WebUI agent when official sold data is gated.

## Terapeak / eBay Product Research (sold comps)

1. Sign in to Seller Hub → Product research (Terapeak).
2. Search the candidate title / EPID / GTIN.
3. Capture: avg sold price, sold count (90d), sell-through, active count.
4. Paste into LPROS verify as `soldCount`, `evidenceStatus: ok`, second demand source `terapeak`.
5. Zero-trust rule: Terapeak + Browse must agree directionally — never ZIK-only.

## Supplier reality check

1. Open wholesale / CJ / private supplier page for the SKU.
2. Record landed cost + handling days.
3. Enter as `productCost` + `altProductCost` (second quote) before PASS.

## Ops after PASS (real-world)

1. Promote PASS rows into LPROS Command registry (`Promote` on board or `npm run ops -- promote …`).
2. Export CSV (`npm run ops -- export` or desk **Export ready CSV/JSON**).
3. Create listings in Seller Hub from CSV / paste — or set `EBAY_USER_REFRESH_TOKEN` + business policies for live Inventory API.
4. When an order arrives, **Order ingest** with registry SKU → HOLD until supplier confirmed + tracking.
5. Attach tracking → dry-run push payload; live push when user token present.

## Anti-patterns

- Do not bulk-scrape eBay HTML search pages (ToS / ban risk). Use Browse crawl.
- Do not let browser agents place supplier orders without HOLD_REVIEW gate.
- Do not `{ live:true }` publish without photos + PASS evidence + policies.
