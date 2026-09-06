"""Moving-block bootstrap intervals for dependent AutoSense forecast origins."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RESEARCH_ROOT = Path(__file__).resolve().parents[1]
if str(RESEARCH_ROOT) not in sys.path:
    sys.path.insert(0, str(RESEARCH_ROOT))

from protocol import prepare  # noqa: E402

OUT = RESEARCH_ROOT / "ieee_results"
PRED_ROOT = OUT / "threshold_event_predictions"
BOOTSTRAP_SEED = 42
REPLICATIONS = 2000


def moving_block_indices(n_origins: int, block_length: int, rng: np.random.Generator) -> np.ndarray:
    """Sample contiguous, non-circular blocks until exactly n origins are drawn."""
    pieces = []
    while sum(len(piece) for piece in pieces) < n_origins:
        start = int(rng.integers(0, n_origins - block_length + 1))
        pieces.append(np.arange(start, start + block_length))
    return np.concatenate(pieces)[:n_origins]


def interval(loss_difference: np.ndarray, block_length: int) -> dict:
    """Bootstrap mean MAE(A)-MAE(B) over dependent forecast origins."""
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    values = np.empty(REPLICATIONS, dtype=float)
    for replication in range(REPLICATIONS):
        values[replication] = loss_difference[moving_block_indices(len(loss_difference), block_length, rng)].mean()
    observed = float(loss_difference.mean())
    lower, upper = np.quantile(values, [.025, .975])
    return {
        "Observed MAE(A)-MAE(B)": observed,
        "Bootstrap mean difference": float(values.mean()),
        "2.5th percentile": float(lower), "97.5th percentile": float(upper),
        "CI excludes zero": bool(lower > 0 or upper < 0),
    }


def predictions_for(dataset: str) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    baseline_path = PRED_ROOT / dataset / "baseline_predictions.npz"
    if not baseline_path.exists():
        raise FileNotFoundError(
            "Threshold-event baseline artifacts are required first. Run "
            "research_v2/ieee_experiments/threshold_event_evaluation.py."
        )
    baseline = np.load(baseline_path)
    neural = np.load(RESEARCH_ROOT / "results" / dataset / "test_predictions.npz")
    np.testing.assert_array_equal(baseline["truth"], neural["truth"])
    return baseline["truth"], {
        "Persistence": baseline["persistence"],
        "Seasonal naive (previous 24 h)": baseline["seasonal_naive"],
        "Random Forest": baseline["random_forest"],
        "Bi-LSTM": neural["prediction"],
    }


def main() -> None:
    output_rows = []
    # The winner rule is frozen from the pre-existing corrected benchmark:
    # lowest MAE among the three non-neural baselines, not a choice made after
    # bootstrap results.  A block spans two full forecast horizons (48 clock
    # hours) to conservatively retain overlap dependence.
    for dataset, best_baseline in {
        "engine_temperature": "Random Forest",
        "tyre_pressure": "Persistence",
        "tyre_temperature": "Random Forest",
    }.items():
        truth, predictions = predictions_for(dataset)
        _, _, masks, _values, _starts, _times, meta = prepare(dataset)
        assert len(truth) == int(masks["test"].sum())
        block_length = 2 * int(meta["Horizon steps"])
        block_clock_hours = block_length * float(meta["Sampling interval (h)"])
        comparisons = [(best_baseline, "Bi-LSTM", "predeclared lowest-MAE corrected baseline vs Bi-LSTM"),
                       ("Random Forest", "Persistence", "Random Forest vs Persistence")]
        for model_a, model_b, comparison in comparisons:
            per_origin = np.abs(truth - predictions[model_a]).mean(axis=1) - np.abs(truth - predictions[model_b]).mean(axis=1)
            result = interval(per_origin, block_length)
            output_rows.append({
                "Dataset": dataset, "Comparison": comparison, "Model A": model_a, "Model B": model_b,
                "Statistic": "pooled MAE(model A) - pooled MAE(model B)",
                "Sign convention": "negative favors model A; positive favors model B",
                "Bootstrap type": "moving-block bootstrap over forecast origins (non-circular contiguous blocks)",
                "Bootstrap replications": REPLICATIONS, "Bootstrap seed": BOOTSTRAP_SEED,
                "Block length (forecast origins)": block_length, "Block length (clock hours)": block_clock_hours,
                "Forecast origins": len(per_origin), "Horizon steps": meta["Horizon steps"],
                "Sampling interval (h)": meta["Sampling interval (h)"], "Unit": meta["Unit"],
                "Data protocol": meta["Protocol"], **result,
            })
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(output_rows).to_csv(OUT / "bootstrap_mae_differences.csv", index=False)
    print(pd.DataFrame(output_rows).to_string(index=False))


if __name__ == "__main__":
    main()
