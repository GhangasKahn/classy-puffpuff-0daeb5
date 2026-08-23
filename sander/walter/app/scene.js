/* WALTER immersive WebGL theater — kernel solids, LEGO steps, shop lighting. */
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

const ACC = 0xb4532a;
const STEPS = 22;

function k2t(x, y, z) {
  return new THREE.Vector3(x, z, y);
}

function birchCanvas() {
  const c = document.createElement("canvas");
  c.width = 256;
  c.height = 256;
  const g = c.getContext("2d");
  g.fillStyle = "#c4a574";
  g.fillRect(0, 0, 256, 256);
  for (let i = 0; i < 48; i++) {
    g.strokeStyle = `rgba(70,48,28,${0.035 + Math.random() * 0.09})`;
    g.lineWidth = 1 + Math.random() * 2;
    const x = Math.random() * 256;
    g.beginPath();
    g.moveTo(x, 0);
    g.bezierCurveTo(x + 14, 90, x - 18, 170, x + 6, 256);
    g.stroke();
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.anisotropy = 8;
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

function matFor(group, color, maps) {
  const hex = new THREE.Color(color);
  if (group === "steel" || group === "motor") {
    return new THREE.MeshStandardMaterial({
      color: hex,
      metalness: group === "motor" ? 0.55 : 0.82,
      roughness: group === "motor" ? 0.45 : 0.28,
      envMapIntensity: 1.1,
    });
  }
  if (group === "conveyor") {
    return new THREE.MeshStandardMaterial({ color: hex, metalness: 0.05, roughness: 0.92 });
  }
  if (group === "drum" && color.toLowerCase() === "#b4532a") {
    return new THREE.MeshStandardMaterial({ color: hex, metalness: 0.08, roughness: 0.88 });
  }
  const birch = group === "frame" || group === "table" || group === "guard" || group === "stand";
  return new THREE.MeshStandardMaterial({
    color: hex,
    map: birch ? maps.birch : null,
    metalness: 0.04,
    roughness: birch ? 0.72 : 0.55,
    envMapIntensity: 0.55,
  });
}

function makeMesh(s, maps) {
  let geom;
  let pos;
  let rot = new THREE.Euler();
  if (s.kind === "box") {
    geom = new THREE.BoxGeometry(s.dx, s.dz, s.dy);
    pos = k2t(s.x + s.dx / 2, s.y + s.dy / 2, s.z + s.dz / 2);
  } else {
    const r = s.d / 2;
    geom = new THREE.CylinderGeometry(r, r, s.h, 28, 1);
    if (s.axis === "x") {
      rot.z = -Math.PI / 2;
      pos = k2t(s.x + s.h / 2, s.y, s.z);
    } else if (s.axis === "y") {
      rot.x = Math.PI / 2;
      pos = k2t(s.x, s.y + s.h / 2, s.z);
    } else {
      pos = k2t(s.x, s.y, s.z + s.h / 2);
    }
  }
  const mesh = new THREE.Mesh(geom, matFor(s.group, s.color, maps));
  mesh.position.copy(pos);
  mesh.rotation.copy(rot);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  mesh.userData = {
    name: s.name,
    group: s.group,
    appear: s.appear,
    rest: pos.clone(),
    explode: s.explode || [0, 0, 0],
    color: s.color,
  };
  return mesh;
}

const CAMERAS = {
  iso: { pos: [42, 28, -22], target: [11, 9, 16] },
  infeed: { pos: [11, 11, -34], target: [11, 9, 12] },
  drive: { pos: [48, 16, 18], target: [12, 10, 18] },
  top: { pos: [11, 52, 18], target: [11, 6, 18] },
  first: { pos: [8, 7, -18], target: [11, 10, 16] },
};

function createTheater(stage, opts = {}) {
  const data = window.WALTER_SOLIDS;
  if (!data || !data.solids) throw new Error("WALTER_SOLIDS missing");

  const state = {
    explode: opts.explode || 0,
    step: opts.step || 22,
    cutaway: false,
    stand: false,
    spin: false,
    playing: false,
    selected: null,
    mode: "inspect",
    running: false,
  };

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.12;
  stage.innerHTML = "";
  stage.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x14110e);
  scene.fog = new THREE.Fog(0x14110e, 55, 140);

  const camera = new THREE.PerspectiveCamera(42, 1, 0.2, 400);
  camera.position.set(42, 28, -22);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.06;
  controls.maxPolarAngle = Math.PI * 0.49;
  controls.minDistance = 12;
  controls.maxDistance = 110;
  controls.target.set(11, 9, 16);

  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

  const hemi = new THREE.HemisphereLight(0xf4efe6, 0x3a2418, 0.55);
  scene.add(hemi);
  const key = new THREE.DirectionalLight(0xfff1dc, 1.35);
  key.position.set(-24, 42, -18);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  key.shadow.camera.near = 4;
  key.shadow.camera.far = 120;
  key.shadow.camera.left = -40;
  key.shadow.camera.right = 40;
  key.shadow.camera.top = 40;
  key.shadow.camera.bottom = -40;
  scene.add(key);
  const rim = new THREE.DirectionalLight(0xd47248, 0.45);
  rim.position.set(30, 18, 24);
  scene.add(rim);
  const fill = new THREE.PointLight(0xc4a574, 0.35, 80, 2);
  fill.position.set(11, 22, 8);
  scene.add(fill);

  const floor = new THREE.Mesh(
    new THREE.CircleGeometry(80, 64),
    new THREE.MeshStandardMaterial({ color: 0x1c1914, roughness: 0.95, metalness: 0.02 })
  );
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -1.55;
  floor.receiveShadow = true;
  scene.add(floor);
  const grid = new THREE.GridHelper(80, 40, 0x3a3228, 0x2a231c);
  grid.position.y = -1.54;
  scene.add(grid);

  const maps = { birch: birchCanvas() };
  const root = new THREE.Group();
  scene.add(root);

  const meshes = [];
  for (const s of data.solids) {
    const mesh = makeMesh(s, maps);
    mesh.userData.baseQuat = mesh.quaternion.clone();
    root.add(mesh);
    meshes.push(mesh);
  }
  const shaft = data.solids.find((s) => s.name === "shaft");
  const drumCenter = shaft
    ? k2t(shaft.x + shaft.h / 2, shaft.y, shaft.z)
    : new THREE.Vector3(11, 13.5, 18);
  const drumAxis = new THREE.Vector3(1, 0, 0);
  let spinAngle = 0;

  const ray = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  const clock = new THREE.Clock();
  let playAcc = 0;
  let camTween = null;

  function applyVisibility() {
    const step = state.step;
    const build = state.mode === "build";
    for (const m of meshes) {
      const u = m.userData;
      const standPart = u.group === "stand";
      const cut = state.cutaway && (u.name === "wall_drive" || u.group === "guard" || u.name === "hood_drive");
      let vis = !cut;
      if (standPart) vis = vis && state.stand;
      if (build && u.appear > 0 && u.appear > step) vis = false;
      m.visible = vis;
      const mat = m.material;
      mat.transparent = true;
      const selected = state.selected && (state.selected === u.name || state.selected === u.group);
      if (build && u.appear === step) {
        mat.opacity = 1;
        mat.emissive = new THREE.Color(ACC);
        mat.emissiveIntensity = 0.28;
      } else if (build && u.appear > 0 && u.appear < step) {
        mat.opacity = 0.42;
        mat.emissive = new THREE.Color(0x000000);
        mat.emissiveIntensity = 0;
      } else if (selected) {
        mat.opacity = 1;
        mat.emissive = new THREE.Color(ACC);
        mat.emissiveIntensity = 0.22;
      } else if (state.selected && !selected) {
        mat.opacity = 0.18;
        mat.emissive = new THREE.Color(0x000000);
        mat.emissiveIntensity = 0;
      } else {
        mat.opacity = 1;
        mat.emissive = new THREE.Color(0x000000);
        mat.emissiveIntensity = 0;
      }
    }
  }

  function applyPose() {
    const e = state.explode;
    const q = new THREE.Quaternion().setFromAxisAngle(drumAxis, spinAngle);
    for (const m of meshes) {
      const [ex, ey, ez] = m.userData.explode;
      const p = m.userData.rest.clone().add(k2t(ex * e, ey * e, ez * e));
      const spinning = state.spin && (m.userData.group === "drum" || m.userData.name.startsWith("bell_"));
      if (spinning) {
        p.sub(drumCenter).applyQuaternion(q).add(drumCenter);
        m.quaternion.copy(m.userData.baseQuat).premultiply(q);
      } else {
        m.quaternion.copy(m.userData.baseQuat);
      }
      m.position.copy(p);
    }
  }

  function emit() {
    stage.dispatchEvent(
      new CustomEvent("walter-scene", {
        bubbles: true,
        detail: {
          selected: state.selected,
          step: state.step,
          explode: state.explode,
          mode: state.mode,
          playing: state.playing,
        },
      })
    );
  }

  function setCamera(name, instant) {
    const c = CAMERAS[name] || CAMERAS.iso;
    const toPos = new THREE.Vector3(...c.pos);
    const toTgt = new THREE.Vector3(...c.target);
    if (instant) {
      camera.position.copy(toPos);
      controls.target.copy(toTgt);
      return;
    }
    const fromPos = camera.position.clone();
    const fromTgt = controls.target.clone();
    camTween = { t: 0, fromPos, fromTgt, toPos, toTgt };
  }

  function resize() {
    const w = stage.clientWidth || 800;
    const h = stage.clientHeight || 520;
    camera.aspect = w / Math.max(h, 1);
    camera.updateProjectionMatrix();
    renderer.setSize(w, h, false);
  }

  function pick(ev) {
    const rect = renderer.domElement.getBoundingClientRect();
    pointer.x = ((ev.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((ev.clientY - rect.top) / rect.height) * 2 + 1;
    ray.setFromCamera(pointer, camera);
    const hits = ray.intersectObjects(meshes.filter((m) => m.visible), false);
    if (!hits.length) {
      state.selected = null;
      applyVisibility();
      emit();
      return;
    }
    const u = hits[0].object.userData;
    state.selected = state.selected === u.name ? null : u.name;
    applyVisibility();
    emit();
  }

  renderer.domElement.addEventListener("pointerdown", (ev) => {
    if (ev.button === 0) pick(ev);
  });

  new ResizeObserver(resize).observe(stage);

  function tick() {
    if (!state.running) return;
    requestAnimationFrame(tick);
    const dt = clock.getDelta();
    if (state.spin) {
      spinAngle += dt * 1.15;
      applyPose();
    }
    if (state.playing) {
      playAcc += dt;
      if (playAcc > 1.15) {
        playAcc = 0;
        if (state.step >= STEPS) {
          state.playing = false;
          state.mode = "inspect";
        } else {
          state.step += 1;
          applyVisibility();
          emit();
        }
      }
    }
    if (camTween) {
      camTween.t = Math.min(1, camTween.t + dt * 1.4);
      const k = 1 - Math.pow(1 - camTween.t, 3);
      camera.position.lerpVectors(camTween.fromPos, camTween.toPos, k);
      controls.target.lerpVectors(camTween.fromTgt, camTween.toTgt, k);
      if (camTween.t >= 1) camTween = null;
    }
    controls.update();
    renderer.render(scene, camera);
  }

  const api = {
    ready: true,
    getState: () => ({ ...state }),
    setExplode(v) {
      state.explode = Math.max(0, Math.min(1, v));
      applyPose();
    },
    setStep(n) {
      state.step = Math.max(1, Math.min(STEPS, n | 0));
      applyVisibility();
      emit();
    },
    setMode(m) {
      state.mode = m === "build" ? "build" : "inspect";
      if (state.mode === "inspect") state.step = STEPS;
      applyVisibility();
      emit();
    },
    setCutaway(v) {
      state.cutaway = !!v;
      applyVisibility();
    },
    setStand(v) {
      state.stand = !!v;
      applyVisibility();
    },
    setSpin(v) {
      state.spin = !!v;
    },
    select(id) {
      state.selected = id;
      applyVisibility();
      emit();
    },
    camera: setCamera,
    play() {
      state.mode = "build";
      state.step = 1;
      state.playing = true;
      playAcc = 0;
      state.explode = 0.12;
      applyPose();
      applyVisibility();
      setCamera("iso");
      emit();
    },
    stopPlay() {
      state.playing = false;
      emit();
    },
    resize,
    start() {
      if (state.running) return;
      state.running = true;
      clock.getDelta();
      resize();
      tick();
    },
    stop() {
      state.running = false;
    },
  };

  applyPose();
  applyVisibility();
  resize();
  setCamera("iso", true);
  return api;
}

function stepMeta(n) {
  const D = window.WALTER_DATA;
  const st = D && D.assembly && D.assembly[n - 1];
  return st ? `Step ${String(n).padStart(2, "0")} · ${st.title}` : `Step ${n} / ${STEPS}`;
}

function bindHud(api) {
  const $ = (id) => document.getElementById(id);
  const exp = $("explodeRange");
  const expVal = $("explodeVal");
  const step = $("stepRange");
  const stepVal = $("stepVal");
  const detail = $("partDetail");

  function paintDetail(d) {
    if (!detail) return;
    const D = window.WALTER_DATA;
    const sel = d.selected;
    const part = D && D.parts && D.parts.find((p) => p.id === sel || p.group === sel);
    const solidHint = sel ? `<p class="mono" style="margin:6px 0 0;color:#8a7a68">${sel}</p>` : "";
    if (d.mode === "build") {
      const body = D && D.assembly && D.assembly[d.step - 1] && D.assembly[d.step - 1].body;
      detail.innerHTML = `<strong>${stepMeta(d.step)}</strong><p style="margin:6px 0 0;color:#c4b49a;font-size:14px">${body || "LEGO bag in copper."}</p>${solidHint}`;
      return;
    }
    if (part) {
      detail.innerHTML = `<strong>${part.label}</strong><p style="margin:6px 0 0;color:#c4b49a;font-size:14px">${part.detail}</p>${solidHint}`;
      return;
    }
    if (sel) {
      detail.innerHTML = `<strong>${sel}</strong><p style="margin:6px 0 0;color:#c4b49a;font-size:14px">Kernel solid. Finish sizes live on the P-sheets.</p>`;
      return;
    }
  }

  if (exp) {
    exp.addEventListener("input", () => {
      const v = parseFloat(exp.value);
      api.setExplode(v);
      if (expVal) expVal.textContent = Math.round(v * 100) + "%";
    });
  }
  if (step) {
    step.addEventListener("input", () => {
      const n = parseInt(step.value, 10);
      api.setMode("build");
      api.setStep(n);
      if (stepVal) stepVal.textContent = n + " / " + STEPS;
    });
  }
  const play = $("btnPlayBuild");
  if (play) play.addEventListener("click", () => api.play());
  const stop = $("btnStopBuild");
  if (stop) stop.addEventListener("click", () => api.stopPlay());
  const brk = $("btnBreakdown");
  if (brk) {
    brk.addEventListener("click", () => {
      api.setExplode(0.72);
      if (exp) exp.value = "0.72";
      if (expVal) expVal.textContent = "72%";
    });
  }
  const asm = $("btnAssembled");
  if (asm) {
    asm.addEventListener("click", () => {
      api.stopPlay();
      api.setMode("inspect");
      api.setExplode(0);
      if (exp) exp.value = "0";
      if (expVal) expVal.textContent = "0%";
      if (step) step.value = "22";
      if (stepVal) stepVal.textContent = "22 / 22";
    });
  }
  document.querySelectorAll("[data-cam]").forEach((b) =>
    b.addEventListener("click", () => api.camera(b.getAttribute("data-cam")))
  );
  const cut = $("chkCutaway");
  if (cut) cut.addEventListener("change", () => api.setCutaway(cut.checked));
  const stand = $("chkStand");
  if (stand) stand.addEventListener("change", () => api.setStand(stand.checked));
  const spin = $("chkSpin");
  if (spin) spin.addEventListener("change", () => api.setSpin(spin.checked));

  document.addEventListener("walter-scene", (ev) => {
    const d = ev.detail || {};
    if (step) step.value = String(d.step || 22);
    if (stepVal) stepVal.textContent = (d.step || 22) + " / " + STEPS;
    paintDetail(d);
  });
}

function boot() {
  const stages = [...document.querySelectorAll("[data-walter-stage]")];
  if (!stages.length) return;
  const first = stages[0];
  try {
    const theater = createTheater(first);
    window.WALTER_SCENE = theater;
    bindHud(theater);
    theater.start();
    first.dataset.ready = "1";
  } catch (err) {
    console.warn("WALTER 3D theater failed", err);
    window.WALTER_SCENE = { ready: false, error: String(err) };
  }
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
else boot();
