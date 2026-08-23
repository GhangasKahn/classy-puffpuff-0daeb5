# Hearth OS — End-to-End Engineering Report
## Cursor + Grok 4.6 High Fast vibe-build pack

**Date:** 2026-08-18  
**Locale:** Erie County, NY  
**Household:** 3 adults. Private health is not a group topic.  
**Baseline:** `/home/workdir/artifacts/hearth-os` already contains a working MVP.

---

## VERDICT

Do not restart from a blank Next.js template. Finish the existing FastAPI + SQLite + rooms system in phases. Each Cursor chat does one phase. Grok 4.6 High Fast executes the prompt. You only merge when the phase acceptance tests pass.

This is a kitchen control system. It is not a clinic, not a wellness brand, not Telegram.

---

## REALITY

### What already exists and has been exercised
- PIN login, person switcher
- Erie County seed prices, Tops-vs-Aldi store split
- Jasmine rice + potatoes, no organs, no Kerrygold, no keto
- Week plan + check-off list (~$101 cart under a $110 cap)
- House room (aliases) + private room (encrypted at rest)
- Quiet needs: private “stomach flu” adds broth/ginger with no name
- Deterministic engines when `XAI_API_KEY` is absent
- 8 unit tests

### What does not exist
- Real Signal-grade E2E
- Reliable weekly-ad scrape
- Per-device identity (only household PIN)
- Production TLS / Tailscale compose that you have deployed
- Verified live Grok tool-calling in production
- Medical diagnosis, genetics, or treatment logic (and it must not)

### Threat model (zero-trust)
| Threat | Current control | Residual |
|---|---|---|
| Sibling/spouse reads private flu note | Room ACL + different Fernet scope | Shared tablet + same PIN |
| Ad scrape lies | Seed + manual upsert is source of truth | Stale prices |
| Agent invents a diet | House law in code | Grok can still ramble if unconstrained |
| App claims to treat cancer | Forbidden | Prompt leakage |
| Box on the open internet | Do not | Compromise of all rooms |
| SQLite on overlay/NAS | WAL optional | Backup discipline |

Honest crypto: **server-mediated encryption at rest**. Agents must decrypt private notes to shop. Other family members cannot. That is the designed trade.

---

## GOVERNING PRODUCT CONCEPT (Siteforge)

**Name:** Hearth  
**Governing idea:** A sealed larder. Food in. Names and diagnoses out.

**Emotional genome**  
Opening: fatigue, expense, distrust of US grocery theater.  
Exit: tonight’s meal is decided, the list is split by store, nobody had to announce they were sick.

**Character**  
Authoritative, restrained, intimate, heritage-material, large-type, zero wellness chrome.

**Visual law**
- Background: `#161310` timber-dark
- Accent: `#e0a35a` brass
- Type: ≥18px, Palatino/Georgia stack
- Tap targets ≥48px
- No purple orbs, no bento marketing, no “unlock your potential”
- Motion: none except check-off and room switch. `prefers-reduced-motion: reduce`

**Signature interaction**  
Two rooms. House vs Private. Agents named. Members aliased.

**Proof the UI may use**
- This week’s dollar total
- Store split
- Sale end dates
- Protein grams from the cart (an estimate, labeled as estimate)

**Proof the UI must not use**
- Invented testimonials, health outcomes, “therapeutic,” “anti-cancer foods,” “cures”

---

## MEDICAL / NUTRITION CONSTRAINTS
### Epistemic Prime + Medical-Genetic Prime — what the software may encode

**Allowed as operational kitchen rules (not treatment):**
- Energy and protein first if a person is flagged “cancer track” (user-set flag, not a diagnosis engine).
- Default floors if weight is known: protein ≥1.2 g/kg; energy ≥25 kcal/kg. If weight unknown, use 70 kg placeholder and label it.
- Fully cook eggs and meat when the cancer-track flag is on.
- 3-day leftover rule.
- Soft-texture variants when the user sets that flag.
- Private symptoms may add bland-food SKUs (bananas, rice, broth, ginger) with **no reason text** on the list.

