"""Run the pre-declared AutoSense Bi-LSTM robustness experiment.

This is intentionally separate from ``research_v2/results``.  It reuses the
corrected chronological protocol and the canonical Bi-LSTM architecture, then
trains it once for each pre-declared initialization seed.  It does not select
models or hyperparameters using held-out test metrics.

Run from the repository root, for example::

    .venv/Scripts/python.exe -u research_v2/ieee_experiments/multiseed_bilstm.py

The only experiment outputs are
``research_v2/ieee_results/multiseed_bilstm_metrics.csv`` and
``research_v2/ieee_results/multiseed_summary.csv``.  Use ``--resume`` after an
interruption to retain completed, provenance-compatible runs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


# Set these before importing TensorFlow.  They match the corrected benchmark.
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_DETERMINISTIC_OPS", "1")

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RESEARCH_ROOT = REPOSITORY_ROOT / "research_v2"
OUTPUT_DIR = RESEARCH_ROOT / "ieee_results"
METRICS_PATH = OUTPUT_DIR / "multiseed_bilstm_metrics.csv"
SUMMARY_PATH = OUTPUT_DIR / "multiseed_summary.csv"

EXPERIMENT_NAME = "AutoSense Bi-LSTM multi-seed robustness"
MODEL_NAME = "Bi-LSTM"
FIXED_SEEDS = (11, 21, 42, 84, 168)
MAX_EPOCHS = 20
BATCH_SIZE = 64
PATIENCE = 5
INTRA_OP_THREADS_DEFAULT = 4
INTER_OP_THREADS = 1
ARCHITECTURE_SOURCE = "research_v2/bilstm_evaluation.py:build_model"
ARCHITECTURE_DESCRIPTION = (
    "Bidirectional(LSTM(128, return_sequences=True)) -> BatchNormalization -> "
    "Dropout(0.2) -> Bidirectional(LSTM(64, return_sequences=True)) -> "
    "BatchNormalization -> Dropout(0.3) -> LSTM(32) -> Dense(64, relu) -> "
    "Dropout(0.2) -> Dense(horizon)"
)

# Keep the CSV schema explicit: a result row contains both the required metrics
# and the facts needed to reproduce or audit the run without altering the
# original corrected-benchmark artifacts.
METRICS_COLUMNS = [
    "Experiment",
    "Git commit",
    "Script SHA256",
    "Protocol SHA256",
    "Architecture source SHA256",
    "Protocol",
    "Model",
    "Architecture",
    "Architecture source",
    "Dataset",
    "Dataset path",
    "Dataset SHA256",
    "Dataset rows",
    "Sampling interval (h)",
    "Lookback (h)",
    "Forecast horizon (h)",
    "Lookback steps",
    "Horizon steps",
    "Input shape",
    "Output shape",
    "Features",
    "Train end row exclusive",
    "Test start row",
    "Train rows",
    "Validation rows",
    "Test rows",
    "Train windows",
    "Validation windows",
    "Test windows",
    "Scaler",
    "Scaler fitting region",
    "Validation use",
    "Test use",
    "Seed set",
    "Seed",
    "Max epochs",
    "Batch size",
    "Early stopping monitor",
    "Patience",
    "Restore best weights",
    "Shuffle",
    "Optimizer",
    "Loss",
    "TensorFlow deterministic ops",
    "Intra-op threads",
    "Inter-op threads",
    "Python",
    "TensorFlow",
    "NumPy",
    "pandas",
    "scikit-learn",
    "Platform",
    "Devices",
    "Training seconds",
    "Epochs run",
    "Best epoch",
    "Best validation loss",
    "MAE",
    "RMSE",
    "R2",
    "Unit",
]

SUMMARY_COLUMNS = [
    "Experiment",
    "Git commit",
    "Script SHA256",
    "Protocol SHA256",
    "Architecture source SHA256",
    "Protocol",
    "Model",
    "Architecture",
    "Dataset",
    "Dataset SHA256",
    "Unit",
    "Seed set",
    "Seeds completed",
    "Seed count",
    "Completed planned seeds",
    "Standard deviation ddof",
    "Max epochs",
    "Batch size",
    "Patience",
    "Shuffle",
    "Scaler fitting region",
    "MAE mean",
    "MAE std",
    "RMSE mean",
    "RMSE std",
    "R2 mean",
    "R2 std",
]


def parse_args() -> argparse.Namespace:
    """Return controls that do not change the pre-registered experiment."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--threads",
        type=int,
        default=INTRA_OP_THREADS_DEFAULT,
        help=(
            "TensorFlow intra-op CPU threads (default: %(default)s). This changes "
            "runtime resources only; all scientific settings remain fixed."
        ),
    )
    parser.add_argument(
        "--verbose",
        type=int,
        choices=(0, 1, 2),
        default=2,
        help="Keras fit verbosity (default: %(default)s).",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Reuse already-completed rows only when their fixed protocol and source "
            "hashes match this script."
        ),
    )
    args = parser.parse_args()
    if args.threads < 1:
        parser.error("--threads must be positive")
    return args


