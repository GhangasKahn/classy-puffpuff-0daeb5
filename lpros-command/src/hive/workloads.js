/**
 * Named hive workloads — ruler-down pipelines with TASK CONTRACTs.
 * Dry-run safe. Capital climate is HOLD. No HTML scrape.
 */
import { getAgent } from "../playground/catalog.js";
import { makeContract, postContract, postReply, listComms } from "./comms.js";
import { runSpecialist } from "./specialists.js";

export const WORKLOADS = [
  {
    id: "research-gate",
    title: "Research → gate",
    summary: "Scout ∥ Intel ∥ Economics → Evidence → Brain. Named workers. Dry-run default.",
    stages: [{ parallel: ["scout", "intel", "economics"] }, { sequential: ["evidence", "brain"] }],
    dryRunDefault: true,
  },
  {
    id: "specialist-gauntlet",
    title: "Legal thesis gauntlet",
    summary: "Joker → Mr. Robot → Bane → Tenet → Wick → Memento. Arguments only. Never crime.",
    stages: [{ sequential: ["redteam", "compliance", "pressure", "inversion", "wick", "memento"] }],
    dryRunDefault: true,
  },
  {
    id: "condition-loop",
    title: "Oracle residual loop",
    summary: "Memento caption → Oracle lesson. No prophecy. Cite or DEFER.",
    stages: [{ sequential: ["memento", "conditioner"] }],
    dryRunDefault: true,
  },
  {
    id: "fulfill-hold",
    title: "Consequence + Shinobi gate",
    summary: "Wick markers then Fulfiller HOLD. AUTO is earned, never assumed.",
    stages: [{ sequential: ["wick", "fulfill"] }],
    dryRunDefault: true,
  },
  {
    id: "full-hive",
    title: "Ruler-down dry hive",
    summary: "Volume soldiers → specialists → Brain → Memento → Oracle. Named workersRan.",
    stages: [
      { parallel: ["scout", "intel", "economics"] },
      { sequential: ["evidence", "redteam", "compliance", "pressure", "inversion", "wick", "copy"] },
      { sequential: ["brain", "memento", "conditioner"] },
    ],
    dryRunDefault: true,
  },
];

export function getWorkload(id) {
  return WORKLOADS.find((w) => w.id === id) || null;
}

const SPECIALIST_IDS = new Set([
  "conditioner",
  "redteam",
  "pressure",
  "compliance",
  "memento",
  "inversion",
  "wick",
]);

function mergeInput(base, extra) {
  return { ...base, ...extra };
}

function firstProduct(result = {}) {
  const bags = [result.products, result.items, result.lethalCandidates, result.top, result.liveItems];
  for (const bag of bags) {
    if (Array.isArray(bag) && bag.length) return bag[0];
  }
  return null;
}

/** Fold a soldier's output into the next stage's payload so Brain actually sees Scout/Intel. */
export function absorbWorker(payload, row) {
  const r = row?.result || {};
  const bags = [r.products, r.items, r.lethalCandidates, r.liveItems, r.top].filter((b) => Array.isArray(b));
  const incoming = bags.flat().filter((p) => p && (p.title || p.url));
  if (incoming.length) {
    payload.products = [...(payload.products || []), ...incoming];
    payload.items = payload.products;
    const first = incoming.find((p) => p.title && (p.url || p.image)) || incoming[0];
    if (first) {
      payload.title = payload.title || first.title;
      payload.salePrice = payload.salePrice ?? first.salePrice ?? first.price;
      payload.price = payload.price ?? payload.salePrice;
      payload.image = payload.image || first.image;
      payload.url = payload.url || first.url;
    }
  }
  if (r.market) payload.market = r.market;
  if (r.productCount != null) payload.productCount = (payload.productCount || 0) + Number(r.productCount || 0);
  payload.hiveSoldiers = [
    ...(payload.hiveSoldiers || []),
    {
      id: row.jobId || null,
      jobId: row.jobId || null,
      agent: row.agent,
      status: row.status,
      result: slimSoldierResult(r),
      error: row.error || null,
    },
  ];
  return payload;
}

function slimSoldierResult(r = {}) {
  const products = (r.products || r.items || r.liveItems || r.lethalCandidates || r.top || []).slice(0, 40);
  return {
    verdict: r.verdict || r.brief?.verdict || null,
    brief: r.brief || null,
    productCount: r.productCount ?? products.length,
    productsWithImages: r.productsWithImages ?? products.filter((p) => p?.image).length,
    productsWithUrls: r.productsWithUrls ?? products.filter((p) => p?.url).length,
    products,
    items: products,
    market: r.market || null,
    fourD: r.fourD || null,
    packId: r.packId || null,
    workerNote: r.workerNote || r.note || null,
    hiveSoldiersSeen: r.hiveSoldiersSeen || null,
    openMarkers: r.openMarkers || null,
    crimeShaped: Boolean(r.crimeShaped),
    policyHits: r.policyHits || null,
    vanityHits: r.vanityHits || null,
  };
}

function slimReply(row) {
  const r = row?.result || {};
  const first = firstProduct(r);
  return {
    agent: row.agent,
    status: row.status,
    verdict: r.verdict || r.brief?.verdict || null,
    productCount: r.productCount || (r.products || r.items || []).length || 0,
    productsWithImages: r.productsWithImages ?? null,
    productsWithUrls: r.productsWithUrls ?? null,
    title: first?.title || null,
    url: first?.url || null,
    hasImage: Boolean(first?.image),
    error: row.error || null,
  };
}

