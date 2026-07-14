/**
 * Passkey (WebAuthn) auth + refresh-token rotation with theft detection.
 * No email/PII — identity is an opaque user id + public key.
 */

import {
  generateRegistrationOptions,
  verifyRegistrationResponse,
  generateAuthenticationOptions,
  verifyAuthenticationResponse,
} from "@simplewebauthn/server";
import type {
  RegistrationResponseJSON,
  AuthenticationResponseJSON,
  AuthenticatorTransportFuture,
} from "@simplewebauthn/types";

import { seal, signJwt, verifyJwt } from "./crypto";
import {
  Env,
  b64url,
  dayUTC,
  err,
  fromB64url,
  json,
  nowSec,
  parseOrigins,
  randomId,
  rateKey,
  readJson,
  sha256Hex,
  toArrayBuffer,
} from "./util";

const CHALLENGE_TTL = 300; // seconds in KV
const ACCESS_TTL = 900; // 15 min
const REFRESH_TTL = 60 * 60 * 24 * 30; // 30 days
const INBOX_TTL = 60 * 60 * 24 * 30;

function rpConfig(env: Env) {
  const origins = parseOrigins(env);
  return {
    rpID: env.RP_ID,
    rpName: env.RP_NAME || "BEDROCK",
    origin: origins[0]!,
    origins,
  };
}

async function rateLimit(
  env: Env,
  req: Request,
  bucket: string,
  limit = 30
): Promise<Response | null> {
  const ip = req.headers.get("cf-connecting-ip") || "0";
  const key = await rateKey(ip, env.SESSION_SECRET, bucket);
  const cur = Number((await env.SESS.get(key)) || "0");
  if (cur >= limit) return err(429, "rate_limited");
  await env.SESS.put(key, String(cur + 1), { expirationTtl: 120 });
  return null;
}

async function pushInbox(
  env: Env,
  userId: string,
  kind: string,
  detail: Record<string, unknown>
): Promise<void> {
  const sealed = await seal(env.KEK_B64, JSON.stringify({ kind, ...detail, t: nowSec() }));
  await env.DB.prepare(
    `INSERT INTO security_inbox (id, user_id, kind, payload_ct, payload_iv, created_at, expires_at)
     VALUES (?, ?, ?, ?, ?, ?, ?)`
  )
    .bind(
      randomId(),
      userId,
      kind,
      fromB64url(sealed.ct),
      fromB64url(sealed.iv),
      nowSec(),
      nowSec() + INBOX_TTL
    )
    .run();
}

async function issueSession(
  env: Env,
  userId: string,
  deviceId: string,
  familyId?: string
): Promise<{ access_token: string; refresh_token: string; device_id: string }> {
  const family = familyId || randomId();
  const refreshRaw = randomId(32);
  const tokenHash = await sha256Hex(refreshRaw);
  const tokenId = randomId();
  await env.DB.prepare(
    `INSERT INTO refresh_tokens (id, user_id, device_id, family_id, token_hash, expires_at, revoked, created_at)
     VALUES (?, ?, ?, ?, ?, ?, 0, ?)`
  )
    .bind(tokenId, userId, deviceId, family, tokenHash, nowSec() + REFRESH_TTL, nowSec())
    .run();

  const access = await signJwt(
    env.SESSION_SECRET,
    { sub: userId, did: deviceId, typ: "access" },
    ACCESS_TTL
  );
  return {
    access_token: access,
    refresh_token: `${tokenId}.${refreshRaw}`,
    device_id: deviceId,
  };
}

export async function requireUser(
  env: Env,
  req: Request
): Promise<{ userId: string; deviceId: string } | Response> {
  const h = req.headers.get("authorization") || "";
  const m = /^Bearer\s+(.+)$/i.exec(h);
  if (!m) return err(401, "unauthorized");
  const claims = await verifyJwt(env.SESSION_SECRET, m[1]!);
  if (!claims || claims.typ !== "access" || typeof claims.sub !== "string") {
    return err(401, "unauthorized");
  }
  return { userId: claims.sub, deviceId: String(claims.did || "") };
}

