# BEDROCK — Site Deployment & Activation
### From the monorepo to a live, installed, configured terminal on your phone

Six phases for the **front-end**. Do Phases 1–2 on a computer (or use the Git route from a phone), then Phases 3–6 on the phone. Budget about 10 minutes to go live, and another 20–30 to enter real numbers properly.

**The one rule, before anything else:** this app stores your data on your device, not on a server. That is the whole point — nobody can see it — but it also means *you* are the backup. Phase 5 (export an encrypted backup) is not optional. Do it the day you start, and do it weekly. If you skip it and clear your browser or lose the phone, the data is gone with no recovery.

For the optional Cloudflare Worker (passkey sync), see `BEDROCK-Deploy-and-Activate.md` (backend) and `PRODUCTION-CHECKLIST.md`.

---

## PHASE 1 — Get the site build

From this monorepo, the deployable web root is **`site/`**:

```
site/
  index.html          # landing
  app/                # PWA
    index.html
    manifest.json
    service-worker.js
    bedrock-api.js
  netlify.toml
  README.md
```

Don't rearrange anything inside `site/` — the app expects those paths.

---

## PHASE 2 — Deploy to Netlify

Pick **one** of the two routes. Route A is fastest. Route B lets future edits auto-publish.

### Route A — Drag and drop (fastest, ~2 minutes, needs a computer)
1. Go to **https://app.netlify.com/signup** and create a free account (email or GitHub login). Signing in first means your site is permanent and renameable — anonymous drops expire.
2. Once logged in, go to **https://app.netlify.com/drop**.
3. Drag the whole **`site` folder** (the folder itself, not the files inside it) onto the drop zone.
4. Netlify uploads it and gives you a live URL like `https://random-words-1234.netlify.app`. HTTPS is automatic — you need that for the app to install.
5. Rename it so it's memorable: **Site configuration → Site details → Change site name** → e.g. `bedrock-capital` → your URL becomes `https://bedrock-capital.netlify.app`.
6. (Optional) Attach a custom domain under **Domain management** if you own one.

> To push an update later with this route: open your site in Netlify → **Deploys** tab → drag the updated `site` folder onto that page. It replaces the live version.

### Route B — Git (best for ongoing updates, works from a phone too)
1. Connect this GitHub repo in Netlify: **Add new site → Import an existing project → GitHub**.
2. Leave **Build command empty**. Set **Publish directory** to `site` (monorepo root deploy) — or `.` if you only push the contents of `site/`.
3. Deploy. From now on, every push auto-deploys.

When this phase is done you have a permanent, HTTPS, public URL. Open it once in a browser to confirm the landing page loads and the **Enter** button jumps you into the app.

---

## PHASE 3 — Install it on your phone (Android)

1. On the phone, open your Netlify URL in **Chrome**. Tap **Enter** (or go straight to `https://your-site.netlify.app/app/`).
2. Let it load fully once **while on Wi-Fi or data** — this first load downloads and caches the engine so it works offline afterward.
3. Tap Chrome's **⋮ menu → "Add to Home screen"** (it may say **"Install app"**). Confirm.
4. A **BEDROCK** icon appears on your home screen. Tap it — it opens full-screen, no browser bars, like a native app.
5. Confirm it's installed properly: close it, turn on airplane mode, reopen it. It should still load (offline-capable). Your live data still needs the internet only for crypto price sync, AI features, and optional ONLINE vault sync.

*(On an iPhone the path is Safari → Share → "Add to Home Screen." Everything else is identical.)*

---

## PHASE 4 — Set up the app with your data

Open the installed app. Work through the tabs in this order — it builds your picture from the ground up. (Tabs: **Home · Ledger · Goals · Quant · Coach · Tribunal · Floor · Config**.)

1. **Config first — make it yours.** Open **Config**. Under **Appearance**, choose Dark or Light (cream). Pick an **Accent** color. This also confirms the app is saving settings.
2. **Ledger — your accounts.** Go to **Ledger** and add your real accounts: cash/checking/savings, investment/brokerage balances, and any liabilities (credit cards, loans) as liability accounts. These drive your net worth on Home.
3. **Ledger → Vault — everything else you own.** Use the **Vault** sub-tab to log non-account assets: watches, cards, metals, vehicles, gear — name, category, quantity, what you paid, and current value. This folds into net worth so the picture is complete, not just bank balances.
4. **Cash flow / income.** Enter your monthly income and recurring expenses where the app asks for them (this powers your true monthly surplus and, for fixed income like SSDI, the deposit timing). Be honest here — the math is only as good as the inputs.
5. **Quant — your holdings.** In **Quant**, add your investment positions (ticker, units, cost). If you have a screenshot of a brokerage page and you've set up an AI key (step 8), you can use **Import from Image** to extract positions automatically. Then **run the simulation** — the Monte-Carlo survival model needs your holdings to tell you anything real.
6. **Floor — your debts and your floor.** In the **Floor** tab, enter each debt (balance, rate, minimum). The kill-order planner ranks them and builds a payoff sequence you can download. Set your emergency floor — the reserve you never breach.
7. **Goals.** In **Goals**, adjust the targets and the **expected return %**. Keep this realistic (see Phase 6) — a fantasy return makes every projection lie to you.
8. **Live prices.** Use **Sync** to pull current crypto prices (this is keyless and needs no setup). Stock tickers won't price automatically — that's expected in the free client-only build.
9. **AI engine (optional but powerful).** Still in **Config → AI Engine**: pick a provider (**OpenRouter** is the easy default), paste your own API key, and the model field auto-fills. This turns on the Coach, the purchase advisor, and image import. Then set the **Spend Governor** — a daily and monthly dollar cap — so a runaway loop can't cost you. The key is stored only on your device. (Also set a hard spending limit inside your provider's own dashboard; the governor is a seatbelt, not a vault.)

