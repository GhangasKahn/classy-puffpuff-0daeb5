# LPROS Agents (PrimeAgent)

MEUFT-structured agent pack. **Phase-1 = single agent: MEUFT Brain.**

## MEUFT (orchestration geometry)

| | Layer |
|---|--------|
| **M** | Mission & Mandate |
| **E** | Economics Engine (cash is truth) |
| **U** | Uncertainty & Evidence |
| **F** | Factor Verification (fail-closed) |
| **T** | Task Contracts & Conditioning |

Full constitution: [`AGENTS.md`](./AGENTS.md)

## Brain (only live agent)

| File | Purpose |
|------|---------|
| `brain/SYSTEM_PROMPT.md` | Long-form system prompt |
| `brain/CONDITIONING.md` | Description + cue→response plan |
| `brain/Meuft Brain Agent.json` | PrimeAgent flow import |
| `brain/meuft_brain_agent.py` | Programmatic graph + prompt card |

## Load into PrimeAgent

```bash
source /workspace/.venv-primeagent/bin/activate
# start UI (needs LLM key in env, e.g. OPENAI_API_KEY)
primeagent run
```

In the UI: **Import** → `lpros-agents/brain/Meuft Brain Agent.json`

Or verify prompts without UI:

```bash
source /workspace/.venv-primeagent/bin/activate
python lpros-agents/brain/meuft_brain_agent.py
```

## First session cue

Ask Brain:

> Evaluate “solid wood desk organizer” around $45–$65 for dropshipping. I do not have sold comps or dual supplier quotes yet.

Expect a **MEUFT BRIEF** ending **CONDITIONAL** / **HOLD**, not a fake PASS.

## Next (not yet)

Soldiers: Scout, Feature, Psych, Margin/Gate, Copy, Fulfill — each gets a TASK CONTRACT under Brain after cue-compliance mastery.
