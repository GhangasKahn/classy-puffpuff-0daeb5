/**
 * Extract Pavlovian targets from a Hermes SOUL.md.
 * Oracle maps residuals onto these named associations — never invents a personality.
 *
 * Do not import named `packDir` here. Netlify NFT tree-shakes barrel re-exports
 * from playground/index.js and then Watch/API crash with:
 * "does not provide an export named 'packDir'".
 */
import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const AGENTS_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../../lpros-agents");

const BULLET = /^\s*[-*]\s+(.+?)(?:\s*→\s*(.+))?$/;

function bullets(block) {
  const rows = [];
  for (const line of String(block || "").split("\n")) {
    const m = line.match(BULLET);
    if (!m) continue;
    rows.push({
      text: m[1].replace(/\*\*/g, "").trim(),
      cue: (m[2] || "").replace(/\*\*/g, "").trim() || null,
    });
  }
  return rows;
}

export function parsePavlovFromSoul(soul) {
  const text = String(soul || "");
  const reinforceChunk = text.split(/\*\*(?:Extinguish|Punish)\b/i)[0] || text;
  const punishChunk = (text.split(/\*\*(?:Extinguish|Punish)\b[^*]*\*\*/i)[1] || "").split(/\*\*[A-Z]/)[0];
  return {
    reinforce: bullets(reinforceChunk).slice(0, 16),
    punish: bullets(punishChunk).slice(0, 16),
  };
}

export function readSoulPavlov(packId) {
  const p = resolve(AGENTS_ROOT, packId, "SOUL.md");
  if (!existsSync(p)) return { reinforce: [], punish: [] };
  return parsePavlovFromSoul(readFileSync(p, "utf8"));
}

export function matchTarget(pavlov, { association = "reinforce", needle } = {}) {
  const list = association === "punish" ? pavlov.punish : pavlov.reinforce;
  const n = String(needle || "").toLowerCase();
  const hit =
    list.find((t) => t.text.toLowerCase().includes(n)) ||
    list.find((t) => n.split(/\s+/).some((w) => w.length > 4 && t.text.toLowerCase().includes(w)));
  return hit?.text || list[0]?.text || String(needle || "named SOUL target");
}
