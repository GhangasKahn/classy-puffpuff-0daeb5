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
      latch: "B",
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
      ["Board feet", "≈ " + m.boardFeet + " buy"],
      ["Climate", "Buffalo NY"],
    ]
      .map(
        ([k, v]) =>
          `<div class="card stat"><span>${k}</span><b>${v}</b></div>`
      )
      .join("");
  }

  /* ---------- Visualizer (SVG) — Rev F.2 gold Tree of Life; never a ranch fence ---------- */
  function motifSvg(m, xOf, yOf, S) {
    const rects = (m.rects || [])
      .map((r) => {
        let fill = "#1c2018";
        if (r.role === "leaf" || r.role === "jewel" || r.role === "pot") fill = "#c9a227";
        else if (r.role === "trunk") fill = "#141610";
        else if (r.role === "frame" || r.role === "ribbon" || r.role === "inner") fill = "#2a322c";
        else if (r.role === "mullion") fill = "#1c2018";
        return `<rect x="${xOf(r.x)}" y="${yOf(r.z + r.h)}" width="${r.w * S}" height="${r.h * S}" fill="${fill}" stroke="#1a1f24" stroke-width="0.4"/>`;
      })
      .join("");
    const lines = (m.lines || [])
      .map(
        (ln) =>
          `<line x1="${xOf(ln.x1)}" y1="${yOf(ln.z1)}" x2="${xOf(ln.x2)}" y2="${yOf(ln.z2)}" stroke="#1a1f24" stroke-width="${Math.max(1.6, (ln.t || 0.75) * S * 0.6)}" stroke-linecap="square"/>`
      )
      .join("");
    return rects + lines;
  }

  function vizLayout() {
    const baked = window.MARTIN_LAYOUT;
    const fab = window.MARTIN_FAB && window.MARTIN_FAB.layout;
    return baked || fab || null;
  }

  function drawViz() {
    const stage = $("#vizStage");
    if (!stage) return;
    const ly = vizLayout();
    const L = (ly && ly.overall_length) || D.meta.length;
    const H = (ly && ly.overall_height) || D.meta.height;
    const gate = (ly && ly.gate_clear) || D.meta.gateClear;
    const explode = state.explode;
    const lift = explode * 28;
    const spread = explode * 18;
    const selected = state.selected;

    const S = 6.2;
    const padX = 40;
    const padY = 40;
    const W = padX * 2 + L * S + explode * 80;
    const VH = padY * 2 + (H + 28) * S + lift * 2;

    const yOf = (z) => padY + (H - z) * S + lift;
    const xOf = (x) => padX + x * S + spread;
    const dim = (id) => (selected && selected !== id ? " dim" : selected === id ? " hot" : "");

    const postsMeta = ly
      ? ly.posts.map((p) => ({ id: p.mark, x: p.cx }))
      : D.posts;
    const slats = ly ? ly.slats : D.rails.filter((r) => r.id !== "CAP");
    const motifs = (ly && ly.motifs) || [];
    const nukiX0 = ly ? ly.nuki_x0 : 36.5;
    const nukiLen = ly ? ly.nuki_len : 109.5;
    const capX0 = ly ? ly.cap_x0 : 36.0;
    const capLen = ly ? ly.cap_len : 110.5;
    const fx = 3.5;

    const sills = `<rect class="fence-part${dim("sills")}" data-part="sills" x="${xOf(-6)}" y="${yOf(0)}" width="${(L + 12) * S}" height="${5.5 * S}" fill="#9a9890" stroke="#1a1f24"/>`;

    const ties = postsMeta
      .map(
        (p, i) =>
          `<rect class="fence-part${dim("ties")}" data-part="ties" x="${xOf(p.x - fx / 2)}" y="${yOf(0) + 2}" width="${fx * S}" height="${8 * S * 0.35}" fill="#b8b6b0" stroke="#1a1f24" transform="translate(0,${i * lift * 0.05})"/>`
      )
      .join("");

    let cassettes = "";
    slats
      .filter((sl) => String(sl.id || "").startsWith("Q-") || sl.stock === "cassette")
      .forEach((sl) => {
        const z0 = sl.z0 != null ? sl.z0 : sl.cl - sl.h / 2;
        cassettes += `<rect class="fence-part${dim("rails")}" data-part="rails" x="${xOf(nukiX0 + 0.4)}" y="${yOf(z0 + sl.h)}" width="${(nukiLen - 0.8) * S}" height="${sl.h * S}" fill="#ebe4cc" stroke="none"/>`;
      });

    const motifDraw = motifs
      .filter((m) => m.bay !== "gate")
      .map((m) => `<g class="fence-part${dim("rails")}" data-part="rails">${motifSvg(m, xOf, yOf, S)}</g>`)
      .join("");

    const belts = slats
      .filter((sl) => sl.nuki || String(sl.id || "").startsWith("K-") || String(sl.id || "").startsWith("R-"))
      .map((sl, i) => {
        const z1 = sl.z1 != null ? sl.z1 : sl.cl + sl.h / 2;
        const fill = String(sl.id || "").startsWith("K") ? "#3a3d38" : "#4a4e48";
        return `<rect class="fence-part${dim("rails")}" data-part="rails" x="${xOf(nukiX0)}" y="${yOf(z1) - i * lift * 0.03}" width="${nukiLen * S}" height="${sl.h * S}" fill="${fill}" stroke="#1a1f24" stroke-width="1"/>`;
      })
      .join("");

    const posts = postsMeta
      .map((p, i) => {
        const x = xOf(p.x - fx / 2);
        const y = yOf(H - 1.5);
        const h = (H - 1.5) * S;
        let bricks = "";
        if (p.id !== "P0") {
          for (let row = 0; row < 18; row++) {
            const z = 2 + row * 1.7;
            if (z > H - 4) break;
            const off = row % 2 ? 0.75 : 0;
            for (let k = 0; k < 3; k++) {
              bricks += `<rect x="${xOf(p.x - 2.1 + off + k * 1.65)}" y="${yOf(z + 1.5) + lift * 0.1}" width="${1.5 * S}" height="${1.5 * S}" fill="#a8aaa4" stroke="#8a8c86" stroke-width=".4"/>`;
            }
          }
        }
        return `<g class="fence-part${dim("posts")}" data-part="posts" transform="translate(0,${-i * lift * 0.15})">
          <rect x="${x}" y="${y}" width="${fx * S}" height="${h}" fill="#c4c2ba" stroke="#1a1f24" stroke-width="1.2"/>
          ${bricks}
          <text x="${x + 1.75 * S}" y="${y - 6}" text-anchor="middle" fill="#8fad78" font-size="11" font-family="IBM Plex Mono,monospace">${p.id}</text>
        </g>`;
      })
      .join("");

    const cap = `<g class="fence-part${dim("cap")}" data-part="cap">
      <rect x="${xOf(capX0)}" y="${yOf(H) - lift * 0.4}" width="${capLen * S}" height="${1.5 * S}" fill="#2a2e2c" stroke="#1a1f24"/>
      <rect x="${xOf(capX0)}" y="${yOf(H - 1.5) - lift * 0.4}" width="${capLen * S}" height="${3.5 * S}" fill="#1a1f24" stroke="#1a1f24"/>
    </g>`;

    let planters = "";
    if (ly && ly.posts) {
      for (const pair of [[1, 2], [2, 3]]) {
        const x0 = ly.posts[pair[0]].cx + fx / 2 + 0.4;
        const x1 = ly.posts[pair[1]].cx - fx / 2 - 0.4;
        planters += `<rect class="fence-part${dim("boards")}" data-part="boards" x="${xOf(x0)}" y="${yOf(7.5)}" width="${(x1 - x0) * S}" height="${7.5 * S}" fill="#6a6e66" stroke="#1a1f24"/>`;
      }
    }

    const gateMotifs = motifs
      .filter((m) => m.bay === "gate")
      .map((m) => motifSvg(m, xOf, yOf, S))
      .join("");
    const latchCl = (ly && ly.latch_cl) || 36.5;
    const gh = (ly && ly.gate_h) || H - 2.4;
    const gw = (ly && ly.gate_leaf_w) || gate - 1;
    const gateLeaf = `<g class="fence-part${dim("gate")}" data-part="gate" transform="translate(${-spread * 0.6},${-lift * 0.25})">
      <rect x="${xOf(fx + 0.5)}" y="${yOf(0.375 + gh)}" width="${gw * S}" height="${gh * S}" fill="#ebe4cc" stroke="#5a6a4a" stroke-width="2"/>
      ${gateMotifs}
      <rect x="${xOf(fx + 0.5)}" y="${yOf(0.375 + gh)}" width="${3.5 * S}" height="${gh * S}" fill="#c4c2ba" stroke="#1a1f24"/>
      <rect x="${xOf(fx + 0.5 + gw - 3.5)}" y="${yOf(0.375 + gh)}" width="${3.5 * S}" height="${gh * S}" fill="#c4c2ba" stroke="#1a1f24"/>
      <text x="${xOf(fx + gate / 2)}" y="${yOf(2.2)}" text-anchor="middle" fill="#c9a227" font-size="11" font-family="IBM Plex Mono,monospace" font-weight="600">TREE OF LIFE</text>
    </g>`;

    const latch = `<rect class="fence-part${dim("latch")}" data-part="latch" x="${xOf(fx + 0.5) - 18 * S * (0.35 + explode * 0.4)}" y="${yOf(latchCl + 1.75)}" width="${18 * S * (0.35 + explode * 0.25)}" height="${3.5 * S}" fill="#aeb6ba" stroke="#1a1f24"/>`;

    stage.innerHTML = `<svg viewBox="0 0 ${W} ${VH}" role="img" aria-label="MARTIN Tree of Life fence">
      <defs>
        <filter id="glow"><feDropShadow dx="0" dy="0" stdDeviation="2.5" flood-color="#c9a227"/></filter>
      </defs>
      ${sills}${ties}${cassettes}${motifDraw}${belts}${posts}${planters}${cap}${gateLeaf}${latch}
      <text x="${padX}" y="${VH - 10}" fill="#c9a227" font-size="11" font-family="IBM Plex Mono,monospace">143″ Tree of Life · gold squares · 2×4 ribbons · explode ${Math.round(explode * 100)}%</text>
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
      .map((m) => {
        const name = m.href
          ? `<a href="${m.href}" rel="noopener" target="_blank">${m.item}</a>`
          : m.item;
        return `<li><strong>${name}</strong> — ${m.qty}</li>`;
      })
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

  function renderFab(fab) {
    if (!fab) return;
    const nest = fab.nest || {};
    $("#fabStats").innerHTML = [
      ["Parts", fab.parts.length],
      ["Joints", fab.joints.length],
      ["Net bf", nest.net_bf],
      ["Buy bf", nest.procurement_bf],
      ["Ballast", fab.ballast ? Math.round(fab.ballast.provided_lb) + " lb" : "—"],
      ["Rev", fab.project.REVISION],
    ]
      .map(([k, v]) => `<div class="card stat"><span>${k}</span><b>${v}</b></div>`)
      .join("");
    $("#fabParts").innerHTML = fab.parts
      .filter((p) => p.MAKE_OR_BUY === "MAKE")
      .map(
        (p) =>
          `<tr><td class="mono">${p.PART_ID}</td><td>${p.PART_NAME}</td><td>${p.QUANTITY}</td><td class="mono">${p.FINISHED_THICKNESS}×${p.FINISHED_WIDTH}×${p.FINISHED_LENGTH}</td><td>${(p.JOINERY || "").slice(0, 72)}</td></tr>`
      )
      .join("");
    $("#fabJoints").innerHTML = fab.joints
      .map(
        (j) =>
          `<tr><td class="mono">${j.JOINT_ID}</td><td>${j.JOINT_TYPE}</td><td>${j.PART_A}</td><td>${j.PART_B}</td><td>${j.FIT_CLASS || ""}</td></tr>`
      )
      .join("");
    $("#fabQa").innerHTML = (fab.qa_geometry || [])
      .map((g) => `<li><strong>${g.level}</strong> — ${g.item}: ${g.detail || ""}</li>`)
      .join("");
    $("#fabOpen").innerHTML = (fab.unresolved || [])
      .map((u) => `<li><strong>${u.ID}</strong> ${u.ITEM} [${u.CLASS}]</li>`)
      .join("");
    const dwg = (fab.drawing_index || []).filter((d) => String(d.FILE).endsWith(".svg"));
    $("#fabDrawings").innerHTML = dwg
      .map((d) => {
        const href = d.FILE.startsWith("T-")
          ? `../fab/10_TEMPLATES/${d.FILE}`
          : d.FILE.startsWith("QA")
          ? `../fab/12_QA/${d.FILE}`
          : d.FILE.startsWith("L-")
          ? `../fab/11_BUILD_MANUAL/${d.FILE}`
          : `../fab/06_DRAWINGS/${d.FILE}`;
        return `<a class="shot" href="${href}" data-gallery="${href}" data-title="${d.DWG}">
          <img src="${href}" alt="${d.TITLE}" loading="lazy"/>
          <figcaption>${d.DWG} · ${d.TITLE}</figcaption>
        </a>`;
      })
      .join("");
    $$("#fabDrawings .shot").forEach((a) =>
      a.addEventListener("click", (e) => {
        e.preventDefault();
        openLightbox(a.dataset.gallery, a.dataset.title);
      })
    );
  }

  function loadFab() {
    fetch("fab.json")
      .then((r) => r.json())
      .then((fab) => {
        window.MARTIN_FAB = fab;
        renderFab(fab);
        drawViz();
      })
      .catch(() => {
        const el = $("#fabStats");
        if (el) el.innerHTML = "<p class='hint'>fab.json not loaded — open the fabrication package folder.</p>";
      });
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
    loadFab();
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
