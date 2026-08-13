/**
 * Load OpenClaw-style elite packs from lpros-agents/<id>/.
 * Packs are the agent. JS workers are optional desk wiring.
 */
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const AGENTS_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

export const REQUIRED_PACK_FILES = [
  "SOUL.md",
  "IDENTITY.md",
  "AGENTS.md",
  "TOOLS.md",
  "HEARTBEAT.md",
  "MEMORY.md",
];

/** Canonical roster — every id must have the six files. */
export const ELITE_PACKS = [
  "orchestrator",
  "scout",
  "intel",
  "verifier",
  "economist",
  "fulfiller",
  "copywriter",
  "conditioner",
  "redteam",
  "pressure",
  "compliance",
  "taxonomy",
  "memento",
  "inversion",
  "factory",
  "wick",
  "browser",
  "vm",
  "swarm",
];

/** Playground catalog id → pack folder (when they differ). */
export const CATALOG_TO_PACK = {
  brain: "orchestrator",
  scout: "scout",
  intel: "intel",
  crawler: "taxonomy",
  economics: "economist",
  evidence: "verifier",
  copy: "copywriter",
  factory: "factory",
  fulfill: "fulfiller",
  conditioner: "conditioner",
  redteam: "redteam",
  pressure: "pressure",
  compliance: "compliance",
  memento: "memento",
  inversion: "inversion",
  taxonomy: "taxonomy",
  orchestrator: "orchestrator",
  economist: "economist",
  verifier: "verifier",
  copywriter: "copywriter",
  fulfiller: "fulfiller",
  wick: "wick",
  browser: "browser",
  vm: "vm",
  swarm: "swarm",
};

export function packDir(id) {
  return resolve(AGENTS_ROOT, id);
}

export function packExists(id) {
  return REQUIRED_PACK_FILES.every((f) => existsSync(resolve(packDir(id), f)));
}

export function missingPackFiles(id) {
  return REQUIRED_PACK_FILES.filter((f) => !existsSync(resolve(packDir(id), f)));
}

function firstNonEmptyLine(text) {
  return String(text || "")
    .split("\n")
    .map((l) => l.trim())
    .find((l) => l && !l.startsWith("#")) || "";
}

function excerpt(text, max = 900) {
  const t = String(text || "").trim();
  if (t.length <= max) return t;
  return `${t.slice(0, max).trim()}…`;
}

export function loadPack(id) {
  const dir = packDir(id);
  if (!existsSync(dir)) {
    throw Object.assign(new Error(`unknown hermes pack: ${id}`), { status: 404 });
  }
  const missing = missingPackFiles(id);
  if (missing.length) {
    throw Object.assign(new Error(`incomplete hermes pack ${id}: missing ${missing.join(", ")}`), {
      status: 409,
    });
  }
  const files = {};
  for (const f of REQUIRED_PACK_FILES) {
    files[f] = readFileSync(resolve(dir, f), "utf8");
  }
  const soul = files["SOUL.md"];
  const identity = files["IDENTITY.md"];
  return {
    id,
    complete: true,
    files: REQUIRED_PACK_FILES,
    mold: (soul.split("\n").find((l) => l.startsWith("# Mold:")) || "").replace(/^#\s*/, ""),
    voice: firstNonEmptyLine(soul),
    soulExcerpt: excerpt(soul, 1200),
    identityExcerpt: excerpt(identity, 800),
    proceduresExcerpt: excerpt(files["AGENTS.md"], 700),
    heartbeatExcerpt: excerpt(files["HEARTBEAT.md"], 400),
    memoryExcerpt: excerpt(files["MEMORY.md"], 400),
    toolsExcerpt: excerpt(files["TOOLS.md"], 400),
    lengths: Object.fromEntries(REQUIRED_PACK_FILES.map((f) => [f, files[f].length])),
    note: "Persona pack loaded. This is the agent. JS worker may still be a stub — do not treat markdown as a live Browse run.",
  };
}

export function packBriefForCatalog(catalogId) {
  const packId = CATALOG_TO_PACK[catalogId] || catalogId;
  if (!ELITE_PACKS.includes(packId) && !packExists(packId)) return null;
  try {
    const pack = loadPack(packId);
    return {
      packId,
      mold: pack.mold,
      voice: pack.voice,
      complete: pack.complete,
    };
  } catch {
    return { packId, complete: false };
  }
}

export function listPacks() {
  return ELITE_PACKS.map((id) => ({
    id,
    complete: packExists(id),
    missing: missingPackFiles(id),
    dir: packDir(id),
  }));
}

export function discoverPackFolders() {
  return readdirSync(AGENTS_ROOT, { withFileTypes: true })
    .filter((d) => d.isDirectory() && !d.name.startsWith(".") && d.name !== "src" && d.name !== "brain")
    .map((d) => d.name)
    .sort();
}
