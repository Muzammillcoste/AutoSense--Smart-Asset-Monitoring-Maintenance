"""External FD001 sensor forecasting under an engine-disjoint protocol.

NASA C-MAPSS is simulator-generated engine-degradation data.  This script
uses only the complete run-to-failure trajectories in train_FD001.txt for
future-sensor forecasting; official test trajectories are never extrapolated.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import sys
import time
import argparse
from pathlib import Path

os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_DETERMINISTIC_OPS", "1")

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import MinMaxScaler

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "external_data" / "cmapss"
OUT = ROOT / "ieee_results"
PRED_DIR = OUT / "cmapss_fd001_predictions"
LOOKBACK, HORIZON, SEED, EPOCHS, BATCH, PATIENCE = 30, 10, 42, 20, 64, 5
NEAR_CONSTANT_RELATIVE_VARIANCE = 1e-8
NEURAL_SEEDS = (11, 42, 84)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_fd001() -> pd.DataFrame:
    path = DATA / "train_FD001.txt"
    if not path.exists():
        raise FileNotFoundError(f"Missing authoritative FD001 file: {path}")
    columns = ["unit", "cycle", "setting_1", "setting_2", "setting_3"] + [f"sensor_{i}" for i in range(1, 22)]
    frame = pd.read_csv(path, sep=r"\s+", header=None, names=columns, engine="python")
    if frame.shape[1] != 26 or frame.isna().any().any() or not np.isfinite(frame.to_numpy(float)).all():
        raise ValueError("FD001 must have 26 finite numeric columns")
    frame["unit"] = frame["unit"].astype(int)
    frame["cycle"] = frame["cycle"].astype(int)
    if not frame["unit"].is_monotonic_increasing:
        raise ValueError("FD001 unit rows are not ordered")
    for unit, group in frame.groupby("unit", sort=False):
        cycles = group["cycle"].to_numpy()
        if cycles[0] != 1 or not np.array_equal(np.diff(cycles), np.ones(len(cycles) - 1, dtype=int)):
            raise ValueError(f"Unit {unit} does not have consecutive cycles")
    if frame["unit"].nunique() != 100:
        raise ValueError("Expected 100 FD001 train engines")
    return frame


def engine_split(frame: pd.DataFrame) -> dict:
    ids = np.sort(frame.unit.unique()).astype(int)
    permutation = np.random.default_rng(SEED).permutation(ids)
    split = {"train_engine_ids": sorted(map(int, permutation[:70])),
             "validation_engine_ids": sorted(map(int, permutation[70:85])),
             "test_engine_ids": sorted(map(int, permutation[85:]))}
    if len(set(sum((v for v in split.values()), []))) != 100:
        raise ValueError("Engine split overlap")
    result = {"dataset": "NASA C-MAPSS FD001 train trajectories", "split_seed": SEED,
              "split_rule": "seeded permutation: first 70 train, next 15 validation, final 15 test",
              "seeded_engine_permutation": list(map(int, permutation)),
              **split, "dataset_sha256": digest(DATA / "train_FD001.txt"),
              "rows": int(len(frame)), "columns": 26}
    (OUT / "cmapss_fd001_split.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def select_sensors(frame: pd.DataFrame, train_ids: list[int]) -> list[str]:
    sensors = [f"sensor_{i}" for i in range(1, 22)]
    train = frame[frame.unit.isin(train_ids)]
    variances = train[sensors].var(ddof=0)
    scale = float(variances.max())
    cutoff = max(scale * NEAR_CONSTANT_RELATIVE_VARIANCE, np.finfo(float).eps)
    retained = [sensor for sensor in sensors if float(variances[sensor]) > cutoff]
    if len(retained) < 4:
        raise ValueError("Near-constant threshold left fewer than four sensors")
    rows = []
    for sensor in sensors:
        corrs = []
        if sensor in retained:
            for _unit, group in train.groupby("unit", sort=False):
                # pandas rank correlation is Spearman and uses only this train engine.
                value = group[sensor].corr(group["cycle"], method="spearman")
                corrs.append(abs(float(value)) if np.isfinite(value) else 0.0)
        score = float(np.median(corrs)) if corrs else np.nan
        rows.append({"Sensor": sensor, "Sensor index": int(sensor.split("_")[1]),
                     "Train-only variance": float(variances[sensor]), "Variance threshold": cutoff,
                     "Retained after near-constant filter": sensor in retained,
                     "Median absolute Spearman correlation with cycle": score,
                     "Selection procedure": "train engines only; median within-engine absolute Spearman"})
    ranking = pd.DataFrame(rows)
    candidates = ranking[ranking["Retained after near-constant filter"]].copy()
    candidates = candidates.sort_values(["Median absolute Spearman correlation with cycle", "Sensor index"],
                                        ascending=[False, True], kind="stable")
    selected = candidates.head(4)["Sensor"].tolist()
    ranking["Rank among retained"] = np.nan
    ranking.loc[candidates.index, "Rank among retained"] = np.arange(1, len(candidates) + 1)
    ranking["Selected top four"] = ranking.Sensor.isin(selected)
    ranking.to_csv(OUT / "cmapss_sensor_selection.csv", index=False)
    return selected


def make_windows(frame: pd.DataFrame, engine_ids: list[int], inputs: list[str], target: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    xs, ys, units, origins = [], [], [], []
    for unit in engine_ids:
        group = frame[frame.unit.eq(unit)].sort_values("cycle")
        values = group[inputs].to_numpy(float)
        target_values = group[target].to_numpy(float)
        cycles = group.cycle.to_numpy(int)
        for start in range(len(group) - LOOKBACK - HORIZON + 1):
            xs.append(values[start:start + LOOKBACK])
            ys.append(target_values[start + LOOKBACK:start + LOOKBACK + HORIZON])
            units.append(unit)
            origins.append(cycles[start + LOOKBACK])
    return np.asarray(xs), np.asarray(ys), np.asarray(units), np.asarray(origins)


def set_seed(seed: int) -> None:
    tf.keras.backend.clear_session(); random.seed(seed); np.random.seed(seed); tf.keras.utils.set_random_seed(seed)


def lstm_model(n_features: int, bidirectional: bool) -> tf.keras.Model:
    layer = tf.keras.layers.LSTM(64)
    if bidirectional:
        layer = tf.keras.layers.Bidirectional(layer)
    return tf.keras.Sequential([tf.keras.Input(shape=(LOOKBACK, n_features)), layer,
                                tf.keras.layers.Dense(32, activation="relu"), tf.keras.layers.Dense(HORIZON)])


def scores(truth: np.ndarray, prediction: np.ndarray) -> dict:
    return {"MAE": float(mean_absolute_error(truth.ravel(), prediction.ravel())),
            "RMSE": float(np.sqrt(mean_squared_error(truth.ravel(), prediction.ravel()))),
            "R2": float(r2_score(truth.ravel(), prediction.ravel()))}


def train_and_predict(model_name: str, x_train: np.ndarray, y_train_scaled: np.ndarray, y_train_raw: np.ndarray,
                      x_valid: np.ndarray, y_valid: np.ndarray, x_test: np.ndarray, target_scaler: MinMaxScaler,
                      seed: int | None, persistence_scale: float, persistence_min: float) -> tuple[np.ndarray, dict]:
    if model_name == "Persistence":
        # In C0 input feature zero is target; in C1 the target's position is
        # supplied as the final feature by the caller below.
        last_raw = (x_test[:, -1, -1] - persistence_min) / persistence_scale
        return np.repeat(last_raw[:, None], HORIZON, axis=1), {"Training seconds": 0., "Epochs run": np.nan, "Best epoch": np.nan, "Parameter count": np.nan}
    if model_name == "Random Forest":
        start = time.monotonic(); model = RandomForestRegressor(n_estimators=300, max_depth=16, min_samples_leaf=2, random_state=SEED, n_jobs=-1)
        model.fit(x_train.reshape(len(x_train), -1), y_train_raw)
        return model.predict(x_test.reshape(len(x_test), -1)), {"Training seconds": time.monotonic() - start, "Epochs run": np.nan, "Best epoch": np.nan, "Parameter count": np.nan}
    set_seed(int(seed)); network = lstm_model(x_train.shape[-1], model_name == "Bi-LSTM"); network.compile(optimizer="adam", loss="mse", metrics=["mae"])
    start = time.monotonic(); history = network.fit(x_train, y_train_scaled, validation_data=(x_valid, y_valid), epochs=EPOCHS, batch_size=BATCH, shuffle=False, verbose=2,
                                                     callbacks=[tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=PATIENCE, restore_best_weights=True)])
    prediction_scaled = network.predict(x_test, batch_size=BATCH, verbose=0)
    prediction = target_scaler.inverse_transform(prediction_scaled.reshape(-1, 1)).reshape(prediction_scaled.shape)
    return prediction, {"Training seconds": time.monotonic() - start, "Epochs run": len(history.history["loss"]),
                        "Best epoch": int(np.argmin(history.history["val_loss"]) + 1), "Parameter count": int(network.count_params())}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-only", action="store_true", help="validate NASA FD001, save the fixed engine split and training-only sensor selection, then stop before any model fit")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True); PRED_DIR.mkdir(parents=True, exist_ok=True)
    tf.config.threading.set_intra_op_parallelism_threads(4); tf.config.threading.set_inter_op_parallelism_threads(1); tf.config.experimental.enable_op_determinism()
    frame = load_fd001(); split = engine_split(frame); sensors = select_sensors(frame, split["train_engine_ids"])
    if args.prepare_only:
        print(f"Validated FD001; saved fixed split and selected sensors: {sensors}")
        return
    metrics_rows, horizon_rows, target_ranges = [], [], {}
    for config in ("C0", "C1"):
        for target_index, target in enumerate(sensors):
            observed = [target] if config == "C0" else ["setting_1", "setting_2", "setting_3", *sensors]
            # Reorder C1 so the target is always the final input feature, which
            # makes the persistence baseline a target-history predictor.
            if config == "C1": observed = [x for x in observed if x != target] + [target]
            train_raw = frame[frame.unit.isin(split["train_engine_ids"])][observed].to_numpy(float)
            feature_scaler = MinMaxScaler().fit(train_raw)
            target_scaler = MinMaxScaler().fit(frame[frame.unit.isin(split["train_engine_ids"])][[target]])
            target_ranges[target] = float(target_scaler.data_range_[0])
            parts = {}
            for label, ids in (("train", split["train_engine_ids"]), ("validation", split["validation_engine_ids"]), ("test", split["test_engine_ids"])):
                x, y, units, origins = make_windows(frame, ids, observed, target)
                parts[label] = (feature_scaler.transform(x.reshape(-1, len(observed))).reshape(x.shape).astype("float32"),
                                target_scaler.transform(y.reshape(-1, 1)).reshape(y.shape).astype("float32"), y, units, origins)
            xtr, ytr_scaled, ytr_raw, _, _ = parts["train"]; xva, yva_scaled, _, _, _ = parts["validation"]; xte, _, yte, test_units, test_origins = parts["test"]
            models = ["Persistence", "Random Forest", "LSTM", "Bi-LSTM"] if config == "C0" else ["Random Forest", "LSTM", "Bi-LSTM"]
            for model in models:
                seeds = NEURAL_SEEDS if model == "Bi-LSTM" else (SEED,)
                for model_seed in seeds:
                    prediction, fit = train_and_predict(model, xtr, ytr_scaled, ytr_raw, xva, yva_scaled, xte, target_scaler, model_seed,
                                                        float(feature_scaler.scale_[-1]), float(feature_scaler.min_[-1]))
                    result = scores(yte, prediction)
                    row = {"Dataset": "NASA C-MAPSS FD001 (simulated)", "Configuration": config, "Target sensor": target,
                           "Model": model, "Seed": model_seed, "Input features": json.dumps(observed), "Lookback cycles": LOOKBACK,
                           "Forecast horizon cycles": HORIZON, "Train engines": len(split["train_engine_ids"]), "Validation engines": len(split["validation_engine_ids"]), "Test engines": len(split["test_engine_ids"]),
                           "Train-only scaling": True, "Dataset SHA256": split["dataset_sha256"], "Unit": "native sensor units", **fit, **result}
                    metrics_rows.append(row)
                    for horizon in range(HORIZON):
                        horizon_rows.append({**{k: row[k] for k in ("Dataset", "Configuration", "Target sensor", "Model", "Seed", "Unit")}, "Horizon cycle": horizon + 1,
                                             "MAE": float(mean_absolute_error(yte[:, horizon], prediction[:, horizon]))})
                    safe = f"{config}_{target}_{model.replace(' ', '_').replace('-', '')}_seed{model_seed}"
                    np.savez_compressed(PRED_DIR / f"{safe}.npz", truth=yte, prediction=prediction, unit_ids=test_units, target_start_cycles=test_origins,
                                        configuration=config, target_sensor=target, model=model, seed=model_seed)
                    pd.DataFrame(metrics_rows).to_csv(OUT / "cmapss_fd001_metrics.csv", index=False)
                    pd.DataFrame(horizon_rows).to_csv(OUT / "cmapss_fd001_horizon_metrics.csv", index=False)
    detailed = pd.DataFrame(metrics_rows)
    # Macro errors are calculated after each target's train-only min--max scale,
    # never by pooling incompatible physical sensor units.
    detailed["Normalized MAE"] = detailed.apply(lambda row: row["MAE"] / target_ranges[row["Target sensor"]], axis=1)
    detailed["Normalized RMSE"] = detailed.apply(lambda row: row["RMSE"] / target_ranges[row["Target sensor"]], axis=1)
    macro_rows = []
    for (config, model, model_seed), group in detailed.groupby(["Configuration", "Model", "Seed"], dropna=False):
        macro_rows.append({"Dataset": "NASA C-MAPSS FD001 (simulated)", "Configuration": config,
                           "Target sensor": "MACRO_AVERAGE_NORMALIZED", "Model": model, "Seed": model_seed,
                           "Metric scale": "training-range-normalized across selected sensors; raw-unit MAE/RMSE not pooled",
                           "Normalized MAE": group["Normalized MAE"].mean(), "Normalized RMSE": group["Normalized RMSE"].mean(),
                           "R2": group["R2"].mean(), "Selected sensor count": len(group)})
    pd.concat([detailed, pd.DataFrame(macro_rows)], ignore_index=True, sort=False).to_csv(OUT / "cmapss_fd001_metrics.csv", index=False)
    horizon_detail = pd.DataFrame(horizon_rows)
    horizon_detail["Normalized MAE"] = horizon_detail.apply(lambda row: row["MAE"] / target_ranges[row["Target sensor"]], axis=1)
    macro_horizon = horizon_detail.groupby(["Configuration", "Model", "Seed", "Horizon cycle"], dropna=False)["Normalized MAE"].mean().reset_index()
    macro_horizon["Target sensor"] = "MACRO_AVERAGE_NORMALIZED"
    macro_horizon["Metric scale"] = "training-range-normalized across selected sensors"
    pd.concat([horizon_detail, macro_horizon], ignore_index=True, sort=False).to_csv(OUT / "cmapss_fd001_horizon_metrics.csv", index=False)
    neural = detailed[detailed.Model.eq("Bi-LSTM")].groupby(["Configuration", "Target sensor"])[["MAE", "RMSE", "R2"]].agg(["mean", "std"]).reset_index()
    neural.columns = ["Configuration", "Target sensor", "MAE mean", "MAE std", "RMSE mean", "RMSE std", "R2 mean", "R2 std"]
    neural.to_csv(OUT / "cmapss_multiseed_summary.csv", index=False)
    print("C-MAPSS FD001 experiment complete. Per-sensor results are in ieee_results; no official test trajectory was forecast beyond truncation.")


if __name__ == "__main__":
    main()
/