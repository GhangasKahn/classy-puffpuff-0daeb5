# VERIFIER — TOOLS.md

═══════════════════════════════════════════════════════════════════════════════
ALLOWED TOOLS
═══════════════════════════════════════════════════════════════════════════════

1. **Economics Engine** (`lpros/src/core/economics.js`) — fee-true net, listings-needed, stress. Read-only as numbers; do not rewrite formulas in prose.
2. **Zero-trust verify / hardenCandidate** (`lpros/src/core/evidence.js`, `verify.js`)
3. **Scout evidence packages** — itemId, Browse URLs, images, uncertainty flags
4. **Terapeak / Insights sold counts** — only when operator-pasted or API-entitled. Never scrape Hub HTML.
5. **Dual supplier quotes** — productCost + altProductCost from operator / supplier playbook

═══════════════════════════════════════════════════════════════════════════════
FORBIDDEN
═══════════════════════════════════════════════════════════════════════════════

- Soft-pass critical factors
- Invent sold comps or COGS
- Publish listings
- Auto-order
- Treat ZIK as sole demand proof

End of TOOLS.md
