/* Live health of public connectors. No secrets. Times are real RTT. */

const TARGETS = [
  { id: "iss", url: "https://api.wheretheiss.at/v1/satellites/25544" },
  { id: "tle", url: "https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=tle" },
  { id: "wx", url: "https://api.open-meteo.com/v1/forecast?latitude=42.8864&longitude=-78.8784&current=cloud_cover&forecast_days=1" },
  { id: "radar", url: "https://api.rainviewer.com/public/weather-maps.json" },
  { id: "kp", url: "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json" }
];

async function ping(url) {
  const t0 = Date.now();
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 6000);
  try {
    const res = await fetch(url, {
      signal: ctrl.signal,
      headers: { "User-Agent": "orbital-prime/op-01 health" }
    });
    await res.arrayBuffer();
    return { ok: res.ok, status: res.status, ms: Date.now() - t0 };
  } catch (e) {
    return { ok: false, status: 0, ms: Date.now() - t0, error: e.name === "AbortError" ? "timeout" : "network" };
  } finally {
    clearTimeout(t);
  }
}

exports.handler = async () => {
  const rows = await Promise.all(TARGETS.map(async (t) => ({ id: t.id, ...(await ping(t.url)) })));
  const body = {
    ok: rows.every((r) => r.ok),
    ts: new Date().toISOString(),
    feeds: Object.fromEntries(rows.map((r) => [r.id, r]))
  };
  return {
    statusCode: 200,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      "Access-Control-Allow-Origin": "*"
    },
    body: JSON.stringify(body)
  };
};
