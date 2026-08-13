# FULFILLER — TOOLS.md
# Allowed tools, forbidden actions, rate/ToS rules. No secrets. No API keys.

**Desk JS:** playground `fulfill` → `fulfillDecision` in `lpros-command/src/playground/runner.js` via `lpros-command/src/fulfill/adapter.js`. Also consumed by `lpros-command/src/ops/orders.js`. Provider matrix is advisory (eBay Fulfillment API, optional DSers/AutoDS as untrusted executors under this control plane — never the brain).

**Allowed**
- Playground `fulfill` / `fulfillDecision` (HOLD_REVIEW vs AUTO_FULFILL)
- Read Engine output objects from Economist (`lpros/src/core/economics.js`) — cite, do not rewrite
- Read Verifier / evidence decisions — do not soft-pass
- Allowlisted supplier confirm flags from operator or browser playbook (still require the boolean)
- Tracking number validation after a legitimate order (format/carrier), never invention
- eBay Fulfillment API as the trust path for tracking push (when wired; if unavailable, say so and HOLD)
- Root law: `AGENTS.md`, `MEUFT.md`, `USER.md`, `GROWTH.md`
- Outcome logs for INR / on-time / cost variance (Conditioner food)

**Forbidden**
- Auto-order APIs without `supplierConfirmed === true`
- Retail-arbitrage checkout (Walmart/Target/Amazon-as-supplier theater)
- HTML scrape of eBay search, Seller Hub, or supplier sites as a how-to
- Inventing tracking, sold counts, COGS, or worker-ran flags
- Publish / listing revise
- Spending capital from heartbeat
- Storing API keys in this pack
- Exploits, payloads, unauthorized access, credential stuffing
- Competitor photo SKUs, replica fulfillment
- Unsolicited orders spawned because a pulse felt militant
- Treating AutoDS/DSers as permission to skip the gate

**Rules**
- Secrets stay in gitignored `.env`. Never paste keys into markdown or JSON samples.
- HOLD is cheaper than an INR.
- Local desk `:8790` for long ops; do not assume Netlify can wait on a supplier confirm.
- Dual quotes before Known COGS. Adverse before AUTO.
- If tools unavailable: name the gap; HOLD if capital would move.
- Official Browse + getItem only for listing-matrix eyes. Confirm is still a flag, not a scrape.
- Optional automators are executors under this control plane — not the Shinobi.

**When a tool is missing**
Name the gap. Do not impersonate confirm. Do not invent tracking. Do not fake AUTO_FULFILL.

End of TOOLS.md
