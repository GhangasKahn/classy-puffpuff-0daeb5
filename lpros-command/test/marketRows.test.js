/**
 * Market desk mapping + Browse fallback — products, images, URLs must survive ranker/dry-run.
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  collectResearchItems,
  deskFromPlaygroundJobs,
  deskFromResearch,
  emptyLiveHint,
  normalizeProduct,
} from "../src/http/marketRows.js";
import { searchBrowseWithFallback } from "../src/intel/competitor.js";
import { routeApi } from "../src/http/router.js";
import { launchAgent, getJob } from "../src/playground/board.js";

describe("marketRows", () => {
  it("maps live intel-shaped items onto title, price, image, url, excerpt", () => {
    const desk = deskFromResearch({
      items: [
        {
          id: "v1|123|0",
          title: "Solid oak desk organizer",
          price: 49,
          url: "https://www.ebay.com/itm/123",
          image: "https://i.ebayimg.com/images/g/abc/s-l1600.jpg",
          images: ["https://i.ebayimg.com/images/g/abc/s-l1600.jpg"],
          seller: "woodshop",
          descriptionExcerpt: "Solid wood. Desktop clutter solution.",
        },
      ],
      lethalCandidates: [],
    });
    assert.equal(desk.productCount, 1);
    assert.equal(desk.productsWithImages, 1);
    assert.equal(desk.productsWithUrls, 1);
    assert.equal(desk.dryRun, false);
    assert.equal(desk.products[0].title, "Solid oak desk organizer");
    assert.match(desk.products[0].url, /ebay\.com\/itm/);
    assert.ok(desk.products[0].image);
  });

  it("keeps Browse items even when the ranker board is empty", () => {
    const rows = collectResearchItems({
      lethalCandidates: [],
      items: [{ title: "Walnut tray", price: 59, url: "https://www.ebay.com/itm/9", image: "https://i.ebayimg.com/x.jpg" }],
    });
    assert.equal(rows.length, 1);
    assert.equal(rows[0].url, "https://www.ebay.com/itm/9");
  });

  it("does not treat dry-run fixtures as live listings", () => {
    const desk = deskFromResearch({
      dryRun: true,
      top: [{ title: "Fake oak", salePrice: 49, source: "dry-fixture" }],
    });
    assert.equal(desk.dryRun, true);
    assert.equal(desk.products[0].url, "");
    assert.equal(desk.products[0].image, "");
    assert.match(desk.emptyReason, /Dry-run/i);
  });

  it("surfaces a credential hint when empty and unconfigured", () => {
    const hint = emptyLiveHint({ configured: false });
    assert.match(hint, /EBAY_PRD_APP_ID/);
    const desk = deskFromResearch({ items: [] }, { configured: false });
    assert.equal(desk.productCount, 0);
    assert.match(desk.emptyReason, /credential|EBAY_PRD/i);
  });

  it("merges playground soldier jobs onto one desk payload", () => {
    const desk = deskFromPlaygroundJobs([
      {
        input: { q: "desk organizer" },
        result: {
          lethalCandidates: [
            { title: "A", price: 40, url: "https://www.ebay.com/itm/1", image: "https://i.ebayimg.com/a.jpg" },
          ],
        },
      },
      {
        result: {
          top: [{ title: "A", salePrice: 40, url: "https://www.ebay.com/itm/1", image: "https://i.ebayimg.com/a.jpg" }],
        },
      },
    ]);
    assert.equal(desk.productCount, 1);
    assert.equal(desk.productsWithImages, 1);
  });

  it("normalizeProduct prefers listing URL and image gallery", () => {
    const row = normalizeProduct({
      title: "Bamboo",
      salePrice: 44,
      itemWebUrl: "https://www.ebay.com/itm/44",
      thumbnail: "https://i.ebayimg.com/th.jpg",
      additionalImages: ["https://i.ebayimg.com/2.jpg"],
    });
    assert.equal(row.url, "https://www.ebay.com/itm/44");
    assert.ok(row.image);
    assert.ok(row.imageCount >= 2);
    const dated = normalizeProduct({
      title: "Oak",
      price: 49,
      url: "https://www.ebay.com/itm/1",
      listingDate: "2026-08-12T12:00:00.000Z",
    });
    assert.equal(dated.listingDate, "2026-08-12T12:00:00.000Z");
  });
});

describe("searchBrowseWithFallback", () => {
  it("retries without sort then without category until items appear", async () => {
    const calls = [];
    const searchFn = async (opts) => {
      calls.push(opts);
      if (opts.sort === "newlyListed" && opts.categoryIds) return { items: [], total: 0 };
      if (!opts.sort && opts.categoryIds) return { items: [], total: 0 };
      return {
        items: [{ id: "x", title: "Live listing", price: 49, url: "https://www.ebay.com/itm/x", image: "https://i.ebayimg.com/x.jpg" }],
        total: 1,
      };
    };
    const { page } = await searchBrowseWithFallback(
      { q: "desk", categoryId: "25339", minPrice: 35, maxPrice: 150 },
      searchFn
    );
    assert.ok(calls.length >= 3);
    assert.equal(page.items.length, 1);
  });
});

describe("health + dry playground honesty", () => {
  it("GET /health reports ebay.appConfigured", async () => {
    const h = await routeApi({ method: "GET", pathname: "/health" });
    assert.equal(h.status, 200);
    assert.equal(typeof h.body.ebay.appConfigured, "boolean");
    assert.ok(h.body.endpoints.includes("/research/live"));
  });

  it("POST /research/live without credentials returns 503", async () => {
    const prevApp = process.env.EBAY_PRD_APP_ID;
    const prevCert = process.env.EBAY_PRD_CERT_ID;
    const prevApp2 = process.env.EBAY_APP_ID;
    const prevCert2 = process.env.EBAY_CERT_ID;
    // config is already loaded — this test documents the route contract when unconfigured.
    // If this environment HAS credentials, skip the 503 assertion and only check the shape.
    const health = await routeApi({ method: "GET", pathname: "/health" });
    if (!health.body.ebay.appConfigured) {
      const r = await routeApi({
        method: "POST",
        pathname: "/research/live",
        body: { q: "desk organizer" },
      });
      assert.equal(r.status, 503);
      assert.match(r.body.error, /EBAY_PRD_APP_ID|credentials/i);
    } else {
      assert.equal(health.body.ebay.appConfigured, true);
    }
    void prevApp;
    void prevCert;
    void prevApp2;
    void prevCert2;
  });

  it("dry Brain launch is labeled dry-run and has no live listing URLs", async () => {
    const job = await launchAgent({
      agent: "brain",
      dryRun: true,
      sync: true,
      input: { q: "solid wood desk organizer", categoryId: "25339" },
    });
    assert.equal(job.status, "done");
    assert.equal(job.result.dryRun, true);
    const scout = getJob(job.children.find((id) => getJob(id)?.agent === "scout"));
    assert.equal(scout.result.dryRun, true);
    assert.equal(scout.result.top[0].source, "dry-fixture");
    assert.ok(!scout.result.top[0].url);
    assert.ok(!scout.result.top[0].image);
    const launched = await routeApi({
      method: "POST",
      pathname: "/playground/launch",
      body: { agent: "brain", dryRun: true, spawn: ["scout"], q: "bamboo" },
    });
    assert.equal(launched.status, 200);
    assert.equal(launched.body.dryRun, true);
    assert.ok((launched.body.emptyReason || "").length > 0);
  });
});
