import type { LikelyScore, Prediction } from "./types";

/** Matches numpy.argmax tie-break on equal probabilities (first max wins). */
function favouredOutcome(pred: Prediction): "home" | "draw" | "away" {
  const { p_home, p_draw, p_away } = pred;
  if (p_home >= p_draw && p_home >= p_away) return "home";
  if (p_draw >= p_away) return "draw";
  return "away";
}

function scorelineMatchesOutcome(s: LikelyScore, o: "home" | "draw" | "away"): boolean {
  if (s.home_goals > s.away_goals) return o === "home";
  if (s.home_goals < s.away_goals) return o === "away";
  return o === "draw";
}

/** max(p) − min(p) over home / draw / away — mirrors `predict_match` spread gate. */
function outcomeSpread(pred: Prediction): number {
  const { p_home, p_draw, p_away } = pred;
  return Math.max(p_home, p_draw, p_away) - Math.min(p_home, p_draw, p_away);
}

function pickBetterHeadline(s: LikelyScore, best: LikelyScore, xh: number, xa: number): LikelyScore {
  const ls = Math.abs(s.home_goals - xh) + Math.abs(s.away_goals - xa);
  const lb = Math.abs(best.home_goals - xh) + Math.abs(best.away_goals - xa);
  if (ls !== lb) return ls < lb ? s : best;
  if (s.prob !== best.prob) return s.prob > best.prob ? s : best;
  const ms = Math.min(s.home_goals, s.away_goals);
  const mb = Math.min(best.home_goals, best.away_goals);
  return ms > mb ? s : best;
}

function pickHeadlineFromLikelyList(pred: Prediction, raw: LikelyScore[]): LikelyScore {
  if (raw.length === 0) return raw[0]!;
  // Tight 1X2: use modal score among rows we have (matches pipeline when regenerated).
  if (outcomeSpread(pred) < 0.15) {
    return raw[0]!;
  }
  const o = favouredOutcome(pred);
  const xh = pred.xg_home;
  const xa = pred.xg_away;
  const top = raw[0];
  if (top && scorelineMatchesOutcome(top, o)) {
    return top;
  }
  const aligned = raw.filter((s) => scorelineMatchesOutcome(s, o));
  if (aligned.length === 0) return top ?? raw[0]!;
  const bestP = Math.max(...aligned.map((s) => s.prob));
  const thr = Math.max(bestP * 0.82, bestP - 0.04);
  const candidates = aligned.filter((s) => s.prob >= thr);
  const pool = candidates.length ? candidates : aligned;
  return pool.reduce((best, s) => pickBetterHeadline(s, best, xh, xa), pool[0]!);
}

/**
 * Reorders likely scorelines so the first row matches the 1X2 favourite, mirroring
 * `predict_match` in the Python bundle. Keeps cards and detail pages consistent
 * with the win/draw/win bar even when the Poisson mode disagrees.
 */
export function orderedLikelyScores(pred: Prediction): LikelyScore[] {
  const raw = pred.likely_scores;
  if (raw.length === 0) return raw;
  const headline = pickHeadlineFromLikelyList(pred, raw);
  const seen = new Set<string>();
  const out: LikelyScore[] = [];
  for (const s of [headline, ...raw]) {
    const key = `${s.home_goals}-${s.away_goals}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(s);
    if (out.length >= 5) break;
  }
  return out;
}

export function headlineScoreline(pred: Prediction): LikelyScore | undefined {
  return orderedLikelyScores(pred)[0];
}
