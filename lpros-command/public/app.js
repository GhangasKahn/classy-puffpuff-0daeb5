import { bootPlayground } from "./playground-ui.js";
import { bootWatch, startResearchWatch } from "./watch-ui.js";
import { bindDeskLayout } from "./layout.js";

const $ = (id) => document.getElementById(id);

/** Local :8790 uses /api; Netlify uses /lpros-command/api */
const API_BASE = (() => {
  const { port, pathname } = location;
  if (port === "8790") return "/api";
  if (pathname.includes("/lpros-command")) return "/lpros-command/api";
  return "/lpros-command/api";
})();

async function post(path, body) {
  const r = await fetch(`${API_BASE}${path.replace(/^\/api/, "")}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const j = await r.json();
  if (!r.ok) throw new Error(j.error || r.statusText);
  return j;
}

async function get(path) {
  const r = await fetch(`${API_BASE}${path.replace(/^\/api/, "")}`);
  const j = await r.json();
  if (!r.ok) throw new Error(j.error || r.statusText);
  return j;
}

const desk = {
  products: [],
  packages: [],
  trends: null,
  intel: null,
  lanes: [],
  ideas: [],
  variants: [],
  jobs: [],
  compare: [],
  lastInspect: null,
  view: "split",
  filter: { q: "", cat: "", hasImg: false, sort: "price", min: null, max: null },
};

function showTab(name) {
  document.querySelectorAll(".tab").forEach((el) => el.classList.toggle("on", el.id === `tab-${name}`));
  document.querySelectorAll(".rail-btn").forEach((b) => b.classList.toggle("on", b.dataset.tab === name));
}
window.showTab = showTab;

function setKpis({ products, images, variants, ideas, packages, heat, skus } = {}) {
  const set = (id, v) => {
    const el = $(id);
    if (el) el.textContent = v == null || v === "" ? "—" : String(v);
  };
  if (products != null) set("kpiProducts", products);
  if (images != null) set("kpiImages", images);
  if (variants != null) set("kpiVariants", variants);
  if (ideas != null) set("kpiIdeas", ideas);
  if (packages != null) set("kpiPackages", packages);
  if (heat != null) set("kpiHeat", heat);
  if (skus != null) set("kpiSkus", skus);
}

function tipShow(ev, html) {
  const el = $("tip");
  if (!el) return;
  el.hidden = false;
  el.innerHTML = html;
  el.style.left = `${Math.min(window.innerWidth - 280, ev.clientX + 12)}px`;
  el.style.top = `${Math.min(window.innerHeight - 80, ev.clientY + 12)}px`;
}
function tipHide() {
  const el = $("tip");
  if (el) el.hidden = true;
}

function openInspector(item) {
  const box = $("inspector");
  const body = $("inspBody");
  if (!box || !body || !item) return;
  box.hidden = false;
  desk.lastInspect = item;
  const imgs = (item.images || []).filter(Boolean);
  if (item.image && !imgs.includes(item.image)) imgs.unshift(item.image);
  const hero = imgs[0] || "";
  body.innerHTML = `
    ${hero ? `<img class="insp-hero" id="inspHero" src="${escapeHtml(hero)}" alt="" />` : ""}
    ${imgs.length > 1 ? `<div class="insp-thumbs">${imgs.slice(0, 10).map((u, i) => `<img class="${i === 0 ? "on" : ""}" data-src="${escapeHtml(u)}" src="${escapeHtml(u)}" alt="" />`).join("")}</div>` : ""}
    <h2 style="font-size:1.05rem;margin:0 0 0.5rem">${escapeHtml((item.title || "").slice(0, 120))}</h2>
    <div class="insp-grid">
      <div class="stat"><span>Price</span><b>$${Number(item.price || item.salePrice || 0).toFixed(2)}</b></div>
      <div class="stat"><span>Images</span><b>${item.imageCount ?? imgs.length}</b></div>
      <div class="stat"><span>PV</span><b>${item.perceivedValue ?? "—"}</b></div>
      <div class="stat"><span>Rank</span><b>${item.rank ?? "—"}</b></div>
      <div class="stat"><span>Score</span><b>${item.rankScore != null ? Number(item.rankScore).toFixed(1) : "—"}</b></div>
      <div class="stat"><span>STR≈</span><b>${item.sellThrough != null ? `${(Number(item.sellThrough) * 100).toFixed(1)}%` : "—"}</b></div>
    </div>
    <div class="meta">
      <span>${escapeHtml(item.seller || "")}</span>
      <span>${escapeHtml(item.categoryPath || item.categoryId || "")}</span>
      ${item.detailFetched ? `<span>getItem</span>` : ""}
    </div>
    <p class="sub">${escapeHtml(item.descriptionExcerpt || item.specificsSummary || "No description excerpt")}</p>
    ${item.contentSignals?.length ? `<p class="sub">${item.contentSignals.map((s) => `<span class="chip">${escapeHtml(s)}</span>`).join(" ")}</p>` : ""}
    <div class="cta-row">
      ${item.url ? `<a class="btn primary" href="${escapeHtml(item.url)}" target="_blank" rel="noopener">Open listing</a>` : ""}
    </div>
    ${item.itemSpecifics && Object.keys(item.itemSpecifics).length ? `<pre class="out">${escapeHtml(JSON.stringify(item.itemSpecifics, null, 2))}</pre>` : ""}
  `;
  body.querySelectorAll(".insp-thumbs img").forEach((img) => {
    img.onclick = () => {
      body.querySelectorAll(".insp-thumbs img").forEach((x) => x.classList.remove("on"));
      img.classList.add("on");
      const heroEl = $("inspHero");
      if (heroEl) heroEl.src = img.dataset.src;
    };
  });
}

function closeInspector() {
  const box = $("inspector");
  if (box) box.hidden = true;
}

function svgEl(tag, attrs, text) {
  const n = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs || {})) n.setAttribute(k, String(v));
  if (text != null) n.textContent = text;
  return n;
}

function drawHBars(svg, rows, { labelKey = "label", valueKey = "value", color = "#c4f542", onClick } = {}) {
  if (!svg) return;
  svg.innerHTML = "";
  const data = (rows || []).slice(0, 8);
  const w = Number(svg.viewBox.baseVal.width) || 420;
  const h = Number(svg.viewBox.baseVal.height) || 180;
  if (!data.length) {
    svg.appendChild(svgEl("text", { x: 12, y: 24, fill: "#8a9a8c", "font-size": 11 }, "No data yet — run intel or marathon"));
    return;
  }
  const max = Math.max(...data.map((d) => Number(d[valueKey]) || 0), 0.01);
  data.forEach((d, i) => {
    const y = 18 + i * ((h - 24) / data.length);
    const bw = ((Number(d[valueKey]) || 0) / max) * (w - 150);
    const g = svgEl("g", { class: "hit" });
    g.appendChild(svgEl("rect", { x: 120, y, width: Math.max(bw, 2), height: 14, fill: color, opacity: 0.85 }));
    g.appendChild(svgEl("text", { x: 8, y: y + 11, fill: "#8a9a8c", "font-size": 10 }, String(d[labelKey] || "").slice(0, 16)));
    g.appendChild(svgEl("text", { x: 124 + bw, y: y + 11, fill: "#c4f542", "font-size": 10 }, String(d[valueKey])));
    g.addEventListener("mousemove", (ev) => tipShow(ev, `<b>${escapeHtml(d[labelKey])}</b><br/>${valueKey} ${escapeHtml(d[valueKey])}`));
    g.addEventListener("mouseleave", tipHide);
    if (onClick) g.addEventListener("click", () => onClick(d));
    svg.appendChild(g);
  });
}

function drawScatterXY(svg, rows, { xKey = "x", yKey = "y", onClick } = {}) {
  if (!svg) return;
  svg.innerHTML = "";
  const data = (rows || []).slice(0, 60);
  const w = 420;
  const h = 180;
  if (!data.length) {
    svg.appendChild(svgEl("text", { x: 12, y: 24, fill: "#8a9a8c", "font-size": 11 }, "No points"));
    return;
  }
  const xs = data.map((d) => Number(d[xKey]) || 0);
  const ys = data.map((d) => Number(d[yKey]) || 0);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs, minX + 1);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys, minY + 1);
  data.forEach((d) => {
    const x = 28 + ((Number(d[xKey]) - minX) / (maxX - minX)) * (w - 50);
    const y = h - 22 - ((Number(d[yKey]) - minY) / (maxY - minY)) * (h - 40);
    const c = svgEl("circle", { cx: x, cy: y, r: 5, fill: "#c4f542", opacity: 0.8, class: "hit" });
    c.addEventListener("mousemove", (ev) =>
      tipShow(ev, `${escapeHtml((d.title || "").slice(0, 60))}<br/>$${Number(d[xKey] || 0).toFixed(0)} · ${yKey} ${d[yKey]}`)
    );
    c.addEventListener("mouseleave", tipHide);
    if (onClick) c.addEventListener("click", () => onClick(d));
    svg.appendChild(c);
  });
  svg.appendChild(svgEl("text", { x: 8, y: 14, fill: "#8a9a8c", "font-size": 10 }, `${xKey} →  ·  ${yKey} ↑`));
}

function drawLadder(svg, ladder) {
  if (!svg) return;
  svg.innerHTML = "";
  const pts = [
    ["p10", ladder?.p10],
    ["p25", ladder?.p25],
    ["p50", ladder?.p50],
    ["p75", ladder?.p75],
    ["p90", ladder?.p90],
  ].filter(([, v]) => v != null);
  if (!pts.length) {
    svg.appendChild(svgEl("text", { x: 12, y: 24, fill: "#8a9a8c", "font-size": 11 }, "No price ladder"));
    return;
  }
  const vals = pts.map((p) => Number(p[1]));
  const min = Math.min(...vals);
  const max = Math.max(...vals, min + 1);
  pts.forEach((p, i) => {
    const x = 40 + i * 75;
    const h = ((Number(p[1]) - min) / (max - min)) * 120 + 16;
    const y = 150 - h;
    svg.appendChild(svgEl("rect", { x, y, width: 36, height: h, fill: i === 2 ? "#c4f542" : "#5ddea8", opacity: 0.8 }));
    svg.appendChild(svgEl("text", { x, y: 168, fill: "#8a9a8c", "font-size": 10 }, p[0]));
    svg.appendChild(svgEl("text", { x, y: y - 6, fill: "#e8efe6", "font-size": 10 }, `$${Number(p[1]).toFixed(0)}`));
  });
}

function percentile(sorted, p) {
  if (!sorted.length) return null;
  const i = (sorted.length - 1) * p;
  const lo = Math.floor(i);
  const hi = Math.ceil(i);
  if (lo === hi) return sorted[lo];
  return sorted[lo] * (hi - i) + sorted[hi] * (i - lo);
}

function deriveMarketStats(rows) {
  const list = rows || [];
  const prices = list.map((r) => Number(r.price || r.salePrice) || 0).filter((n) => n > 0).sort((a, b) => a - b);
  const imgs = list.map((r) => Number(r.imageCount) || (r.image ? 1 : 0));
  const sellers = new Map();
  for (const r of list) {
    const s = r.seller || "unknown";
    sellers.set(s, (sellers.get(s) || 0) + 1);
  }
  const sellerRows = [...sellers.entries()]
    .map(([seller, listings]) => ({ seller, listings, share: list.length ? listings / list.length : 0 }))
    .sort((a, b) => b.listings - a.listings);
  const hhi = sellerRows.reduce((acc, s) => acc + s.share * s.share, 0);
  const withImg = list.filter((r) => r.image || (r.images || []).length).length;
  const cats = new Map();
  for (const r of list) {
    const c = r.categoryPath || r.categoryId || "uncat";
    cats.set(c, (cats.get(c) || 0) + 1);
  }
  return {
    n: list.length,
    withImg,
    imgPct: list.length ? Math.round((withImg / list.length) * 100) : 0,
    median: percentile(prices, 0.5),
    p10: percentile(prices, 0.1),
    p25: percentile(prices, 0.25),
    p75: percentile(prices, 0.75),
    p90: percentile(prices, 0.9),
    min: prices[0] || null,
    max: prices[prices.length - 1] || null,
    uniqueSellers: sellers.size,
    hhi: Math.round(hhi * 10000) / 10000,
    sellerRows,
    prices,
    imgs,
    catRows: [...cats.entries()].map(([label, value]) => ({ label, value })).sort((a, b) => b.value - a.value),
  };
}

function buckets(values, count = 8) {
  const nums = (values || []).filter((n) => Number.isFinite(n));
  if (!nums.length) return [];
  const min = Math.min(...nums);
  const max = Math.max(...nums, min + 1);
  const step = (max - min) / count || 1;
  const bins = Array.from({ length: count }, (_, i) => ({
    i,
    min: min + i * step,
    max: i === count - 1 ? max : min + (i + 1) * step,
    value: 0,
  }));
  for (const n of nums) {
    let idx = Math.floor((n - min) / step);
    if (idx >= count) idx = count - 1;
    if (idx < 0) idx = 0;
    bins[idx].value += 1;
  }
  return bins;
}

function drawHistogram(svg, bins, { label = "$", onClick } = {}) {
  if (!svg) return;
  svg.innerHTML = "";
  const w = Number(svg.viewBox.baseVal.width) || 420;
  const h = Number(svg.viewBox.baseVal.height) || 180;
  if (!bins?.length) {
    svg.appendChild(svgEl("text", { x: 12, y: 24, fill: "#8a9a8c", "font-size": 11 }, "No distribution"));
    return;
  }
  const max = Math.max(...bins.map((b) => b.value), 1);
  const bw = (w - 36) / bins.length;
  bins.forEach((b, i) => {
    const bh = (b.value / max) * (h - 40);
    const x = 24 + i * bw;
    const y = h - 22 - bh;
    const g = svgEl("g", { class: "hit" });
    g.appendChild(svgEl("rect", { x, y, width: Math.max(bw - 4, 2), height: Math.max(bh, 1), fill: "#c4f542", opacity: 0.8 }));
    g.appendChild(svgEl("text", { x, y: h - 8, fill: "#8a9a8c", "font-size": 9 }, `${label}${Math.round(b.min)}`));
    g.addEventListener("mousemove", (ev) =>
      tipShow(ev, `${label}${Math.round(b.min)}–${Math.round(b.max)}<br/><b>${b.value}</b> listings`)
    );
    g.addEventListener("mouseleave", tipHide);
    if (onClick) g.addEventListener("click", () => onClick(b));
    svg.appendChild(g);
  });
}

function drawDonut(svg, parts) {
  if (!svg) return;
  svg.innerHTML = "";
  const data = (parts || []).filter((p) => p.value > 0);
  const total = data.reduce((s, p) => s + p.value, 0);
  if (!total) {
    svg.appendChild(svgEl("text", { x: 12, y: 24, fill: "#8a9a8c", "font-size": 11 }, "No mix yet"));
    return;
  }
  const cx = 70;
  const cy = 70;
  const r = 48;
  let a0 = -Math.PI / 2;
  const colors = ["#c4f542", "#5ddea8", "#ff6b3d", "#8a9a8c", "#e6c35c"];
  data.forEach((p, i) => {
    const slice = (p.value / total) * Math.PI * 2;
    const a1 = a0 + slice;
    const x1 = cx + r * Math.cos(a0);
    const y1 = cy + r * Math.sin(a0);
    const x2 = cx + r * Math.cos(a1);
    const y2 = cy + r * Math.sin(a1);
    const large = slice > Math.PI ? 1 : 0;
    const path = `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2} Z`;
    const g = svgEl("g", { class: "hit" });
    g.appendChild(svgEl("path", { d: path, fill: colors[i % colors.length], opacity: 0.9 }));
    g.addEventListener("mousemove", (ev) => tipShow(ev, `<b>${escapeHtml(p.label)}</b><br/>${p.value}`));
    g.addEventListener("mouseleave", tipHide);
    svg.appendChild(g);
    svg.appendChild(svgEl("text", { x: 140, y: 28 + i * 16, fill: colors[i % colors.length], "font-size": 11 }, `${p.label} ${p.value}`));
    a0 = a1;
  });
}

function drawSparkline(svg, values) {
  if (!svg) return;
  svg.innerHTML = "";
  const nums = (values || []).filter((n) => Number.isFinite(n));
  if (nums.length < 2) return;
  const w = 180;
  const h = 36;
  const min = Math.min(...nums);
  const max = Math.max(...nums, min + 1);
  const pts = nums
    .map((n, i) => {
      const x = (i / (nums.length - 1)) * (w - 4) + 2;
      const y = h - 4 - ((n - min) / (max - min)) * (h - 8);
      return `${x},${y}`;
    })
    .join(" ");
  svg.appendChild(svgEl("polyline", { points: pts, fill: "none", stroke: "#c4f542", "stroke-width": 1.5 }));
}

function renderStatStrip(el, stats) {
  if (!el) return;
  if (!stats?.n) {
    el.innerHTML = `<div class="stat"><span>Sample</span><b>0</b><em>run intel or marathon</em></div>`;
    return;
  }
  const money = (n) => (n == null ? "—" : `$${Number(n).toFixed(0)}`);
  el.innerHTML = [
    ["Listings", stats.n, `${stats.withImg} with photos`],
    ["Median $", money(stats.median), `${money(stats.p10)}–${money(stats.p90)}`],
    ["Image cover", `${stats.imgPct}%`, `${stats.withImg}/${stats.n}`],
    ["Sellers", stats.uniqueSellers, `HHI ${stats.hhi}`],
    ["P25 / P75", `${money(stats.p25)} / ${money(stats.p75)}`, "ladder"],
  ]
    .map(([k, v, sub]) => `<div class="stat"><span>${k}</span><b>${v}</b><em>${sub}</em></div>`)
    .join("");
}

function setPriceFilter(min, max) {
  desk.filter.min = min;
  desk.filter.max = max;
  if ($("marketMin")) $("marketMin").value = min != null ? Math.round(min) : "";
  if ($("marketMax")) $("marketMax").value = max != null ? Math.round(max) : "";
  applyMarketFilters();
}

function pinCompare(item) {
  if (!item) return;
  const key = item.itemId || item.url || item.title;
  if (desk.compare.some((c) => (c.itemId || c.url || c.title) === key)) return;
  desk.compare = [...desk.compare.slice(-1), item].slice(-2);
  renderCompare();
}

function renderCompare() {
  const tray = $("compareTray");
  const body = $("compareBody");
  if (!tray || !body) return;
  if (desk.compare.length < 1) {
    tray.hidden = true;
    return;
  }
  tray.hidden = false;
  body.innerHTML = desk.compare
    .map(
      (p) => `<div class="compare-col">
        ${p.image ? `<img src="${escapeHtml(p.image)}" alt="" />` : ""}
        <h3>${escapeHtml((p.title || "").slice(0, 80))}</h3>
        <div class="meta">
          <span><b>$${Number(p.price || p.salePrice || 0).toFixed(2)}</b></span>
          <span>${p.imageCount ?? 0} imgs</span>
          <span>PV ${p.perceivedValue ?? "—"}</span>
          <span>${escapeHtml(p.seller || "")}</span>
        </div>
      </div>`
    )
    .join("");
}

function renderJobsRail(jobs) {
  desk.jobs = jobs || [];
  const rail = $("jobsRail");
  const list = $("jobsList");
  const html = (desk.jobs || [])
    .slice(0, 12)
    .map((j) => {
      const n = j.productCount || j.results?.productCount || 0;
      return `<button type="button" class="job-chip" data-job="${escapeHtml(j.id)}">
        <b>${escapeHtml(j.status || "")}</b> ${escapeHtml(j.type || "job")}
        <small>${escapeHtml(j.id)} · ${n} products · ${escapeHtml(j.query || j.q || "")}</small>
      </button>`;
    })
    .join("");
  if (rail) rail.innerHTML = html || `<p class="muted">No jobs yet</p>`;
  if (list) list.innerHTML = html || "";
  const bind = (host) => {
    host?.querySelectorAll(".job-chip").forEach((btn) => {
      btn.onclick = async () => {
        try {
          const job = await get(`/orchestrate/jobs/${encodeURIComponent(btn.dataset.job)}`);
          orchJobId = job.id;
          finishOrchUi(job);
          showTab("market");
        } catch (e) {
          appendOrchLog([{ at: new Date().toISOString(), level: "error", message: String(e.message || e) }]);
        }
      };
    });
  };
  bind(rail);
  bind(list);
}

async function refreshJobsRail() {
  try {
    const data = await get("/orchestrate/jobs?limit=12");
    renderJobsRail(data.jobs || []);
    return data.jobs || [];
  } catch {
    return [];
  }
}

function renderIdeas(ideas) {
  const el = $("ideasBoard");
  if (!el) return;
  const rows = ideas || [];
  el.innerHTML = rows
    .slice(0, 24)
    .map(
      (i) =>
        `<button type="button" class="chip" data-q="${escapeHtml(i.title || i.term || "")}">${escapeHtml((i.title || i.term || "").slice(0, 48))} ${i.family ? `· ${escapeHtml(i.family)}` : ""}</button>`
    )
    .join("") || `<p class="muted">No ideas yet — run a marathon.</p>`;
  el.querySelectorAll(".chip").forEach((b) => {
    b.onclick = () => {
      const q = (b.dataset.q || "").split(" ").slice(0, 3).join(" ");
      desk.filter.q = q;
      if ($("marketSearch")) $("marketSearch").value = q;
      applyMarketFilters();
      showTab("market");
    };
  });
}

function renderVariants(rows) {
  const el = $("variantsBoard");
  if (!el) return;
  const list = rows || [];
  if (!list.length) {
    el.innerHTML = `<p class="muted">No title variants yet.</p>`;
    return;
  }
  el.innerHTML = list
    .slice(0, 16)
    .map((v) => {
      const title = v.title || v.variant || v.candidate || "";
      const seo = v.seoScore ?? v.seo_score ?? "—";
      const dec = v.decision || "";
      return `<article class="card-row"><div><h3>${escapeHtml(String(title).slice(0, 90))}</h3>
        <div class="meta"><span class="badge-dec ${escapeHtml(dec)}">${escapeHtml(dec || "variant")}</span><span>SEO <b>${escapeHtml(String(seo))}</b></span></div></div></article>`;
    })
    .join("");
}

function filteredProducts() {
  const f = desk.filter;
  let rows = [...(desk.products || [])];
  const q = f.q.trim().toLowerCase();
  if (q) {
    rows = rows.filter((r) =>
      `${r.title || ""} ${r.seller || ""} ${r.categoryPath || ""}`.toLowerCase().includes(q)
    );
  }
  if (f.cat) rows = rows.filter((r) => String(r.categoryPath || r.categoryId) === f.cat);
  if (f.hasImg) rows = rows.filter((r) => r.image || (r.images || []).length);
  if (f.min != null && f.min !== "") rows = rows.filter((r) => Number(r.price || r.salePrice || 0) >= Number(f.min));
  if (f.max != null && f.max !== "") rows = rows.filter((r) => Number(r.price || r.salePrice || 0) <= Number(f.max));
  const key = f.sort || "price";
  rows.sort((a, b) => (Number(b[key]) || 0) - (Number(a[key]) || 0));
  return rows;
}

function applyMarketFilters() {
  const rows = filteredProducts();
  const count = $("marketCount");
  if (count) count.textContent = `${rows.length} / ${desk.products.length} rows`;
  renderOrchTable(rows);
  renderMarketGallery(rows);
  renderStatStrip($("statStrip"), deriveMarketStats(rows));
  drawScatterXY($("chartScatter"), rows, {
    xKey: "price",
    yKey: "imageCount",
    onClick: openInspector,
  });
}

function renderMarketGallery(rows) {
  const host = $("gallery");
  if (!host) return;
  const list = (rows || []).filter((r) => r.image || r.url).slice(0, 36);
  if (!list.length) {
    host.innerHTML = `<div class="empty-market">${escapeHtml(desk.emptyReason || "No products, images, or listing URLs yet. Click Live product research (not Dry-run).")}</div>`;
    return;
  }
  host.innerHTML = list
    .map(
      (g, i) => `
    <button type="button" class="gal-card" data-idx="${i}">
      ${g.image ? `<img src="${escapeHtml(g.image)}" alt="" loading="lazy" />` : `<div class="gal-ph"></div>`}
      <div class="gal-meta">
        <span>$${Number(g.price || g.salePrice || 0).toFixed(2)}</span>
        <span>${g.imageCount != null ? `${g.imageCount} imgs` : ""}</span>
        <span>${escapeHtml((g.title || "").slice(0, 42))}</span>
      </div>
    </button>`
    )
    .join("");
  host.querySelectorAll(".gal-card").forEach((btn) => {
    btn.onclick = () => openInspector(list[Number(btn.dataset.idx)]);
  });
}

function renderDeskCharts() {
  const stats = deriveMarketStats(desk.products);
  const heatSrc = (desk.trends?.categoryHeat || []).map((c) => ({
    label: c.label || c.categoryId,
    value: c.heatScore,
    id: c.categoryId,
  }));
  const heat = heatSrc.length ? heatSrc : stats.catRows;
  drawHBars($("chartHeat"), heat, {
    onClick: (d) => {
      const match =
        (desk.products || []).find((p) => (p.categoryPath || p.categoryId) === d.label) ||
        (desk.products || []).find((p) => String(p.categoryId) === String(d.id));
      const cat = match ? match.categoryPath || match.categoryId : d.label;
      const sel = $("marketCat");
      if (sel) sel.value = cat || "";
      desk.filter.cat = cat || "";
      applyMarketFilters();
    },
  });
  const rising = (desk.trends?.risingKeywords || []).map((k) => ({
    label: k.term,
    value: Number(k.lift || k.freshCount || 0).toFixed(2),
  }));
  drawHBars($("chartKw"), rising, {
    color: "#5ddea8",
    onClick: (d) => {
      desk.filter.q = d.label || "";
      if ($("marketSearch")) $("marketSearch").value = desk.filter.q;
      applyMarketFilters();
    },
  });
  const ladder =
    desk.trends?.hottestCategory?.priceLadder ||
    desk.trends?.categoryHeat?.[0]?.priceLadder ||
    desk.intel?.market?.priceLadder ||
    desk.intel?.priceLadder ||
    (stats.median
      ? { p10: stats.p10, p25: stats.p25, p50: stats.median, p75: stats.p75, p90: stats.p90 }
      : null);
  drawLadder($("chartLadder"), ladder);
  drawHistogram($("chartHist"), buckets(stats.prices, 8), {
    label: "$",
    onClick: (b) => setPriceFilter(b.min, b.max),
  });
  const imgBins = [0, 1, 2, 4, 6, 8, 12].map((lo, i, arr) => {
    const hi = arr[i + 1] ?? 99;
    const label = hi === 99 ? `${lo}+` : lo === hi - 1 ? String(lo) : `${lo}–${hi - 1}`;
    return {
      label,
      value: stats.imgs.filter((n) => n >= lo && n < hi).length,
      lo,
    };
  });
  drawHBars($("chartImgs"), imgBins, {
    labelKey: "label",
    valueKey: "value",
    color: "#5ddea8",
    onClick: (d) => {
      desk.filter.hasImg = (d.lo || 0) > 0;
      if ($("marketHasImg")) $("marketHasImg").checked = desk.filter.hasImg;
      applyMarketFilters();
    },
  });
  const sellers = (desk.intel?.market?.topSellers || desk.intel?.topSellers || stats.sellerRows).slice(0, 8).map((s) => ({
    label: s.seller,
    value: s.listings,
  }));
  drawHBars($("chartSellers"), sellers, {
    onClick: (d) => {
      desk.filter.q = d.label || "";
      if ($("marketSearch")) $("marketSearch").value = desk.filter.q;
      applyMarketFilters();
    },
  });
  const lanes = (desk.lanes || []).map((l) => ({
    label: l.label || l.categoryId,
    value: l.productCount || l.heatScore || 0,
  }));
  drawHBars($("chartLanes"), lanes.length ? lanes : stats.catRows, {
    onClick: (d) => {
      desk.filter.cat = d.label || "";
      if ($("marketCat")) $("marketCat").value = desk.filter.cat;
      applyMarketFilters();
    },
  });
  const decisions = {};
  for (const p of desk.packages || []) {
    const k = p.decision || "OPEN";
    decisions[k] = (decisions[k] || 0) + 1;
  }
  drawDonut(
    $("chartDecisions"),
    Object.entries(decisions).map(([label, value]) => ({ label, value }))
  );
  drawSparkline($("kpiSpark"), stats.prices.slice(0, 40));
  drawScatterXY($("chartScatter"), desk.products, {
    xKey: "price",
    yKey: "imageCount",
    onClick: openInspector,
  });
}

function setDeskBanner(msg, kind = "err") {
  const el = $("deskBanner");
  if (!el) return;
  if (!msg) {
    el.hidden = true;
    el.textContent = "";
    return;
  }
  el.hidden = false;
  el.className = `desk-banner ${kind}`;
  el.textContent = msg;
}

function clientProduct(item = {}) {
  const images = [...new Set([item.image, item.thumbnail, ...(item.images || [])].filter(Boolean))];
  return {
    ...item,
    title: item.title || "",
    price: Number(item.price ?? item.salePrice) || 0,
    salePrice: Number(item.salePrice ?? item.price) || 0,
    url: item.url || "",
    image: images[0] || item.image || "",
    images,
    imageCount: item.imageCount ?? images.length,
    descriptionExcerpt: item.descriptionExcerpt || item.description || item.specificsSummary || "",
  };
}

function collectClientProducts(payload = {}) {
  const r = payload.results || payload;
  const bags = [
    r.productsPreview,
    r.products,
    r.items,
    r.lethalCandidates,
    r.lethalBoard,
    r.marketBoard,
    r.top,
    r.gallery,
    r.viz?.gallery,
    payload.market?.products,
  ];
  const out = [];
  const seen = new Set();
  for (const bag of bags) {
    if (!Array.isArray(bag)) continue;
    for (const it of bag) {
      const row = clientProduct(it);
      if (!row.title) continue;
      const key = row.url || row.itemId || row.id || row.title.toLowerCase();
      if (seen.has(key)) continue;
      seen.add(key);
      out.push(row);
    }
  }
  return out;
}

function hydrateMarketFromResearch(payload, meta = {}) {
  const r = payload?.results || payload || {};
  const products = collectClientProducts(payload);
  const dryRun = Boolean(r.dryRun || meta.dryRun || payload?.dryRun || products.some((p) => p.source === "dry-fixture"));
  desk.products = dryRun ? [] : products;
  desk.intel = r.intel || r.market ? r : desk.intel;
  if (r.intel) desk.intel = r.intel;
  if (r.market && !r.intel) desk.intel = { market: r.market, ...r };
  desk.emptyReason =
    r.emptyReason ||
    payload?.emptyReason ||
    meta.emptyReason ||
    (dryRun
      ? "Dry-run fixtures are not live listings. Click Live product research."
      : products.length
        ? null
        : "No products yet. Click Live product research (not Dry-run).");
  const imgs = desk.products.filter((p) => p.image).length;
  const urls = desk.products.filter((p) => p.url).length;
  setKpis({
    products: desk.products.length,
    images: r.productsWithImages ?? imgs,
    variants: r.variantTotalGenerated ?? desk.variants.length,
    ideas: r.ideaCount ?? desk.ideas.length,
    packages: r.packageCount ?? desk.packages.length,
    heat: r.trends?.hottestCategory?.heatScore ?? heatMax(r.trends),
  });
  renderDeskCharts();
  applyMarketFilters();
  renderBoard(desk.products.length ? desk.products : products);
  if (desk.products.length) {
    setDeskBanner(
      `${desk.products.length} products · ${imgs} images · ${urls} listing URLs${r.detailsFetched ? ` · ${r.detailsFetched} getItem pages` : ""}`,
      "ok"
    );
  } else {
    setDeskBanner(desk.emptyReason, dryRun ? "info" : "err");
  }
  const rs = $("railStatus");
  if (rs) rs.textContent = meta.status || (desk.products.length ? "live" : "empty");
}

async function runLiveResearch(p) {
  const payload = p || missionPayload();
  setDeskBanner("Booting research VM — live eBay Browse, not a CSV dump…", "info");
  const phase = $("orchPhase");
  if (phase) phase.textContent = "watch boot…";
  showTab("watch");
  try {
    return await startResearchWatch(payload);
  } catch (e) {
    const msg = String(e.message || e);
    setDeskBanner(msg, "err");
    hydrateMarketFromResearch({ products: [], emptyReason: msg });
    throw e;
  }
}
window.hydrateMarketFromResearch = hydrateMarketFromResearch;
window.runLiveResearch = runLiveResearch;

function hydrateMarketFromJob(job) {
  const r = job?.results || {};
  desk.packages = r.packagesPreview || r.packages || [];
  desk.trends = r.trends || null;
  desk.lanes = r.lanes || [];
  desk.ideas = r.ideasPreview || r.trends?.ideasPreview || r.recommendations?.topIdeas || [];
  desk.variants = r.variantsPreview || r.variants || [];
  hydrateMarketFromResearch(job?.results || job || {}, { status: job?.status });
  desk.intel = r.intel || desk.intel;
  const cats = [...new Set(desk.products.map((p) => p.categoryPath || p.categoryId).filter(Boolean))];
  const sel = $("marketCat");
  if (sel) {
    const cur = sel.value;
    sel.innerHTML = `<option value="">All categories</option>${cats.map((c) => `<option value="${escapeHtml(String(c))}">${escapeHtml(String(c))}</option>`).join("")}`;
    sel.value = cur;
  }
  const clusters = r.clusters?.clusters || [];
  const cv = $("clusterViz");
  if (cv) {
    cv.innerHTML = clusters
      .slice(0, 16)
      .map((c) => `<button type="button" class="chip" data-seed="${escapeHtml(c.seed)}">${escapeHtml(c.seed)} · ${c.size}</button>`)
      .join("");
    cv.querySelectorAll(".chip").forEach((b) => {
      b.onclick = () => {
        desk.filter.q = b.dataset.seed || "";
        const inp = $("marketSearch");
        if (inp) inp.value = desk.filter.q;
        applyMarketFilters();
        showTab("market");
      };
    });
  }
  setKpis({
    products: r.productCount ?? desk.products.length,
    images: r.productsWithImages,
    variants: r.variantTotalGenerated,
    ideas: r.ideaCount ?? desk.ideas.length,
    packages: r.packageCount ?? desk.packages.length,
    heat: r.trends?.hottestCategory?.heatScore ?? heatMax(r.trends),
  });
  renderDeskCharts();
  applyMarketFilters();
  renderIdeas(desk.ideas);
  renderVariants(desk.variants);
  const pkgStats = $("pkgStats");
  if (pkgStats) {
    const nets = desk.packages.map((p) => Number(p.estNet) || 0);
    renderStatStrip(pkgStats, {
      n: desk.packages.length,
      withImg: desk.packages.filter((p) => p.beatThis?.image).length,
      imgPct: desk.packages.length
        ? Math.round((desk.packages.filter((p) => p.beatThis?.image).length / desk.packages.length) * 100)
        : 0,
      median: percentile(nets.sort((a, b) => a - b), 0.5),
      p10: percentile(nets, 0.1),
      p25: percentile(nets, 0.25),
      p75: percentile(nets, 0.75),
      p90: percentile(nets, 0.9),
      uniqueSellers: new Set(desk.packages.map((p) => p.clusterSeed).filter(Boolean)).size,
      hhi: desk.packages.length,
    });
  }
  const rs = $("railStatus");
  if (rs) rs.textContent = job?.status || "ready";
}

function heatMax(trends) {
  const hs = (trends?.categoryHeat || []).map((c) => Number(c.heatScore) || 0);
  return hs.length ? Math.max(...hs) : null;
}


function numOrNull(v) {
  if (v == null || v === "") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function missionPayload() {
  const fd = new FormData($("missionForm"));
  const evidence = {};
  const soldCount = numOrNull(fd.get("soldCount"));
  const avgSoldPrice = numOrNull(fd.get("avgSoldPrice"));
  const productCost = numOrNull(fd.get("productCost"));
  const altProductCost = numOrNull(fd.get("altProductCost"));
  const leadTimeDays = numOrNull(fd.get("leadTimeDays"));
  if (soldCount != null) evidence.soldCount = soldCount;
  if (avgSoldPrice != null) evidence.avgSoldPrice = avgSoldPrice;
  if (productCost != null) evidence.productCost = productCost;
  if (altProductCost != null) evidence.altProductCost = altProductCost;
  if (leadTimeDays != null) evidence.leadTimeDays = leadTimeDays;

  return {
    q: fd.get("q"),
    categoryId: fd.get("categoryId"),
    categoryLabel: "Home",
    minPrice: Number(fd.get("minPrice")),
    maxPrice: Number(fd.get("maxPrice")),
    costRatio: Number(fd.get("costRatio")),
    deepCrawl: fd.get("deepCrawl") === "on",
    crawlPages: 2,
    targetDailyProfit: 50,
    evidence: Object.keys(evidence).length ? evidence : undefined,
    promotePass: fd.get("promotePass") === "on",
  };
}

function renderBrief(brief) {
  const v = brief.verdict || "";
  const cls = v.startsWith("GO") ? "go" : v.startsWith("NO") ? "nogo" : "caution";
  $("briefPanel").hidden = false;
  $("brief").innerHTML = `
    <div class="verdict ${cls}">${escapeHtml(v)}</div>
    <p class="sub">PASS ${brief.passCount ?? 0} · CONDITIONAL ${brief.conditionalCount ?? "—"}</p>
    <p class="sub">Why this beats ZIK/AutoDS gravity</p>
    <ul class="list">${(brief.whySuperiorToZikAutods || []).map((x) => `<li>${escapeHtml(x)}</li>`).join("")}</ul>
    <p class="sub" style="margin-top:1rem">Next actions</p>
    <ul class="list">${(brief.nextActions || []).map((x) => `<li>${escapeHtml(x)}</li>`).join("")}</ul>
  `;
}

function renderBoard(rows) {
  $("boardPanel").hidden = false;
  const list = rows || [];
  if (!list.length) {
    $("board").innerHTML = `<p class="empty-market">${escapeHtml(desk.emptyReason || "Lethal board empty until Live product research returns listings.")}</p>`;
    window.__boardRows = [];
    return;
  }
  $("board").innerHTML = (rows || [])
    .slice(0, 12)
    .map(
      (r, i) => `
    <article class="card-row">
      ${r.image ? `<img class="thumb" src="${escapeHtml(r.image)}" alt="" loading="lazy" />` : `<div class="thumb"></div>`}
      <div>
        <h3>${escapeHtml((r.title || "").slice(0, 100))}</h3>
        <div class="meta">
          ${r.rank != null ? `<span>Rank <b>#${r.rank}</b></span>` : ""}
          <span><b>$${Number(r.salePrice || 0).toFixed(2)}</b> price</span>
          <span><b>$${Number(r.net || 0).toFixed(2)}</b> net*</span>
          <span>PV <b>${r.perceivedValue ?? "—"}</b></span>
          ${r.sellThrough != null ? `<span>STR <b>${(Number(r.sellThrough) * 100).toFixed(1)}%</b></span>` : ""}
          ${r.ctrProxy != null ? `<span>CTR≈ <b>${(Number(r.ctrProxy) * 100).toFixed(2)}%</b></span>` : ""}
          ${r.popularity != null ? `<span>Pop <b>${Number(r.popularity).toFixed(2)}</b></span>` : ""}
          <span>${escapeHtml(r.decision || "")}</span>
          <span>${escapeHtml(r.source || "")}</span>
        </div>
      </div>
      <div>
        <button type="button" class="btn ghost btn-promote" data-idx="${i}">Promote</button>
        ${r.url ? `<a class="btn ghost" href="${escapeHtml(r.url)}" target="_blank" rel="noreferrer">Listing</a>` : ""}
      </div>
    </article>`
    )
    .join("");

  window.__boardRows = rows || [];
  $("board").querySelectorAll(".btn-promote").forEach((btn) => {
    btn.onclick = async () => {
      const row = window.__boardRows[Number(btn.dataset.idx)];
      if (!row) return;
      const p = missionPayload();
      try {
        const saved = await post("/api/skus/promote", {
          candidate: row,
          evidence: p.evidence,
          categoryId: p.categoryId,
          costRatio: p.costRatio,
          productCost: p.evidence?.productCost,
        });
        $("opsOut").textContent = `Promoted ${saved.sku} → ${saved.status} (${saved.decision})`;
        await loadSkus();
      } catch (e) {
        $("opsOut").textContent = String(e.message || e);
      }
    };
  });
}

function renderViz(viz, board, meta) {
  if (!viz && !(board || []).length) {
    return;
  }
  $("vizPanel").hidden = false;
  showTab("market");

  if (board?.length && !desk.products.length) {
    desk.products = board.map((r) => ({
      ...r,
      price: r.salePrice ?? r.price,
    }));
  }

  const gallery = viz?.gallery || (board || []).slice(0, 12).map((r) => ({
    rank: r.rank,
    title: r.title,
    image: r.image,
    price: r.salePrice || r.price,
    url: r.url,
    score: r.rankScore,
  }));

  renderMarketGallery(gallery.length ? gallery : desk.products);

  drawBars($("chartStr"), viz?.strBars || [], "str", "conf");
  drawTwinBars($("chartPop"), viz?.popularityBars || [], "popularity", "ctrProxy");
  if (viz?.priceVsRank?.length) {
    drawScatterXY($("chartScatter"), viz.priceVsRank.map((d) => ({ ...d, imageCount: d.score, price: d.price })), {
      xKey: "price",
      yKey: "imageCount",
    });
  }

  const histRow = (board || []).find((b) => b.purchaseHistory?.available);
  if (histRow?.purchaseHistory?.events?.length) {
    $("historyPanel").hidden = false;
    $("historyCaveat").textContent = histRow.purchaseHistory.caveat || "Sold / purchase events";
    $("historyList").innerHTML = histRow.purchaseHistory.events
      .slice(0, 12)
      .map(
        (e) => `<article class="card-row"><div><h3>${escapeHtml((e.title || "").slice(0, 80))}</h3>
        <div class="meta"><span>${escapeHtml(e.date || "")}</span><span><b>$${Number(e.price || 0).toFixed(2)}</b></span><span>${escapeHtml(e.kind || "")}</span></div></div>
        ${e.url ? `<a class="btn ghost" href="${escapeHtml(e.url)}" target="_blank" rel="noreferrer">Open</a>` : ""}</article>`
      )
      .join("");
  } else {
    $("historyPanel").hidden = false;
    $("historyCaveat").textContent =
      "No purchase history on this keyset yet — Marketplace Insights gated. Paste Terapeak sold count into Mission evidence to harden STR.";
    $("historyList").innerHTML = "";
  }

  $("rankMeta").textContent = JSON.stringify(
    meta || {
      note: "CTR is engagement proxy — not official eBay CTR",
      gallery: gallery.length,
    },
    null,
    2
  );
}

function drawBars(svg, rows, key, confKey) {
  if (!svg) return;
  const w = 420;
  const h = 140;
  const data = (rows || []).slice(0, 12);
  if (!data.length) {
    svg.innerHTML = `<text x="12" y="24" fill="#8a9a8c" font-size="11">No STR series — run swarm/intel</text>`;
    return;
  }
  const max = Math.max(...data.map((d) => Number(d[key]) || 0), 0.01);
  const bw = (w - 40) / data.length;
  const bars = data
    .map((d, i) => {
      const v = Number(d[key]) || 0;
      const bh = (v / max) * 100;
      const x = 24 + i * bw;
      const y = 120 - bh;
      const opacity = 0.35 + 0.65 * (Number(d[confKey]) || 0.4);
      return `<rect x="${x}" y="${y}" width="${Math.max(bw - 4, 2)}" height="${bh}" fill="#c4f542" opacity="${opacity}" />`;
    })
    .join("");
  svg.innerHTML = `<rect width="${w}" height="${h}" fill="transparent"/>${bars}
    <text x="8" y="14" fill="#8a9a8c" font-size="10" font-family="IBM Plex Mono, monospace">0–max STR</text>`;
}

function drawTwinBars(svg, rows, aKey, bKey) {
  if (!svg) return;
  const data = (rows || []).slice(0, 10);
  if (!data.length) {
    svg.innerHTML = `<text x="12" y="24" fill="#8a9a8c" font-size="11">No popularity series — run swarm/intel</text>`;
    return;
  }
  const w = 420;
  const h = 140;
  const bw = (w - 40) / data.length;
  const maxA = Math.max(...data.map((d) => Number(d[aKey]) || 0), 0.01);
  const maxB = Math.max(...data.map((d) => Number(d[bKey]) || 0), 0.001);
  const bars = data
    .map((d, i) => {
      const x = 24 + i * bw;
      const ah = ((Number(d[aKey]) || 0) / maxA) * 100;
      const bh = ((Number(d[bKey]) || 0) / maxB) * 100;
      return `<rect x="${x}" y="${120 - ah}" width="${Math.max(bw / 2 - 2, 2)}" height="${ah}" fill="#c4f542"/>
        <rect x="${x + bw / 2}" y="${120 - bh}" width="${Math.max(bw / 2 - 2, 2)}" height="${bh}" fill="#5ddea8"/>`;
    })
    .join("");
  svg.innerHTML = `${bars}<text x="8" y="14" fill="#8a9a8c" font-size="10" font-family="IBM Plex Mono, monospace">pop (acid) · CTR proxy (teal)</text>`;
}

function drawScatter(svg, rows) {
  if (!svg) return;
  const data = (rows || []).slice(0, 20);
  if (!data.length) {
    svg.innerHTML = "";
    return;
  }
  const prices = data.map((d) => Number(d.price) || 0);
  const scores = data.map((d) => Number(d.score) || 0);
  const minP = Math.min(...prices);
  const maxP = Math.max(...prices, minP + 1);
  const maxS = Math.max(...scores, 0.01);
  const dots = data
    .map((d) => {
      const x = 30 + ((Number(d.price) - minP) / (maxP - minP)) * 260;
      const y = 120 - ((Number(d.score) || 0) / maxS) * 100;
      return `<circle cx="${x}" cy="${y}" r="4" fill="#c4f542" opacity="0.85"/>`;
    })
    .join("");
  svg.innerHTML = `${dots}<text x="8" y="14" fill="#8a9a8c" font-size="10" font-family="IBM Plex Mono, monospace">price → · score ↑</text>`;
}

function renderSkus(skus) {
  $("skuBoard").innerHTML = (skus || [])
    .slice(0, 24)
    .map(
      (s) => `
    <article class="sku-card">
      <div>
        <div class="pack-rank">${escapeHtml(s.status || "")} · ${escapeHtml(s.decision || "")}</div>
        <h3>${escapeHtml(s.sku)}</h3>
        <div class="meta">
          <span>${escapeHtml((s.title || "").slice(0, 70))}</span>
          <span><b>$${Number(s.salePrice || 0).toFixed(2)}</b></span>
        </div>
      </div>
      <div>
        <button type="button" class="btn ghost btn-dry" data-sku="${escapeHtml(s.sku)}">Dry-run</button>
      </div>
    </article>`
    )
    .join("") || `<p class="muted">No SKUs in registry yet.</p>`;
  $("skuBoard").querySelectorAll(".btn-dry").forEach((btn) => {
    btn.onclick = async () => {
      const data = await post("/api/publish/dry-run", { sku: btn.dataset.sku });
      $("publishOut").textContent = JSON.stringify(
        { mode: data.mode, ready: data.package?.ready, blockers: data.package?.blockers, canGoLive: data.canGoLive },
        null,
        2
      );
      $("publishForm").sku.value = btn.dataset.sku;
    };
  });
}

async function loadSkus() {
  const r = await fetch(`${API_BASE}/skus`);
  const data = await r.json();
  renderSkus(data.skus || []);
  setKpis({ skus: data.count ?? (data.skus || []).length });
  return data;
}

function renderDrafts(rows) {
  if (!rows?.length) {
    $("draftPanel").hidden = true;
    return;
  }
  $("draftPanel").hidden = false;
  $("drafts").innerHTML = rows
    .map(
      (r) => `
    <article class="card-row">
      <div>
        <h3>${escapeHtml(r.draft?.title || r.title || "").slice(0, 100)}</h3>
        <div class="meta">
          ${(r.draft?.bullets || []).slice(0, 2).map((b) => `<span>${escapeHtml(b.slice(0, 80))}</span>`).join("")}
        </div>
      </div>
    </article>`
    )
    .join("");
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

$("btnSwarm").onclick = async () => {
  const btn = $("btnSwarm");
  btn.disabled = true;
  $("agentLog").textContent = "Swarm running… Scout ∥ Intel → Quality → Evidence → Copy → Brain";
  try {
    const data = await post("/api/swarm", missionPayload());
    $("agentLog").textContent = (data.agents || [])
      .map((a) => `${a.ts.slice(11, 19)}  [${a.agent}]  ${a.msg}`)
      .join("\n");
    renderBrief(data.brief || {});
    const board = data.products?.length
      ? data.products
      : data.marketBoard?.length
        ? data.marketBoard
        : data.lethalBoard || [];
    hydrateMarketFromResearch(data);
    renderBoard(board);
    renderViz(data.viz, board, {
      algorithm: data.scout?.market?.algorithm || data.intel?.market?.algorithm,
      weights: data.scout?.market?.weights || data.intel?.market?.weights,
      stats: data.scout?.market?.stats || data.intel?.market?.rankStats,
      caveats: [
        "CTR is engagement PROXY — not official eBay CTR",
        "Purchase history empty until Insights/Terapeak",
      ],
    });
    renderDrafts(data.listingDrafts || []);
    showTab("market");
    if (data.promoted?.length) {
      $("opsOut").textContent = `Auto-promoted ${data.promoted.length} PASS SKUs`;
      await loadSkus();
    }
  } catch (e) {
    $("agentLog").textContent = String(e.message || e);
    setDeskBanner(String(e.message || e), "err");
  } finally {
    btn.disabled = false;
  }
};

// ── Orchestration deploy / live log / spreadsheet ──
let orchJobId = null;
let orchPollTimer = null;
let orchEventIdx = 0;

function orchPayload() {
  const fd = new FormData($("orchForm"));
  const marathon = fd.get("marathon") === "on";
  return {
    q: fd.get("q"),
    categoryId: fd.get("categoryId"),
    cost: Number(fd.get("cost")),
    suggestedPrice: Number(fd.get("suggestedPrice")),
    variantCount: Number(fd.get("variantCount")),
    detailCount: Number(fd.get("detailCount") || 12),
    ideasTarget: Number(fd.get("ideasTarget") || 250),
    liveProbeCount: Number(fd.get("liveProbeCount")),
    minPrice: Number(fd.get("minPrice")),
    maxPrice: Number(fd.get("maxPrice")),
    crawlPages: marathon ? 4 : 2,
    mode: marathon ? "marathon" : undefined,
    marathon,
    sync: location.port !== "8790" && !marathon,
  };
}

function appendOrchLog(lines) {
  const el = $("orchLog");
  const chunk = (lines || [])
    .map((ev) => `${ev.at?.slice(11, 19) || ""} [${ev.level}] ${ev.message}`)
    .join("\n");
  if (!chunk) return;
  el.textContent = (el.textContent ? el.textContent + "\n" : "") + chunk;
  el.scrollTop = el.scrollHeight;
}

function setOrchProgress(progress) {
  const pct = progress?.pct ?? 0;
  $("orchPct").style.width = `${pct}%`;
  const lane =
    progress?.lane && progress?.laneTotal
      ? ` · lane ${progress.lane}/${progress.laneTotal}${progress.label ? ` ${progress.label}` : ""}`
      : "";
  $("orchPhase").textContent = progress
    ? `${progress.phase || "…"} · ${pct}%${lane}`
    : "Idle — deploy for live product research";
}

function renderOrchTrends(trends) {
  const el = $("orchTrends");
  if (!trends?.categoryHeat?.length && !trends?.risingKeywords?.length) {
    el.hidden = true;
    el.innerHTML = "";
    return;
  }
  el.hidden = false;
  const heat = (trends.categoryHeat || [])
    .slice(0, 5)
    .map(
      (c) =>
        `<div class="heat-row"><span>${escapeHtml(c.label || c.categoryId)}</span><b>${c.heatScore}</b><span>${escapeHtml(c.read || "")}</span></div>`
    )
    .join("");
  const rising = (trends.risingKeywords || [])
    .slice(0, 10)
    .map((r) => `<li><b>${escapeHtml(r.term)}</b> lift ${r.lift} · ${escapeHtml(r.label || "")}</li>`)
    .join("");
  const ideas = (trends.ideasPreview || [])
    .slice(0, 8)
    .map((i) => `<li>${escapeHtml(i.title)} <span class="meta">(${escapeHtml(i.family || "")})</span></li>`)
    .join("");
  el.innerHTML = `
    <h3 class="viz-title">Trend heat · rising keywords · ideas</h3>
    <p class="sub">${escapeHtml(trends.caveat || "")}</p>
    <div class="heat-board">${heat}</div>
    <div class="split-lite">
      <ul class="list">${rising}</ul>
      <ul class="list">${ideas}</ul>
    </div>`;
}

function renderOrchGallery(gallery) {
  const el = $("orchGallery");
  if (!el) return;
  if (!gallery?.length) {
    el.hidden = true;
    el.innerHTML = "";
    return;
  }
  el.hidden = true; // primary gallery is #gallery on Market tab
  renderMarketGallery(gallery);
}

function renderOrchRecs(recs) {
  const el = $("orchRecs");
  if (!recs) {
    el.hidden = true;
    return;
  }
  el.hidden = false;
  const beat = recs.productsToBeat || [];
  const testNow = recs.testNow || [];
  el.innerHTML =
    beat
      .slice(0, 8)
      .map(
        (r) => `
    <article class="card-row">
      ${r.image ? `<img class="thumb" src="${escapeHtml(r.image)}" alt="" loading="lazy" />` : `<div class="thumb"></div>`}
      <div>
        <h3><a href="${escapeHtml(r.url || "#")}" target="_blank" rel="noopener">${escapeHtml((r.title || "").slice(0, 90))}</a></h3>
        <div class="meta">
          <span class="badge-dec">BEAT THIS</span>
          <span><b>$${Number(r.price || 0).toFixed(2)}</b></span>
          <span>${escapeHtml(r.categoryPath || "")}</span>
          <span>${r.imageCount ?? 0} images</span>
        </div>
      </div>
    </article>`
      )
      .join("") +
    testNow
      .slice(0, 4)
      .map(
        (r) => `
    <article class="card-row">
      <div>
        <h3>${escapeHtml((r.title || "").slice(0, 90))}</h3>
        <div class="meta">
          <span class="badge-dec ${escapeHtml(r.decision || "")}">${escapeHtml(r.decision || "")}</span>
          <span>SEO <b>${r.seoScore ?? "—"}</b></span>
          <span>${escapeHtml(r.categoryPath || "")}</span>
        </div>
      </div>
    </article>`
      )
      .join("");
}

function renderOrchTable(products) {
  const wrap = $("orchTableWrap");
  const table = $("orchTable");
  if (!wrap || !table) return;
  if (!products?.length) {
    wrap.hidden = false;
    table.querySelector("tbody").innerHTML = `<tr><td colspan="8">No rows — run a mission or apply a looser filter</td></tr>`;
    return;
  }
  wrap.hidden = false;
  const cols = ["rank", "price", "imageCount", "perceivedValue", "seller", "categoryPath", "title", "url"];
  table.querySelector("thead").innerHTML = `<tr>${cols.map((c) => `<th data-sort="${c}">${c}</th>`).join("")}</tr>`;
  table.querySelector("tbody").innerHTML = products
    .slice(0, 80)
    .map(
      (r, i) => `<tr data-idx="${i}">${cols
        .map((c) => {
          let v = r[c];
          if (c === "title") v = String(v || "").slice(0, 70);
          if (c === "url" && v) {
            return `<td><a href="${escapeHtml(String(v))}" target="_blank" rel="noopener">listing</a></td>`;
          }
          return `<td>${escapeHtml(v == null ? "" : String(v))}</td>`;
        })
        .join("")}</tr>`
    )
    .join("");
  table.querySelectorAll("tbody tr").forEach((tr) => {
    tr.onclick = (e) => {
      if (e.target.closest("a")) return;
      openInspector(products[Number(tr.dataset.idx)]);
    };
  });
  table.querySelectorAll("th[data-sort]").forEach((th) => {
    th.onclick = () => {
      desk.filter.sort = th.dataset.sort;
      const sel = $("marketSort");
      if (sel) sel.value = desk.filter.sort;
      applyMarketFilters();
    };
  });
}

function renderOrchPackages(packages) {
  const el = $("orchPackages");
  if (!el) return;
  if (!packages?.length) {
    el.hidden = true;
    el.innerHTML = "";
    return;
  }
  el.hidden = false;
  el.innerHTML = packages
    .slice(0, 18)
    .map((p, i) => {
      const score = Math.min(100, Math.max(4, Number(p.ideaScore || p.estNet || 0)));
      return `
    <article class="pack-card" data-idx="${i}">
      ${p.beatThis?.image ? `<img class="thumb" src="${escapeHtml(p.beatThis.image)}" alt="" />` : ""}
      <div class="pack-rank">#${i + 1} · ${escapeHtml(p.packageId || "")} · ${escapeHtml(p.decision || "")}</div>
      <h3>${escapeHtml((p.title || "").slice(0, 90))}</h3>
      <div class="scorebar" title="idea/net"><span style="width:${score}%"></span></div>
      <div class="meta">
        <span>Net <b>$${Number(p.estNet || 0).toFixed(2)}</b></span>
        <span>Price <b>$${Number(p.salePrice || p.price || 0).toFixed(2)}</b></span>
        <span>Idea <b>${p.ideaScore ?? "—"}</b></span>
        <span>${escapeHtml(p.clusterSeed || "")}</span>
        <span>imgs ≥ ${p.imagePlan?.beatWith ?? 8}</span>
      </div>
      <p class="sub">${escapeHtml((p.bullets || [])[0] || "")}</p>
    </article>`;
    })
    .join("");
}

function finishOrchUi(job, data, opts = {}) {
  const gallery = job?.results?.gallery || data?.gallery || [];
  const products = job?.results?.productsPreview || job?.results?.products || [];
  const recs = job?.results?.recommendations || data?.recommendations;
  const trends = job?.results?.trends || null;
  if (trends) {
    trends.ideasPreview = trends.ideasPreview || job?.results?.ideasPreview || recs?.topIdeas;
  }
  renderOrchTrends(trends);
  renderOrchGallery(gallery);
  renderOrchRecs(recs);
  hydrateMarketFromJob(job || { results: { ...data, products, gallery, trends, recommendations: recs } });
  renderOrchPackages(job?.results?.packagesPreview || job?.results?.packages || []);
  const n = job?.results?.productCount ?? data?.productCount ?? products.length;
  const imgs = job?.results?.productsWithImages ?? data?.productsWithImages;
  const ideas = job?.results?.ideaCount;
  const variants = job?.results?.variantTotalGenerated;
  const pkgs = job?.results?.packageCount;
  $("orchPhase").textContent = `done · ${n} products${imgs != null ? ` · ${imgs} images` : ""}${variants != null ? ` · ${variants} variants` : ""}${ideas != null ? ` · ${ideas} ideas` : ""}${pkgs != null ? ` · ${pkgs} packages` : ""}`;
  $("btnOrchCsv").disabled = false;
  $("btnOrchProductsCsv").disabled = false;
  $("btnOrchPromote").disabled = !(pkgs || job?.results?.packagesPreview?.length);
  refreshJobsRail().catch(() => {});
  if (!opts.stay) showTab("market");
}

async function pollOrchJob() {
  if (!orchJobId) return;
  try {
    const ev = await get(
      `/orchestrate/jobs/${encodeURIComponent(orchJobId)}/events?after=${orchEventIdx}`
    );
    appendOrchLog(ev.events || []);
    orchEventIdx = ev.nextIndex ?? orchEventIdx;
    setOrchProgress(ev.progress);
    if (ev.status === "completed" || ev.status === "failed" || ev.status === "cancelled") {
      clearInterval(orchPollTimer);
      orchPollTimer = null;
      const job = await get(`/orchestrate/jobs/${encodeURIComponent(orchJobId)}`);
      if (ev.status === "completed" || ev.status === "cancelled") finishOrchUi(job);
      $("btnOrchDeploy").disabled = false;
      $("btnOrchMarathon").disabled = false;
      if (ev.status === "failed") {
        $("orchPhase").textContent = `Failed — ${job.error || "see log"}`;
      }
    }
  } catch (e) {
    appendOrchLog([{ at: new Date().toISOString(), level: "error", message: String(e.message || e) }]);
  }
}

async function startOrch(payload, endpoint) {
  $("btnOrchDeploy").disabled = true;
  $("btnOrchMarathon").disabled = true;
  $("orchLog").textContent = "";
  $("btnOrchCsv").disabled = true;
  $("btnOrchProductsCsv").disabled = true;
  $("btnOrchPromote").disabled = true;
  $("orchRecs").hidden = true;
  $("orchPackages") && ($("orchPackages").hidden = true);
  $("orchTableWrap").hidden = true;
  $("orchGallery").hidden = true;
  $("orchTrends").hidden = true;
  orchEventIdx = 0;
  if (orchPollTimer) clearInterval(orchPollTimer);
  try {
    const data = await post(endpoint, payload);
    orchJobId = data.jobId;
    appendOrchLog([
      {
        at: new Date().toISOString(),
        level: "info",
        message: `Deployed ${data.jobId} (${data.type || "mission"} · ${data.sync ? "sync" : "async"})`,
      },
    ]);
    setOrchProgress(data.progress || { phase: "queued", pct: 0 });
    if (data.sync && data.status === "completed") {
      const job = await get(`/orchestrate/jobs/${encodeURIComponent(orchJobId)}`);
      appendOrchLog(job.events || []);
      setOrchProgress(job.progress);
      finishOrchUi(job, data);
      $("btnOrchDeploy").disabled = false;
      $("btnOrchMarathon").disabled = false;
    } else if (data.status === "failed") {
      appendOrchLog([{ at: new Date().toISOString(), level: "error", message: data.error || "failed" }]);
      $("btnOrchDeploy").disabled = false;
      $("btnOrchMarathon").disabled = false;
    } else {
      orchPollTimer = setInterval(pollOrchJob, 1200);
      pollOrchJob();
    }
  } catch (e) {
    appendOrchLog([{ at: new Date().toISOString(), level: "error", message: String(e.message || e) }]);
    $("btnOrchDeploy").disabled = false;
    $("btnOrchMarathon").disabled = false;
  }
}

$("btnOrchDeploy").onclick = async () => {
  const payload = orchPayload();
  if (payload.marathon) {
    await startOrch({ ...payload, sync: false }, "/api/orchestrate/campaign");
  } else {
    await startOrch(payload, "/api/orchestrate/deploy");
  }
};

$("btnOrchMarathon").onclick = async () => {
  const payload = { ...orchPayload(), mode: "marathon", marathon: true, sync: false };
  delete payload.categoryId;
  await startOrch(payload, "/api/orchestrate/campaign");
};

$("btnOrchCancel").onclick = async () => {
  if (!orchJobId) return;
  try {
    const data = await post(`/api/orchestrate/jobs/${encodeURIComponent(orchJobId)}/cancel`, {});
    appendOrchLog([
      {
        at: new Date().toISOString(),
        level: "warn",
        message: `Cancel requested (${data.status}) — finishing current lane then rolling up`,
      },
    ]);
  } catch (e) {
    appendOrchLog([{ at: new Date().toISOString(), level: "error", message: String(e.message || e) }]);
  }
};

$("btnOrchPromote").onclick = async () => {
  if (!orchJobId) return;
  try {
    const data = await post(`/api/orchestrate/jobs/${encodeURIComponent(orchJobId)}/promote`, {
      limit: 8,
      decision: "TEST_NOW",
    });
    appendOrchLog([
      {
        at: new Date().toISOString(),
        level: "info",
        message: `Promoted ${data.count} packages → SKU registry`,
      },
    ]);
    $("opsOut").textContent = JSON.stringify(
      (data.skus || []).map((s) => ({ sku: s.sku, title: s.title, status: s.status, net: s.net })),
      null,
      2
    );
    await loadSkus();
    showTab("registry");
  } catch (e) {
    appendOrchLog([{ at: new Date().toISOString(), level: "error", message: String(e.message || e) }]);
  }
};

$("btnDeploy").onclick = () => {
  showTab("launch");
  $("btnOrchMarathon").click();
};

$("btnOrchJobs").onclick = async () => {
  const jobs = await refreshJobsRail();
  $("orchLog").textContent = (jobs || [])
    .map(
      (j) =>
        `${j.id} · ${j.type || "mission"} · ${j.status} · ${j.query || ""} · products=${j.productCount || 0} · variants=${j.variantCount || 0} · ideas=${j.ideaCount || 0} · ${j.progress?.phase || ""}`
    )
    .join("\n");
  showTab("launch");
};

async function downloadOrchCsv(qs) {
  if (!orchJobId) return;
  const r = await fetch(
    `${API_BASE}/orchestrate/jobs/${encodeURIComponent(orchJobId)}/spreadsheet${qs}`
  );
  if (!r.ok) {
    const j = await r.json().catch(() => ({}));
    throw new Error(j.error || r.statusText);
  }
  const blob = await r.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `lpros-${qs.includes("products") ? "products" : "workbook"}-${orchJobId}.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
}

