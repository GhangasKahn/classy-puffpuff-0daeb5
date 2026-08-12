import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { deployCampaign, DEFAULT_MARATHON_CATEGORIES } from "../src/orchestrate/campaign.js";
import { routeApi } from "../src/http/router.js";

describe("marathon campaign dry-run", () => {
  it("runs 5 categories and produces products + ideas workbook", async () => {
    const job = await deployCampaign(
      {
        mode: "marathon",
        q: "desk organizer",
        categories: DEFAULT_MARATHON_CATEGORIES,
        variantCount: 40,
        ideasTarget: 120,
        dryRun: true,
      },
      { sync: true }
    );
    assert.equal(job.status, "completed");
    assert.equal(job.results.categoryCount, 5);
    assert.ok(job.results.productCount >= 15);
    assert.ok(job.results.variantTotalGenerated >= 50);
    assert.ok(job.results.ideaCount >= 50);
    assert.ok(job.results.workbookCsv.includes("TRENDS"));
    assert.ok(job.results.workbookCsv.includes("IDEAS"));
    assert.ok(job.results.trends.categoryHeat.length === 5);
    assert.ok(job.checkpoints.length === 5);
    assert.ok((job.results.packageCount || 0) >= 1);
    assert.ok((job.results.packages || []).length >= 1);
    assert.ok(job.results.packagesCsv.includes("packageId"));
  });
});

describe("marathon API", () => {
  it("POST /orchestrate/campaign dryRun", async () => {
    const res = await routeApi({
      method: "POST",
      pathname: "/orchestrate/campaign",
      body: {
        dryRun: true,
        sync: true,
        q: "bamboo organizer",
        variantCount: 30,
        ideasTarget: 80,
        categories: DEFAULT_MARATHON_CATEGORIES.slice(0, 3),
      },
    });
    assert.equal(res.status, 200);
    assert.equal(res.body.status, "completed");
    assert.ok(res.body.productCount >= 8);
    assert.ok(res.body.ideaCount >= 20);

    const pkgs = await routeApi({
      method: "GET",
      pathname: `/orchestrate/jobs/${res.body.jobId}/packages`,
    });
    assert.equal(pkgs.status, 200);
    assert.ok(pkgs.body.packageCount >= 1);

    const sheet = await routeApi({
      method: "GET",
      pathname: `/orchestrate/jobs/${res.body.jobId}/spreadsheet`,
      query: new URLSearchParams({ workbook: "1" }),
    });
    assert.equal(sheet.status, 200);
    assert.ok(String(sheet.body).includes("PRODUCT_RESEARCH"));
  });
});
