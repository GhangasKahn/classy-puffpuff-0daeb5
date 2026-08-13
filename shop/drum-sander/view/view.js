const D = window.WALTER_DATA;
const PACK = "../pack/WALTER-DS16-RevB.zip";
const PACK_NAME = "WALTER-DS16-RevB.zip";

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];

async function saveToPhone(url, filename, mime) {
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error("fetch");
    const blob = await res.blob();
    const file = new File([blob], filename, { type: mime || blob.type || "application/octet-stream" });
    if (navigator.canShare && navigator.canShare({ files: [file] })) {
      await navigator.share({ files: [file], title: filename, text: "WALTER DS-16" });
      return;
    }
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 2500);
  } catch (err) {
    if (err && err.name === "AbortError") return;
    location.href = url;
  }
}

function showScreen(id) {
  $$(".screen").forEach((s) => s.classList.toggle("on", s.dataset.screen === id));
  $$(".nav button").forEach((b) => b.classList.toggle("on", b.dataset.go === id));
  if (id === "model" && window.__ds16) setTimeout(() => window.__ds16.resize(), 40);
}

$$(".nav button").forEach((b) => b.addEventListener("click", () => showScreen(b.dataset.go)));

const stage = $("#stage");
const detail = $("#partDetail");
const openSheet = $("#openSheet");
let currentSheet = null;
let viewer = null;

function selectPart(id, part) {
  const row = (D.parts || []).find((p) => p.id === id) || {
    label: part?.label || id,
    detail: part?.detail || "",
    sheet: null,
  };
  currentSheet = row.sheet ? "../plans/" + row.sheet : null;
  detail.innerHTML = `<strong>${row.label}</strong><p>${row.detail}</p>`;
  openSheet.hidden = !currentSheet;
  openSheet.textContent = currentSheet ? "Open " + row.sheet.replace(".svg", "").replace("_", " ") : "";
  $$(".chip").forEach((c) => c.classList.toggle("on", c.dataset.id === id));
}

function showFallback(message) {
  const wait = $("#stageWait");
  if (wait) wait.remove();
  const wrap = document.createElement("div");
  wrap.className = "stage-fallback";
  wrap.innerHTML = `<img src="../renders/iso_assembled.svg" alt="WALTER DS-16 assembled">`;
  stage.appendChild(wrap);
  detail.innerHTML = `<strong>Still viewable as a drawing</strong><p>${message} Swipe Plans for every sheet.</p>`;
}

async function bootModel() {
  try {
    const mod = await import("../app/model3d.js");
    const wait = $("#stageWait");
    if (wait) wait.remove();
    viewer = mod.createWalterModel(stage, {
      autoRotate: true,
      onSelect: selectPart,
    });
    window.__ds16 = viewer;
    const paint = () => viewer && viewer.resize();
    requestAnimationFrame(paint);
    setTimeout(paint, 80);
    setTimeout(paint, 320);
    window.addEventListener("orientationchange", () => setTimeout(paint, 200));
  } catch (err) {
    console.error("WALTER 3D failed", err);
    showFallback("The live 3D view could not start on this phone.");
  }
}

const chips = $("#chips");
chips.innerHTML = (D.parts || [])
  .map((p) => `<button type="button" class="chip" data-id="${p.id}"><i style="background:${p.color}"></i>${p.label}</button>`)
  .join("");
$$(".chip", chips).forEach((b) =>
  b.addEventListener("click", () => {
    if (!viewer) return;
    viewer.highlight(b.dataset.id);
    viewer.controls.autoRotate = false;
  })
);

const explode = $("#explode");
explode.addEventListener("input", () => {
  if (!viewer) return;
  viewer.setExplode(+explode.value);
  viewer.controls.autoRotate = false;
});
$("#assembled").onclick = () => {
  explode.value = 0;
  if (viewer) viewer.setExplode(0);
};
$("#exploded").onclick = () => {
  explode.value = 1;
  if (!viewer) return;
  viewer.setExplode(1);
  viewer.controls.autoRotate = false;
};
openSheet.addEventListener("click", () => {
  if (!currentSheet) return;
  const g = D.gallery.find((x) => currentSheet.endsWith(x.src.split("/").pop()));
  openLightbox(currentSheet, g ? g.title : "Plan");
});

