---
name: create-elite-agent
description: Spawn a new LPROS elite Hermes soldier with the full OpenClaw-style workspace (SOUL, IDENTITY, AGENTS, TOOLS, HEARTBEAT, MEMORY). Use when adding a specialist under lpros-agents/ or when a playground catalog agent has JS but no prompt pack. Live roster already includes orchestrator (ruler), scout, intel, verifier, economist, fulfiller, copywriter, conditioner, redteam, pressure, compliance, taxonomy, memento, inversion, factory, wick, browser, vm, swarm.
---

# Create Elite Agent

## When to use

- User asks for a new Hermes / LPROS soldier or specialist
- Folders under `lpros-agents/` exist with only a README
- A playground catalog agent has JS but no prompt pack

## Law

Root `lpros-agents/AGENTS.md` is binding. The new soldier’s `AGENTS.md` is **procedures only**. Do not write a second constitution. Cash is truth. Fail-closed. No invented sold counts. No eBay HTML search scrape. No competitor photo copy.

## Atomic sequence (do not skip)

1. **Name the slot** — lowercase kebab-case id not already in `ROSTER.md`.
2. **Read** root `AGENTS.md`, `GROWTH.md`, `USER.md`, `MEUFT.md`, and a complete live pack (`orchestrator/` as the ruler bar, or `scout/` / `verifier/`) as the quality bar.
3. **Write six files** in `lpros-agents/<id>/`:

| File | Contains | Does not contain |
|------|----------|------------------|
| `SOUL.md` | Identity, mythos (lawful take/refuse), battlefield, millionaire path, 15–20 expectations, communication, Pavlovian +/−, voice samples, failure modes, autonomy gradient (outperform day one) | Workflows, tool lists, crime how-tos |
| `IDENTITY.md` | Tier, owns / does not own, hard boundaries, JSON input/output contract, escalation | Personality essays |
| `AGENTS.md` | Numbered mission procedure, reasoning scaffold, conditioning hooks, stop conditions | Swarm law |
| `TOOLS.md` | Allowed tools with paths, forbidden actions, rate/ToS rules | Secrets |
| `HEARTBEAT.md` | Light pulse + idle behavior. Comments-only for expensive checks | Broad unsolicited scrapes |
| `MEMORY.md` | What may be remembered, what must never be stored as fact, growth/prune rules | One-off spikes as “demand” |

4. **Wire** — one line in IDENTITY: desk JS (`lpros-command/src/playground/runner.js` case) and/or `lpros/src/agents/*`. If JS is missing, say so; do not fake a live runner.
5. **Update** root `lpros-agents/README.md` live-pack table, `ROSTER.md`, `INSPIRATION.md`, `GROWTH.md` if the learning loop changes, `src/loadPack.js` `ELITE_PACKS`, and playground `catalog.js` (`hermesPack` / `packOnly`).
6. **Do not** put API keys in any markdown. Do not gitignore SOUL/IDENTITY (those are the agent). `USER.md` may be gitignored if it grows private.

## Quality bar (reject the draft if)

- Soft-pass language on Supply / Economics / Compliance
- ZIK as sole demand authority
- LLM arithmetic replacing the Economics Engine
- HEARTBEAT that starts unsolicited scrapes
- MEMORY that stores unverified costs or invented sold counts
- Missing JSON output contract in IDENTITY

## After spawn

Tell the operator: pack is markdown-ready; JS worker may still be a stub. Next is wiring or a live Watch/playground launch — not capital.
