/**
 * Shared orchestration job persistence (durable under lpros-command/data/orch).
 */
import { EventEmitter } from "node:events";
import fs from "node:fs";
import path from "node:path";
import { dataPath, ensureDataDir } from "../ops/store.js";

export const orchBus = new EventEmitter();
orchBus.setMaxListeners(80);

export function orchDir() {
  if (process.env.LPROS_ORCH_DIR) {
    const d = process.env.LPROS_ORCH_DIR;
    if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true });
    return d;
  }
  return ensureDataDir("orch");
}

export function jobPath(id) {
  return path.join(orchDir(), `${id}.json`);
}

/** @type {Map<string, object>} */
export const jobMem = new Map();

export function persistJob(job) {
  try {
    fs.writeFileSync(jobPath(job.id), JSON.stringify(job, null, 2));
  } catch {
    /* ignore */
  }
}

export function loadJob(jobId) {
  if (jobMem.has(jobId)) return jobMem.get(jobId);
  const p = jobPath(jobId);
  if (fs.existsSync(p)) {
    const job = JSON.parse(fs.readFileSync(p, "utf8"));
    jobMem.set(jobId, job);
    return job;
  }
  return null;
}

export function appendJobEvent(job, level, message, data = {}) {
  const ev = { at: new Date().toISOString(), level, message, ...data };
  job.events = job.events || [];
  job.events.push(ev);
  const cap = job.type === "campaign" ? 4000 : 2000;
  if (job.events.length > cap) job.events.splice(0, job.events.length - cap);
  orchBus.emit("event", { jobId: job.id, event: ev });
  persistJob(job);
  return ev;
}

export function requestCancel(jobId) {
  const job = loadJob(jobId);
  if (!job) return null;
  job.cancelRequested = true;
  job.updatedAt = new Date().toISOString();
  appendJobEvent(job, "warn", "Cancel requested — will stop after current lane/phase", {
    phase: "cancel",
  });
  return job;
}

export function isCancelled(job) {
  return Boolean(job?.cancelRequested);
}
