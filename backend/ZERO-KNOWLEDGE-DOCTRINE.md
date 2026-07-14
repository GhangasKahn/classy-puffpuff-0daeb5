# BEDROCK — Zero-Knowledge Doctrine
### The privacy constitution. Modeled on Mullvad · Proton · Wasabi · Sparrow · Trezor. Every backend decision answers to this file.

This is not "encryption as a feature." This is a privacy posture where **the operator (you, me, a future host) is structurally unable to surveil the user, and a seized server yields as close to nothing as physics allows.** Where a tradeoff is unavoidable, it is named here in plain language rather than hidden. The cardinal sin is pretending something is zero-knowledge when it isn't.

---

## The seven laws

**1. No accounts, no identity, no email.** Like Mullvad's account-number model: identity is a cryptographic keypair (your passkey) and an opaque random user ID. We never ask for, store, or accept an email, name, or phone number. There is no "profile." There is nothing to leak because nothing identifying is collected. *(Plaid is the one bounded exception — see "The Plaid Tension" below.)*

**2. Zero logging.** No request logs, no access logs, no IP logs, no analytics, no error-tracker that ships request bodies, no timestamps of "last seen" beyond what the user themselves needs. Like Mullvad and Proton's no-logs stance: what we do not record cannot be subpoenaed, stolen, or sold. The hash-chained audit log from the original spec is **removed from the server** — auditing happens *client-side over the user's own vault*, never as a server-side record of their activity.

**3. Client-side encryption, always. The server holds ciphertext it cannot read.** Like Wasabi (your keys never leave your machine) and Proton (zero-access encryption): the vault — ledger, accounts, notes, goals, everything you type — is encrypted on your device with a key derived from your passphrase. The key never touches the wire. The server is a dumb encrypted-blob store. This is non-negotiable and covers **notes and every field**, not just balances.

**4. Login ≠ decryption, and we cannot reset the latter.** Like Trezor/Sparrow seed custody: your passkey authenticates the transport; your passphrase decrypts the data. We can revoke a session. **Nobody — not us, not a court, not an attacker with the whole database — can recover your passphrase or read your vault without it.** Lose it and the data is cryptographically gone. That is the cost of real zero-knowledge, stated up front, the way Sparrow tells you a lost seed is a lost wallet.

**5. Minimize, then encrypt what remains.** Like FlokiNET/Mullvad data-minimization: collect the absolute minimum, then encrypt even that. Tier-2 secrets (Plaid/Coinbase tokens) that the server *must* use are envelope-encrypted; the wrapping key lives only in runtime memory, never in the database. A database dump alone is inert.

**6. Open and inspectable.** Like every project on this list: the crypto is standard (WebCrypto AES-256-GCM, PBKDF2/Argon2id), no proprietary black box, and the client can verify the server is only storing ciphertext. Trust is verified, not requested.

**7. Graceful, honest degradation.** The app works fully offline and client-only (the Wasabi/Sparrow ethos: your tool doesn't depend on someone else's server being honest or alive). Every server feature can be switched off and the instrument still runs on your device.

---

## The Plaid Tension — stated, not hidden

You want Mullvad-grade privacy **and** Plaid account-syncing with identity verification. These pull in opposite directions, and honesty here is the whole point of this document.

**What Plaid inherently breaks:** Plaid is a US-regulated financial-data aggregator. Using it means *Plaid* — and your bank — know who you are, that you connected, and what accounts you linked. That identity exposure happens at Plaid's layer and **cannot** be encrypted away by us; it's the nature of regulated bank connectivity. Wasabi/Sparrow avoid exactly this by never touching the banking system. So: **the moment you link a bank via Plaid, that specific connection is not zero-knowledge to Plaid.** No design of mine changes that. Pretending otherwise would be the lie this doctrine exists to prevent.

**What we can still guarantee around it — the containment:**
- **BEDROCK itself still never learns your identity.** Plaid's Link UI collects bank credentials directly (they never hit our server); what we receive is an opaque `access_token`. We store it envelope-encrypted. We hold no name, no email, no SSN — Plaid's identity product, if ever enabled, stays at Plaid.
- **The token is the only hostage, and it's revocable.** It can't move money (we request read scopes only), and you can sever it from either side instantly.
- **Fetched balances are Tier-2:** envelope-encrypted at rest, the wrapping key only in runtime memory, decrypted only in the instant a refresh runs, never logged.
- **You can run Plaid-free.** Manual entry + the keyless price feed is the *fully* zero-knowledge mode. Plaid is strictly opt-in, per-account, and quarantined. The app makes the privacy cost of linking explicit at the moment you link.

**The two custody modes, your choice (Sparrow's "your node vs. a public server" pattern):**
- **Sovereign (max privacy):** no Plaid, no unattended cron. Manual entry and on-demand price pulls only. The server is purely an encrypted-vault sync target. Nothing about your finances is ever server-readable.
- **Recon (max automation):** Plaid/Coinbase linked, server refreshes on a schedule. You accept the Tier-2 exposure (server-readable-while-running balances + Plaid knowing your identity) in exchange for automated, time-series net worth. Toggleable; revocable; the boundary is always shown.

This is the same bargain Mullvad makes explicit and the same one Sparrow makes with a third-party Electrum server: we tell you exactly where the trust boundary is, default you to the private side, and let *you* move it consciously.

---

## What changes in the build because of this doctrine

1. **Audit log: removed from the server.** No server-side record of logins, syncs, or activity. Integrity verification becomes a *client-side* check the user runs over their own vault history. (This reverses the original spec — correctly.)
2. **No `last_seen` surveillance.** Device rows keep only what the user needs to manage devices; we don't build a behavioral timeline.
3. **Notes and all free-text are Tier-1, client-encrypted.** Explicitly: nothing you type is ever server-readable.
4. **KDF hardened toward the Wasabi/Sparrow bar:** Argon2id (memory-hard, WASM in the browser) preferred for the vault key, with PBKDF2-SHA256 @ 600k as the no-WASM fallback. Memory-hard derivation resists the GPU cracking a leaked blob would invite.
5. **Encrypted client-side metadata padding:** vault blobs are padded to bucketed sizes before upload so the server can't infer how much you own from ciphertext length. (Proton/Wasabi-style metadata defense.)
6. **No IP retention:** rate-limiting uses ephemeral, salted, rotating counters that expire in minutes — enough to stop abuse, too short and too hashed to be a log.
7. **Sovereign mode is the default.** Recon is something you deliberately switch on.

> The standing rule: **default to the private side of every boundary, name every boundary in plain words, and never record what we don't absolutely need.** This is research/educational tooling you operate for yourself; it moves no money by design; and it is built so that the people running it can't betray you even if they wanted to.
