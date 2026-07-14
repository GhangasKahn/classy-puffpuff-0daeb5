/**
 * Pure helpers shared by Worker handlers and unit tests.
 * No Env / Request dependencies.
 */

export function dayUTC(d = new Date()): string {
  return d.toISOString().slice(0, 10);
}

export function nowSec(ms = Date.now()): number {
  return Math.floor(ms / 1000);
}

export function resolveVaultConflict(
  currentVersion: number,
  expectedBase: number
): { ok: true; next: number } | { ok: false; current: number } {
  if (currentVersion !== expectedBase) {
    return { ok: false, current: currentVersion };
  }
  return { ok: true, next: currentVersion + 1 };
}

export function versionsToPrune(
  versionsDesc: number[],
  keep = 30
): number[] {
  if (versionsDesc.length <= keep) return [];
  return versionsDesc.slice(keep);
}

export const PAD_BUCKETS = [
  16 * 1024,
  64 * 1024,
  256 * 1024,
  1024 * 1024,
  2 * 1024 * 1024,
] as const;

/** Server-side size check: ciphertext must land on a known pad bucket (±header). */
export function isBucketSized(byteLength: number): boolean {
  return (PAD_BUCKETS as readonly number[]).includes(byteLength);
}

export function parseOriginList(raw: string): string[] {
  return raw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

export function pickCorsOrigin(
  requestOrigin: string | null,
  allowed: string[]
): string {
  if (requestOrigin && allowed.includes(requestOrigin)) return requestOrigin;
  return allowed[0] ?? "";
}
