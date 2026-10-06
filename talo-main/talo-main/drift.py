"""
Population Stability Index (PSI) drift detection.

Compares a "current" batch of transactions against a "baseline" batch to
flag when the underlying data has shifted enough that a model trained on
the baseline can no longer be trusted on the current data.

PSI thresholds (industry-standard rule of thumb):
    < 0.1   : no significant shift
    0.1-0.25: moderate shift, worth watching
    > 0.25  : significant shift, model may need retraining/review
"""
from collections import Counter
import math


def _bucket_feature(values: list[float], n_buckets: int = 10) -> list[float]:
    """Split a numeric feature into n_buckets equal-width bins and return the fraction of values in each bin."""
    if not values:
        return [0.0] * n_buckets
    lo, hi = min(values), max(values)
    if lo == hi:
        result = [0.0] * n_buckets
        result[0] = 1.0
        return result
    width = (hi - lo) / n_buckets
    counts = [0] * n_buckets
    for v in values:
        idx = min(int((v - lo) / width), n_buckets - 1)
        counts[idx] += 1
    total = len(values)
    return [c / total for c in counts]


def psi(baseline: list[float], current: list[float], n_buckets: int = 10) -> float:
    """Compute the Population Stability Index between two numeric distributions."""
    baseline_pct = _bucket_feature(baseline, n_buckets)
    current_pct = _bucket_feature(current, n_buckets)
    score = 0.0
    for b, c in zip(baseline_pct, current_pct):
        b = max(b, 1e-6)
        c = max(c, 1e-6)
        score += (c - b) * math.log(c / b)
    return score


def categorical_psi(baseline: list[str], current: list[str]) -> float:
    """PSI variant for categorical features (e.g. decision type, region)."""
    baseline_counts = Counter(baseline)
    current_counts = Counter(current)
    categories = set(baseline_counts) | set(current_counts)
    b_total, c_total = len(baseline) or 1, len(current) or 1
    score = 0.0
    for cat in categories:
        b = max(baseline_counts.get(cat, 0) / b_total, 1e-6)
        c = max(current_counts.get(cat, 0) / c_total, 1e-6)
        score += (c - b) * math.log(c / b)
    return score


def interpret_psi(score: float) -> str:
    if score < 0.1:
        return "stable"
    elif score < 0.25:
        return "moderate_shift"
    return "significant_shift"


def _try_numeric(values: list) -> list[float] | None:
    try:
        return [float(v) for v in values]
    except (TypeError, ValueError):
        return None


def drift_report(baseline_rows: list[dict], current_rows: list[dict]) -> dict:
    """
    Run PSI across every feature present in the normalized rows (output of
    ingest.py) and return a per-feature drift summary.
    """
    if not baseline_rows or not current_rows:
        return {"error": "need both a baseline and a current period with data"}

    all_feature_keys = set()
    for row in baseline_rows + current_rows:
        all_feature_keys.update(row.get("features", {}).keys())

    results = {}
    for key in all_feature_keys:
        baseline_vals = [r["features"].get(key) for r in baseline_rows if key in r.get("features", {})]
        current_vals = [r["features"].get(key) for r in current_rows if key in r.get("features", {})]

        numeric_baseline = _try_numeric(baseline_vals)
        numeric_current = _try_numeric(current_vals)

        if numeric_baseline is not None and numeric_current is not None:
            score = psi(numeric_baseline, numeric_current)
        else:
            score = categorical_psi([str(v) for v in baseline_vals], [str(v) for v in current_vals])

        results[key] = {"psi": round(score, 4), "status": interpret_psi(score)}

    overall = sum(r["psi"] for r in results.values()) / max(len(results), 1)
    return {
        "per_feature": results,
        "overall_psi": round(overall, 4),
        "overall_status": interpret_psi(overall),
    }
