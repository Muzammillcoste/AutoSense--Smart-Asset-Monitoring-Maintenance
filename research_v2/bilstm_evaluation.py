"""Train and evaluate a common Bi-LSTM on strictly separated target periods."""
import os
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_DETERMINISTIC_OPS", "1")
import argparse
import json
import platform
import random
import time
from pathlib import Path
import numpy as np
import pandas as pd
import sklearn
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from baseline_evaluation import DATASETS, metrics, evaluate_dataset
from protocol import prepare

OUT = Path(__file__).resolve().parent / "results"

def build_model(lookback, horizon):
    return tf.keras.Sequential([
        tf.keras.Input(shape=(lookback, 1)),
        tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(128, return_sequences=True)),
        tf.keras.layers.BatchNormalization(), tf.keras.layers.Dropout(.2),
        tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(64, return_sequences=True)),
        tf.keras.layers.BatchNormalization(), tf.keras.layers.Dropout(.3),
        tf.keras.layers.LSTM(32), tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dropout(.2), tf.keras.layers.Dense(horizon)])

def run(name, args):
    tf.keras.backend.clear_session()
    random.seed(42)
    np.random.seed(42)
    tf.keras.utils.set_random_seed(42)
    X, y, masks, values, starts, times, meta = prepare(name)
    scaler = MinMaxScaler().fit(values[:meta["Train end row exclusive"], None])
    xs = scaler.transform(X.reshape(-1, 1)).reshape(*X.shape, 1).astype("float32")
    ys = scaler.transform(y.reshape(-1, 1)).reshape(y.shape).astype("float32")
    model = build_model(meta["Lookback steps"], meta["Horizon steps"])
    model.compile(optimizer="adam", loss="mse", metrics=["mae"])
    artifact = OUT / name
    artifact.mkdir(parents=True, exist_ok=True)
    meta.update({"Model": "Bi-LSTM", "Model source": str(artifact / "model.keras"), "Retrained": True,
                 "Input shape": list(model.input_shape), "Output shape": list(model.output_shape),
                 "Features": [DATASETS[name]["target_col"]], "Seed": 42, "Max epochs": args.epochs,
                 "Batch size": args.batch_size, "Patience": 5, "Shuffle": False})
    print(json.dumps(meta, indent=2), flush=True)
    begin = time.monotonic()
    history = model.fit(xs[masks["train"]], ys[masks["train"]],
        validation_data=(xs[masks["validation"]], ys[masks["validation"]]),
        epochs=args.epochs, batch_size=args.batch_size, shuffle=False, verbose=2,
        callbacks=[tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True),
                   tf.keras.callbacks.CSVLogger(str(artifact / "training_history.csv"))])
    meta["Training seconds"] = time.monotonic() - begin
    meta["Epochs run"] = len(history.history["loss"])
    meta["Best epoch"] = int(np.argmin(history.history["val_loss"]) + 1)
    model.save(artifact / "model.keras")
    np.savez(artifact / "scaler.npz", scale=scaler.scale_, min=scaler.min_, data_min=scaler.data_min_, data_max=scaler.data_max_)
    pred_scaled = model.predict(xs[masks["test"]], batch_size=args.batch_size, verbose=0)
    pred = scaler.inverse_transform(pred_scaled.reshape(-1, 1)).reshape(pred_scaled.shape)
    truth = y[masks["test"]]
    np.savez_compressed(artifact / "test_predictions.npz", truth=truth, prediction=pred,
                        target_start_rows=starts[masks["test"]])
    (artifact / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    row = {**meta, **metrics(truth, pred)}
    horizon_rows = [{"Dataset": name, "Model": "Bi-LSTM", "Horizon (h)": (h+1)*meta["Sampling interval (h)"],
                     "Unit": meta["Unit"], **metrics(truth[:, h], pred[:, h])} for h in range(truth.shape[1])]
    pd.DataFrame([row]).to_csv(artifact / "metrics.csv", index=False)
    pd.DataFrame(horizon_rows).to_csv(artifact / "horizon_metrics.csv", index=False)
    print(name, metrics(truth, pred), flush=True)
    return row, horizon_rows

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--threads", type=int, default=4)
    args = parser.parse_args()
    if min(args.epochs, args.batch_size, args.threads) < 1:
        parser.error("epochs, batch-size and threads must be positive")
    tf.config.threading.set_intra_op_parallelism_threads(args.threads)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.config.experimental.enable_op_determinism()
    OUT.mkdir(parents=True, exist_ok=True)
    # Invalidate completion artifacts before a rerun; partial results are not final.
    for filename in ["final_comparison.csv", "bilstm_metrics.csv", "bilstm_horizon_metrics.csv",
                     "verification.json", "mae_comparison.csv"]:
        (OUT / filename).unlink(missing_ok=True)
    (OUT.parent / "REPORT_FOR_CHATGPT_REVIEW.md").unlink(missing_ok=True)
    environment = {"Python": platform.python_version(), "TensorFlow": tf.__version__,
                   "NumPy": np.__version__, "pandas": pd.__version__, "scikit-learn": sklearn.__version__,
                   "Platform": platform.platform(), "Devices": [str(x) for x in tf.config.list_physical_devices()],
                   "Arguments": vars(args)}
    print(json.dumps(environment, indent=2), flush=True)
    (OUT / "environment.json").write_text(json.dumps(environment, indent=2), encoding="utf-8")
    # Always regenerate baselines: stale CSVs may use the former leaking split.
    baseline = pd.concat([evaluate_dataset(n, c) for n, c in DATASETS.items()], ignore_index=True)
    baseline.to_csv(OUT / "baseline_metrics.csv", index=False)
    rows, horizons = [], []
    for name in DATASETS:
        row, hr = run(name, args)
        rows.append(row)
        horizons.extend(hr)
        pd.DataFrame(rows).to_csv(OUT / "bilstm_metrics.csv", index=False)
        pd.DataFrame(horizons).to_csv(OUT / "bilstm_horizon_metrics.csv", index=False)
    comparison = pd.concat([baseline, pd.DataFrame(rows)], ignore_index=True)
    comparison.to_csv(OUT / "final_comparison.csv", index=False)
    print(comparison[["Dataset", "Model", "MAE", "RMSE", "R2", "Unit"]].to_string(index=False), flush=True)

if __name__ == "__main__":
    main()
