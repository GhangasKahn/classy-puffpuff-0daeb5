---
name: create-elite-agent
description: Spawn a new LPROS elite Hermes soldier with the full OpenClaw-style workspace (SOUL, IDENTITY, AGENTS, TOOLS, HEARTBEAT, MEMORY). Use when adding economist, orchestrator, fulfiller, copywriter, conditioner, or any new specialist under lpros-agents/.
---

# Create Elite Agent

Canonical copy lives at `lpros-agents/.cursor/skills/create-elite-agent/SKILL.md`. Follow that file.

## Law

Root `lpros-agents/AGENTS.md` is binding. Soldier `AGENTS.md` = procedures only.

## Atomic sequence

1. Read root constitution + `scout/` or `verifier/` as the bar.
2. Write `SOUL.md`, `IDENTITY.md`, `AGENTS.md`, `TOOLS.md`, `HEARTBEAT.md`, `MEMORY.md` under `lpros-agents/<id>/`.
3. Wire IDENTITY to desk JS if it exists.
4. Update `lpros-agents/README.md`.
5. Never put secrets in markdown. Never invent sold counts. Never scrape eBay search HTML.
