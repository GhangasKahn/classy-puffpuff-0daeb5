/**
 * Outcome / Learning Agent — logs outcomes and applies simple online weight nudges.
 * Conditioning hooks (authoritative + Pavlovian) attach here later; keep math honest.
 */
import { writeFileSync, readFileSync, existsSync, mkdirSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const dataDir = process.env.LPROS_DATA_DIR
  ? resolve(process.env.LPROS_DATA_DIR)
  : process.env.NETLIFY || process.env.AWS_LAMBDA_FUNCTION_NAME
    ? resolve("/tmp/lpros-outcomes")
    : resolve(dirname(fileURLToPath(import.meta.url)), "../../data");
const logPath = resolve(dataDir, "outcomes.jsonl");
const weightsPath = resolve(dataDir, "psych_weights.json");

const DEFAULT_WEIGHTS = {
  remorse: 0.22,
  fomo: 0.18,
  greene: 0.12,
  hero: 0.1,
  caregiver: 0.08,
  adler: 0.08,
  voss: 0.1,
  hughes: 0.12,
};

export function logOutcome(row) {
  if (!existsSync(dataDir)) mkdirSync(dataDir, { recursive: true });
  const line = JSON.stringify({ ts: new Date().toISOString(), ...row }) + "\n";
  writeFileSync(logPath, line, { flag: "a" });
}

/** Most recent outcomes (newest first). */
export function readRecentOutcomes(limit = 50) {
  if (!existsSync(logPath)) return [];
  const lines = readFileSync(logPath, "utf8")
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
  const rows = [];
  for (let i = lines.length - 1; i >= 0 && rows.length < limit; i--) {
    try {
      rows.push(JSON.parse(lines[i]));
    } catch {
      /* skip corrupt */
    }
  }
  return rows;
}

/**
 * Record a sale/return outcome and nudge psych weights.
 */
export function recordSaleOutcome({
  title,
  sku,
  profitable,
  returned,
  net,
  salePrice,
  featureSnapshot,
  note,
} = {}) {
  const row = {
    type: "sale_outcome",
    title,
    sku,
    profitable: Boolean(profitable),
    returned: Boolean(returned),
    net: net != null ? Number(net) : null,
    salePrice: salePrice != null ? Number(salePrice) : null,
    note: note || null,
  };
  logOutcome(row);
  const weights = nudgeWeightsFromOutcome({
    profitable: row.profitable,
    returned: row.returned,
    featureSnapshot,
  });
  return { outcome: row, weights };
}

export function loadWeights() {
  if (!existsSync(weightsPath)) return { ...DEFAULT_WEIGHTS };
  try {
    return { ...DEFAULT_WEIGHTS, ...JSON.parse(readFileSync(weightsPath, "utf8")) };
  } catch {
    return { ...DEFAULT_WEIGHTS };
  }
}

/**
 * Tiny online nudge: if listing was profitable, slightly boost features that were high;
 * if returned/lost, boost remorse weight. Not full ML — honest incremental conditioning signal.
 */
export function nudgeWeightsFromOutcome({ profitable, returned, featureSnapshot }) {
  const w = loadWeights();
  const lr = 0.01;
  if (returned) w.remorse = clamp(w.remorse + lr * 2);
  if (profitable && featureSnapshot?.fomo) w.fomo = clamp(w.fomo + lr * featureSnapshot.fomo);
  if (profitable && featureSnapshot?.vossEmpathy) w.voss = clamp(w.voss + lr * featureSnapshot.vossEmpathy);
  if (!existsSync(dataDir)) mkdirSync(dataDir, { recursive: true });
  writeFileSync(weightsPath, JSON.stringify(w, null, 2));
  return w;
}

function clamp(x) {
  return Math.min(0.4, Math.max(0.05, x));
}

export { DEFAULT_WEIGHTS };
