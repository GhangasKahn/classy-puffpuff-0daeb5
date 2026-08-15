import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";

const PARTS = [
  { id: "01-frame", label: "01 Frame", kind: "metal" },
  { id: "02-mizu", label: "02 MIZU-82", kind: "metal" },
  { id: "03-kumiko", label: "03 KUMIKO-42", kind: "metal" },
  { id: "04-nata", label: "04 NATA-60", kind: "metal" },
  { id: "05-saya", label: "05 Saya", kind: "wood" },
  { id: "06-spike", label: "06 KAGE-HARI", kind: "metal" },
  { id: "07-togi", label: "07 TOGI plate", kind: "metal" },
  { id: "08-tweezer", label: "08 Tweezer", kind: "metal" },
  { id: "09-cassette", label: "09 Cassette", kind: "metal" },
  { id: "10-s50", label: "10 S-50 coil", kind: "metal" },
  { id: "11-l80", label: "11 L-80 coil", kind: "metal" },
  { id: "12-locator", label: "12 Locator", kind: "cloth" },
  { id: "13-wedge", label: "13 Kusabi wedge", kind: "metal" },
  { id: "14-chest", label: "14 Kiri chest", kind: "wood" }
];

const host = document.getElementById("cad-stage");
const list = document.getElementById("cad-parts");
const status = document.getElementById("cad-status");
const download = document.getElementById("cad-download");
if (!host || !list) {
  throw new Error("CAD viewer markup missing");
}

const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches
  || document.documentElement.dataset.motion === "off";

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: "high-performance" });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
renderer.setSize(host.clientWidth, Math.max(320, host.clientWidth * 0.62));
renderer.outputColorSpace = THREE.SRGBColorSpace;
host.appendChild(renderer.domElement);
renderer.domElement.setAttribute("role", "img");
renderer.domElement.setAttribute("aria-label", "Interactive CAD view of the selected SHINOBI part");

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x161816);
const camera = new THREE.PerspectiveCamera(35, host.clientWidth / Math.max(320, host.clientWidth * 0.62), 0.1, 2000);
camera.position.set(80, 48, 110);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = !reduce;
controls.autoRotate = !reduce;
controls.autoRotateSpeed = 0.6;
controls.enablePan = false;

scene.add(new THREE.AmbientLight(0xcfc4b2, 0.55));
const key = new THREE.DirectionalLight(0xfff4e2, 1.15);
key.position.set(40, 80, 60);
scene.add(key);
const fill = new THREE.DirectionalLight(0x9eb4c2, 0.35);
fill.position.set(-60, 20, -40);
scene.add(fill);
const rim = new THREE.DirectionalLight(0xffffff, 0.25);
rim.position.set(0, -30, 80);
scene.add(rim);

const loader = new STLLoader();
const texLoader = new THREE.TextureLoader();
const albedo = texLoader.load("./assets/cad/togi-albedo.webp");
const normal = texLoader.load("./assets/cad/togi-normal.webp");
albedo.wrapS = albedo.wrapT = THREE.RepeatWrapping;
normal.wrapS = normal.wrapT = THREE.RepeatWrapping;
albedo.colorSpace = THREE.SRGBColorSpace;
albedo.repeat.set(2.2, 2.2);
normal.repeat.set(2.2, 2.2);

function materialFor(kind) {
  if (kind === "wood") {
    return new THREE.MeshStandardMaterial({
      color: 0xc9b48a,
      roughness: 0.72,
      metalness: 0.02,
      map: albedo,
      normalMap: normal,
      normalScale: new THREE.Vector2(0.35, 0.35)
    });
  }
  if (kind === "cloth") {
    return new THREE.MeshStandardMaterial({
      color: 0xe8e0d2,
      roughness: 0.9,
      metalness: 0,
      map: albedo,
      normalMap: normal,
      normalScale: new THREE.Vector2(0.2, 0.2)
    });
  }
  return new THREE.MeshStandardMaterial({
    color: 0x8a8680,
    roughness: 0.42,
    metalness: 0.72,
    map: albedo,
    normalMap: normal,
    normalScale: new THREE.Vector2(1.15, 1.15)
  });
}

let current;
let playing = true;
const clock = new THREE.Clock();

function fit(mesh) {
  const box = new THREE.Box3().setFromObject(mesh);
  const size = box.getSize(new THREE.Vector3()).length();
  const center = box.getCenter(new THREE.Vector3());
  mesh.position.sub(center);
  camera.position.set(size * 0.7, size * 0.42, size * 0.9);
  controls.target.set(0, 0, 0);
  controls.update();
}

function setStatus(text) {
  if (status) status.textContent = text;
}

function loadPart(part) {
  setStatus(`Loading ${part.label}…`);
  loader.load(
    `./cad/stl/${part.id}.stl`,
    (geom) => {
      geom.computeVertexNormals();
      if (current) {
        scene.remove(current);
        current.geometry.dispose();
        current.material.dispose();
      }
      current = new THREE.Mesh(geom, materialFor(part.kind));
      scene.add(current);
      fit(current);
      if (download) {
        download.href = `./cad/stl/${part.id}.stl`;
        download.setAttribute("download", `${part.id}.stl`);
        download.textContent = `Download ${part.id}.stl`;
      }
      setStatus(`${part.label} — TOGI hammered map on every textured face. Proposed CAD, not a production release.`);
      list.querySelectorAll("[data-cad]").forEach((btn) => {
        btn.setAttribute("aria-pressed", btn.dataset.cad === part.id ? "true" : "false");
      });
    },
    undefined,
    () => setStatus(`Could not load ${part.label}.`)
  );
}

PARTS.forEach((part, i) => {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "tag-btn";
  btn.dataset.cad = part.id;
  btn.textContent = part.label;
  btn.setAttribute("aria-pressed", i === 0 ? "true" : "false");
  btn.addEventListener("click", () => loadPart(part));
  list.appendChild(btn);
});

loadPart(PARTS[0]);

function frame() {
  if (!playing) return;
  const delta = clock.getDelta();
  if (document.documentElement.dataset.motion === "off") {
    controls.autoRotate = false;
    controls.enableDamping = false;
  } else if (!reduce) {
    controls.autoRotate = true;
    controls.enableDamping = true;
  }
  controls.update(delta);
  renderer.render(scene, camera);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

const ro = new ResizeObserver(() => {
  const w = host.clientWidth;
  const h = Math.max(320, w * 0.62);
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
  }, { threshold: 0.05 });
  io.observe(host);
}

document.getElementById("motion-toggle")?.addEventListener("click", () => {
  const off = document.documentElement.dataset.motion === "off";
  controls.autoRotate = !off;
});