$("btnOrchCsv").onclick = async () => {
  try {
    await downloadOrchCsv("?workbook=1");
  } catch (e) {
    appendOrchLog([{ at: new Date().toISOString(), level: "error", message: String(e.message || e) }]);
  }
};

$("btnOrchProductsCsv").onclick = async () => {
  try {
    await downloadOrchCsv("?products=1");
  } catch (e) {
    appendOrchLog([{ at: new Date().toISOString(), level: "error", message: String(e.message || e) }]);
  }
};

$("btnIntel").onclick = async () => {
  $("agentLog").textContent = "Pulling competitor intel…";
  try {
    const p = missionPayload();
    const data = await post("/api/intel", p);
    $("agentLog").textContent = JSON.stringify(data.market, null, 2);
    hydrateMarketFromResearch(data);
    renderBoard(data.products || data.lethalCandidates || []);
    renderViz(data.viz, data.products || data.lethalCandidates || [], {
      algorithm: data.market?.algorithm,
      weights: data.market?.weights,
      stats: data.market?.rankStats,
    });
    $("boardPanel").hidden = false;
    showTab("market");
    if (data.market?.priceLadder) drawLadder($("chartLadder"), data.market.priceLadder);
    if (!data.productCount) setDeskBanner(data.emptyReason || "Intel returned 0 products", "err");
  } catch (e) {
    $("agentLog").textContent = String(e.message || e);
    setDeskBanner(String(e.message || e), "err");
  }
};

