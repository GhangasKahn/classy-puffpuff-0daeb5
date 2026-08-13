/**
 * Listing Draft Agent — title / bullets / item specifics from a lethal candidate.
 * Deterministic template (no LLM required). Optional Ollama hook later.
 */
import { psychProxies } from "../core/psychology.js";

export function draftListing(candidate = {}, opts = {}) {
  const titleRaw = String(candidate.title || candidate.ref || "Product").trim();
  const brand = opts.brand || detectBrand(titleRaw) || "Unbranded";
  const material = detectMaterial(titleRaw);
  const problem = detectProblem(titleRaw);
  const salePrice = Number(candidate.salePrice ?? candidate.price) || null;
  const psych = psychProxies({
    title: titleRaw,
    salePrice,
    categoryMedianPrice: candidate.categoryMedianPrice || salePrice,
  });

  const title = buildTitle({ titleRaw, brand, material, maxLen: opts.maxTitleLen || 80 });
  const bullets = [
    problem
      ? `Solves: ${problem} — built for daily desk / workspace use`
      : "Built for daily desk organization — fewer piles, faster reach",
    material
      ? `Material: ${material} — higher perceived quality vs thin plastic trays`
      : "Solid construction over disposable plastic organizers",
    "Dimensions and slot count listed in Item Specifics — measure your desk before buy",
    "Ships carefully packed; inspect on arrival and message within 24h if damaged",
    psych.features?.upgradeReplace
      ? "Upgrade path: replace cluttered multi-gadget piles with one coherent station"
      : "Clean look that fits home office and studio setups",
  ];

  const specifics = {
    Brand: brand,
    Type: opts.type || "Desk Organizer",
    Material: material || "Wood",
    Color: detectColor(titleRaw) || "See photos",
    "Number of Compartments": detectSlots(titleRaw) || "See description",
    Condition: candidate.condition || "New",
  };

  const descriptionHtml = [
    `<h2>${escape(title)}</h2>`,
    `<p>${escape(bullets[0])}</p>`,
    "<ul>",
    ...bullets.slice(1).map((b) => `<li>${escape(b)}</li>`),
    "</ul>",
    salePrice != null
      ? `<p><strong>Competitive anchor:</strong> research band around $${salePrice.toFixed(2)} (verify with sold comps before publish).</p>`
      : "",
    "<p>Wholesale fulfillment only — not retail arbitrage.</p>",
  ]
    .filter(Boolean)
    .join("\n");

  return {
    title,
    bullets,
    itemSpecifics: specifics,
    descriptionHtml,
    psychFit: psych.psychFit,
    perceivedValue: psych.perceivedValue,
    scammy: psych.scammy,
    warnings: [
      ...(psych.scammy ? ["Source title looked scammy — rewrite before publish"] : []),
      "Confirm EPID/GTIN and category leaf before publish",
      "Do not copy competitor photos; use supplier + your own",
    ],
    sourceTitle: titleRaw,
    sourceUrl: candidate.url || null,
  };
}

function buildTitle({ titleRaw, brand, material, maxLen }) {
  let t = titleRaw
    .replace(/\s+/g, " ")
    .replace(/[|]+/g, "-")
    .trim();
  if (material && !new RegExp(material, "i").test(t)) {
    t = `${material} ${t}`;
  }
  if (brand && brand !== "Unbranded" && !new RegExp(brand, "i").test(t)) {
    t = `${brand} ${t}`;
  }
  if (t.length > maxLen) t = t.slice(0, maxLen - 1).trim() + "…";
  return t;
}

function detectBrand(t) {
  const m = t.match(/\b(Kirigen|SimpleHouseware|Homestyle|AmazonBasics)\b/i);
  return m ? m[1] : null;
}
function detectMaterial(t) {
  if (/\boak\b/i.test(t)) return "Oak";
  if (/\bbamboo\b/i.test(t)) return "Bamboo";
  if (/\bsolid wood\b|\bwood\b/i.test(t)) return "Wood";
  if (/\bmetal\b|\bsteel\b/i.test(t)) return "Metal";
  if (/\bleather\b/i.test(t)) return "Leather";
  return null;
}
function detectProblem(t) {
  if (/cable|cord/i.test(t)) return "cable clutter";
  if (/mail|letter|tray/i.test(t)) return "paper / mail pile-up";
  if (/drawer|organiz/i.test(t)) return "drawer / desk clutter";
  return null;
}
function detectColor(t) {
  const m = t.match(/\b(black|brown|white|gray|grey|natural|walnut|caramel)\b/i);
  return m ? m[1][0].toUpperCase() + m[1].slice(1).toLowerCase() : null;
}
function detectSlots(t) {
  const m = t.match(/\b(\d+)\s*(slot|compartment|tray|tier)/i);
  return m ? m[1] : null;
}
function escape(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
