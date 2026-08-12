/**
 * Publish-ready listing packages + CSV for Seller Hub / File Exchange.
 * Usable today without Sell API user OAuth.
 */
import { writeFileSync } from "node:fs";
import { draftListing } from "../../../lpros/src/agents/listing.js";
import { ensureDataDir, dataPath, appendJsonl } from "./store.js";
import { listSkus, getSku } from "./skus.js";

/** Build one publish package from a registry SKU. */
export function buildListingPackage(skuRow, opts = {}) {
  if (!skuRow) throw Object.assign(new Error("sku required"), { status: 400 });
  const draft = skuRow.draft || draftListing(skuRow);
  const price = Number(skuRow.salePrice);
  const qty = Number(skuRow.quantity ?? 1);
  const categoryId = String(skuRow.categoryId || opts.categoryId || "25339");

  const inventoryItem = {
    sku: skuRow.sku,
    product: {
      title: draft.title.slice(0, 80),
      description: draft.descriptionHtml,
      aspects: Object.fromEntries(
        Object.entries(draft.itemSpecifics || {}).map(([k, v]) => [k, [String(v)]])
      ),
      imageUrls: skuRow.imageUrls || [],
    },
    condition: mapCondition(skuRow.condition),
    availability: {
      shipToLocationAvailability: { quantity: qty },
    },
  };

  const offer = {
    sku: skuRow.sku,
    marketplaceId: opts.marketplaceId || "EBAY_US",
    format: "FIXED_PRICE",
    availableQuantity: qty,
    categoryId,
    listingDescription: draft.descriptionHtml,
    listingPolicies: {
      fulfillmentPolicyId: opts.fulfillmentPolicyId || process.env.EBAY_FULFILLMENT_POLICY_ID || null,
      paymentPolicyId: opts.paymentPolicyId || process.env.EBAY_PAYMENT_POLICY_ID || null,
      returnPolicyId: opts.returnPolicyId || process.env.EBAY_RETURN_POLICY_ID || null,
    },
    pricingSummary: {
      price: { value: price.toFixed(2), currency: "USD" },
    },
    merchantLocationKey: opts.merchantLocationKey || process.env.EBAY_MERCHANT_LOCATION_KEY || null,
  };

  const sellerHub = {
    sku: skuRow.sku,
    title: draft.title.slice(0, 80),
    categoryId,
    conditionID: 1000,
    price,
    quantity: qty,
    description: draft.bullets?.join("\n• ") || "",
    itemSpecifics: draft.itemSpecifics,
    productCost: skuRow.productCost,
    altProductCost: skuRow.altProductCost,
    decision: skuRow.decision,
    status: skuRow.status,
    sourceUrl: skuRow.sourceUrl,
  };

  const blockers = [];
  if (skuRow.status !== "ready" && skuRow.decision !== "PASS") {
    blockers.push(`status=${skuRow.status} decision=${skuRow.decision} — harden evidence first`);
  }
  if (!(price > 0)) blockers.push("missing sale price");
  if (!offer.listingPolicies.fulfillmentPolicyId) {
    blockers.push("missing EBAY_FULFILLMENT_POLICY_ID (required for live Inventory offer)");
  }
  if (!offer.listingPolicies.paymentPolicyId) {
    blockers.push("missing EBAY_PAYMENT_POLICY_ID");
  }
  if (!offer.listingPolicies.returnPolicyId) {
    blockers.push("missing EBAY_RETURN_POLICY_ID");
  }
  if (!(skuRow.imageUrls || []).length) {
    blockers.push("no imageUrls — add supplier/own photos before publish");
  }

  return {
    sku: skuRow.sku,
    ready: blockers.length === 0,
    blockers,
    draft,
    sellerHub,
    inventoryItem,
    offer,
    cash: {
      salePrice: price,
      productCost: skuRow.productCost,
      net: skuRow.net,
      marginPct: skuRow.marginPct,
    },
  };
}

export function buildPackagesForStatus(status = "ready", opts = {}) {
  const { skus } = listSkus({ status });
  return skus.map((s) => buildListingPackage(s, opts));
}

/** CSV columns useful for manual Seller Hub / spreadsheet ops. */
export function packagesToCsv(packages) {
  const headers = [
    "SKU",
    "Title",
    "CategoryID",
    "ConditionID",
    "Price",
    "Quantity",
    "ProductCost",
    "AltCost",
    "Net",
    "Decision",
    "Status",
    "SourceURL",
    "Bullet1",
    "Bullet2",
    "Bullet3",
    "Blockers",
  ];
  const lines = [headers.join(",")];
  for (const p of packages) {
    const b = p.draft?.bullets || [];
    lines.push(
      [
        csv(p.sku),
        csv(p.sellerHub.title),
        csv(p.sellerHub.categoryId),
        csv(1000),
        csv(p.sellerHub.price),
        csv(p.sellerHub.quantity),
        csv(p.cash.productCost),
        csv(p.sellerHub.altProductCost),
        csv(p.cash.net),
        csv(p.sellerHub.decision),
        csv(p.sellerHub.status),
        csv(p.sellerHub.sourceUrl),
        csv(b[0]),
        csv(b[1]),
        csv(b[2]),
        csv((p.blockers || []).join("; ")),
      ].join(",")
    );
  }
  return lines.join("\n") + "\n";
}

export function exportPackages({ status = "ready", format = "both" } = {}) {
  ensureDataDir("exports");
  const packages = buildPackagesForStatus(status);
  const stamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  const out = { stamp, status, count: packages.length, files: [] };

  if (format === "json" || format === "both") {
    const file = `exports/listings-${status}-${stamp}.json`;
    const abs = dataPath(file);
    writeFileSync(abs, JSON.stringify({ generatedAt: new Date().toISOString(), packages }, null, 2));
    out.files.push({ type: "json", path: abs, relative: file });
  }
  if (format === "csv" || format === "both") {
    const file = `exports/listings-${status}-${stamp}.csv`;
    const abs = dataPath(file);
    writeFileSync(abs, packagesToCsv(packages));
    out.files.push({ type: "csv", path: abs, relative: file });
  }

  appendJsonl("export-events.jsonl", {
    type: "export",
    status,
    count: packages.length,
    files: out.files.map((f) => f.relative),
  });
  return { ...out, packages };
}

export function exportSku(sku, opts = {}) {
  const row = getSku(sku);
  if (!row) throw Object.assign(new Error(`SKU not found: ${sku}`), { status: 404 });
  return buildListingPackage(row, opts);
}

function mapCondition(c) {
  const v = String(c || "NEW").toUpperCase();
  if (v.includes("USED")) return "USED_EXCELLENT";
  return "NEW";
}

function csv(v) {
  if (v == null) return "";
  const s = String(v);
  if (/[",\n]/.test(s)) return `"${s.replaceAll('"', '""')}"`;
  return s;
}
