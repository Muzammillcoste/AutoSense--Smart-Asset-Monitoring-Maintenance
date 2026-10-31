# Corrected benchmark results

Outputs of the main benchmark ([`../BENCHMARK_REPORT.md`](../BENCHMARK_REPORT.md)) and of the audit of the original results ([`../AUDIT.md`](../AUDIT.md)). These files are the evidence behind the manuscript's main results table, so they are not edited by hand.

Files are created by:

- [`../bilstm_evaluation.py`](../bilstm_evaluation.py) and [`../baseline_evaluation.py`](../baseline_evaluation.py), for the benchmark
- [`../audit_originals.py`](../audit_originals.py) and [`../audit_uae_legacy.py`](../audit_uae_legacy.py), for the audit
- [`../verify_generators.py`](../verify_generators.py) and [`../verify_results.py`](../verify_results.py), for the checks

Rerunning `bilstm_evaluation.py` overwrites the benchmark files here.

## Metrics

| File | Contents |
|---|---|
| `final_comparison.csv` | All four models on all three targets: MAE, RMSE and R² in physical units, plus split metadata and dataset hashes. This is the main results table. |
| `mae_comparison.csv` | Best baseline vs Bi-LSTM MAE and the percentage change. |
| `baseline_metrics.csv` | Persistence, seasonal naive and Random Forest metrics with split metadata. |
| `bilstm_metrics.csv` | Bi-LSTM metrics with split metadata and training details. |
| `bilstm_horizon_metrics.csv` | Bi-LSTM MAE, RMSE and R² at each lead time. |

## Per-target folders

Folders `engine_temperature/`, `tyre_pressure/` and `tyre_temperature/` each contain the files below.

| File | Contents |
|---|---|
| `model.keras` | Trained Bi-LSTM. Load it with `tf.keras.models.load_model(path, compile=False)`; the input shape is `(windows, lookback_steps, 1)`. |
| `scaler.npz` | MinMax scaler arrays `scale`, `min`, `data_min` and `data_max`, where `scaled = raw * scale + min` and `raw = (scaled - min) / scale`. |
| `test_predictions.npz` | `truth` and `prediction` in physical units, plus `target_start_rows` (the first target row of each window in the source CSV). Rows are in source-CSV order. |
| `training_history.csv` | Training and validation loss and MAE for each epoch. |
| `metadata.json` | Protocol version, dataset path and SHA256, cadence, window lengths, partition rows and dates, and training settings. |
| `metrics.csv`, `horizon_metrics.csv` | Bi-LSTM metrics for this target, aggregated and by lead time. |

## Environment, checks and audit evidence

| File | Contents |
|---|---|
| `environment.json`, `environment_freeze.txt` | Python and package versions of the recorded run, and the full `pip freeze`. |
| `source_hashes.json` | SHA256 hashes of the benchmark source files used for the run. |
| `verification.json` | Output of `verify_results.py`: metrics recomputed from the saved forecasts, a target check, split consistency and model reloads. |
| `generator_verification.json` | Output of `verify_generators.py`: the generator notebooks reproduce the three CSVs. |
| `notebook_evidence.json` | Source and saved outputs of the original notebooks; cell numbers are zero-based. |
| `legacy_model_audit.json` | Reproduced evaluations of the original saved models. They are **not** benchmark results. |
| `uae_legacy_audit.json` | Reproduction of the older UAE engine result behind the original 0.1795 value. |
