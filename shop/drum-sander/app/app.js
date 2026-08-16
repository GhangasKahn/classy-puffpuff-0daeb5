/* WALTER DS-16 Build App */
(function () {
  const D = window.WALTER_DATA;
  const KEY = "walter_ds16_progress_v1";

  function $(sel, el) {
    return (el || document).querySelector(sel);
  }
  function $$(sel, el) {
    return [...(el || document).querySelectorAll(sel)];
  }

  function loadProgress() {
    try {
      return JSON.parse(localStorage.getItem(KEY) || "{}");
    } catch {
      return {};
    }
  }
  function saveProgress(p) {
    localStorage.setItem(KEY, JSON.stringify(p));
  }

  let progress = loadProgress();
  let phaseFilter = "all";
  let selectedPart = null;

  function pctDone() {
    const n = D.assembly.length;
    const done = D.assembly.filter((a) => progress[a.id]).length;
    return n ? Math.round((100 * done) / n) : 0;
  }

  function updateProgressUI() {
    const p = pctDone();
    $$(".progress-pill").forEach((el) => (el.textContent = p + "% built"));
    const bar = $("#progressBar");
    if (bar) bar.style.width = p + "%";
  }

  /* Tabs */
  function showTab(id) {
    $$(".tab").forEach((t) => t.classList.toggle("on", t.dataset.tab === id));
    $$(".panel").forEach((p) => p.classList.toggle("on", p.dataset.panel === id));
    history.replaceState(null, "", "#" + id);
  }
  $$(".tab").forEach((t) =>
    t.addEventListener("click", () => showTab(t.dataset.tab))
  );
  $$("[data-go]").forEach((a) =>
    a.addEventListener("click", (e) => {
      e.preventDefault();
      showTab(a.dataset.go);
    })
  );

  /* Overview stats */
  const stats = $("#overviewStats");
  if (stats) {
    const items = [
      { k: "Capacity", v: D.meta.capacity + "″" },
      { k: "Drum", v: "⌀" + D.meta.drumOd + "″ @ " + D.meta.drumRpm + " RPM" },
      { k: "A/B spec", v: "±" + D.meta.parallelTol + "″" },
      { k: "Rev", v: D.meta.revision },
    ];
    stats.innerHTML = items
      .map(
        (i) =>
          `<div class="stat"><span class="k">${i.k}</span><strong>${i.v}</strong></div>`
      )
      .join("");
  }

  const modList = $("#modernList");
  if (modList) {
    modList.innerHTML = D.modernizations.map((m) => `<li>${m}</li>`).join("");
  }

  const safety = $("#safetyList");
  if (safety) {
    safety.innerHTML = D.safety.map((m) => `<li>${m}</li>`).join("");
  }

  /* Viz — 3D viewer is created by model3d.js; keep list + highlight in sync */
  function selectPart(id, from3d) {
    selectedPart = id;
    const p = D.parts.find((x) => x.id === id);
    const detail = $("#partDetail");
    if (detail && p) {
      detail.innerHTML = `<strong>${p.label}</strong><p style="margin:6px 0 0;color:var(--dim);font-size:14px">${p.detail}</p><p class="hint">Group: ${p.group}</p>`;
    }
    $$(".part-item").forEach((el) =>
      el.classList.toggle("on", el.dataset.id === id)
    );
    if (!from3d && window.__ds16 && id) window.__ds16.highlight(id);
  }
  window.selectWalterPart = (id) => selectPart(id, true);

  const partList = $("#partList");
  if (partList) {
    partList.innerHTML = D.parts
      .map(
        (p) =>
          `<button type="button" class="part-item" data-id="${p.id}"><i style="background:${p.color}"></i><span>${p.label}</span></button>`
      )
      .join("");
    $$(".part-item", partList).forEach((b) =>
      b.addEventListener("click", () => selectPart(b.dataset.id))
    );
  }

  const explode = $("#explodeRange");
  if (explode) {
    explode.addEventListener("input", () => {
      const n = $("#explodeVal");
      if (n) n.textContent = Math.round(explode.value * 100) + "%";
    });
  }

  /* Assembly */
  function renderAssembly() {
    const box = $("#assemblyList");
    if (!box) return;
    const items = D.assembly.filter(
      (a) => phaseFilter === "all" || a.phase === phaseFilter
    );
    box.innerHTML = items
      .map((a) => {
        const on = !!progress[a.id];
        return `<label class="check-row ${on ? "done" : ""}">
          <input type="checkbox" data-id="${a.id}" ${on ? "checked" : ""}/>
          <div><strong>${a.title}</strong><p>${a.body}</p><span class="chip-mini">${a.phase}</span></div>
        </label>`;
      })
      .join("");
    $$("input[type=checkbox]", box).forEach((inp) =>
      inp.addEventListener("change", () => {
        progress[inp.dataset.id] = inp.checked;
        saveProgress(progress);
        updateProgressUI();
        renderAssembly();
      })
    );
  }

  $$(".chip[data-phase]").forEach((c) =>
    c.addEventListener("click", () => {
      phaseFilter = c.dataset.phase;
      $$(".chip[data-phase]").forEach((x) =>
        x.classList.toggle("on", x === c)
      );
      renderAssembly();
    })
  );
  renderAssembly();

  /* Calibration */
  const CALKEY = "walter_ds16_cal_v1";
  function loadCal() {
    try {
      return JSON.parse(localStorage.getItem(CALKEY) || "{}");
    } catch {
      return {};
    }
  }
  function saveCal(p) {
    localStorage.setItem(CALKEY, JSON.stringify(p));
  }
  let cal = loadCal();

  const qbox = $("#qualityList");
  if (qbox) {
    qbox.innerHTML = (D.quality || [])
      .map((r) => `<tr><td>${r.check}</td><td>${r.spec}</td><td>${r.tool}</td></tr>`)
      .join("");
  }
  const pbox = $("#passList");
  if (pbox) {
    pbox.innerHTML = (D.passes || [])
      .map(
        (p) =>
          `<div class="stat"><span class="k">${p.grit} grit</span><strong>${p.depth}</strong><p class="hint" style="margin:8px 0 0">${p.use}</p></div>`
      )
      .join("");
  }
  function renderCal() {
    const box = $("#calList");
    if (!box) return;
    box.innerHTML = (D.calibration || [])
      .map((a) => {
        const on = !!cal[a.id];
        return `<label class="check-row ${on ? "done" : ""}">
          <input type="checkbox" data-cid="${a.id}" ${on ? "checked" : ""}/>
          <div><strong>${a.title}</strong><p>${a.body}</p></div>
        </label>`;
      })
      .join("");
    $$("input[data-cid]", box).forEach((inp) =>
      inp.addEventListener("change", () => {
        cal[inp.dataset.cid] = inp.checked;
        saveCal(cal);
        renderCal();
      })
    );
  }
  renderCal();

  /* Materials */
  const cuts = $("#cutList");
  if (cuts) {
    cuts.innerHTML = D.cutList
      .map(
        (r) =>
          `<tr><td>${r.partId ? `<b>${r.partId}</b> ` : ""}${r.qty}</td><td>${r.size}${r.sizeMm ? `<div class="hint">${r.sizeMm}</div>` : ""}</td><td>${r.stock}</td><td>${r.use}</td></tr>`
      )
      .join("");
  }
  const lumber = $("#lumberList");
  if (lumber) {
    lumber.innerHTML = (D.lumberyard || [])
      .map((r) => `<tr><td>${r.where}</td><td>${r.item}</td><td>${r.qty}</td><td>${r.use}</td></tr>`)
      .join("");
  }
  const fast = $("#fastenerList");
  if (fast) {
    fast.innerHTML = (D.fasteners || [])
      .map((r) => `<tr><td>${r.qty}</td><td>${r.item}</td><td>${r.use}</td></tr>`)
      .join("");
  }
  const hw = $("#hardwareList");
  if (hw) {
    hw.innerHTML = D.hardware
      .map((r) => `<tr><td>${r.qty}</td><td>${r.item}</td></tr>`)
      .join("");
  }
  const tools = $("#toolsList");
  if (tools) {
    tools.innerHTML = D.tools.map((t) => `<li>${t}</li>`).join("");
  }

  /* Gallery + phone save */
  const PACK_ZIP = "../pack/WALTER-DS16-RevC.zip";
  const PACK_NAME = "WALTER-DS16-RevC.zip";

  async function saveToPhone(url, filename, mime) {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error("fetch");
      const blob = await res.blob();
      const type = mime || blob.type || "application/octet-stream";
      const file = new File([blob], filename, { type });
      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        await navigator.share({ files: [file], title: filename, text: "WALTER DS-16" });
        return "shared";
      }
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(a.href), 2500);
      return "downloaded";
    } catch (err) {
      if (err && err.name === "AbortError") return "cancel";
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.rel = "noopener";
      a.click();
      return "open";
    }
  }

  function bindShare(el) {
    if (!el) return;
    el.addEventListener("click", () => saveToPhone(PACK_ZIP, PACK_NAME, "application/zip"));
  }
  bindShare($("#sharePackBtn"));
  bindShare($("#sharePackBtn2"));

  const gal = $("#gallery");
  if (gal) {
    gal.innerHTML = D.gallery
      .map((g) => {
        const name = (g.src.split("/").pop() || "sheet.svg");
        return `<div class="gal-card">
          <a href="${g.src}" target="_blank" rel="noopener"><img src="${g.src}" alt="${g.title}"/><span>${g.title}</span></a>
          <div class="gal-actions">
            <a class="btn" href="${g.src}" download="${name}">Download</a>
            <button type="button" class="btn" data-share-src="${g.src}" data-share-name="${name}">Save to Files</button>
          </div>
        </div>`;
      })
      .join("");
    $$("[data-share-src]", gal).forEach((b) =>
      b.addEventListener("click", () =>
        saveToPhone(b.dataset.shareSrc, b.dataset.shareName, "image/svg+xml")
      )
    );
  }

  /* Files */
  const files = $("#filesList");
  if (files) {
    files.innerHTML = D.downloads
      .map((d) => {
        const dl = d.download ? ` download="${d.download}"` : "";
        const share = d.share
          ? `<button type="button" class="btn" data-share-file="${d.href}" data-share-name="${d.download || ""}">Share</button>`
          : "";
        return `<div class="file-row ${d.primary ? "primary" : ""}">
          <a href="${d.href}"${dl}><strong>${d.label}</strong><span>${d.note}</span></a>
          ${share}
        </div>`;
      })
      .join("");
    $$("[data-share-file]", files).forEach((b) =>
      b.addEventListener("click", () =>
        saveToPhone(
          b.dataset.shareFile,
          b.dataset.shareName || "WALTER-DS16-RevC.zip",
          "application/zip"
        )
      )
    );
  }
  const srcs = $("#sourcesList");
  if (srcs) {
    srcs.innerHTML = D.sources
      .map(
        (s) =>
          `<li><a href="${s.href}" target="_blank" rel="noopener">${s.label}</a></li>`
      )
      .join("");
  }

  /* Reset / print */
  const reset = $("#resetProgress");
  if (reset) {
    reset.addEventListener("click", () => {
      progress = {};
      saveProgress(progress);
      updateProgressUI();
      renderAssembly();
    });
  }
  const printBtn = $("#printBtn");
  if (printBtn) printBtn.addEventListener("click", () => window.print());

  updateProgressUI();

  const hash = (location.hash || "#overview").slice(1);
  if ($$(`.tab[data-tab="${hash}"]`).length) showTab(hash);
})();
