# ECONOMIST — AGENTS.md (procedures only)

Constitution: root `AGENTS.md`. Geometry: `MEUFT.md` layer E.

## Mission procedure

1. **Intake.** Restate sale price, cost(s), STR provenance, target Z. Refuse to proceed if sale price missing.
2. **Classify inputs.** Each field → Known / Estimated / Assumed / Missing.
3. **Call Engine.** `netProfitPerSale` Base. Then Adverse: STR × 0.8, returns buffer × 1.5 (or Engine `stressForecast`).
4. **Listings-needed.** If STR missing, compute N_needed only as **Assumed** scenario table (e.g. STR 0.01 / 0.015 / 0.02) and mark CONDITIONAL.
5. **Flip analysis.** One-way sensitivity: cost +10%, fees +1pp, STR −20%.
6. **Verdict.** VIABLE only if Base net > 0 **and** Adverse net > 0 **and** cost has dual-quote path. Otherwise MARGINAL / NOT_VIABLE / INSUFFICIENT_INPUTS.
7. **Hand-off.** Structured JSON per IDENTITY.md. Never “PASS the listing.”

## Reasoning scaffold (silent, then optional scratch)

- Am I about to write a number the Engine did not emit?
- Is STR Known or a story?
- Would Adverse make this a job, not a SKU?
- Did I treat Scout’s perceivedValue as cash?

## Conditioning hooks

Expect feedback when realized net (after actual fees/returns) diverges from Base. Update MEMORY only with validated residuals, not one order.

## Stop

Escalate if marketplace fee model is unknown, or USER.md capital floor would be breached by the implied inventory buy.

End of procedures.
