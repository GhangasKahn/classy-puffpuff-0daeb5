/**
 * BEDROCK API — Phase 0+1
 * Passkey auth · refresh rotation · Tier-1 vault sync
 * Read PRIVACY.md and ZERO-KNOWLEDGE-DOCTRINE.md before changing behavior.
 */

import { handleAuth } from "./auth";
import { handleVault } from "./vault";
import { Env, corsHeaders, err, json, nowSec } from "./util";

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";
    const origin = req.headers.get("origin");
    const cors = corsHeaders(origin, env);

    if (req.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors });
    }

    // Fail closed if secrets missing (local misconfig)
    if (!env.SESSION_SECRET || !env.KEK_B64) {
      return withCors(err(503, "misconfigured"), cors);
    }

    try {
      let res: Response;

      if (path === "/healthz" || path === "/health") {
        res = json({
          ok: true,
          service: "bedrock-api",
          phase: "0+1",
          ts_day: new Date().toISOString().slice(0, 10),
        });
      } else if (path.startsWith("/auth/")) {
        res = await handleAuth(req, env, path);
      } else if (path.startsWith("/vault")) {
        res = await handleVault(req, env, path);
      } else {
        res = err(404, "not_found");
      }

      return withCors(res, cors);
    } catch {
      // No error bodies with internals; nothing logged (observability.enabled=false)
      return withCors(err(500, "internal"), cors);
    }
  },

  /** Daily purge of expired security-inbox rows — no activity logs retained. */
  async scheduled(
    _controller: ScheduledController,
    env: Env,
    _ctx: ExecutionContext
  ): Promise<void> {
    if (!env.DB) return;
    await env.DB.prepare(`DELETE FROM security_inbox WHERE expires_at < ?`)
      .bind(nowSec())
      .run();
  },
} satisfies ExportedHandler<Env>;

function withCors(res: Response, cors: HeadersInit): Response {
  const headers = new Headers(res.headers);
  for (const [k, v] of Object.entries(cors)) headers.set(k, String(v));
  return new Response(res.body, { status: res.status, headers });
}
