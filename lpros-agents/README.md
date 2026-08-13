# LPROS Elite Agent System

First-principles agent engineering for **Hermes + Cursor**. Conditioning doctrine. Zero-trust. Cash is truth.

OpenClaw-style workspace: each live soldier is a folder of markdown. **The files are the agent.** They learn from cited residuals, communicate through JSON contracts, work under the Economics Engine, and accelerate only after fail-closed proof. Millionaire dropshipping is the **long-horizon target** (fee-true expectancy, not a slogan).

## Structure

```
lpros-agents/
├── AGENTS.md                          # Swarm constitution (binding law)
├── MEUFT.md                           # How Brain stages work (briefs + contracts)
├── USER.md                            # Operator card (Kyle; capital bar)
├── ROSTER.md                          # Inspiration → folder map
├── INSPIRATION.md                     # Lawful use of each mold
├── README.md
├── src/loadPack.js                    # Pack loader used by Command desk
├── .cursor/skills/create-elite-agent/
├── brain/                             # PrimeAgent Brain (prompt + JSON graph)
├── orchestrator/                      # Fischer × Dark Knight × Morpheus
├── scout/                             # Beekeeper × Neo × MacGyver
├── intel/                             # Beekeeper × Fischer
├── verifier/                          # Dark Knight × Accountant × Memento
├── economist/                         # Accountant × Fischer × Tenet
├── fulfiller/                         # Bane × Beekeeper
├── copywriter/                        # MacGyver × Ending Things × Joker
├── conditioner/                       # Oracle × Sidis
├── redteam/                           # Joker (legal chaos)
├── pressure/                          # Bane (Adverse/Severe)
├── compliance/                        # Mr. Robot (ToS)
├── taxonomy/                          # Sidis × Neo (crawler)
├── memento/                           # Memento (memory integrity)
├── inversion/                         # Tenet (reverse P&L)
└── factory/                           # MacGyver × Beekeeper
```

## Live packs

Every folder above (except `brain/` which is the PrimeAgent graph) has:

`SOUL.md` · `IDENTITY.md` · `AGENTS.md` · `TOOLS.md` · `HEARTBEAT.md` · `MEMORY.md`

| Pack | Mold | Desk JS today |
|------|------|----------------|
| orchestrator | Fischer × Dark Knight × Morpheus | playground `brain` |
| scout | Beekeeper × Neo × MacGyver | playground `scout` → Browse |
| intel | Beekeeper × Fischer | playground `intel` |
| verifier | Dark Knight × Bane × Accountant × Memento | playground `evidence` |
| economist | Accountant × Fischer × Tenet | playground `economics` |
| fulfiller | Bane × Beekeeper | playground `fulfill` |
| copywriter | MacGyver × Ending Things × Joker | playground `copy` |
| factory | MacGyver × Beekeeper | playground `factory` |
| taxonomy | Sidis × Neo | playground `crawler` |
| conditioner | Oracle × Sidis | pack-only (`conditioner`) |
| redteam | Joker × Ending Things | pack-only (`redteam`) |
| pressure | Bane × Tenet | pack-only (`pressure`) |
| compliance | Mr. Robot × Dark Knight | pack-only (`compliance`) |
| memento | Memento × Accountant | pack-only (`memento`) |
| inversion | Tenet × Fischer | pack-only (`inversion`) |

Pack-only soldiers launch from the Command playground and return the persona (excerpts + contracts). They do **not** pretend a markdown file ran Browse. Wire JS next; do not fake it.

Loader: `lpros-agents/src/loadPack.js`. API: `GET /playground/packs`.

## Core doctrine

- Conditioning > pure imitation training
- Authoritative structure + Pavlovian association
- ARC-AGI-3 style independent capability as baseline
- Hierarchical models (Brain sparse, Soldiers default)
- Fail-closed verification
- Economics Engine as numerical source of truth — no LLM fee math
- Explicit uncertainty (Known / Estimated / Assumed)
- Auditable evidence trails
- Official Browse + getItem only. No eBay HTML search scrape. No competitor photo copy. No invented sold counts.

Villain molds (Joker, Bane, Mr. Robot) are **legal red-team / stress / ToS**. They do not commit crime, fraud, or unauthorized access.

## How to create additional elite agents

Use the `create-elite-agent` skill. Follow the atomic sequence. Every new agent must receive the full six-file set.

PrimeAgent import (Brain graph) is unchanged: `brain/Meuft Brain Agent.json`.
