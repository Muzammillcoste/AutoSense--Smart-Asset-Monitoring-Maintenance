"""Versioned local research inference wrapper for the corrected AutoSense mapping."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestRegressor

RESEARCH_ROOT = Path(__file__).resolve().parents[1]
if str(RESEARCH_ROOT) not in sys.path:
    sys.path.insert(0, str(RESEARCH_ROOT))

from protocol import prepare  # noqa: E402

MODEL_SELECTION = {
    "engine_temperature": "Random Forest",
    "tyre_pressure": "Persistence",
    "tyre_temperature": "Random Forest",
}


class ResearchForecastService:
    """Local-only wrapper; initialization fits the frozen corrected RF models."""
    version = "autosense-research-wrapper-v1"

    def __init__(self) -> None:
        self._forests: dict[str, RandomForestRegressor] = {}
        self._lookbacks: dict[str, int] = {}
        self._horizons: dict[str, int] = {}
        for dataset, selection in MODEL_SELECTION.items():
            X, y, masks, _values, _starts, _times, meta = prepare(dataset)
            self._lookbacks[dataset] = int(meta["Lookback steps"])
            self._horizons[dataset] = int(meta["Horizon steps"])
            if selection == "Random Forest":
                forest = RandomForestRegressor(n_estimators=300, max_depth=16, min_samples_leaf=2,
                                               random_state=42, n_jobs=-1)
                forest.fit(X[masks["train"]], y[masks["train"]])
                self._forests[dataset] = forest

    def predict(self, dataset: str, history: np.ndarray) -> np.ndarray:
        """Forecast one observed target-history window in physical units."""
        if dataset not in MODEL_SELECTION:
            raise KeyError(f"Unknown research target: {dataset}")
        values = np.asarray(history, dtype=float).reshape(-1)
        if values.shape != (self._lookbacks[dataset],) or not np.isfinite(values).all():
            raise ValueError(f"{dataset} requires {self._lookbacks[dataset]} finite historical target values")
        if MODEL_SELECTION[dataset] == "Persistence":
            return np.repeat(values[-1], self._horizons[dataset])
        return self._forests[dataset].predict(values[None, :])[0]
