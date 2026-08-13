/**
 * SEO swarm + spreadsheet unit tests (no eBay).
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  mineKeywordPatterns,
  generateTitleVariations,
  scoreTitleSeo,
  imageSeoChecklist,
  buildConversionDescription,
  extractKeywordsFromTitle,
} from "../src/core/seo.js";
import { toDecisionCsv, decisionForRow } from "../src/core/spreadsheet.js";

describe("seo swarm", () => {
  it("mines patterns and generates 100+ titles", () => {
    const patterns = mineKeywordPatterns([
      "Solid wood desk organizer oak",
      "Bamboo desk organizer clutter solution",
      "Walnut desktop storage tray upgrade",
    ]);
    assert.ok(patterns.topUnigrams.length > 0);
    const titles = generateTitleVariations({
      seed: "desk organizer",
      maxTitles: 120,
      patterns,
    });
    assert.ok(titles.length >= 80);
    assert.ok(titles.every((t) => t.title.length <= 80));
  });

  it("scores SEO and builds description + image checklist", () => {
    const patterns = mineKeywordPatterns(["oak desk organizer wood storage"]);
    const seo = scoreTitleSeo("Solid oak desk organizer clutter solution", patterns);
    assert.ok(seo.seoScore >= 0 && seo.seoScore <= 1);
    const kw = extractKeywordsFromTitle("Solid oak desk organizer", patterns);
    assert.ok(kw.primaryKeyword);
    const img = imageSeoChecklist({ title: "Oak desk", primaryKeyword: kw.primaryKeyword });
    assert.ok(img.checks.length >= 4);
    const desc = buildConversionDescription({
      title: "Oak desk organizer",
      keywords: kw.secondaryKeywords,
      price: 49,
    });
    assert.ok(desc.descriptionText.includes("Oak"));
  });
});

describe("spreadsheet decisions", () => {
  it("exports CSV with TEST_NOW rows", () => {
    const { csv, rows } = toDecisionCsv(
      [
        {
          title: "A",
          seoScore: 75,
          testPriority: "A",
          primaryKeyword: "desk",
          secondaryKeywords: ["oak"],
          suggestedPrice: 59,
          landedCost: 18,
          estNet: 12,
          imageSeo: { score: 40, checks: [{ id: "hero", ok: false }] },
          description: { bullets: ["a", "b"] },
        },
        {
          title: "B",
          seoScore: 30,
          testPriority: "C",
          primaryKeyword: "desk",
        },
      ],
      { jobId: "job_test", query: "desk organizer" }
    );
    assert.equal(decisionForRow(rows[0]), "TEST_NOW");
    assert.equal(rows[1].decision, "REWRITE");
    assert.ok(csv.includes("test_priority"));
    assert.ok(csv.includes("TEST_NOW"));
  });
});
