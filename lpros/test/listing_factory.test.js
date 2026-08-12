import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { clusterKeywords, scoreIdea } from "../src/core/keyword_clusters.js";
import { buildListingPackages } from "../src/core/listing_factory.js";

describe("keyword clusters", () => {
  it("groups similar titles into test families", () => {
    const clustered = clusterKeywords(
      [
        { title: "oak desk organizer tray", seoScore: 80 },
        { title: "oak desk organizer upgrade", seoScore: 70 },
        { title: "bamboo kitchen drawer organizer", seoScore: 60 },
      ],
      { minSize: 1 }
    );
    assert.ok(clustered.clusterCount >= 1);
    assert.ok(clustered.clusters[0].testPlan.listingsToTest >= 1);
  });

  it("scores idea uniqueness vs competitor corpus", () => {
    const s = scoreIdea(
      { title: "walnut modular cable riser" },
      { competitorTitles: ["plastic desk tray set", "plastic desk tray set"], heatScore: 70 }
    );
    assert.ok(s.ideaScore >= 40);
    assert.ok(s.uniqueness > 0.3);
  });
});

describe("listing factory", () => {
  it("builds packages with beat-this URL, copy, and image plan", () => {
    const out = buildListingPackages({
      cost: 18,
      maxPackages: 8,
      products: [
        {
          title: "Solid oak desk organizer",
          price: 49,
          url: "https://www.ebay.com/itm/111",
          image: "https://i.ebayimg.com/images/g/x/s-l1600.jpg",
          imageCount: 4,
          itemSpecifics: { Material: "Oak", Brand: "Unbranded", Type: "Desk Organizer" },
          descriptionExcerpt: "Oak wood organizer for clutter. Measures 12 inch.",
          categoryId: "25339",
        },
        {
          title: "Bamboo desk tray",
          price: 42,
          url: "https://www.ebay.com/itm/222",
          image: "https://i.ebayimg.com/images/g/y/s-l1600.jpg",
          imageCount: 3,
          itemSpecifics: { Material: "Bamboo", Brand: "Unbranded" },
          descriptionExcerpt: "Bamboo clutter solution for home office.",
          categoryId: "25339",
        },
      ],
      variants: [
        {
          title: "Solid oak desk organizer clutter solution",
          decision: "TEST_NOW",
          testPriority: "A",
          seoScore: 88,
          suggestedPrice: 59.99,
          categoryId: "25339",
        },
      ],
      ideas: [{ title: "walnut modular desk organizer", heatScore: 70, categoryId: "25339" }],
    });
    assert.ok(out.packageCount >= 1);
    const p = out.packages[0];
    assert.ok(p.title);
    assert.ok(p.estNet != null);
    assert.ok(p.beatThis?.url.includes("ebay.com"));
    assert.ok(p.imagePlan.beatWith >= 8);
    assert.ok(p.descriptionText.includes("Original photos") || p.draft.warnings);
    assert.ok(p.itemSpecifics.Material);
  });
});
