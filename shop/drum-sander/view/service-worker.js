const CACHE = "walter-view-v2";
const ASSETS = [
  "./",
  "./index.html",
  "./view.css",
  "./view.js",
  "./manifest.json",
  "../app/data.js",
  "../app/model3d.js",
  "../app/apple-touch-icon.png",
  "../app/icon.svg",
  "../vendor/three.module.js",
  "../vendor/OrbitControls.js",
  "../pocket/index.html",
  "../plans/D1_general.svg",
  "../plans/D2_frame.svg",
  "../plans/D3_drum.svg",
  "../plans/D4_drive.svg",
  "../plans/D5_hood.svg",
  "../plans/D6_cutlist.svg",
  "../plans/D7_geometry.svg",
  "../plans/D8_holddowns.svg",
  "../plans/D9_model.svg",
  "../plans/D10_lumberyard.svg",
  "../renders/iso_assembled.svg",
  "../renders/iso_exploded.svg",
  "../renders/ortho_front.svg",
  "../renders/ortho_side.svg",
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) =>
      Promise.all(ASSETS.map((url) => c.add(url).catch(() => undefined)))
    )
  );
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  const live = /(?:service-worker|view|model3d|index)\.(?:js|html)$/.test(url.pathname);
  if (live) {
    e.respondWith(
      fetch(e.request)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copy));
          return res;
        })
        .catch(() => caches.match(e.request))
    );
    return;
  }
  e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
});