---

## PHASE 5 — Lock it down (do this the first day)

This is the survival step. No passphrase recovery — so you create your own backup.

1. **Config → Security.** Set a **backup passphrase**. Choose something strong you will not forget — there is deliberately **no way to recover the backup if you lose the passphrase** (that's what makes it private).
2. Tap **Export Encrypted Backup**. It saves a `.bdv` file — your entire financial picture, encrypted with AES-256 (PBKDF2 600k).
3. **Store that `.bdv` somewhere safe and separate** from the phone: a password manager's file vault, an encrypted drive, or cloud storage you control. Keep the passphrase somewhere equally safe.
4. **Repeat weekly**, and always before you clear browser data, switch phones, or update the app. To move to a new device: install the app there, then **Security → Restore** the `.bdv`.

> A plain (unencrypted) JSON export also exists for migration. It deliberately **excludes your AI key**, but it's still readable — only use it if you understand that, and prefer the encrypted `.bdv` for real backups.

Optional: after a local `.bdv` exists, **Config → ONLINE** can register a passkey and sync the same encrypted vault to your Worker (see backend deploy doc). Lose the passphrase and that remote copy is equally unreadable.

---

## PHASE 6 — Optimize and let it run

You're now live. To make it sharp and keep it honest:

- **Set truthful assumptions.** For long-run projections, the broad equity market has historically returned roughly 7–10% a year. Turning ~$25k into seven figures is about a ~17%/year path sustained over ~20 years — slow, disciplined, real. No one survives the 100%+/year path; the route that could is the same route to zero. Enter returns you'd actually defend, not the ones you wish for, or the Monte-Carlo and goal math will flatter you into bad decisions.
- **Use the Tribunal before you buy.** Before any meaningful purchase, run it through the **Tribunal** / opportunity-cost engine. Seeing what a buy costs your future self in years, not dollars, is the daily discipline this whole tool exists to enforce.
- **Watch the floor, not the ceiling.** Let the **Floor** tab and the survival simulation be your dashboard. The job is to never reach zero and protect the reserve; the upside takes care of itself if the floor holds.
- **Mind the AI budget.** If you enabled AI, glance at the Spend Governor meters occasionally and keep the caps tight.
- **Keep backing up.** Weekly `.bdv` export. This is the one habit that protects everything else.
- **Updating the app:** if you used the Git route, push changes and they go live automatically; if you used drag-and-drop, re-drag the updated `site` folder onto your site's Deploys tab. The service worker is configured to pick up new versions on next open.

---

## Troubleshooting

- **Blank/white screen on first open:** you were offline before it cached. Open it once on Wi-Fi/data, let it fully load, then it works offline.
- **No "Install / Add to Home screen" option:** you must be on the **Netlify HTTPS URL**, not a local file, and on Chrome/Safari. Reload the page and check the menu again. Icons require `icon-192.png` / `icon-512.png` in `site/app/` for a polished install badge.
- **My data disappeared:** you cleared browser storage, or the OS evicted it. Reinstall/reopen and **Security → Restore** your latest `.bdv`. (This is why Phase 5 matters.)
- **AI features error out:** check that your key is pasted correctly in Config → AI Engine, that you have credit at the provider, and that you haven't hit your Spend Governor cap for the day/month.
- **Crypto prices not updating:** Sync needs internet. Stock tickers don't auto-price in this build — that's expected.
- **Theme didn't carry from the landing page:** it carries only within the same site URL (same origin); if you bookmarked the app directly that's fine, just set the theme once in Config.
- **ONLINE / passkey fails:** `RP_ID` and `APP_ORIGINS` on the Worker must match this exact HTTPS origin. See backend deploy doc.

---

## What this is — the honest boundary

You now have a real, installed, private financial terminal: net worth, vault, debt kill-order, opportunity-cost engine, Monte-Carlo survival math, and optional AI — all running on your device. That is the complete **front-end** product.

Optional **backend** Phase 0+1 adds passkey login and encrypted multi-device vault sync. Bank/brokerage linking (Plaid) and automated recon are Phase 3+ — see `BEDROCK-Backend-Architecture.md`. Hosting on Netlify alone does not add them.

And the standing line: **BEDROCK is research and educational tooling you operate yourself. It is not financial advice.** The only person accountable for your money is you — which is exactly why the tool refuses to flatter you, and why you should keep it honest.
