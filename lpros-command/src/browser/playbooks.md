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

## Anti-patterns

- Do not bulk-scrape eBay HTML search pages (ToS / ban risk). Use Browse crawl.
- Do not let browser agents place supplier orders without HOLD_REVIEW gate.
