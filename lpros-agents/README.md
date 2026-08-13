# LPROS Elite Agent System

First-principles agent engineering for **Hermes + Cursor**. Conditioning doctrine. Zero-trust. Cash is truth.

OpenClaw-style workspace: each live soldier is a folder of markdown. **The files are the agent.** They learn from cited residuals (`GROWTH.md`), communicate through JSON contracts, work under the Economics Engine, and accelerate only after fail-closed proof. Millionaire dropshipping is the **long-horizon target** (fee-true expectancy, not a slogan).

Restart order is **ruler down**: Orchestrator (Fischer × Dark Knight × Morpheus), then Soldiers, then Specialists. Day-zero over-HOLDs. Day-N outperforms day-zero inside the constitution — never around it.

## Structure

```
lpros-agents/
├── AGENTS.md                          # Swarm constitution (binding law)
├── GROWTH.md                          # Day-zero → day-N; 4D; residual loop
├── MEUFT.md                           # How Brain stages work (briefs + contracts)
├── USER.md                            # Operator card (Kyle; capital bar)
├── ROSTER.md                          # Inspiration → folder map
├── INSPIRATION.md                     # Lawful use of each mold
├── README.md
├── src/loadPack.js                    # Pack loader used by Command desk
├── .cursor/skills/create-elite-agent/
├── brain/                             # PrimeAgent Brain (prompt + JSON graph)
├── orchestrator/                      # RULER — Fischer × Dark Knight × Morpheus
├── scout/                             # Beekeeper × Neo × MacGyver
├── intel/                             # Beekeeper × Fischer
├── taxonomy/                          # Sidis × Neo (crawler)
├── browser/                           # Neo × MacGyver
├── verifier/                          # Dark Knight × Accountant × Memento
├── economist/                         # Accountant × Fischer × Tenet
├── inversion/                         # Tenet × Fischer
├── memento/                           # Memento × Accountant
├── fulfiller/                         # Shinobi / Last Samurai × Bane
├── wick/                              # John Wick (consequence / HOLD)
├── copywriter/                        # MacGyver × Ending Things × Joker
├── factory/                           # MacGyver × Beekeeper
├── conditioner/                       # Oracle × Sidis
├── redteam/                           # Joker (legal chaos)
├── pressure/                          # Bane (Adverse/Severe)
├── compliance/                        # Mr. Robot (ToS)
├── swarm/                             # Beekeeper × Morpheus
└── vm/                                # MacGyver × Accountant
```

## Live packs

Every folder above (except `brain/` which is the PrimeAgent graph) has:

`SOUL.md` · `IDENTITY.md` · `AGENTS.md` · `TOOLS.md` · `HEARTBEAT.md` · `MEMORY.md`

| Pack | Mold | Desk JS today |
|------|------|----------------|
| orchestrator | Fischer × Dark Knight × Morpheus | playground `brain` |
| scout | Beekeeper × Neo × MacGyver | playground `scout` → Browse |
| intel | Beekeeper × Fischer | playground `intel` |
| taxonomy | Sidis × Neo | playground `crawler` |
| browser | Neo × MacGyver | playground `browser` |
| verifier | Dark Knight × Bane × Accountant × Memento | playground `evidence` |
| economist | Accountant × Fischer × Tenet | playground `economics` |
| inversion | Tenet × Fischer | pack-only (`inversion`) |
| memento | Memento × Accountant | pack-only (`memento`) |
| fulfiller | Shinobi / Last Samurai × Bane × Beekeeper | playground `fulfill` |
| wick | John Wick × Dark Knight | pack-only (`wick`) |
| copywriter | MacGyver × Ending Things × Joker | playground `copy` |
| factory | MacGyver × Beekeeper | playground `factory` |
| conditioner | Oracle × Sidis | pack-only (`conditioner`) |
| redteam | Joker × Ending Things | pack-only (`redteam`) |
| pressure | Bane × Tenet | pack-only (`pressure`) |
| compliance | Mr. Robot × Dark Knight | pack-only (`compliance`) |
| swarm | Beekeeper × Morpheus | playground `swarm` |
| vm | MacGyver × Accountant | playground `vm` |

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
- Official Browse + getItem only. No eBay HTML search scrape. No competitor photo copy. No invented sold counts
- Growth via `GROWTH.md`: 4D (Cash, Time, Policy, Reputation); residuals; outperform day one **inside** the gate

Villain molds (Joker, Bane, Mr. Robot) and consequence molds (Wick, Shinobi) are **legal red-team / stress / ToS / logistics**. They do not commit crime, fraud, or unauthorized access.

## How to create additional elite agents

Use `.cursor/skills/create-elite-agent/SKILL.md`. Quality bar is the orchestrator pack plus `GROWTH.md`.
