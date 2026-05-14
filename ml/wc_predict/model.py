"""Calibrated classifier + Poisson goal model.

- Classifier (default): gradient-boosted trees (LightGBM if installed, else XGBoost,
  else sklearn HistGradientBoosting), wrapped in CalibratedClassifierCV (isotonic,
  time-series CV). Set ``WC26_CLASSIFIER=logistic`` to use the legacy multinomial
  logistic pipeline. Override with ``WC26_CLASSIFIER=lightgbm|xgboost|hist``.
- Goal model: two Poisson regressors (lambda_home, lambda_away) fit via
  Poisson GLM approximation using sklearn (PoissonRegressor).
- Combined: classifier provides win/draw/win probabilities; goal model
  provides expected goals + scoreline distribution. Both are time-aware.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import os
import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression, PoissonRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import log_loss, brier_score_loss, accuracy_score, confusion_matrix
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.inspection import permutation_importance
from sklearn.ensemble import HistGradientBoostingClassifier


CLASS_LABELS = ["home", "draw", "away"]


@dataclass
class ModelArtifacts:
    classifier: object
    poisson_home: object  # sklearn Pipeline(scaler -> PoissonRegressor)
    poisson_away: object
    feature_cols: list[str]
    metrics: dict
    trained_at: str
    version: str
    classifier_backend: str = "logistic"
    explain_features: list[tuple[str, float]] | None = None

    def save(self, path) -> None:
        joblib.dump(
            {
                "classifier": self.classifier,
                "poisson_home": self.poisson_home,
                "poisson_away": self.poisson_away,
                "feature_cols": self.feature_cols,
                "metrics": self.metrics,
                "trained_at": self.trained_at,
                "version": self.version,
                "classifier_backend": self.classifier_backend,
                "explain_features": self.explain_features,
            },
            path,
        )

    @staticmethod
    def load(path) -> "ModelArtifacts":
        d = joblib.load(path)
        d.setdefault("classifier_backend", "logistic")
        d.setdefault("explain_features", None)
        return ModelArtifacts(**d)


def time_split(df: pd.DataFrame, train_frac: float = 0.85) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.sort_values("date").reset_index(drop=True)
    cut = int(len(df) * train_frac)
    return df.iloc[:cut].copy(), df.iloc[cut:].copy()


def resolve_classifier_backend(explicit: str | None = None) -> str:
    """Pick tree backend: env ``WC26_CLASSIFIER`` or ``explicit``; ``auto`` prefers LightGBM."""
    raw = (explicit or os.environ.get("WC26_CLASSIFIER", "auto")).strip().lower()
    if raw not in ("auto", "lightgbm", "xgboost", "hist", "logistic"):
        raw = "auto"
    if raw != "auto":
        return raw
    try:
        import lightgbm  # noqa: F401

        return "lightgbm"
    except ImportError:
        pass
    try:
        import xgboost  # noqa: F401

        return "xgboost"
    except ImportError:
        pass
    return "hist"


def build_classifier(backend: str) -> object:
    """Uncalibrated multiclass estimator (``predict_proba``) for 1X2."""
    if backend == "logistic":
        return Pipeline(
            [
                ("scale", StandardScaler()),
                ("lr", LogisticRegression(max_iter=2000, C=0.6)),
            ]
        )
    if backend == "lightgbm":
        from lightgbm import LGBMClassifier

        return LGBMClassifier(
            objective="multiclass",
            num_class=3,
            n_estimators=500,
            learning_rate=0.04,
            num_leaves=47,
            max_depth=-1,
            min_child_samples=12,
            subsample=0.9,
            colsample_bytree=0.85,
            reg_alpha=0.03,
            reg_lambda=0.08,
            random_state=42,
            verbosity=-1,
            force_row_wise=True,
        )
    if backend == "xgboost":
        from xgboost import XGBClassifier

        return XGBClassifier(
            n_estimators=500,
            max_depth=7,
            learning_rate=0.04,
            subsample=0.88,
            colsample_bytree=0.88,
            reg_alpha=0.04,
            reg_lambda=0.12,
            objective="multi:softprob",
            num_class=3,
            random_state=42,
            n_jobs=-1,
            verbosity=0,
            tree_method="hist",
        )
    if backend == "hist":
        return HistGradientBoostingClassifier(
            max_depth=8,
            max_iter=450,
            learning_rate=0.055,
            l2_regularization=0.12,
            min_samples_leaf=14,
            random_state=42,
        )
    raise ValueError(f"unknown classifier backend: {backend}")


def train(
    features_df: pd.DataFrame,
    feature_cols: list[str],
    version: str,
    *,
    classifier_backend: str | None = None,
) -> ModelArtifacts:
    df = features_df.dropna(subset=feature_cols + ["target", "home_goals", "away_goals"]).copy()
    train_df, test_df = time_split(df, train_frac=0.85)

    Xtr = train_df[feature_cols].values
    ytr = train_df["target"].values
    Xte = test_df[feature_cols].values
    yte = test_df["target"].values

    backend = resolve_classifier_backend(classifier_backend)
    try:
        base = build_classifier(backend)
    except ImportError:
        if backend in ("lightgbm", "xgboost"):
            base = build_classifier("hist")
            backend = "hist"
        else:
            raise

    sw = compute_sample_weight("balanced", ytr)
    tscv = TimeSeriesSplit(n_splits=4)
    cal = CalibratedClassifierCV(base, method="isotonic", cv=tscv)
    cal.fit(Xtr, ytr, sample_weight=sw)

    explain_features: list[tuple[str, float]] | None = None
    try:
        n_sub = min(1000, len(Xtr))
        rng = np.random.RandomState(42)
        sub = rng.choice(len(Xtr), size=n_sub, replace=False)
        pi = permutation_importance(
            cal,
            Xtr[sub],
            ytr[sub],
            n_repeats=2,
            random_state=0,
            n_jobs=1,
        )
        explain_features = sorted(
            zip(feature_cols, pi.importances_mean),
            key=lambda t: -abs(t[1]),
        )[:5]
        explain_features = [(str(a), float(b)) for a, b in explain_features]
    except Exception:
        explain_features = None

    # Probabilistic metrics on holdout
    proba_te = cal.predict_proba(Xte)
    pred_te = np.argmax(proba_te, axis=1)
    one_hot = np.eye(3)[yte]
    brier = float(np.mean(np.sum((proba_te - one_hot) ** 2, axis=1)))
    ll = float(log_loss(yte, proba_te, labels=[0, 1, 2]))
    acc = float(accuracy_score(yte, pred_te))
    cm = confusion_matrix(yte, pred_te, labels=[0, 1, 2]).tolist()
    # Ranked probability score (Epstein)
    cdf_p = np.cumsum(proba_te, axis=1)[:, :2]
    cdf_y = np.cumsum(one_hot, axis=1)[:, :2]
    rps = float(np.mean(np.sum((cdf_p - cdf_y) ** 2, axis=1)))

    # Calibration curve (bin by max-probability)
    bins = np.linspace(0, 1, 11)
    binned = []
    max_proba = proba_te.max(axis=1)
    correct = (pred_te == yte).astype(int)
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (max_proba >= lo) & (max_proba < hi)
        if mask.sum() > 0:
            binned.append({
                "bin_lo": float(lo),
                "bin_hi": float(hi),
                "n": int(mask.sum()),
                "avg_conf": float(max_proba[mask].mean()),
                "acc": float(correct[mask].mean()),
            })

    # Baseline: home-favoured prior (frequency baseline)
    counts = np.bincount(ytr, minlength=3) / len(ytr)
    base_proba = np.tile(counts, (len(yte), 1))
    base_ll = float(log_loss(yte, base_proba, labels=[0, 1, 2]))
    base_brier = float(np.mean(np.sum((base_proba - one_hot) ** 2, axis=1)))

    # Poisson goal models — predict home_goals from home-perspective features,
    # away_goals from same features. Scaling is essential here: features mix
    # Elo (~1500-2000) with binary flags, so an unscaled L2 penalty would
    # zero every coefficient and collapse the model to the intercept.
    poisson_home = Pipeline([
        ("scale", StandardScaler()),
        ("pr", PoissonRegressor(alpha=0.05, max_iter=4000)),
    ]).fit(Xtr, train_df["home_goals"].values)
    poisson_away = Pipeline([
        ("scale", StandardScaler()),
        ("pr", PoissonRegressor(alpha=0.05, max_iter=4000)),
    ]).fit(Xtr, train_df["away_goals"].values)
    pred_h = poisson_home.predict(Xte)
    pred_a = poisson_away.predict(Xte)
    mae_h = float(np.mean(np.abs(pred_h - test_df["home_goals"].values)))
    mae_a = float(np.mean(np.abs(pred_a - test_df["away_goals"].values)))

    metrics = {
        "n_train": int(len(train_df)),
        "n_test": int(len(test_df)),
        "log_loss": ll,
        "brier_score": brier,
        "accuracy": acc,
        "rps": rps,
        "confusion_matrix": cm,
        "calibration_bins": binned,
        "baseline_log_loss": base_ll,
        "baseline_brier": base_brier,
        "goal_mae_home": mae_h,
        "goal_mae_away": mae_a,
        "feature_cols": feature_cols,
        "class_labels": CLASS_LABELS,
        "classifier_backend": backend,
    }
    return ModelArtifacts(
        classifier=cal,
        poisson_home=poisson_home,
        poisson_away=poisson_away,
        feature_cols=feature_cols,
        metrics=metrics,
        trained_at=datetime.utcnow().isoformat() + "Z",
        version=version,
        classifier_backend=backend,
        explain_features=explain_features,
    )


def predict_match(art: ModelArtifacts, feature_row: dict) -> dict:
    """Return calibrated probabilities + xG + likely scorelines for one fixture."""
    import math
    X = np.array([[feature_row[c] for c in art.feature_cols]], dtype=float)
    proba = art.classifier.predict_proba(X)[0]  # [home, draw, away]
    lam_h = float(max(0.05, art.poisson_home.predict(X)[0]))
    lam_a = float(max(0.05, art.poisson_away.predict(X)[0]))

    # Scoreline distribution via independent Poisson up to 6-6 (good enough for display)
    max_g = 6
    score_probs: list[tuple[int, int, float]] = []
    for h in range(max_g + 1):
        for a in range(max_g + 1):
            p = (math.exp(-lam_h) * lam_h ** h / math.factorial(h)) * (
                math.exp(-lam_a) * lam_a ** a / math.factorial(a)
            )
            score_probs.append((h, a, float(p)))
    score_probs.sort(key=lambda x: -x[2])

    # Order scorelines so the headline agrees with the classifier's favoured
    # outcome (home / draw / away). The Poisson head is fit separately, so its
    # global mode can be 1-1 even when the calibrated outcome is an away win;
    # surfacing that mode next to a 55% away bar is confusing UX.
    outcome_idx = int(np.argmax(proba))

    def _outcome_matches(h: int, a: int) -> bool:
        if h > a:
            return outcome_idx == 0
        if h < a:
            return outcome_idx == 2
        return outcome_idx == 1

    spread = float(np.max(proba) - np.min(proba))
    # When 1X2 is a three-way photo finish, the joint Poisson mode (often 1-1) is a
    # better headline than forcing a thin one-goal win that always zeros the loser.
    if spread < 0.15:
        headline = score_probs[0]
    else:
        aligned = [t for t in score_probs if _outcome_matches(t[0], t[1])]
        if not aligned:
            headline = score_probs[0]
        else:
            # Among outcome-aligned cells near the peak mass, stay close to (λ_h, λ_a),
            # then prefer both teams scoring when probability and distance tie (2-1
            # over 2-0) so cards are less dominated by "favourite wins to nil".
            best_p = max(t[2] for t in aligned)
            thr = max(best_p * 0.82, best_p - 0.04)
            candidates = [t for t in aligned if t[2] >= thr]
            headline = min(
                candidates,
                key=lambda t: (
                    abs(t[0] - lam_h) + abs(t[1] - lam_a),
                    -t[2],
                    -min(t[0], t[1]),
                ),
            )

    seen: set[tuple[int, int]] = set()
    ordered: list[tuple[int, int, float]] = []
    for t in (headline, *score_probs):
        key = (t[0], t[1])
        if key in seen:
            continue
        seen.add(key)
        ordered.append(t)
        if len(ordered) >= 5:
            break
    top_scores = ordered

    # Confidence: 1 - normalized entropy
    eps = 1e-9
    H = -sum(p * math.log(p + eps) for p in proba) / math.log(3)
    confidence = float(1 - H)

    # Feature explanations: permutation importance (trees) or logistic coef path.
    top_features: list[tuple[str, float]] = []
    if art.explain_features:
        top_features = list(art.explain_features)[:5]
    else:
        try:
            base_pipeline = art.classifier.calibrated_classifiers_[0].estimator
            scaler = base_pipeline.named_steps["scale"]
            lr = base_pipeline.named_steps["lr"]
            std = np.sqrt(scaler.var_)
            std[std == 0] = 1.0
            xs = (X - scaler.mean_) / std
            cls = int(np.argmax(proba))
            coefs = lr.coef_[cls]
            contribs = (xs[0] * coefs).tolist()
            items = sorted(
                zip(art.feature_cols, contribs), key=lambda t: -abs(t[1])
            )[:5]
            top_features = [(name, float(val)) for name, val in items]
        except Exception:
            top_features = []

    return {
        "p_home": float(proba[0]),
        "p_draw": float(proba[1]),
        "p_away": float(proba[2]),
        "xg_home": lam_h,
        "xg_away": lam_a,
        "likely_scores": top_scores,
        "confidence": confidence,
        "top_features": top_features,
    }
