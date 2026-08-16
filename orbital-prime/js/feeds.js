/* Public connector client.
   Prefers same-origin Netlify proxy when deployed. Falls back to the
   public origin. Never invents a payload. Retries with backoff. */

const DIRECT = {
  iss: () => "https://api.wheretheiss.at/v1/satellites/25544",
  tle: ({ catnr = "25544" } = {}) => `https://celestrak.org/NORAD/elements/gp.php?CATNR=${catnr}&FORMAT=tle`,
  tleMirror: ({ catnr = "25544" } = {}) => `https://celestrak.com/NORAD/elements/gp.php?CATNR=${catnr}&FORMAT=tle`,
  stations: () => "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle",
  starship: () => "https://celestrak.org/NORAD/elements/gp.php?NAME=STARSHIP&FORMAT=json",
  kp: () => "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json",
  wx: ({ lat, lon }) =>
    `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=cloud_cover,precipitation,visibility&hourly=cloud_cover,precipitation,visibility&forecast_days=2&timezone=auto`,
  radar: () => "https://api.rainviewer.com/public/weather-maps.json"
};

function useProxy() {
  const { hostname, pathname } = location;
  return pathname.startsWith("/orbital-prime") || hostname.includes("netlify.app");
}

function proxyUrl(src, params = {}) {
  const q = new URLSearchParams({ src, ...params });
  return `/orbital-prime/api/feed?${q}`;
}

async function once(url, timeout) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeout);
  try {
    const res = await fetch(url, { signal: ctrl.signal, cache: "no-store" });
    return res;
  } finally {
    clearTimeout(t);
  }
}

async function pull(urls, { timeout = 10000, as = "text" } = {}) {
  let last = null;
  for (const url of urls) {
    try {
      const res = await once(url, timeout);
      if (res.status === 404 && as === "json") return { ok: true, status: 404, data: null, url };
      if (!res.ok) {
        last = new Error(`HTTP ${res.status} ${url}`);
        continue;
      }
      const data = as === "json" ? await res.json() : await res.text();
      return { ok: true, status: res.status, data, url };
    } catch (e) {
      last = e;
    }
  }
  throw last || new Error("feed empty");
}

export async function getIss() {
  const urls = useProxy()
    ? [proxyUrl("iss"), DIRECT.iss()]
    : [DIRECT.iss()];
  return pull(urls, { as: "json", timeout: 8000 });
}

export async function getTle(catnr = "25544") {
  const urls = useProxy()
    ? [proxyUrl("tle", { catnr }), DIRECT.tle({ catnr }), DIRECT.tleMirror({ catnr })]
    : [DIRECT.tle({ catnr }), DIRECT.tleMirror({ catnr })];
  return pull(urls, { as: "text", timeout: 8000 });
}

export async function getStations() {
  const urls = useProxy()
    ? [proxyUrl("stations"), DIRECT.stations()]
    : [DIRECT.stations()];
  return pull(urls, { as: "text", timeout: 10000 });
}

export async function getStarship() {
  const urls = useProxy()
    ? [proxyUrl("starship"), DIRECT.starship()]
    : [DIRECT.starship()];
  return pull(urls, { as: "json", timeout: 8000 });
}

export async function getKp() {
  const urls = useProxy()
    ? [proxyUrl("kp"), DIRECT.kp()]
    : [DIRECT.kp()];
  return pull(urls, { as: "json", timeout: 8000 });
}

export async function getWeather(lat, lon) {
  return pull([DIRECT.wx({ lat, lon })], { as: "json", timeout: 10000 });
}

export async function getRadarIndex() {
  return pull([DIRECT.radar()], { as: "json", timeout: 8000 });
}

export async function getHealth() {
  if (!useProxy()) return null;
  try {
    const res = await once("/orbital-prime/api/health", 8000);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}
