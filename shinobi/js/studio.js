import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

export const PARTS = [
  { id: "01-frame", key: "frame", label: "01 Frame", kind: "metal", mm: "94 × 16.2 × 4.6", job: "Ti-6Al-4V monocoque. Rinse slots, kusabi pocket, Ø4.40 eye." },
  { id: "02-mizu", key: "mizu", label: "02 MIZU-82", kind: "steel", mm: "82 + 28 tang × 15.2 × 1.55", job: "Low-belly river blade. 60/40 hamaguri as two flats. Distal to 0.60." },
  { id: "03-kumiko", key: "kumiko", label: "03 KUMIKO-42", kind: "steel", mm: "42 + 28 tang × 12.4 × 2.00", job: "Dead-flat ura. 15° single bevel. The land that registers to a square." },
  { id: "04-nata", key: "nata", label: "04 NATA-60", kind: "steel", mm: "60 + 28 tang × 17.8 × 2.40", job: "24° chisel. Whittling and notches. No baton face." },
  { id: "05-saya", key: "saya", label: "05 Saya", kind: "wood", mm: "92 × 20 × 9.2", job: "Kiri / honoki slip. 1.8 wall. The pale thing you can find." },
  { id: "06-spike", key: "spike", label: "06 KAGE-HARI", kind: "steel", mm: "Ø3.4 × 55", job: "Dedicated ikejime point. Not the knife tip." },
  { id: "07-togi", key: "togi", label: "07 TOGI plate", kind: "metal", mm: "52 × 18 × 2.8", job: "Hammered traction face. 600 / 1200 diamond and 1 μm strop." },
  { id: "08-tweezer", key: "tweezer", label: "08 Tweezer", kind: "metal", mm: "46 × 6.4 × 1.1", job: "Beta-titanium pinbone. Nests. Not for ikejime." },
  { id: "09-cassette", key: "cassette", label: "09 Cassette", kind: "metal", mm: "64 × 16 × 8.2", job: "Vented SHINKEI house. Open channels. No sealed cavity." },
  { id: "10-s50", key: "s50", label: "10 S-50", kind: "steel", mm: "Ø0.80 × 500", job: "Nitinol stock. Coil on this page is display only." },
  { id: "11-l80", key: "l80", label: "11 L-80", kind: "steel", mm: "Ø1.20 × 800", job: "Nitinol stock for adult salmon. Straight in the BOM." },
  { id: "12-locator", key: "locator", label: "12 Locator", kind: "cloth", mm: "22 × 8 × 0.7", job: "Pale mark on the saya mouth." },
  { id: "13-wedge", key: "wedge", label: "13 Kusabi", kind: "metal", mm: "16 × 7.2 × 2.40→1.55", job: "The one mating contract. Drives from the spine." },
  { id: "14-chest", key: "chest", label: "14 Chest", kind: "wood", mm: "168 × 78 × 22", job: "Kiri studio box. Open top. Not the wet system." }
];

export const byId = Object.fromEntries(PARTS.map((p) => [p.id, p]));
export const byKey = Object.fromEntries(PARTS.map((p) => [p.key, p]));

function prefersReduce() {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches
    || document.documentElement.dataset.motion === "off";
}

function boxUv(geometry) {
  geometry.computeBoundingBox();
  geometry.computeVertexNormals();
  const { min, max } = geometry.boundingBox;
  const size = new THREE.Vector3().subVectors(max, min);
  const pos = geometry.attributes.position;
  const nrm = geometry.attributes.normal;
  const uv = new Float32Array(pos.count * 2);
  const scale = 2.6 / Math.max(size.x, size.y, size.z, 1);
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i);
    const y = pos.getY(i);
    const z = pos.getZ(i);
    const ax = Math.abs(nrm.getX(i));
    const ay = Math.abs(nrm.getY(i));
    const az = Math.abs(nrm.getZ(i));
    let u;
    let v;
    if (ax >= ay && ax >= az) {
      u = y * scale;
      v = z * scale;
    } else if (ay >= ax && ay >= az) {
      u = x * scale;
      v = z * scale;
    } else {
      u = x * scale;
      v = y * scale;
    }
    uv[i * 2] = u;
    uv[i * 2 + 1] = v;
  }
  geometry.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
}

function makeTextures() {
  const loader = new THREE.TextureLoader();
  const albedo = loader.load("./assets/cad/togi-albedo.webp");
  const normal = loader.load("./assets/cad/togi-normal.webp");
  [albedo, normal].forEach((tex) => {
    tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
    tex.anisotropy = 8;
  });
  albedo.colorSpace = THREE.SRGBColorSpace;
  return { albedo, normal };
}

