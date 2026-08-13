/* WALTER DS-16 — interactive Three.js solid model (inches, Y-up)
 * Shared by the Build app viz tab, the design hero, and /model/
 */
import * as THREE from "../vendor/three.module.js";
import { OrbitControls } from "../vendor/OrbitControls.js";
import { P } from "./geometry.js";

const COLORS = {
  sides: 0xc4a574,
  base: 0xa89070,
  stretch: 0x8a7355,
  ways: 0xd9dcde,
  table: 0xc4b8a4,
  wear: 0xd9dcde,
  drum: 0xb8a990,
  shaft: 0x8a9098,
  flange: 0x6e7578,
  motor: 0x4a5058,
  pulley: 0x5a6068,
  rollers: 0x5a6068,
  yoke: 0x8a7355,
  hood: 0x9aa8a0,
  port: 0x7a8f68,
  elev: 0x8a9098,
};

const PARTS = {
  sides: { label: "Side panels (2)", detail: "¾″ Baltic birch · stack-drilled as a pair" },
  base: { label: "Base deck", detail: "¾″ BB spanning overall width" },
  stretch: { label: "Stretchers (3)", detail: "P-003 housed in ¼″ dados — not the table datum" },
  ways: { label: "UHMW ways", detail: "Inner-face vertical reference · no rack" },
  table: { label: "Torsion-box table", detail: "Skins + ribs + phenolic/MIC-6 wear face" },
  elev: { label: "Dual Acme lift", detail: "½-10 screws · chain couple · home dog" },
  drum: { label: "Sanding drum", detail: "⌀5″ × 15.75″ · pack-bored discs" },
  shaft: { label: "Shaft + bearings", detail: "Fixed drive · floating idler" },
  rollers: { label: "Hold-down rollers", detail: "Infeed/outfeed · 0.030″ below drum" },
  motor: { label: "Motor + pulleys", detail: "½ HP · coplanar 3″/5″ · locked cradle" },
  hood: { label: "Dust hood", detail: "Kerf-bent · 4″ port · osc clearance" },
};

function mat(hex, opts = {}) {
  return new THREE.MeshStandardMaterial({
    color: hex,
    roughness: opts.roughness ?? 0.55,
    metalness: opts.metalness ?? 0.08,
    transparent: !!opts.opacity && opts.opacity < 1,
    opacity: opts.opacity ?? 1,
    emissive: opts.emissive ?? 0x000000,
    emissiveIntensity: opts.ei ?? 0,
    side: opts.side ?? THREE.FrontSide,
  });
}

function box(w, h, d, hex, extra = {}) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat(hex, extra));
  m.castShadow = true;
  m.receiveShadow = true;
  return m;
}

function cylX(len, r, hex, segs = 24, extra = {}) {
  const g = new THREE.CylinderGeometry(r, r, len, segs);
  g.rotateZ(Math.PI / 2);
  const m = new THREE.Mesh(g, mat(hex, extra));
  m.castShadow = true;
  m.receiveShadow = true;
  return m;
}

function tag(mesh, id) {
  mesh.userData.part = id;
  mesh.traverse((c) => {
    c.userData.part = id;
  });
  return mesh;
}

