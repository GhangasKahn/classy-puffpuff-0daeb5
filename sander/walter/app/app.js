/* WALTER Build App — copper / birch */
(function () {
  const D = window.WALTER_DATA;
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const store = {
    get(k, fallback) {
      try {
        const v = localStorage.getItem("walter_" + k);
        return v == null ? fallback : JSON.parse(v);
      } catch {
        return fallback;
      }
    },
    set(k, v) {
      try {
        localStorage.setItem("walter_" + k, JSON.stringify(v));
      } catch {}
    },
  };

  const state = {
    tab: store.get("tab", "overview"),
    explode: store.get("explode", 0),
    selected: store.get("selected", null),
    done: store.get("done", {}),
    bought: store.get("bought", {}),
    phase: store.get("phase", "all"),
    drafts: store.get("drafts", {
      grit: "80",
      opening: 1.5,
      feed: 8,
      elec: "",
      notes: "",
    }),
  };

  function toast(msg) {
    const t = $("#toast");
    t.textContent = msg;
    t.classList.add("on");
    clearTimeout(toast._t);
    toast._t = setTimeout(() => t.classList.remove("on"), 2200);
  }

  function setTab(id) {
    state.tab = id;
    store.set("tab", id);
    $$(".panel").forEach((p) => p.classList.toggle("on", p.dataset.panel === id));
    $$(".tab, .mobile-nav button").forEach((b) =>
      b.classList.toggle("on", b.dataset.tab === id)
    );
    if (id === "viz") {
      if (window.WALTER_SCENE && window.WALTER_SCENE.ready) {
        window.WALTER_SCENE.resize();
        window.WALTER_SCENE.start();
      } else {
        drawViz();
      }
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function progressPct() {
    const n = D.assembly.length;
    const d = Object.values(state.done).filter(Boolean).length;
    return Math.round((100 * d) / n);
  }

  function refreshProgress() {
    const pct = progressPct();
    $$(".progress-pill").forEach((el) => (el.textContent = pct + "% assembled"));
    const bar = $("#progressBar");
    if (bar) bar.style.width = pct + "%";
  }

  function renderOverview() {
    const m = D.meta;
    $("#overviewStats").innerHTML = [
      ["Width", m.width + "″"],
      ["Drum", m.drum + "″ Ø"],
      ["Speed", m.rpm + " RPM"],
      ["SFM", String(m.sfm)],
      ["Envelope", m.envelope],
      ["Budget", m.budget],
    ]
      .map(([k, v]) => `<div class="card stat"><span>${k}</span><b>${v}</b></div>`)
      .join("");
  }

  function iso(x, y, z) {
    return [(x - y) * 0.866, -z + (x + y) * 0.5];
  }

  function drawViz() {
    if (window.WALTER_SCENE && window.WALTER_SCENE.ready) {
      window.WALTER_SCENE.setExplode(state.explode);
      return;
    }
    if (window.WALTER_SOLIDS && document.querySelector("[data-walter-stage]")) return;
    const stage = $("#vizStage");
    if (!stage) return;
    const e = state.explode;
    const selected = state.selected;
    const dim = (id) =>
      selected && selected !== id ? " dim" : selected === id ? " hot" : "";

    const groups = {
      frame: { dx: 0, dy: 0, dz: 0 },
      table: { dx: 0, dy: 0, dz: -6 * e },
      conveyor: { dx: 0, dy: 0, dz: -6 * e },
      drum: { dx: 0, dy: 0, dz: 8 * e },
      hood: { dx: 0, dy: 0, dz: 12 * e },
      motor: { dx: 8 * e, dy: 0, dz: 0 },
      guard: { dx: 6 * e, dy: 0, dz: 0 },
      stand: { dx: 0, dy: 0, dz: -10 * e },
    };

    const faces = [];
    function box(id, x, y, z, dx, dy, dz, color) {
      const g = groups[id] || { dx: 0, dy: 0, dz: 0 };
      x += g.dx;
      y += g.dy;
      z += g.dz;
      const v = [
        [x, y, z],
        [x + dx, y, z],
        [x + dx, y + dy, z],
        [x, y + dy, z],
        [x, y, z + dz],
        [x + dx, y, z + dz],
        [x + dx, y + dy, z + dz],
        [x, y + dy, z + dz],
      ];
      const quads = [
        [0, 1, 2, 3],
        [4, 5, 6, 7],
        [0, 1, 5, 4],
        [1, 2, 6, 5],
        [2, 3, 7, 6],
        [3, 0, 4, 7],
      ];
      for (const q of quads) {
        const pts = q.map((i) => v[i]);
        const depth = pts.reduce((a, p) => a + p[0] + p[1] + p[2], 0) / 4;
        faces.push({ id, color, pts, depth });
      }
    }
    function cylX(id, x, y, z, d, h, color) {
      box(id, x, y - d / 2, z - d / 2, h, d, d, color);
    }

    box("stand", 0.5, 2, -14, 21, 32, 12, "#6e5638");
    box("frame", 0, 0, 0, 22, 36, 0.75, "#8a6a42");
    box("frame", 0, 0, 0.75, 1.5, 36, 19.25, "#c4a574");
    box("frame", 18, 0, 0.75, 1.5, 36, 19.25, "#b89660");
    box("table", 1.62, 5.5, 8.5, 16.26, 25, 0.75, "#e8eef0");
    box("conveyor", 1.65, 4.57, 9.25, 16.2, 26.86, 0.08, "#1a1a1c");
    cylX("drum", 1.75, 18, 13.5, 5.0, 16, "#b4532a");
    cylX("drum", -0.25, 18, 13.5, 0.75, 22, "#d0d4d6");
    box("hood", 1.58, 13.8, 13.9, 16.34, 8.4, 0.25, "#3d4a46");
    cylX("motor", 19.75, 28, 4.6, 6.5, 8, "#161616");
    box("guard", 19.55, 12, 1, 2.2, 16.5, 16.5, "#8a6a42");

    faces.sort((a, b) => a.depth - b.depth);
    let minx = Infinity,
      maxx = -Infinity,
      miny = Infinity,
      maxy = -Infinity;
    const proj = faces.map((f) => {
      const xy = f.pts.map((p) => iso(p[0], p[1], p[2]));
      xy.forEach(([x, y]) => {
        minx = Math.min(minx, x);
        maxx = Math.max(maxx, x);
        miny = Math.min(miny, y);
        maxy = Math.max(maxy, y);
      });
      return { ...f, xy };
    });
    const W = 900,
      H = 560,
      pad = 36;
    const s = Math.min((W - pad * 2) / (maxx - minx + 0.01), (H - pad * 2) / (maxy - miny + 0.01));
    const cx = (minx + maxx) / 2,
      cy = (miny + maxy) / 2;
    const T = (x, y) => [W / 2 + (x - cx) * s, H / 2 + (y - cy) * s];

    const polys = proj
      .map((f) => {
        const pts = f.xy.map(([x, y]) => T(x, y).map((n) => n.toFixed(1)).join(",")).join(" ");
        return `<polygon class="fence-part${dim(f.id)}" data-part="${f.id}" points="${pts}" fill="${f.color}" stroke="#1c1914" stroke-width="0.8" stroke-linejoin="round"/>`;
      })
      .join("");

    stage.innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="WALTER sander visualization">
      <defs><filter id="glow"><feDropShadow dx="0" dy="0" stdDeviation="2.5" flood-color="#d47248"/></filter></defs>
      ${polys}
      <text x="24" y="${H - 16}" fill="#8a7a68" font-size="12" font-family="IBM Plex Mono,monospace">22×36×22″ · explode ${Math.round(e * 100)}%</text>
    </svg>`;

    stage.querySelectorAll("[data-part]").forEach((el) => {
      el.addEventListener("click", (ev) => {
        ev.stopPropagation();
        selectPart(el.getAttribute("data-part"));
      });
    });
  }

  function selectPart(id) {
    state.selected = state.selected === id ? null : id;
    store.set("selected", state.selected);
    $$(".part").forEach((p) => p.classList.toggle("on", p.dataset.part === id && state.selected));
    drawViz();
    const part = D.parts.find((p) => p.id === id);
    if (part && state.selected) {
      $("#partDetail").innerHTML = `<strong>${part.label}</strong><p>${part.detail}</p>`;
    } else {
      $("#partDetail").innerHTML = `<strong>Select a part</strong><p>Click the model or the list to inspect. Drag the explode slider for assembly breakdown.</p>`;
    }
  }

  function renderPartList() {
    $("#partList").innerHTML = D.parts
      .map(
        (p) =>
          `<button type="button" class="part${state.selected === p.id ? " on" : ""}" data-part="${p.id}">
            <strong>${p.label}</strong><small>${p.detail}</small>
          </button>`
      )
      .join("");
    $$("#partList .part").forEach((b) =>
      b.addEventListener("click", () => {
        selectPart(b.dataset.part);
        if (window.WALTER_SCENE && window.WALTER_SCENE.ready) window.WALTER_SCENE.select(b.dataset.part);
      })
    );
  }

  function renderAssembly() {
    const phase = state.phase;
    const list = D.assembly.filter((s) => phase === "all" || s.phase === phase);
    $("#assemblyList").innerHTML = list
      .map((s) => {
        const done = !!state.done[s.id];
        const n = D.assembly.findIndex((x) => x.id === s.id) + 1;
        return `<div class="step${done ? " done" : ""}" data-id="${s.id}">
          <div class="num">${String(n).padStart(2, "0")}</div>
          <div><h3>${s.title}</h3><p>${s.body}</p></div>
          <button type="button" class="check" aria-label="Mark done" data-id="${s.id}"></button>
        </div>`;
      })
      .join("");
    $$("#assemblyList .check").forEach((b) =>
      b.addEventListener("click", () => {
        state.done[b.dataset.id] = !state.done[b.dataset.id];
        store.set("done", state.done);
        renderAssembly();
        refreshProgress();
        toast(state.done[b.dataset.id] ? "Step complete" : "Step reopened");
        if (window.WALTER_SCENE && window.WALTER_SCENE.ready) {
          const n = D.assembly.findIndex((x) => x.id === b.dataset.id) + 1;
          window.WALTER_SCENE.setMode("build");
          window.WALTER_SCENE.setStep(n);
        }
      })
    );
    $$(".phase-rail .chip").forEach((c) => c.classList.toggle("on", c.dataset.phase === phase));
  }

  function renderPhases() {
    $("#phaseRail").innerHTML = D.phases
      .map(
        (p) =>
          `<button type="button" class="chip${state.phase === p.id ? " on" : ""}" data-phase="${p.id}">${p.label}</button>`
      )
      .join("");
    $$("#phaseRail .chip").forEach((c) =>
      c.addEventListener("click", () => {
        state.phase = c.dataset.phase;
        store.set("phase", state.phase);
        renderAssembly();
      })
    );
  }

  function renderMaterials() {
    const rows = D.lumber
      .map((r, i) => {
        const id = "l" + i;
        const bought = !!state.bought[id];
        return `<tr class="${bought ? "bought" : ""}">
          <td><input class="buy-check" type="checkbox" data-id="${id}" ${bought ? "checked" : ""}/></td>
          <td>${r.qty}</td><td>${r.nom}</td><td>${r.len}</td><td>${r.use}</td><td class="mono">${r.bf.toFixed(1)}</td>
        </tr>`;
      })
      .join("");
    $("#lumberBody").innerHTML = rows;
    const total = D.lumber.reduce((a, r) => a + r.bf, 0);
    $("#bfTotal").textContent = "≈ " + total.toFixed(1) + " bf";
    $$("#lumberBody .buy-check").forEach((c) =>
      c.addEventListener("change", () => {
        state.bought[c.dataset.id] = c.checked;
        store.set("bought", state.bought);
        renderMaterials();
      })
    );
    $("#miscList").innerHTML = D.misc.map((m) => `<li><strong>${m.item}</strong> — ${m.qty}</li>`).join("");
    $("#toolsList").innerHTML = D.tools.map((t) => `<li>${t}</li>`).join("");
  }

  function renderJoinery() {
    $("#joineryList").innerHTML = D.subsystems
      .map(
        (j) => `<article class="join">
          <div class="glyph">${j.id.slice(0, 2).toUpperCase()}</div>
          <div>
            <h3>${j.name}</h3>
            <p class="hint" style="margin:0 0 6px">${j.where} · <span class="mono">${j.lock}</span></p>
            <p style="margin:0;color:var(--dim);font-size:14px">${j.tip}</p>
          </div>
        </article>`
      )
      .join("");
  }

  function renderGallery() {
    $("#galleryGrid").innerHTML = D.gallery
      .map(
        (g) => `<a class="shot" href="${g.src}" data-gallery="${g.src}" data-title="${g.title}">
          <img src="${g.src}" alt="${g.title}" loading="lazy"/>
          <figcaption>${g.kind} · ${g.title}</figcaption>
        </a>`
      )
      .join("");
    $$("#galleryGrid .shot").forEach((a) =>
      a.addEventListener("click", (e) => {
        e.preventDefault();
        openLightbox(a.dataset.gallery, a.dataset.title);
      })
    );
  }

  function openLightbox(src, title) {
    const box = $("#lightbox");
    const isSvg = src.endsWith(".svg");
    $("#lightboxBody").innerHTML = isSvg
      ? `<object data="${src}" type="image/svg+xml" aria-label="${title}"></object>`
      : `<img src="${src}" alt="${title}"/>`;
    box.classList.add("on");
  }

  function renderDownloads() {
    $("#downloadGrid").innerHTML = D.downloads
      .map(
        (d) =>
          `<a class="dl" href="${d.href}" ${d.href.match(/\.(FCStd|step|stl|obj|py|svg|csv|json|scad)$/) ? "download" : ""}>
            <b>${d.label}</b><span>${d.note}</span>
          </a>`
      )
      .join("");
  }

  function renderDrafts() {
    const d = state.drafts;
    $("#draftGrit").value = d.grit || "80";
    $("#draftOpen").value = d.opening ?? 1.5;
    $("#draftFeed").value = d.feed ?? 8;
    $("#draftElec").value = d.elec || "";
    $("#draftNotes").value = d.notes || "";
  }

  function saveDrafts() {
    state.drafts = {
      grit: $("#draftGrit").value,
      opening: parseFloat($("#draftOpen").value) || 1.5,
      feed: parseFloat($("#draftFeed").value) || 8,
      elec: $("#draftElec").value,
      notes: $("#draftNotes").value,
    };
    store.set("drafts", state.drafts);
    toast("Drafts saved locally");
  }

  function exportDrafts() {
    const payload = {
      exportedAt: new Date().toISOString(),
      design: D.meta,
      drafts: state.drafts,
      assemblyDone: state.done,
      lumberBought: state.bought,
      progressPct: progressPct(),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "walter-sander-drafts.json";
    a.click();
    toast("JSON exported");
  }

  function renderWinter() {
    $("#winterList").innerHTML = D.rules.map((w, i) => `<li><span class="mono">${i + 1}.</span> ${w}</li>`).join("");
  }

  function init() {
    renderOverview();
    renderPartList();
    renderPhases();
    renderAssembly();
    renderMaterials();
    renderJoinery();
    renderGallery();
    renderDownloads();
    renderDrafts();
    renderWinter();
    refreshProgress();
    drawViz();
    setTab(state.tab);
    const hash = (location.hash || "").replace("#", "");
    if (hash === "viz") setTab("viz");

    $$(".tab, .mobile-nav button").forEach((b) =>
      b.addEventListener("click", () => setTab(b.dataset.tab))
    );
    $$("[data-tab]").forEach((b) => {
      if (b.closest(".tabs, .mobile-nav")) return;
      b.addEventListener("click", () => {
        if (b.dataset.tab) setTab(b.dataset.tab);
      });
    });

    $("#explodeRange").addEventListener("input", (e) => {
      state.explode = parseFloat(e.target.value);
      store.set("explode", state.explode);
      $("#explodeVal").textContent = Math.round(state.explode * 100) + "%";
      if (window.WALTER_SCENE && window.WALTER_SCENE.ready) window.WALTER_SCENE.setExplode(state.explode);
      else drawViz();
    });
    $("#explodeRange").value = state.explode;
    $("#explodeVal").textContent = Math.round(state.explode * 100) + "%";
    $("#btnBreakdown").addEventListener("click", () => {
      $("#explodeRange").value = 0.72;
      $("#explodeRange").dispatchEvent(new Event("input"));
    });
    $("#btnAssembled").addEventListener("click", () => {
      $("#explodeRange").value = 0;
      $("#explodeRange").dispatchEvent(new Event("input"));
    });

    $("#saveDrafts").addEventListener("click", saveDrafts);
    $("#exportDrafts").addEventListener("click", exportDrafts);
    $("#resetProgress").addEventListener("click", () => {
      if (confirm("Reset assembly checklist?")) {
        state.done = {};
        store.set("done", state.done);
        renderAssembly();
        refreshProgress();
        toast("Progress reset");
      }
    });
    $("#printBtn").addEventListener("click", () => window.print());
    $("#lightboxClose").addEventListener("click", () => $("#lightbox").classList.remove("on"));
    $("#lightbox").addEventListener("click", (e) => {
      if (e.target.id === "lightbox") $("#lightbox").classList.remove("on");
    });
    ["draftGrit", "draftOpen", "draftFeed", "draftElec", "draftNotes"].forEach((id) => {
      const el = $("#" + id);
      if (el) el.addEventListener("change", saveDrafts);
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
