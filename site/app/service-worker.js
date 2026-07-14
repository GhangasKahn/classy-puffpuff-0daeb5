// BEDROCK service worker — network-first for the app shell so new deploys
// appear immediately; cache-first for heavy CDN assets; offline fallback.
const CACHE = "bedrock-v7";
const CDN = [
  "https://unpkg.com/react@18.2.0/umd/react.production.min.js",
  "https://unpkg.com/react-dom@18.2.0/umd/react-dom.production.min.js",
  "https://unpkg.com/@babel/standalone@7.24.7/babel.min.js",
  "https://fonts.googleapis.com/css2?family=Archivo+Black&family=Archivo:wght@400;500;600;700&family=Chakra+Petch:wght@500;600;700&family=Space+Mono:wght@400;700&display=swap"
];
self.addEventListener("install", function (e) {
  e.waitUntil((async function () {
    const c = await caches.open(CACHE);
    try { await c.addAll(["./", "./index.html", "./manifest.json", "./bedrock-api.js", "./quant-engine.js", "./hermes-agents.js", "./icon-192.png", "./icon-512.png", "./apple-touch-icon.png", "./favicon-32.png"]); } catch (err) {}
    for (const u of CDN) { try { await c.add(u); } catch (err) {} }
    self.skipWaiting();
  })());
});
self.addEventListener("activate", function (e) {
  e.waitUntil(caches.keys().then(function (ks) {
    return Promise.all(ks.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});
self.addEventListener("fetch", function (e) {
  if (e.request.method !== "GET") return;
  const req = e.request;
  const isPage = req.mode === "navigate" || req.destination === "document";
  if (isPage) {
    // network-first: always try to fetch the freshest app, fall back to cache offline
    e.respondWith(
      fetch(req).then(function (resp) {
        const copy = resp.clone();
        caches.open(CACHE).then(function (c) { c.put(req, copy); }).catch(function () {});
        return resp;
      }).catch(function () {
        return caches.match(req).then(function (h) { return h || caches.match("./index.html"); });
      })
    );
    return;
  }
  // cache-first for static/CDN assets
  e.respondWith(caches.match(req).then(function (hit) {
    return hit || fetch(req).then(function (resp) {
      const copy = resp.clone();
      caches.open(CACHE).then(function (c) { c.put(req, copy); }).catch(function () {});
      return resp;
    }).catch(function () { return caches.match("./index.html"); });
  }));
});