**Forbidden:**
- Diagnosing cancer, flu, genetics, deficiencies.
- Claiming keto, jasmine rice, polyphenols, or sardines treat cancer.
- Organ-meat “protocols.”
- Drug–food interaction engines unless a later phase cites a primary source per item.
- Storing diagnosis strings on `MealPlan.notes` or shopping item names.

**Mandatory methylation / mitochondrial audit (epistemic requirement, software implication):**  
The app does **not** model MTHFR, ETC, or BHB. Data void. Do not add supplement protocols to close the void.

**Confidence:** Kitchen logistics high. Clinical effect of any food pattern on cancer or disability: **not in scope**.

---

## TARGET STACK (do not change without a phase)

- Python 3.12, FastAPI, Jinja2, HTMX-optional later
- SQLite + foreign keys (one household)
- Fernet derived from `SECRET_KEY` + room scope
- Grok via `https://api.x.ai/v1` , model `grok-4` or whatever 4.6 is named in your key’s catalog
- PWA (manifest + service worker for CSS/JS only)
- Deploy: LAN or Tailscale, Docker Compose
- Tests: pytest on engines, privacy, store-split

Do not introduce Next.js, Postgres, Redis, or auth vendors in Phases 0–8.

---

## CURSOR HARNESS RULES

1. New Cursor chat per phase. Paste the **entire** phase prompt.
2. Model: **Grok 4.6 High Fast**.
3. Open the `hearth-os` folder as the workspace.
4. After the agent finishes: run `PYTHONPATH=. python3 -m pytest -q` and click through the phase acceptance list.
5. If a test fails, stay in that chat. Do not start the next phase.
6. Commit: `git add -A && git commit -m "phase N: <slug>"`
7. Never let the agent “improve” food law, add keto, or add organ meats.
8. Never let the agent scrape a paywall or store a medical narrative on the shopping list.

---

## PHASE 0 — Baseline audit
**Goal:** Prove the existing app boots and you know the map.

### Tasks
- [ ] Create venv, install `requirements.txt`
- [ ] Copy `.env.example` → `.env`; set `HOUSEHOLD_PIN`, `SECRET_KEY`
- [ ] `PYTHONPATH=. python3 -m pytest -q`
- [ ] `PYTHONPATH=. python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8080`
- [ ] Login PIN, rebuild week, confirm Tops vs Aldi split
- [ ] House message vs private flu message; confirm ginger/broth appear unnamed

### Cursor prompt — Phase 0
```
You are in /hearth-os. Do not rewrite the app.

1. Read README.md, ENGINEERING_REPORT.md, app/main.py, app/agents/harness.py, app/services/shopping.py, app/services/rooms.py.
2. Produce AUDIT.md with:
   - file map
   - what works
   - what is stubbed
   - threat model leftovers
   - exact commands to run tests and the server
3. Run pytest. Paste the result in AUDIT.md.
4. Do not change product behavior.

Stop when AUDIT.md exists and tests pass.
```

**Proof:** `AUDIT.md` + 8 passing tests.  
**Recovery:** If import errors, fix `requirements.txt` only.

---

## PHASE 1 — Secrets, config, migrate
**Goal:** Production-shaped config without changing UX.

### Subtasks
- [ ] Refuse to boot if `SECRET_KEY` is the example string when `ENV=prod`
- [ ] `HOUSEHOLD_ENC_KEY` optional; if set, use it instead of `SECRET_KEY` for Fernet
- [ ] SQLite path configurable; create parent dir
- [ ] Health endpoint includes db-writable check
- [ ] `.gitignore` covers `.env`, `data/`, `__pycache__`

### Cursor prompt — Phase 1
```
Workspace: hearth-os. Model constraints: do not touch meal math or chat UX.

Harden app/config.py, app/db.py, app/main.py:
- Add ENV=dev|prod.
- In prod, abort startup if SECRET_KEY contains "change-me" or HOUSEHOLD_PIN is 4829.
- Add optional HOUSEHOLD_ENC_KEY used by app/services/crypto.py; fallback SECRET_KEY.
- GET /health returns {ok, db, grok, version}.
- db is true only if a sqlite write+read succeeds.

Add tests/test_health_and_config.py for the health shape (dev mode).
Keep existing tests green.

Do not add Postgres.
```