def sha256_file(path: Path) -> str:
    """Hash a small source or dataset file without loading it all into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repository_relative(path: Path) -> str:
    """Prefer a portable repository-relative path in reproducibility metadata."""
    try:
        return path.resolve().relative_to(REPOSITORY_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def git_commit() -> str:
    """Return the checked-out commit, without failing a run outside a Git clone."""
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPOSITORY_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"
    return completed.stdout.strip() or "unavailable"


def add_research_import_path() -> None:
    """Make legacy absolute imports work for both script and module invocation."""
    research_path = str(RESEARCH_ROOT)
    if research_path not in sys.path:
        sys.path.insert(0, research_path)


def import_dependencies() -> dict[str, Any]:
    """Import the canonical protocol and architecture after TensorFlow env setup."""
    add_research_import_path()
    import numpy as np
    import pandas as pd
    import sklearn
    import tensorflow as tf
    from sklearn.preprocessing import MinMaxScaler

    from baseline_evaluation import DATASETS, metrics
    from bilstm_evaluation import build_model
    from protocol import prepare

    return {
        "np": np,
        "pd": pd,
        "sklearn": sklearn,
        "tf": tf,
        "MinMaxScaler": MinMaxScaler,
        "DATASETS": DATASETS,
        "metrics": metrics,
        "build_model": build_model,
        "prepare": prepare,
    }


def configure_tensorflow(tf: Any, threads: int) -> None:
    """Apply the corrected benchmark's deterministic TensorFlow configuration."""
    tf.config.threading.set_intra_op_parallelism_threads(threads)
    tf.config.threading.set_inter_op_parallelism_threads(INTER_OP_THREADS)
    tf.config.experimental.enable_op_determinism()


def expected_dataset_order(datasets: dict[str, Any]) -> tuple[str, ...]:
    """Assert the exact three pre-declared AutoSense targets and their order."""
    expected = ("engine_temperature", "tyre_pressure", "tyre_temperature")
    if tuple(datasets) != expected:
        raise RuntimeError(
            "The corrected benchmark dataset mapping changed; refusing to run a "
            f"different robustness experiment. Expected {expected}, got {tuple(datasets)}."
        )
    return expected


def environment_metadata(deps: dict[str, Any], threads: int) -> dict[str, Any]:
    """Collect runtime facts once so every result row is independently auditable."""
    tf = deps["tf"]
    devices = [str(device) for device in tf.config.list_physical_devices()]
    return {
        "Experiment": EXPERIMENT_NAME,
        "Git commit": git_commit(),
        "Script SHA256": sha256_file(Path(__file__).resolve()),
        "Protocol SHA256": sha256_file(RESEARCH_ROOT / "protocol.py"),
        "Architecture source SHA256": sha256_file(RESEARCH_ROOT / "bilstm_evaluation.py"),
        "Model": MODEL_NAME,
        "Architecture": ARCHITECTURE_DESCRIPTION,
        "Architecture source": ARCHITECTURE_SOURCE,
        "Scaler": "sklearn.preprocessing.MinMaxScaler",
        "Scaler fitting region": "Raw rows [0, Train end row exclusive); validation/test excluded",
        "Validation use": "Chronological validation target period; early stopping only",
        "Test use": "Final evaluation only; no tuning or refitting",
        "Seed set": json.dumps(FIXED_SEEDS),
        "Max epochs": MAX_EPOCHS,
        "Batch size": BATCH_SIZE,
        "Early stopping monitor": "val_loss",
        "Patience": PATIENCE,
        "Restore best weights": True,
        "Shuffle": False,
        "Optimizer": "Adam (Keras default settings)",
        "Loss": "mean_squared_error",
        "TensorFlow deterministic ops": True,
        "Intra-op threads": threads,
        "Inter-op threads": INTER_OP_THREADS,
        "Python": platform.python_version(),
        "TensorFlow": tf.__version__,
        "NumPy": deps["np"].__version__,
        "pandas": deps["pd"].__version__,
        "scikit-learn": deps["sklearn"].__version__,
        "Platform": platform.platform(),
        "Devices": json.dumps(devices),
    }


