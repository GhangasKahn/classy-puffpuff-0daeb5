/** Shared Worker bindings & request helpers. */

export interface Env {
  DB: D1Database;
  SESS: KVNamespace;
  SESSION_SECRET: string;
  KEK_B64: string;
  RP_ID: string;
  RP_NAME: string;
  APP_ORIGINS: string;
}

export type Json = Record<string, unknown>;

export { dayUTC, nowSec, parseOriginList as parseOriginsList, pickCorsOrigin } from "./logic";
import { dayUTC, nowSec, parseOriginList, pickCorsOrigin } from "./logic";

/** Copy into a real ArrayBuffer so WebCrypto BufferSource typings are happy. */
export function toArrayBuffer(u8: Uint8Array): ArrayBuffer {
  const out = new ArrayBuffer(u8.byteLength);
  new Uint8Array(out).set(u8);
  return out;
}

export function b64url(buf: ArrayBuffer | Uint8Array): string {
  const u8 = buf instanceof Uint8Array ? buf : new Uint8Array(buf);
  let s = "";
  for (let i = 0; i < u8.length; i++) s += String.fromCharCode(u8[i]!);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function fromB64url(s: string): Uint8Array {
  const pad = "=".repeat((4 - (s.length % 4)) % 4);
  const b64 = (s + pad).replace(/-/g, "+").replace(/_/g, "/");
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

export function randomId(bytes = 16): string {
  const buf = new Uint8Array(bytes);
  crypto.getRandomValues(buf);
  return b64url(buf);
}

export async function sha256Hex(data: string | Uint8Array): Promise<string> {
  const bytes =
    typeof data === "string" ? new TextEncoder().encode(data) : data;
  const digest = await crypto.subtle.digest("SHA-256", toArrayBuffer(bytes));
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

/** Ephemeral rate-limit key: salted IP hash with short TTL — never persisted as raw IP. */
export async function rateKey(ip: string, secret: string, bucket: string): Promise<string> {
  return "rl:" + (await sha256Hex(`${secret}:${bucket}:${ip}`)).slice(0, 32);
}

export function json(data: unknown, status = 200, extra: HeadersInit = {}): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      ...extra,
    },
  });
}

export function err(status: number, code: string): Response {
  // Generic codes only — no stack, no details (logging policy: zero)
  return json({ error: code }, status);
}

export function parseOrigins(env: Env): string[] {
  return parseOriginList(env.APP_ORIGINS);
}

export function corsHeaders(origin: string | null, env: Env): HeadersInit {
  const allowed = parseOrigins(env);
  const ok = pickCorsOrigin(origin, allowed);
  return {
    "access-control-allow-origin": ok,
    "access-control-allow-headers": "content-type, authorization",
    "access-control-allow-methods": "GET,POST,DELETE,OPTIONS",
    "access-control-max-age": "600",
    vary: "Origin",
    "x-content-type-options": "nosniff",
    "referrer-policy": "no-referrer",
    "permissions-policy": "interest-cohort=()",
    "cache-control": "no-store",
  };
}

export async function readJson<T = Json>(req: Request): Promise<T | null> {
  try {
    return (await req.json()) as T;
  } catch {
    return null;
  }
}
