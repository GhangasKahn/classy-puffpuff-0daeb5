/**
 * Research Watch VM — stepped live session (no fake uploads).
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  cancelWatch,
  clipProof,
  createWatchSession,
  getWatch,
  slimWatch,
  tickWatch,
} from "../src/research/watch.js";
import { routeApi } from "../src/http/router.js";

const liveItems = [
  {
    id: "v1|111|0",
    title: "Solid oak desk organizer",
    price: 49,
    url: "https://www.ebay.com/itm/111",
    image: "https://i.ebayimg.com/images/g/aaa/s-l1600.jpg",
    seller: "woodshop",
  },
  {
    id: "v1|222|0",
    title: "Walnut desktop tray",
    price: 62,
    url: "https://www.ebay.com/itm/222",
    image: "https://i.ebayimg.com/images/g/bbb/s-l1600.jpg",
    seller: "mill",
  },
];

describe("research watch VM", () => {
  it("clipProof keeps listing URLs for the Proof tab", () => {
    const s = clipProof({ url: "https://www.ebay.com/itm/111", title: "oak" });
    assert.match(s, /ebay\.com\/itm\/111/);
    assert.match(clipProof({ n: "x".repeat(4000) }, 80), /truncated/);
  });

  it("refuses dry-run — watch is live-only", () => {
    assert.throws(() => createWatchSession({ dryRun: true, q: "desk" }), /live-only/i);
  });

  it("boots a VM snapshot then ingests mocked Browse listings with images + URLs", async () => {
    const session = createWatchSession({ q: "solid wood desk organizer", categoryId: "25339" });
    assert.equal(session.phase, "boot");
    assert.equal(session.proof.source, "ebay_browse");
    assert.equal(session.proof.dryRun, false);
    assert.ok(session.vm.hostname);
    assert.ok(session.vm.pid);

    await tickWatch(session.id, { n: 1 });
    const afterBoot = getWatch(session.id);
    assert.ok(["search", "failed"].includes(afterBoot.phase));
    if (afterBoot.phase === "failed") {
      assert.match(afterBoot.error || "", /EBAY_PRD|credential/i);
      return;
    }

    await tickWatch(session.id, {
      n: 1,
      searchFn: async () => ({ items: liveItems, total: 2, source: "ebay_browse" }),
    });
    let cur = getWatch(session.id);
    assert.equal(cur.phase, "ingest");
    assert.equal(cur.raw.length, 2);
    assert.equal(cur.apiCalls[0].host, "api.ebay.com");
    assert.equal(typeof cur.apiCalls[0].ms, "number");

    await tickWatch(session.id, { n: 1 });
    cur = getWatch(session.id);
    assert.ok(cur.products.length >= 1);
    assert.match(cur.products[0].url, /ebay\.com\/itm/);
    assert.ok(cur.products[0].image);
    assert.equal(cur.products[0].source, "ebay_browse");

    while (getWatch(session.id).phase === "ingest") {
      await tickWatch(session.id, { n: 1 });
    }
    assert.equal(getWatch(session.id).phase, "detail");

    await tickWatch(session.id, {
      n: 1,
      getItemFn: async (id) => ({
        id,
        itemId: id,
        title: "Solid oak desk organizer",
        price: 49,
        url: "https://www.ebay.com/itm/111",
        image: "https://i.ebayimg.com/images/g/aaa/s-l1600.jpg",
        descriptionText: "Solid oak. Desktop clutter solution. Dimensions in listing.",
        itemSpecifics: { Material: "Oak" },
      }),
    });
    cur = getWatch(session.id);
    assert.equal(cur.current.detailFetched, true);
    assert.match(cur.current.descriptionExcerpt, /Solid oak/i);
    assert.ok(cur.apiCalls.some((c) => /item_summary\/search/.test(c.path)));
    assert.ok(cur.apiCalls.some((c) => /\/item\//.test(c.path)));
    const slim = slimWatch(cur);
    assert.equal(slim.productCount, cur.products.length);
    assert.ok(slim.productsWithImages >= 1);
    assert.match(cur.proof.browseSnippet, /ebay\.com\/itm/);
    assert.match(cur.proof.itemSnippet, /Solid oak/i);
    assert.equal(cur.proof.notUploadedCsv, true);
  });

  it("cancel stops the session", () => {
    const session = createWatchSession({ q: "tray" });
    const stopped = cancelWatch(session.id);
    assert.equal(stopped.status, "cancelled");
  });
});

describe("research watch HTTP", () => {
  it("POST dryRun is rejected", async () => {
    const r = await routeApi({
      method: "POST",
      pathname: "/research/watch",
      body: { q: "desk", dryRun: true },
    });
    assert.equal(r.status, 400);
    assert.match(r.body.error, /live-only/i);
  });

  it("POST creates a bootstrapped session and GET lists it", async () => {
    const created = await routeApi({
      method: "POST",
      pathname: "/research/watch",
      body: { q: "bamboo cable tray", categoryId: "25339" },
    });
    assert.equal(created.status, 200);
    assert.ok(created.body.id);
    assert.equal(created.body.proof.dryRun, false);
    assert.ok(created.body.vm.hostname);
    assert.ok(["search", "failed"].includes(created.body.phase));

    const listed = await routeApi({ method: "GET", pathname: "/research/watch" });
    assert.equal(listed.status, 200);
    assert.ok((listed.body.sessions || []).some((s) => s.id === created.body.id));

    const one = await routeApi({
      method: "GET",
      pathname: `/research/watch/${created.body.id}`,
    });
    assert.equal(one.status, 200);
    assert.equal(one.body.id, created.body.id);

    const cancelled = await routeApi({
      method: "POST",
      pathname: `/research/watch/${created.body.id}/cancel`,
      body: {},
    });
    assert.equal(cancelled.status, 200);
    assert.equal(cancelled.body.status, "cancelled");
  });

  it("health lists /research/watch", async () => {
    const h = await routeApi({ method: "GET", pathname: "/health" });
    assert.ok(h.body.endpoints.includes("/research/watch"));
  });
});
