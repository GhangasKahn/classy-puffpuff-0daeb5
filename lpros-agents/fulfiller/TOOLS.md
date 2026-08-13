# FULFILLER — TOOLS.md

**Allowed**
- Playground `fulfill` / `fulfillDecision`
- Read Engine output objects (not rewrite)
- Read Verifier status
- Allowlisted supplier confirm flags from operator or browser playbook
- Tracking number validation after order (format/carrier), never invention

**Forbidden**
- Auto-order APIs without confirm
- Retail-arbitrage checkout
- HTML scrape
- Inventing tracking or sold counts
- Publish
- Spending capital from heartbeat

**Rules**
- Secrets never in this pack
- HOLD is cheaper than an INR
- Local desk for long ops; do not assume Netlify can wait on a supplier site

End of TOOLS.md
