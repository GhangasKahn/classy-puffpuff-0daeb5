/**
 * Playground board — create jobs, launch sub-agents, cancel/retry.
 */
import { AGENT_CATALOG, getAgent, JOB_KINDS, PRIORITIES } from "./catalog.js";
import { appendEvent, listKind, load, nid, persist, slimJob } from "./store.js";
import { executeJob } from "./runner.js";
import { promoteCandidate } from "../ops/skus.js";

function titleFor(kind, agent, input = {}) {
  if (input.title) return String(input.title).slice(0, 120);
  if (agent) return `${agent}: ${input.q || input.recipe || input.playbookId || input.url || "run"}`.slice(0, 120);
  return `${kind} job`;
}

export function createJob({
  kind = "agent",
  agent = null,
  title,
  priority = "P1",
  parentId = null,
  input = {},
  start = false,
} = {}) {
  if (kind && !JOB_KINDS.includes(kind)) {
    throw Object.assign(new Error(`invalid kind: ${kind}`), { status: 400 });
  }
  if (agent && !getAgent(agent)) {
    throw Object.assign(new Error(`unknown agent: ${agent}`), { status: 400 });
  }
  if (priority && !PRIORITIES.includes(priority)) priority = "P1";
  const now = new Date().toISOString();
  const job = {
    id: nid("pg"),
    kind: agent && kind === "agent" ? "agent" : kind,
    agent: agent || null,
    title: title || titleFor(kind, agent, input),
    status: "queued",
    priority,
    parentId,
    children: [],
    input: { ...input },
    result: null,
    error: null,
    progress: { phase: "queued", pct: 0 },
    events: [],
    createdAt: now,
    updatedAt: now,
  };
  persist("job", job);
  appendEvent(job, "info", `Created ${job.kind}${job.agent ? ` / ${job.agent}` : ""}`, { phase: "queued" });
  if (parentId) {
    const parent = load("job", parentId);
    if (parent) {
      parent.children = [...new Set([...(parent.children || []), job.id])];
      persist("job", parent);
    }
  }
  return job;
}

export function getJob(id) {
  return load("job", id);
}

export function listJobs({ status, agent, kind, limit = 80 } = {}) {
  let rows = listKind("job", 200);
  if (status) rows = rows.filter((j) => j.status === status);
  if (agent) rows = rows.filter((j) => j.agent === agent);
  if (kind) rows = rows.filter((j) => j.kind === kind);
  return rows.slice(0, limit);
}

export function boardSummary() {
  const jobs = listKind("job", 200);
  const byStatus = {};
  for (const j of jobs) byStatus[j.status] = (byStatus[j.status] || 0) + 1;
  const agents = {};
  for (const j of jobs) {
    if (!j.agent) continue;
    agents[j.agent] = (agents[j.agent] || 0) + 1;
  }
  return {
    total: jobs.length,
    byStatus,
    agents,
    running: jobs.filter((j) => j.status === "running").map(slimJob),
  };
}

export function cancelJob(id) {
  const job = load("job", id);
  if (!job) return null;
  job.cancelRequested = true;
  if (job.status === "queued" || job.status === "hold") job.status = "cancelled";
  appendEvent(job, "warn", "Cancel requested", { phase: "cancel" });
  for (const cid of job.children || []) {
    const child = load("job", cid);
    if (child && (child.status === "queued" || child.status === "running" || child.status === "hold")) {
      child.cancelRequested = true;
      if (child.status === "queued" || child.status === "hold") child.status = "cancelled";
      appendEvent(child, "warn", "Cancel (parent)", { phase: "cancel" });
    }
  }
  return job;
}

export function setJobStatus(id, status) {
  const job = load("job", id);
  if (!job) return null;
  const allowed = ["queued", "hold", "cancelled"];
  if (!allowed.includes(status)) {
    throw Object.assign(new Error("can only move to queued / hold / cancelled from the board"), { status: 400 });
  }
  if (job.status === "running") {
    throw Object.assign(new Error("stop a running job with cancel"), { status: 409 });
  }
  job.status = status;
  appendEvent(job, "info", `Board → ${status}`, { phase: status });
  return job;
}

export async function startJob(id, { sync = true } = {}) {
  const job = load("job", id);
  if (!job) return null;
  if (job.status === "running") return job;
  if (sync) return executeJob(id);
  job.status = "queued";
  persist("job", job);
  setImmediate(() => {
    executeJob(id).catch(() => {});
  });
  return job;
}

export async function retryJob(id, { sync = true } = {}) {
  const job = load("job", id);
  if (!job) return null;
  job.status = "queued";
  job.error = null;
  job.cancelRequested = false;
  job.result = null;
  job.progress = { phase: "queued", pct: 0 };
  appendEvent(job, "info", "Retry", { phase: "queued" });
  return startJob(id, { sync });
}

/**
 * Launch a sub-agent. Optionally spawn soldiers as child jobs (Brain default).
 */
