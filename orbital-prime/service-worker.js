/* Orbital Prime SW — offline app shell only.
   Live telemetry (ISS, TLE, weather, radar, Kp) is NEVER cached:
   a field instrument must not serve stale data as if it were live. */

const CACHE = "orbital-prime-v2";

const SHELL = [
  "./",
  "index.html",
  "styles/orbital.css",
  "js/main.js",
  "js/render.js",
  "js/motion.js",
  "js/astro.js",
  "js/singularity.js",
  "favicon.svg",
  "manifest.webmanifest"
];

const LIVE_HOSTS = [
  "api.wheretheiss.at",
  "celestrak.org",
  "celestrak.com",
  "api.open-meteo.com",
  "api.rainviewer.com",
  "tilecache.rainviewer.com",
  "services.swpc.noaa.gov"
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET") return;
  if (LIVE_HOSTS.includes(url.hostname)) return; // live data: network only, no SW interference

  // App shell + static CDN (fonts, satellite.js): cache-first with background refresh
  e.respondWith(
    caches.match(e.request).then((hit) => {
      const fetched = fetch(e.request)
        .then((res) => {
          if (res.ok && (url.origin === location.origin || url.hostname === "cdn.jsdelivr.net" || url.hostname.endsWith("gstatic.com") || url.hostname.endsWith("googleapis.com"))) {
            const clone = res.clone();
            caches.open(CACHE).then((c) => c.put(e.request, clone));
          }
          return res;
        })
        .catch(() => hit);
      return hit || fetched;
    })
  );
});