$("btnLiveResearch")?.addEventListener("click", () => {
  runLiveResearch(missionPayload()).catch(() => {});
});

$("evidenceForm").onsubmit = async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const data = await post("/api/evidence/verify", {
    title: fd.get("title"),
    salePrice: Number(fd.get("salePrice")),
    perceivedValue: 0.55,
    evidence: {
      soldCount: Number(fd.get("soldCount")),
      productCost: Number(fd.get("productCost")),
      altProductCost: Number(fd.get("altProductCost")),
      leadTimeDays: Number(fd.get("leadTimeDays")),
      demandSource: "terapeak",
    },
  });
  $("evidenceOut").textContent = JSON.stringify(
    {
      decision: data.decision,
      cleared: data.cleared,
      flags: data.remainingFlags,
      net: data.economics?.net,
      confidence: data.verification?.verificationConfidence,
    },
    null,
    2
  );
};

$("outcomeForm").onsubmit = async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const data = await post("/api/outcomes", {
    title: fd.get("title"),
    net: Number(fd.get("net")),
    profitable: fd.get("profitable") === "on",
    returned: fd.get("returned") === "on",
  });
  $("outcomeOut").textContent = JSON.stringify(data, null, 2);
};

$("btnOutcomes").onclick = async () => {
  const data = await get("/outcomes?limit=15");
  $("outcomeOut").textContent = JSON.stringify(data, null, 2);
};

