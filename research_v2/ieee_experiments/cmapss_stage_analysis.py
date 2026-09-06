"""Stratify FD001 held-out sensor-forecast error by observed degradation stage.

RUL is not predicted here.  Complete train_FD001 trajectories make each held
out engine's terminal cycle observable, so normalized cycle position can be
used only to group already-produced forecasting errors.
"""
from __future__ import annotations

import json
import hashlib
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
import tensorflow as tf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ieee_results"
PREDICTIONS = OUT / "cmapss_fd001_predictions"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stage(fraction: float) -> str:
    if fraction < .5:
        return "early (<0.5 normalized cycle fraction)"
    if fraction < .8:
        return "mid (0.5 to <0.8 normalized cycle fraction)"
    return "late (>=0.8 normalized cycle fraction)"


def main() -> None:
    protocol_path = ROOT / "CODEX_IEEE_EXECUTION_PLAN.md"
    split_path = OUT / "cmapss_fd001_split.json"
    split = json.loads(split_path.read_text(encoding="utf-8"))
    test_ids = set(split["test_engine_ids"])
    data_path = ROOT / "external_data" / "cmapss" / "train_FD001.txt"
    raw = pd.read_csv(data_path, sep=r"\s+", header=None, usecols=[0, 1], names=["unit", "cycle"], engine="python")
    max_cycle = raw.groupby("unit")["cycle"].max().to_dict()
    rows = []
    files = sorted(PREDICTIONS.glob("*.npz"))
    if not files:
        raise FileNotFoundError("No C-MAPSS predictions found; run cmapss_fd001_forecasting.py first.")
    provenance = {
        "Stage analysis script SHA256": sha256(Path(__file__)),
        "Forecasting script SHA256 source": "prediction artifact metadata",
        "Protocol SHA256": sha256(protocol_path),
        "C-MAPSS engine split SHA256": sha256(split_path),
        "Dataset SHA256": sha256(data_path),
        "Python": sys.version.split()[0],
        "TensorFlow": tf.__version__,
        "scikit-learn": sklearn.__version__,
        "Platform": platform.platform(),
        "Devices": str([str(device) for device in tf.config.list_physical_devices()]),
    }
    for path in files:
        saved = np.load(path, allow_pickle=False)
        units, origins = saved["unit_ids"].astype(int), saved["target_start_cycles"].astype(int)
        if not set(units).issubset(test_ids):
            raise ValueError(f"Prediction file contains a non-test engine: {path}")
        labels = np.asarray([stage(origin / max_cycle[unit]) for unit, origin in zip(units, origins)])
        truth, prediction = saved["truth"], saved["prediction"]
        errors = np.abs(truth - prediction).mean(axis=1)
        for label in ("early (<0.5 normalized cycle fraction)", "mid (0.5 to <0.8 normalized cycle fraction)", "late (>=0.8 normalized cycle fraction)"):
            selected = errors[labels == label]
            selected_truth = truth[labels == label]
            selected_prediction = prediction[labels == label]
            rows.append({"Dataset": "NASA C-MAPSS FD001 (simulated)", "Configuration": str(saved["configuration"].item()),
                         "Target sensor": str(saved["target_sensor"].item()), "Model": str(saved["model"].item()),
                         "Seed": int(saved["seed"].item()), "Stage": label, "Forecast origins": len(selected),
                         "MAE": float(selected.mean()) if len(selected) else np.nan,
                         "RMSE": float(np.sqrt(np.mean((selected_truth - selected_prediction) ** 2))) if len(selected) else np.nan,
                         "R2": float(1 - np.sum((selected_truth - selected_prediction) ** 2) /
                                     np.sum((selected_truth - selected_truth.mean()) ** 2)) if len(selected) and np.sum((selected_truth - selected_truth.mean()) ** 2) else np.nan,
                         "Unit": "native sensor units",
                         "Stage definition": "target-start cycle / terminal cycle of held-out run-to-failure train_FD001 engine",
                         "RUL use": "analysis stratification only; not a prediction target",
                         "Prediction dataset SHA256": str(saved["dataset_sha256"].item()),
                         "Forecasting script SHA256": str(saved["experiment_script_sha256"].item()),
                         "Forecasting architecture source SHA256": str(saved["architecture_source_sha256"].item()),
                         "Model parameters": float(saved["model_parameters"].item()),
                         "Epochs run": float(saved["epochs_run"].item()),
                         "Best epoch": float(saved["best_epoch"].item()),
                         "Training seconds": float(saved["training_seconds"].item()),
                         **provenance})
    pd.DataFrame(rows).to_csv(OUT / "cmapss_stage_metrics.csv", index=False)
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
