/* DS-18 Build App — hash tabs, checklists, Three.js viz */
import { mountScene, drawFallbackSvg } from "./scene.js";

const D = window.DS_DATA;
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
/* Hash routes: #overview #viz #assembly #cutlist #shop #plans #files */
const TABS = ["overview", "viz", "assembly", "cutlist", "shop", "plans", "files"];

const store = {
  get(k, fallback) {
    try {
      const v = localStorage.getItem("ds18_" + k);
      return v == null ? fallback : JSON.parse(v);
    } catch {
      return fallback;
    }
  },
  set(k, v) {
    try {
      localStorage.setItem("ds18_" + k, JSON.stringify(v));
    } catch {}
  },
};

const state = {
  tab: "overview",
  explode: store.get("explode", 0),
  selected: store.get("selected", null),
  done: store.get("done", {}),
  bought: store.get("bought", {}),
  cut: store.get("cut", {}),
  phase: store.get("phase", "all"),
  spin: store.get("spin", true),
  table: store.get("table", 0.35),
};

let sceneApi = null;
let vizMode = "none";

function toast(msg) {
  const t = $("#toast");
  if (!t) return;
  t.textContent = msg;
  t.classList.add("on");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => t.classList.remove("on"), 2200);
}

function setTab(id, { push = true } = {}) {
  if (!TABS.includes(id)) id = "overview";
  state.tab = id;
  $$(".panel").forEach((p) => p.classList.toggle("on", p.dataset.panel === id));
  $$(".tab, .mobile-nav button").forEach((b) => b.classList.toggle("on", b.dataset.tab === id));
  if (push) {
    const hash = "#" + id;
    if (location.hash !== hash) history.replaceState(null, "", hash);
  }
  window.scrollTo({ top: 0, behavior: "smooth" });
  if (id === "viz") ensureViz();
}

function progressPct() {
  const n = D.assembly.length;
  const d = Object.values(state.done).filter(Boolean).length;
  return n ? Math.round((100 * d) / n) : 0;
}

function refreshProgress() {
  const pct = progressPct();
  $$(".progress-pill").forEach((el) => (el.textContent = pct + "% assembled"));
  const bar = $("#progressBar");
  if (bar) bar.style.width = pct + "%";
}

function renderPartList() {
  const box = $("#partList");
  if (!box) return;
  box.innerHTML = D.parts
    .map(
      (p) => `<button type="button" class="part${state.selected === p.id ? " on" : ""}" data-part="${p.id}">
        <strong><i class="swatch" style="background:${p.color}"></i>${p.name}</strong>
        <small>${p.note}</small>
      </button>`
    )
    .join("");
  box.querySelectorAll(".part").forEach((b) =>
    b.addEventListener("click", () => selectPart(b.dataset.part))
  );
}

function selectPart(id) {
  state.selected = id;
  store.set("selected", id);
  renderPartList();
  const p = D.parts.find((x) => x.id === id);
  const detail = $("#partDetail");
  if (detail && p) {
    detail.innerHTML = `<strong>${p.name}</strong>
      <p style="margin:6px 0 0;color:var(--dim);font-size:14px">${p.note}</p>
      <p class="hint mono">${p.id}</p>`;
  }
  if (sceneApi) sceneApi.selectPart(id);
  else if (vizMode === "svg") drawSvg();
}

function renderAssembly() {
  const box = $("#assemblyList");
  if (!box) return;
  $$(".phase-rail .chip").forEach((c) => c.classList.toggle("on", c.dataset.phase === state.phase));
  const rows = D.assembly.filter((s) => state.phase === "all" || s.phase === state.phase);
  box.innerHTML = rows
    .map((s, i) => {
      const done = !!state.done[s.id];
      return `<article class="step${done ? " done" : ""}" data-id="${s.id}">
        <div class="num">${String(D.assembly.indexOf(s) + 1).padStart(2, "0")}</div>
        <div>
          <h3>${s.title}</h3>
          <p>${s.body}</p>
        </div>
        <button type="button" class="check" aria-label="Mark done" data-id="${s.id}"></button>
      </article>`;
    })
    .join("");
  box.querySelectorAll(".check").forEach((b) =>
    b.addEventListener("click", () => {
      state.done[b.dataset.id] = !state.done[b.dataset.id];
      store.set("done", state.done);
      renderAssembly();
      refreshProgress();
    })
  );
}

