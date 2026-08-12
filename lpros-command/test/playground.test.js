/**
 * Playground: job board, sub-agent launch, browser allowlist, VM recipes.
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { routeApi } from "../src/http/router.js";
import { hostnameAllowed, parseItemId } from "../src/playground/browser.js";
import { launchAgent, createJob, listJobs, cancelJob, getJob } from "../src/playground/board.js";
import { AGENT_CATALOG, PLAYBOOKS, VM_RECIPES } from "../src/playground/catalog.js";

describe("playground catalog", () => {
  it("lists soldiers, playbooks, and VM recipes", () => {
    assert.ok(AGENT_CATALOG.some((a) => a.id === "brain"));
    assert.ok(AGENT_CATALOG.some((a) => a.id === "browser"));
    assert.ok(AGENT_CATALOG.some((a) => a.id === "vm"));
    assert.ok(PLAYBOOKS.some((p) => p.id === "terapeak"));
    assert.ok(VM_RECIPES.some((r) => r.id === "health"));
  });
});

describe("playground browser safety", () => {
  it("blocks private hosts and eBay search HTML", () => {
    assert.equal(hostnameAllowed("127.0.0.1"), false);
    assert.equal(hostnameAllowed("localhost"), false);
    assert.equal(hostnameAllowed("169.254.169.254"), false);
    assert.equal(hostnameAllowed("192.168.1.9"), false);
    assert.equal(hostnameAllowed("example.com"), true);
    assert.equal(hostnameAllowed("www.ebay.com"), "ebay-item-only");
    assert.equal(parseItemId("https://www.ebay.com/itm/123456789012"), "123456789012");
    assert.equal(parseItemId("123456789012"), "123456789012");
  });

  it("POST fetch rejects private and search URLs", async () => {
    const priv = await routeApi({
      method: "POST",
      pathname: "/playground/browser/fetch",
      body: { url: "https://127.0.0.1/secret" },
    });
    assert.equal(priv.status, 403);

    const search = await routeApi({
      method: "POST",
      pathname: "/playground/browser/fetch",
      body: { url: "https://www.ebay.com/sch/i.html?_nkw=desk" },
    });
    assert.equal(search.status, 403);
  });
});

describe("playground job board + launcher", () => {
  it("creates a queued job and cancels it", () => {
    const job = createJob({
      kind: "agent",
      agent: "copy",
      title: "Draft a title",
      input: { title: "Oak desk organizer" },
    });
    assert.equal(job.status, "queued");
    assert.ok(listJobs().some((j) => j.id === job.id));
    const cancelled = cancelJob(job.id);
    assert.equal(cancelled.status, "cancelled");
  });

  it("launches Brain with dry soldiers and returns CONDITIONAL brief", async () => {
    const job = await launchAgent({
      agent: "brain",
      dryRun: true,
      sync: true,
      input: { q: "solid wood desk organizer", categoryId: "25339" },
    });
    assert.equal(job.status, "done");
    assert.ok(job.children.length >= 2);
    assert.equal(job.result.brief.verdict, "CONDITIONAL");
    assert.ok(job.result.brief.factors.flags.includes("sold_evidence_missing"));
    const scout = getJob(job.children.find((id) => getJob(id)?.agent === "scout"));
    assert.equal(scout.status, "done");
    assert.equal(scout.result.dryRun, true);
  });

  it("launches economics and copy soldiers", async () => {
    const econ = await launchAgent({
      agent: "economics",
      sync: true,
      input: { price: 49, cost: 18 },
    });
    assert.equal(econ.status, "done");
    assert.ok(econ.result.net.net > 0);

    const copy = await launchAgent({
      agent: "copy",
      sync: true,
      input: { title: "Walnut desk organizer upgrade", salePrice: 59 },
    });
    assert.equal(copy.status, "done");
    assert.ok(copy.result.draft.title);
  });

  it("fulfill soldier HOLDs without supplier cost", async () => {
    const job = await launchAgent({
      agent: "fulfill",
      sync: true,
      input: { buyerTotal: 54, supplierConfirmed: false },
    });
    assert.equal(job.status, "done");
    const gate = job.result.decision || job.result.gate || job.result;
    const text = JSON.stringify(gate);
    assert.match(text, /HOLD/i);
  });
});

describe("playground HTTP", () => {
  it("GET catalog + VM snapshot + launch via router", async () => {
    const cat = await routeApi({ method: "GET", pathname: "/playground/catalog" });
    assert.equal(cat.status, 200);
    assert.ok(cat.body.agents.length >= 8);

    const vm = await routeApi({ method: "GET", pathname: "/playground/vm" });
    assert.equal(vm.status, 200);
    assert.ok(vm.body.node);

    const health = await routeApi({
      method: "POST",
      pathname: "/playground/vm/exec",
      body: { recipe: "health" },
    });
    assert.equal(health.status, 200);
    assert.equal(health.body.run.result.ok, true);

    const launched = await routeApi({
      method: "POST",
      pathname: "/playground/launch",
      body: {
        agent: "brain",
        dryRun: true,
        q: "bamboo cable tray",
        spawn: ["economics"],
      },
    });
    assert.equal(launched.status, 200);
    assert.equal(launched.body.status, "done");
    assert.equal(launched.body.brief.verdict, "CONDITIONAL");

    const board = await routeApi({ method: "GET", pathname: "/playground/jobs" });
    assert.equal(board.status, 200);
    assert.ok(board.body.jobs.length >= 1);
  });

  it("browser session playbook advances", async () => {
    const created = await routeApi({
      method: "POST",
      pathname: "/playground/browser/sessions",
      body: { playbookId: "terapeak" },
    });
    assert.equal(created.status, 200);
    const id = created.body.session.id;
    const adv = await routeApi({
      method: "POST",
      pathname: `/playground/browser/sessions/${id}/advance`,
      body: { capture: { soldCount: 22 } },
    });
    assert.equal(adv.status, 200);
    assert.equal(adv.body.session.stepIndex, 1);
    assert.equal(adv.body.session.steps[0].done, true);
  });
});
