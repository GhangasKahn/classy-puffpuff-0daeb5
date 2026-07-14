/**
 * Node harness for site/app/quant-engine.js (no DOM).
 */
import { readFileSync } from "fs";
import { createContext, runInContext } from "vm";
import { describe, expect, it } from "vitest";

function loadQuant() {
  const code = readFileSync(new URL("../../site/app/quant-engine.js", import.meta.url), "utf8");
  const sandbox = { Math, console, JSON, Array, Object, parseInt, parseFloat, isFinite, Infinity, NaN };
  sandbox.globalThis = sandbox;
  sandbox.window = sandbox;
  runInContext(code, createContext(sandbox));
  return sandbox.window.BedrockQuant;
}

const Q = loadQuant();

describe("BedrockQuant god-tier stack", () => {
  it("exposes versioned API", () => {
    expect(Q.version).toMatch(/godtier/);
  });

  it("LLN: running mean converges toward μ", () => {
    const ex = Q.llnExperiment({ seed: 7, n: 5000, mu: 0.1, sigma: 0.2 });
    expect(Math.abs(ex.finalMean - 0.1)).toBeLessThan(0.02);
    expect(ex.finalError).toBeLessThan(ex.absError[10]);
  });

  it("portfolio suite: risk parity weights sum ~1 and CVaR defined", () => {
    const suite = Q.portfolioSuite(42);
    const w = suite.books.riskParity.weights;
    const sum = w.reduce((a, b) => a + b, 0);
    expect(sum).toBeCloseTo(1, 5);
    expect(suite.books.maxSharpe.sharpe).toBeGreaterThan(suite.books.equityHeavy.sharpe - 0.5);
    expect(Number.isFinite(suite.books.minVar.cvar5)).toBe(true);
    expect(suite.rotation.regime).toMatch(/RISK_|NEUTRAL/);
  });

  it("Black–Scholes call delta in (0,1) ATM", () => {
    const bs = Q.blackScholes({ S: 100, K: 100, T: 1, r: 0.03, sigma: 0.2, type: "call" });
    expect(bs.price).toBeGreaterThan(0);
    expect(bs.delta).toBeGreaterThan(0.4);
    expect(bs.delta).toBeLessThan(0.7);
    const leg = Q.deltaHedgeLeg(bs, 1, 100);
    expect(leg.shares).toBeCloseTo(-bs.delta * 100, 5);
  });

  it("bond convexity positive", () => {
    const b = Q.bondMetrics(100, 0.05, 10, 0.05, 2);
    expect(b.convexity).toBeGreaterThan(0);
    expect(b.macaulay).toBeGreaterThan(5);
  });

  it("chaos: logistic Lyapunov positive at r=3.9", () => {
    expect(Q.lyapunovLogistic(3.9, 3000, 0.5)).toBeGreaterThan(0);
  });

  it("game theory mixed Nash probabilities in [0,1]", () => {
    const hd = Q.hawkDove(2, 4);
    expect(hd.nash.p[0]).toBeGreaterThan(0);
    expect(hd.nash.p[0]).toBeLessThan(1);
  });

  it("OLS recovers approximate slope", () => {
    const rng = Q.makeRng(3);
    const X = [], y = [];
    for (let i = 0; i < 80; i++) {
      const x = rng();
      X.push([1, x]);
      y.push(2 + 3 * x + 0.01 * Q.gauss(rng));
    }
    const fit = Q.ols(X, y);
    expect(fit.beta[1]).toBeGreaterThan(2.5);
    expect(fit.beta[1]).toBeLessThan(3.5);
    expect(fit.r2).toBeGreaterThan(0.95);
  });

  it("Q-learning returns a policy for all regimes", () => {
    const ql = Q.qLearnCapital({ seed: 1, episodes: 120 });
    expect(ql.policy.BULL).toBeTruthy();
    expect(ql.policy.BEAR).toBeTruthy();
  });

  it("Heston path stays positive", () => {
    const h = Q.hestonPath({ seed: 5, steps: 100 });
    expect(h.S.every((s) => s > 0)).toBe(true);
    expect(h.v.every((v) => v > 0)).toBe(true);
  });

  it("effective bets ≤ n holdings", () => {
    const w = [0.5, 0.3, 0.2];
    expect(Q.effectiveBets(w)).toBeLessThanOrEqual(3);
    expect(Q.effectiveBets([1, 0, 0])).toBeCloseTo(1, 5);
  });
});
