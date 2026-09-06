"""Evaluate forecast-derived proxy threshold events on AutoSense test origins.

Thresholds are statistical proxies fitted only on the chronological fitting
region.  They are not engineering safety limits and the events are not
component-failure labels.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RESEARCH_ROOT = Path(__file__).resolve().parents[1]
if str(RESEARCH_ROOT) not in sys.path:
    sys.path.insert(0, str(RESEARCH_ROOT))

from baseline_evaluation import DATASETS, evaluate_dataset  # noqa: E402
from protocol import prepare  # noqa: E402

OUT = RESEARCH_ROOT / "ieee_results"
PREDICTION_ROOT = OUT / "threshold_event_predictions"
MODEL_LABELS = {
    "persistence": "Persistence",
    "seasonal_naive": "Seasonal naive (previous 24 h)",
    "random_forest": "Random Forest",
    "bilstm": "Bi-LSTM",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def proxy_thresholds(dataset: str, fitting_values: np.ndarray) -> tuple[dict[str, float], str]:
    """Return the predeclared training-derived threshold rule."""
    if dataset == "tyre_pressure":
        return {"lower_5th_percentile": float(np.quantile(fitting_values, .05)),
                "upper_95th_percentile": float(np.quantile(fitting_values, .95))}, "two_sided"
    return {"upper_95th_percentile": float(np.quantile(fitting_values, .95))}, "upper_only"


def crossing(values: np.ndarray, thresholds: dict[str, float], rule: str) -> np.ndarray:
    if rule == "upper_only":
        return values >= thresholds["upper_95th_percentile"]
    return ((values <= thresholds["lower_5th_percentile"]) |
            (values >= thresholds["upper_95th_percentile"]))


def safe_ratio(numerator: int, denominator: int) -> float:
    return float(numerator / denominator) if denominator else 0.0


def event_statistics(actual_crossings: np.ndarray, predicted_crossings: np.ndarray,
                     step_hours: float) -> tuple[dict, dict]:
    """Calculate event scores and lead time for aligned forecast windows.

    A positive lead time means predicted crossing occurred earlier in the
    horizon than the earliest actual crossing; a negative value is late.
    """
    actual = actual_crossings.any(axis=1)
    predicted = predicted_crossings.any(axis=1)
    tp = int(np.sum(actual & predicted))
    fp = int(np.sum(~actual & predicted))
    tn = int(np.sum(~actual & ~predicted))
    fn = int(np.sum(actual & ~predicted))
    precision = safe_ratio(tp, tp + fp)
    recall = safe_ratio(tp, tp + fn)
    f1 = safe_ratio(2 * tp, 2 * tp + fp + fn)
    specificity = safe_ratio(tn, tn + fp)
    fpr = safe_ratio(fp, fp + tn)
    lead_hours = []
    for actual_row, predicted_row in zip(actual_crossings[actual & predicted], predicted_crossings[actual & predicted]):
        first_actual = int(np.flatnonzero(actual_row)[0])
        first_predicted = int(np.flatnonzero(predicted_row)[0])
        lead_hours.append((first_actual - first_predicted) * step_hours)
    lead = np.asarray(lead_hours, dtype=float)
    summary = {
        "Forecast origins": int(len(actual)), "Event prevalence": float(actual.mean()),
        "Precision": precision, "Recall": recall, "F1": f1, "Specificity": specificity,
        "False positive rate": fpr, "Balanced accuracy": (recall + specificity) / 2.0,
        "True-positive lead-time count": int(len(lead)),
        "Mean lead time (h)": float(lead.mean()) if len(lead) else np.nan,
        "Median lead time (h)": float(np.median(lead)) if len(lead) else np.nan,
        "Lead-time sign convention": "positive = earliest predicted crossing precedes earliest actual crossing",
        "Zero-denominator convention": "metric set to 0.0",
    }
    confusion = {"TP": tp, "FP": fp, "TN": tn, "FN": fn}
    return summary, confusion


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    threshold_manifest: dict[str, dict] = {
        "description": "Training-derived proxy maintenance/anomaly thresholds; not engineering safety thresholds.",
        "threshold_source": "only raw fitting-region target values, never validation or test values",
        "datasets": {},
    }
    metric_rows: list[dict] = []
    confusion_rows: list[dict] = []
    for dataset, cfg in DATASETS.items():
        # This fixed baseline replay creates only new ieee_results artifacts.
        # Its model specification is the corrected benchmark specification.
        evaluate_dataset(dataset, cfg, prediction_dir=PREDICTION_ROOT)
        saved_baselines = np.load(PREDICTION_ROOT / dataset / "baseline_predictions.npz")
        neural = np.load(RESEARCH_ROOT / "results" / dataset / "test_predictions.npz")
        truth = saved_baselines["truth"]
        np.testing.assert_array_equal(truth, neural["truth"])
        np.testing.assert_array_equal(saved_baselines["target_start_rows"], neural["target_start_rows"])
        _, _, masks, values, _starts, _times, meta = prepare(dataset)
        thresholds, rule = proxy_thresholds(dataset, values[:meta["Train end row exclusive"]])
        threshold_manifest["datasets"][dataset] = {
            "unit": meta["Unit"], "rule": rule, "thresholds": thresholds,
            "fitting_rows": [0, int(meta["Train end row exclusive"])],
            "data_sha256": meta["SHA256"], "test_origins": int(masks["test"].sum()),
            "horizon_steps": meta["Horizon steps"], "sampling_interval_hours": meta["Sampling interval (h)"],
        }
        predictions = {
            "persistence": saved_baselines["persistence"],
            "seasonal_naive": saved_baselines["seasonal_naive"],
            "random_forest": saved_baselines["random_forest"],
            "bilstm": neural["prediction"],
        }
        actual_crossings = crossing(truth, thresholds, rule)
        for key, prediction in predictions.items():
            predicted_crossings = crossing(prediction, thresholds, rule)
            summary, counts = event_statistics(actual_crossings, predicted_crossings, meta["Sampling interval (h)"])
            shared = {
                "Dataset": dataset, "Model": MODEL_LABELS[key], "Unit": meta["Unit"],
                "Threshold rule": rule, "Thresholds": json.dumps(thresholds, sort_keys=True),
                "Threshold label": "training-derived proxy maintenance/anomaly thresholds",
                "Truth/prediction source": ("preserved corrected Bi-LSTM artifact" if key == "bilstm"
                                            else "fixed regenerated corrected-baseline artifact"),
                "Data SHA256": meta["SHA256"],
            }
            metric_rows.append({**shared, **summary})
            confusion_rows.append({**shared, **counts, "Forecast origins": summary["Forecast origins"]})
            print(f"{dataset} | {MODEL_LABELS[key]} | F1={summary['F1']:.4f} | prevalence={summary['Event prevalence']:.4f}")
    (OUT / "threshold_event_thresholds.json").write_text(json.dumps(threshold_manifest, indent=2), encoding="utf-8")
    pd.DataFrame(metric_rows).to_csv(OUT / "threshold_event_metrics.csv", index=False)
    pd.DataFrame(confusion_rows).to_csv(OUT / "threshold_event_confusions.csv", index=False)
    print("Saved threshold-event metrics, confusion counts, and threshold provenance.")


if __name__ == "__main__":
    main()
