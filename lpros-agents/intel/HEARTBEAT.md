# INTEL — HEARTBEAT.md

On pulse:
- If a Watch is live, confirm Page/Term/Net/Proof still updating.
- If stalled > 90s with no page increment, surface STALL once.
- Do not start a new crawl from heartbeat.
- Do not scrape.
- If last packet is THIN solely for missing sold paste, log once — do not nag.

# Optional:
# - Re-read last conflictFlags if operator pasted Terapeak since last pulse

Idle otherwise.

## Idle law
- Do not start unsolicited crawls or HTML scrapes from heartbeat.
- Do not invent sold counts to clear THIN.
- Watch STALL notes once; do not nag.

Self-check: Did I treat actives as demand? Did I kick the hive for sport?

End of HEARTBEAT.md
