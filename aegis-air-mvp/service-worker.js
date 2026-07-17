/* Aegis Air MVP service worker.
   App shell: cache-first so the UI opens offline.
   Live APIs (Open-Meteo, EONET): network-first with cache fallback,
   so stale data can still be shown when offline. */

const SHELL_CACHE = "aegis-shell-v2";
const DATA_CACHE = "aegis-data-v2";

const SHELL_ASSETS = [
  "./",
  "./index.html",
  "./styles.css",
  "./app.js",
  "./manifest.json",
  "./icon.svg",
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(SHELL_CACHE)
      .then((c) => c.addAll(SHELL_ASSETS))
      .catch(() => { /* partial cache is fine; first online load fills the rest */ })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== SHELL_CACHE && k !== DATA_CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

const API_HOSTS = ["api.open-meteo.com", "air-quality-api.open-meteo.com", "eonet.gsfc.nasa.gov"];

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET") return;

  if (API_HOSTS.includes(url.hostname)) {
    // network-first for live data
    e.respondWith(
      fetch(e.request)
        .then((res) => {
          const copy = res.clone();
          caches.open(DATA_CACHE).then((c) => c.put(e.request, copy));
          return res;
        })
        .catch(() => caches.match(e.request))
    );
    return;
  }

  if (url.hostname === "tile.openstreetmap.org") {
    // cache-first for map tiles (they rarely change)
    e.respondWith(
      caches.match(e.request).then((hit) => hit || fetch(e.request).then((res) => {
        const copy = res.clone();
        caches.open(DATA_CACHE).then((c) => c.put(e.request, copy));
        return res;
      }))
    );
    return;
  }

  // app shell: cache-first
  e.respondWith(
    caches.match(e.request).then((hit) => hit || fetch(e.request).then((res) => {
      const copy = res.clone();
      caches.open(SHELL_CACHE).then((c) => c.put(e.request, copy));
      return res;
    }))
  );
});
