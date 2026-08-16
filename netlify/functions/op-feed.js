/* Orbital Prime feed proxy.
   Allowlisted public connectors only. No secrets. No open proxy.
   In-memory TTL cache on warm isolates. */

const TTL_MS = {
  iss: 3_000,
  tle: 10 * 60_000,
  stations: 10 * 60_000,
  starship: 10 * 60_000,
  kp: 60_000
};

const cache = new Map();

function json(status, body, extra = {}) {
  return {
    statusCode: status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": extra.cache || "public, max-age=15",
      "Access-Control-Allow-Origin": "*",
      "X-OP-Upstream": extra.upstream || "",
      "X-OP-Cache": extra.hit ? "HIT" : "MISS"
    },
    body: JSON.stringify(body)
  };
}

function text(status, body, extra = {}) {
  return {
    statusCode: status,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": extra.cache || "public, max-age=60",
      "Access-Control-Allow-Origin": "*",
      "X-OP-Upstream": extra.upstream || "",
      "X-OP-Cache": extra.hit ? "HIT" : "MISS"
    },
    body
  };
}

function resolve(src, q) {
  if (src === "iss") {
    return { url: "https://api.wheretheiss.at/v1/satellites/25544", kind: "json", ttl: TTL_MS.iss };
  }
  if (src === "kp") {
    return { url: "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json", kind: "json", ttl: TTL_MS.kp };
  }
  if (src === "stations") {
    return { url: "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle", kind: "text", ttl: TTL_MS.stations };
  }
  if (src === "starship") {
    return { url: "https://celestrak.org/NORAD/elements/gp.php?NAME=STARSHIP&FORMAT=json", kind: "json", ttl: TTL_MS.starship };
  }
  if (src === "tle") {
    const catnr = String(q.catnr || "25544");
    if (!/^\d{1,8}$/.test(catnr)) return { error: "bad catnr" };
    return {
      url: `https://celestrak.org/NORAD/elements/gp.php?CATNR=${catnr}&FORMAT=tle`,
      kind: "text",
      ttl: TTL_MS.tle,
      fallback: `https://celestrak.com/NORAD/elements/gp.php?CATNR=${catnr}&FORMAT=tle`
    };
  }
  return { error: "unknown src" };
}

async function pull(url, timeout = 8000) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeout);
  try {
    const res = await fetch(url, {
      signal: ctrl.signal,
      headers: { Accept: "*/*", "User-Agent": "orbital-prime/op-01 (field instrument; public ephemeris)" }
    });
    const body = await res.text();
    return { ok: res.ok, status: res.status, body };
  } finally {
    clearTimeout(t);
  }
}

exports.handler = async (event) => {
  if (event.httpMethod === "OPTIONS") {
    return { statusCode: 204, headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET,OPTIONS" } };
  }
  if (event.httpMethod !== "GET") return json(405, { error: "GET only" });

  const q = event.queryStringParameters || {};
  const src = q.src;
  const spec = resolve(src, q);
  if (spec.error) return json(400, { error: spec.error });

  const key = spec.url;
  const hit = cache.get(key);
  if (hit && Date.now() - hit.at < spec.ttl) {
    return spec.kind === "json"
      ? json(200, JSON.parse(hit.body), { upstream: spec.url, hit: true, cache: "public, max-age=15" })
      : text(200, hit.body, { upstream: spec.url, hit: true, cache: "public, max-age=60" });
  }

  let got = await pull(spec.url);
  if (!got.ok && spec.fallback) got = await pull(spec.fallback);

  if (!got.ok) {
    return json(got.status || 502, {
      error: "upstream",
      src,
      status: got.status,
      note: "Public connector failed. Client may retry direct."
    }, { upstream: spec.url, cache: "no-store" });
  }

  cache.set(key, { at: Date.now(), body: got.body });

  if (spec.kind === "json") {
    try {
      return json(200, JSON.parse(got.body), { upstream: spec.url, cache: "public, max-age=15" });
    } catch {
      return json(502, { error: "upstream json", src }, { cache: "no-store" });
    }
  }
  return text(200, got.body, { upstream: spec.url, cache: "public, max-age=60" });
};