function money(n) {
  return "$" + n.toFixed(0);
}

function renderShop() {
  const body = $("#shopBody");
  if (!body) return;
  let total = 0;
  let bought = 0;
  body.innerHTML = D.shopping
    .map((s) => {
      total += s.est;
      const on = !!state.bought[s.id];
      if (on) bought += s.est;
      return `<tr class="${on ? "bought" : ""}">
        <td><input class="buy-check" type="checkbox" data-id="${s.id}" ${on ? "checked" : ""}/></td>
        <td class="mono">${s.qty}</td>
        <td>${s.item}</td>
        <td>${s.use}</td>
        <td class="mono">${money(s.est)}</td>
      </tr>`;
    })
    .join("");
  $("#shopTotal").textContent = money(total);
  $("#shopBought").textContent = money(bought);
  body.querySelectorAll(".buy-check").forEach((c) =>
    c.addEventListener("change", () => {
      state.bought[c.dataset.id] = c.checked;
      store.set("bought", state.bought);
      renderShop();
    })
  );
}

function renderCutlist() {
  const body = $("#cutBody");
  if (!body) return;
  const n = D.cutlist.reduce((a, r) => a + r.qty, 0);
  let done = 0;
  body.innerHTML = D.cutlist
    .map((r) => {
      const on = !!state.cut[r.id];
      if (on) done += r.qty;
      return `<tr class="${on ? "bought" : ""}">
        <td><input class="buy-check" type="checkbox" data-id="${r.id}" ${on ? "checked" : ""}/></td>
        <td class="mono">${r.qty}</td>
        <td>${r.material}</td>
        <td class="mono">${r.size}</td>
        <td>${r.part}</td>
        <td class="mono">${r.sheet}</td>
      </tr>`;
    })
    .join("");
  const tot = $("#cutTotal");
  if (tot) tot.textContent = `${done} / ${n} pcs`;
  body.querySelectorAll(".buy-check").forEach((c) =>
    c.addEventListener("change", () => {
      state.cut[c.dataset.id] = c.checked;
      store.set("cut", state.cut);
      renderCutlist();
    })
  );
}

function renderPlans() {
  const g = $("#plansGrid");
  if (!g) return;
  g.innerHTML = D.plans
    .map(
      (p) => `<a class="shot" href="${p.href}" data-lightbox="${p.href}">
        <img src="${p.href}" alt="${p.id} ${p.title}"/>
        <figcaption>${p.id} · ${p.title}</figcaption>
      </a>`
    )
    .join("");
  g.querySelectorAll("[data-lightbox]").forEach((a) =>
    a.addEventListener("click", (ev) => {
      ev.preventDefault();
      openLightbox(a.getAttribute("data-lightbox"));
    })
  );
}

function renderFiles() {
  const g = $("#downloadGrid");
  if (!g) return;
  g.innerHTML = D.files
    .map((f) => `<a class="dl" href="${f.href}" download><b>${f.label}</b><span>${f.note}</span></a>`)
    .join("");
}

function openLightbox(href) {
  const box = $("#lightbox");
  const body = $("#lightboxBody");
  body.innerHTML = `<object data="${href}" type="image/svg+xml" style="width:min(1100px,96vw);height:86vh"></object>`;
  box.classList.add("on");
}

function drawSvg() {
  const stage = $("#vizStage");
  if (!stage) return;
  drawFallbackSvg(stage, {
    explode: state.explode,
    selected: state.selected,
    onPick: selectPart,
  });
}

async function ensureViz() {
  const stage = $("#vizStage");
  if (!stage) return;
  if (vizMode === "three" && sceneApi) {
    sceneApi.resize();
    return;
  }
  if (vizMode === "svg") {
    drawSvg();
    return;
  }
  stage.innerHTML = `<div class="viz-msg">Loading 3D model…</div>`;
  try {
    sceneApi = await mountScene(stage, {
      onPick: selectPart,
      onReady: () => toast("3D model ready — drag to orbit"),
    });
    sceneApi.setExplode(state.explode);
    sceneApi.setTableLift(state.table);
    sceneApi.setSpin(state.spin);
    if (state.selected) sceneApi.selectPart(state.selected);
    vizMode = "three";
  } catch (err) {
    console.warn("Three.js failed, using SVG fallback", err);
    vizMode = "svg";
    drawSvg();
    toast("3D unavailable — isometric fallback");
  }
}

