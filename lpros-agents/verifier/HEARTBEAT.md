# VERIFIER — HEARTBEAT.md

On routine heartbeat:
- Confirm no PASS decisions exist without evidence logs
- Scan recent CONDITIONAL flags for uncleared `sold_evidence_missing` / `product_cost_missing`
- Remain idle if no candidates are in the gate

# Optional (comments-only until scheduled):
# - Re-audit last 10 PASS rows against outcome JSONL for false negatives

When idle: do not invent a queue. Wait for Scout packages.

End of HEARTBEAT.md