export async function handleAuth(req: Request, env: Env, path: string): Promise<Response> {
  const method = req.method.toUpperCase();

  // POST /auth/register/options
  if (method === "POST" && path === "/auth/register/options") {
    const rl = await rateLimit(env, req, "reg-opt", 20);
    if (rl) return rl;
    const rp = rpConfig(env);
    const userId = randomId(18);
    const userIdBytes = fromB64url(userId);
    const options = await generateRegistrationOptions({
      rpName: rp.rpName,
      rpID: rp.rpID,
      userID: userIdBytes,
      userName: userId, // no email — opaque id is the only name
      userDisplayName: "BEDROCK",
      attestationType: "none",
      authenticatorSelection: {
        residentKey: "preferred",
        userVerification: "preferred",
        authenticatorAttachment: "platform",
      },
    });
    await env.SESS.put(`chal:reg:${userId}`, options.challenge, {
      expirationTtl: CHALLENGE_TTL,
    });
    await env.SESS.put(`reguser:${options.challenge}`, userId, {
      expirationTtl: CHALLENGE_TTL,
    });
    return json({ ...options, userId });
  }

  // POST /auth/register/verify
  if (method === "POST" && path === "/auth/register/verify") {
    const rl = await rateLimit(env, req, "reg-ver", 20);
    if (rl) return rl;
    const body = await readJson<{
      userId?: string;
      response?: RegistrationResponseJSON;
      deviceLabelCt?: string;
      deviceLabelIv?: string;
    }>(req);
    if (!body?.userId || !body.response) return err(400, "bad_request");
    const challenge = await env.SESS.get(`chal:reg:${body.userId}`);
    if (!challenge) return err(400, "challenge_expired");
    const rp = rpConfig(env);
    let verification;
    try {
      verification = await verifyRegistrationResponse({
        response: body.response,
        expectedChallenge: challenge,
        expectedOrigin: rp.origins,
        expectedRPID: rp.rpID,
      });
    } catch {
      return err(400, "verify_failed");
    }
    if (!verification.verified || !verification.registrationInfo) {
      return err(400, "verify_failed");
    }
    const { credentialID, credentialPublicKey, counter } = verification.registrationInfo;
    const credId = credentialID; // already base64url
    const day = dayUTC();
    const deviceId = randomId();

    await env.DB.batch([
      env.DB.prepare(`INSERT INTO users (id, created_day) VALUES (?, ?)`).bind(body.userId, day),
      env.DB.prepare(
        `INSERT INTO credentials (id, user_id, public_key, counter, transports, created_day)
         VALUES (?, ?, ?, ?, ?, ?)`
      ).bind(
        credId,
        body.userId,
        toArrayBuffer(credentialPublicKey),
        counter,
        JSON.stringify(body.response.response.transports || []),
        day
      ),
      env.DB.prepare(
        `INSERT INTO devices (id, user_id, label_ct, label_iv, last_seen_day, created_day)
         VALUES (?, ?, ?, ?, ?, ?)`
      ).bind(
        deviceId,
        body.userId,
        body.deviceLabelCt ? fromB64url(body.deviceLabelCt) : null,
        body.deviceLabelIv ? fromB64url(body.deviceLabelIv) : null,
        day,
        day
      ),
    ]);

    await env.SESS.delete(`chal:reg:${body.userId}`);
    const session = await issueSession(env, body.userId, deviceId);
    return json({ ok: true, user_id: body.userId, ...session });
  }

  // POST /auth/login/options
  if (method === "POST" && path === "/auth/login/options") {
    const rl = await rateLimit(env, req, "login-opt", 40);
    if (rl) return rl;
    const body = await readJson<{ userId?: string }>(req);
    const rp = rpConfig(env);
    let allowCredentials:
      | { id: string; transports?: AuthenticatorTransportFuture[] }[]
      | undefined;
    if (body?.userId) {
      const rows = await env.DB.prepare(
        `SELECT id, transports FROM credentials WHERE user_id = ?`
      )
        .bind(body.userId)
        .all<{ id: string; transports: string | null }>();
      allowCredentials = (rows.results || []).map((r) => ({
        id: r.id,
        transports: r.transports
          ? (JSON.parse(r.transports) as AuthenticatorTransportFuture[])
          : undefined,
      }));
    }
    const options = await generateAuthenticationOptions({
      rpID: rp.rpID,
      userVerification: "preferred",
      allowCredentials,
    });
    await env.SESS.put(`chal:login:${options.challenge}`, body?.userId || "*", {
      expirationTtl: CHALLENGE_TTL,
    });
    return json(options);
  }

  // POST /auth/login/verify
  if (method === "POST" && path === "/auth/login/verify") {
    const rl = await rateLimit(env, req, "login-ver", 40);
    if (rl) return rl;
    const body = await readJson<{
      response?: AuthenticationResponseJSON;
      deviceLabelCt?: string;
      deviceLabelIv?: string;
    }>(req);
    if (!body?.response) return err(400, "bad_request");
    const credId = body.response.id;
    const challengeExpected = body.response.response.clientDataJSON
      ? undefined
      : undefined;
    void challengeExpected;

    const cred = await env.DB.prepare(
      `SELECT c.id, c.user_id, c.public_key, c.counter, c.transports
       FROM credentials c WHERE c.id = ?`
    )
      .bind(credId)
      .first<{
        id: string;
        user_id: string;
        public_key: ArrayBuffer;
        counter: number;
        transports: string | null;
      }>();
    if (!cred) return err(401, "unknown_credential");

    // Recover challenge from clientData
    let clientChallenge: string;
    try {
      const cd = JSON.parse(
        new TextDecoder().decode(fromB64url(body.response.response.clientDataJSON))
      ) as { challenge: string };
      clientChallenge = cd.challenge;
    } catch {
      return err(400, "bad_request");
    }
    const stored = await env.SESS.get(`chal:login:${clientChallenge}`);
    if (!stored) return err(400, "challenge_expired");

    const rp = rpConfig(env);
    let verification;
    try {
      verification = await verifyAuthenticationResponse({
        response: body.response,
        expectedChallenge: clientChallenge,
        expectedOrigin: rp.origins,
        expectedRPID: rp.rpID,
        authenticator: {
          credentialID: cred.id,
          credentialPublicKey: new Uint8Array(cred.public_key),
          counter: cred.counter,
          transports: cred.transports
            ? (JSON.parse(cred.transports) as AuthenticatorTransportFuture[])
            : undefined,
        },
      });
    } catch {
      return err(401, "verify_failed");
    }
    if (!verification.verified) return err(401, "verify_failed");

    await env.DB.prepare(`UPDATE credentials SET counter = ? WHERE id = ?`)
      .bind(verification.authenticationInfo.newCounter, cred.id)
      .run();
    await env.SESS.delete(`chal:login:${clientChallenge}`);

    const deviceId = randomId();
    const day = dayUTC();
    await env.DB.prepare(
      `INSERT INTO devices (id, user_id, label_ct, label_iv, last_seen_day, created_day)
       VALUES (?, ?, ?, ?, ?, ?)`
    )
      .bind(
        deviceId,
        cred.user_id,
        body.deviceLabelCt ? fromB64url(body.deviceLabelCt) : null,
        body.deviceLabelIv ? fromB64url(body.deviceLabelIv) : null,
        day,
        day
      )
      .run();
    await pushInbox(env, cred.user_id, "new_device", { device_id: deviceId });

    const session = await issueSession(env, cred.user_id, deviceId);
    return json({ ok: true, user_id: cred.user_id, ...session });
  }

  // POST /auth/refresh
  if (method === "POST" && path === "/auth/refresh") {
    const body = await readJson<{ refresh_token?: string }>(req);
    if (!body?.refresh_token) return err(400, "bad_request");
    const [tokenId, raw] = body.refresh_token.split(".");
    if (!tokenId || !raw) return err(401, "invalid_token");
    const hash = await sha256Hex(raw);
    const row = await env.DB.prepare(
      `SELECT id, user_id, device_id, family_id, token_hash, expires_at, revoked
       FROM refresh_tokens WHERE id = ?`
    )
      .bind(tokenId)
      .first<{
        id: string;
        user_id: string;
        device_id: string;
        family_id: string;
        token_hash: string;
        expires_at: number;
        revoked: number;
      }>();
    if (!row || row.token_hash !== hash) return err(401, "invalid_token");

    // Theft detection: presenting an already-rotated or revoked token burns the family
    if (row.revoked || row.expires_at < nowSec()) {
      await env.DB.prepare(
        `UPDATE refresh_tokens SET revoked = 1 WHERE family_id = ?`
      )
        .bind(row.family_id)
        .run();
      await pushInbox(env, row.user_id, "token_reuse", { family_id: row.family_id });
      return err(401, "token_reuse");
    }

    await env.DB.prepare(`UPDATE refresh_tokens SET revoked = 1 WHERE id = ?`)
      .bind(row.id)
      .run();
    await env.DB.prepare(
      `UPDATE devices SET last_seen_day = ? WHERE id = ?`
    )
      .bind(dayUTC(), row.device_id)
      .run();

    const session = await issueSession(env, row.user_id, row.device_id, row.family_id);
    return json({ ok: true, ...session });
  }

  // POST /auth/logout
  if (method === "POST" && path === "/auth/logout") {
    const body = await readJson<{ refresh_token?: string }>(req);
    const auth = await requireUser(env, req);
    if (auth instanceof Response && !body?.refresh_token) return auth;

    if (body?.refresh_token) {
      const [tokenId] = body.refresh_token.split(".");
      if (tokenId) {
        const row = await env.DB.prepare(
          `SELECT family_id FROM refresh_tokens WHERE id = ?`
        )
          .bind(tokenId)
          .first<{ family_id: string }>();
        if (row) {
          await env.DB.prepare(
            `UPDATE refresh_tokens SET revoked = 1 WHERE family_id = ?`
          )
            .bind(row.family_id)
            .run();
        }
      }
    } else if (!(auth instanceof Response)) {
      await env.DB.prepare(
        `UPDATE refresh_tokens SET revoked = 1 WHERE device_id = ?`
      )
        .bind(auth.deviceId)
        .run();
    }
    return json({ ok: true });
  }

  // GET /auth/devices
  if (method === "GET" && path === "/auth/devices") {
    const auth = await requireUser(env, req);
    if (auth instanceof Response) return auth;
    const rows = await env.DB.prepare(
      `SELECT id, label_ct, label_iv, last_seen_day, created_day FROM devices WHERE user_id = ?`
    )
      .bind(auth.userId)
      .all<{
        id: string;
        label_ct: ArrayBuffer | null;
        label_iv: ArrayBuffer | null;
        last_seen_day: string;
        created_day: string;
      }>();
    return json({
      devices: (rows.results || []).map((d) => ({
        id: d.id,
        label_ct: d.label_ct ? b64url(d.label_ct) : null,
        label_iv: d.label_iv ? b64url(d.label_iv) : null,
        last_seen_day: d.last_seen_day,
        created_day: d.created_day,
        current: d.id === auth.deviceId,
      })),
    });
  }

  // DELETE /auth/devices/:id
  const deviceMatch = /^\/auth\/devices\/([^/]+)$/.exec(path);
  if (method === "DELETE" && deviceMatch) {
    const auth = await requireUser(env, req);
    if (auth instanceof Response) return auth;
    const deviceId = deviceMatch[1]!;
    const row = await env.DB.prepare(
      `SELECT id FROM devices WHERE id = ? AND user_id = ?`
    )
      .bind(deviceId, auth.userId)
      .first();
    if (!row) return err(404, "not_found");
    await env.DB.batch([
      env.DB.prepare(`DELETE FROM devices WHERE id = ?`).bind(deviceId),
      env.DB.prepare(
        `UPDATE refresh_tokens SET revoked = 1 WHERE device_id = ?`
      ).bind(deviceId),
    ]);
    await pushInbox(env, auth.userId, "device_removed", { device_id: deviceId });
    return json({ ok: true });
  }

  // GET /auth/inbox — pull + delete sealed security signals
  if (method === "GET" && path === "/auth/inbox") {
    const auth = await requireUser(env, req);
    if (auth instanceof Response) return auth;
    await env.DB.prepare(`DELETE FROM security_inbox WHERE expires_at < ?`)
      .bind(nowSec())
      .run();
    const rows = await env.DB.prepare(
      `SELECT id, kind, payload_ct, payload_iv, created_at FROM security_inbox WHERE user_id = ?`
    )
      .bind(auth.userId)
      .all<{
        id: string;
        kind: string;
        payload_ct: ArrayBuffer;
        payload_iv: ArrayBuffer;
        created_at: number;
      }>();
    const items = rows.results || [];
    if (items.length) {
      const ids = items.map((i) => i.id);
      await env.DB.prepare(
        `DELETE FROM security_inbox WHERE id IN (${ids.map(() => "?").join(",")})`
      )
        .bind(...ids)
        .run();
    }
    return json({
      items: items.map((i) => ({
        id: i.id,
        kind: i.kind,
        payload_ct: b64url(i.payload_ct),
        payload_iv: b64url(i.payload_iv),
        created_at: i.created_at,
      })),
    });
  }

  return err(404, "not_found");
}
