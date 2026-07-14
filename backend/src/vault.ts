/**
 * Tier-1 zero-knowledge vault sync.
 * Server stores ciphertext + IV + hash-of-ciphertext only.
 * Conflict-safe: client sends expected_base_version; 409 on mismatch.
 * Keeps last 30 versions per user.
 */

import { requireUser } from "./auth";
import {
  Env,
  b64url,
  err,
  fromB64url,
  json,
  nowSec,
  readJson,
  sha256Hex,
} from "./util";

const HISTORY_KEEP = 30;

async function pruneHistory(env: Env, userId: string): Promise<void> {
  const rows = await env.DB.prepare(
    `SELECT version FROM vault_versions WHERE user_id = ? ORDER BY version DESC`
  )
    .bind(userId)
    .all<{ version: number }>();
  const versions = (rows.results || []).map((r) => r.version);
  if (versions.length <= HISTORY_KEEP) return;
  const drop = versions.slice(HISTORY_KEEP);
  await env.DB.prepare(
    `DELETE FROM vault_versions WHERE user_id = ? AND version IN (${drop.map(() => "?").join(",")})`
  )
    .bind(userId, ...drop)
    .run();
}

export async function handleVault(req: Request, env: Env, path: string): Promise<Response> {
  const method = req.method.toUpperCase();
  const auth = await requireUser(env, req);
  if (auth instanceof Response) return auth;

  // GET /vault/latest
  if (method === "GET" && path === "/vault/latest") {
    const row = await env.DB.prepare(
      `SELECT version, ciphertext, iv, ct_hash, created_at
       FROM vault_versions WHERE user_id = ? ORDER BY version DESC LIMIT 1`
    )
      .bind(auth.userId)
      .first<{
        version: number;
        ciphertext: ArrayBuffer;
        iv: ArrayBuffer;
        ct_hash: string;
        created_at: number;
      }>();
    if (!row) return json({ version: 0, vault: null });
    return json({
      version: row.version,
      ct_hash: row.ct_hash,
      created_at: row.created_at,
      ciphertext: b64url(row.ciphertext),
      iv: b64url(row.iv),
    });
  }

  // GET /vault/history
  if (method === "GET" && path === "/vault/history") {
    const rows = await env.DB.prepare(
      `SELECT version, ct_hash, created_at FROM vault_versions
       WHERE user_id = ? ORDER BY version DESC LIMIT ?`
    )
      .bind(auth.userId, HISTORY_KEEP)
      .all<{ version: number; ct_hash: string; created_at: number }>();
    return json({ versions: rows.results || [] });
  }

  // GET /vault/:version
  const verMatch = /^\/vault\/(\d+)$/.exec(path);
  if (method === "GET" && verMatch) {
    const version = Number(verMatch[1]);
    const row = await env.DB.prepare(
      `SELECT version, ciphertext, iv, ct_hash, created_at
       FROM vault_versions WHERE user_id = ? AND version = ?`
    )
      .bind(auth.userId, version)
      .first<{
        version: number;
        ciphertext: ArrayBuffer;
        iv: ArrayBuffer;
        ct_hash: string;
        created_at: number;
      }>();
    if (!row) return err(404, "not_found");
    return json({
      version: row.version,
      ct_hash: row.ct_hash,
      created_at: row.created_at,
      ciphertext: b64url(row.ciphertext),
      iv: b64url(row.iv),
    });
  }

  // POST /vault — upload new version
  if (method === "POST" && path === "/vault") {
    const body = await readJson<{
      expected_base_version?: number;
      ciphertext?: string;
      iv?: string;
    }>(req);
    if (
      typeof body?.expected_base_version !== "number" ||
      !body.ciphertext ||
      !body.iv
    ) {
      return err(400, "bad_request");
    }

    const latest = await env.DB.prepare(
      `SELECT version FROM vault_versions WHERE user_id = ? ORDER BY version DESC LIMIT 1`
    )
      .bind(auth.userId)
      .first<{ version: number }>();
    const current = latest?.version ?? 0;
    if (current !== body.expected_base_version) {
      return json(
        { error: "conflict", current_version: current },
        409
      );
    }

    const ctBytes = fromB64url(body.ciphertext);
    const ivBytes = fromB64url(body.iv);
    if (ctBytes.length < 16 || ivBytes.length < 12) return err(400, "bad_request");
    // Soft size guard (~2 MiB) — blobs should be padded client-side to buckets
    if (ctBytes.length > 2 * 1024 * 1024) return err(413, "too_large");

    const ctHash = await sha256Hex(ctBytes);
    const next = current + 1;
    try {
      await env.DB.prepare(
        `INSERT INTO vault_versions (user_id, version, ciphertext, iv, ct_hash, created_at)
         VALUES (?, ?, ?, ?, ?, ?)`
      )
        .bind(auth.userId, next, ctBytes, ivBytes, ctHash, nowSec())
        .run();
    } catch {
      // concurrent writer
      const again = await env.DB.prepare(
        `SELECT version FROM vault_versions WHERE user_id = ? ORDER BY version DESC LIMIT 1`
      )
        .bind(auth.userId)
        .first<{ version: number }>();
      return json({ error: "conflict", current_version: again?.version ?? current }, 409);
    }

    await pruneHistory(env, auth.userId);
    return json({ ok: true, version: next, ct_hash: ctHash });
  }

  return err(404, "not_found");
}