$("econForm").onsubmit = async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const data = await post("/api/econ", {
    price: Number(fd.get("price")),
    cost: Number(fd.get("cost")),
  });
  $("econOut").textContent = JSON.stringify(data, null, 2);
  const net = Number(data.net ?? data.economics?.net ?? 0);
  const price = Number(fd.get("price")) || 1;
  const pct = Math.max(0, Math.min(100, (net / price) * 100));
  let g = $("econGauge");
  if (!g) {
    g = document.createElement("div");
    g.id = "econGauge";
    g.className = "stat";
    $("econOut").after(g);
  }
  g.innerHTML = `<span>Fee-true net</span><b>$${Number.isFinite(net) ? net.toFixed(2) : "—"}</b><div class="gauge"><span style="width:${pct}%"></span></div>`;
};

$("forecastForm").onsubmit = async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const data = await post("/api/forecast", {
    listings: Number(fd.get("listings")),
    str: Number(fd.get("str")),
    net: Number(fd.get("net")),
    target: Number(fd.get("target")),
  });
  $("forecastOut").textContent = JSON.stringify(data, null, 2);
};

$("btnProviders").onclick = async () => {
  $("fulfillOut").textContent = JSON.stringify(await get("/providers"), null, 2);
};

$("btnFulfillDemo").onclick = async () => {
  const data = await post("/api/fulfill/decide", {
    order: {
      buyerTotal: 54,
      supplierCost: null,
      supplierLeadDays: 9,
      margin: 0.2,
      supplierConfirmed: false,
      policyCompliant: true,
      lineItems: [{ sku: "demo" }],
    },
  });
  $("fulfillOut").textContent = JSON.stringify(data, null, 2);
};

