"""First-pass LSTM versus Bi-LSTM architecture ablation for AutoSense.

This script deliberately uses the unchanged chronological protocol in
``research_v2/protocol.py``.  Both architectures receive the same raw-window
origins, train-only MinMax scaler, training budget, and seed.  The Bi-LSTM is
constructed with the exact model builder used by the corrected benchmark;
the LSTM is its unidirectional counterpart specified in the IEEE execution
plan.

Important limitation: this is a *seed-42-only first pass*.  Its output must
not be interpreted as a seed-robust architecture ranking.  It is an ablation
to be complemented by a multi-seed study, rather than a procedure for tuning
an architecture against held-out test results.

Run from the repository root:

    python research_v2/ieee_experiments/architecture_ablation.py

The only result artifact written by this script is
``research_v2/ieee_results/architecture_ablation.csv``.  Original corrected
benchmark artifacts under ``research_v2/results`` are never overwritten.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import time
from pathlib import Path
from typing import Callable

# Set before TensorFlow is imported, matching the deterministic settings used
# by the corrected Bi-LSTM benchmark.
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_DETERMINISTIC_OPS", "1")

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler


# ``protocol.py`` and its historical dependencies use sibling absolute
# imports.  Adding research_v2 makes this module work both when executed by
# path from the repository root and when imported as a package module.
RESEARCH_ROOT = Path(__file__).resolve().parents[1]
if str(RESEARCH_ROOT) not in sys.path:
    sys.path.insert(0, str(RESEARCH_ROOT))

from baseline_evaluation import DATASETS, metrics  # noqa: E402
from bilstm_evaluation import build_model as build_reference_bilstm  # noqa: E402
from protocol import prepare  # noqa: E402


OUTPUT_FILE = RESEARCH_ROOT / "ieee_results" / "architecture_ablation.csv"
SEED = 42
MAX_EPOCHS = 20
BATCH_SIZE = 64
PATIENCE = 5
SEED_SCOPE = "seed_42_first_pass_only"
SEED_LIMITATION = (
    "Seed 42 only: this first-pass ablation cannot establish a seed-robust "
    "architecture ranking; no architecture was tuned against test results."
)
SCALER_POLICY = "MinMaxScaler fit only on raw fitting-region target rows"


def build_lstm(lookback: int, horizon: int) -> tf.keras.Model:
    """Build the pre-declared unidirectional counterpart to the Bi-LSTM.

    Layer widths, normalization, dropout, dense head, optimizer, and training
    budget are intentionally not architecture-specific tuning knobs.  Only
    bidirectionality differs from the current benchmark family.
    """

    return tf.keras.Sequential(
        [
            tf.keras.Input(shape=(lookback, 1)),
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
        ],
        name="lstm_unidirectional_reference",
    )


def build_bilstm(lookback: int, horizon: int) -> tf.keras.Model:
    """Build the exact current corrected-benchmark Bi-LSTM family.

    Importing the existing builder rather than reproducing its layers here
    prevents silent architectural drift between the corrected benchmark and
    this ablation.
    """

    return build_reference_bilstm(lookback, horizon)


ARCHITECTURES: tuple[tuple[str, str, Callable[[int, int], tf.keras.Model]], ...] = (
    (
        "LSTM",
        "LSTM(128)-BN-Dropout(0.2)-LSTM(64)-BN-Dropout(0.3)-"
        "LSTM(32)-Dense(64,relu)-Dropout(0.2)-Dense(horizon)",
        build_lstm,
    ),
    (
        "Bi-LSTM",
        "Exact current benchmark family from bilstm_evaluation.build_model: "
        "BiLSTM(128)-BN-Dropout(0.2)-BiLSTM(64)-BN-Dropout(0.3)-"
        "LSTM(32)-Dense(64,relu)-Dropout(0.2)-Dense(horizon)",
        build_bilstm,
    ),
)


def set_reproducible_seed(seed: int) -> None:
    """Reset all relevant random generators before each fixed-seed fit."""

    random.seed(seed)
    np.random.seed(seed)
    tf.keras.utils.set_random_seed(seed)


def scale_from_fitting_region(
    values: np.ndarray, X: np.ndarray, y: np.ndarray, fitting_end_row: int
) -> tuple[MinMaxScaler, np.ndarray, np.ndarray]:
    """Fit the scaler on raw fitting data only, then transform all windows.

    Transforming validation and test windows with a training-fitted scaler is
    permitted; fitting on them is not.  This function deliberately receives
    the fitting boundary from the committed protocol metadata rather than
    deriving a new split.
    """

    scaler = MinMaxScaler().fit(values[:fitting_end_row, None])
    X_scaled = scaler.transform(X.reshape(-1, 1)).reshape(*X.shape, 1).astype("float32")
    y_scaled = scaler.transform(y.reshape(-1, 1)).reshape(y.shape).astype("float32")
    return scaler, X_scaled, y_scaled


def origin_metadata(starts: np.ndarray, masks: dict[str, np.ndarray]) -> dict[str, int]:
    """Record raw-row forecast origins to make split identity auditable."""

    result: dict[str, int] = {}
    for split, mask in masks.items():
        split_origins = starts[mask]
        label = split.title()
        result[f"{label} first origin row"] = int(split_origins[0])
        result[f"{label} last origin row"] = int(split_origins[-1])
    return result


def run_one_architecture(
    *,
    dataset: str,
    architecture: str,
    architecture_definition: str,
    builder: Callable[[int, int], tf.keras.Model],
    X_scaled: np.ndarray,
    y_scaled: np.ndarray,
    y_raw: np.ndarray,
    masks: dict[str, np.ndarray],
    scaler: MinMaxScaler,
    metadata: dict,
    verbosity: int,
) -> dict:
    """Fit once using validation-only early stopping and evaluate test once."""

    tf.keras.backend.clear_session()
    set_reproducible_seed(SEED)
    model = builder(metadata["Lookback steps"], metadata["Horizon steps"])
    model.compile(optimizer="adam", loss="mse", metrics=["mae"])
    parameter_count = int(model.count_params())

    # Test labels are intentionally absent from fitting and callbacks.  The
    # only model-selection signal is validation loss under the fixed patience.
    started = time.monotonic()
    history = model.fit(
        X_scaled[masks["train"]],
        y_scaled[masks["train"]],
        validation_data=(X_scaled[masks["validation"]], y_scaled[masks["validation"]]),
        epochs=MAX_EPOCHS,
        batch_size=BATCH_SIZE,
        shuffle=False,
        verbose=verbosity,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(
                monitor="val_loss", patience=PATIENCE, restore_best_weights=True
            )
        ],
    )
    training_seconds = time.monotonic() - started

    prediction_scaled = model.predict(
        X_scaled[masks["test"]], batch_size=BATCH_SIZE, verbose=0
    )
    prediction = scaler.inverse_transform(prediction_scaled.reshape(-1, 1)).reshape(
        prediction_scaled.shape
    )
    truth = y_raw[masks["test"]]

    # Preserve the protocol fields verbatim and append ablation-specific
    # audit metadata.  Metrics are computed after inverse transformation, so
    # MAE/RMSE are in the physical unit recorded by ``Unit``.
    row = {
        **metadata,
        "Model": architecture,
        "Architecture definition": architecture_definition,
        "Model definition source": (
            "research_v2/bilstm_evaluation.py:build_model"
            if architecture == "Bi-LSTM"
            else "research_v2/ieee_experiments/architecture_ablation.py:build_lstm"
        ),
        "Seed": SEED,
        "Seed scope": SEED_SCOPE,
        "Seed limitation": SEED_LIMITATION,
        "Scaler policy": SCALER_POLICY,
        "Scaler fitting end row exclusive": int(metadata["Train end row exclusive"]),
        "Training budget": f"max_epochs={MAX_EPOCHS}; batch_size={BATCH_SIZE}; patience={PATIENCE}",
        "Max epochs": MAX_EPOCHS,
        "Batch size": BATCH_SIZE,
        "Patience": PATIENCE,
        "Shuffle": False,
        "Model parameters": parameter_count,
        "Training seconds": training_seconds,
        "Epochs run": int(len(history.history["loss"])),
        "Best epoch": int(np.argmin(history.history["val_loss"]) + 1),
        "Input shape": str(list(model.input_shape)),
        "Output shape": str(list(model.output_shape)),
        **metrics(truth, prediction),
    }
    print(
        f"{dataset} | {architecture} | parameters={parameter_count:,} | "
        f"MAE={row['MAE']:.6g} {metadata['Unit']} | training={training_seconds:.1f}s",
        flush=True,
    )
    return row


def run_dataset(dataset: str, verbosity: int = 2) -> list[dict]:
    """Run both pre-declared architectures on an identical protocol split."""

    X, y, masks, values, starts, _times, metadata = prepare(dataset)
    metadata = {
        **metadata,
        **origin_metadata(starts, masks),
        "Features": [DATASETS[dataset]["target_col"]],
        "Feature configuration": "F0 target history only",
        "Ablation comparison": "LSTM versus exact current Bi-LSTM family",
    }
    scaler, X_scaled, y_scaled = scale_from_fitting_region(
        values, X, y, metadata["Train end row exclusive"]
    )
    return [
        run_one_architecture(
            dataset=dataset,
            architecture=architecture,
            architecture_definition=definition,
            builder=builder,
            X_scaled=X_scaled,
            y_scaled=y_scaled,
            y_raw=y,
            masks=masks,
            scaler=scaler,
            metadata=metadata,
            verbosity=verbosity,
        )
        for architecture, definition, builder in ARCHITECTURES
    ]


def configure_tensorflow(threads: int) -> None:
    """Apply the benchmark's thread/determinism settings before model use."""

    tf.config.threading.set_intra_op_parallelism_threads(threads)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.config.experimental.enable_op_determinism()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--threads",
        type=int,
        default=4,
        help="TensorFlow intra-op threads (default: 4; does not alter the model protocol).",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress per-epoch Keras output."
    )
    args = parser.parse_args()
    if args.threads < 1:
        parser.error("--threads must be positive")

    configure_tensorflow(args.threads)
    print(
        "Architecture-ablation scope: seed 42 only. Results are a first-pass "
        "comparison, not a seed-robust architecture ranking.",
        flush=True,
    )
    print(
        "Fixed protocol: raw chronological origins; train-only scaling; "
        "168 h history; 24 h horizon; no shuffle; 20-epoch cap; batch size 64; "
        "validation early stopping patience 5.",
        flush=True,
    )

    rows: list[dict] = []
    for dataset in DATASETS:
        rows.extend(run_dataset(dataset, verbosity=0 if args.quiet else 2))

    # Write only after all fixed comparisons have completed, so an interrupted
    # run cannot be mistaken for a complete architecture-ablation result.
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUTPUT_FILE, index=False)
    print(f"Saved {len(rows)} rows to {OUTPUT_FILE}", flush=True)


if __name__ == "__main__":
    main()