export async function launchAgent({
  agent,
  input = {},
  spawn = null,
  priority = "P1",
  title,
  sync = true,
  dryRun = false,
} = {}) {
  const spec = getAgent(agent);
  if (!spec) throw Object.assign(new Error(`unknown agent: ${agent}`), { status: 400 });
  const kind = agent === "browser" ? "browser" : agent === "vm" ? "vm" : "agent";
  const payload = { ...input, dryRun: Boolean(dryRun || input.dryRun) };
  const parent = createJob({
    kind,
    agent,
    title: title || `${spec.title}: ${payload.q || payload.recipe || payload.playbookId || "run"}`,
    priority,
    input: payload,
  });

  const spawnList = spawn == null && spec.spawnDefault && !payload.noSpawn ? spec.spawnDefault : spawn || [];
  for (const role of spawnList) {
    if (!getAgent(role)) continue;
    createJob({
      kind: role === "browser" ? "browser" : role === "vm" ? "vm" : "agent",
      agent: role,
      parentId: parent.id,
      priority,
      input: payload,
      title: `${role} ← ${parent.id}`,
    });
  }
  const fresh = load("job", parent.id);
  if (sync) return executeJob(fresh.id);
  setImmediate(() => {
    executeJob(fresh.id).catch(() => {});
  });
  return load("job", fresh.id);
}

export function catalog() {
  return {
    agents: AGENT_CATALOG,
    note: "Soldiers run under Brain contracts. Capital actions HOLD. No eBay HTML scrape.",
  };
}

export function jobTree(id) {
  const job = load("job", id);
  if (!job) return null;
  return {
    job: slimJob(job),
    parent: job.parentId ? slimJob(load("job", job.parentId)) : null,
    children: (job.children || []).map((cid) => slimJob(load("job", cid))).filter(Boolean),
    events: (job.events || []).slice(-40),
    brief: job.result?.brief || null,
    verdict: job.result?.brief?.verdict || job.result?.decision || null,
  };
}

export function activityFeed(limit = 50) {
  const jobs = listKind("job", 80);
  const evs = [];
  for (const j of jobs) {
    for (const e of j.events || []) {
      evs.push({
        jobId: j.id,
        agent: j.agent,
        title: j.title,
        status: j.status,
        at: e.at,
        level: e.level,
        message: e.message,
        phase: e.phase,
      });
    }
  }
  evs.sort((a, b) => String(b.at).localeCompare(String(a.at)));
  return evs.slice(0, limit);
}

export function commentJob(id, text) {
  const job = load("job", id);
  if (!job) return null;
  const msg = String(text || "").trim().slice(0, 500);
  if (!msg) throw Object.assign(new Error("comment required"), { status: 400 });
  appendEvent(job, "note", msg, { phase: "note" });
  return job;
}

export async function applySessionEvidence(sessionId, { q, title, salePrice, sync = true, relaunchBrain = false } = {}) {
  const { getSession, mergedCaptures } = await import("./browser.js");
  const session = getSession(sessionId);
  if (!session) throw Object.assign(new Error("session not found"), { status: 404 });
  const cap = mergedCaptures(session);
  const input = {
    q: q || title || "desk organizer",
    title: title || q || "Candidate",
    salePrice: salePrice ?? cap.avgSoldPrice ?? 49,
    soldCount: cap.soldCount,
    productCost: cap.productCost,
    altProductCost: cap.altProductCost,
    demandSource: "terapeak",
    leadTimeDays: cap.leadTimeDays || 7,
  };
  const evidence = await launchAgent({ agent: "evidence", input, sync, spawn: [] });
  let brain = null;
  if (relaunchBrain) {
    brain = await launchAgent({
      agent: "brain",
      input: { ...input, dryRun: true },
      dryRun: true,
      spawn: ["economics"],
      sync,
    });
  }
  return { capture: cap, evidence, brain };
}

export function promoteFromJob(id) {
  const job = load("job", id);
  if (!job) return null;
  const verdict = job.result?.brief?.verdict || job.result?.decision;
  const evidencePass = job.agent === "evidence" && job.result?.decision === "PASS";
  if (verdict !== "PASS_READY" && !evidencePass) {
    throw Object.assign(new Error("job is not PASS_READY / PASS — capture sold + dual cost first"), {
      status: 409,
      verdict,
    });
  }
  const input = job.input || {};
  const title = input.title || input.q || job.title;
  const salePrice = Number(input.salePrice ?? input.price ?? 49);
  const row = promoteCandidate(
    { title, salePrice, perceivedValue: 0.55 },
    {
      requireHarden: true,
      categoryId: input.categoryId || "25339",
      evidence: {
        soldCount: input.soldCount,
        productCost: input.productCost ?? input.cost,
        altProductCost: input.altProductCost,
        leadTimeDays: input.leadTimeDays || 7,
        demandSource: "terapeak",
      },
    }
  );
  appendEvent(job, "info", `Promoted ${row.sku} → ${row.status} (${row.decision})`, { phase: "promote" });
  job.result = { ...(job.result || {}), promoted: { sku: row.sku, status: row.status, decision: row.decision } };
  persist("job", job);
  return { sku: row, job: slimJob(job) };
}
