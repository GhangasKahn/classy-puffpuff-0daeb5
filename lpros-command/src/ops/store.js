/**
 * Local JSON store for real-world ops (SKUs, orders, exports metadata).
 * Survives restarts; gitignored under lpros-command/data/.
 */
import {
  readFileSync,
  writeFileSync,
  existsSync,
  mkdirSync,
} from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../../data");

export function dataPath(...parts) {
  return resolve(root, ...parts);
}

export function ensureDataDir(...parts) {
  const dir = parts.length ? dataPath(...parts) : root;
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
  return dir;
}

export function readJson(file, fallback) {
  const p = dataPath(file);
  if (!existsSync(p)) return typeof fallback === "function" ? fallback() : fallback;
  try {
    return JSON.parse(readFileSync(p, "utf8"));
  } catch {
    return typeof fallback === "function" ? fallback() : fallback;
  }
}

export function writeJson(file, data) {
  ensureDataDir();
  const p = dataPath(file);
  writeFileSync(p, JSON.stringify(data, null, 2) + "\n");
  return p;
}

export function appendJsonl(file, row) {
  ensureDataDir();
  const p = dataPath(file);
  writeFileSync(p, JSON.stringify({ ts: new Date().toISOString(), ...row }) + "\n", {
    flag: "a",
  });
  return p;
}

export function slugSku(title, salePrice) {
  const base = String(title || "sku")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 40);
  const price = salePrice != null ? Math.round(Number(salePrice)) : 0;
  const salt = Date.now().toString(36).slice(-4);
  return `LPROS-${base || "item"}-${price}-${salt}`.toUpperCase();
}
