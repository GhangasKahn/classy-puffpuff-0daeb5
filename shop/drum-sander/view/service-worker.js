const CACHE = "walter-view-v6";
const ASSETS = [
  "./",
  "./index.html",
  "./view.css",
  "./view.js",
  "./manifest.json",
  "../app/data.js",
  "../app/model3d.js",
  "../app/geometry.js",
  "../app/apple-touch-icon.png",
  "../app/icon.svg",
  "../vendor/three.module.js",
  "../vendor/OrbitControls.js",
  "../pocket/index.html",
  "../guide/index.html",
  "../plans/G001_cover.svg",
  "../plans/G002_design_basis.svg",
  "../plans/G003_registers.svg",
  "../plans/G004_safety.svg",
  "../plans/E101_exploded.svg",
  "../plans/M101_kinematics.svg",
  "../plans/J001_stretcher.svg",
  "../plans/J002_way.svg",
  "../plans/J006_drive_bearing.svg",
  "../plans/J007_idler_float.svg",
  "../plans/J011_lift.svg",
  "../plans/F101_routing.svg",
  "../plans/S101_load_path.svg",
  "../plans/Q101_commissioning.svg",
  "../plans/Q102_zero_gap.svg",
  "../plans/ST01_step.svg",
  "../plans/ST02_step.svg",
  "../plans/ST03_step.svg",
  "../plans/ST04_step.svg",
  "../plans/ST05_step.svg",
  "../plans/ST06_step.svg",
  "../plans/ST07_step.svg",
  "../plans/ST08_step.svg",
  "../plans/ST09_step.svg",
  "../plans/ST10_step.svg",
  "../plans/ST11_step.svg",
  "../plans/ST12_step.svg",
  "../plans/ST13_step.svg",
  "../plans/ST14_step.svg",
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
  "../plans/P017_table_shoe.svg",
  "../plans/P018_thrust_block.svg",
  "../plans/P019_home_dog.svg",
  "../plans/A01_frame.svg",
  "../plans/A02_drum.svg",
  "../plans/A03_table.svg",
  "../plans/A04_drive.svg",
  "../plans/A05_holddowns.svg",
  "../plans/H01_hardware.svg",
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
