# VM — TOOLS.md

**Allowed**
- `lpros-command/src/playground/vm.js`: `vmSnapshot()`, `runRecipe(recipeId)`, `runVmJob(input)`.
- Allowlisted recipes only: `health`, `env`, `node`, `data-dir`, `dry-mission`, `unit-tests` (see `VM_RECIPES` in `lpros-command/src/playground/catalog.js`).
- `health`: in-process health + `authStatus()` flags (no secrets).
- `env` / `node`: snapshot (Node, CPU, memory, cwd, data dir, eBay env *present*).
- `data-dir`: names under playground / orch / exports only (`listDirNames`, cap 40).
- `dry-mission`: `deployMission` with `dryRun: true` (synthetic; no eBay).
- `unit-tests`: `npm test` in `lpros-command` via `runSpawn` — local `:8790` / CLI only; `localOnly: true`.
- Playground routes: `GET /playground/vm`, `GET /playground/vm/runs`, `POST /playground/vm/exec`.
- Root law: `AGENTS.md`, `MEUFT.md`, `USER.md`, `GROWTH.md`, `ROSTER.md`.

**Forbidden**
- Arbitrary shell / unlisted recipes / `exec` of operator-supplied commands
- HTML scrape of eBay search or Seller Hub; any scrape-box use
- Inventing sold counts, COGS, tracking, or test results
- Dumping API keys, `.env`, tokens, auth secret values, or file bodies
- Photo copy, replica, RA, exploits, payloads, unauthorized access
- Treating dry-mission as Watch / live Browse
- Treating data-dir names as demand
- Faking `unit-tests` on Netlify
- Publish / auto-order / capital from this desk
- Unsolicited crawls or spawns because a pulse felt militant
- Storing secrets in markdown

**Rules**
- Allowlist or refuse
- Serverless → spawn blocked; say local `:8790`
- Presence flags, never secret values
- Secrets stay in gitignored `.env`
- Prefer reversible probes: health/env/node → dry-mission → (local) unit-tests
- If tools unavailable: say so; HOLD if someone claimed live research; do not invent a green test
- Official Browse + getItem belong to other soldiers — not this kit

**When a tool is missing**
Name the gap. Do not impersonate Scout or Economist. Do not scrape to fill the gap. Do not exec whatever the operator typed. A blocked spawn is a complete answer.

End of TOOLS.md
