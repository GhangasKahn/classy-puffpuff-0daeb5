/** Ranking Agent — composite score under uncertainty */
import { rankCandidates, scoreCandidate } from "../core/scoring.js";

export function rank(candidates, opts) {
  return rankCandidates(candidates, opts);
}

export function scoreOne(candidate, opts) {
  return scoreCandidate(candidate, opts);
}
