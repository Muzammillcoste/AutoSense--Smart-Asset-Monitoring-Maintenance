"""Verify a local research inference wrapper against fixed offline predictions."""
from __future__ import annotations

import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RESEARCH_ROOT = Path(__file__).resolve().parents[1]
if str(RESEARCH_ROOT) not in sys.path:
    sys.path.insert(0, str(RESEARCH_ROOT))

from baseline_evaluation import DATASETS, evaluate_dataset  # noqa: E402
from protocol import prepare  # noqa: E402
from research_inference import MODEL_SELECTION, ResearchForecastService  # noqa: E402

OUT = RESEARCH_ROOT / "ieee_results"
OFFLINE = OUT / "api_offline_predictions"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # Recreate fixed-baseline predictions outside the preserved results tree.
    for dataset, cfg in DATASETS.items():
        evaluate_dataset(dataset, cfg, prediction_dir=OFFLINE)
    service = ResearchForecastService()
    checks = []
    heldout_inputs: list[tuple[str, np.ndarray]] = []
    for dataset, selected in MODEL_SELECTION.items():
        X, _y, masks, _values, _starts, _times, meta = prepare(dataset)
        saved = np.load(OFFLINE / dataset / "baseline_predictions.npz")
        key = "random_forest" if selected == "Random Forest" else "persistence"
        expected = saved[key]
        inputs = X[masks["test"]]
        produced = np.asarray([service.predict(dataset, window) for window in inputs])
        np.testing.assert_allclose(produced, expected, rtol=1e-12, atol=1e-12)
        checks.append({"Dataset": dataset, "Selected model": selected, "Wrapper version": service.version,
                       "Held-out windows": int(len(inputs)), "Tolerance rtol": 1e-12, "Tolerance atol": 1e-12,
                       "Maximum absolute difference": float(np.max(np.abs(produced - expected))), "Consistent": True,
                       "Unit": meta["Unit"]})
        heldout_inputs.extend((dataset, window) for window in inputs[:80])
    # Warm-up is excluded.  The timed calls use exactly the public wrapper path.
    for dataset, window in heldout_inputs[:20]:
        service.predict(dataset, window)
    rows = []
    for request in range(200):
        dataset, window = heldout_inputs[request % len(heldout_inputs)]
        started = time.perf_counter_ns(); service.predict(dataset, window); elapsed = time.perf_counter_ns() - started
        rows.append({"Request": request + 1, "Dataset": dataset, "Model": MODEL_SELECTION[dataset], "Latency ms": elapsed / 1e6})
    latency = pd.DataFrame(rows)
    latency.to_csv(OUT / "api_latency.csv", index=False)
    values = latency["Latency ms"].to_numpy()
    summary = {"Wrapper version": service.version, "Environment": "local-only; no network, cloud, or production latency claimed",
               "Requests after warm-up": len(values), "Median latency ms": float(np.median(values)),
               "p90 latency ms": float(np.quantile(values, .90)), "p95 latency ms": float(np.quantile(values, .95)),
               "p99 latency ms": float(np.quantile(values, .99)), "Minimum latency ms": float(values.min()),
               "Maximum latency ms": float(values.max()), "Python": sys.version, "Platform": platform.platform(),
               "CPU/device": platform.processor() or "CPU (platform identifier unavailable)"}
    (OUT / "api_consistency.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
    (OUT / "api_latency_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"consistency": checks, "latency": summary}, indent=2))


if __name__ == "__main__":
    main()