function syncControls() {
  const ex = $("#explodeRange");
  const ev = $("#explodeVal");
  if (ex) {
    ex.value = state.explode;
    if (ev) ev.textContent = Math.round(state.explode * 100) + "%";
  }
  const tb = $("#tableRange");
  const tv = $("#tableVal");
  if (tb) {
    tb.value = state.table;
    if (tv) tv.textContent = (state.table * D.meta.tableTravel).toFixed(2) + "″";
  }
  const sp = $("#spinToggle");
  if (sp) sp.classList.toggle("primary", state.spin);
}

function init() {
  renderPartList();
  renderAssembly();
  renderCutlist();
  renderShop();
  renderPlans();
  renderFiles();
  refreshProgress();
  syncControls();

  $$(".tab, .mobile-nav button").forEach((b) =>
    b.addEventListener("click", () => setTab(b.dataset.tab))
  );
  $$("[data-go]").forEach((b) =>
    b.addEventListener("click", (e) => {
      const id = b.getAttribute("data-go");
      if (id) {
        e.preventDefault();
        setTab(id);
      }
    })
  );

  window.addEventListener("hashchange", () => {
    const id = location.hash.replace(/^#/, "") || "overview";
    setTab(id, { push: false });
  });

  const fromHash = location.hash.replace(/^#/, "");
  setTab(TABS.includes(fromHash) ? fromHash : "overview", { push: false });

  $("#explodeRange")?.addEventListener("input", (e) => {
    state.explode = parseFloat(e.target.value);
    store.set("explode", state.explode);
    $("#explodeVal").textContent = Math.round(state.explode * 100) + "%";
    if (sceneApi) sceneApi.setExplode(state.explode);
    else if (vizMode === "svg") drawSvg();
  });
  $("#tableRange")?.addEventListener("input", (e) => {
    state.table = parseFloat(e.target.value);
    store.set("table", state.table);
    $("#tableVal").textContent = (state.table * D.meta.tableTravel).toFixed(2) + "″";
    if (sceneApi) sceneApi.setTableLift(state.table);
  });
  $("#spinToggle")?.addEventListener("click", () => {
    state.spin = !state.spin;
    store.set("spin", state.spin);
    syncControls();
    if (sceneApi) sceneApi.setSpin(state.spin);
    toast(state.spin ? "Drum spinning" : "Drum paused");
  });
  $("#camReset")?.addEventListener("click", () => sceneApi?.resetCamera());
  $("#breakdownBtn")?.addEventListener("click", () => {
    $("#explodeRange").value = 0.7;
    $("#explodeRange").dispatchEvent(new Event("input"));
  });
  $("#assembledBtn")?.addEventListener("click", () => {
    $("#explodeRange").value = 0;
    $("#explodeRange").dispatchEvent(new Event("input"));
  });

  $$(".phase-rail .chip").forEach((c) =>
    c.addEventListener("click", () => {
      state.phase = c.dataset.phase;
      store.set("phase", state.phase);
      renderAssembly();
    })
  );

  $("#resetProgress")?.addEventListener("click", () => {
    if (confirm("Reset assembly checklist?")) {
      state.done = {};
      store.set("done", state.done);
      renderAssembly();
      refreshProgress();
      toast("Progress reset");
    }
  });
  $("#resetShop")?.addEventListener("click", () => {
    state.bought = {};
    store.set("bought", state.bought);
    renderShop();
    toast("Shopping list reset");
  });
  $("#resetCut")?.addEventListener("click", () => {
    state.cut = {};
    store.set("cut", state.cut);
    renderCutlist();
    toast("Cut list reset");
  });
  $("#printBtn")?.addEventListener("click", () => window.print());
  $("#exportBtn")?.addEventListener("click", () => {
    const payload = {
      machine: D.meta.name,
      assemblyDone: state.done,
      shoppingBought: state.bought,
      cutDone: state.cut,
      progressPct: progressPct(),
    };
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" }));
    a.download = "ds18-build-progress.json";
    a.click();
    toast("JSON exported");
  });
  $("#lightboxClose")?.addEventListener("click", () => $("#lightbox").classList.remove("on"));
  $("#lightbox")?.addEventListener("click", (e) => {
    if (e.target.id === "lightbox") $("#lightbox").classList.remove("on");
  });
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