**Proof:** health JSON; prod boot fails on default secrets.  
**Recovery:** leave ENV=dev.

---

## PHASE 2 — Identity and rooms (privacy lock)
**Goal:** Aliases default; private rooms cannot be read by swapping query params.

### Subtasks
- [ ] `ensure_aliases` on every startup
- [ ] GET `/chat?room=private` without a person session → house
- [ ] Cannot fetch another person’s private messages by id
- [ ] Vault ciphertext never returned in HTML (only decrypted for authorized room)
- [ ] House `VaultMessage.person_id` is always NULL
- [ ] Login screen: show aliases, not legal names (legal names stay in DB)

### Cursor prompt — Phase 2
```
Workspace: hearth-os.

Tighten privacy in app/services/rooms.py, app/auth.py, app/routers/pages.py, templates/login.html:

1. House posts never store person_id.
2. read_private(household_id, person_id) is the only private reader. No route accepts a target_person_id from the query string.
3. Login select options use alias only. Value remains person.id.
4. Add tests/test_rooms_acl.py:
   - encrypt/decrypt isolation (already in test_privacy.py — keep)
   - posting house does not persist person_id
   - applying quiet needs does not write "flu" into ShoppingItem.name or MealPlan.notes

Do not implement Signal protocol.
Do not log plaintext private messages to stdout.
```

**Proof:** pytest + manual: two sessions, person 2 cannot see person 1 private HTML.  
**Recovery:** if templates break, Starlette TemplateResponse is `TemplateResponse(request, name, context)`.

---

## PHASE 3 — Nutrition engine (no clinic)
**Goal:** Numbers only. Flags are user-set.

### Subtasks
- [ ] `person_need` keeps cancer floor if flag set
- [ ] Label outputs “estimate”
- [ ] Soft-food flag only changes cook-sheet verbs
- [ ] Add `tests/test_nutrition.py` cases for unknown weight (70 kg placeholder)

### Cursor prompt — Phase 3
```
Workspace: hearth-os.

In app/services/nutrition.py and templates that show protein/kcal:
- Keep cancer-track floors: protein max(user, 1.2 g/kg), kcal max(user, 25 kcal/kg).
- If weight_kg is None, use 70.0 and surface the word "estimate" and "weight unknown".
- Do not mention disease names in shopping or meal titles.
- Do not add supplements, genes, keto, or organ meats.
- Extend tests accordingly.

No new dependencies.
```

**Proof:** tests; UI says estimate.  
**Stop:** any sentence that claims food treats cancer — delete it.

---

## PHASE 4 — Catalog, ads, store split
**Goal:** Live prices are data. Seeds are the floor.

### Subtasks
- [ ] Catalog keys stay stable (`chicken_quarters`, `jasmine_rice`, …)
- [ ] `upsert_ad` from Money form
- [ ] Scout fetch of Tops page is best-effort; store raw text in a `AdFetch` table, do not parse as gospel
- [ ] Chicken sale logic: price ≤1.29 and sale_ends ≥ today → Tops
- [ ] After 2026-08-22 default seed, chicken is not assumed $0.99 unless an ad says so

### Cursor prompt — Phase 4
```
Workspace: hearth-os.

Upgrade app/services/ads.py and shopping.py:

1. Add model AdFetch(id, store, fetched_at, url, ok, text_excerpt).
2. fetch_tops_ad_text stores an AdFetch row even on failure.
3. build_shopping_plan uses ad table first, catalog second.
4. If chicken_quarters has no live sale, do not force store=tops.
5. Tests:
   - $0.99 through sale_ends → Tops
   - $1.79 after sale_ends → note "not live"
6. Jasmine rice remains the only bulk rice. Quinoa optional 1 lb.

Do not add ground beef as a staple.
Do not invent coupon stacking.
```

**Proof:** unit tests for sale window.  
**Recovery:** seed prices remain if fetch fails.

---

## PHASE 5 — Grok 4.6 agent harness
**Goal:** Tools do the work. Prose does not mutate the database except through tools.

