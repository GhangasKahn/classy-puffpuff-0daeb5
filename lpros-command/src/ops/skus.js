/**
 * SKU registry — promote PASS candidates into a durable operator workbook.
 */
import { draftListing } from "../../../lpros/src/agents/listing.js";
import { hardenCandidate } from "../../../lpros/src/core/evidence.js";
import { readJson, writeJson, slugSku, appendJsonl } from "./store.js";

const FILE = "skus.json";

function empty() {
  return { version: 1, updatedAt: null, skus: [] };
}

export function listSkus({ status } = {}) {
  const db = readJson(FILE, empty);
  let rows = db.skus || [];
  if (status) rows = rows.filter((s) => s.status === status);
  return { updatedAt: db.updatedAt, count: rows.length, skus: rows };
}

export function getSku(sku) {
  return (readJson(FILE, empty).skus || []).find((s) => s.sku === sku) || null;
}

export function upsertSku(entry) {
  const db = readJson(FILE, empty);
  const sku = entry.sku || slugSku(entry.title, entry.salePrice);
  const idx = db.skus.findIndex((s) => s.sku === sku);
  const now = new Date().toISOString();
  const row = {
    ...(idx >= 0 ? db.skus[idx] : {}),
    ...entry,
    sku,
    updatedAt: now,
    createdAt: idx >= 0 ? db.skus[idx].createdAt : now,
  };
  if (idx >= 0) db.skus[idx] = row;
  else db.skus.unshift(row);
  db.updatedAt = now;
  writeJson(FILE, db);
  appendJsonl("sku-events.jsonl", { type: "upsert", sku, status: row.status });
  return row;
}

/**
 * Promote a lethal-board / evidence-hardened row into the registry.
 */
export function promoteCandidate(candidate = {}, opts = {}) {
  const evidence = opts.evidence || null;
  let decision = candidate.decision || "CANDIDATE";
  let flags = candidate.flags || [];
  let net = candidate.net;
  let marginPct = candidate.marginPct;
  let verification = null;

  const cost =
    opts.productCost ??
    evidence?.productCost ??
    (candidate.salePrice != null && opts.costRatio
      ? candidate.salePrice * opts.costRatio
      : candidate.productCost);

  if (evidence || opts.requireHarden) {
    const hardened = hardenCandidate(
      {
        title: candidate.title,
        salePrice: candidate.salePrice ?? candidate.price,
        productCost: cost,
        productCostEstimated: cost == null,
        leadTimeDays: evidence?.leadTimeDays ?? opts.leadTimeDays ?? 7,
        soldEvidenceMissing: true,
        evidenceStatus: "partial",
        demandSources: ["ebay_browse"],
        activeCount: opts.activeCount ?? 40,
        density: opts.density ?? 50,
        perceivedValue: candidate.perceivedValue ?? 0.45,
        remorseRisk: 0.35,
        scammy: Boolean(candidate.scammy),
        hasImages: true,
        hasItemSpecifics: true,
        str: opts.str ?? 0.015,
        problemSolving: true,
      },
      evidence || {},
      {
        minSalePrice: opts.minPrice ?? 35,
        maxSalePrice: opts.maxPrice ?? 200,
      }
    );
    decision = hardened.decision;
    flags = hardened.remainingFlags;
    net = hardened.economics?.net;
    marginPct = hardened.economics?.marginPct;
    verification = {
      confidence: hardened.verification?.verificationConfidence,
      passCount: hardened.verification?.passCount,
    };
  }

  const draft = draftListing({
    title: candidate.title,
    salePrice: candidate.salePrice ?? candidate.price,
    url: candidate.url,
    condition: candidate.condition || "NEW",
  });

  const status =
    decision === "PASS"
      ? "ready"
      : decision === "CONDITIONAL"
        ? "needs_evidence"
        : decision === "FAIL"
          ? "killed"
          : "watch";

  return upsertSku({
    sku: opts.sku,
    title: candidate.title,
    sourceUrl: candidate.url || null,
    salePrice: Number(candidate.salePrice ?? candidate.price) || null,
    productCost: cost != null ? Number(cost) : null,
    altProductCost:
      evidence?.altProductCost != null ? Number(evidence.altProductCost) : null,
    categoryId: opts.categoryId || candidate.categoryId || "25339",
    quantity: opts.quantity ?? 3,
    condition: "NEW",
    decision,
    flags,
    status,
    net,
    marginPct,
    perceivedValue: candidate.perceivedValue,
    psychFit: candidate.psychFit,
    draft,
    verification,
    evidence: evidence || null,
    notes: opts.notes || null,
  });
}

export function setSkuStatus(sku, status, patch = {}) {
  const row = getSku(sku);
  if (!row) throw Object.assign(new Error(`SKU not found: ${sku}`), { status: 404 });
  return upsertSku({ ...row, ...patch, status });
}

export function removeSku(sku) {
  const db = readJson(FILE, empty);
  const before = db.skus.length;
  db.skus = db.skus.filter((s) => s.sku !== sku);
  if (db.skus.length === before) {
    throw Object.assign(new Error(`SKU not found: ${sku}`), { status: 404 });
  }
  db.updatedAt = new Date().toISOString();
  writeJson(FILE, db);
  appendJsonl("sku-events.jsonl", { type: "remove", sku });
  return { ok: true, sku };
}
