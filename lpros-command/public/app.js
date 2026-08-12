const $ = (id) => document.getElementById(id);

async function post(path, body) {
  const r = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
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
      <div>
        <h3>${escapeHtml((r.title || "").slice(0, 100))}</h3>
        <div class="meta">
          <span><b>$${Number(r.salePrice || 0).toFixed(2)}</b> price</span>
          <span><b>$${Number(r.net || 0).toFixed(2)}</b> net*</span>
          <span>PV <b>${r.perceivedValue ?? "—"}</b></span>
          <span>${escapeHtml(r.decision || "")}</span>
          <span>${escapeHtml(r.source || "")}</span>
          ${(r.flags || []).slice(0, 3).map((f) => `<span>${escapeHtml(f)}</span>`).join("")}
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
  const r = await fetch("/api/skus");
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
    renderBoard(data.lethalBoard || []);
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

$("btnIntel").onclick = async () => {
  $("agentLog").textContent = "Pulling competitor intel…";
  try {
    const p = missionPayload();
    const data = await post("/api/intel", p);
    $("agentLog").textContent = JSON.stringify(data.market, null, 2);
    renderBoard(data.lethalCandidates || []);
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
  const r = await fetch("/api/outcomes?limit=15");
  $("outcomeOut").textContent = JSON.stringify(await r.json(), null, 2);
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
  const r = await fetch("/api/providers");
  $("fulfillOut").textContent = JSON.stringify(await r.json(), null, 2);
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
  const r = await fetch("/api/auth/status");
  $("opsOut").textContent = JSON.stringify(await r.json(), null, 2);
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
  const r = await fetch("/api/orders");
  $("orderOut").textContent = JSON.stringify(await r.json(), null, 2);
};

loadSkus().catch(() => {});
