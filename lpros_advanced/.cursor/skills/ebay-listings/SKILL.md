---
name: ebay-listings
description: Attach eBay sold/active listing evidence for vault comps and forecasts. Use when valuing collectibles, checking liquidity, or satisfying LPROS listings-needed via the ebay-sold-items service.
---

# eBay Listings Skill

## When to use

- Vault / alt-asset valuation (watches, cards, spirits, cars, metals)
- Any price claim that needs marketplace evidence
- Forecasting exits or liquidity under listings-needed rules

## Evidence hierarchy

1. **eBay sold** (Marketplace Insights, ~90d) — preferred for comps
2. **eBay active** (Browse API) — asking prices only; mark evidence **partial**
3. **No listings** — `listings-needed`; refuse tight Base paths

Never present Browse asking prices as sold comps without labeling them.

## Procedure

### 1. Query the bridge

Default local service (`ebay-sold-items` on `:8787`):

```http
GET /v1/market/alt/comps?category=Watch&ref=126610LN
GET /v1/ebay/sold?q=126610LN&categoryIds=31387
GET /v1/ebay/search?q=126610LN&categoryIds=31387
```

### 2. Interpret response

| Field | Meaning |
|-------|---------|
| `evidenceStatus: ok` | Sold comps present |
| `evidenceStatus: partial` | Active only / weak sold |
| `evidenceStatus: listings-needed` | No usable listings |
| `listingsNeeded: true` | Widen forecast or block precise Base |
| `comps[].url` | Primary evidence link — cite it |

### 3. Feed forecasting

- Use median/avg of **sold** prices for Base when `soldCount > 0`
- Adverse/Severe: haircut for fees, slow sale, condition gaps (`physics-informed`, fee algebra)
- If Insights returns 403 entitlement → note limited-release gap; do not invent sold history

### 4. Output contract

```text
EBAY EVIDENCE
- Query (category/ref):
- evidenceStatus / listingsNeeded:
- soldCount / activeCount:
- suggestedValue + basis (sold|active|none):
- Top listing URLs:
- Forecast impact:
```

## Anti-patterns

- Embedding Cert ID in frontend or commits
- Treating Sandbox catalog noise as real comps for Production decisions
- Silent fallback from sold → active without `partial` / listings-needed flags
