/**
 * Agent playground UI — job board, launcher, browser, VM.
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
  catalog: { agents: [], playbooks: [], recipes: [] },
  selected: null,
  session: null,
  agent: "brain",
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
  groups.cancelled = [];
  for (const j of jobs || []) {
    const st = groups[j.status] ? j.status : "failed";
    (groups[st] || groups.failed).push(j);
  }
  host.innerHTML = COLS.map((col) => {
    const cards = (groups[col] || [])
      .map(
        (j) => `<button type="button" class="pg-card${pg.selected === j.id ? " on" : ""}" draggable="true" data-id="${esc(j.id)}" data-status="${esc(j.status)}">
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
    card.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", card.dataset.id);
    });
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
        await api(`/playground/jobs/${encodeURIComponent(id)}/status`, {
          method: "POST",
          body: { status },
        });
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
    sel.innerHTML = (agents || [])
      .map((a) => `<option value="${esc(a.id)}">${esc(a.id)}</option>`)
      .join("");
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

async function inspectJob(id) {
  pg.selected = id;
  const job = await api(`/playground/jobs/${encodeURIComponent(id)}`);
  $("pgJobTitle").textContent = `${job.agent || job.kind} · ${job.status} · ${job.title}`;
  $("pgJobOut").textContent = JSON.stringify(
    {
      id: job.id,
      status: job.status,
      children: job.children,
      progress: job.progress,
      error: job.error,
      brief: job.result?.brief,
      result: job.result,
      events: (job.events || []).slice(-12),
    },
    null,
    2
  );
  const actions = $("pgJobActions");
  actions.innerHTML = `
    <button type="button" class="btn primary" data-act="start">Start</button>
    <button type="button" class="btn" data-act="retry">Retry</button>
    <button type="button" class="btn ghost" data-act="cancel">Cancel</button>
    <button type="button" class="btn ghost" data-act="hold">Hold</button>
  `;
  actions.querySelectorAll("button").forEach((b) => {
    b.onclick = async () => {
      try {
        if (b.dataset.act === "start") await api(`/playground/jobs/${id}/start`, { method: "POST", body: { sync: true } });
        if (b.dataset.act === "retry") await api(`/playground/jobs/${id}/retry`, { method: "POST", body: { sync: true } });
        if (b.dataset.act === "cancel") await api(`/playground/jobs/${id}/cancel`, { method: "POST", body: {} });
        if (b.dataset.act === "hold") await api(`/playground/jobs/${id}/status`, { method: "POST", body: { status: "hold" } });
        await refreshBoard();
        await inspectJob(id);
      } catch (e) {
        $("pgJobOut").textContent = String(e.message || e);
      }
    };
  });
  document.querySelectorAll(".pg-card").forEach((c) => c.classList.toggle("on", c.dataset.id === id));
}

async function refreshBoard() {
  const data = await api("/playground/jobs?limit=80");
  pg.jobs = data.jobs || [];
  renderStats(data.summary);
  renderKanban(pg.jobs);
}

async function launch(start) {
  const form = $("pgLaunchForm");
  const p = formPayload(form);
  p.agent = p.agent || pg.agent;
  pg.agent = p.agent;
  try {
    if (start) {
      const body = { ...p, input: p, agent: p.agent, dryRun: p.dryRun, spawn: p.spawn };
      const out = await api("/playground/launch", { method: "POST", body });
      $("pgJobOut").textContent = JSON.stringify(out, null, 2);
      $("pgJobTitle").textContent = `${out.agent} · ${out.status}`;
      pg.selected = out.jobId;
    } else {
      const out = await api("/playground/jobs", {
        method: "POST",
        body: { agent: p.agent, title: `${p.agent} ${p.q || p.recipe || ""}`, priority: p.priority, input: p },
      });
      pg.selected = out.job?.id;
    }
    await refreshBoard();
  } catch (e) {
    $("pgJobOut").textContent = String(e.message || e);
  }
}

async function runVm(recipe) {
  $("pgVmOut").textContent = `Running ${recipe}…`;
  try {
    const out = await api("/playground/vm/exec", { method: "POST", body: { recipe } });
    $("pgVmOut").textContent = JSON.stringify(out.run, null, 2);
  } catch (e) {
    $("pgVmOut").textContent = String(e.message || e);
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
  } catch {
    /* ignore */
  }

  $("pgLaunchBtn")?.addEventListener("click", () => launch(true));
  $("pgCreateBtn")?.addEventListener("click", () => launch(false));
  $("pgRefresh")?.addEventListener("click", () => refreshBoard());
  $("pgDryBrain")?.addEventListener("click", async () => {
    $("pgAgent").value = "brain";
    pg.agent = "brain";
    $("pgLaunchForm").dryRun.checked = true;
    $("pgLaunchForm").spawn.value = "scout,intel,economics";
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
    } catch (err) {
      $("pgBrowserView").textContent = String(err.message || err);
    }
  });
}
