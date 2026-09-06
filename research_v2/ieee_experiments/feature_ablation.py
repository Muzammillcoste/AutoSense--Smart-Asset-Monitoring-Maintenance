"""Controlled causal-feature ablation on the preserved AutoSense protocol.

The script deliberately uses a fixed, predeclared configuration.  It does not
look at test scores to choose features or tune a model.  F1 and F2 supply only
features aligned with observed input timestamps; no future target values or
future-derived statistics enter a forecast window.
"""
import os
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_DETERMINISTIC_OPS", "1")

import json
import hashlib
import platform
import random
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf
import sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler

RESEARCH_ROOT = Path(__file__).resolve().parents[1]
if str(RESEARCH_ROOT) not in sys.path:
    sys.path.insert(0, str(RESEARCH_ROOT))

from baseline_evaluation import DATASETS, metrics, steps_for_hours  # noqa: E402
from protocol import prepare  # noqa: E402


OUT = RESEARCH_ROOT / "ieee_results"
SEED = 42
MAX_EPOCHS = 20
BATCH_SIZE = 64
PATIENCE = 5
CONFIGURATIONS = {
    "F0": "target history only",
    "F1": "target history plus deterministic calendar features at observed input timestamps",
    "F2": "F1 plus a real 24-hour causal lag and trailing 72-hour causal mean",
}
FIXED_PROTOCOL_METADATA = {
    "engine_temperature": {"Lookback steps": 168, "Horizon steps": 24,
                           "Train end row exclusive": 5956, "Test start row": 7008,
                           "Train rows": 5956, "Validation rows": 1052, "Test rows": 1753},
    "tyre_pressure": {"Lookback steps": 56, "Horizon steps": 8,
                      "Train end row exclusive": 1985, "Test start row": 2336,
                      "Train rows": 1985, "Validation rows": 351, "Test rows": 585},
    "tyre_temperature": {"Lookback steps": 56, "Horizon steps": 8,
                         "Train end row exclusive": 1985, "Test start row": 2336,
                         "Train rows": 1985, "Validation rows": 351, "Test rows": 585},
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_provenance() -> dict[str, object]:
    """Bind every feature-ablation row to the exact run environment/sources."""

    return {
        "Experiment script SHA256": sha256(Path(__file__)),
        "Protocol SHA256": sha256(RESEARCH_ROOT / "protocol.py"),
        "Architecture source SHA256": sha256(Path(__file__)),
        "Python": sys.version.split()[0],
        "TensorFlow": tf.__version__,
        "scikit-learn": sklearn.__version__,
        "Platform": platform.platform(),
        "Devices": str([str(device) for device in tf.config.list_physical_devices()]),
        "TensorFlow deterministic ops": True,
    }


def set_seed(seed: int) -> None:
    """Reset all supported pseudo-random generators before a declared run."""
    tf.keras.backend.clear_session()
    random.seed(seed)
    np.random.seed(seed)
    tf.keras.utils.set_random_seed(seed)


def build_lstm(lookback: int, n_features: int, horizon: int) -> tf.keras.Model:
    """The predeclared unidirectional counterpart of the benchmark Bi-LSTM."""
    return tf.keras.Sequential([
        tf.keras.Input(shape=(lookback, n_features)),
        tf.keras.layers.LSTM(128, return_sequences=True),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.LSTM(64, return_sequences=True),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.LSTM(32),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(horizon),
    ])


def calendar_features(times: pd.DatetimeIndex) -> np.ndarray:
    """Known deterministic calendar covariates, with no fitted statistics."""
    hour = times.hour.to_numpy(dtype=float) + times.minute.to_numpy(dtype=float) / 60.0
    weekday = times.dayofweek.to_numpy(dtype=float)
    month = times.month.to_numpy(dtype=float) - 1.0
    return np.column_stack([
        np.sin(2 * np.pi * hour / 24.0),
        np.cos(2 * np.pi * hour / 24.0),
        np.sin(2 * np.pi * weekday / 7.0),
        np.cos(2 * np.pi * weekday / 7.0),
        np.sin(2 * np.pi * month / 12.0),
        np.cos(2 * np.pi * month / 12.0),
    ])


def make_raw_features(values: np.ndarray, times: pd.DatetimeIndex, configuration: str,
                      cadence_hours: float) -> tuple[np.ndarray, list[str], dict]:
    """Build only causal row-level features before windowing.

    The 72-hour mean includes the observation at that row, which is available
    at that timestamp; it never includes a later observation.  At a forecast
    origin, every row in the input window predates the target horizon.
    """
    target = np.asarray(values, dtype=float)[:, None]
    if configuration == "F0":
        return target, ["target"], {}

    calendar = calendar_features(times)
    names = ["target", "hour_sin", "hour_cos", "day_of_week_sin", "day_of_week_cos",
             "month_sin", "month_cos"]
    output = [target, calendar]
    details: dict[str, int] = {}
    if configuration == "F2":
        lag_steps = steps_for_hours(24, cadence_hours)
        rolling_steps = steps_for_hours(72, cadence_hours)
        lag = np.full(len(values), np.nan, dtype=float)
        lag[lag_steps:] = values[:-lag_steps]
        rolling = pd.Series(values, dtype=float).rolling(
            window=rolling_steps, min_periods=rolling_steps
        ).mean().to_numpy()
        output.extend([lag[:, None], rolling[:, None]])
        names.extend(["target_lag_24_hours", "target_trailing_mean_72_hours"])
        details = {
            "24-hour lag sample count": lag_steps,
            "72-hour trailing mean sample count": rolling_steps,
        }
    return np.column_stack(output), names, details


def feature_windows(row_features: np.ndarray, starts: np.ndarray, lookback: int) -> np.ndarray:
    return np.asarray([row_features[start - lookback:start] for start in starts], dtype=np.float32)


def fixed_random_forest() -> RandomForestRegressor:
    return RandomForestRegressor(
        n_estimators=300, max_depth=16, min_samples_leaf=2,
        random_state=SEED, n_jobs=-1,
    )


def run_configuration(name: str, configuration: str) -> list[dict]:
    """Run both predeclared models for one data set/configuration pair."""
    _, targets, masks, values, starts, times, meta = prepare(name)
    expected_metadata = FIXED_PROTOCOL_METADATA[name]
    actual_metadata = {key: meta.get(key) for key in expected_metadata}
    if actual_metadata != expected_metadata:
        raise ValueError(
            f"{name} no longer matches the committed chronological protocol: "
            f"expected {expected_metadata}, got {actual_metadata}"
        )
    raw_features, feature_names, feature_details = make_raw_features(
        values, times, configuration, meta["Sampling interval (h)"]
    )
    train_end = meta["Train end row exclusive"]
    fitting_rows = raw_features[:train_end]
    finite_fitting_rows = fitting_rows[np.isfinite(fitting_rows).all(axis=1)]
    if not len(finite_fitting_rows):
        raise ValueError("No finite fitting-region rows available for feature scaling")
    feature_scaler = MinMaxScaler().fit(finite_fitting_rows)
    scaled_rows = feature_scaler.transform(raw_features)
    scaled_windows = feature_windows(scaled_rows, starts, meta["Lookback steps"])
    # F2 has no mathematically defined 24-hour lag at the beginning of the
    # raw series.  Discard only those early windows instead of imputing a
    # fabricated lag.  The standard validation/test origins are all valid;
    # thus target-period disjointness and the held-out test set are unchanged.
    valid_windows = np.isfinite(scaled_windows).all(axis=(1, 2))
    if not valid_windows[masks["test"]].all():
        raise ValueError("A standard test window lacks a causal feature")
    masks = {partition: mask & valid_windows for partition, mask in masks.items()}
    if not all(mask.any() for mask in masks.values()):
        raise ValueError("No valid windows remain in one chronological partition")
    target_scaler = MinMaxScaler().fit(values[:train_end, None])
    scaled_targets = target_scaler.transform(targets.reshape(-1, 1)).reshape(targets.shape).astype("float32")

    x_train = scaled_windows[masks["train"]]
    x_valid = scaled_windows[masks["validation"]]
    x_test = scaled_windows[masks["test"]]
    y_train_raw = targets[masks["train"]]
    y_valid_scaled = scaled_targets[masks["validation"]]
    y_train_scaled = scaled_targets[masks["train"]]
    truth = targets[masks["test"]]
    common = {
        "Dataset": name,
        "Dataset SHA256": meta["SHA256"],
        "Feature configuration": configuration,
        "Feature description": CONFIGURATIONS[configuration],
        "Feature names": json.dumps(feature_names),
        "Feature count": len(feature_names),
        "Seed": SEED,
        "Max epochs": MAX_EPOCHS,
        "Batch size": BATCH_SIZE,
        "Patience": PATIENCE,
        "Shuffle": False,
        "Scaler fitting region": "raw fitting-region rows only",
        "Unavailable-causal-feature policy": "discard early windows with unavailable lag/rolling inputs; no test origins discarded",
        "Target-period protocol": meta["Protocol"],
        "Sampling interval (h)": meta["Sampling interval (h)"],
        "Lookback steps": meta["Lookback steps"],
        "Horizon steps": meta["Horizon steps"],
        "Unit": meta["Unit"],
        "Test forecast origins": int(masks["test"].sum()),
        "Train forecast origins used": int(masks["train"].sum()),
        "Validation forecast origins used": int(masks["validation"].sum()),
        **run_provenance(),
        **feature_details,
    }
    rows: list[dict] = []

    # Trees use exactly the same fixed RF specification as the corrected
    # benchmark.  Features are input-scaled only from fitting-region rows;
    # targets stay in their physical units for transparent inverse-free scores.
    start = time.monotonic()
    forest = fixed_random_forest()
    forest.fit(x_train.reshape(len(x_train), -1), y_train_raw)
    forest_prediction = forest.predict(x_test.reshape(len(x_test), -1))
    rows.append({
        **common,
        "Model": "Random Forest",
        "Parameter count": np.nan,
        "Model parameters": np.nan,
        "Training seconds": time.monotonic() - start,
        "Epochs run": np.nan,
        "Best epoch": np.nan,
        **metrics(truth, forest_prediction),
    })

    # The LSTM architecture/budget are fixed before test evaluation and match
    # the Phase-C unidirectional reference family.
    set_seed(SEED)
    network = build_lstm(meta["Lookback steps"], len(feature_names), meta["Horizon steps"])
    network.compile(optimizer="adam", loss="mse", metrics=["mae"])
    start = time.monotonic()
    history = network.fit(
        x_train, y_train_scaled, validation_data=(x_valid, y_valid_scaled),
        epochs=MAX_EPOCHS, batch_size=BATCH_SIZE, shuffle=False, verbose=2,
        callbacks=[tf.keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=PATIENCE, restore_best_weights=True
        )],
    )
    scaled_prediction = network.predict(x_test, batch_size=BATCH_SIZE, verbose=0)
    prediction = target_scaler.inverse_transform(scaled_prediction.reshape(-1, 1)).reshape(scaled_prediction.shape)
    rows.append({
        **common,
        "Model": "LSTM",
        "Parameter count": int(network.count_params()),
        "Model parameters": int(network.count_params()),
        "Training seconds": time.monotonic() - start,
        "Epochs run": len(history.history["loss"]),
        "Best epoch": int(np.argmin(history.history["val_loss"]) + 1),
        **metrics(truth, prediction),
    })
    return rows


def main() -> None:
    tf.config.threading.set_intra_op_parallelism_threads(4)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.config.experimental.enable_op_determinism()
    OUT.mkdir(parents=True, exist_ok=True)
    destination = OUT / "feature_ablation.csv"
    all_rows: list[dict] = []
    for dataset in DATASETS:
        for configuration in CONFIGURATIONS:
            print(f"{dataset}: {configuration}", flush=True)
            all_rows.extend(run_configuration(dataset, configuration))
            pd.DataFrame(all_rows).to_csv(destination, index=False)
    print(pd.DataFrame(all_rows).to_string(index=False))


if __name__ == "__main__":
    main()
