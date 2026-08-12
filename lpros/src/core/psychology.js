/**
 * Psychological feature proxies — FEATURE ENGINEERING, not calibrated probabilities.
 * Sources (Greene, Jung, Adler, Voss, Hughes, Babylon, etc.) inspire features;
 * every feature must later prove value against real conversion/returns.
 */

const COMPLEXITY =
  /\b(kit|diy|assembly|setup required|instructions|calibrat|programmable|multi[- ]?step|compatible with)\b/i;
const IMPULSE_HIGH =
  /\b(gadget|novelty|funny|meme|viral|led|rgb|surprise)\b/i;
const UTILITY =
  /\b(tool|organizer|holder|protector|charger|adapter|replacement|filter|seal|mount|stand|storage)\b/i;
const STATUS =
  /\b(premium|pro|leather|stainless|titanium|luxury|limited|edition|carbon)\b/i;
const MASTERY =
  /\b(training|practice|skill|beginner|intermediate|professional|learn|guide)\b/i;
const CAREGIVER =
  /\b(comfort|relief|support|massage|orthopedic|baby|pet|sleep|recovery)\b/i;
const SCARCITY =
  /\b(limited|rare|discontinued|last|only \d+|oes|nwt|vintage)\b/i;
const AUTHORITY =
  /\b(oem|official|certified|tested|warranty|spec|datasheet|industrial)\b/i;
const EMPATHY_PAIN =
  /\b(fix|leak|rust|noise|clutter|slow|broken|worn|scratch|fog|glare)\b/i;

/**
 * Extract cheap text/price proxies from a candidate listing or keyword cluster.
 * @returns {{ features: object, subscores: object, psychFit: number, remorseRisk: number, notes: string[] }}
 */
export function psychProxies({
  title = "",
  description = "",
  salePrice = 0,
  categoryMedianPrice = 0,
  velocityPerDay = 0,
  active = 0,
} = {}) {
  const text = `${title} ${description}`;
  const notes = [];

  const complexity = COMPLEXITY.test(text) ? 1 : 0;
  const impulse = IMPULSE_HIGH.test(text) ? 1 : 0;
  const utility = UTILITY.test(text) ? 1 : 0;
  const status = STATUS.test(text) ? 1 : 0;
  const mastery = MASTERY.test(text) ? 1 : 0;
  const caregiver = CAREGIVER.test(text) ? 1 : 0;
  const scarcity = SCARCITY.test(text) ? 1 : 0;
  const authority = AUTHORITY.test(text) ? 1 : 0;
  const empathy = EMPATHY_PAIN.test(text) ? 1 : 0;

  const price = Number(salePrice) || 0;
  const med = Number(categoryMedianPrice) || 0;
  const priceToMedian = med > 0 ? price / med : 1;

  // Remorse risk 0..1 (higher = worse). Kill-filter input.
  let remorseRisk =
    0.15 +
    0.25 * complexity +
    0.2 * impulse * (price > 40 ? 1 : 0.4) +
    0.15 * Math.max(0, priceToMedian - 1.4) +
    (utility || caregiver || mastery ? -0.12 : 0);
  remorseRisk = clamp01(remorseRisk);
  if (remorseRisk > 0.65) notes.push("high remorse-risk proxies");

  // FOMO / urgency from velocity vs stock (authentic only)
  const fomo =
    active > 0
      ? clamp01((velocityPerDay * 7) / Math.max(active, 1))
      : clamp01(velocityPerDay / 2);
  if (scarcity && fomo < 0.2) notes.push("scarcity language without velocity — fake FOMO risk");

  // Archetype / drive proxies (inspirational, uncalibrated)
  const hero = clamp01(0.5 * mastery + 0.3 * utility + 0.2 * status);
  const caregiverScore = clamp01(0.7 * caregiver + 0.3 * empathy);
  const magician = clamp01(0.4 * status + 0.3 * impulse + 0.3 * scarcity);
  const adler = clamp01(0.5 * mastery + 0.3 * status + 0.2 * authority);
  const greeneFantasy = clamp01(0.4 * status + 0.3 * mastery + 0.3 * magician);
  const vossEmpathy = clamp01(0.6 * empathy + 0.4 * utility);
  const hughesCompliance = clamp01(0.5 * authority + 0.3 * utility + 0.2 * mastery);

  const features = {
    complexity,
    impulse,
    utility,
    status,
    mastery,
    caregiver,
    scarcity,
    authority,
    empathy,
    priceToMedian: round3(priceToMedian),
    fomo: round3(fomo),
  };

  const subscores = {
    remorseRisk: round3(remorseRisk),
    fomo: round3(fomo),
    greeneFantasy: round3(greeneFantasy),
    jungHero: round3(hero),
    jungCaregiver: round3(caregiverScore),
    jungMagician: round3(magician),
    adler: round3(adler),
    vossEmpathy: round3(vossEmpathy),
    hughesCompliance: round3(hughesCompliance),
  };

  // Weighted fit — provisional expert weights; must be recalibrated on outcomes
  const psychFit = clamp01(
    0.22 * (1 - remorseRisk) +
      0.18 * fomo +
      0.12 * greeneFantasy +
      0.1 * hero +
      0.08 * caregiverScore +
      0.08 * adler +
      0.1 * vossEmpathy +
      0.12 * hughesCompliance
  );

  return {
    features,
    subscores,
    psychFit: round3(psychFit),
    remorseRisk: round3(remorseRisk),
    notes,
    caveat:
      "PsychFit is a provisional proxy score from text/price heuristics — not a validated probability. Recalibrate with real conversion/returns.",
  };
}

function clamp01(x) {
  return Math.min(1, Math.max(0, x));
}
function round3(x) {
  return Math.round(x * 1000) / 1000;
}
