# COMMS — Hive Contract Protocol

Binding runtime: `lpros-command/src/hive/`. Law still `AGENTS.md`. Geometry still `MEUFT.md`. Growth still `GROWTH.md`.

Agents do not “chat.” They exchange **TASK CONTRACTs** and **replies**. Heartbeat never sends unsolicited scrapes, crawls, or capital.

═══════════════════════════════════════════════════════════════════════════════
ENVELOPE
═══════════════════════════════════════════════════════════════════════════════

```json
{
  "id": "msg_…",
  "type": "contract | reply | veto | lesson | caption | hold",
  "from": "brain | scout | …",
  "to": "string",
  "contractId": "tc_… | null",
  "payload": {},
  "at": "ISO-8601"
}
```

**TASK CONTRACT payload (Brain → Soldier)**

```json
{
  "goal": "string",
  "inputs": {},
  "tools": ["string"],
  "constraints": {
    "tos": ["no_html_scrape", "no_replica", "no_photo_copy", "no_invented_sold"],
    "capital": "HOLD_DEFAULT"
  },
  "doneWhen": "IDENTITY output JSON",
  "onFailure": "HOLD | narrow | escalate"
}
```

**Reply payload (Soldier → Brain)**

```json
{
  "verdict": "string",
  "workersRan": ["string"],
  "workersSimulated": ["string"],
  "uncertainty": { "known": [], "estimated": [], "assumed": [] },
  "fourD": { "cash": "string", "time": "string", "policy": "string", "reputation": "string" }
}
```

Markdown packs are not Browse. Pack-only specialists still return `packOnly: true` even when their JS worker ran a **legal thesis / stress / ToS / caption / reverse-P&L / HOLD** function.

═══════════════════════════════════════════════════════════════════════════════
ROUTING (RULER DOWN)
═══════════════════════════════════════════════════════════════════════════════

1. Brain writes contracts. Soldiers do not spawn each other except Swarm (named workers).
2. Specialists (Joker, Bane, Mr. Robot, Memento, Tenet, Wick, Oracle) attack *arguments and residuals*, never platforms.
3. Fulfiller / Wick climate is HOLD until markers close.
4. Oracle lessons cite a job id, outcome row, or operator confirm — or they DEFER.
5. A veto from Compliance stops the workload. It does not become a how-to.

Desk: `POST /api/playground/hive/run`, `GET /api/playground/hive/comms`, `POST /api/playground/hive/condition`.

End of COMMS.md
