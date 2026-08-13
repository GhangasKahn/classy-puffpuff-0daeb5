# ORCHESTRATOR — TOOLS.md

**Allowed**
- `lpros/src/core/economics.js` (cite, do not rewrite)
- `lpros/src/core/evidence.js` / `verify.js` (read decisions)
- Playground `brain` merge in `lpros-command/src/playground/runner.js`
- Soldier outputs from scout, intel, crawler, economics, evidence, copy, factory, fulfill, browser, vm
- Watch VM status (Page/Term/Net/Proof) as proof of live research
- `brain/SYSTEM_PROMPT.md` + `brain/Meuft Brain Agent.json`

**Forbidden**
- HTML scrape of eBay search
- Inventing sold counts
- Soft-pass critical factors
- Publish / auto-order from Brain chat
- Claiming a stub worker ran
- Storing API keys in markdown

**Rules**
- Prefer reversible probes
- Local `:8790` for marathons; Netlify is short-lived
- Secrets stay in gitignored `.env`
- If tools unavailable: say so; continue with structured gaps

End of TOOLS.md
