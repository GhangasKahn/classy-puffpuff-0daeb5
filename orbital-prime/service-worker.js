/* Orbital Prime SW — offline app shell only.
   Live telemetry is NEVER cached. */

const CACHE = "orbital-prime-v7";

const SHELL = [
  "./",
  "index.html",
  "styles/orbital.css",
  "js/main.js",
  "js/render.js",
  "js/motion.js",
  "js/astro.js",
  "js/audio.js",
  "js/feeds.js",
  "js/score.js",
  "js/gl/unit.js",
  "vendor/satellite.min.js",
  "fonts/archivo-black-latin-400.woff2",
  "fonts/inter-latin-400.woff2",
  "fonts/inter-latin-600.woff2",
  "fonts/inter-latin-700.woff2",
  "fonts/space-mono-latin-400.woff2",
  "fonts/space-mono-latin-700.woff2",
  "favicon.svg",
  "og.svg",
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
  if (LIVE_HOSTS.includes(url.hostname)) return;
  if (url.pathname.includes("/api/") || url.pathname.includes("/.netlify/functions/")) return;

  e.respondWith(
    caches.match(e.request).then((hit) => {
      const fetched = fetch(e.request)
        .then((res) => {
          if (res.ok && url.origin === location.origin) {
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
