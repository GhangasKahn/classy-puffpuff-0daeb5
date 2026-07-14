# BEDROCK — Privacy Architecture & Covenant
### The Mullvad principle, applied: nobody can be forced to hand over what was never written down.

This backend is built to the standard of Mullvad, Proton, and Sparrow: **minimal existence**.
Not "we promise not to look" — but "there is almost nothing to look at."

## What the server CAN see (the complete list)
- That an opaque account ID exists, and the **day** (not time) it was created.
- A WebAuthn **public** key per passkey (public by nature; proves possession, reveals nothing).
- Opaque device rows: random IDs, **encrypted** labels, day-coarse last-seen.
- Encrypted vault blobs: ciphertext + IV + a hash **of the ciphertext**, with version numbers
  and timestamps (needed so you can roll back). Content: unreadable. Always.
- A **transient** sealed security inbox: theft-relevant signals only (new-device login,
  token-reuse, device removal), encrypted at rest, **deleted when your app collects them**
  (30-day auto-expiry regardless). There is no persistent server-side activity log —
  your lasting audit chain lives inside your encrypted vault, where we cannot read it.
- Once Plaid/Coinbase are linked (Phase 3+): that links exist, their provider type,
  day-coarse refresh times — tokens, institution names, balances all **encrypted at rest**.

## What the server CANNOT see
- Your name, email, phone, or any identity. **There is no email field in the entire schema.**
  Your account is a passkey and a random ID — Mullvad-account style.
- Anything inside your vault: ledger, holdings, notes, goals, debts, settings, AI keys.
  Tier-1 encryption happens **on your device** with a passphrase that never leaves it.
- Your IP address, anywhere at rest. Rate-limiting uses salted hashes with minutes-long
  TTLs; raw IPs are never written to the database or any log.
- Plaintext device names, token labels, institution names, audit details — all sealed.

## Logging policy: zero
- Cloudflare Workers persistent logging is **disabled in config** (`observability.enabled=false`).
- No analytics, no error trackers, no third-party beacons. Errors return generic codes and
  record nothing.
- The only lasting "log" is **your** client-side audit chain, stored inside the encrypted
  vault — tamper-evident (each entry hashes the previous), unreadable by the server.

## The two honest trust boundaries (stated, not hidden)
1. **Cloudflare terminates TLS.** Like Mullvad's datacenter providers, the edge can observe
   that traffic exists and its metadata in flight. We minimize what is *recorded* (nothing),
   not what physically transits. Mitigations available to you: access over VPN/Tor (nothing
   here blocks or fingerprints them), custom domain, and the fact that payloads are
   ciphertext before they ever leave your device.
2. **Plaid is the identified rail — by definition.** Linking a bank means Plaid knows who
   you are and what you hold; that data's ceiling is Plaid's policy, not our cryptography.
   The design *quarantines* it: the anonymous rail (account, vault, notes) and the identified
   rail (Plaid/Coinbase) meet only inside Tier-2 envelopes, we request the minimum products,
   and a future "manual recon only" mode can trade the 6 a.m. cron for tighter custody.

## The covenant you accept in return
**Zero-knowledge means zero recovery.** Your passphrase decrypts the vault; we cannot reset
it, recover it, or be compelled to produce what it protects. Lose the passphrase and the
vault is cryptographically gone — the same deal Sparrow and Wasabi offer, because it is the
only honest one. (Your *login* passkey is recoverable via another enrolled passkey or
recovery codes; your *passphrase* is not. Two different things, deliberately.)

*Research and educational tooling, operated by you, for you. Not financial advice; moves no money.*
