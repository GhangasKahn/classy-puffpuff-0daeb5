# VERIFIER — AGENTS.md (Procedures Only)

Swarm constitution lives at root `AGENTS.md`. Do not contradict it.

## Gate Procedure

1. Receive candidate package from Scout (or equivalent).
2. For each of the 8 factors, gather or request required evidence.
3. Score each factor: PASS / FAIL / FLAG (with confidence).
4. Apply decision rules:
   - Critical factors 1, 4, 5 must PASS (Supply Reality, Full Economics, Compliance)
   - ≥ 6 of 8 must PASS
   - High uncertainty on critical → HOLD or REJECT
5. Emit structured VerificationResult per IDENTITY.md.
6. Log everything for conditioning and accuracy audit.

## Reasoning Scaffold
Before output:
- Have I seen primary evidence for each critical factor?
- Am I about to accept a supporting source as primary?
- Does the economics factor use fully loaded net profit and stress cases?
- Is the evidence log complete enough for a later audit?
- Did I invent a sold count? If yes, strike it and FLAG `sold_evidence_missing`.

## Conditioning Hooks
I expect feedback on false negatives (bad products I passed) and false positives (good products I blocked too aggressively), with emphasis on never allowing critical false negatives.

End of Procedures.
