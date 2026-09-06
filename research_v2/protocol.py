"""Shared chronological forecasting protocol; boundaries refer to raw rows."""
import hashlib
import numpy as np
import pandas as pd
from baseline_evaluation import DATASETS, infer_step_hours, steps_for_hours, make_supervised

PROTOCOL = "raw80_train68_validation12_test20_v1"

def prepare(name):
    cfg = DATASETS[name]
    df = pd.read_csv(cfg["path"])
    times = pd.DatetimeIndex(pd.to_datetime(df[cfg["time_col"]], errors="raise"))
    values = df[cfg["target_col"]].to_numpy(dtype=float)
    if times.hasnans or not times.is_monotonic_increasing or times.has_duplicates or not np.isfinite(values).all():
        raise ValueError("Require ordered unique timestamps and finite observations")
    step = infer_step_hours(times)
    if not np.allclose(np.diff(times.asi8) / 3.6e12, step):
        raise ValueError("Irregular cadence: explicit resampling policy required")
    lookback, horizon = steps_for_hours(168, step), steps_for_hours(24, step)
    test_start = int(len(values) * .8)
    val_start = int(test_start * .85)
    X, y = make_supervised(values, lookback, horizon)
    starts = np.arange(lookback, len(values) - horizon + 1)
    masks = {"train": starts + horizon <= val_start,
             "validation": (starts >= val_start) & (starts + horizon <= test_start),
             "test": starts >= test_start}
    if not all(mask.any() for mask in masks.values()):
        raise ValueError("Insufficient data for the requested splits")
    metadata = {"Protocol": PROTOCOL, "Dataset": name, "Rows": len(values),
        "Dataset path": str(cfg["path"]), "SHA256": hashlib.sha256(cfg["path"].read_bytes()).hexdigest(),
        "Sampling interval (h)": step, "Lookback (h)": 168, "Forecast horizon (h)": 24,
        "Lookback steps": lookback, "Horizon steps": horizon, "Unit": cfg["unit"],
        "Train end row exclusive": val_start, "Test start row": test_start,
        "Train rows": val_start, "Validation rows": test_start-val_start, "Test rows": len(values)-test_start}
    for key, mask in masks.items():
        origins = starts[mask]
        metadata[key.title()+" windows"] = int(mask.sum())
        metadata[key.title()+" first target"] = str(times[origins[0]])
        metadata[key.title()+" last target"] = str(times[origins[-1]+horizon-1])
    return X, y, masks, values, starts, times, metadata
