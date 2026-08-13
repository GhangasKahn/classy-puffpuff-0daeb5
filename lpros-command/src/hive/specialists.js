/**
 * Specialist JS workers — legal thesis / stress / ToS / caption / reverse-P&L / HOLD.
 * Markdown packs remain personas (packOnly). These functions are the desk workers.
 * Never crime. Never scrape how-tos. Never invent sold counts.
 */
import {
  listingsNeeded,
  netProfitPerSale,
  stressForecast,
} from "../../../lpros/src/core/economics.js";
import { CATALOG_TO_PACK, loadPack } from "../../../lpros-agents/src/loadPack.js";
import { getAgent } from "../playground/catalog.js";
import { postMessage, postReply } from "./comms.js";
import { runConditioner } from "./conditioner.js";

const CRIME = /hack|exploit|payload|phish|malware|credential.?stuff|doxx|unauthori[sz]ed|html scrape|scrape (ebay|search|hub)/i;

function num(v, d = null) {
  if (v == null || v === "") return d;
  const n = Number(v);
  return Number.isFinite(n) ? n : d;
}

export function attachPack(catalogId) {
  const spec = getAgent(catalogId);
  const packId = spec?.hermesPack || CATALOG_TO_PACK[catalogId] || catalogId;
  const pack = loadPack(packId);
  return {
    packOnly: true,
    packId: pack.id,
    mold: pack.mold,
    voice: pack.voice,
    soulExcerpt: pack.soulExcerpt,
    identityExcerpt: pack.identityExcerpt,
    proceduresExcerpt: pack.proceduresExcerpt,
    lengths: pack.lengths,
    note: pack.note,
    millionairePath:
      "Long-horizon fee-true expectancy after fail-closed gates — not a promise. Capital after proven loops (USER.md).",
  };
}

function fourD(partial = {}) {
  return {
    cash: partial.cash || "needs_engine or cited",
    time: partial.time || "lead unconfirmed",
    policy: partial.policy || "clean-so-far",
    reputation: partial.reputation || "no original photos claimed",
  };
}

export function runRedteam(input = {}) {
  const thesis = String(input.thesis || input.packet || "");
  if (CRIME.test(thesis) || CRIME.test(JSON.stringify(input))) {
    return {
      verdict: "REFUSE",
      crimeShaped: true,
      killingQuestion: "Would this require unauthorized access, scrape, or fraud?",
      vanityHits: ["crime_shaped_ask"],
      note: "Legal thesis attack only. Refuse and stop. No exploit steps.",
      fourD: fourD({ policy: "constitution veto" }),
    };
  }
  const vanityHits = [];
  const blob = thesis.toLowerCase();
  if (/zik/.test(blob)) vanityHits.push("zik_as_gospel");
  if (/print/.test(blob) && num(input.soldCount) == null) vanityHits.push("print_without_sold");
  if (/screenshot/.test(blob)) vanityHits.push("screenshot_as_demand");
  if (/all agents agree|swarm agrees/.test(blob)) vanityHits.push("swarm_theater");
  if (num(input.productCost) == null && num(input.cost) == null) vanityHits.push("single_quote_or_none");
  const kill = vanityHits.length > 0;
  return {
    verdict: kill ? "KILL" : "SURVIVE",
    crimeShaped: false,
    killingQuestion: kill
      ? "What observation would falsify this thesis without inventing n?"
      : "Thesis survived ridicule; still fail-closed at Verifier.",
    vanityHits,
    fourD: fourD({ cash: kill ? "vanity not cash" : "still needs Engine" }),
  };
}

export function runPressure(input = {}) {
  const price = num(input.salePrice ?? input.price, 49);
  const cost = num(input.productCost ?? input.cost, price * 0.4);
  const net = netProfitPerSale({
    salePrice: price,
    productCost: cost,
    returnsBufferRate: num(input.returns, 0.04),
  });
  const listings = num(input.listings, 300);
  const str = num(input.str, 0.015);
  const target = num(input.target, 50);
  const stress = stressForecast({ listings, str, avgNet: net.net, targetDailyProfit: target });
  const adverseNet = net.net * (1 - 0.15 * 0.5);
  const breaks = net.net <= 0 || adverseNet <= 0 || (stress.adverse?.expectedDailyProfit ?? 0) <= 0;
  return {
    verdict: breaks ? "HOLD" : "SURVIVE",
    engine: { net, stress },
    flipInputs: breaks
      ? { raisePriceOrCutCost: true, adverseDaily: stress.adverse?.expectedDailyProfit }
      : null,
    fourD: fourD({
      cash: breaks ? "Adverse/net cannot carry winter" : "Adverse still positive",
      time: "stress is a cost",
    }),
  };
}

export function runCompliance(input = {}) {
  const blob = JSON.stringify(input || {}).toLowerCase();
  const policyHits = [];
  if (/retail.?arbitrage|\bra\b/.test(blob)) policyHits.push("retail_arbitrage");
  if (/replica|counterfeit|knockoff/.test(blob)) policyHits.push("replica");
  if (/html scrape|scrape search|scrape hub/.test(blob)) policyHits.push("html_scrape");
  if (/copy (competitor )?photo|stolen photo|competitor image/.test(blob)) policyHits.push("photo_copy");
  if (/invented sold|fake sold/.test(blob)) policyHits.push("invented_sold");
  if (CRIME.test(blob)) policyHits.push("unauthorized_access");
  const veto = policyHits.length > 0;
  return {
    verdict: veto ? "VETO" : "CLEAR",
    policyHits,
    note: veto ? "See the system. Never become the criminal. Stop." : "No policy hit in packet.",
    fourD: fourD({ policy: veto ? "veto" : "clean-so-far" }),
  };
}

