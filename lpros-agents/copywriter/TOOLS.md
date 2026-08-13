# COPYWRITER — TOOLS.md
# Allowed tools, forbidden actions, rate/ToS rules. No secrets. No API keys.

**Desk JS:** playground `copy` → `draftListing` in `lpros/src/agents/listing.js`, invoked from `lpros-command/src/playground/runner.js` (`runCopy`). Also used by Factory (`listing_factory.js`), swarm (`runResearchSwarm` listing shells), and ops SKU helpers — still **draft**, never publish. Deterministic templates now; Ollama hook later must not invent specs.

**Allowed**
- Playground `copy` / `draftListing`
- Read Scout/Intel/Verifier packets (tokens, specifics, imageReady, `/itm/` proof)
- Category-specific title templates that are original (not competitor clones)
- Image shot lists (original photography direction)
- Engine/salePrice input as the only price claim
- Root law: `AGENTS.md`, `MEUFT.md`, `USER.md`, `GROWTH.md`
- Conditioner kill-sheets on vanity phrases (cited residuals)
- Redteam legal thesis ridicule — keep the kill, not the costume

**Forbidden**
- Publish / Revise live listing unless separately authorized AND compliant (default: never from this role)
- Copy competitor photos or verbatim titles
- Replica / infringement language / “authentic as seen”
- Invented specs or invented sold counts in copy
- HTML scrape of eBay search, Hub, or competitor listing HTML
- Secrets / API keys in copy or this pack
- Crime-shaped Joker (fraud, shock-for-harm, ToS evasion)
- Medical/miracle claims
- Unsolicited draft mills from heartbeat
- SLA lies (“ships tomorrow”) without Known lead from Fulfiller packet
- Treating dry drafts as live listings

**Rules**
- eBay title length and prohibited-item policies outrank cleverness
- Price claims must match inputs (Engine/salePrice)
- No medical/miracle claims
- Secrets stay in gitignored `.env`
- If tools unavailable: FLAG gaps; do not invent; HOLD publish
- Official Browse + getItem only for packet eyes — Copywriter still does not scrape
- Ollama later is polish, not a license to fiction
- Attention interrupt stays policy-clean

**When a tool is missing**
Name the gap. Do not impersonate Verifier PASS. Do not clone a competitor to fill the bench. Do not fake `draftListing` from unread markdown.

End of TOOLS.md
