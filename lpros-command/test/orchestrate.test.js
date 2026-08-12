/**
 * Orchestration dry-run + API route smoke (no eBay).
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  deployMission,
  getJobEvents,
  getJobSpreadsheet,
  listJobs,
} from "../src/orchestrate/runner.js";
import { routeApi } from "../src/http/router.js";

describe("orchestrate dry-run", () => {
  it("deploys sync dry mission and produces spreadsheet", async () => {
    const job = await deployMission(
      {
        q: "desk organizer",
        categoryId: "25339",
        cost: 18,
        suggestedPrice: 59.99,
        variantCount: 80,
        sheetRows: 40,
        dryRun: true,
      },
      { sync: true }
    );
    assert.equal(job.status, "completed");
    assert.ok(job.results.products.length >= 1);
    assert.ok(job.results.variants.length >= 10);
    assert.ok(job.results.spreadsheetCsv.includes("seo_score"));
    assert.ok(job.results.productSpreadsheetCsv.includes("PRODUCT") || job.results.productSpreadsheetCsv.includes("itemId") || job.results.productSpreadsheetCsv.includes("url"));
    assert.ok(job.results.workbookCsv.includes("PRODUCT_RESEARCH"));
    assert.ok(job.events.some((e) => /complete/i.test(e.message)));

    const sheet = getJobSpreadsheet(job.id, { workbook: true });
    assert.equal(sheet.ready, true);
    assert.ok(sheet.csv.includes("TITLE_KEYWORD_TESTS"));

    const ev = getJobEvents(job.id, 0);
    assert.ok(ev.events.length > 3);
    assert.ok(listJobs().some((j) => j.id === job.id));
  });
});

describe("orchestrate API", () => {
  it("POST deploy dryRun + GET job/spreadsheet", async () => {
    const deployed = await routeApi({
      method: "POST",
      pathname: "/orchestrate/deploy",
      body: {
        q: "bamboo desk organizer",
        dryRun: true,
        sync: true,
        variantCount: 60,
        sheetRows: 30,
      },
    });
    assert.equal(deployed.status, 200);
    assert.equal(deployed.body.status, "completed");
    const jobId = deployed.body.jobId;

    const job = await routeApi({
      method: "GET",
      pathname: `/orchestrate/jobs/${jobId}`,
    });
    assert.equal(job.status, 200);
    assert.ok((job.body.results.productsPreview || []).length > 0);

    const csv = await routeApi({
      method: "GET",
      pathname: `/orchestrate/jobs/${jobId}/spreadsheet`,
      query: new URLSearchParams({ workbook: "1" }),
    });
    assert.equal(csv.status, 200);
    assert.match(csv.type, /csv/);
    assert.ok(String(csv.body).includes("PRODUCT_RESEARCH"));
  });
});
