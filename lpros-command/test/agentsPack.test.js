/**
 * Elite Hermes packs must exist as OpenClaw-style markdown workspaces.
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { launchAgent } from "../src/playground/board.js";
import { AGENT_CATALOG } from "../src/playground/catalog.js";
import { routeApi } from "../src/http/router.js";
import {
  ELITE_PACKS,
  REQUIRED_PACK_FILES,
  loadPack,
  listPacks,
  packExists,
} from "../../lpros-agents/src/loadPack.js";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../../lpros-agents");

describe("lpros-agents elite packs", () => {
  it("root constitution and operator card exist", () => {
    assert.ok(existsSync(resolve(root, "AGENTS.md")));
    assert.ok(existsSync(resolve(root, "MEUFT.md")));
    assert.ok(existsSync(resolve(root, "USER.md")));
    assert.ok(existsSync(resolve(root, "ROSTER.md")));
    assert.ok(existsSync(resolve(root, "INSPIRATION.md")));
    assert.ok(existsSync(resolve(root, ".cursor/skills/create-elite-agent/SKILL.md")));
  });

  it("roster lists every elite pack as complete", () => {
    const listed = listPacks();
    assert.equal(listed.length, ELITE_PACKS.length);
    for (const row of listed) {
      assert.equal(row.complete, true, `${row.id} incomplete: ${row.missing.join(", ")}`);
    }
  });

  for (const agent of ELITE_PACKS) {
    it(`${agent} has the full OpenClaw workspace`, () => {
      assert.ok(packExists(agent), agent);
      for (const f of REQUIRED_PACK_FILES) {
        const p = resolve(root, agent, f);
        assert.ok(existsSync(p), `${agent}/${f}`);
        const text = readFileSync(p, "utf8");
        assert.ok(text.length > 400, `${agent}/${f} too short (${text.length})`);
      }
    });

    it(`${agent} IDENTITY has a JSON output contract`, () => {
      const text = readFileSync(resolve(root, agent, "IDENTITY.md"), "utf8");
      assert.match(text, /```json/);
      assert.match(text, /Desk JS/i);
    });

    it(`${agent} HEARTBEAT does not unsolicited-scrape`, () => {
      const text = readFileSync(resolve(root, agent, "HEARTBEAT.md"), "utf8");
      assert.match(text, /unsolicited/i);
    });
  }

  it("loadPack returns excerpts for scout and oracle", () => {
    const scout = loadPack("scout");
    assert.equal(scout.complete, true);
    assert.ok(scout.soulExcerpt.length > 80);
    const oracle = loadPack("conditioner");
    assert.match(oracle.soulExcerpt, /Oracle/i);
  });
});

describe("playground persona packs", () => {
  it("catalog includes specialists and hermesPack wiring", async () => {
    for (const id of ["conditioner", "redteam", "pressure", "compliance", "memento", "inversion"]) {
      assert.ok(AGENT_CATALOG.some((a) => a.id === id), id);
    }
    assert.equal(AGENT_CATALOG.find((a) => a.id === "brain")?.hermesPack, "orchestrator");
    assert.equal(AGENT_CATALOG.find((a) => a.id === "crawler")?.hermesPack, "taxonomy");
    const cat = await routeApi({ method: "GET", pathname: "/playground/catalog" });
    assert.ok((cat.body.packs || []).every((p) => p.complete));
    const packs = await routeApi({ method: "GET", pathname: "/playground/packs" });
    assert.ok(packs.body.packs.length >= ELITE_PACKS.length);
  });

  it("launches Oracle pack without claiming a live Browse run", async () => {
    const job = await launchAgent({
      agent: "conditioner",
      dryRun: true,
      sync: true,
      input: { soldierId: "scout" },
    });
    assert.equal(job.status, "done");
    assert.equal(job.result.packOnly, true);
    assert.equal(job.result.packId, "conditioner");
    assert.match(job.result.note, /not treat markdown as a live Browse/i);
  });

  it("launches Joker red-team pack and stays legal", async () => {
    const job = await launchAgent({
      agent: "redteam",
      dryRun: true,
      sync: true,
      input: { thesis: "ZIK screenshot means print" },
    });
    assert.equal(job.status, "done");
    assert.equal(job.result.packId, "redteam");
    assert.match(job.result.soulExcerpt, /Joker|lawful|crime|thesis/i);
  });
});
