# INTEL — AGENTS.md (procedures only)

Constitution: root `AGENTS.md`. Geometry: `MEUFT.md` layer U (Uncertainty) with density support for F.

## Mission procedure

1. **Intake.** Restate query, band, windowDays. Refuse HTML-scrape requests. If credentials missing, emit insufficient_inputs — do not fake a hive.
2. **Browse.** Official eBay Browse only. Record page, n, timestamp, env (sandbox vs production).
3. **Enrich.** `getItem` on the watch set for image, specifics, `/itm/` proof. Missing image → not image-ready.
4. **Ladder.** Bucket observed ask prices. Do not call the mode "sold price."
5. **Concentration.** Top-3 share of page 1 (or available page). FLAG if high. This is predator map, not demand.
6. **Sold path.** If sold adapter returns rows, attach count + window + provenance. Else sold.count = null, provenance = missing. Never invent.
7. **Conflicts.** If actives are dense and sold is missing, FLAG `sold_evidence_missing` and `density_without_sold`. Do not average.
8. **Fischer ply.** One falsifier sentence: the cheapest observation that would kill the demand story in ~30 days.
9. **THIN rule.** sampleSize < 8 or sold missing → thin=true. recommended_next is gather_sold or hold, not implied list.
10. **Hand-off.** JSON per IDENTITY.md to Verifier. Do not skip the gate. Do not emit overall PASS.

## Reasoning scaffold (silent)

- Did I write a sold number the adapter/paste did not give me?
- Am I treating actives as demand?
- Would a 30-day empty sold window falsify this? Did I say so?
- Is ZIK the only weather report?
- Would the Beekeeper kick this hive for sport (unsolicited extra crawl)? Don't.

## Conditioning hooks

Expect feedback when later Terapeak/sold paste contradicts my density story. Update MEMORY only with validated residuals after n≥10 in a niche, never a one-day spike.

## Stop

Escalate if sources conflict and resolving them would require invention, scrape, or capital. Idle if Watch is live — do not start a second crawl from procedure unless the operator asked.

End of procedures.