### Subtasks
- [ ] Model name from env (`XAI_MODEL=grok-4` or 4.6 id)
- [ ] Tool loop max 8
- [ ] House system prompt: never name a person, never repeat medical text
- [ ] Private system prompt: Care may apply quiet needs, then speak only to that person
- [ ] If API errors, fallback engines still build the week
- [ ] Redact private plaintext from any house-bound tool result

### Cursor prompt — Phase 5
```
Workspace: hearth-os.

Upgrade app/agents/harness.py, prompts.py, tools.py.

1. Keep tools: get_household_state, get_current_ads, fetch_tops_circular, upsert_ad, build_week.
2. Add tool apply_quiet_from_private_text(text) usable only when room=private.
3. System prompt must include: agents are named Kitchen|Scout|Budget|Care; members are aliases; never copy private symptom words into MealPlan.notes or house messages.
4. On httpx errors, call the existing deterministic fallbacks.
5. Add tests/test_harness_fallback.py that monkeypatches missing API key and asserts persist_week still runs from "build this week".

Do not send the entire private history into a house completion.
Do not print API keys.
```

**Proof:** no key → fallback works; with key → tool calls only change state.  
**Recovery:** leave key unset.

---

## PHASE 6 — UI (Siteforge pass)
**Goal:** Mom/Dad can use it on a phone. No AI-slop look.

### Subtasks
- [ ] Keep color/type already in `app/static/app.css`
- [ ] Rooms tab contrast, focus rings
- [ ] Checkboxes 48px
- [ ] `prefers-reduced-motion`
- [ ] Error text in plain language
- [ ] Home “Tonight” uses first upcoming dinner, not always meals[0] if you can use weekday
- [ ] Remove any remaining “Agents” label; it is “Rooms”

### Cursor prompt — Phase 6
```
Workspace: hearth-os.

You are finishing a commissioned household PWA, not a marketing site.

Governing idea: a sealed larder. Timber-dark #161310, brass #e0a35a, serif ≥18px, 48px taps.

Edit templates and app/static/app.css:
- Visible :focus styles
- prefers-reduced-motion: reduce { animation: none; transition: none }
- Room pills announce House vs Private
- Agent bubbles prefix "Agent · Name"
- Member bubbles show alias only
- No purple, no glassmorphism, no gradient orbs, no "unlock" copy
- Shop list grouped by store, totals per store
- Login: alias only

Do not add a landing page, blog, or pricing section.
Do not add client-side frameworks.
```

**Proof:** lighthouse-ish manual: keyboard through login → rooms → shop.  
**Recovery:** CSS-only changes if templates regress.

---

## PHASE 7 — Quiet needs + bland protocol
**Goal:** Private illness restocks food without a story.

### Subtasks
- [ ] Keyword map stays in `app/services/quiet.py`
- [ ] Merging quiet into list does not duplicate bananas if already in cart; may bump qty
- [ ] `public_ack` contains no symptom words
- [ ] Rebuild week preserves quiet needs for that `week_start`

### Cursor prompt — Phase 7
```
Workspace: hearth-os.

Improve quiet needs without leaking diagnosis:

1. infer_quiet_adds remains keyword-based (stomach/flu/vomit/diarrhea/nausea, headache/migraine, constipat).
2. When bananas already in the week cart, increase qty by the quiet amount instead of skipping.
3. persist_week copies QuietNeed rows after the main cart.
4. Tests: public_ack never contains flu, vomit, headache, cancer.
5. ShoppingItem.name must equal the food name only.

No medications. No "electrolyte drinks" with sugar brands. Broth, rice, bananas, ginger, apples, cabbage only.
```

**Proof:** test_privacy + a new merge test.  

---

## PHASE 8 — Recipes and week notes
**Goal:** House recipes are food. Private recipes stay private.

### Subtasks
- [ ] Recipe upload to house room only if the form is on the house path
- [ ] Private paste does not create a household Recipe row
- [ ] Recipe body is not scanned for organs/Kerrygold; Kitchen refuses those ingredients in the reply