function buildMachine() {
  const root = new THREE.Group();
  root.name = "ds16";

  const groups = {};
  function grp(id) {
    if (!groups[id]) {
      groups[id] = new THREE.Group();
      groups[id].name = id;
      groups[id].userData.part = id;
      groups[id].userData.home = new THREE.Vector3();
      root.add(groups[id]);
    }
    return groups[id];
  }

  const base = box(P.W, 0.75, P.sideD, COLORS.base);
  base.position.y = 0.375;
  grp("base").add(tag(base, "base"));

  const L = box(P.sideT, P.sideH - 0.75, P.sideD, COLORS.sides);
  L.position.set(-P.hx + P.sideT / 2, 0.75 + (P.sideH - 0.75) / 2, 0);
  grp("sides").add(tag(L, "sides"));
  const R = box(P.sideT, P.sideH - 0.75, P.sideD, COLORS.sides);
  R.position.set(P.hx - P.sideT / 2, 0.75 + (P.sideH - 0.75) / 2, 0);
  grp("sides").add(tag(R, "sides"));

  for (const y of P.stretcherZ.map((z) => z + 0.375)) {
    const s = box(P.stretcherLen, 0.75, P.stretcherH, COLORS.stretch);
    s.position.set(0, y, -6);
    grp("stretch").add(tag(s, "stretch"));
  }

  const wayL = box(P.wayProject, P.wayStock, P.sideD - 2, COLORS.ways, { roughness: 0.3 });
  wayL.position.set(-P.hx + P.sideT + P.wayProject / 2, P.wayZ + P.wayStock / 2, 0);
  grp("ways").add(tag(wayL, "ways"));
  const wayR = box(P.wayProject, P.wayStock, P.sideD - 2, COLORS.ways, { roughness: 0.3 });
  wayR.position.set(P.hx - P.sideT - P.wayProject / 2, P.wayZ + P.wayStock / 2, 0);
  grp("ways").add(tag(wayR, "ways"));

  const core = box(P.tableW, P.tableT - 0.25, P.tableD, COLORS.table);
  core.position.set(0, P.tableY + (P.tableT - 0.25) / 2, 0);
  grp("table").add(tag(core, "table"));
  const wear = box(P.tableW, 0.25, P.tableD, COLORS.wear, { roughness: 0.35, metalness: 0.15 });
  wear.position.set(0, P.tableY + P.tableT - 0.125, 0);
  grp("table").add(tag(wear, "table"));

  for (const x of [-6.8, 6.8]) {
    const sc = new THREE.Mesh(
      new THREE.CylinderGeometry(0.25, 0.25, 14, 16),
      mat(COLORS.elev, { metalness: 0.55, roughness: 0.35 })
    );
    sc.position.set(x, 9, -6);
    sc.castShadow = true;
    grp("elev").add(tag(sc, "elev"));
    const nut = box(1.2, 0.5, 1.2, 0xb87333, { metalness: 0.4 });
    nut.position.set(x, P.tableY - 0.1, -6);
    grp("elev").add(tag(nut, "elev"));
  }

  const drumSpin = new THREE.Group();
  drumSpin.position.set(0, P.drumY, 0);
  const drum = cylX(P.drumLen, P.drumOd / 2, COLORS.drum, 32, { roughness: 0.7 });
  drumSpin.add(tag(drum, "drum"));
  for (let i = 0; i < 8; i++) {
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(P.drumOd / 2 + 0.03, 0.035, 6, 32),
      mat(0x8a7355, { roughness: 0.8 })
    );
    ring.rotation.y = Math.PI / 2;
    ring.position.x = -P.drumLen / 2 + 1 + i * 1.85;
    drumSpin.add(tag(ring, "drum"));
  }
  grp("drum").add(drumSpin);
  grp("drum").userData.spin = drumSpin;

  const shaft = cylX(P.shaftLen, P.shaftOd / 2, COLORS.shaft, 16, { metalness: 0.7, roughness: 0.25 });
  shaft.position.set(0, P.drumY, 0);
  grp("shaft").add(tag(shaft, "shaft"));
  for (const x of [-8.15, 8.15]) {
    const fl = box(0.5, 2.8, 2.8, COLORS.flange, { metalness: 0.45, roughness: 0.4 });
    fl.position.set(x, P.drumY, 0);
    grp("shaft").add(tag(fl, "shaft"));
  }

  const dPulley = cylX(0.9, 2.5, COLORS.pulley, 28, { metalness: 0.35 });
  dPulley.position.set(10.35, P.drumY, 0);
  grp("motor").add(tag(dPulley, "motor"));

  const motorBody = box(6, 6, 8, COLORS.motor, { metalness: 0.2, roughness: 0.5 });
  motorBody.position.set(6.2, 5.5, -7.2);
  grp("motor").add(tag(motorBody, "motor"));
  const mPulley = cylX(0.8, 1.5, COLORS.pulley, 24, { metalness: 0.35 });
  mPulley.position.set(9.4, 6.5, -5.2);
  grp("motor").add(tag(mPulley, "motor"));

  // V-belt as a thin tube path
  const beltPts = [
    new THREE.Vector3(10.35, P.drumY + 2.3, 0),
    new THREE.Vector3(10.0, 12, -2.2),
    new THREE.Vector3(9.4, 8.1, -5.2),
    new THREE.Vector3(9.4, 5.0, -5.2),
    new THREE.Vector3(10.1, 14, -1.5),
    new THREE.Vector3(10.35, P.drumY - 2.3, 0),
  ];
  const belt = new THREE.Mesh(
    new THREE.TubeGeometry(new THREE.CatmullRomCurve3(beltPts, true), 64, 0.12, 8, true),
    mat(0x2a2a2a, { roughness: 0.8 })
  );
  grp("motor").add(tag(belt, "motor"));

  const rY = P.tableY + P.tableT + P.rollerOd / 2 + 0.35;
  for (const z of [-3.6, 3.6]) {
    const r = cylX(P.rollerLen, P.rollerOd / 2, COLORS.rollers, 18, { roughness: 0.65 });
    r.position.set(0, rY, z);
    grp("rollers").add(tag(r, "rollers"));
    const yk = box(P.clear - 0.8, 0.4, 0.8, COLORS.yoke);
    yk.position.set(0, rY + 0.85, z);
    grp("rollers").add(tag(yk, "rollers"));
  }

  const hoodG = new THREE.CylinderGeometry(5.4, 5.4, P.clear - 1.2, 28, 1, true, 0, Math.PI);
  hoodG.rotateZ(Math.PI / 2);
  const hood = new THREE.Mesh(hoodG, mat(COLORS.hood, { opacity: 0.5, roughness: 0.45, side: THREE.DoubleSide }));
  hood.position.set(0, P.drumY, 0);
  hood.rotation.x = Math.PI; // arch over the drum
  grp("hood").add(tag(hood, "hood"));
  const port = new THREE.Mesh(
    new THREE.CylinderGeometry(2.0, 2.0, 1.6, 20),
    mat(COLORS.port, { roughness: 0.4 })
  );
  port.rotation.z = Math.PI / 2;
  port.position.set(7.4, P.drumY + 4.4, 0);
  grp("hood").add(tag(port, "hood"));

  groups.sides.userData.explode = new THREE.Vector3(0, 0, 0); // children handled
  groups.base.userData.explode = new THREE.Vector3(0, -2.5, 0);
  groups.stretch.userData.explode = new THREE.Vector3(0, 0, 2);
  groups.ways.userData.explode = new THREE.Vector3(0, 1.5, 0);
  groups.table.userData.explode = new THREE.Vector3(0, -4.5, 0);
  groups.elev.userData.explode = new THREE.Vector3(0, -3.5, -2);
  groups.drum.userData.explode = new THREE.Vector3(0, 5.5, 0);
  groups.shaft.userData.explode = new THREE.Vector3(0, 5.5, 0);
  groups.rollers.userData.explode = new THREE.Vector3(0, 2.2, 0);
  groups.motor.userData.explode = new THREE.Vector3(3.5, 0, -5);
  groups.hood.userData.explode = new THREE.Vector3(0, 8, 0);

  return { root, groups };
}