export function runMemento(input = {}) {
  const entry = input.proposedEntry || input;
  const blob = JSON.stringify(entry || {});
  const cooked = /soft-pass|cook.*fail|fail.*into.*pass/i.test(blob);
  const invented = /invented sold|soldCount.: *"?guess/i.test(blob);
  const unwritten = !entry || (typeof entry === "object" && !Object.keys(entry).length);
  const ok = !cooked && !invented && !unwritten;
  const caption = ok
    ? `TATTOO ${new Date().toISOString()} soldier=${entry.soldierId || input.soldierId || "unknown"} verdict=${entry.verdict || "noted"} citation=${entry.citation || input.citation || "none"}`
    : "REJECTED — unwritten, cooked, or invented n is not a tattoo.";
  return {
    verdict: ok ? "TATTOO" : "REJECT",
    caption,
    cooked,
    invented,
    fourD: fourD({ reputation: ok ? "written" : "unwritten is untrue" }),
  };
}

export function runInversion(input = {}) {
  const target = num(input.target ?? input.desiredDailyProfit, 50);
  const str = num(input.str, 0.015);
  const price = num(input.salePrice ?? input.price, 49);
  const cost = num(input.productCost ?? input.cost);
  const packet = input.packet || input;
  const breaks = [];
  if (cost == null) breaks.push({ link: "cogs", reason: "single quote / missing cost — cannot reverse P&L" });
  const net = cost != null ? netProfitPerSale({ salePrice: price, productCost: cost }) : null;
  if (net && net.net <= 0) breaks.push({ link: "net", reason: "Base net ≤ 0 — resign the forward line" });
  const need = net && net.net > 0 ? listingsNeeded({ targetDailyProfit: target, str, avgNet: net.net }) : null;
  if (need && need.listingsNeeded > 2000) {
    breaks.push({ link: "listings_needed", reason: `Need ${need.listingsNeeded} listings — time is a cost` });
  }
  if (/invented|prophecy|will explode/.test(JSON.stringify(packet))) {
    breaks.push({ link: "future_cash", reason: "Invented future cash is mysticism" });
  }
  const firstBreak = breaks[0] || null;
  return {
    verdict: firstBreak ? "HOLD" : "CHAIN_OK",
    firstBreak,
    reverseChain: [
      { link: "desired_daily", value: target },
      { link: "str", value: str },
      { link: "net", value: net?.net ?? null },
      { link: "listings_needed", value: need?.listingsNeeded ?? null },
    ],
    engine: net,
    fourD: fourD({ cash: firstBreak ? firstBreak.reason : "reverse chain intact", time: "first broken reverse link wins" }),
  };
}

export function runWick(input = {}) {
  const markers = []
    .concat(input.openMarkers || [])
    .concat(input.markers || [])
    .filter(Boolean);
  if (num(input.soldCount) == null && input.requireSold !== false) markers.push("sold_evidence_missing");
  if (num(input.productCost ?? input.cost) == null) markers.push("supplier_cost_missing");
  if (num(input.altProductCost) == null) markers.push("alt_cost_missing");
  if (!input.supplierConfirmed) markers.push("supplier_unconfirmed");
  const unique = [...new Set(markers)];
  const clear = unique.length === 0;
  return {
    verdict: clear ? "CLEAR" : "HOLD",
    openMarkers: unique,
    consequenceIfSkipped: clear
      ? null
      : "Skip confirm → INR / skip Engine → capital death / skip ToS → account health death.",
    note: "Wick never AUTO. CLEAR means Fulfiller may consider AUTO only after Adverse net > 0.",
    fourD: fourD({ cash: clear ? "markers closed" : "open markers", policy: "HOLD until complete" }),
  };
}

const SPECIALISTS = {
  redteam: runRedteam,
  pressure: runPressure,
  compliance: runCompliance,
  memento: runMemento,
  inversion: runInversion,
  wick: runWick,
  conditioner: runConditioner,
};

export function runSpecialist(catalogId, input = {}, { contractId = null } = {}) {
  const fn = SPECIALISTS[catalogId];
  if (!fn) {
    throw Object.assign(new Error(`unknown specialist: ${catalogId}`), { status: 400 });
  }
  const worker = fn(input);
  const pack = attachPack(catalogId);
  const result = {
    ...pack,
    ...worker,
    note: pack.note,
    packId: pack.packId,
    workerNote: worker.note || null,
    input,
    workerRan: true,
    workersRan: [catalogId],
    workersSimulated: [],
  };
  postReply({
    from: catalogId,
    to: "brain",
    contractId,
    payload: {
      verdict: result.verdict,
      workersRan: result.workersRan,
      workersSimulated: [],
      fourD: result.fourD,
    },
  });
  if (result.verdict === "VETO" || result.crimeShaped) {
    postMessage({ from: catalogId, to: "brain", type: "veto", contractId, payload: { verdict: result.verdict } });
  }
  if (result.verdict === "HOLD") {
    postMessage({ from: catalogId, to: "brain", type: "hold", contractId, payload: { verdict: "HOLD" } });
  }
  return result;
}

export { SPECIALISTS };
