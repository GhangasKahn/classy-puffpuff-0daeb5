/**
 * Assemble listing packages from a completed mission/campaign and promote to SKU registry.
 */
import { buildListingPackages, packagesToCsv } from "../../../lpros/src/core/listing_factory.js";
import { promoteCandidate, upsertSku } from "../ops/skus.js";
import { loadJob, persistJob, appendJobEvent } from "./jobstore.js";

export function assemblePackages(job, { maxPackages = 25 } = {}) {
  if (!job?.results) throw Object.assign(new Error("job has no results yet"), { status: 409 });
  const factory = buildListingPackages({
    products: job.results.products || [],
    variants: job.results.variants || [],
    ideas: job.results.trends?.ideasPreview || job.results.recommendations?.topIdeas || [],
    cost: job.config?.cost || 18,
    maxPackages,
    jobId: job.id,
  });
  job.results.packages = factory.packages;
  job.results.packageCount = factory.packageCount;
  job.results.clusters = factory.clusters;
  job.results.imageStats = factory.imageStats;
  job.results.packagesCsv = packagesToCsv(factory.packages);
  if (job.results.workbookCsv && !job.results.workbookCsv.includes("SHEET: LISTING_PACKAGES")) {
    job.results.workbookCsv +=
      "\n# SHEET: LISTING_PACKAGES\n" + job.results.packagesCsv.trimEnd() + "\n";
  }
  job.updatedAt = new Date().toISOString();
  persistJob(job);
  appendJobEvent(
    job,
    "info",
    `Listing factory: ${factory.packageCount} packages · ${factory.clusters.clusterCount} keyword clusters`,
    { phase: "factory" }
  );
  return factory;
}

export function promotePackages(job, { limit = 8, decision = "TEST_NOW" } = {}) {
  if (!job.results?.packages?.length) assemblePackages(job);
  const picked = (job.results.packages || [])
    .filter((p) => !decision || p.decision === decision || p.kind === "title_test")
    .slice(0, limit);
  const promoted = picked.map((p) => {
    const row = promoteCandidate(
      {
        title: p.title,
        salePrice: p.salePrice,
        price: p.salePrice,
        url: p.sourceUrl,
        categoryId: p.categoryId,
        perceivedValue: 0.55,
        decision: "CANDIDATE",
      },
      {
        categoryId: p.categoryId,
        productCost: p.productCost,
        notes: `From ${job.id} ${p.packageId} cluster=${p.clusterSeed || ""} beat=${p.beatThis?.url || ""}`,
        requireHarden: false,
      }
    );
    return upsertSku({
      ...row,
      draft: p.draft || row.draft,
      imagePlan: p.imagePlan,
      beatThis: p.beatThis,
      packageId: p.packageId,
      title: p.title,
      sourceUrl: p.sourceUrl || row.sourceUrl,
    });
  });
  appendJobEvent(job, "info", `Promoted ${promoted.length} listing packages into SKU registry`, {
    phase: "promote",
  });
  return { count: promoted.length, skus: promoted };
}

export function packagesForJob(jobId, opts) {
  const job = loadJob(jobId);
  if (!job) return null;
  return assemblePackages(job, opts);
}
