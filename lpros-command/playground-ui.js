/**
 * Agent playground UI — job board, launcher, browser, VM, live watch.
 */
const $ = (id) => document.getElementById(id);

const API_BASE = (() => {
  const { port, pathname } = location;
  if (port === "8790") return "/api";
  if (pathname.includes("/lpros-command")) return "/lpros-command/api";
  return "/lpros-command/api";
})();

async function api(path, opts = {}) {
  const r = await fetch(`${API_BASE}${path.replace(/^\/api/, "")}`, {
    method: opts.method || "GET",
    headers: opts.body ? { "Content-Type": "application/json" } : undefined,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || r.statusText);
  return j;
}

function esc(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

const COLS = ["queued", "running", "hold", "done", "failed"];
const pg = {
  jobs: [],
  catalog: { agents: [], playbooks: [], recipes: [], presets: [] },
  selected: null,
  session: null,
  agent: "brain",
  poll: null,
};

function formPayload(form) {
  const fd = new FormData(form);
  const o = {};
  for (const [k, v] of fd.entries()) {
    if (v === "" || v == null) continue;
    if (k === "dryRun") o.dryRun = true;
    else o[k] = v;
  }
  if (!fd.get("dryRun")) o.dryRun = false;
  if (o.spawn && typeof o.spawn === "string") {
    o.spawn = o.spawn
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
  }
  ["minPrice", "maxPrice", "price", "cost", "soldCount", "altProductCost"].forEach((k) => {
    if (o[k] != null && o[k] !== "") o[k] = Number(o[k]);
  });
  return o;
}

function fillForm(input = {}) {
  const form = $("pgLaunchForm");
  if (!form) return;
  for (const [k, v] of Object.entries(input)) {
    if (!form[k]) continue;
    if (form[k].type === "checkbox") form[k].checked = Boolean(v);
    else form[k].value = Array.isArray(v) ? v.join(",") : v;
  }
}

function renderStats(summary) {
  const el = $("pgStats");
  if (!el) return;
  const s = summary?.byStatus || {};
  const cells = [
    ["Total", summary?.total ?? 0, "jobs"],
    ["Queued", s.queued || 0, "ready"],
    ["Running", s.running || 0, "live"],
    ["Done", s.done || 0, "complete"],
    ["Failed", s.failed || 0, "errors"],
    ["Hold", s.hold || 0, "paused"],
  ];
  el.innerHTML = cells
    .map(([k, v, sub]) => `<div class="stat"><span>${k}</span><b>${v}</b><em>${sub}</em></div>`)
    .join("");
  const kpi = $("kpiPlay");
  if (kpi) kpi.textContent = String(summary?.total ?? "—");
}

function renderKanban(jobs) {
  const host = $("pgKanban");
  if (!host) return;
  const groups = Object.fromEntries(COLS.map((c) => [c, []]));
  for (const j of jobs || []) {
    const st = groups[j.status] ? j.status : "failed";
    groups[st].push(j);
  }
  host.innerHTML = COLS.map((col) => {
    const cards = (groups[col] || [])
      .map(
        (j) => `<button type="button" class="pg-card${pg.selected === j.id ? " on" : ""}" draggable="true" data-id="${esc(j.id)}">
        <b>${esc(j.agent || j.kind)} · ${esc(j.priority || "P1")}</b>
        <small>${esc(j.title || j.id)}</small>
        <small>${esc(j.verdict || j.status)} · ${(j.children || []).length} kids</small>
      </button>`
      )
      .join("");
    return `<div class="pg-col" data-col="${col}"><h3>${col} (${(groups[col] || []).length})</h3>${cards || `<p class="muted">empty</p>`}</div>`;
  }).join("");

  host.querySelectorAll(".pg-card").forEach((card) => {
    card.onclick = () => inspectJob(card.dataset.id);
    card.addEventListener("dragstart", (e) => e.dataTransfer.setData("text/plain", card.dataset.id));
  });
  host.querySelectorAll(".pg-col").forEach((col) => {
    col.addEventListener("dragover", (e) => {
      e.preventDefault();
      col.classList.add("drop");
    });
    col.addEventListener("dragleave", () => col.classList.remove("drop"));
    col.addEventListener("drop", async (e) => {
      e.preventDefault();
      col.classList.remove("drop");
      const id = e.dataTransfer.getData("text/plain");
      const status = col.dataset.col;
      if (!id || !["queued", "hold"].includes(status)) return;
      try {
        await api(`/playground/jobs/${encodeURIComponent(id)}/status`, { method: "POST", body: { status } });
        await refreshBoard();
      } catch (err) {
        $("pgJobOut").textContent = String(err.message || err);
      }
    });
  });
}

function renderCatalog(agents) {
  const host = $("pgCatalog");
  const sel = $("pgAgent");
  if (sel) {
    sel.innerHTML = (agents || []).map((a) => `<option value="${esc(a.id)}">${esc(a.id)}</option>`).join("");
    sel.value = pg.agent;
  }
  if (!host) return;
  host.innerHTML = (agents || [])
    .map(
      (a) => `<button type="button" class="pg-agent${pg.agent === a.id ? " on" : ""}" data-id="${esc(a.id)}">
        ${esc(a.title)}<span>${esc(a.role)}</span></button>`
    )
    .join("");
  host.querySelectorAll(".pg-agent").forEach((btn) => {
    btn.onclick = () => {
      pg.agent = btn.dataset.id;
      if (sel) sel.value = pg.agent;
      host.querySelectorAll(".pg-agent").forEach((b) => b.classList.toggle("on", b === btn));
    };
  });
}

function renderPresets(presets) {
  const host = $("pgPresets");
  if (!host) return;
  host.innerHTML = (presets || [])
    .map((p) => `<button type="button" class="chip" data-preset="${esc(p.id)}">${esc(p.title)}</button>`)
    .join("");
  host.querySelectorAll(".chip").forEach((b) => {
    b.onclick = () => applyPreset(b.dataset.preset);
  });
}

function applyPreset(id) {
  const p = (pg.catalog.presets || []).find((x) => x.id === id);
  if (!p) return;
  pg.agent = p.agent;
  fillForm({ agent: p.agent, dryRun: p.dryRun, spawn: p.spawn, ...(p.input || {}) });
  renderCatalog(pg.catalog.agents);
}

function renderPlaybooks(playbooks) {
  const html = (playbooks || []).map((p) => `<option value="${esc(p.id)}">${esc(p.id)}</option>`).join("");
  ["pgPlaybook", "pgBrowserPlaybook"].forEach((id) => {
    const el = $(id);
    if (el) el.innerHTML = html;
  });
}

function renderRecipes(recipes) {
  const host = $("pgVmRecipes");
  if (!host) return;
  host.innerHTML = (recipes || [])
    .map((r) => `<button type="button" class="chip" data-recipe="${esc(r.id)}">${esc(r.title)}</button>`)
    .join("");
  host.querySelectorAll(".chip").forEach((b) => {
    b.onclick = () => runVm(b.dataset.recipe);
  });
}

function renderVmSnap(snap) {
  const el = $("pgVmSnap");
  if (!el || !snap) return;
  el.innerHTML = [
    ["Node", snap.node],
    ["CPUs", snap.cpus],
    ["Mem", `${snap.memory?.usedPct}%`],
    ["Host", snap.hostname],
    ["Serverless", snap.serverless ? "yes" : "no"],
    ["eBay env", snap.ebayEnvSet ? "set" : "—"],
  ]
    .map(([k, v]) => `<div class="stat"><span>${k}</span><b>${esc(v)}</b></div>`)
    .join("");
}

function renderBrowser(session, snapshot) {
  const steps = $("pgBrowserSteps");
  const view = $("pgBrowserView");
  if (session && steps) {
    steps.innerHTML = (session.steps || [])
      .map((s, i) => {
        const cls = s.done ? "done" : i === session.stepIndex ? "now" : "";
        return `<div class="pg-step ${cls}">${i + 1}. ${esc(s.label)}</div>`;
      })
      .join("");
  }
  if (view) {
    if (snapshot) {
      view.innerHTML = `<h3>${esc(snapshot.title || snapshot.url)}</h3>
        <p class="sub">${esc(snapshot.mode || "")} · ${esc(snapshot.url || "")}</p>
        ${snapshot.image ? `<img class="thumb" src="${esc(snapshot.image)}" alt="" />` : ""}
        <p>${esc(snapshot.excerpt || snapshot.descriptionExcerpt || "")}</p>`;
    } else if (session) {
      view.innerHTML = `<p class="sub">Session ${esc(session.id)} · playbook ${esc(session.playbookId)}</p>`;
    }
  }
}

function renderGraph(tree) {
  const svg = $("pgGraph");
  if (!svg) return;
  if (!tree?.job) {
    svg.innerHTML = `<text x="12" y="24" fill="#8a9a8c" font-size="11">Select a job with children</text>`;
    return;
  }
  const kids = tree.children || [];
  const parent = tree.job;
  let html = `<rect x="150" y="16" width="120" height="36" fill="#c4f542" rx="2"/>
    <text x="160" y="38" font-size="11">${esc((parent.agent || parent.kind).slice(0, 14))}</text>`;
  kids.forEach((c, i) => {
    const x = 20 + i * 80;
    html += `<line x1="210" y1="52" x2="${x + 30}" y2="88" stroke="#2a332c"/>
      <rect class="pg-graph-node" data-id="${esc(c.id)}" x="${x}" y="88" width="70" height="32" fill="#161c18" stroke="#c4f542"/>
      <text x="${x + 6}" y="108" fill="#e8efe6" font-size="10">${esc((c.agent || "").slice(0, 8))}</text>`;
  });
  svg.innerHTML = html;
  svg.querySelectorAll("[data-id]").forEach((n) => {
    n.addEventListener("click", () => inspectJob(n.getAttribute("data-id")));
  });
}

function renderActivity(events) {
  const el = $("pgActivity");
  if (!el) return;
  el.innerHTML = (events || [])
    .slice(0, 24)
    .map(
      (e) =>
        `<div><b>${esc(e.agent || "")}</b> ${esc(e.message)} <span>${esc((e.at || "").slice(11, 19))}</span></div>`
    )
    .join("") || `<p class="muted">No events yet.</p>`;
}

function renderLog(events) {
  const el = $("pgJobLog");
  if (!el) return;
  el.textContent = (events || [])
    .map((e) => `${(e.at || "").slice(11, 19)} [${e.level}] ${e.message}`)
    .join("\n");
  el.scrollTop = el.scrollHeight;
}

async function inspectJob(id) {
  pg.selected = id;
  const job = await api(`/playground/jobs/${encodeURIComponent(id)}`);
  $("pgJobTitle").textContent = `${job.agent || job.kind} · ${job.status} · ${job.title}`;
  renderLog(job.events);
  $("pgJobOut").textContent = JSON.stringify(
    {
      id: job.id,
      status: job.status,
      children: job.children,
      progress: job.progress,
      error: job.error,
      brief: job.result?.brief,
      promoted: job.result?.promoted,
      productCount: job.result?.productCount,
      emptyReason: job.result?.emptyReason,
      result: job.result,
    },
    null,
    2
  );
  if (
    job.status === "done" &&
    !job.input?.dryRun &&
    !job.result?.dryRun &&
    (job.result?.productCount ||
      job.result?.products?.length ||
      job.result?.items?.length ||
      job.result?.lethalCandidates?.length) &&
    typeof window.hydrateMarketFromResearch === "function"
  ) {
    window.hydrateMarketFromResearch(job.result || {}, { status: job.status });
  }
  const verdict = job.result?.brief?.verdict || job.result?.decision;
  const actions = $("pgJobActions");
  actions.innerHTML = `
    <button type="button" class="btn primary" data-act="start">Start</button>
    <button type="button" class="btn" data-act="retry">Retry</button>
    <button type="button" class="btn ghost" data-act="cancel">Cancel</button>
    <button type="button" class="btn ghost" data-act="hold">Hold</button>
    ${verdict === "PASS_READY" || verdict === "PASS" ? `<button type="button" class="btn primary" data-act="promote">Promote SKU</button>` : ""}
  `;
  actions.querySelectorAll("button").forEach((b) => {
    b.onclick = async () => {
      try {
        const sync = true;
        if (b.dataset.act === "start") await api(`/playground/jobs/${id}/start`, { method: "POST", body: { sync } });
        if (b.dataset.act === "retry") await api(`/playground/jobs/${id}/retry`, { method: "POST", body: { sync } });
        if (b.dataset.act === "cancel") await api(`/playground/jobs/${id}/cancel`, { method: "POST", body: {} });
        if (b.dataset.act === "hold") await api(`/playground/jobs/${id}/status`, { method: "POST", body: { status: "hold" } });
        if (b.dataset.act === "promote") {
          const out = await api(`/playground/jobs/${id}/promote`, { method: "POST", body: {} });
          $("pgJobOut").textContent = JSON.stringify(out, null, 2);
        }
        await refreshBoard();
        await inspectJob(id);
      } catch (e) {
        $("pgJobOut").textContent = String(e.message || e);
      }
    };
  });
  document.querySelectorAll(".pg-card").forEach((c) => c.classList.toggle("on", c.dataset.id === id));
  try {
    renderGraph(await api(`/playground/jobs/${encodeURIComponent(id)}/tree`));
  } catch {
    /* ignore */
  }
}

function watchIfNeeded(jobs) {
  const busy = (jobs || []).some((j) => j.status === "running" || j.status === "queued");
  if (busy && !pg.poll) {
    pg.poll = setInterval(() => {
      refreshBoard().catch(() => {});
      if (pg.selected) inspectJob(pg.selected).catch(() => {});
    }, 1400);
  }
  if (!busy && pg.poll) {
    clearInterval(pg.poll);
    pg.poll = null;
  }
}

async function refreshBoard() {
  const data = await api("/playground/jobs?limit=80");
  pg.jobs = data.jobs || [];
  renderStats(data.summary);
  renderKanban(pg.jobs);
  watchIfNeeded(pg.jobs);
  try {
    const act = await api("/playground/activity?limit=30");
    renderActivity(act.events);
  } catch {
    /* ignore */
  }
}

async function launch(start) {
  const form = $("pgLaunchForm");
  const p = formPayload(form);
  p.agent = p.agent || pg.agent;
  pg.agent = p.agent;
  const live = !p.dryRun;
  try {
    if (start) {
      const body = { ...p, input: p, agent: p.agent, dryRun: p.dryRun, spawn: p.spawn, sync: true };
      const out = await api("/playground/launch", { method: "POST", body });
      $("pgJobOut").textContent = JSON.stringify(out, null, 2);
      $("pgJobTitle").textContent = `${out.agent} · ${out.status}`;
      pg.selected = out.jobId;
      if (live && typeof window.hydrateMarketFromResearch === "function") {
        window.hydrateMarketFromResearch(out.market || out.result || out, { dryRun: out.dryRun });
        if (out.productCount) window.showTab?.("market");
      } else if (out.dryRun && typeof window.hydrateMarketFromResearch === "function") {
        window.hydrateMarketFromResearch({ products: [], dryRun: true, emptyReason: out.emptyReason });
      }
    } else {
      const out = await api("/playground/jobs", {
        method: "POST",
        body: { agent: p.agent, title: `${p.agent} ${p.q || p.recipe || ""}`, priority: p.priority, input: p },
      });
      pg.selected = out.job?.id;
    }
    await refreshBoard();
    if (pg.selected) await inspectJob(pg.selected);
  } catch (e) {
    $("pgJobOut").textContent = String(e.message || e);
  }
}

async function runVm(recipe) {
  $("pgVmOut").textContent = `Running ${recipe}…`;
  try {
    const out = await api("/playground/vm/exec", { method: "POST", body: { recipe } });
    $("pgVmOut").textContent = JSON.stringify(out.run, null, 2);
    const runs = await api("/playground/vm/runs");
    const host = $("pgVmRuns");
    if (host) {
      host.innerHTML = (runs.runs || [])
        .slice(0, 6)
        .map((r) => `<article class="card-row"><div><h3>${esc(r.recipe)}</h3><div class="meta"><span>${esc(r.status)}</span><span>${r.ms}ms</span></div></div></article>`)
        .join("");
    }
  } catch (e) {
    $("pgVmOut").textContent = String(e.message || e);
  }
}

async function refreshSessions() {
  const host = $("pgSessions");
  if (!host) return;
  try {
    const data = await api("/playground/browser/sessions");
    host.innerHTML = (data.sessions || [])
      .slice(0, 8)
      .map((s) => `<button type="button" class="chip" data-sid="${esc(s.id)}">${esc(s.playbookId)} · ${esc(s.id.slice(-6))}</button>`)
      .join("");
    host.querySelectorAll(".chip").forEach((b) => {
      b.onclick = async () => {
        const out = await api(`/playground/browser/sessions/${b.dataset.sid}`);
        pg.session = out.session;
        renderBrowser(pg.session);
      };
    });
  } catch {
    /* ignore */
  }
}

export async function bootPlayground() {
  if (!$("tab-playground")) return;
  try {
    const cat = await api("/playground/catalog");
    pg.catalog = cat;
    renderCatalog(cat.agents);
    renderPlaybooks(cat.playbooks);
    renderRecipes(cat.recipes);
    renderPresets(cat.presets);
  } catch {
    /* desk may boot before API */
  }
  try {
    const vm = await api("/playground/vm");
    renderVmSnap(vm);
  } catch {
    /* ignore */
  }
  try {
    await refreshBoard();
    await refreshSessions();
  } catch {
    /* ignore */
  }

  $("pgLaunchBtn")?.addEventListener("click", () => launch(true));
  $("pgCreateBtn")?.addEventListener("click", () => launch(false));
  $("pgRefresh")?.addEventListener("click", () => refreshBoard());
  $("pgLiveResearch")?.addEventListener("click", async () => {
    const form = $("pgLaunchForm");
    if (form?.dryRun) form.dryRun.checked = false;
    const p = formPayload(form);
    if (typeof window.runLiveResearch === "function") {
      try {
        await window.runLiveResearch(p);
        window.showTab?.("market");
      } catch (e) {
        $("pgJobOut").textContent = String(e.message || e);
      }
    } else {
      applyPreset("live-intel");
      await launch(true);
    }
  });
  $("pgDryBrain")?.addEventListener("click", async () => {
    applyPreset("dry-brain");
    await launch(true);
  });
  $("pgAgent")?.addEventListener("change", (e) => {
    pg.agent = e.target.value;
    renderCatalog(pg.catalog.agents);
  });

  $("pgBrowserForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      const out = await api("/playground/browser/sessions", {
        method: "POST",
        body: { playbookId: fd.get("playbookId"), url: fd.get("url") },
      });
      pg.session = out.session;
      renderBrowser(pg.session);
      await api("/playground/jobs", {
        method: "POST",
        body: {
          agent: "browser",
          kind: "browser",
          title: `browser ${fd.get("playbookId")}`,
          input: { playbookId: fd.get("playbookId"), url: fd.get("url") },
        },
      });
      await refreshBoard();
      await refreshSessions();
    } catch (err) {
      $("pgBrowserView").textContent = String(err.message || err);
    }
  });
  $("pgBrowserFetch")?.addEventListener("click", async () => {
    const url = $("pgBrowserForm").url.value;
    try {
      const out = await api("/playground/browser/fetch", {
        method: "POST",
        body: { url, sessionId: pg.session?.id },
      });
      renderBrowser(pg.session, out.snapshot);
    } catch (err) {
      $("pgBrowserView").textContent = String(err.message || err);
    }
  });
  $("pgCaptureForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!pg.session) return;
    const fd = new FormData(e.target);
    const capture = {};
    for (const [k, v] of fd.entries()) if (v) capture[k] = Number(v) || v;
    try {
      const out = await api(`/playground/browser/sessions/${pg.session.id}/advance`, {
        method: "POST",
        body: { capture },
      });
      pg.session = out.session;
      renderBrowser(pg.session);
      fillForm(capture);
    } catch (err) {
      $("pgBrowserView").textContent = String(err.message || err);
    }
  });
  $("pgApplyEvidence")?.addEventListener("click", async () => {
    if (!pg.session) return;
    const p = formPayload($("pgLaunchForm"));
    try {
      const out = await api(`/playground/browser/sessions/${pg.session.id}/apply`, {
        method: "POST",
        body: { q: p.q, title: p.q, salePrice: p.price, relaunchBrain: true },
      });
      $("pgJobOut").textContent = JSON.stringify(
        {
          capture: out.capture,
          evidence: out.evidence?.result?.decision,
          brain: out.brain?.result?.brief?.verdict,
        },
        null,
        2
      );
      pg.selected = out.brain?.id || out.evidence?.id;
      await refreshBoard();
      if (pg.selected) await inspectJob(pg.selected);
    } catch (err) {
      $("pgJobOut").textContent = String(err.message || err);
    }
  });
  $("pgCommentForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!pg.selected) return;
    const text = new FormData(e.target).get("text");
    try {
      await api(`/playground/jobs/${pg.selected}/comment`, { method: "POST", body: { text } });
      e.target.reset();
      await inspectJob(pg.selected);
    } catch (err) {
      $("pgJobOut").textContent = String(err.message || err);
    }
  });
}
