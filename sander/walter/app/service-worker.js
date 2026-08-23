const CACHE = "walter-v3";
const ASSETS = ["./","index.html","styles.css","app.js","data.js","solids.js","scene.js","immersive.html","manifest.json","icon.svg"];
self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
});
self.addEventListener("fetch", e => {
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});
