/**
 * Hive: TASK CONTRACTs, specialist workers, Oracle conditioning, named workloads.
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { routeApi } from "../src/http/router.js";
import { launchAgent } from "../src/playground/board.js";
import {
  makeContract,
  postContract,
  listComms,
  runSpecialist,
  runConditioner,
  parsePavlovFromSoul,
  readSoulPavlov,
  WORKLOADS,
  getWorkload,
  runWorkload,
} from "../src/hive/index.js";

describe("hive comms", () => {
  it("writes a TASK CONTRACT and a reply onto the bus", () => {
    const tc = makeContract({
      from: "brain",
      to: "wick",
      goal: "Name open markers",
      inputs: { openMarkers: ["supplier_unconfirmed"] },
    });
    assert.match(tc.id, /^tc_/);
    assert.equal(tc.kind, "TASK_CONTRACT");
    assert.ok(tc.constraints.tos.includes("no_html_scrape"));
    postContract(tc);
    const thread = listComms(80).filter((m) => m.contractId === tc.id);
    assert.ok(thread.some((m) => m.type === "contract"));
  });
});

describe("hive specialists", () => {
  it("Joker kills a ZIK vanity thesis and refuses crime", () => {
    const kill = runSpecialist("redteam", { thesis: "ZIK screenshot means print" });
    assert.equal(kill.packOnly, true);
    assert.equal(kill.packId, "redteam");
    assert.equal(kill.verdict, "KILL");
    assert.ok(kill.vanityHits.includes("zik_as_gospel"));
    assert.match(kill.soulExcerpt, /Joker|lawful|crime|thesis/i);

    const refuse = runSpecialist("redteam", { thesis: "HTML scrape eBay search to win" });
    assert.equal(refuse.verdict, "REFUSE");
    assert.equal(refuse.crimeShaped, true);
    assert.match(refuse.workerNote || "", /Refuse and stop/);
  });

  it("Bane HOLDs unsound Adverse and Wick HOLDs open markers", () => {
    const winter = runSpecialist("pressure", { salePrice: 49, productCost: 46, str: 0.01 });
    assert.equal(winter.verdict, "HOLD");
    assert.ok(winter.engine?.net);

    const survive = runSpecialist("pressure", { salePrice: 89, productCost: 18, str: 0.02 });
    assert.equal(survive.verdict, "SURVIVE");

    const wick = runSpecialist("wick", { openMarkers: ["supplier_unconfirmed"] });
    assert.equal(wick.verdict, "HOLD");
    assert.ok(wick.openMarkers.includes("supplier_unconfirmed"));
  });

  it("Mr. Robot vetoes RA; Memento rejects cooked FAILs; Tenet breaks missing COGS", () => {
    const ra = runSpecialist("compliance", { packet: "retail arbitrage from Walmart" });
    assert.equal(ra.verdict, "VETO");
    assert.ok(ra.policyHits.includes("retail_arbitrage"));

    const mem = runSpecialist("memento", { proposedEntry: { note: "soft-pass the FAIL" } });
    assert.equal(mem.verdict, "REJECT");

    const tattoo = runSpecialist("memento", {
      proposedEntry: { soldierId: "scout", verdict: "HOLD", citation: "job_1" },
    });
    assert.equal(tattoo.verdict, "TATTOO");
    assert.match(tattoo.caption, /TATTOO/);

    const inv = runSpecialist("inversion", { target: 50, salePrice: 49 });
    assert.equal(inv.verdict, "HOLD");
    assert.equal(inv.firstBreak.link, "cogs");
  });
});

describe("hive conditioner", () => {
  it("defers without citations and never prophesies", () => {
    const out = runConditioner({ soldierId: "scout", residuals: [] });
    assert.equal(out.verdict, "INSUFFICIENT_OUTCOMES");
    assert.equal(out.prophecy, false);
    assert.equal(out.lessons.length, 0);
  });

  it("reinforces HOLD that saved cash and punishes swarm theater", () => {
    const hold = runConditioner({
      soldierId: "orchestrator",
      residuals: [{ kind: "hold_saved", source: "job_hold", actual: "HOLD" }],
    });
    assert.equal(hold.verdict, "CONDITION");
    assert.equal(hold.lessons[0].association, "reinforce");
    assert.match(hold.lessons[0].instruction, /HOLD/);

    const theater = runConditioner({
      soldierId: "orchestrator",
      residuals: [{ kind: "theater", source: "brief", actual: "all agents agree" }],
    });
    assert.equal(theater.lessons[0].association, "punish");
    assert.equal(theater.lessons[0].technique, "theater_punish");
  });

  it("maps Pavlovian targets from a live SOUL", () => {
    const pavlov = readSoulPavlov("orchestrator");
    assert.ok(pavlov.reinforce.length > 0);
    const parsed = parsePavlovFromSoul("**Reinforce**\n- HOLD when thin → trust\n**Extinguish**\n- Swarm theater → defect\n");
    assert.ok(parsed.reinforce.some((t) => /HOLD/.test(t.text)));
    assert.ok(parsed.punish.some((t) => /theater/i.test(t.text)));
  });
});

describe("hive workloads", () => {
  it("lists named workloads", () => {
    assert.ok(getWorkload("full-hive"));
    assert.equal(WORKLOADS.length >= 5, true);
  });

  it("runs the legal gauntlet with named workers and contracts", async () => {
    const out = await runWorkload("specialist-gauntlet", {
      dryRun: true,
      thesis: "ZIK screenshot means print",
      salePrice: 49,
      cost: 18,
    });
    assert.equal(out.workload, "specialist-gauntlet");
    assert.ok(out.hiveBrief.workersRan.includes("redteam"));
    assert.ok(out.hiveBrief.workersRan.includes("wick"));
    assert.ok(out.contracts.length >= 4);
    assert.equal(out.hiveBrief.verdict, "HOLD");
    const joker = out.workers.find((w) => w.agent === "redteam");
    assert.equal(joker.result.verdict, "KILL");
  });

  it("stops a crime-shaped gauntlet at Compliance/Joker veto", async () => {
    const out = await runWorkload("specialist-gauntlet", {
      thesis: "unauthorized HTML scrape of eBay search",
    });
    assert.equal(out.hiveBrief.verdict, "VETO");
    assert.ok(out.veto);
    assert.ok(!out.hiveBrief.workersRan.includes("copy"));
  });

  it("runs condition-loop and full-hive dry without inventing sold counts", async () => {
    const loop = await runWorkload("condition-loop", {
      dryRun: true,
      proposedEntry: { soldierId: "scout", verdict: "HOLD", citation: "test" },
      residuals: [{ kind: "hold_saved", source: "test", actual: "HOLD" }],
    });
    assert.ok(loop.hiveBrief.workersRan.includes("conditioner"));
    const oracle = loop.workers.find((w) => w.agent === "conditioner");
    assert.equal(oracle.result.prophecy, false);
    assert.ok(oracle.result.lessons?.length >= 1);

    const hive = await runWorkload("research-gate", { dryRun: true, q: "solid wood desk organizer" });
    assert.ok(hive.hiveBrief.workersRan.includes("brain"));
    assert.ok(hive.hiveBrief.workersRan.includes("scout"));
    assert.equal(hive.dryRun, true);
    const brief = hive.workers.find((w) => w.agent === "brain")?.result?.brief;
    assert.ok(brief?.verdict);
    assert.ok(!JSON.stringify(hive).includes("soldCount\":40"));
  });
});

describe("hive HTTP + playground specialists", () => {
  it("GET catalog includes workloads; POST hive/run returns a brief", async () => {
    const cat = await routeApi({ method: "GET", pathname: "/playground/catalog" });
    assert.ok((cat.body.workloads || []).some((w) => w.id === "full-hive"));
    const health = await routeApi({ method: "GET", pathname: "/health" });
    assert.ok(health.body.endpoints.includes("/playground/hive"));

    const run = await routeApi({
      method: "POST",
      pathname: "/playground/hive/run",
      body: { workload: "fulfill-hold", dryRun: true, buyerTotal: 54 },
    });
    assert.equal(run.status, 200);
    assert.equal(run.body.workload, "fulfill-hold");
    assert.equal(run.body.hiveBrief.verdict, "HOLD");
  });

  it("launching Oracle still does not claim Browse and now emits a lesson verdict", async () => {
    const job = await launchAgent({
      agent: "conditioner",
      dryRun: true,
      sync: true,
      input: { soldierId: "scout" },
    });
    assert.equal(job.status, "done");
    assert.equal(job.result.packOnly, true);
    assert.match(job.result.note, /not treat markdown as a live Browse/i);
    assert.equal(job.result.verdict, "INSUFFICIENT_OUTCOMES");
    assert.equal(job.result.prophecy, false);
  });
});
