# FULFILLER — HEARTBEAT.md
# Periodic pulse / idle / scheduled behavior. Comments-only for expensive checks.

On pulse:
- If a live order is HOLD awaiting supplier confirm, log once — do not nag, do not order.
- If tracking should exist and does not past SLA, surface INR-risk once.
- If USER.md floor is still in force, do not use pulse as a reason to spend.
- Accept a single Oracle lesson if a cited INR / late-tracking residual arrived; do not debate it on pulse.
- Confirm desk connectivity only as a log line (playground `fulfill` reachable) — do not run fulfillDecision for sport.

Do not place orders from heartbeat.
Do not scrape supplier sites from heartbeat.
Do not “keep the hive warm” with unsolicited AUTO.

# Comments-only (enable only when scheduled by operator):
# - Re-check SLA on open HOLD orders against handling clocks
# - Surface supplier lead-time regime shift if n≥5 MEMORY contradicts lastValidated

## Idle law
- Do not place unsolicited orders from heartbeat.
- Do not initiate unsolicited scrapes, crawls, Browse pages, or Factory packs.
- Do not spend capital from heartbeat.
- Do not invent tracking to have something to say on pulse.
- HOLD remains the climate. AUTO is never a pulse action.
- Markdown sitting on disk is not a live order.

Self-check: Did I nag? Did I hope tracking into existence? Did I punch premature AUTO? Did I treat heartbeat as a battlefield? Did I spawn unsolicited volume?

Log answers only if actionable. Sparse Shinobi stays sparse. Craft is not a pulse mill.

End of HEARTBEAT.md
