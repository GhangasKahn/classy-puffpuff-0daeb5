/* Aegis Air Field Intel service worker.
   App shell: cache-first. Live APIs: network-first with cache fallback.
   GIBS satellite tiles: cache-first (immutable per date). */

const SHELL_CACHE = "aegis-shell-v3";
const DATA_CACHE = "aegis-data-v3";

const SHELL_ASSETS = [
  "./",
  "./index.html",
  "./styles.css",
  "./core.js",
  "./ml.js",
  "./sat.js",
  "./manifest.json",
  "./icon.svg",
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(SHELL_CACHE)
      .then((c) => c.addAll(SHELL_ASSETS))
      .catch(() => {})
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
const TILE_HOSTS = ["gibs.earthdata.nasa.gov", "tile.openstreetmap.org"];

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);

  if (API_HOSTS.includes(url.hostname)) {
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

  if (TILE_HOSTS.includes(url.hostname)) {
    e.respondWith(
      caches.match(e.request).then((hit) => hit || fetch(e.request).then((res) => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(DATA_CACHE).then((c) => c.put(e.request, copy));
        }
        return res;
      }))
    );
    return;
  }

  e.respondWith(
    caches.match(e.request).then((hit) => hit || fetch(e.request).then((res) => {
      const copy = res.clone();
      caches.open(SHELL_CACHE).then((c) => c.put(e.request, copy));
      return res;
    }))
  );
});
