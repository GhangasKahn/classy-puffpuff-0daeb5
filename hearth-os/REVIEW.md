# Hearth OS — adversarial review

Read of the tree after the kitchen engines, rooms, and packaging were in place. Only issues that are real.

## High (fixed)

- **Disease word in Home HTML.** The flags form posted `name="cancer_track"`. The visible label was already “Calories and protein first.” The field is now `energy_first`. Template source no longer contains “cancer” or “flu.”

## Medium (noted, not refactored)

- **CSRF.** Forms use a same-origin session cookie (`hearth_session`, SameSite=Lax). That is acceptable on a Tailscale/LAN box. Residual: a browser that is already logged in and visits a malicious page on another origin cannot POST (Lax), but a same-site attacker on a shared LAN site could. No CSRF token. Do not put this on the public internet.
- **Shared PIN.** Any person who knows `HOUSEHOLD_PIN` can switch aliases on Home and open that alias’s private room on this device. Designed. Residual: a shared kitchen tablet.
- **Fernet is server-mediated.** Agents must decrypt private notes to shop. Other members cannot read them in the UI. This is not end-to-end encryption.
- **No PIN rate limit.** LAN assumption. Brute force is easy if the box is reachable.

## Low

- **Ad scrape lies.** `fetch_tops_ad_text` stores an excerpt even on failure. Prices come from seed + Money upsert. Intended.
- **XSS.** Jinja2Templates autoescape is on for `.html`. Chat and recipes render with `{{ }}` only. No `|safe`. Agent names are assigned in code.
- **Private ACL.** `read_private(household_id, person_id)` is the only private reader. `/chat?room=private` without a person session redirects to house. `target_person_id` query is ignored. Covered by tests.
- **Medical-claim scan.** Templates, CSS, and prompts were grepped for therapeutic / anti-cancer / cures / “unlock your potential.” House system prompt forbids diagnosis and treatment claims. ShoppingItem.name is the catalog food name.
- **Dead code.** Compatibility `/chat` redirects to `/rooms`. Harmless.
- **Cookie `https_only`** only when `ENV=prod`. Set `ENV=prod` on the house box.

## Secrets

- `.gitignore` covers `.env` and `data/`.
- Prod refuses `SECRET_KEY` containing `change-me` and PIN `4829`.
- `HOUSEHOLD_ENC_KEY` optional; else Fernet derives from `SECRET_KEY`.
- `CRON_TOKEN` empty ⇒ `/internal/scout` always 401.
- API keys are not logged.

## Do not “fix” for taste

Food law stays in code. No keto, no organs, no Kerrygold, jasmine rice + potatoes. Quiet extras stay food names. No new APIs, prices, or medical protocols.