bootModel();

/* Plans */
function card(g) {
  return `<button type="button" class="plan-card" data-src="${g.src}" data-title="${g.title}">
    <img src="${g.src}" alt="${g.title}"/><span>${g.title}</span>
  </button>`;
}
const plans = D.gallery.filter((g) => g.kind === "plan");
const partSheets = D.gallery.filter((g) => g.kind === "part");
const assemblySheets = D.gallery.filter((g) => g.kind === "assembly" || g.kind === "hardware");
const renders = D.gallery.filter((g) => g.kind === "render");
const partRail = $("#partRail");
if (partRail) partRail.innerHTML = partSheets.map(card).join("");
const assemblyRail = $("#assemblyRail");
if (assemblyRail) assemblyRail.innerHTML = assemblySheets.map(card).join("");
$("#planRail").innerHTML = plans.map(card).join("");
$("#renderGrid").innerHTML = renders.map(card).join("");

const lb = $("#lightbox");
const lbImg = $("#lbImg");
const lbTitle = $("#lbTitle");
let lbList = D.gallery;
let lbIndex = 0;

function openLightbox(src, title) {
  lbList = D.gallery;
  lbIndex = Math.max(0, lbList.findIndex((g) => g.src === src));
  showLb();
  showScreen("plans");
}
function showLb() {
  const g = lbList[lbIndex];
  if (!g) return;
  lb.hidden = false;
  lb.classList.add("on");
  lbImg.src = g.src;
  lbImg.alt = g.title;
  lbTitle.textContent = g.title;
}
function closeLb() {
  lb.classList.remove("on");
  lb.hidden = true;
}
$$(".plan-card").forEach((c) =>
  c.addEventListener("click", () => openLightbox(c.dataset.src, c.dataset.title))
);
$("#lbClose").onclick = closeLb;
$("#lbPrev").onclick = () => {
  lbIndex = (lbIndex + lbList.length - 1) % lbList.length;
  showLb();
};
$("#lbNext").onclick = () => {
  lbIndex = (lbIndex + 1) % lbList.length;
  showLb();
};
$("#lbSave").onclick = () => {
  const g = lbList[lbIndex];
  if (g) saveToPhone(g.src, g.src.split("/").pop(), "image/svg+xml");
};

/* Guide */
const phasePart = {
  frame: "sides",
  drum: "drum",
  drive: "motor",
  table: "table",
  hood: "hood",
  wrap: "drum",
  tune: "elev",
};
$("#steps").innerHTML = D.assembly
  .map(
    (a) =>
      `<button type="button" class="step" data-phase="${a.phase}"><b>${a.title}</b><p>${a.body}</p></button>`
  )
  .join("");
$$(".step").forEach((s) =>
  s.addEventListener("click", () => {
    const id = phasePart[s.dataset.phase];
    showScreen("model");
    if (!viewer) return;
    if (id) viewer.highlight(id);
    viewer.controls.autoRotate = false;
  })
);

/* Save / install */
$("#saveBtn").onclick = () => saveToPhone(PACK, PACK_NAME, "application/zip");

let deferredPrompt = null;
const hint = $("#installHint");
const installBtn = $("#installBtn");
const standalone = window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone;
if (!standalone) hint.classList.add("on");
window.addEventListener("beforeinstallprompt", (e) => {
  e.preventDefault();
  deferredPrompt = e;
  hint.classList.add("on");
});
installBtn.onclick = async () => {
  if (deferredPrompt) {
    deferredPrompt.prompt();
    deferredPrompt = null;
    return;
  }
  hint.classList.add("on");
  hint.querySelector("span").textContent =
    "iPhone: tap Share, then Add to Home Screen. Android: browser menu → Install app.";
};
$("#dismissInstall").onclick = () => hint.classList.remove("on");
