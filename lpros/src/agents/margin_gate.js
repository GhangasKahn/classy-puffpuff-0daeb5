/** Margin & Gate Agent — pure deterministic economics + zero-trust verify */
import { netProfitPerSale, listingsNeeded, stressForecast, expectedDailyProfit } from "../core/economics.js";
import { verifyProduct } from "../core/verify.js";

export function runMarginGate(candidate, thresholds) {
  const economics = netProfitPerSale({
    salePrice: candidate.salePrice,
    shippingCharged: candidate.shippingCharged || 0,
    productCost: candidate.productCost,
    shippingCostExtra: candidate.shippingCostExtra || 0,
    returnsBufferRate: candidate.returnsBufferRate ?? 0.04,
    hasStore: candidate.hasStore,
    toolAmortPerSale: candidate.toolAmortPerSale || 0,
  });
  const verification = verifyProduct(
    {
      ...candidate,
      remorseRisk: candidate.remorseRisk ?? candidate.psych?.remorseRisk,
      density: candidate.features?.density?.density ?? candidate.density,
      velocityPerDay: candidate.features?.velocity?.mean ?? candidate.velocityPerDay,
      demandConfidence: candidate.demandConfidence ?? candidate.features?.sellThrough?.confidence,
    },
    thresholds
  );
  return { ...candidate, economics, verification };
}

export function forecastListings({ targetDailyProfit, str, avgNet, listings }) {
  return {
    expected: expectedDailyProfit({ listings, str, avgNet }),
    needed: listingsNeeded({ targetDailyProfit, str, avgNet }),
    stress: stressForecast({ listings, str, avgNet, targetDailyProfit }),
  };
}