function materialFor(kind, textures) {
  const { albedo, normal } = textures;
  if (kind === "wood") {
    return new THREE.MeshPhysicalMaterial({
      color: 0xe2c48a,
      roughness: 0.78,
      metalness: 0.02,
      map: albedo,
      normalMap: normal,
      normalScale: new THREE.Vector2(0.28, 0.28),
      envMapIntensity: 0.45
    });
  }
  if (kind === "cloth") {
    return new THREE.MeshPhysicalMaterial({
      color: 0xf0e6d4,
      roughness: 0.92,
      metalness: 0,
      map: albedo,
      normalMap: normal,
      normalScale: new THREE.Vector2(0.15, 0.15),
      envMapIntensity: 0.25
    });
  }
  if (kind === "steel") {
    return new THREE.MeshPhysicalMaterial({
      color: 0xd8d2c4,
      roughness: 0.28,
      metalness: 0.92,
      map: albedo,
      normalMap: normal,
      normalScale: new THREE.Vector2(0.55, 0.55),
      envMapIntensity: 1.25,
      clearcoat: 0.15,
      clearcoatRoughness: 0.4
    });
  }
  return new THREE.MeshPhysicalMaterial({
    color: 0x6e6a64,
    roughness: 0.38,
    metalness: 0.86,
    map: albedo,
    normalMap: normal,
    normalScale: new THREE.Vector2(1.35, 1.35),
    envMapIntensity: 1.05,
    clearcoat: 0.35,
    clearcoatRoughness: 0.45
  });
}

export function createStudio(host, options = {}) {
  if (!host) throw new Error("studio host missing");
  const heightOf = () => {
    const fromCss = host.clientHeight || 0;
    const fromWidth = Math.max(options.minHeight || 320, (host.clientWidth || 320) * (options.ratio || 0.58));
    return Math.max(fromCss, fromWidth);
  };

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
  renderer.setSize(host.clientWidth || 320, heightOf());
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.28;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  host.appendChild(renderer.domElement);
  renderer.domElement.setAttribute("role", "img");
  renderer.domElement.setAttribute("aria-label", options.label || "CAD studio of SHINOBI parts");

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xeee4d4);
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.03).texture;

  const camera = new THREE.PerspectiveCamera(32, (host.clientWidth || 320) / heightOf(), 0.1, 4000);
  camera.position.set(90, 55, 120);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = !prefersReduce();
  controls.autoRotate = !prefersReduce() && options.spin !== false;
  controls.autoRotateSpeed = options.spinSpeed || 0.45;
  controls.enablePan = false;
  controls.target.set(0, 0, 0);

  const hemi = new THREE.HemisphereLight(0xfff4e4, 0x7a8a94, 0.85);
  scene.add(hemi);
  const key = new THREE.DirectionalLight(0xfff1dc, 1.35);
  key.position.set(60, 90, 50);
  key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0x9eb4c2, 0.4);
  fill.position.set(-70, 20, -30);
  scene.add(fill);
  const rim = new THREE.DirectionalLight(0xffffff, 0.55);
  rim.position.set(0, 20, 100);
  scene.add(rim);

  const ground = new THREE.Mesh(
    new THREE.CircleGeometry(480, 64),
    new THREE.MeshStandardMaterial({ color: 0xd9cbb6, roughness: 0.96, metalness: 0 })
  );
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  scene.add(ground);

  const loader = new STLLoader();
  const textures = makeTextures();
  const group = new THREE.Group();
  scene.add(group);

  const cache = new Map();
  let playing = true;
  const clock = new THREE.Clock();

  function fit() {
    const box = new THREE.Box3().setFromObject(group);
    if (!isFinite(box.min.x)) return;
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    group.position.sub(center);
    const span = Math.max(size.length(), 20);
    camera.position.set(span * 0.62, span * 0.38, span * 0.78);
    controls.target.set(0, 0, 0);
    controls.update();
    ground.position.y = -size.y * 0.5 - 0.4;
  }

  function clearGroup() {
    [...group.children].forEach((child) => {
      group.remove(child);
      child.geometry?.dispose();
      if (child.material && child.material !== textures) child.material.dispose?.();
    });
  }

  function meshFrom(id, geom) {
    const part = byId[id] || { kind: "metal" };
    const geo = geom.clone();
    boxUv(geo);
    const mesh = new THREE.Mesh(geo, materialFor(part.kind, textures));
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.userData.id = id;
    return mesh;
  }

  function loadGeom(id) {
    if (cache.has(id)) return Promise.resolve(cache.get(id));
    return new Promise((resolve, reject) => {
      loader.load(
        `./cad/stl/${id}.stl`,
        (geom) => {
          cache.set(id, geom);
          resolve(geom);
        },
        undefined,
        reject
      );
    });
  }

  async function showSingle(id) {
    const geom = await loadGeom(id);
    clearGroup();
    group.add(meshFrom(id, geom));
    fit();
    return byId[id];
  }

  async function showRow(ids) {
    clearGroup();
    let x = 0;
    for (const id of ids) {
      const geom = await loadGeom(id);
      const mesh = meshFrom(id, geom);
      const box = new THREE.Box3().setFromObject(mesh);
      const size = box.getSize(new THREE.Vector3());
      mesh.position.set(x - box.min.x, -box.min.y, -box.min.z);
      group.add(mesh);
      x += size.x + 12;
    }
    fit();
  }

  async function showSeat(detail) {
    const ids = ["01-frame"];
    const blade = byKey[detail.blade];
    if (blade) ids.push(blade.id);
    const extras = (detail.seated || [])
      .map((key) => byKey[key]?.id)
      .filter((id) => id && !ids.includes(id) && id !== "14-chest");
    await showRow([...ids, ...extras.slice(0, 6)]);
  }

  function frame() {
    if (!playing) return;
    const delta = clock.getDelta();
    const reduce = prefersReduce();
    controls.autoRotate = !reduce && options.spin !== false;
    controls.enableDamping = !reduce;
    controls.update(delta);
    renderer.render(scene, camera);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  const ro = new ResizeObserver(() => {
    const w = host.clientWidth || 320;
    const h = heightOf();
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  });
  ro.observe(host);

  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      playing = entries.some((e) => e.isIntersecting);
      if (playing) {
        clock.getDelta();
        requestAnimationFrame(frame);
      }
    }, { threshold: 0.04 });
    io.observe(host);
  }

  document.getElementById("motion-toggle")?.addEventListener("click", () => {
    controls.autoRotate = !prefersReduce() && options.spin !== false;
  });

  return { showSingle, showRow, showSeat, fit };
}