### Cursor prompt — Phase 8
```
Workspace: hearth-os.

Split recipe ingestion:
- /recipes posts to house via handle_house
- A private recipe stays a VaultMessage, not a Recipe row
- If recipe text contains kerrygold, liver, organ, keto, reject with Kitchen: "House law forbids that ingredient."

Add a small test for is_banned().

Do not store the uploader's legal name on Recipe.
```

---

## PHASE 9 — Test wall and fixtures
**Goal:** You can vibe without breaking food law.

### Cursor prompt — Phase 9
```
Workspace: hearth-os.

Add tests/conftest.py with an isolated tmp sqlite via monkeypatched DATABASE_URL.

Cover:
- week_start is Monday
- store split
- privacy isolation
- quiet merge
- prod secret refusal if you can set ENV in-process

Target ≥15 tests, all green.
Do not hit the live xAI or Tops network in tests. Mock httpx.
```

**Proof:** `pytest -q` green offline.

---

## PHASE 10 — Package for the house box
**Goal:** One machine on Tailscale. Three phones.

### Subtasks
- [ ] `docker compose up` with volume `./data`
- [ ] README: change PIN, key, Tailscale serve or bind 0.0.0.0 on tailnet only
- [ ] Backup command: copy `hearth.db`
- [ ] Sunday cron optional: curl POST `/internal/scout` with a shared cron token

### Cursor prompt — Phase 10
```
Workspace: hearth-os.

Production packaging:
1. Dockerfile already exists — make sure USER is non-root and data dir is writable.
2. docker-compose.yml: bind 127.0.0.1:8080:8080 by default (comment for tailnet).
3. Add POST /internal/scout protected by CRON_TOKEN env. It fetch_tops + seed_week.
4. Document restore from hearth.db.
5. Do not add cloud vendors. Do not add public ingress.
```

**Proof:** compose healthcheck passes on your box.  
**Recovery:** run uvicorn without Docker.

---

## PHASE 11 — Adversarial review
**Goal:** Night Watch + Accountant pass.

### Cursor prompt — Phase 11
```
Workspace: hearth-os.

Read the whole app. Write REVIEW.md with only real issues:
- secrets
- CSRF (forms are same-origin cookie; note the residual)
- XSS in chat rendering (Jinja autoescape — confirm)
- private room ACL
- medical-claim scan of templates and prompts
- dead code

Then fix only High issues. No refactors for taste.
```

---

## VIBE SESSION ORDER (do this)

| Day | Phase | Time box |
|---|---|---|
| 1 | 0–2 | 90 min |
| 1 | 3–4 | 60 min |
| 2 | 5–6 | 90 min |
| 2 | 7–9 | 60 min |
| 3 | 10–11 | 60 min |

If a phase overruns, stop. Green tests beat a prettier button.

---

## GROK 4.6 / CURSOR SYSTEM PREAMBLE
Paste this once as a Cursor user rule for this repo:

```
You are building Hearth OS, a household kitchen control system for three adults in Erie County, NY.

Food law is code: no keto, no organ meats, no Kerrygold, jasmine rice + potatoes, cancer-track flag means calories/protein first and fully cooked eggs/meat. Never diagnose. Never claim food treats disease.

Privacy: house room is aliases + named agents. Private room is one person + agents, encrypted at rest. Shopping extras from private notes must not include a name or a diagnosis.

Stack: FastAPI, Jinja, SQLite, existing files. Prefer editing over rewriting. Run pytest. Starlette templates: TemplateResponse(request, name, context).

If unsure, keep the deterministic engine and leave a TODO. Do not invent APIs, prices, or medical protocols.
```

---

## COST

- Rewriting in Next.js: weeks, no extra food on the table.
- Finishing this repo: days.
- Public deploy: high downside (private health + PIN).
- Grok API: optional. The house eats without it.

---

## ORDER

Phase 0 in a fresh Cursor chat, this repo as the folder, Grok 4.6 High Fast, prompt copied verbatim.

## PROOF

`AUDIT.md` exists and `pytest -q` is green.

## RECOVERY

If Cursor wrecks a file, `git checkout --` that path and rerun the same phase prompt with “do not rewrite unrelated files.”
