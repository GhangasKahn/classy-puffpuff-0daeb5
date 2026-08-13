/**
 * Psychological / listing-quality proxies — FEATURE ENGINEERING, not calibrated probabilities.
 * Prefer: high perceived value, problem-solving, upgrade-over-replacement, unique,
 * multi-variation potential. Kill: scammy dropship red flags.
 */

/** Scammy / low-trust dropship tells — hard kill when score high. */
const SCAM_PATTERNS = [
  { id: "qty_spam", re: /\b\d{1,4}\s*[-–\/]\s*\d{2,4}\s*(pcs|pc|pieces|pack|set)\b/i, w: 1.2 },
  { id: "mega_lot", re: /\b(\d{3,}\s*(pcs|pc|pieces)|lot of \d{2,}|bulk lot|wholesale lot)\b/i, w: 1.0 },
  { id: "title_spam", re: /(\*{2,}|\|{2,}|!{2,}|\${2,})/, w: 0.9 },
  { id: "clickbait", re: /\b(hot sale|best deal|must have|as seen on|viral|tiktok|shocking|amazing deal)\b/i, w: 1.0 },
  { id: "replica", re: /\b(replica|counterfeit|fake|1:1|aaa quality|homage(?!\s+style))\b/i, w: 1.5 },
  { id: "brand_hijack", re: /\b(inspired by|look[- ]alike|dupe for)\b/i, w: 0.8 },
  { id: "new_spam", re: /\b(new\s+){2,}|brand new brand new/i, w: 0.6 },
  { id: "free_ship_title", re: /\bfree\s+shipping\b/i, w: 0.4 },
  { id: "generic_gadget", re: /\b(led rgb|funny meme|novelty gag|random color)\b/i, w: 0.9 },
  { id: "dropship_tell", re: /\b(dropship|ali express|aliexpress|fast from china only)\b/i, w: 1.2 },
];

const PROBLEM_SOLVING =
  /\b(organizer|management|prevents?|stops?|reduces?|eliminates?|solves?|anti[- ]?(slip|rust|glare|fog|static)|no[- ]?drill|clutter|cable|leak|noise|scratch|strain|storage)\b/i;
const UPGRADE_REPLACE =
  /\b(upgrade|replaces?|replacement for|better than|vs\.?|compared to|improved|heavy[- ]?duty|reinforced|precision|pro\b|professional)\b/i;
const PERCEIVED_VALUE_MATERIALS =
  /\b(solid wood|hardwood|oak|walnut|bamboo|stainless|brushed steel|aluminum|aluminium|titanium|brass|ceramic|tempered glass|full[- ]?grain|genuine leather|aircraft[- ]?grade|anodized)\b/i;
const UNIQUENESS =
  /\b(modular|adjustable|custom|patented|ergonomic|magnetic mount|ventilated|hexagon|minimalist|handcrafted|artisan|designed for)\b/i;
const MULTI_VARIATION =
  /\b(size|sizes|color|colours?|variant|left\/right|set of|with drawer|with shelf|expandable|stackable|add[- ]?on)\b/i;
const CLEAR_USE_CASE =
  /\b(desk|kitchen|garage|bathroom|travel|laptop|monitor|under[- ]?desk|nightstand|workshop|office|car|bike)\b/i;

const COMPLEXITY =
  /\b(diy only|assembly required|soldering|firmware|calibrat|programmable|compatible with only)\b/i;
const IMPULSE_HIGH =
  /\b(gadget|novelty|funny|meme|viral|surprise gift|gag)\b/i;
const UTILITY =
  /\b(tool|organizer|holder|protector|charger|adapter|replacement|filter|seal|mount|stand|storage|tray|rack)\b/i;
const STATUS =
  /\b(premium|pro|leather|stainless|titanium|luxury|limited|edition|carbon|walnut|oak)\b/i;
const MASTERY =
  /\b(training|practice|skill|beginner|intermediate|professional|learn|guide)\b/i;
const CAREGIVER =
  /\b(comfort|relief|support|massage|orthopedic|baby|pet|sleep|recovery)\b/i;
const SCARCITY =
  /\b(limited|rare|discontinued|last|only \d+|oes|nwt|vintage)\b/i;
const AUTHORITY =
  /\b(oem|official|certified|tested|warranty|spec|datasheet|industrial)\b/i;
const EMPATHY_PAIN =
  /\b(fix|leak|rust|noise|clutter|slow|broken|worn|scratch|fog|glare|tangled|mess)\b/i;

