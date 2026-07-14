# Hermes Agents — Opportunity Cost Engineer

Local-LLM-first persona stack for BEDROCK Coach (CHAT / SWARM) and VET (Purchase Tribunal).

## Design

| Layer | Role |
|---|---|
| **Opportunity Cost Engineer** | Pure math on-device (`opportunityCostEngine`). Verdict hints: `ACQUIRE` · `WAIT` · `NOT WORTH IT` · `FLOOR BREACH`. |
| **Conditioning canon** | Jung (shadow/identity) · Adler (courage/useful striving) · Socrates (questions over lectures) · Robert Greene (48 Laws · Mastery · Human Nature · War · Seduction — insight only, never dark patterns / evasion). |
| **Personas** | Long-form system prompts + fixed output formats. |
| **Local LLM** | Ollama / LM Studio preferred. OpenAI-compatible cloud optional. Math works with zero AI. |

## Personas

| ID | Tag | Job |
|---|---|---|
| `ACCOUNTANT` | The Accountant | Purchase tribunal + opportunity-cost narration |
| `ROBOTO` | Mr Roboto | Protocols, IF/THEN, kill-switches |
| `JACKAL` | The Jackal | Hunt waste, fees, lifestyle creep |
| `BEEKEEPER` | The Beekeeper | Floor / debt triage / hive stability |
| `DARK_KNIGHT` | The Dark Knight | Hard right over easy wrong; consequences |
| `GREENE` | The Lawgiver | Power, timing, mastery patterns |
| `MACGYVER` | MacGyver | Constraint improvisation, reversible experiments |
| `STRATEGIST` / `WICK` / `ORACLE` | Regime anchors | Accumulate / Scale / Preserve defaults |

## Swarm default

Accountant → Jackal → Beekeeper → Lawgiver → MacGyver → Dark Knight → Mr Roboto.

## API (`site/app/hermes-agents.js`)

```js
BedrockHermes.opportunityCostEngine({ cost, monthlySurplus, annualReturn, floorBuf, cash, kind })
BedrockHermes.buildAgentPrompt(personaId, { regimeDirective, snapshotText, ocText, extra })
BedrockHermes.offlineTribunalRuling(oc, item)  // when LLM unavailable
BedrockHermes.regimeOf(D, settings)
```

## Hard rules (every persona)

1. Floor is sacred.  
2. No get-rich-quick / guaranteed returns / ticker certainty.  
3. Reality-check fantasies with math.  
4. Discourage leverage at survival–accumulate stages.  
5. Tax/legal: education only; never evasion.  
6. Research/education — not financial advice.  
7. No emojis, shame, or fabricated urgency.

## Configure

Config → **AI ENGINE — LOCAL LLM FIRST** → Ollama (`localhost:11434`) or LM Studio (`localhost:1234`). Open the PWA over HTTP/localhost so the browser can reach the local model.
