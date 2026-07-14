/**
 * Node harness for site/app/hermes-agents.js (no DOM).
 */
import { readFileSync } from "fs";
import { createContext, runInContext } from "vm";
import { describe, expect, it } from "vitest";

function loadHermes() {
  const code = readFileSync(new URL("../../site/app/hermes-agents.js", import.meta.url), "utf8");
  const sandbox = { Math, console, JSON, Array, Object, parseInt, parseFloat, isFinite, Infinity, NaN };
  sandbox.globalThis = sandbox;
  sandbox.window = sandbox;
  runInContext(code, createContext(sandbox));
  return sandbox.window.BedrockHermes;
}

const H = loadHermes();

describe("BedrockHermes agents + OC engineer", () => {
  it("exposes versioned API and full roster", () => {
    expect(H.version).toMatch(/hermes/);
    const keys = H.listPersonas();
    for (const id of [
      "ACCOUNTANT",
      "ROBOTO",
      "JACKAL",
      "BEEKEEPER",
      "DARK_KNIGHT",
      "GREENE",
      "MACGYVER",
      "STRATEGIST",
      "WICK",
      "ORACLE",
    ]) {
      expect(keys).toContain(id);
      expect(H.PERSONAS[id].systemLong.length).toBeGreaterThan(400);
      expect(H.PERSONAS[id].systemLong).toMatch(/JUNGIAN|ADLERIAN|SOCRATIC|GREENE/);
    }
  });

  it("OC engineer: floor breach is absolute", () => {
    const oc = H.opportunityCostEngine({
      cost: 5000,
      monthlySurplus: 800,
      annualReturn: 0.1,
      floorBuf: 10000,
      cash: 12000,
      kind: "Depreciating",
    });
    expect(oc.floorBreach).toBe(true);
    expect(oc.verdict).toBe("FLOOR BREACH");
    expect(oc.fv[10]).toBeCloseTo(5000 * Math.pow(1.1, 10), 5);
  });

  it("OC engineer: mild utility can acquire", () => {
    const oc = H.opportunityCostEngine({
      cost: 200,
      monthlySurplus: 1000,
      annualReturn: 0.1,
      floorBuf: 5000,
      cash: 15000,
      kind: "Pure utility",
    });
    expect(oc.floorBreach).toBe(false);
    expect(oc.verdict).toBe("ACQUIRE");
    expect(oc.monthsOfSurplus).toBeCloseTo(0.2, 5);
  });

  it("OC engineer: large depreciating spend → not worth / wait", () => {
    const oc = H.opportunityCostEngine({
      cost: 8000,
      monthlySurplus: 500,
      annualReturn: 0.1,
      floorBuf: 3000,
      cash: 20000,
      kind: "Depreciating",
    });
    expect(["NOT WORTH IT", "WAIT"]).toContain(oc.verdict);
  });

  it("buildAgentPrompt embeds snapshot + OC", () => {
    const oc = H.opportunityCostEngine({ cost: 1000, monthlySurplus: 400, cash: 8000, floorBuf: 3000 });
    const prompt = H.buildAgentPrompt("ACCOUNTANT", {
      regimeDirective: "FOUNDATION",
      snapshotText: H.formatSnapshot({ nw: 20000, cash: 8000, surplus: 400 }),
      ocText: H.formatOcForPrompt(oc),
    });
    expect(prompt).toMatch(/THE ACCOUNTANT/);
    expect(prompt).toMatch(/OPPORTUNITY COST ENGINEER/);
    expect(prompt).toMatch(/FOUNDATION/);
  });

  it("offline tribunal ruling starts with verdict", () => {
    const oc = H.opportunityCostEngine({ cost: 10000, monthlySurplus: 200, cash: 5000, floorBuf: 4000 });
    const text = H.offlineTribunalRuling(oc, { name: "toy" });
    expect(text.split("\n")[0]).toBe(oc.verdict);
    expect(text).toMatch(/not financial advice/i);
  });

  it("regime maps survival → beekeeper", () => {
    const r = H.regimeOf({ runway: 0.2, liab: 50000, nw: 1000, assets: 2000 }, { efMonths: 3 });
    expect(r.stage).toBe("SURVIVAL");
    expect(r.persona).toBe("BEEKEEPER");
  });

  it("swarm default has seven named agents", () => {
    expect(H.SWARM_DEFAULT).toHaveLength(7);
    expect(H.SWARM_DEFAULT[0]).toBe("ACCOUNTANT");
  });
});
