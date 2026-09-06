"""Stratify FD001 held-out sensor-forecast error by observed degradation stage.

RUL is not predicted here.  Complete train_FD001 trajectories make each held
out engine's terminal cycle observable, so normalized cycle position can be
used only to group already-produced forecasting errors.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ieee_results"
PREDICTIONS = OUT / "cmapss_fd001_predictions"


def stage(fraction: float) -> str:
    if fraction < .5:
        return "early (<0.5 normalized cycle fraction)"
    if fraction < .8:
        return "mid (0.5 to <0.8 normalized cycle fraction)"
    return "late (>=0.8 normalized cycle fraction)"


def main() -> None:
    split = json.loads((OUT / "cmapss_fd001_split.json").read_text(encoding="utf-8"))
    test_ids = set(split["test_engine_ids"])
    raw = pd.read_csv(ROOT / "external_data" / "cmapss" / "train_FD001.txt", sep=r"\s+", header=None, usecols=[0, 1], names=["unit", "cycle"], engine="python")
    max_cycle = raw.groupby("unit")["cycle"].max().to_dict()
    rows = []
    files = sorted(PREDICTIONS.glob("*.npz"))
    if not files:
        raise FileNotFoundError("No C-MAPSS predictions found; run cmapss_fd001_forecasting.py first.")
    for path in files:
        saved = np.load(path, allow_pickle=False)
        units, origins = saved["unit_ids"].astype(int), saved["target_start_cycles"].astype(int)
        if not set(units).issubset(test_ids):
            raise ValueError(f"Prediction file contains a non-test engine: {path}")
        labels = np.asarray([stage(origin / max_cycle[unit]) for unit, origin in zip(units, origins)])
        errors = np.abs(saved["truth"] - saved["prediction"]).mean(axis=1)
        for label in ("early (<0.5 normalized cycle fraction)", "mid (0.5 to <0.8 normalized cycle fraction)", "late (>=0.8 normalized cycle fraction)"):
            selected = errors[labels == label]
            rows.append({"Dataset": "NASA C-MAPSS FD001 (simulated)", "Configuration": str(saved["configuration"].item()),
                         "Target sensor": str(saved["target_sensor"].item()), "Model": str(saved["model"].item()),
                         "Seed": int(saved["seed"].item()), "Stage": label, "Forecast origins": len(selected),
                         "MAE": float(selected.mean()) if len(selected) else np.nan,
                         "Stage definition": "target-start cycle / terminal cycle of held-out run-to-failure train_FD001 engine",
                         "RUL use": "analysis stratification only; not a prediction target"})
    pd.DataFrame(rows).to_csv(OUT / "cmapss_stage_metrics.csv", index=False)
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
