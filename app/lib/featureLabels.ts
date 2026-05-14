/** User-friendly labels + interpretation for the technical feature names. */
export const FEATURE_LABEL: Record<string, { label: string; positive: string; negative: string }> = {
  elo_diff: {
    label: "Ranking edge",
    positive: "ranking favours the home side",
    negative: "ranking favours the away side",
  },
  elo_home: { label: "Home rating", positive: "home rating is high", negative: "home rating is lower" },
  elo_away: { label: "Away rating", positive: "away rating is low", negative: "away rating is high" },
  form5_diff: {
    label: "Recent form (last 5)",
    positive: "home in better recent form",
    negative: "away in better recent form",
  },
  form10_diff: {
    label: "Recent form (last 10)",
    positive: "home in better extended form",
    negative: "away in better extended form",
  },
  gf5_home: { label: "Home scoring rate", positive: "home scoring lots recently", negative: "home struggling to score" },
  gf5_away: { label: "Away scoring rate", positive: "away scoring lots recently", negative: "away struggling to score" },
  ga5_home: { label: "Home defence", positive: "home conceding too much", negative: "home defence solid" },
  ga5_away: { label: "Away defence", positive: "away leaking goals", negative: "away defence solid" },
  attack_home: { label: "Home attack strength", positive: "home attack productive", negative: "home attack quiet" },
  attack_away: { label: "Away attack strength", positive: "away attack productive", negative: "away attack quiet" },
  defense_home: { label: "Home defensive record", positive: "home leakier than usual", negative: "home defensively tight" },
  defense_away: { label: "Away defensive record", positive: "away leakier than usual", negative: "away defensively tight" },
  rest_diff: { label: "Rest days advantage", positive: "home better rested", negative: "away better rested" },
  host_home: { label: "Home is a host nation", positive: "playing on home soil", negative: "not a host" },
  host_away: { label: "Away is a host nation", positive: "away is a host nation", negative: "away is not a host" },
  same_confederation: { label: "Familiar opponent", positive: "regional opponents — familiar matchup", negative: "different confederations" },
  neutral: { label: "Neutral venue", positive: "neutral pitch", negative: "not neutral" },
};

export function describeFeature(name: string, contribution: number): { label: string; explanation: string } {
  const meta = FEATURE_LABEL[name];
  if (!meta) {
    return { label: name, explanation: contribution >= 0 ? "supports the model's pick" : "argues against the model's pick" };
  }
  return {
    label: meta.label,
    explanation: contribution >= 0 ? meta.positive : meta.negative,
  };
}