$("btnSkus").onclick = async () => {
  const data = await loadSkus();
  $("opsOut").textContent = `${data.count} SKUs · updated ${data.updatedAt || "—"}`;
};

$("btnExport").onclick = async () => {
  const data = await post("/api/export", { status: "ready", format: "both" });
  $("opsOut").textContent = JSON.stringify(
    { count: data.count, files: data.files, sample: data.sample?.map((p) => p.sku) },
    null,
    2
  );
};

$("btnAuth").onclick = async () => {
  $("opsOut").textContent = JSON.stringify(await get("/auth/status"), null, 2);
};

$("publishForm").onsubmit = async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const data = await post("/api/publish", { sku: fd.get("sku"), live: false });
  $("publishOut").textContent = JSON.stringify(
    {
      mode: data.mode,
      ready: data.package?.ready,
      blockers: data.package?.blockers,
      canGoLive: data.canGoLive,
      next: data.next,
    },
    null,
    2
  );
};

$("orderForm").onsubmit = async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const data = await post("/api/orders/ingest", {
    orderId: fd.get("orderId"),
    sku: fd.get("sku"),
    buyerTotal: Number(fd.get("buyerTotal")),
    supplierConfirmed: fd.get("supplierConfirmed") === "on",
  });
  $("orderOut").textContent = JSON.stringify(
    { orderId: data.order?.orderId, status: data.order?.status, gate: data.gate },
    null,
    2
  );
};

