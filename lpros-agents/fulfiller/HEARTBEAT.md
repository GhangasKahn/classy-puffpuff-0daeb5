# FULFILLER — HEARTBEAT.md

On pulse:
- If a live order is HOLD awaiting confirm, log once.
- If tracking should exist and does not past SLA, surface INR-risk once.
- Do not place orders from heartbeat.
- Do not scrape supplier sites from heartbeat.

Idle otherwise.

## Idle law
- Do not place unsolicited orders from heartbeat.
- Do not scrape supplier sites.
- HOLD remains the climate. AUTO is never a pulse action.

Self-check: Did I hope tracking into existence? Did I punch premature AUTO?

End of HEARTBEAT.md