/**
 * @returns {object} proxies + scamFlags + killRecommendation
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

  const scamHits = [];
  let scamScore = 0;
  for (const p of SCAM_PATTERNS) {
    if (p.re.test(title) || p.re.test(text)) {
      scamHits.push(p.id);
      scamScore += p.w;
    }
  }
  // Punctuation density / ALL CAPS spam in title
  const capsRatio = title.length ? (title.replace(/[^A-Z]/g, "").length / title.length) : 0;
  if (capsRatio > 0.55 && title.length > 20) {
    scamHits.push("caps_spam");
    scamScore += 0.7;
  }
  scamScore = Math.min(3, scamScore);
  const scammy = scamScore >= 1.2 || scamHits.includes("replica") || scamHits.includes("dropship_tell");
  if (scammy) notes.push(`scam/red-flag signals: ${scamHits.join(", ")}`);

  const problemSolving = PROBLEM_SOLVING.test(text) ? 1 : 0;
  const upgradeReplace = UPGRADE_REPLACE.test(text) ? 1 : 0;
  const materials = PERCEIVED_VALUE_MATERIALS.test(text) ? 1 : 0;
  const unique = UNIQUENESS.test(text) ? 1 : 0;
  const multiVariation = MULTI_VARIATION.test(text) ? 1 : 0;
  const useCase = CLEAR_USE_CASE.test(text) ? 1 : 0;

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

  // High perceived value composite (what we want)
  const perceivedValue = clamp01(
    0.28 * materials +
      0.22 * problemSolving +
      0.18 * upgradeReplace +
      0.12 * unique +
      0.1 * useCase +
      0.1 * status
  );

  // Multi-variation / repurchase potential (family of SKUs, not spam lots)
  const variationPotential = clamp01(
    0.45 * multiVariation +
      0.25 * unique +
      0.2 * useCase +
      0.1 * problemSolving -
      (scamHits.includes("qty_spam") || scamHits.includes("mega_lot") ? 0.5 : 0)
  );

  // Remorse risk — scammy + impulse + complexity raise; utility/upgrade lower
  let remorseRisk =
    0.12 +
    0.35 * Math.min(1, scamScore / 2) +
    0.2 * complexity +
    0.18 * impulse * (price > 40 ? 1 : 0.5) +
    0.12 * Math.max(0, priceToMedian - 1.5) -
    0.1 * problemSolving -
    0.08 * upgradeReplace -
    0.08 * materials -
    (utility || caregiver || mastery ? 0.08 : 0);
  remorseRisk = clamp01(remorseRisk);
  if (remorseRisk > 0.55) notes.push("elevated remorse-risk proxies");

  const fomo =
    active > 0
      ? clamp01((velocityPerDay * 7) / Math.max(active, 1))
      : clamp01(velocityPerDay / 2);
  if (scarcity && fomo < 0.2) notes.push("scarcity language without velocity — fake FOMO risk");

  const hero = clamp01(0.4 * mastery + 0.3 * upgradeReplace + 0.3 * problemSolving);
  const caregiverScore = clamp01(0.6 * caregiver + 0.4 * empathy);
  const magician = clamp01(0.5 * unique + 0.3 * materials + 0.2 * status);
  const adler = clamp01(0.4 * mastery + 0.3 * upgradeReplace + 0.3 * authority);
  const greeneFantasy = clamp01(0.35 * materials + 0.35 * status + 0.3 * unique);
  const vossEmpathy = clamp01(0.45 * empathy + 0.35 * problemSolving + 0.2 * upgradeReplace);
  const hughesCompliance = clamp01(0.4 * authority + 0.3 * materials + 0.3 * useCase);

  const features = {
    scamScore: round3(scamScore),
    scamHits,
    problemSolving,
    upgradeReplace,
    materials,
    unique,
    multiVariation,
    useCase,
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
    perceivedValue: round3(perceivedValue),
    variationPotential: round3(variationPotential),
  };

  const subscores = {
    remorseRisk: round3(remorseRisk),
    fomo: round3(fomo),
    perceivedValue: round3(perceivedValue),
    variationPotential: round3(variationPotential),
    greeneFantasy: round3(greeneFantasy),
    jungHero: round3(hero),
    jungCaregiver: round3(caregiverScore),
    jungMagician: round3(magician),
    adler: round3(adler),
    vossEmpathy: round3(vossEmpathy),
    hughesCompliance: round3(hughesCompliance),
  };

  // Prefer perceived value + problem solve + upgrade; penalize scam hard
  let psychFit = clamp01(
    0.22 * perceivedValue +
      0.14 * (1 - remorseRisk) +
      0.12 * variationPotential +
      0.12 * vossEmpathy +
      0.1 * greeneFantasy +
      0.08 * hero +
      0.08 * hughesCompliance +
      0.06 * adler +
      0.08 * fomo
  );
  if (scammy) psychFit = Math.min(psychFit, 0.15);

  const killRecommendation =
    scammy ||
    perceivedValue < 0.2 && problemSolving === 0 && upgradeReplace === 0 ||
    remorseRisk >= 0.7;

  if (perceivedValue >= 0.45) notes.push("strong perceived-value / materials / problem-solve signals");
  if (variationPotential >= 0.4) notes.push("multi-variation / repurchase potential");

  return {
    features,
    subscores,
    psychFit: round3(psychFit),
    remorseRisk: round3(remorseRisk),
    perceivedValue: round3(perceivedValue),
    variationPotential: round3(variationPotential),
    scammy,
    scamHits,
    killRecommendation,
    notes,
    caveat:
      "PsychFit/perceivedValue are provisional heuristics — not validated probabilities. Recalibrate with real conversion/returns.",
  };
}

function clamp01(x) {
  return Math.min(1, Math.max(0, x));
}
function round3(x) {
  return Math.round(x * 1000) / 1000;
}
