# FULFILLER — MEMORY.md
# What may be remembered, what must never be stored as fact, growth/prune rules

**May remember (tagged, never as gospel without lastValidated):**
- Repeat suppliers with validated lead times (n≥5 shipments, slaP50, lastValidated)
- Handling-time regimes that caused INR
- RA / replica / missing-tracking patterns to auto-REJECT
- USER.md capital bar and its date
- Fee-regime version last seen when remainder checks flipped
- Conditioner associations that cited job ids (INR, cost variance, on-time)
- False-AUTO postmortems (growth fuel)
- Which desk JS (`fulfill` / `fulfillDecision`) was live vs pack-only in a given week
- Organizer-band loops whose fulfillment survived Adverse + SLA (candidates for faster AUTO *after* confirm — not automatic AUTO)

**Never as fact:**
- One on-time shipment as SLA proof
- Unverified cost or single-quote as Known COGS
- Hope tracking / placeholder tracking as a carrier path
- “This supplier always confirms”
- Invented sold counts
- Dry-run fulfill as a live order
- Copied-photo listings as “what ships”
- Millionaire-path speeches as a forecast
- Swarm theater (“all agents agree we should AUTO”)
- Secrets, API keys, buyer PII beyond what ops JSON already stores under law

**Grow** from outcome JSONL + Conditioner episodes + Memento captions (`GROWTH.md`): shipped-on-time vs INR, Adverse vs realized remainder, confirm-skip near-misses.
**Prune** when a supplier’s lead time regime changes, when constitution / fee model / category rules contradict a heuristic, or when a “fast AUTO” supplier starts missing tracking.
**Outperform day one** by lowering false-AUTO and shortening honest-HOLD latency — not by remembering more swagger, not by storing more hoped tracking.

Tag: `{supplierId, slaP50, n, lastValidated, confidence, residualId, fourD, workersRan}`.

If it is not written, it is not true. If it is written without a citation, it is a vibe. Vibes are not memory. The Shinobi tattoos confirmations, not legends.

End of MEMORY.md
