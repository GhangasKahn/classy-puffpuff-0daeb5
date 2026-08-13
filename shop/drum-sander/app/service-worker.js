const CACHE = "walter-ds16-v4";
const ASSETS = [
  "./",
  "./index.html",
  "./styles.css",
  "./app.js",
  "./data.js",
  "./model3d.js",
  "./manifest.json",
  "./icon.svg",
  "./apple-touch-icon.png",
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
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)));
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
  e.respondWith(
    caches.match(e.request).then((r) => r || fetch(e.request))
  );
});