export function boot() {
  const inspect = document.getElementById("inspect-stage");
  const seat = document.getElementById("seat-stage");
  const grindStill = document.getElementById("grind-still");

  const inspectStudio = inspect ? createStudio(inspect, { ratio: 0.62, minHeight: 300, label: "Selected SHINOBI solid" }) : null;
  const seatStudio = seat ? createStudio(seat, { ratio: 0.55, minHeight: 260, label: "Seated loadout from the CAD solids" }) : null;

  const status = document.getElementById("inspect-status");
  const dim = document.getElementById("inspect-dim");
  const job = document.getElementById("inspect-job");
  const stepLink = document.getElementById("cad-step");
  const stlLink = document.getElementById("cad-download");

  async function inspectPart(id) {
    const part = byId[id];
    if (!part || !inspectStudio) return;
    await inspectStudio.showSingle(id);
    if (status) status.textContent = `${part.label} — the STEP solid, lit on washi. Proposed, not a released revision.`;
    if (dim) dim.textContent = part.mm;
    if (job) job.textContent = part.job;
    if (stepLink) {
      stepLink.href = `./cad/step/${id}.step`;
      stepLink.setAttribute("download", `${id}.step`);
      stepLink.textContent = `Download ${id}.step`;
    }
    if (stlLink) {
      stlLink.href = `./cad/stl/${id}.stl`;
      stlLink.setAttribute("download", `${id}.stl`);
      stlLink.textContent = `Download ${id}.stl`;
    }
    document.querySelectorAll("[data-inspect]").forEach((btn) => {
      btn.setAttribute("aria-pressed", btn.dataset.inspect === id ? "true" : "false");
    });
  }

  document.querySelectorAll("[data-inspect]").forEach((btn) => {
    btn.addEventListener("click", () => inspectPart(btn.dataset.inspect));
  });
  inspectPart("01-frame").catch(() => {});

  window.addEventListener("shinobi:inspect", (event) => {
    if (event.detail?.id) inspectPart(event.detail.id);
  });

  let lastGrind = "";
  window.addEventListener("shinobi:grind", (event) => {
    const part = byKey[event.detail?.blade];
    if (!part || part.id === lastGrind) return;
    lastGrind = part.id;
    if (grindStill) {
      grindStill.src = `./assets/studio/${part.id}.webp`;
      grindStill.alt = `${part.label} solid, rendered from the CadQuery mesh`;
    }
  });

  let seatTimer = 0;
  let lastSeat = "";
  window.addEventListener("shinobi:seat", (event) => {
    const key = JSON.stringify(event.detail || {});
    if (key === lastSeat) return;
    lastSeat = key;
    window.clearTimeout(seatTimer);
    seatTimer = window.setTimeout(() => seatStudio?.showSeat(event.detail || {}), 160);
  });

  seatStudio?.showSeat({ blade: "mizu", seated: ["saya", "togi", "spike", "tweezer"] });
}

boot();