export function createWalterModel(container, options = {}) {
  const autoRotate = options.autoRotate !== false;
  const onSelect = options.onSelect || (() => {});

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(options.background ?? 0x14181c);
  scene.fog = new THREE.Fog(scene.background, 80, 160);

  const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 400);
  camera.position.set(38, 28, 42);

  const mobile = typeof window !== "undefined" && (window.innerWidth < 900 || matchMedia("(pointer: coarse)").matches);
  const renderer = new THREE.WebGLRenderer({
    antialias: !mobile,
    alpha: false,
    powerPreference: "default",
    failIfMajorPerformanceCaveat: false,
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, mobile ? 1.5 : 2));
  renderer.setClearColor(scene.background, 1);
  renderer.shadowMap.enabled = !mobile;
  if (!mobile) renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.domElement.style.width = "100%";
  renderer.domElement.style.height = "100%";
  renderer.domElement.style.display = "block";
  renderer.domElement.style.touchAction = "none";
  container.appendChild(renderer.domElement);

  const hemi = new THREE.HemisphereLight(0xf3f1ec, 0x3a3228, 0.85);
  scene.add(hemi);
  const key = new THREE.DirectionalLight(0xfff6e8, 1.35);
  key.position.set(24, 40, 18);
  key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024);
  key.shadow.camera.near = 4;
  key.shadow.camera.far = 90;
  key.shadow.camera.left = -30;
  key.shadow.camera.right = 30;
  key.shadow.camera.top = 30;
  key.shadow.camera.bottom = -30;
  scene.add(key);
  const fill = new THREE.DirectionalLight(0x8fad78, 0.35);
  fill.position.set(-20, 18, -12);
  scene.add(fill);

  const ground = new THREE.Mesh(
    new THREE.CircleGeometry(48, 48),
    new THREE.MeshStandardMaterial({ color: 0x1a2228, roughness: 1, metalness: 0 })
  );
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = 0;
  ground.receiveShadow = true;
  scene.add(ground);

  const { root, groups } = buildMachine();
  scene.add(root);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.06;
  controls.target.set(0, 14, 0);
  controls.minPolarAngle = 0.12;
  controls.maxPolarAngle = Math.PI * 0.72;
  controls.minDistance = 18;
  controls.maxDistance = 90;
  controls.autoRotate = autoRotate;
  controls.autoRotateSpeed = 0.6;

  const ray = new THREE.Raycaster();
  const mouse = new THREE.Vector2();
  let selected = null;
  const original = new Map();

  function highlight(id) {
    selected = id;
    root.traverse((obj) => {
      if (!obj.isMesh || !obj.material) return;
      if (!original.has(obj)) {
        original.set(obj, obj.material.emissiveIntensity || 0);
      }
      const on = id && obj.userData.part === id;
      obj.material.emissive = new THREE.Color(on ? 0x8fad78 : 0x000000);
      obj.material.emissiveIntensity = on ? 0.35 : 0;
    });
    if (id && PARTS[id]) onSelect(id, PARTS[id]);
  }

  function setExplode(t) {
    const k = Math.max(0, Math.min(1, t));
    for (const g of Object.values(groups)) {
      const v = g.userData.explode || new THREE.Vector3();
      g.position.copy(v).multiplyScalar(k);
    }
    // split sides left/right extra
    const sideKids = groups.sides.children;
    if (sideKids[0]) sideKids[0].position.x = -P.hx + P.sideT / 2 - k * 4.5;
    if (sideKids[1]) sideKids[1].position.x = P.hx - P.sideT / 2 + k * 4.5;
  }

  function resize() {
    const w = Math.max(container.clientWidth || 0, container.offsetWidth || 0, 280);
    const h = Math.max(container.clientHeight || 0, container.offsetHeight || 0, 240);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h, true);
  }

  const ro = new ResizeObserver(resize);
  ro.observe(container);
  resize();

  renderer.domElement.addEventListener("pointerdown", (ev) => {
    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ((ev.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((ev.clientY - rect.top) / rect.height) * 2 + 1;
    ray.setFromCamera(mouse, camera);
    const hits = ray.intersectObjects(root.children, true);
    if (hits.length) highlight(hits[0].object.userData.part || null);
  });

  let raf = 0;
  let drumSpin = 0;
  function tick() {
    raf = requestAnimationFrame(tick);
    drumSpin += 0.012;
    if (groups.drum?.userData.spin) groups.drum.userData.spin.rotation.x = drumSpin;
    controls.update();
    renderer.render(scene, camera);
  }
  tick();

  function dispose() {
    cancelAnimationFrame(raf);
    ro.disconnect();
    controls.dispose();
    renderer.dispose();
    if (renderer.domElement.parentNode) renderer.domElement.parentNode.removeChild(renderer.domElement);
  }

  return {
    setExplode,
    highlight,
    select: highlight,
    parts: PARTS,
    resize,
    dispose,
    controls,
  };
}

export { PARTS };