$("btnOrders").onclick = async () => {
  $("orderOut").textContent = JSON.stringify(await get("/orders"), null, 2);
};

// Fix playbook link for Netlify vs local
const playbook = document.getElementById("playbookLink");
if (playbook) playbook.href = `${API_BASE}/playbook`;

document.querySelectorAll(".rail-btn, .kpi").forEach((btn) => {
  btn.addEventListener("click", () => {
    if (btn.dataset.tab) showTab(btn.dataset.tab);
  });
});
$("inspClose")?.addEventListener("click", closeInspector);
$("marketSearch")?.addEventListener("input", (e) => {
  desk.filter.q = e.target.value;
  applyMarketFilters();
});
$("marketCat")?.addEventListener("change", (e) => {
  desk.filter.cat = e.target.value;
  applyMarketFilters();
});
$("marketSort")?.addEventListener("change", (e) => {
  desk.filter.sort = e.target.value;
  applyMarketFilters();
});
$("marketHasImg")?.addEventListener("change", (e) => {
  desk.filter.hasImg = e.target.checked;
  applyMarketFilters();
});

$("orchPackages")?.addEventListener("click", (e) => {
  const card = e.target.closest(".pack-card, .card-row");
  if (!card) return;
  const idx = Number(card.dataset.idx);
  const pkg = Number.isFinite(idx) ? desk.packages[idx] : null;
  const title = card.querySelector("h3")?.textContent;
  const found =
    pkg ||
    (desk.packages || []).find((p) => p.title && title && p.title.startsWith(title.slice(0, 40)));
  if (found) {
    openInspector({
      title: found.title,
      price: found.salePrice || found.price,
      url: found.beatThis?.url,
      image: found.beatThis?.image,
      images: found.beatThis?.image ? [found.beatThis.image] : [],
      descriptionExcerpt: (found.bullets || []).join(" · "),
      categoryPath: found.categoryPath,
      itemSpecifics: found.itemSpecifics,
      perceivedValue: found.ideaScore,
      rankScore: found.estNet,
      imageCount: found.imagePlan?.beatWith,
    });
  }
});

