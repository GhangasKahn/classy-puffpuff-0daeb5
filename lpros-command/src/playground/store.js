/**
 * Durable playground store — jobs, agents, browser sessions, VM runs.
 */
import { randomBytes } from "node:crypto";
import { EventEmitter } from "node:events";
import fs from "node:fs";
import path from "node:path";
import { ensureDataDir } from "../ops/store.js";

export const playgroundBus = new EventEmitter();
playgroundBus.setMaxListeners(80);

export function playgroundDir() {
  return ensureDataDir("playground");
}

function fileFor(kind, id) {
  return path.join(playgroundDir(), `${kind}-${id}.json`);
}

/** @type {Map<string, object>} */
const mem = new Map();

export function nid(prefix) {
  return `${prefix}_${Date.now().toString(36)}_${randomBytes(3).toString("hex")}`;
}

export function persist(kind, doc) {
  mem.set(`${kind}:${doc.id}`, doc);
  try {
    fs.writeFileSync(fileFor(kind, doc.id), JSON.stringify(doc, null, 2));
  } catch {
    /* ignore */
  }
  return doc;
}

export function load(kind, id) {
  const k = `${kind}:${id}`;
  if (mem.has(k)) return mem.get(k);
  const p = fileFor(kind, id);
  if (fs.existsSync(p)) {
    const doc = JSON.parse(fs.readFileSync(p, "utf8"));
    mem.set(k, doc);
    return doc;
  }
  return null;
}

export function listKind(kind, limit = 80) {
  const dir = playgroundDir();
  const prefix = `${kind}-`;
  const files = fs.existsSync(dir)
    ? fs.readdirSync(dir).filter((f) => f.startsWith(prefix) && f.endsWith(".json"))
    : [];
  const rows = [];
  for (const f of files) {
    const id = f.slice(prefix.length, -5);
    const doc = load(kind, id);
    if (doc) rows.push(doc);
  }
  rows.sort((a, b) => String(b.updatedAt || b.createdAt).localeCompare(String(a.updatedAt || a.createdAt)));
  return rows.slice(0, limit);
}

export function appendEvent(job, level, message, extra = {}) {
  const ev = { at: new Date().toISOString(), level, message, ...extra };
  job.events = job.events || [];
  job.events.push(ev);
  if (job.events.length > 400) job.events.splice(0, job.events.length - 400);
  job.updatedAt = ev.at;
  persist("job", job);
  playgroundBus.emit("event", { jobId: job.id, event: ev });
  return ev;
}

export function slimJob(job) {
  if (!job) return null;
  return {
    id: job.id,
    kind: job.kind,
    agent: job.agent || null,
    title: job.title,
    status: job.status,
    priority: job.priority,
    parentId: job.parentId || null,
    children: job.children || [],
    progress: job.progress || null,
    createdAt: job.createdAt,
    updatedAt: job.updatedAt,
    error: job.error || null,
    verdict: job.result?.verdict || job.result?.brief?.verdict || null,
    dryRun: Boolean(job.input?.dryRun),
  };
}