async function runAgent(agent, input, { launchAgent, contract }) {
  if (SPECIALIST_IDS.has(agent)) {
    return {
      agent,
      status: "done",
      result: runSpecialist(agent, input, { contractId: contract?.id }),
      contractId: contract?.id,
    };
  }
  const job = await launchAgent({
    agent,
    input,
    spawn: [],
    sync: true,
    dryRun: Boolean(input.dryRun),
    title: `${agent} ← ${contract?.id || "hive"}`,
  });
  return {
    agent,
    status: job.status,
    result: job.result,
    jobId: job.id,
    contractId: contract?.id,
    error: job.error || null,
  };
}

/**
 * Execute a named workload. Returns named workers, contracts, comms slice, and a hive brief.
 */
export async function runWorkload(id, input = {}) {
  const spec = getWorkload(id);
  if (!spec) throw Object.assign(new Error(`unknown workload: ${id}`), { status: 404 });
  const { launchAgent } = await import("../playground/board.js");
  const payload = { dryRun: spec.dryRunDefault, ...input };
  if (payload.dryRun == null) payload.dryRun = true;
  const workers = [];
  const contracts = [];
  let veto = null;

  for (const stage of spec.stages) {
    const roles = stage.parallel || stage.sequential || [];
    const live = roles.filter((r) => getAgent(r));
    const runOne = async (role) => {
      const extra = {};
      if (role === "conditioner") {
        extra.soldierId = extra.soldierId || payload.soldierId || "orchestrator";
        extra.residuals = (payload.residuals || []).concat(
          workers
            .filter((w) => w.result?.verdict)
            .map((w) => ({
              kind: w.result.verdict === "HOLD" || w.result.verdict === "KILL" ? "hold_saved" : "residual",
              source: w.jobId || w.agent,
              actual: w.result.verdict,
              expected: "fail-closed",
            }))
        );
        extra.jobIds = workers.map((w) => w.jobId).filter(Boolean);
      }
      if (role === "memento") {
        extra.proposedEntry = payload.proposedEntry || {
          soldierId: "hive",
          verdict: veto?.verdict || "noted",
          citation: contracts.at(-1)?.id || "hive",
          workersRan: workers.map((w) => w.agent),
        };
      }
      if (role === "redteam" && !payload.thesis) {
        extra.thesis = payload.thesis || `SKU "${payload.q || payload.title || "candidate"}" is ready to list`;
      }
      const contract = makeContract({
        from: "brain",
        to: role,
        goal: `${spec.title}: ${role}`,
        inputs: mergeInput(payload, extra),
        tools: getAgent(role)?.tools || [],
        onFailure: "HOLD",
      });
      contracts.push(contract);
      postContract(contract);
      const row = await runAgent(role, mergeInput(payload, extra), { launchAgent, contract });
      return row;
    };
    const finish = (row) => {
      workers.push(row);
      absorbWorker(payload, row);
      if (!SPECIALIST_IDS.has(row.agent)) {
        postReply({
          from: row.agent,
          to: "brain",
          contractId: row.contractId,
          payload: slimReply(row),
        });
      }
      if (row.result?.verdict === "VETO" || row.result?.crimeShaped) {
        veto = { agent: row.agent, verdict: row.result.verdict };
      }
    };
    if (stage.parallel) {
      const rows = await Promise.all(live.map(runOne));
      for (const row of rows) finish(row);
    } else {
      for (const role of live) {
        finish(await runOne(role));
        if (veto) break;
      }
    }
    if (veto) break;
  }

  const workersRan = workers.filter((w) => w.status === "done").map((w) => w.agent);
  const workersFailed = workers.filter((w) => w.status === "failed").map((w) => w.agent);
  const holds = workers.filter((w) => w.result?.verdict === "HOLD" || w.result?.verdict === "KILL").map((w) => w.agent);
  const brain = workers.find((w) => w.agent === "brain");
  const hiveBrief = {
    mission: spec.title,
    workload: spec.id,
    dryRun: Boolean(payload.dryRun),
    verdict: veto ? "VETO" : holds.length ? "HOLD" : brain?.result?.brief?.verdict || "CONDITIONAL",
    workersRan,
    workersFailed,
    workersSimulated: payload.dryRun ? workersRan.filter((a) => ["scout", "intel"].includes(a)) : [],
    holds,
    veto,
    productCount: (payload.products || []).length,
    productsWithImages: (payload.products || []).filter((p) => p.image).length,
    productsWithUrls: (payload.products || []).filter((p) => p.url).length,
    next: veto
      ? ["Stop. Compliance veto. Do not list."]
      : holds.length
        ? ["HOLD. Close markers / dual cost / Terapeak paste."]
        : ["Promote only after PASS + original photos."],
    caveat: "Hive never fabricates sold counts. Pack-only specialists are not Browse.",
  };

  return {
    workload: spec.id,
    title: spec.title,
    dryRun: Boolean(payload.dryRun),
    hiveBrief,
    workers,
    contracts: contracts.map((c) => ({ id: c.id, to: c.to, goal: c.goal })),
    comms: listComms(40),
    veto,
  };
}
