export type LikelyScore = {
  home_goals: number;
  away_goals: number;
  prob: number;
};

export type FeatureContribution = {
  name: string;
  contribution: number;
};

export type Prediction = {
  match_id: string;
  date: string;
  kickoff?: string | null;
  stage: "group" | "r32" | "r16" | "qf" | "sf" | "third" | "final";
  group?: string | null;
  venue?: string | null;
  home: string;
  away: string;
  p_home: number;
  p_draw: number;
  p_away: number;
  xg_home: number;
  xg_away: number;
  likely_scores: LikelyScore[];
  confidence: number;
  top_features: FeatureContribution[];
  model_version: string;
  generated_at: string;
};

export type PredictionsBundle = {
  items: Prediction[];
  generated_at: string;
  model_version: string;
};

export type Team = {
  code: string;
  name: string;
  confederation: string;
  pot: number;
  is_host: number | boolean;
  elo_seed: number;
};

export type Fixture = {
  match_id: string;
  date: string;
  kickoff?: string | null;
  stage: string;
  group?: string | null;
  venue?: string | null;
  home: string;
  away: string;
  neutral?: boolean | number;
};

export type RoundProb = {
  group_play: number;
  r32: number;
  r16: number;
  qf: number;
  sf: number;
  final: number;
  winner: number;
};

export type SimulationBundle = {
  n_sims: number;
  seed: number;
  round_probs: Record<string, RoundProb>;
  group_finish: Record<string, Record<string, Record<string, number>>>;
  generated_at: string;
};

export type ModelInfo = {
  version: string;
  trained_at: string;
  feature_cols: string[];
  classifier_backend?: string;
  n_train: number;
  n_test: number;
  metrics: {
    log_loss: number;
    brier_score: number;
    accuracy: number;
    rps: number;
    baseline_log_loss: number;
    baseline_brier: number;
    goal_mae_home: number;
    goal_mae_away: number;
  };
  git_commit?: string;
};

export type DataStatus = {
  results_source: "REAL" | "SAMPLE" | string;
  fixtures_source: "REAL" | "SAMPLE" | string;
  is_sample: boolean;
  note: string;
  generated_at: string;
};

export type Metrics = ModelInfo["metrics"] & {
  n_train: number;
  n_test: number;
  confusion_matrix: number[][];
  calibration_bins: Array<{
    bin_lo: number;
    bin_hi: number;
    n: number;
    avg_conf: number;
    acc: number;
  }>;
  class_labels: string[];
  feature_cols: string[];
  classifier_backend?: string;
};
