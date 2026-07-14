/**
 * Tier-2 envelope helpers (KEK → DEK).
 * KEK lives only as a Worker secret (runtime memory). Never written to D1.
 */

import { b64url, fromB64url, toArrayBuffer } from "./util";

function decodeKeyMaterial(kekB64: string): Uint8Array {
  // Accept both standard base64 (openssl rand -base64) and base64url
  try {
    const std = Uint8Array.from(atob(kekB64), (c) => c.charCodeAt(0));
    if (std.length === 32) return std;
  } catch {
    /* fall through */
  }
  const url = fromB64url(kekB64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, ""));
  if (url.length !== 32) {
    throw new Error("KEK_B64 must decode to 32 bytes");
  }
  return url;
}

async function importKek(kekB64: string): Promise<CryptoKey> {
  return crypto.subtle.importKey(
    "raw",
    toArrayBuffer(decodeKeyMaterial(kekB64)),
    "AES-GCM",
    false,
    ["encrypt", "decrypt"]
  );
}

export async function seal(
  kekB64: string,
  plaintext: Uint8Array | string
): Promise<{ ct: string; iv: string }> {
  const key = await importKek(kekB64);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const data =
    typeof plaintext === "string"
      ? new TextEncoder().encode(plaintext)
      : plaintext;
  const ct = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    key,
    toArrayBuffer(data)
  );
  return { ct: b64url(ct), iv: b64url(iv) };
}

export async function unseal(
  kekB64: string,
  ctB64: string,
  ivB64: string
): Promise<Uint8Array> {
  const key = await importKek(kekB64);
  const pt = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv: toArrayBuffer(fromB64url(ivB64)) },
    key,
    toArrayBuffer(fromB64url(ctB64))
  );
  return new Uint8Array(pt);
}

/** HMAC-sign session claims with SESSION_SECRET. */
export async function signJwt(
  secret: string,
  claims: Record<string, unknown>,
  ttlSec: number
): Promise<string> {
  const header = b64url(
    new TextEncoder().encode(JSON.stringify({ alg: "HS256", typ: "JWT" }))
  );
  const body = {
    ...claims,
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + ttlSec,
  };
  const payload = b64url(new TextEncoder().encode(JSON.stringify(body)));
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const sig = await crypto.subtle.sign(
    "HMAC",
    key,
    new TextEncoder().encode(`${header}.${payload}`)
  );
  return `${header}.${payload}.${b64url(sig)}`;
}

export async function verifyJwt(
  secret: string,
  token: string
): Promise<Record<string, unknown> | null> {
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  const [header, payload, sig] = parts as [string, string, string];
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["verify"]
  );
  const ok = await crypto.subtle.verify(
    "HMAC",
    key,
    toArrayBuffer(fromB64url(sig)),
    new TextEncoder().encode(`${header}.${payload}`)
  );
  if (!ok) return null;
  try {
    const claims = JSON.parse(
      new TextDecoder().decode(fromB64url(payload))
    ) as Record<string, unknown>;
    if (typeof claims.exp === "number" && claims.exp < Math.floor(Date.now() / 1000)) {
      return null;
    }
    return claims;
  } catch {
    return null;
  }
}
