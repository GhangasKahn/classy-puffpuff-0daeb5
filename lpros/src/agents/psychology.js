/** Psychology / Fit Agent — provisional proxies; kills scammy dropship junk */
import { psychProxies } from "../core/psychology.js";

export function scorePsychology(candidate) {
  const psych = psychProxies({
    title: candidate.title || candidate.ref || "",
    description: candidate.description || "",
    salePrice: candidate.salePrice,
    categoryMedianPrice: candidate.categoryMedianPrice || candidate.salePrice,
    velocityPerDay: candidate.features?.velocity?.mean || candidate.velocityPerDay || 0,
    active: candidate.activeCount || 0,
  });
  return {
    ...candidate,
    psych,
    remorseRisk: psych.remorseRisk,
    psychFit: psych.psychFit,
    perceivedValue: psych.perceivedValue,
    variationPotential: psych.variationPotential,
    scammy: psych.scammy,
    scamHits: psych.scamHits,
    problemSolving: Boolean(psych.features?.problemSolving),
    upgradeReplace: Boolean(psych.features?.upgradeReplace),
  };
}
