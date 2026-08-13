/**
 * Side-by-side research VM — polls ticks so you watch Browse + getItem land live.
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

const watch = {
  session: null,
  looping: false,
};

function formPayload() {
  const form = $("watchForm");
  if (!form) return {};
  const fd = new FormData(form);
  const o = {};
  for (const [k, v] of fd.entries()) {
    if (v === "" || v == null) continue;
    o[k] = v;
  }
  ["minPrice", "maxPrice", "limit", "detailCount"].forEach((k) => {
    if (o[k] != null) o[k] = Number(o[k]);
  });
  return o;
}

function fillWatchForm(p = {}) {
  const form = $("watchForm");
  if (!form) return;
  for (const [k, v] of Object.entries(p)) {
    if (form[k] && v != null) form[k].value = v;
  }
}

function renderProof(s) {
  const el = $("watchProof");
  if (!el) return;
  const p = s?.proof || {};
  const chips = [
    ["source", p.source || "—", p.source === "ebay_browse"],
    ["env", p.env || "—", p.appConfigured],
    ["dryRun", p.dryRun ? "YES (fake)" : "no — live API", !p.dryRun],
    ["host", p.hostname || "—", true],
    ["pid", p.pid || "—", true],
  ];
  el.innerHTML = chips
    .map(([k, v, ok]) => `<span class="${ok ? "live" : "warn"}">${esc(k)} ${esc(v)}</span>`)
    .join("");
}

function renderLog(s) {
  const el = $("watchLog");
  if (!el) return;
  el.textContent = (s?.events || [])
    .map((e) => `${(e.at || "").slice(11, 19)} [${e.phase || ""}] ${e.message}`)
    .join("\n");
  el.scrollTop = el.scrollHeight;
}

function renderCalls(s) {
  const el = $("watchCalls");
  if (!el) return;
  el.innerHTML = (s?.apiCalls || [])
    .slice(-8)
    .reverse()
    .map(
      (c) =>
        `<div><b>${esc(c.method)}</b> ${esc(c.path)} <span>${c.status ?? "…"}</span>${
          c.sample != null ? ` · ${c.sample} items` : ""
        }</div>`
    )
    .join("");
}

function renderHero(item) {
  const el = $("watchHero");
  if (!el) return;
  if (!item) {
    el.className = "vm-hero idle";
    el.innerHTML = `<p class="muted">Waiting for live listings…</p>`;
    return;
  }
  el.className = "vm-hero";
  const img = item.image ? `<img src="${esc(item.image)}" alt="" />` : `<div class="ph"></div>`;
  el.innerHTML = `${img}
    <div>
      <h3>${esc((item.title || "").slice(0, 110))}</h3>
      <div class="meta">
        <span><b>$${Number(item.price || item.salePrice || 0).toFixed(2)}</b></span>
        <span>${item.detailFetched ? "getItem" : "search"}</span>
        <span>${esc(item.seller || "")}</span>
        <span>${item.imageCount || 0} imgs</span>
      </div>
      <p class="sub">${esc((item.descriptionExcerpt || item.specificsSummary || "Listing knowledge lands after getItem.").slice(0, 280))}</p>
      ${item.url ? `<a class="btn ghost" href="${esc(item.url)}" target="_blank" rel="noopener">Open eBay listing</a>` : ""}
    </div>`;
}

function renderGallery(s) {
  const el = $("watchGallery");
  if (!el) return;
  const rows = s?.products || [];
  const cur = s?.current?.itemId || s?.current?.id;
  el.innerHTML = rows
    .slice(0, 36)
    .map((p) => {
      const id = p.itemId || p.id || p.title;
      const on = cur && (p.itemId === cur || p.id === cur) ? " on" : "";
      return `<button type="button" class="${on}" data-id="${esc(id)}" title="${esc(p.title || "")}">
        ${p.image ? `<img src="${esc(p.image)}" alt="" loading="lazy" />` : `<div class="ph"></div>`}
        <small>$${Number(p.price || 0).toFixed(0)}</small>
      </button>`;
    })
    .join("");
  el.querySelectorAll("button").forEach((btn) => {
    btn.onclick = () => {
      const item = rows.find((p) => (p.itemId || p.id || p.title) === btn.dataset.id);
      if (item) renderHero(item);
    };
  });
}

export function renderWatch(s) {
  watch.session = s;
  const running = s?.status === "running";
  const badge = $("vmBadge");
  if (badge) {
    badge.textContent = running ? "LIVE BROWSE" : (s?.status || "STANDBY").toUpperCase();
    badge.className = `vm-badge${running ? " live" : s?.status === "failed" ? " fail" : ""}`;
  }
  const title = $("vmTitle");
  if (title) {
    const vm = s?.vm || {};
    title.textContent = `${vm.hostname || "research-vm"} · ${vm.node || ""} · pid ${vm.pid || "—"}`;
  }
  const st = $("vmStatus");
  if (st) {
    const last = (s?.apiCalls || []).at(-1);
    st.textContent = last
      ? `${last.method} ${last.path} · ${last.status ?? "in flight"} · ${s.productCount ?? 0} products`
      : s?.status === "running"
        ? `phase ${s.phase}`
        : "Waiting for a session";
  }
  const phase = $("watchPhaseLabel");
  if (phase) {
    phase.textContent = s
      ? `${s.phase} · ${s.productCount || 0} products · ${s.productsWithImages || 0} images · ${s.productsWithUrls || 0} URLs`
      : "Idle — VM not running";
  }
  const bar = $("watchPct");
  if (bar) bar.style.width = `${s?.progress?.pct || 0}%`;
  const kpi = $("kpiWatch");
  if (kpi) kpi.textContent = s?.status === "running" ? s.phase : s?.status || "idle";
  const orch = $("orchPhase");
  if (orch && s) orch.textContent = `watch ${s.phase} · ${s.progress?.pct || 0}%`;
  renderProof(s);
  renderLog(s);
  renderCalls(s);
  renderHero(s?.current);
  renderGallery(s);
}

async function loopTicks() {
  if (watch.looping) return;
  watch.looping = true;
  try {
    while (watch.session?.status === "running" && watch.session?.id) {
      const next = await api(`/research/watch/${encodeURIComponent(watch.session.id)}/tick`, {
        method: "POST",
        body: { n: 1 },
      });
      renderWatch(next);
      if (typeof window.hydrateMarketFromResearch === "function" && (next.products || []).length) {
        window.hydrateMarketFromResearch(next, { status: next.status });
      }
      if (next.status !== "running") break;
      await new Promise((r) => setTimeout(r, next.phase === "search" ? 80 : 280));
    }
    if (watch.session?.status === "done") {
      if (typeof window.hydrateMarketFromResearch === "function") {
        window.hydrateMarketFromResearch(watch.session, { status: "live" });
      }
      const b = $("deskBanner");
      if (b) {
        b.hidden = false;
        b.className = "desk-banner ok";
        b.textContent = `${watch.session.productCount} live products · ${watch.session.productsWithImages} images · ${watch.session.productsWithUrls} URLs (Watch VM)`;
      }
    }
  } catch (e) {
    const log = $("watchLog");
    if (log) log.textContent += `\nERROR ${e.message || e}`;
    const badge = $("vmBadge");
    if (badge) {
      badge.textContent = "FAILED";
      badge.className = "vm-badge fail";
    }
  } finally {
    watch.looping = false;
  }
}

export async function startResearchWatch(payload) {
  const p = payload || formPayload();
  fillWatchForm(p);
  window.showTab?.("watch");
  if ($("watchLog")) $("watchLog").textContent = "Booting research VM…";
  if ($("vmBadge")) {
    $("vmBadge").textContent = "BOOT";
    $("vmBadge").className = "vm-badge live";
  }
  const session = await api("/research/watch", { method: "POST", body: p });
  renderWatch(session);
  loopTicks();
  return session;
}

export async function bootWatch() {
  if (!$("tab-watch")) return;
  $("watchStartBtn")?.addEventListener("click", () => {
    startResearchWatch(formPayload()).catch((e) => {
      if ($("watchLog")) $("watchLog").textContent = String(e.message || e);
    });
  });
  $("watchCancelBtn")?.addEventListener("click", async () => {
    if (!watch.session?.id) return;
    try {
      renderWatch(await api(`/research/watch/${watch.session.id}/cancel`, { method: "POST", body: {} }));
    } catch (e) {
      if ($("watchLog")) $("watchLog").textContent = String(e.message || e);
    }
  });
  $("watchToMarket")?.addEventListener("click", () => window.showTab?.("market"));
  try {
    const data = await api("/research/watch");
    const last = (data.sessions || [])[0];
    if (last) renderWatch(last);
  } catch {
    /* empty */
  }
}

window.startResearchWatch = startResearchWatch;
window.renderWatch = renderWatch;
