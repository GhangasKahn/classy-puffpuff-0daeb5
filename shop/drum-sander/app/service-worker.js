const CACHE = "walter-ds16-v7";
const ASSETS = [
  "./",
  "./index.html",
  "./styles.css",
  "./app.js",
  "./data.js",
  "./model3d.js",
  "./geometry.js",
  "./manifest.json",
  "./icon.svg",
  "./apple-touch-icon.png",
  "../vendor/three.module.js",
  "../vendor/OrbitControls.js",
  "../pocket/index.html",
  "../plans/IDX_drawings.svg",
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
  "../plans/D11_register.svg",
  "../plans/D12_joinery.svg",
  "../plans/P001L_side_drive.svg",
  "../plans/P001R_side_idler.svg",
  "../plans/P002_base.svg",
  "../plans/P003_stretcher.svg",
  "../plans/P004_table_skin.svg",
  "../plans/P005_table_ribs.svg",
  "../plans/P006_wear_face.svg",
  "../plans/P007_uhmw_way.svg",
  "../plans/P008_disc_core.svg",
  "../plans/P009_disc_end.svg",
  "../plans/P010_shaft.svg",
  "../plans/P011_hood.svg",
  "../plans/P012_motor_cradle.svg",
  "../plans/P013_truing_sled.svg",
  "../plans/P014_roller_yoke.svg",
  "../plans/P015_pack_bore.svg",
  "../plans/P016_nut_block.svg",
  "../plans/A01_frame.svg",
  "../plans/A02_drum.svg",
  "../plans/A03_table.svg",
  "../plans/A04_drive.svg",
  "../plans/A05_holddowns.svg",
  "../plans/H01_hardware.svg",
  "../renders/iso_assembled.svg",
  "../renders/iso_exploded.svg",
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
  e.respondWith(
    caches.match(e.request).then((r) => r || fetch(e.request))
  );
});