def dataset_metadata(
    name: str,
    cfg: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Extract the protocol fields that must be identical for every seed."""
    return {
        "Protocol": metadata["Protocol"],
        "Dataset": name,
        "Dataset path": repository_relative(Path(cfg["path"])),
        "Dataset SHA256": metadata["SHA256"],
        "Dataset rows": metadata["Rows"],
        "Sampling interval (h)": metadata["Sampling interval (h)"],
        "Lookback (h)": metadata["Lookback (h)"],
        "Forecast horizon (h)": metadata["Forecast horizon (h)"],
        "Lookback steps": metadata["Lookback steps"],
        "Horizon steps": metadata["Horizon steps"],
        "Input shape": json.dumps([metadata["Lookback steps"], 1]),
        "Output shape": json.dumps([metadata["Horizon steps"]]),
        "Features": json.dumps([cfg["target_col"]]),
        "Train end row exclusive": metadata["Train end row exclusive"],
        "Test start row": metadata["Test start row"],
        "Train rows": metadata["Train rows"],
        "Validation rows": metadata["Validation rows"],
        "Test rows": metadata["Test rows"],
        "Train windows": metadata["Train windows"],
        "Validation windows": metadata["Validation windows"],
        "Test windows": metadata["Test windows"],
        "Unit": metadata["Unit"],
    }


def scale_windows(
    X: Any,
    y: Any,
    values: Any,
    train_end_row_exclusive: int,
    min_max_scaler: Any,
) -> tuple[Any, Any, Any]:
    """Fit the scaler only on raw fitting-region values, as in the benchmark."""
    scaler = min_max_scaler().fit(values[:train_end_row_exclusive, None])
    xs = scaler.transform(X.reshape(-1, 1)).reshape(*X.shape, 1).astype("float32")
    ys = scaler.transform(y.reshape(-1, 1)).reshape(y.shape).astype("float32")
    return scaler, xs, ys


def run_one_seed(
    *,
    name: str,
    cfg: dict[str, Any],
    seed: int,
    X: Any,
    y: Any,
    masks: dict[str, Any],
    values: Any,
    metadata: dict[str, Any],
    common_metadata: dict[str, Any],
    deps: dict[str, Any],
    verbose: int,
) -> dict[str, Any]:
    """Train exactly one fixed Bi-LSTM initialization and score the untouched test set."""
    np = deps["np"]
    tf = deps["tf"]

    # This mirrors the corrected benchmark, changing only its pre-declared seed.
    tf.keras.backend.clear_session()
    random.seed(seed)
    np.random.seed(seed)
    tf.keras.utils.set_random_seed(seed)

    scaler, xs, ys = scale_windows(
        X,
        y,
        values,
        metadata["Train end row exclusive"],
        deps["MinMaxScaler"],
    )
    model = None
    try:
        model = deps["build_model"](metadata["Lookback steps"], metadata["Horizon steps"])
        expected_input = (None, metadata["Lookback steps"], 1)
        expected_output = (None, metadata["Horizon steps"])
        if tuple(model.input_shape) != expected_input or tuple(model.output_shape) != expected_output:
            raise RuntimeError(
                "The imported canonical Bi-LSTM does not have the expected input/output "
                f"shapes: {model.input_shape}, {model.output_shape}."
            )
        model.compile(optimizer="adam", loss="mse", metrics=["mae"])

        started = time.monotonic()
        history = model.fit(
            xs[masks["train"]],
            ys[masks["train"]],
            validation_data=(xs[masks["validation"]], ys[masks["validation"]]),
            epochs=MAX_EPOCHS,
            batch_size=BATCH_SIZE,
            shuffle=False,
            verbose=verbose,
            callbacks=[
                tf.keras.callbacks.EarlyStopping(
                    monitor="val_loss",
                    patience=PATIENCE,
                    restore_best_weights=True,
                )
            ],
        )
        training_seconds = time.monotonic() - started
        pred_scaled = model.predict(xs[masks["test"]], batch_size=BATCH_SIZE, verbose=0)
        prediction = scaler.inverse_transform(pred_scaled.reshape(-1, 1)).reshape(pred_scaled.shape)
        truth = y[masks["test"]]
        scores = deps["metrics"](truth, prediction)

        row = {
            **common_metadata,
            **dataset_metadata(name, cfg, metadata),
            "Seed": seed,
            "Training seconds": training_seconds,
            "Epochs run": len(history.history["loss"]),
            "Best epoch": int(np.argmin(history.history["val_loss"]) + 1),
            "Best validation loss": float(np.min(history.history["val_loss"])),
            **scores,
        }
        return {column: row.get(column, "") for column in METRICS_COLUMNS}
    finally:
        # No model binaries or training-history artifacts are retained for this study.
        if model is not None:
            del model
        tf.keras.backend.clear_session()


def validate_resume_frame(frame: Any, dataset_order: tuple[str, ...], common: dict[str, Any]) -> None:
    """Reject a resume file if it could silently mix a different experiment."""
    required = set(METRICS_COLUMNS)
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise RuntimeError(
            "Cannot resume: metrics file lacks required reproducibility columns: " + ", ".join(missing)
        )
    if frame.empty:
        return

    keys = frame[["Dataset", "Seed"]].copy()
    try:
        keys["Seed"] = keys["Seed"].astype(int)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("Cannot resume: existing Seed values are not integers.") from exc
    if not keys["Dataset"].isin(dataset_order).all() or not keys["Seed"].isin(FIXED_SEEDS).all():
        raise RuntimeError("Cannot resume: metrics file contains a dataset or seed outside the pre-declared plan.")
    if keys.duplicated().any():
        raise RuntimeError("Cannot resume: metrics file contains duplicate Dataset/Seed rows.")

    # These source and protocol fields must match exactly.  Runtime timing and
    # hardware fields are deliberately not compared because they describe the
    # completed runs rather than the methodological contract.
    for field in (
        "Experiment",
        "Script SHA256",
        "Protocol SHA256",
        "Architecture source SHA256",
        "Model",
        "Architecture",
        "Architecture source",
        "Seed set",
        "Max epochs",
        "Batch size",
        "Early stopping monitor",
        "Patience",
        "Restore best weights",
        "Shuffle",
        "Optimizer",
        "Loss",
        "Scaler",
        "Scaler fitting region",
        "Validation use",
        "Test use",
    ):
        expected = common[field]
        observed = frame[field]
        if field in {"Max epochs", "Batch size", "Patience"}:
            matches = observed.astype(float).eq(float(expected))
        else:
            matches = observed.astype(str).eq(str(expected))
        if not matches.all():
            raise RuntimeError(f"Cannot resume: existing {field!r} does not match this fixed experiment.")


def ordered_metrics_frame(rows: list[dict[str, Any]], deps: dict[str, Any]) -> Any:
    """Return rows in pre-declared dataset/seed order, irrespective of resume order."""
    pd = deps["pd"]
    frame = pd.DataFrame(rows, columns=METRICS_COLUMNS)
    if frame.empty:
        return frame
    dataset_rank = {name: index for index, name in enumerate((
        "engine_temperature", "tyre_pressure", "tyre_temperature"
    ))}
    seed_rank = {seed: index for index, seed in enumerate(FIXED_SEEDS)}
    frame["_dataset_rank"] = frame["Dataset"].map(dataset_rank)
    frame["_seed_rank"] = frame["Seed"].astype(int).map(seed_rank)
    frame = frame.sort_values(["_dataset_rank", "_seed_rank"], kind="stable")
    return frame.drop(columns=["_dataset_rank", "_seed_rank"]).reset_index(drop=True)


def make_summary(metrics_frame: Any, deps: dict[str, Any]) -> Any:
    """Summarize per-dataset seed variation using the sample standard deviation."""
    np = deps["np"]
    pd = deps["pd"]
    rows: list[dict[str, Any]] = []
    for dataset in ("engine_temperature", "tyre_pressure", "tyre_temperature"):
        group = metrics_frame.loc[metrics_frame["Dataset"] == dataset]
        if group.empty:
            continue
        first = group.iloc[0]
        completed_seeds = sorted(int(seed) for seed in group["Seed"].tolist())
        row = {
            "Experiment": first["Experiment"],
            "Git commit": first["Git commit"],
            "Script SHA256": first["Script SHA256"],
            "Protocol SHA256": first["Protocol SHA256"],
            "Architecture source SHA256": first["Architecture source SHA256"],
            "Protocol": first["Protocol"],
            "Model": first["Model"],
            "Architecture": first["Architecture"],
            "Dataset": dataset,
            "Dataset SHA256": first["Dataset SHA256"],
            "Unit": first["Unit"],
            "Seed set": json.dumps(FIXED_SEEDS),
            "Seeds completed": json.dumps(completed_seeds),
            "Seed count": len(completed_seeds),
            "Completed planned seeds": completed_seeds == list(FIXED_SEEDS),
            "Standard deviation ddof": 1,
            "Max epochs": first["Max epochs"],
            "Batch size": first["Batch size"],
            "Patience": first["Patience"],
            "Shuffle": first["Shuffle"],
            "Scaler fitting region": first["Scaler fitting region"],
        }
        for metric in ("MAE", "RMSE", "R2"):
            numeric = group[metric].astype(float)
            row[f"{metric} mean"] = float(numeric.mean())
            # The sample standard deviation is undefined for a partial one-seed checkpoint.
            row[f"{metric} std"] = float(numeric.std(ddof=1)) if len(numeric) > 1 else np.nan
        rows.append(row)
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def write_outputs(rows: list[dict[str, Any]], deps: dict[str, Any]) -> None:
    """Persist the two declared CSV artifacts after each completed seed checkpoint."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    metrics_frame = ordered_metrics_frame(rows, deps)
    metrics_frame.to_csv(METRICS_PATH, index=False)
    make_summary(metrics_frame, deps).to_csv(SUMMARY_PATH, index=False)


def main() -> None:
    args = parse_args()
    deps = import_dependencies()
    configure_tensorflow(deps["tf"], args.threads)
    datasets = deps["DATASETS"]
    dataset_order = expected_dataset_order(datasets)
    common = environment_metadata(deps, args.threads)

    rows: list[dict[str, Any]] = []
    if args.resume and METRICS_PATH.exists():
        existing = deps["pd"].read_csv(METRICS_PATH)
        validate_resume_frame(existing, dataset_order, common)
        rows = existing[METRICS_COLUMNS].to_dict(orient="records")
        print(f"Resuming with {len(rows)} completed run(s) from {METRICS_PATH}", flush=True)

    completed = {(str(row["Dataset"]), int(row["Seed"])) for row in rows}
    for name in dataset_order:
        X, y, masks, values, _starts, _times, metadata = deps["prepare"](name)
        for seed in FIXED_SEEDS:
            if (name, seed) in completed:
                print(f"Skipping completed {name}, seed {seed}", flush=True)
                continue
            print(f"Training {name}, seed {seed} ({MAX_EPOCHS} epoch cap; no shuffle)", flush=True)
            row = run_one_seed(
                name=name,
                cfg=datasets[name],
                seed=seed,
                X=X,
                y=y,
                masks=masks,
                values=values,
                metadata=metadata,
                common_metadata=common,
                deps=deps,
                verbose=args.verbose,
            )
            rows.append(row)
            completed.add((name, seed))
            write_outputs(rows, deps)
            print(
                f"Completed {name}, seed {seed}: MAE={row['MAE']:.6g}, "
                f"RMSE={row['RMSE']:.6g}, R2={row['R2']:.6g}",
                flush=True,
            )

    # Also refresh the summary if --resume found all planned runs already complete.
    if rows:
        write_outputs(rows, deps)
    print(f"Saved metrics to {METRICS_PATH}", flush=True)
    print(f"Saved per-dataset seed summary to {SUMMARY_PATH}", flush=True)


if __name__ == "__main__":
    main()
