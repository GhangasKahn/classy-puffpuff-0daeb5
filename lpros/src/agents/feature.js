/** Feature Agent — statistical features from raw candidates */
import { sellThroughProxy, competitionDensity, updateGammaPoisson, WEAK_VELOCITY_PRIOR } from "../core/bayesian.js";

export function extractFeatures(candidate) {
  const active = Number(candidate.activeCount || 0);
  const sold = Number(candidate.soldCount || 0);
  const windowDays = Number(candidate.windowDays || 14);
  const st = sellThroughProxy({ sold, active });
  const vel = updateGammaPoisson(WEAK_VELOCITY_PRIOR, sold, windowDays);
  const dens = competitionDensity({ active, velocityPerDay: vel.mean });
  return {
    ...candidate,
    features: {
      sellThrough: st,
      velocity: vel,
      density: dens,
      price: candidate.salePrice,
      cost: candidate.productCost,
    },
  };
}
