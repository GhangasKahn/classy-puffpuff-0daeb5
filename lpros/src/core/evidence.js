/**
 * Evidence pack — operator / Terapeak / second-supplier intake.
 * Turns CONDITIONAL candidates into PASS when sold + dual-cost evidence is real.
 */
import { verifyProduct } from "./verify.js";
import { netProfitPerSale } from "./economics.js";

/**
 * Merge an evidence pack into a candidate (immutable-ish: returns new object).
 * @param {object} candidate
 * @param {object} pack
 * @param {number} [pack.soldCount] - 90d sold from Terapeak / Insights
 * @param {number} [pack.avgSoldPrice]
 * @param {number} [pack.sellThrough] - 0–1
 * @param {string} [pack.demandSource] - default terapeak
 * @param {number} [pack.productCost] - primary landed cost
 * @param {number} [pack.altProductCost] - second supplier quote
 * @param {number} [pack.leadTimeDays]
 * @param {boolean} [pack.productCostEstimated]
 * @param {string} [pack.note]
 */
export function applyEvidencePack(candidate, pack = {}) {
  const demandSource = pack.demandSource || "terapeak";
  const sources = new Set([...(candidate.demandSources || []), "ebay_browse"]);
  const soldCount =
    pack.soldCount != null ? Number(pack.soldCount) : Number(candidate.soldCount || 0);
  const hasSold = soldCount > 0;

  if (hasSold) sources.add(demandSource);

  const productCost =
    pack.productCost != null ? Number(pack.productCost) : Number(candidate.productCost);
  const altProductCost =
    pack.altProductCost != null
      ? Number(pack.altProductCost)
      : candidate.altProductCost != null
        ? Number(candidate.altProductCost)
        : null;

  const salePrice =
    pack.avgSoldPrice != null
      ? Number(pack.avgSoldPrice)
      : Number(candidate.salePrice ?? candidate.price);

  const merged = {
    ...candidate,
    salePrice,
    productCost,
    altProductCost,
    productCostEstimated:
      pack.productCostEstimated != null
        ? Boolean(pack.productCostEstimated)
        : pack.productCost != null
          ? false
          : Boolean(candidate.productCostEstimated),
    leadTimeDays:
      pack.leadTimeDays != null
        ? Number(pack.leadTimeDays)
        : Number(candidate.leadTimeDays ?? 7),
    soldCount,
    soldEvidenceMissing: !hasSold,
    evidenceStatus: hasSold ? "ok" : candidate.evidenceStatus || "partial",
    demandSources: [...sources],
    sellThrough: pack.sellThrough != null ? Number(pack.sellThrough) : candidate.sellThrough,
    str: pack.sellThrough != null ? Number(pack.sellThrough) : candidate.str,
    demandConfidence: hasSold
      ? Math.min(0.95, 0.35 + Math.log10(soldCount + 1) * 0.25)
      : candidate.demandConfidence ?? 0.2,
    evidenceNote: pack.note || candidate.evidenceNote,
    evidenceAppliedAt: new Date().toISOString(),
  };

  return merged;
}

/**
 * Re-run zero-trust verify after evidence merge; returns economics + decision.
 */
export function hardenCandidate(candidate, pack = {}, thresholds = {}) {
  const merged = applyEvidencePack(candidate, pack);
  const verification = verifyProduct(merged, thresholds);
  const economics =
    verification.economics ||
    netProfitPerSale({
      salePrice: merged.salePrice,
      productCost: merged.productCost,
      returnsBufferRate: merged.returnsBufferRate ?? 0.04,
    });

  return {
    candidate: merged,
    verification,
    economics,
    cleared:
      verification.decision === "PASS" &&
      !(verification.flags || []).includes("sold_evidence_missing") &&
      !(verification.flags || []).includes("single_source_cost"),
    remainingFlags: verification.flags || [],
    decision: verification.decision,
  };
}
