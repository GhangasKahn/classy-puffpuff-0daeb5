/* MARTIN Build App — visual 5-phase walk + explode + checklist */
(function () {
  const D = window.MARTIN_DATA;
  let SSOT = null;

  function loadSSOT() {
    return fetch("martin.json")
      .then((r) => (r.ok ? r.json() : null))
      .then((j) => {
        SSOT = j;
        return j;
      })
      .catch(() => null);
  }
  const W = window.MARTIN_WALK;
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
    tab: store.get("tab", "walk"),
    explode: store.get("explode", 0),
    selected: store.get("selected", null),
    done: store.get("done", {}),
    bought: store.get("bought", {}),
    phase: store.get("phase", "all"),
    walkIdx: store.get("walkIdx", 0),
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
    if (id === "walk") renderWalk();
    if (id === "registry") renderRegistry();
    if (id === "qa") renderQA();
    if (id === "fab") {
      if (window.MARTIN_FAB) renderFab(window.MARTIN_FAB);
      else loadFab();
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
    $$(".progress-pill").forEach((el) => (el.textContent = pct + "% complete"));
    const bar = $("#progressBar");
    if (bar) bar.style.width = pct + "%";
  }

  function phaseProgress(phaseId) {
    const steps = D.assembly.filter((s) => s.phase === phaseId);
    if (!steps.length) return 0;
    const done = steps.filter((s) => state.done[s.id]).length;
    return Math.round((100 * done) / steps.length);
  }

  /* ---------- Walk (primary visual) ---------- */
  function currentPhase() {
    return W.phases[Math.max(0, Math.min(state.walkIdx, W.phases.length - 1))];
  }

  function renderPhaseMap() {
    $("#phaseMap").innerHTML = W.phases
      .map((p, i) => {
        const pct = phaseProgress(p.id);
        const on = i === state.walkIdx ? " on" : "";
        const done = pct === 100 ? " done" : "";
        return `<button type="button" class="phase-card${on}${done}" data-walk="${i}">
          <span class="mono">${p.num}</span>
          <strong>${p.title}</strong>
          <small>${p.subtitle}</small>
          <i class="bar"><i style="width:${pct}%"></i></i>
          <em>${pct}%</em>
        </button>`;
      })
      .join("");
    $$("#phaseMap .phase-card").forEach((b) =>
      b.addEventListener("click", () => {
        state.walkIdx = parseInt(b.dataset.walk, 10);
        store.set("walkIdx", state.walkIdx);
        renderWalk();
      })
    );
  }

  function renderWalk() {
    const p = currentPhase();
    $("#walkNum").textContent = p.num;
    $("#walkTitle").textContent = p.title;
    $("#walkHero").textContent = p.hero;
    W.drawScene(p.viz, $("#walkStage"), { grayHex: state.drafts.grayHex });
    $("#walkHighlights").innerHTML = p.highlights
      .map(
        (h) =>
          `<div class="card stat"><span>${h.title}</span><b style="font-size:15px;line-height:1.35;font-family:var(--sans);font-weight:500">${h.body}</b></div>`
      )
      .join("");
    $("#walkSheets").innerHTML = p.sheets
      .map(
        (s) =>
          `<a class="sheet-chip" href="../plans/${s}" data-gallery="../plans/${s}" data-title="${s}">${s.replace(".svg", "")}</a>`
      )
      .join("");
    $$("#walkSheets .sheet-chip").forEach((a) =>
      a.addEventListener("click", (e) => {
        e.preventDefault();
        openLightbox(a.dataset.gallery, a.dataset.title);
      })
    );

    const steps = D.assembly.filter((s) => s.phase === p.id);
    $("#walkSteps").innerHTML = steps
      .map((s) => {
        const done = !!state.done[s.id];
        return `<div class="step${done ? " done" : ""}">
          <div class="num">${done ? "✓" : s.id.replace(/\D/g, "") || "·"}</div>
          <div><h3>${s.title}</h3><p>${s.body}</p></div>
          <button type="button" class="check" data-id="${s.id}" aria-label="Mark done"></button>
        </div>`;
      })
      .join("");
    $$("#walkSteps .check").forEach((b) =>
      b.addEventListener("click", () => {
        state.done[b.dataset.id] = !state.done[b.dataset.id];
        store.set("done", state.done);
        renderWalk();
        renderAssembly();
        refreshProgress();
      })
    );

    renderPhaseMap();
    $("#walkPrev").disabled = state.walkIdx === 0;
    $("#walkNext").disabled = state.walkIdx >= W.phases.length - 1;
  }

  function markPhaseDone() {
    const p = currentPhase();
    D.assembly
      .filter((s) => s.phase === p.id)
      .forEach((s) => {
        state.done[s.id] = true;
      });
    store.set("done", state.done);
    renderWalk();
    renderAssembly();
    refreshProgress();
    toast(p.title + " marked done");
  }

  /* ---------- Overview stats ---------- */
  function renderOverview() {
    const m = D.meta;
    $("#overviewStats").innerHTML = [
      ["Length", m.length + "″"],
      ["Height", m.height + "″"],
      ["Gate", m.gateClear + "″ clear"],
      ["Bay", m.bayClear + "″ each"],
      ["Mill buy", "≈ " + m.boardFeet + " bf"],
      ["Rev", m.rev + " · " + (m.species || "DF + oak")],
    ]
      .map(([k, v]) => `<div class="card stat"><span>${k}</span><b>${v}</b></div>`)
      .join("");
  }

  /* ---------- Visualizer (SVG) ---------- */
  function drawViz() {
    const stage = $("#vizStage");
    if (!stage) return;
    const L = D.meta.length;
    const H = D.meta.height;
    const gate = D.meta.gateClear;
    const explode = state.explode;
    const lift = explode * 28;
    const spread = explode * 18;
    const selected = state.selected;
    const gray = state.drafts.grayHex || "#6e7578";

    const S = 6.2;
    const padX = 40;
    const padY = 36;
    const Wsvg = padX * 2 + L * S + explode * 80;
    const VH = padY * 2 + (H + 24) * S + lift * 2;

    const yOf = (z) => padY + (H - z) * S + lift;
    const xOf = (x) => padX + x * S + spread;
    const dim = (id) =>
      selected && selected !== id ? " dim" : selected === id ? " hot" : "";

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
        return `<rect class="fence-part${dim("rails")}" data-part="rails" x="${x0}" y="${y - i * lift * 0.08}" width="${w}" height="${7.25 * S}" fill="${gray}" stroke="#1a1f24" stroke-width="1"/>`;
      })
      .join("");

    const cap = (() => {
      const x0 = xOf(41.25 - 1.75 - 0.75);
      const w = (141.25 + 1.75 + 0.75 - (41.25 - 1.75 - 0.75)) * S;
      return `<rect class="fence-part${dim("cap")}" data-part="cap" x="${x0}" y="${yOf(H) - lift * 0.4}" width="${w}" height="${1.5 * S}" fill="#8a9094" stroke="#1a1f24"/>`;
    })();

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

    stage.innerHTML = `<svg viewBox="0 0 ${Wsvg} ${VH}" role="img" aria-label="MARTIN fence visualization">
      <defs><filter id="glow"><feDropShadow dx="0" dy="0" stdDeviation="2.5" flood-color="#8fad78"/></filter></defs>
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
      $("#partDetail").innerHTML = `<strong>Select a part</strong><p>Click the model or the list to inspect.</p>`;
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
          <div><h3>${s.title}</h3><p><span class="mono" style="color:var(--sage-hi)">${s.phase}</span> · ${s.body}</p></div>
          <button type="button" class="check" aria-label="Mark done" data-id="${s.id}"></button>
        </div>`;
      })
      .join("");
    $$("#assemblyList .check").forEach((b) =>
      b.addEventListener("click", () => {
        state.done[b.dataset.id] = !state.done[b.dataset.id];
        store.set("done", state.done);
        renderAssembly();
        renderWalk();
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
    $("#bfTotal").textContent = "≈ " + total.toFixed(1) + " bf buy";
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
    const tolEl = $("#tolerancesList");
    if (tolEl && D.tolerances) {
      tolEl.innerHTML = D.tolerances
        .map((t) => `<li><strong>${t.item}</strong> — ${t.spec}</li>`)
        .join("");
    }
    const finEl = $("#finishedList");
    if (finEl && D.finished) {
      finEl.innerHTML = D.finished
        .map(
          (f) =>
            `<li><strong>${f.qty} × ${f.part}</strong> — <span class="mono">${f.size}</span> · ${f.note}</li>`
        )
        .join("");
    }
    const grainEl = $("#grainList");
    if (grainEl && D.grainRules) {
      grainEl.innerHTML = D.grainRules.map((g) => `<li>${g}</li>`).join("");
    }
  }

  function fmtSize(p) {
    const t = p.FINISHED_THICKNESS;
    const w = p.FINISHED_WIDTH;
    const l = p.FINISHED_LENGTH;
    if (!t && !w && !l) return "—";
    return `${t} × ${w} × ${l}`;
  }

  function renderRegistry() {
    if (!SSOT) {
      $("#registryBody").innerHTML = `<tr><td colspan="6">Loading martin.json…</td></tr>`;
      return;
    }
    const ly = SSOT.layout || {};
    const mat = SSOT.material || {};
    $("#ssotStats").innerHTML = [
      ["Rev", SSOT.project.REVISION],
      ["Parts", String(SSOT.parts.length)],
      ["Joints", String(SSOT.joints.length)],
      ["Post L", ly.post_finished_length + "″"],
      ["Nuki L", ly.nuki_length + "″"],
      ["Buy bf", String(mat.procurement_board_feet)],
    ]
      .map(([k, v]) => `<div class="card stat"><span>${k}</span><b>${v}</b></div>`)
      .join("");
    $("#registryBody").innerHTML = SSOT.parts
      .map(
        (p) => `<tr>
          <td class="mono">${p.PART_ID}</td>
          <td>${p.PART_NAME}</td>
          <td>${p.QUANTITY}</td>
          <td class="mono">${fmtSize(p)}</td>
          <td>${p.JOINERY || ""}</td>
          <td>${p.MAKE_OR_BUY}</td>
        </tr>`
      )
      .join("");
    $("#paramBody").innerHTML = Object.entries(SSOT.parameters)
      .map(([k, meta]) => {
        const val = Array.isArray(meta.value) ? meta.value.join(" / ") : meta.value;
        return `<tr><td class="mono">${k}</td><td>${val}</td><td>${meta.class}</td><td>${meta.note}</td></tr>`;
      })
      .join("");
  }

  function renderQA() {
    if (!SSOT) return;
    $("#gateList").innerHTML = Object.entries(SSOT.gates || {})
      .map(
        ([k, v]) =>
          `<div class="card"><span class="mono">${k}</span><p style="margin:6px 0 0;color:var(--dim)">${v}</p></div>`
      )
      .join("");
    $("#qcList").innerHTML = (SSOT.inspection || [])
      .map(
        (q) => `<div class="step">
          <div class="num">${q.QC.replace("QC-", "")}</div>
          <div><h3>${q.CHECK}</h3><p>${q.CRITERIA} · ${q.GATE} · ${q.CLASS}</p></div>
        </div>`
      )
      .join("");
    $("#decisionList").innerHTML = (SSOT.decisions || [])
      .map(
        (d) => `<article class="join" style="grid-template-columns:80px 1fr;margin-bottom:10px">
          <div class="glyph">${d.ID}</div>
          <div><h3>${d.DECISION}</h3><p style="margin:0;color:var(--dim);font-size:14px">${d.REASON}<br><span class="mono">${d.AFFECTED}</span></p></div>
        </article>`
      )
      .join("");
    $("#unresolvedList").innerHTML = (SSOT.unresolved || [])
      .map((u) => `<li><strong>${u.ID}</strong> ${u.ITEM} (${u.CLASS}) — ${u.ACTION}</li>`)
      .join("");
  }

  function renderJoinery() {
    const extra = SSOT
      ? SSOT.joints
          .map(
            (j) => `<article class="join">
          <div class="glyph">${j.JOINT_ID.replace("J-", "")}</div>
          <div>
            <h3>${j.JOINT_TYPE}</h3>
            <p class="hint" style="margin:0 0 6px">${j.PART_A} ↔ ${j.PART_B} · <span class="mono">${j.FIT_CLASS}</span></p>
            <p style="margin:0;color:var(--dim);font-size:14px">${j.LOCATION || ""} · ${j.TOOLING || ""}</p>
          </div>
        </article>`
          )
          .join("")
      : "";
    $("#joineryList").innerHTML =
      D.joinery
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
        .join("") + extra;
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
          `<a class="dl" href="${d.href}" ${d.href.match(/\.(FCStd|step|stl|py|svg|json|csv)$/) ? "download" : ""}>
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
    if (state.tab === "walk") renderWalk();
    if (state.tab === "viz") drawViz();
    toast("Drafts saved locally");
  }

  function exportDrafts() {
    const payload = {
      exportedAt: new Date().toISOString(),
      design: D.meta,
      drafts: state.drafts,
      assemblyDone: state.done,
      lumberBought: state.bought,
      walkPhase: currentPhase().id,
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
    $("#winterList").innerHTML = D.winter
      .map((w, i) => `<li><span class="mono">${i + 1}.</span> ${w}</li>`)
      .join("");
  }

  function renderFab(fab) {
    if (!fab || !$("#fabStats")) return;
    const nest = fab.nest || {};
    $("#fabStats").innerHTML = [
      ["Parts", fab.parts.length],
      ["Joints", fab.joints.length],
      ["Net bf", nest.net_bf],
      ["Buy bf", nest.procurement_bf],
      ["Concrete", (fab.concrete && fab.concrete.concrete_yd3) + " yd³"],
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
      })
      .catch(() => {
        const el = $("#fabStats");
        if (el) el.innerHTML = "<p class='hint'>fab.json not loaded — open the fabrication package folder.</p>";
      });
  }

  function init() {
    loadSSOT().then(() => {
      renderRegistry();
      renderQA();
      renderJoinery();
    });
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
    renderWalk();
    setTab(state.tab === "overview" ? "walk" : state.tab);

    $$(".tab, .mobile-nav button").forEach((b) =>
      b.addEventListener("click", () => setTab(b.dataset.tab))
    );
    $$("[data-tab-jump]").forEach((b) =>
      b.addEventListener("click", () => setTab(b.dataset.tabJump))
    );

    $("#explodeRange").addEventListener("input", (e) => {
      state.explode = parseFloat(e.target.value);
      store.set("explode", state.explode);
      $("#explodeVal").textContent = Math.round(state.explode * 100) + "%";
      drawViz();
    });
    $("#explodeRange").value = state.explode;
    $("#explodeVal").textContent = Math.round(state.explode * 100) + "%";
    $("#btnBreakdown").addEventListener("click", () => {
      $("#explodeRange").value = 0.55;
      $("#explodeRange").dispatchEvent(new Event("input"));
    });
    $("#btnAssembled").addEventListener("click", () => {
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

    $("#walkPrev").addEventListener("click", () => {
      state.walkIdx = Math.max(0, state.walkIdx - 1);
      store.set("walkIdx", state.walkIdx);
      renderWalk();
    });
    $("#walkNext").addEventListener("click", () => {
      state.walkIdx = Math.min(W.phases.length - 1, state.walkIdx + 1);
      store.set("walkIdx", state.walkIdx);
      renderWalk();
    });
    $("#walkMarkPhase").addEventListener("click", markPhaseDone);

    $("#saveDrafts").addEventListener("click", saveDrafts);
    $("#exportDrafts").addEventListener("click", exportDrafts);
    $("#resetProgress").addEventListener("click", () => {
      if (confirm("Reset assembly checklist?")) {
        state.done = {};
        store.set("done", state.done);
        renderAssembly();
        renderWalk();
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
