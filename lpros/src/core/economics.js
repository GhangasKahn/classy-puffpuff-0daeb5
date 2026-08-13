/**
 * LPROS Economics Engine — deterministic, cash-is-truth.
 * All agents defer to this for fee / net / listings-needed math.
 */

/** Default US marketplace fee stack (2026-ish standard categories). */
export const DEFAULT_FEES = {
  fvfRate: 0.136, // Final Value Fee on (item + shipping charged to buyer)
  perOrderFeeLow: 0.3, // orders ≤ $10
  perOrderFeeHigh: 0.4, // orders > $10
  perOrderThreshold: 10,
  storeFvfDiscount: 0.009, // Basic Store often ~0.9 pts lower
};

/**
 * eBay fees on total buyer payment (item + shipping charged).
 * @param {number} buyerTotal
 * @param {{ fvfRate?: number, hasStore?: boolean }} [opts]
 */
export function ebayFees(buyerTotal, opts = {}) {
  const rate = Math.max(
    0,
    (opts.fvfRate ?? DEFAULT_FEES.fvfRate) - (opts.hasStore ? DEFAULT_FEES.storeFvfDiscount : 0)
  );
  const perOrder =
    buyerTotal <= DEFAULT_FEES.perOrderThreshold
      ? DEFAULT_FEES.perOrderFeeLow
      : DEFAULT_FEES.perOrderFeeHigh;
  const fvf = buyerTotal * rate;
  const total = fvf + perOrder;
  return {
    buyerTotal,
    fvfRate: rate,
    fvf: round2(fvf),
    perOrderFee: perOrder,
    fees: round2(total),
    effectiveRate: buyerTotal > 0 ? total / buyerTotal : 0,
  };
}

/**
 * Net profit per sale after product cost, fees, shipping differential, returns buffer.
 *
 * @param {object} p
 * @param {number} p.salePrice - what buyer pays for item (shipping may be separate)
 * @param {number} [p.shippingCharged=0] - shipping charged to buyer
 * @param {number} p.productCost - landed cost from supplier (incl supplier shipping to buyer if dropship)
 * @param {number} [p.shippingCostExtra=0] - any extra you pay beyond productCost
 * @param {number} [p.returnsBufferRate=0.04] - reserve as fraction of salePrice
 * @param {number} [p.toolAmortPerSale=0] - fixed tools allocated per expected sale
 * @param {boolean} [p.hasStore=false]
 * @param {number} [p.fvfRate]
 */
export function netProfitPerSale(p) {
  const salePrice = num(p.salePrice);
  const shippingCharged = num(p.shippingCharged);
  const buyerTotal = salePrice + shippingCharged;
  const fees = ebayFees(buyerTotal, { hasStore: p.hasStore, fvfRate: p.fvfRate });
  const productCost = num(p.productCost);
  const shippingCostExtra = num(p.shippingCostExtra);
  const returnsBufferRate = p.returnsBufferRate ?? 0.04;
  const returnsBuffer = salePrice * returnsBufferRate;
  const toolAmort = num(p.toolAmortPerSale);
  const cogs = productCost + shippingCostExtra;
  const net = buyerTotal - fees.fees - cogs - returnsBuffer - toolAmort;
  const margin = buyerTotal > 0 ? net / buyerTotal : 0;
  return {
    ...fees,
    salePrice,
    shippingCharged,
    productCost,
    shippingCostExtra,
    returnsBuffer: round2(returnsBuffer),
    returnsBufferRate,
    toolAmortPerSale: round2(toolAmort),
    cogs: round2(cogs),
    net: round2(net),
    margin: round4(margin),
    marginPct: round2(margin * 100),
  };
}

/**
 * Expected daily profit = N × STR × avgNet
 * STR = sales per listing per day (e.g. 0.018 = 1.8%/day)
 */
export function expectedDailyProfit({ listings, str, avgNet }) {
  const N = num(listings);
  const s = num(str);
  const a = num(avgNet);
  return {
    listings: N,
    str: s,
    avgNet: a,
    expectedDailyProfit: round2(N * s * a),
  };
}

/**
 * Listings needed to hit daily profit target Z.
 * N = Z / (STR × avgNet)
 */
export function listingsNeeded({ targetDailyProfit, str, avgNet }) {
  const Z = num(targetDailyProfit);
  const s = num(str);
  const a = num(avgNet);
  if (s <= 0 || a <= 0) {
    return {
      targetDailyProfit: Z,
      str: s,
      avgNet: a,
      listingsNeeded: Infinity,
      feasible: false,
      reason: "STR and avgNet must be > 0",
    };
  }
  const n = Z / (s * a);
  return {
    targetDailyProfit: Z,
    str: s,
    avgNet: a,
    listingsNeeded: Math.ceil(n),
    listingsExact: round2(n),
    feasible: true,
  };
}

/**
 * Stress / sensitivity: Base, Adverse, Severe (LPROS forecasting triad).
 */
export function stressForecast({
  listings,
  str,
  avgNet,
  targetDailyProfit,
  strHaircut = 0.2,
  returnsHitOnNet = 0.15,
}) {
  const base = expectedDailyProfit({ listings, str, avgNet });
  const adverse = expectedDailyProfit({
    listings,
    str: str * (1 - strHaircut),
    avgNet: avgNet * (1 - returnsHitOnNet * 0.5),
  });
  const severe = expectedDailyProfit({
    listings,
    str: str * (1 - strHaircut * 1.5),
    avgNet: avgNet * (1 - returnsHitOnNet),
  });
  const needBase = listingsNeeded({ targetDailyProfit, str, avgNet });
  const needAdverse = listingsNeeded({
    targetDailyProfit,
    str: str * (1 - strHaircut),
    avgNet: avgNet * (1 - returnsHitOnNet * 0.5),
  });
  return {
    assumptions: { listings, str, avgNet, targetDailyProfit, strHaircut, returnsHitOnNet },
    base,
    adverse,
    severe,
    listingsForTarget: { base: needBase, adverse: needAdverse },
  };
}

/**
 * Minimum sale price to hit target net margin given costs.
 */
export function minSalePriceForMargin({
  productCost,
  shippingCharged = 0,
  shippingCostExtra = 0,
  targetMargin = 0.15,
  returnsBufferRate = 0.04,
  hasStore = false,
  fvfRate,
  toolAmortPerSale = 0,
}) {
  // Solve roughly by search — fees depend on buyer total.
  let lo = productCost + 1;
  let hi = Math.max(productCost * 5, productCost + 100);
  let best = null;
  for (let i = 0; i < 40; i++) {
    const mid = (lo + hi) / 2;
    const r = netProfitPerSale({
      salePrice: mid,
      shippingCharged,
      productCost,
      shippingCostExtra,
      returnsBufferRate,
      hasStore,
      fvfRate,
      toolAmortPerSale,
    });
    if (r.margin >= targetMargin) {
      best = r;
      hi = mid;
    } else {
      lo = mid;
    }
  }
  return best;
}

function num(x) {
  const n = Number(x);
  return Number.isFinite(n) ? n : 0;
}
function round2(x) {
  return Math.round(x * 100) / 100;
}
function round4(x) {
  return Math.round(x * 10000) / 10000;
}
