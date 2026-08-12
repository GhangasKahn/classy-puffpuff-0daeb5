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

function missionPayload() {
  const fd = new FormData($("missionForm"));
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
  };
}

function renderBrief(brief) {
  const v = brief.verdict || "";
  const cls = v.startsWith("GO") ? "go" : v.startsWith("NO") ? "nogo" : "caution";
  $("briefPanel").hidden = false;
  $("brief").innerHTML = `
    <div class="verdict ${cls}">${escapeHtml(v)}</div>
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
      (r) => `
    <article class="card-row">
      <div>
        <h3>${escapeHtml((r.title || "").slice(0, 100))}</h3>
        <div class="meta">
          <span><b>$${Number(r.salePrice || 0).toFixed(2)}</b> price</span>
          <span><b>$${Number(r.net || 0).toFixed(2)}</b> net*</span>
          <span>PV <b>${r.perceivedValue ?? "—"}</b></span>
          <span>${escapeHtml(r.source || "")}</span>
        </div>
      </div>
      <div>${r.url ? `<a class="btn ghost" href="${escapeHtml(r.url)}" target="_blank" rel="noreferrer">Listing</a>` : ""}</div>
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
  $("agentLog").textContent = "Swarm running… Scout → Intel → Quality → Economics → Brain";
  try {
    const data = await post("/api/swarm", missionPayload());
    $("agentLog").textContent = (data.agents || [])
      .map((a) => `${a.ts.slice(11, 19)}  [${a.agent}]  ${a.msg}`)
      .join("\n");
    renderBrief(data.brief || {});
    renderBoard(data.lethalBoard || []);
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
