/* DS-18 parametric Three.js scene. 1 unit = 1 inch.
   Three.js is imported only inside mountScene so a CDN miss cannot blank the app. */

const M = window.DS_DATA.meta;

export async function mountScene(stage, hooks = {}) {
  const { onPick, onReady } = hooks;
  const THREE = await import("three");
  const { OrbitControls } = await import("three/addons/controls/OrbitControls.js");

  function mat(hex, opts = {}) {
    return new THREE.MeshStandardMaterial({
      color: hex,
      roughness: opts.roughness ?? 0.62,
      metalness: opts.metalness ?? 0.08,
      emissive: opts.emissive ?? 0x000000,
      emissiveIntensity: opts.emissiveIntensity ?? 0,
    });
  }

  function box(w, h, d, material) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), material);
    m.castShadow = true;
    m.receiveShadow = true;
    return m;
  }

  function cyl(rTop, rBot, h, segs, material, axis = "y") {
    const m = new THREE.Mesh(new THREE.CylinderGeometry(rTop, rBot, h, segs), material);
    if (axis === "x") m.rotation.z = Math.PI / 2;
    if (axis === "z") m.rotation.x = Math.PI / 2;
    m.castShadow = true;
    m.receiveShadow = true;
    return m;
  }

  function tag(obj, id) {
    obj.userData.partId = id;
    obj.traverse((c) => {
      c.userData.partId = id;
    });
    return obj;
  }

  const W = stage.clientWidth || 640;
  const H = stage.clientHeight || 420;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x1a1f27);
  scene.fog = new THREE.Fog(0x1a1f27, 90, 220);

  const camera = new THREE.PerspectiveCamera(42, W / H, 0.1, 500);
  camera.position.set(48, 38, 56);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(W, H);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  stage.innerHTML = "";
  stage.appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.target.set(0, 22, 0);
  controls.maxPolarAngle = Math.PI * 0.48;
  controls.minDistance = 28;
  controls.maxDistance = 140;

  scene.add(new THREE.HemisphereLight(0xf4efe6, 0x2a241c, 0.85));
  const key = new THREE.DirectionalLight(0xffe6c8, 1.15);
  key.position.set(30, 55, 28);
  key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024);
  key.shadow.camera.near = 10;
  key.shadow.camera.far = 140;
  key.shadow.camera.left = -50;
  key.shadow.camera.right = 50;
  key.shadow.camera.top = 50;
  key.shadow.camera.bottom = -50;
  scene.add(key);
  const fill = new THREE.DirectionalLight(0x8aa0b8, 0.35);
  fill.position.set(-40, 20, -20);
  scene.add(fill);

  const floor = new THREE.Mesh(
    new THREE.CircleGeometry(70, 48),
    new THREE.MeshStandardMaterial({ color: 0x2a241c, roughness: 0.95, metalness: 0 })
  );
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  scene.add(floor);
  const grid = new THREE.GridHelper(80, 16, 0x3a342c, 0x2a2620);
  grid.position.y = 0.02;
  scene.add(grid);

  const root = new THREE.Group();
  scene.add(root);

  const groups = {};
  const home = {};
  const explodeDir = {};

  function addGroup(id, dir) {
    const g = new THREE.Group();
    g.name = id;
    root.add(g);
    groups[id] = g;
    explodeDir[id] = dir.clone();
    return g;
  }

  const ply = mat(0xc4a574, { roughness: 0.78 });
  const plyDark = mat(0xb08958, { roughness: 0.8 });
  const plyLite = mat(0xd2b48c, { roughness: 0.74 });
  const steel = mat(0x8a9098, { metalness: 0.65, roughness: 0.32 });
  const steelDark = mat(0x5a6570, { metalness: 0.7, roughness: 0.28 });
  const shaftMat = mat(0xc5cbcf, { metalness: 0.85, roughness: 0.18 });
  const motorMat = mat(0x2a2e33, { metalness: 0.4, roughness: 0.45 });
  const beltMat = mat(0x1a1a1a, { roughness: 0.7 });
  const sand = mat(0xd4a574, { roughness: 0.92 });
  const hoodMat = mat(0x4a5560, { metalness: 0.35, roughness: 0.45 });
  const copper = mat(0xc47a3a, { metalness: 0.2, roughness: 0.5, emissive: 0x3a1808, emissiveIntensity: 0.15 });
  const fenceMat = mat(0x8b5a2b, { roughness: 0.7 });

  const cabW = M.cabW;
  const cabD = M.cabD;
  const cabH = M.cabH;
  const t = 0.75;

  /* ---- cabinet ---- */
  const cab = addGroup("cabinet", new THREE.Vector3(0, -10, 0));
  const left = box(t, cabH, cabD, ply);
  left.position.set(-cabW / 2 + t / 2, cabH / 2, 0);
  const right = box(t, cabH, cabD, ply);
  right.position.set(cabW / 2 - t / 2, cabH / 2, 0);
  const front = box(cabW - 2 * t, cabH, t, plyDark);
  front.position.set(0, cabH / 2, cabD / 2 - t / 2);
  const back = box(cabW - 2 * t, cabH, t, plyDark);
  back.position.set(0, cabH / 2, -cabD / 2 + t / 2);
  const bottom = box(cabW - 2 * t, t, cabD - 2 * t, ply);
  bottom.position.set(0, t / 2, 0);
  const shelf = box(14, t, cabD - 2 * t, plyLite);
  shelf.position.set(-cabW / 2 + 8, 8, 0);
  cab.add(left, right, front, back, bottom, shelf);
  tag(cab, "cabinet");

  /* casters */
  for (const [x, z] of [
    [-cabW / 2 + 3, -cabD / 2 + 3],
    [cabW / 2 - 3, -cabD / 2 + 3],
    [-cabW / 2 + 3, cabD / 2 - 3],
    [cabW / 2 - 3, cabD / 2 - 3],
  ]) {
    const wheel = cyl(1.4, 1.4, 1.2, 16, steelDark);
    wheel.position.set(x, -0.4, z);
    cab.add(wheel);
  }

  /* ---- motor ---- */
  const motorG = addGroup("motor", new THREE.Vector3(-16, -4, -8));
  const motorBody = cyl(3.4, 3.4, 9, 24, motorMat, "x");
  motorBody.position.set(-10, 11.2, -2);
  const motorEnd = box(1.2, 6.2, 6.2, steelDark);
  motorEnd.position.set(-5.2, 11.2, -2);
  const feet = box(8, 0.6, 5.5, steel);
  feet.position.set(-10, 7.6, -2);
  motorG.add(motorBody, motorEnd, feet);
  tag(motorG, "motor");

  const pulleyM = addGroup("pulleyM", new THREE.Vector3(-18, 0, -6));
  const pm = cyl(2, 2, 0.9, 28, steel, "x");
  pm.position.set(-4.4, 11.2, -2);
  pulleyM.add(pm);
  tag(pulleyM, "pulleyM");

  /* ---- uprights / towers ---- */
  const towers = addGroup("uprights", new THREE.Vector3(0, 4, 0));
  const tw = 6;
  const th = 14;
  const towerL = box(t, th, tw, plyDark);
  towerL.position.set(-10.5, cabH + th / 2, 0);
  const towerR = box(t, th, tw, plyDark);
  towerR.position.set(10.5, cabH + th / 2, 0);
  towers.add(towerL, towerR);
  tag(towers, "uprights");

  /* ---- drum + shaft (spin together) ---- */
  const drumY = cabH + 8;
  const drumG = addGroup("drum", new THREE.Vector3(0, 14, 0));
  const drumMesh = cyl(M.drumOd / 2, M.drumOd / 2, M.drumLen, 48, sand, "x");
  drumMesh.position.set(0, drumY, 0);
  const stripe = cyl(M.drumOd / 2 + 0.04, M.drumOd / 2 + 0.04, 0.35, 48, mat(0x8b5a2b, { roughness: 0.9 }), "x");
  stripe.position.set(-M.drumLen / 2 + 0.4, drumY, 0);
  drumG.add(drumMesh, stripe);
  tag(drumG, "drum");

  const shaftG = addGroup("shaft", new THREE.Vector3(0, 12, 0));
  const shaftMesh = cyl(M.shaftOd / 2, M.shaftOd / 2, M.shaftLen, 24, shaftMat, "x");
  shaftMesh.position.set(0, drumY, 0);
  shaftG.add(shaftMesh);
  tag(shaftG, "shaft");

  const pulleyD = addGroup("pulleyD", new THREE.Vector3(-14, 12, 0));
  const pd = cyl(4, 4, 1.0, 32, steel, "x");
  pd.position.set(-11.2, drumY, 0);
  pulleyD.add(pd);
  tag(pulleyD, "pulleyD");

  /* belt as a flattened torus-ish loop (two pulleys) */
  const beltG = addGroup("belt", new THREE.Vector3(-16, 6, -4));
  const belt = new THREE.Mesh(
    new THREE.TorusGeometry(6.4, 0.22, 10, 48),
    beltMat
  );
  belt.rotation.y = Math.PI / 2;
  belt.position.set(-11.2, (drumY + 11.2) / 2, -1);
  belt.scale.set(1, (drumY - 11.2) / 12.8 + 0.55, 0.55);
  beltG.add(belt);
  tag(beltG, "belt");

  /* bearings */
  const brg = addGroup("bearings", new THREE.Vector3(0, 8, 4));
  function pillow(x) {
    const g = new THREE.Group();
    const base = box(3.2, 0.7, 4.2, steelDark);
    base.position.y = -2.1;
    const body = cyl(1.6, 1.6, 1.8, 20, steel, "x");
    g.add(base, body);
    g.position.set(x, drumY, 0);
    return g;
  }
  brg.add(pillow(-9.6), pillow(9.6));
  tag(brg, "bearings");

  /* table + fence + jacks */
  const tableY0 = drumY - M.drumOd / 2 - 0.9;
  const tableG = addGroup("table", new THREE.Vector3(0, -8, 8));
  const table = box(M.tableW, t, M.tableD, plyLite);
  table.position.set(0, tableY0, 2);
  tableG.add(table);
  tag(tableG, "table");

  const fenceG = addGroup("fence", new THREE.Vector3(0, -6, 12));
  const fence = box(M.tableW, 3, 0.75, fenceMat);
  fence.position.set(0, tableY0 + 1.5 + t / 2, 2 - M.tableD / 2 + 0.4);
  fenceG.add(fence);
  tag(fenceG, "fence");

  const jacksG = addGroup("jacks", new THREE.Vector3(0, -12, 6));
  const jackPts = [
    [-8, 2 - M.tableD / 2 + 2],
    [8, 2 - M.tableD / 2 + 2],
    [-8, 2 + M.tableD / 2 - 2],
    [8, 2 + M.tableD / 2 - 2],
  ];
  for (const [x, z] of jackPts) {
    const rod = cyl(0.22, 0.22, 10, 10, shaftMat);
    rod.position.set(x, tableY0 - 5, z);
    const wheel = cyl(1.4, 1.4, 0.45, 18, steel);
    wheel.position.set(x, tableY0 - 9.6, z);
    jacksG.add(rod, wheel);
  }
  tag(jacksG, "jacks");

  /* hood + port */
  const hoodG = addGroup("hood", new THREE.Vector3(0, 16, -6));
  const hood = new THREE.Mesh(
    new THREE.CylinderGeometry(4.2, 4.2, 18.4, 28, 1, false, 0, Math.PI),
    hoodMat
  );
  hood.rotation.z = Math.PI / 2;
  hood.rotation.x = Math.PI;
  hood.position.set(0, drumY + 0.4, -0.4);
  hoodG.add(hood);
  tag(hoodG, "hood");

  const portG = addGroup("port", new THREE.Vector3(0, 10, -14));
  const port = cyl(2, 2, 4, 20, steelDark, "z");
  port.position.set(0, drumY + 2.2, -6.5);
  const flange = cyl(2.6, 2.6, 0.3, 20, steel, "z");
  flange.position.set(0, drumY + 2.2, -8.4);
  portG.add(port, flange);
  tag(portG, "port");

  /* switch */
  const swG = addGroup("switch", new THREE.Vector3(-14, 0, 10));
  const sw = box(3.2, 4.4, 2.2, copper);
  sw.position.set(-cabW / 2 - 0.4, 18, cabD / 2 - 4);
  const knob = cyl(0.55, 0.55, 0.5, 12, mat(0xf4efe6), "z");
  knob.position.set(-cabW / 2 + 0.8, 18.6, cabD / 2 - 2.7);
  swG.add(sw, knob);
  tag(swG, "switch");

  Object.keys(groups).forEach((id) => {
    home[id] = groups[id].position.clone();
  });

  /* picking */
  const ray = new THREE.Raycaster();
  const mouse = new THREE.Vector2();
  let selected = null;
  const highlight = {};

  function applySelect(id) {
    selected = id;
    Object.entries(groups).forEach(([gid, g]) => {
      g.traverse((c) => {
        if (!c.isMesh || !c.material) return;
        if (!highlight[c.uuid]) {
          highlight[c.uuid] = { em: c.material.emissive?.clone?.() || new THREE.Color(0), ei: c.material.emissiveIntensity || 0 };
        }
        const hot = id && gid === id;
        const dim = id && gid !== id;
        c.material.transparent = true;
        c.material.opacity = dim ? 0.22 : 1;
        if (c.material.emissive) {
          c.material.emissive.set(hot ? 0xc47a3a : 0x000000);
          c.material.emissiveIntensity = hot ? 0.35 : 0;
        }
      });
    });
  }

  function pick(ev) {
    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ((ev.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((ev.clientY - rect.top) / rect.height) * 2 + 1;
    ray.setFromCamera(mouse, camera);
    const hits = ray.intersectObjects(root.children, true);
    const id = hits[0]?.object?.userData?.partId || null;
    applySelect(id);
    if (onPick) onPick(id);
  }
  renderer.domElement.addEventListener("pointerdown", pick);

  let explode = 0;
  let tableLift = 0;
  let spin = true;
  let raf = 0;
  let disposed = false;

  function setExplode(t01) {
    explode = Math.max(0, Math.min(1, t01));
    Object.entries(groups).forEach(([id, g]) => {
      const d = explodeDir[id];
      g.position.set(home[id].x + d.x * explode, home[id].y + d.y * explode, home[id].z + d.z * explode);
    });
  }

  function setTableLift(t01) {
    tableLift = t01;
    const dy = t01 * M.tableTravel;
    tableG.position.y = home.table.y + explodeDir.table.y * explode + dy;
    fenceG.position.y = home.fence.y + explodeDir.fence.y * explode + dy;
  }

  function setSpin(on) {
    spin = !!on;
  }

  function selectPart(id) {
    applySelect(id);
  }

  function resize() {
    const w = stage.clientWidth || 640;
    const h = stage.clientHeight || 420;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  }

  const ro = new ResizeObserver(resize);
  ro.observe(stage);

  const clock = new THREE.Clock();
  function tick() {
    if (disposed) return;
    raf = requestAnimationFrame(tick);
    const dt = clock.getDelta();
    if (spin) {
      drumG.rotation.x += dt * 1.8;
      shaftG.rotation.x += dt * 1.8;
      pulleyD.rotation.x += dt * 1.8;
      pulleyM.rotation.x += dt * 3.6;
    }
    controls.update();
    renderer.render(scene, camera);
  }
  tick();

  function dispose() {
    disposed = true;
    cancelAnimationFrame(raf);
    ro.disconnect();
    renderer.domElement.removeEventListener("pointerdown", pick);
    controls.dispose();
    renderer.dispose();
  }

  function resetCamera() {
    camera.position.set(48, 38, 56);
    controls.target.set(0, 22, 0);
  }

  if (onReady) onReady();
  return { setExplode, setTableLift, setSpin, selectPart, resize, dispose, resetCamera };
}

export function drawFallbackSvg(stage, { explode = 0, selected = null, onPick } = {}) {
  const e = explode;
  const lift = e * 40;
  const spread = e * 28;
  const dim = (id) => (selected && selected !== id ? " dim" : selected === id ? " hot" : "");
  stage.innerHTML = `
<svg viewBox="0 0 640 420" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DS-18 isometric fallback">
  <defs>
    <filter id="glow"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect width="640" height="420" fill="#1a1f27"/>
  <ellipse cx="320" cy="368" rx="210" ry="22" fill="#2a241c"/>
  <g class="iso-part${dim("cabinet")}" data-part="cabinet" transform="translate(0,${lift * 0.4})">
    <polygon points="${180 - spread},${260 + lift} ${360 + spread},${260 + lift} ${420 + spread},${210 + lift} ${240 - spread},${210 + lift}" fill="#b08958" stroke="#1a1f24"/>
    <polygon points="${180 - spread},${260 + lift} ${240 - spread},${210 + lift} ${240 - spread},${120 + lift} ${180 - spread},${170 + lift}" fill="#c4a574" stroke="#1a1f24"/>
    <polygon points="${360 + spread},${260 + lift} ${420 + spread},${210 + lift} ${420 + spread},${120 + lift} ${360 + spread},${170 + lift}" fill="#a07848" stroke="#1a1f24"/>
  </g>
  <g class="iso-part${dim("motor")}" data-part="motor" transform="translate(${-spread},${lift * 0.2})">
    <ellipse cx="230" cy="${188 + lift}" rx="22" ry="14" fill="#2a2e33" stroke="#1a1f24"/>
    <rect x="208" y="${174 + lift}" width="44" height="28" rx="10" fill="#2a2e33" stroke="#1a1f24"/>
  </g>
  <g class="iso-part${dim("drum")}" data-part="drum" transform="translate(0,${-lift})">
    <ellipse cx="318" cy="${118 + lift}" rx="86" ry="22" fill="#d4a574" stroke="#1a1f24" stroke-width="1.4"/>
    <rect x="232" y="${106 + lift}" width="172" height="24" fill="#d4a574"/>
    <ellipse cx="318" cy="${106 + lift}" rx="86" ry="22" fill="#e0b888" stroke="#1a1f24" stroke-width="1.4"/>
  </g>
  <g class="iso-part${dim("hood")}" data-part="hood" transform="translate(0,${-lift * 1.3})">
    <path d="M232 ${96 + lift} C232 ${70 + lift}, 404 ${70 + lift}, 404 ${96 + lift}" fill="none" stroke="#4a5560" stroke-width="10" stroke-linecap="round"/>
  </g>
  <g class="iso-part${dim("table")}" data-part="table" transform="translate(0,${lift * 0.7})">
    <polygon points="${210},${200 + lift} ${410},${200 + lift} ${450},${168 + lift} ${250},${168 + lift}" fill="#d2b48c" stroke="#1a1f24"/>
  </g>
  <g class="iso-part${dim("switch")}" data-part="switch">
    <rect x="${152 - spread}" y="${200 + lift * 0.3}" width="18" height="28" rx="3" fill="#c47a3a" stroke="#1a1f24"/>
  </g>
  <text x="24" y="36" fill="#e09a58" font-family="IBM Plex Mono,monospace" font-size="12">DS-18 · isometric fallback</text>
  <text x="24" y="54" fill="#7a7368" font-family="IBM Plex Mono,monospace" font-size="11">Three.js CDN unavailable — 2D still picks &amp; explodes</text>
</svg>`;
  stage.querySelectorAll("[data-part]").forEach((el) => {
    el.addEventListener("click", (ev) => {
      ev.stopPropagation();
      if (onPick) onPick(el.dataset.part);
    });
  });
}
