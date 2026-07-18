/* MARTIN Build App — interactive shell */
(function () {
  const D = window.MARTIN_DATA;
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const store = {
    get(k, fallback) {
      try {
        const v = localStorage.getItem("martin_" + k);
        return v == null ? fallback : JSON.parse(v);
      } catch {
        return fallback;
      }
    },
    set(k, v) {
      try {
        localStorage.setItem("martin_" + k, JSON.stringify(v));
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
      dropOff: D.meta.dropDefault,
      grayHex: "#6e7578",
      latch: "A",
      notes: "",
      site: "",
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
    if (id === "viz") drawViz();
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

  /* ---------- Overview ---------- */
  function renderOverview() {
    const m = D.meta;
    $("#overviewStats").innerHTML = [
      ["Length", m.length + "″"],
      ["Height", m.height + "″"],
      ["Gate", m.gateClear + "″ clear"],
      ["Bay", m.bayClear + "″ each"],
      ["Board feet", "≈ " + m.boardFeet],
      ["Climate", "Buffalo NY"],
    ]
      .map(
        ([k, v]) =>
          `<div class="card stat"><span>${k}</span><b>${v}</b></div>`
      )
      .join("");
  }

  /* ---------- Visualizer (SVG) ---------- */
  function drawViz() {
    const stage = $("#vizStage");
    if (!stage) return;
    const L = D.meta.length;
    const H = D.meta.height;
    const gate = D.meta.gateClear;
    const explode = state.explode; // 0..1
    const lift = explode * 28;
    const spread = explode * 18;
    const selected = state.selected;

    const S = 6.2; // px per inch
    const padX = 40;
    const padY = 36;
    const W = padX * 2 + L * S + explode * 80;
    const VH = padY * 2 + (H + 24) * S + lift * 2;

    const yOf = (z) => padY + (H - z) * S + lift;
    const xOf = (x) => padX + x * S + spread;

    const dim = (id) => (selected && selected !== id ? " dim" : selected === id ? " hot" : "");

    const posts = D.posts
      .map((p, i) => {
        const x = xOf(p.x - 1.75);
        const y = yOf(H - 1.5);
        const h = (H - 1.5) * S;
        return `<g class="fence-part${dim("posts")}" data-part="posts" transform="translate(0,${-i * lift * 0.15})">
          <rect x="${x}" y="${y}" width="${3.5 * S}" height="${h}" fill="#d9dcde" stroke="#1a1f24" stroke-width="1.2"/>
          <text x="${x + 1.75 * S}" y="${y - 6}" text-anchor="middle" fill="#8fad78" font-size="11" font-family="IBM Plex Mono,monospace">${p.id}</text>
        </g>`;
      })
      .join("");

    const rails = D.rails
      .filter((r) => r.id !== "CAP")
      .map((r, i) => {
        const x0 = xOf(41.25 - 1.75 - 0.5);
        const w = (141.25 + 1.75 + 0.5 - (41.25 - 1.75 - 0.5)) * S;
        const y = yOf(r.cl + 3.625);
        return `<rect class="fence-part${dim("rails")}" data-part="rails" x="${x0}" y="${y - i * lift * 0.08}" width="${w}" height="${7.25 * S}" fill="#6e7578" stroke="#1a1f24" stroke-width="1"/>`;
      })
      .join("");

    const cap = (() => {
      const x0 = xOf(41.25 - 1.75 - 0.75);
      const w = (141.25 + 1.75 + 0.75 - (41.25 - 1.75 - 0.75)) * S;
      return `<rect class="fence-part${dim("cap")}" data-part="cap" x="${x0}" y="${yOf(H) - lift * 0.4}" width="${w}" height="${1.5 * S}" fill="#8a9094" stroke="#1a1f24"/>`;
    })();

    // boards hint
    let boards = "";
    for (const bay of [
      [41.25 + 1.75, 91.25 - 1.75],
      [91.25 + 1.75, 141.25 - 1.75],
    ]) {
      const clear = bay[1] - bay[0];
      const n = 7;
      const pitch = clear / n;
      for (let i = 0; i < n; i++) {
        const x = xOf(bay[0] + i * pitch + 0.15);
        boards += `<rect class="fence-part${dim("boards")}" data-part="boards" x="${x}" y="${yOf(10 - 3.625) + lift * 0.2}" width="${(pitch - 0.3) * S}" height="${(10 - 3.625 - 1.5) * S}" fill="#cfd3d5" stroke="#9aa3a6" stroke-width=".5"/>`;
      }
    }

    const gateLeaf = `<g class="fence-part${dim("gate")}" data-part="gate" transform="translate(${-spread * 0.6},${-lift * 0.25})">
      <rect x="${xOf(3.5 + 0.5)}" y="${yOf(H - 0.5)}" width="${(gate - 1) * S}" height="${(H - 1.5) * S}" fill="#e8eaeb" stroke="#5a6a4a" stroke-width="2" stroke-dasharray="${explode > 0.2 ? "0" : "6 4"}"/>
      <line x1="${xOf(7)}" y1="${yOf(8)}" x2="${xOf(3.5 + gate - 4)}" y2="${yOf(H - 8)}" stroke="#5a6a4a" stroke-width="3"/>
      <text x="${xOf(3.5 + gate / 2)}" y="${yOf(H / 2)}" text-anchor="middle" fill="#5a6a4a" font-size="13" font-family="IBM Plex Mono,monospace" font-weight="600">GATE</text>
    </g>`;

    const latch = `<rect class="fence-part${dim("latch")}" data-part="latch" x="${xOf(3.5 + 0.5) - 18 * S * (0.35 + explode * 0.4)}" y="${yOf(28 + 1.75)}" width="${18 * S * (0.35 + explode * 0.25)}" height="${3.5 * S}" fill="#aeb6ba" stroke="#1a1f24"/>`;

    const pad = `<rect class="fence-part${dim("pad")}" data-part="pad" x="${xOf(-6)}" y="${yOf(0)}" width="${(L + 12) * S}" height="${6 * S}" fill="#9a9890" stroke="#1a1f24"/>`;

    const piers = D.posts
      .map((p, i) => {
        const x = xOf(p.x - 7);
        return `<rect class="fence-part${dim("piers")}" data-part="piers" x="${x}" y="${yOf(0) + 2}" width="${14 * S * 0.35}" height="${10 * S * 0.35}" fill="#b8b6b0" stroke="#1a1f24" transform="translate(0,${i * lift * 0.05})"/>`;
      })
      .join("");

    stage.innerHTML = `<svg viewBox="0 0 ${W} ${VH}" role="img" aria-label="MARTIN fence visualization">
      <defs>
        <filter id="glow"><feDropShadow dx="0" dy="0" stdDeviation="2.5" flood-color="#8fad78"/></filter>
      </defs>
      ${pad}${piers}${posts}${boards}${rails}${cap}${gateLeaf}${latch}
      <text x="${padX}" y="${VH - 10}" fill="#6e7578" font-size="11" font-family="IBM Plex Mono,monospace">143″ overall · explode ${Math.round(explode * 100)}%</text>
    </svg>`;

    stage.querySelectorAll("[data-part]").forEach((el) => {
      el.addEventListener("click", (e) => {
        e.stopPropagation();
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
      b.addEventListener("click", () => selectPart(b.dataset.part))
    );
  }

  /* ---------- Assembly ---------- */
  function renderAssembly() {
    const phase = state.phase;
    const list = D.assembly.filter((s) => phase === "all" || s.phase === phase);
    $("#assemblyList").innerHTML = list
      .map((s, i) => {
        const done = !!state.done[s.id];
        return `<div class="step${done ? " done" : ""}" data-id="${s.id}">
          <div class="num">${String(i + 1).padStart(2, "0")}</div>
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
      })
    );
    $$(".phase-rail .chip").forEach((c) =>
      c.classList.toggle("on", c.dataset.phase === phase)
    );
  }

  /* ---------- Materials ---------- */
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
    $("#miscList").innerHTML = D.misc
      .map((m) => `<li><strong>${m.item}</strong> — ${m.qty}</li>`)
      .join("");
    $("#toolsList").innerHTML = D.tools.map((t) => `<li>${t}</li>`).join("");
  }

  /* ---------- Joinery / Gallery / Downloads / Drafts ---------- */
  function renderJoinery() {
    $("#joineryList").innerHTML = D.joinery
      .map(
        (j) => `<article class="join">
          <div class="glyph">${j.jp}</div>
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
          `<a class="dl" href="${d.href}" ${d.href.match(/\.(FCStd|step|stl|py|svg)$/) ? "download" : ""}>
            <b>${d.label}</b><span>${d.note}</span>
          </a>`
      )
      .join("");
  }

  function renderDrafts() {
    const d = state.drafts;
    $("#draftDrop").value = d.dropOff;
    $("#draftGray").value = d.grayHex;
    $("#draftLatch").value = d.latch;
    $("#draftSite").value = d.site || "";
    $("#draftNotes").value = d.notes || "";
    $("#graySwatch").style.background = d.grayHex;
  }

  function saveDrafts() {
    state.drafts = {
      dropOff: parseFloat($("#draftDrop").value) || D.meta.dropDefault,
      grayHex: $("#draftGray").value,
      latch: $("#draftLatch").value,
      site: $("#draftSite").value,
      notes: $("#draftNotes").value,
    };
    store.set("drafts", state.drafts);
    $("#graySwatch").style.background = state.drafts.grayHex;
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
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "martin-fence-drafts.json";
    a.click();
    toast("JSON exported");
  }

  function renderWinter() {
    $("#winterList").innerHTML = D.winter.map((w, i) => `<li><span class="mono">${i + 1}.</span> ${w}</li>`).join("");
  }

  /* ---------- Wire UI ---------- */
  function init() {
    renderOverview();
    renderPartList();
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

    $$(".tab, .mobile-nav button").forEach((b) =>
      b.addEventListener("click", () => setTab(b.dataset.tab))
    );

    $("#explodeRange").addEventListener("input", (e) => {
      state.explode = parseFloat(e.target.value);
      store.set("explode", state.explode);
      $("#explodeVal").textContent = Math.round(state.explode * 100) + "%";
      drawViz();
    });
    $("#explodeRange").value = state.explode;
    $("#explodeVal").textContent = Math.round(state.explode * 100) + "%";

    $$(".phase-rail .chip").forEach((c) =>
      c.addEventListener("click", () => {
        state.phase = c.dataset.phase;
        store.set("phase", state.phase);
        renderAssembly();
      })
    );

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
    $("#lightboxClose").addEventListener("click", () =>
      $("#lightbox").classList.remove("on")
    );
    $("#lightbox").addEventListener("click", (e) => {
      if (e.target.id === "lightbox") $("#lightbox").classList.remove("on");
    });
    ["draftDrop", "draftGray", "draftLatch", "draftSite", "draftNotes"].forEach(
      (id) => {
        const el = $("#" + id);
        if (el) el.addEventListener("change", saveDrafts);
      }
    );
    $("#draftGray").addEventListener("input", () => {
      $("#graySwatch").style.background = $("#draftGray").value;
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else init();
})();
