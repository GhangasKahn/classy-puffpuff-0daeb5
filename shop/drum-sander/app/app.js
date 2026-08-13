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
      { k: "Motor", v: D.meta.motorHp + " HP" },
      { k: "Surface", v: "~" + D.meta.surfaceFpm + " sfpm" },
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

  /* Viz */
  function renderViz(explode) {
    const stage = $("#vizStage");
    if (!stage) return;
    const e = explode || 0;
    const gap = e * 28;
    const parts = D.parts;
    let y = 20;
    const blocks = parts
      .map((p, i) => {
        const yy = y + i * gap;
        const h = 36;
        return `<g class="viz-part" data-id="${p.id}" style="cursor:pointer">
          <rect x="40" y="${yy}" width="280" height="${h}" rx="4" fill="${p.color}" stroke="#1a1f24" stroke-width="1.5"/>
          <text x="54" y="${yy + 23}" fill="#1a1f24" font-size="13" font-family="IBM Plex Mono, monospace">${p.label}</text>
        </g>`;
      })
      .join("");
    stage.innerHTML = `<svg viewBox="0 0 360 ${80 + parts.length * 36 + e * 28 * parts.length}" width="100%" height="100%">${blocks}</svg>`;
    $$(".viz-part", stage).forEach((g) =>
      g.addEventListener("click", () => selectPart(g.dataset.id))
    );
  }

  function selectPart(id) {
    selectedPart = id;
    const p = D.parts.find((x) => x.id === id);
    const detail = $("#partDetail");
    if (detail && p) {
      detail.innerHTML = `<strong>${p.label}</strong><p style="margin:6px 0 0;color:var(--dim);font-size:14px">${p.detail}</p><p class="hint">Group: ${p.group}</p>`;
    }
    $$(".part-item").forEach((el) =>
      el.classList.toggle("on", el.dataset.id === id)
    );
  }

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
      $("#explodeVal").textContent = Math.round(explode.value * 100) + "%";
      renderViz(+explode.value);
    });
    renderViz(0);
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

  /* Materials */
  const cuts = $("#cutList");
  if (cuts) {
    cuts.innerHTML = D.cutList
      .map(
        (r) =>
          `<tr><td>${r.qty}</td><td>${r.size}</td><td>${r.stock}</td><td>${r.use}</td></tr>`
      )
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

  /* Gallery */
  const gal = $("#gallery");
  if (gal) {
    gal.innerHTML = D.gallery
      .map(
        (g) =>
          `<a class="gal-card" href="${g.src}" target="_blank" rel="noopener"><img src="${g.src}" alt="${g.title}"/><span>${g.title}</span></a>`
      )
      .join("");
  }

  /* Files */
  const files = $("#filesList");
  if (files) {
    files.innerHTML = D.downloads
      .map(
        (d) =>
          `<a class="file-row" href="${d.href}"><strong>${d.label}</strong><span>${d.note}</span></a>`
      )
      .join("");
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