$("marketMin")?.addEventListener("input", (e) => {
  desk.filter.min = e.target.value === "" ? null : Number(e.target.value);
  applyMarketFilters();
});
$("marketMax")?.addEventListener("input", (e) => {
  desk.filter.max = e.target.value === "" ? null : Number(e.target.value);
  applyMarketFilters();
});
$("viewSeg")?.querySelectorAll("button").forEach((btn) => {
  btn.addEventListener("click", () => {
    desk.view = btn.dataset.view || "split";
    $("viewSeg").querySelectorAll("button").forEach((b) => b.classList.toggle("on", b === btn));
    const body = $("marketBody");
    if (body) body.className = `market-body view-${desk.view}`;
  });
});
$("inspCompare")?.addEventListener("click", () => pinCompare(desk.lastInspect));
$("compareClear")?.addEventListener("click", () => {
  desk.compare = [];
  renderCompare();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeInspector();
  if (e.target && ["INPUT", "TEXTAREA", "SELECT"].includes(e.target.tagName)) return;
  const tabs = ["launch", "watch", "market", "packages", "registry", "ops", "playground"];
  if (e.key >= "1" && e.key <= "7") showTab(tabs[Number(e.key) - 1]);
  if (e.key === "/") {
    e.preventDefault();
    showTab("market");
    $("marketSearch")?.focus();
  }
});

async function bootDesk() {
  renderDeskCharts();
  try {
    const h = await get("/health");
    if (h.ebay && !h.ebay.appConfigured) {
      setDeskBanner(h.ebay.hint || "eBay credentials missing — live research will return 0 products.", "err");
    }
  } catch (e) {
    setDeskBanner(
      "Command API unreachable. For live listings run local :8790 (`cd lpros-command && npm start`) or set Netlify EBAY_PRD_* env vars.",
      "err"
    );
  }
  const jobs = await refreshJobsRail();
  const done = (jobs || []).find((j) => j.status === "completed");
  if (done?.id) {
    try {
      const job = await get(`/orchestrate/jobs/${encodeURIComponent(done.id)}`);
      orchJobId = job.id;
      finishOrchUi(job, null, { stay: true });
    } catch {
      /* empty desk until a run */
    }
  }
}

loadSkus().catch(() => {});
bindDeskLayout(document.body);
bootDesk();
bootPlayground();
bootWatch();
