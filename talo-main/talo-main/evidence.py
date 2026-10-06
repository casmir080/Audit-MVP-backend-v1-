"""
Deterministic evidence rules. The LLM explains these results; it never
decides them. This exists because the first real test of this product
proved the failure mode directly: with 2 of 20 rows carrying a confirmed
outcome, the model produced something that read like a performance
assessment instead of stating plainly that there wasn't enough evidence.

Tune MIN_ROWS_FOR_PERFORMANCE once real risk/compliance conversations
tell you what threshold they'd actually trust - this number is a
placeholder, not a researched constant.
"""

MIN_ROWS_FOR_PERFORMANCE = 30


def outcome_coverage(rows: list[dict]) -> dict:
    total = len(rows)
    labeled = [r for r in rows if r.get("outcome")]
    return {
        "total_rows": total,
        "labeled_rows": len(labeled),
        "coverage_pct": round(len(labeled) / total * 100, 1) if total else 0.0,
    }


def evidence_confidence(coverage: dict) -> str:
    """insufficient / limited / moderate / high - a hard rule, not a guess."""
    n = coverage["labeled_rows"]
    if n < MIN_ROWS_FOR_PERFORMANCE:
        return "insufficient"
    elif n < MIN_ROWS_FOR_PERFORMANCE * 3:
        return "limited"
    elif n < MIN_ROWS_FOR_PERFORMANCE * 10:
        return "moderate"
    return "high"


def performance_metrics(rows: list[dict]) -> dict:
    """
    Only computes precision/recall/F1 when there's enough labeled data to
    mean anything. Returns explicit nulls and a status otherwise - never a
    fabricated number standing in for "we don't actually know."
    """
    coverage = outcome_coverage(rows)
    confidence = evidence_confidence(coverage)

    if confidence == "insufficient":
        return {
            "status": confidence,
            "coverage": coverage,
            "precision": None,
            "recall": None,
            "f1": None,
        }

    labeled = [r for r in rows if r.get("outcome")]
    tp = sum(1 for r in labeled if r.get("decision") == "flagged" and r.get("outcome") == "confirmed_fraud")
    fp = sum(1 for r in labeled if r.get("decision") == "flagged" and r.get("outcome") == "false_positive")
    fn = sum(1 for r in labeled if r.get("decision") == "cleared" and r.get("outcome") == "confirmed_fraud")

    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    f1 = (2 * precision * recall / (precision + recall)) if precision and recall else None

    return {
        "status": confidence,
        "coverage": coverage,
        "precision": round(precision, 3) if precision is not None else None,
        "recall": round(recall, 3) if recall is not None else None,
        "f1": round(f1, 3) if f1 is not None else None,
    }


def model_health(drift_status: str, evidence_status: str) -> str:
    """
    One deterministic traffic-light for the person who just wants to know
    if they need to worry, before they read a single paragraph.
    stable / attention / high_risk
    """
    if drift_status == "significant_shift":
        return "high_risk" if evidence_status in ("insufficient", "limited") else "attention"
    if drift_status == "moderate_shift":
        return "attention"
    return "stable"
