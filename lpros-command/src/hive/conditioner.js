/**
 * Oracle conditioner — authoritative gap + Pavlovian pairing from cited residuals.
 * Never prophesies. Never invents sold counts. Never punishes a HOLD that saved cash.
 */
import { readRecentOutcomes } from "../../../lpros/src/agents/outcome.js";
import { CATALOG_TO_PACK } from "../../../lpros-agents/src/loadPack.js";
import { postMessage } from "./comms.js";
import { matchTarget, readSoulPavlov } from "./pavlov.js";

const PACK_FOR = {
  brain: "orchestrator",
  evidence: "verifier",
  economics: "economist",
  copy: "copywriter",
  fulfill: "fulfiller",
  crawler: "taxonomy",
  ...Object.fromEntries(Object.entries(CATALOG_TO_PACK)),
};

export const TECHNIQUES = [
  "authoritative_gap",
  "pavlovian_pair",
  "process_vs_variance",
  "hold_saved",
  "theater_punish",
  "insufficient_defer",
  "four_d_score",
];

function packIdFor(soldierId) {
  return PACK_FOR[soldierId] || soldierId || "orchestrator";
}

function fourD({ cash = "cited residual", time = "this mission", policy = "constitution holds", reputation = "honest caption" } = {}) {
  return { cash, time, policy, reputation };
}

function classifyResidual(row) {
  const blob = JSON.stringify(row || {}).toLowerCase();
  if (row?.kind === "hold_saved" || /hold_saved|hold saved|protected cash/.test(blob)) {
    return { kind: "hold_saved", association: "reinforce", needle: "HOLD", processVsVariance: "process" };
  }
  if (row?.kind === "theater" || /swarm theater|workersran|claimed.*ran|all agents agree/.test(blob)) {
    return { kind: "theater", association: "punish", needle: "theater", processVsVariance: "process" };
  }
  if (row?.kind === "invented_sold" || /invented sold|fake sold|estimated \d+ sold/.test(blob)) {
    return { kind: "invented_sold", association: "punish", needle: "invented", processVsVariance: "process" };
  }
  if (row?.returned || row?.kind === "return") {
    return { kind: "return", association: "punish", needle: "remorse", processVsVariance: "variance" };
  }
  if (row?.profitable && !row?.returned) {
    return { kind: "net", association: "reinforce", needle: "Adverse", processVsVariance: "variance" };
  }
  if (row?.kind === "policy" || /replica|scrape|photo.copy|retail arbitrage/.test(blob)) {
    return { kind: "policy", association: "punish", needle: "scrape", processVsVariance: "process" };
  }
  return { kind: row?.kind || "residual", association: "reinforce", needle: "HOLD", processVsVariance: "process" };
}

function lessonFrom({ soldierId, row, citation, pavlov }) {
  const cls = classifyResidual(row);
  const target = matchTarget(pavlov, { association: cls.association, needle: cls.needle });
  const instruction =
    cls.kind === "hold_saved"
      ? "HOLD on thin evidence remains the correct next action; do not treat caution as failure."
      : cls.kind === "theater"
        ? "Name workersRan vs workersSimulated; never claim a pack executed Browse."
        : cls.kind === "invented_sold"
          ? "Replace invented n with sold_evidence_missing; Engine or HOLD."
          : cls.association === "punish"
            ? `Punish process: ${cls.kind} is not skill.`
            : `Reinforce the named SOUL target after cited residual (${cls.kind}).`;
  return {
    soldierId,
    association: cls.association,
    target,
    citation,
    processVsVariance: cls.processVsVariance,
    instruction,
    technique: cls.kind === "hold_saved" ? "hold_saved" : cls.kind === "theater" ? "theater_punish" : "pavlovian_pair",
    fourD: fourD({
      cash: cls.kind === "hold_saved" ? "floor protected" : "residual cited",
      policy: cls.kind === "invented_sold" || cls.kind === "policy" ? "constitution wins" : "clean-so-far",
    }),
  };
}

/**
 * @param {object} input
 * @param {string} [input.soldierId]
 * @param {string[]} [input.jobIds]
 * @param {object[]} [input.residuals]
 */
export function runConditioner(input = {}) {
  const soldierId = input.soldierId || "orchestrator";
  const packId = packIdFor(soldierId);
  const pavlov = readSoulPavlov(packId);
  const residuals = Array.isArray(input.residuals) ? input.residuals.filter(Boolean) : [];
  const jobIds = Array.isArray(input.jobIds) ? input.jobIds.filter(Boolean) : [];
  const outcomes = residuals.length || !input.useOutcomeLog ? [] : readRecentOutcomes(12);
  const cited = residuals.length
    ? residuals.map((r, i) => ({ row: r, citation: r.source || r.citation || jobIds[i] || `residual:${i}` }))
    : outcomes.map((r) => ({ row: r, citation: r.ts || r.sku || "outcomes.jsonl" }));

  if (!cited.length && !input.operatorConfirm) {
    const result = {
      verdict: "INSUFFICIENT_OUTCOMES",
      packOnly: true,
      prophecy: false,
      techniques: TECHNIQUES,
      lessons: [],
      prunes: [],
      recommended_next: "wait",
      soldierId,
      packId,
      note: "No cited residual, job id, or operator confirm — Oracle defers. No prophecy.",
    };
    postMessage({
      from: "conditioner",
      to: soldierId,
      type: "lesson",
      payload: result,
    });
    return result;
  }

  const lessons = cited.slice(0, 5).map(({ row, citation }) =>
    lessonFrom({ soldierId, row, citation, pavlov })
  );
  if (input.operatorConfirm && !lessons.length) {
    lessons.push(
      lessonFrom({
        soldierId,
        row: { kind: "hold_saved", note: input.operatorConfirm },
        citation: "operatorConfirm",
        pavlov,
      })
    );
  }

  const prunes = lessons
    .filter((l) => l.association === "punish" && l.processVsVariance === "process")
    .map((l) => l.target);

  const result = {
    verdict: "CONDITION",
    packOnly: true,
    prophecy: false,
    techniques: TECHNIQUES,
    lessons,
    prunes,
    recommended_next: "memento",
    soldierId,
    packId,
  };
  postMessage({ from: "conditioner", to: soldierId, type: "lesson", payload: result });
  return result;
}
