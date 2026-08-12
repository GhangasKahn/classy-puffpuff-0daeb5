/**
 * Cheap Bayesian / statistical helpers for demand velocity.
 * Gamma-Poisson conjugate for daily sold counts (lightweight, no ML deps).
 */

/**
 * Posterior for Poisson rate λ given Gamma(α, β) prior (rate parameterization:
 * mean = α/β). Observations: counts over days (or listing-days).
 *
 * @param {{ alpha: number, beta: number }} prior
 * @param {number} totalSold - sum of counts
 * @param {number} exposure - days or listing-days
 */
export function updateGammaPoisson(prior, totalSold, exposure) {
  const alpha = prior.alpha + totalSold;
  const beta = prior.beta + exposure;
  const mean = alpha / beta;
  const variance = alpha / (beta * beta);
  const std = Math.sqrt(variance);
  // Approximate 90% credible interval via normal on mean for speed (ok for α>5)
  const z = 1.645;
  return {
    alpha,
    beta,
    mean,
    variance,
    std,
    ci90: [Math.max(0, mean - z * std), mean + z * std],
    exposure,
    totalSold,
  };
}

/** Weakly informative prior: expect ~0.5 sold / day / category cluster, soft. */
export const WEAK_VELOCITY_PRIOR = { alpha: 2, beta: 4 }; // mean 0.5

/**
 * Sell-through proxy: sold / (active + sold) over window.
 * Uncertainty via Wilson-like widening when n small.
 */
export function sellThroughProxy({ sold, active }) {
  const s = Math.max(0, Number(sold) || 0);
  const a = Math.max(0, Number(active) || 0);
  const n = s + a;
  if (n === 0) {
    return { str: 0, n: 0, low: 0, high: 0, confidence: 0 };
  }
  const p = s / n;
  // Agresti-Coull style adjustment
  const z = 1.96;
  const n2 = n + z * z;
  const p2 = (s + (z * z) / 2) / n2;
  const se = Math.sqrt((p2 * (1 - p2)) / n2);
  const low = Math.max(0, p2 - z * se);
  const high = Math.min(1, p2 + z * se);
  const confidence = Math.min(1, n / (n + 30)); // saturates as sample grows
  return { str: p, n, low, high, confidence };
}

/**
 * Competition density: active / max(velocity, eps).
 * Lower is better for entry.
 */
export function competitionDensity({ active, velocityPerDay }) {
  const a = Math.max(0, Number(active) || 0);
  const v = Math.max(Number(velocityPerDay) || 0, 0.01);
  const density = a / v;
  return { active: a, velocityPerDay: v, density };
}

/**
 * Uncertainty penalty for ranking: shrink expected value toward 0 when confidence low.
 * score = expected * (confidence ^ k)
 */
export function uncertaintyShrink(expected, confidence, k = 1) {
  const c = Math.min(1, Math.max(0, Number(confidence) || 0));
  const e = Number(expected) || 0;
  return e * Math.pow(c, k);
}
