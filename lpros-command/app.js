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
    $("vizPanel").hidden = true;
    return;
  }
  $("vizPanel").hidden = false;

  const gallery = viz?.gallery || (board || []).slice(0, 12).map((r) => ({
    rank: r.rank,
    title: r.title,
    image: r.image,
    price: r.salePrice || r.price,
    url: r.url,
    score: r.rankScore,
  }));

  $("gallery").innerHTML = gallery
    .map(
      (g) => `
    <figure>
      ${g.image ? `<img src="${escapeHtml(g.image)}" alt="" loading="lazy" />` : `<div style="aspect-ratio:1;background:#1a1f1c"></div>`}
      <figcaption>
        ${g.rank != null ? `#${g.rank} · ` : ""}<b>$${Number(g.price || 0).toFixed(0)}</b><br/>
        ${escapeHtml((g.title || "").slice(0, 48))}
      </figcaption>
    </figure>`
    )
    .join("");

  drawBars($("chartStr"), viz?.strBars || [], "str", "conf");
  drawTwinBars($("chartPop"), viz?.popularityBars || [], "popularity", "ctrProxy");
  drawScatter($("chartScatter"), viz?.priceVsRank || []);

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
  const w = 320;
  const h = 140;
  const data = (rows || []).slice(0, 12);
  if (!data.length) {
    svg.innerHTML = "";
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
    svg.innerHTML = "";
    return;
  }
  const w = 320;
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
    .slice(0, 20)
    .map(
      (s) => `
    <article class="card-row">
      <div>
        <h3>${escapeHtml(s.sku)}</h3>
        <div class="meta">
          <span>${escapeHtml((s.title || "").slice(0, 70))}</span>
          <span><b>$${Number(s.salePrice || 0).toFixed(2)}</b></span>
          <span>${escapeHtml(s.status)}</span>
          <span>${escapeHtml(s.decision || "")}</span>
        </div>
      </div>
      <div>
        <button type="button" class="btn ghost btn-dry" data-sku="${escapeHtml(s.sku)}">Dry-run</button>
      </div>
    </article>`
    )
    .join("");
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
    const board = data.marketBoard?.length ? data.marketBoard : data.lethalBoard || [];
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
    if (data.promoted?.length) {
      $("opsOut").textContent = `Auto-promoted ${data.promoted.length} PASS SKUs`;
      await loadSkus();
    }
  } catch (e) {
    $("agentLog").textContent = String(e.message || e);
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
  return {
    q: fd.get("q"),
    categoryId: fd.get("categoryId"),
    cost: Number(fd.get("cost")),
    suggestedPrice: Number(fd.get("suggestedPrice")),
    variantCount: Number(fd.get("variantCount")),
    liveProbeCount: Number(fd.get("liveProbeCount")),
    minPrice: Number(fd.get("minPrice")),
    maxPrice: Number(fd.get("maxPrice")),
    sync: location.port !== "8790",
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
  $("orchPhase").textContent = progress
    ? `${progress.phase || "…"} · ${pct}%`
    : "Idle — deploy to start agents";
}

function renderOrchRecs(recs) {
  const el = $("orchRecs");
  if (!recs) {
    el.hidden = true;
    return;
  }
  el.hidden = false;
  const testNow = recs.testNow || [];
  el.innerHTML = testNow
    .slice(0, 8)
    .map(
      (r) => `
    <article class="card-row">
      <div>
        <h3>${escapeHtml((r.title || "").slice(0, 90))}</h3>
        <div class="meta">
          <span class="badge-dec ${escapeHtml(r.decision || "")}">${escapeHtml(r.decision || "")}</span>
          <span>SEO <b>${r.seoScore ?? "—"}</b></span>
          <span>Pri <b>${escapeHtml(r.testPriority || "")}</b></span>
          <span>Net <b>$${Number(r.estNet || 0).toFixed(2)}</b></span>
          <span>${escapeHtml(r.primaryKeyword || "")}</span>
        </div>
      </div>
    </article>`
    )
    .join("");
}

function renderOrchTable(rows) {
  const wrap = $("orchTableWrap");
  const table = $("orchTable");
  if (!rows?.length) {
    wrap.hidden = true;
    return;
  }
  wrap.hidden = false;
  const cols = [
    "rank",
    "decision",
    "testPriority",
    "seoScore",
    "title",
    "suggestedPrice",
    "landedCost",
    "estNet",
    "liveTotal",
    "outrankNotes",
  ];
  table.querySelector("thead").innerHTML = `<tr>${cols.map((c) => `<th>${c}</th>`).join("")}</tr>`;
  table.querySelector("tbody").innerHTML = rows
    .slice(0, 40)
    .map(
      (r) => `<tr>${cols
        .map((c) => {
          let v = r[c];
          if (c === "title") v = String(v || "").slice(0, 70);
          if (c === "decision") {
            return `<td><span class="badge-dec ${escapeHtml(String(v || ""))}">${escapeHtml(String(v || ""))}</span></td>`;
          }
          return `<td>${escapeHtml(v == null ? "" : String(v))}</td>`;
        })
        .join("")}</tr>`
    )
    .join("");
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
    if (ev.status === "completed" || ev.status === "failed") {
      clearInterval(orchPollTimer);
      orchPollTimer = null;
      const job = await get(`/orchestrate/jobs/${encodeURIComponent(orchJobId)}`);
      renderOrchRecs(job.results?.recommendations);
      renderOrchTable(job.results?.variantsPreview || []);
      $("btnOrchCsv").disabled = ev.status !== "completed";
      $("btnOrchDeploy").disabled = false;
      if (ev.status === "failed") {
        $("orchPhase").textContent = `Failed — ${job.error || "see log"}`;
      }
    }
  } catch (e) {
    appendOrchLog([{ at: new Date().toISOString(), level: "error", message: String(e.message || e) }]);
  }
}

$("btnOrchDeploy").onclick = async () => {
  $("btnOrchDeploy").disabled = true;
  $("orchLog").textContent = "";
  $("btnOrchCsv").disabled = true;
  $("orchRecs").hidden = true;
  $("orchTableWrap").hidden = true;
  orchEventIdx = 0;
  if (orchPollTimer) clearInterval(orchPollTimer);
  try {
    const payload = orchPayload();
    const data = await post("/api/orchestrate/deploy", payload);
    orchJobId = data.jobId;
    appendOrchLog([
      {
        at: new Date().toISOString(),
        level: "info",
        message: `Deployed ${data.jobId} (${data.sync ? "sync" : "async"})`,
      },
    ]);
    setOrchProgress(data.progress || { phase: "queued", pct: 0 });
    if (data.sync && data.status === "completed") {
      const job = await get(`/orchestrate/jobs/${encodeURIComponent(orchJobId)}`);
      appendOrchLog(job.events || []);
      setOrchProgress(job.progress);
      renderOrchRecs(job.results?.recommendations || data.recommendations);
      renderOrchTable(job.results?.variantsPreview || []);
      $("btnOrchCsv").disabled = false;
      $("btnOrchDeploy").disabled = false;
    } else if (data.status === "failed") {
      appendOrchLog([{ at: new Date().toISOString(), level: "error", message: data.error || "failed" }]);
      $("btnOrchDeploy").disabled = false;
    } else {
      orchPollTimer = setInterval(pollOrchJob, 900);
      pollOrchJob();
    }
  } catch (e) {
    appendOrchLog([{ at: new Date().toISOString(), level: "error", message: String(e.message || e) }]);
    $("btnOrchDeploy").disabled = false;
  }
};

$("btnDeploy").onclick = () => {
  $("orchPanel")?.scrollIntoView({ behavior: "smooth", block: "start" });
  $("btnOrchDeploy").click();
};

$("btnOrchJobs").onclick = async () => {
  const data = await get("/orchestrate/jobs?limit=12");
  $("orchLog").textContent = (data.jobs || [])
    .map(
      (j) =>
        `${j.id} · ${j.status} · ${j.query || ""} · variants=${j.variantCount || 0} · ${j.progress?.phase || ""}`
    )
    .join("\n");
};

$("btnOrchCsv").onclick = async () => {
  if (!orchJobId) return;
  try {
    const r = await fetch(
      `${API_BASE}/orchestrate/jobs/${encodeURIComponent(orchJobId)}/spreadsheet`
    );
    if (!r.ok) {
      const j = await r.json().catch(() => ({}));
      throw new Error(j.error || r.statusText);
    }
    const blob = await r.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `lpros-decision-${orchJobId}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
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
    renderBoard(data.lethalCandidates || []);
    renderViz(data.viz, data.lethalCandidates || [], {
      algorithm: data.market?.algorithm,
      weights: data.market?.weights,
      stats: data.market?.rankStats,
    });
    $("boardPanel").hidden = false;
  } catch (e) {
    $("agentLog").textContent = String(e.message || e);
  }
};

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

loadSkus().catch(() => {});
