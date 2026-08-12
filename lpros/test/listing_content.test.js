/**
 * Listing content + product research CSV tests.
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  toProductResearchRow,
  productsToCsv,
  extractContentSignals,
} from "../src/core/listing_content.js";

describe("listing content", () => {
  it("builds researched product rows with image/url/content", () => {
    const row = toProductResearchRow(
      {
        id: "v1|123",
        title: "Solid oak desk organizer clutter solution",
        price: 54.99,
        url: "https://www.ebay.com/itm/123",
        image: "https://i.ebayimg.com/images/g/abc/s-l1600.jpg",
        images: [
          "https://i.ebayimg.com/images/g/abc/s-l1600.jpg",
          "https://i.ebayimg.com/images/g/def/s-l1600.jpg",
        ],
        descriptionText:
          "Solid oak wood organizer for home office clutter. Measures 12 inch. Premium upgrade.",
        itemSpecifics: { Material: "Oak", Brand: "Unbranded" },
        seller: "pro_seller",
        detailFetched: true,
        rank: 1,
      },
      { jobId: "job_x", query: "desk organizer" }
    );
    assert.equal(row.kind, "PRODUCT_RESEARCH");
    assert.ok(row.image);
    assert.ok(row.url.includes("ebay.com"));
    assert.ok(row.contentSignals.includes("material_premium"));
    assert.ok(row.contentSignals.includes("problem_solve"));
    const csv = productsToCsv([row]);
    assert.ok(csv.includes("https://www.ebay.com/itm/123"));
    assert.ok(csv.includes("imageCount"));
  });

  it("flags qty spam in content signals", () => {
    const s = extractContentSignals("Buy 10 pcs lot pack desk trays", "lot");
    assert.ok(s.includes("qty_spam_risk"));
  });
});
