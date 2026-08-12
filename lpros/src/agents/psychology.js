/** Psychology / Fit Agent — provisional proxies only */
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
  return { ...candidate, psych, remorseRisk: psych.remorseRisk, psychFit: psych.psychFit };
}
