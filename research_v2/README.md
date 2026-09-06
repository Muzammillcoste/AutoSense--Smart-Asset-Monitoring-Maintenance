# Research V2: reproducible sensor forecasting

This experiment evaluates multi-step sensor forecasts for threshold-based maintenance. It does not evaluate failure prediction, remaining useful life, operational downtime reduction, or real-fleet deployment.

## Run from PowerShell

From the repository root, using the existing Python 3.11 environment:

```powershell
.venv/Scripts/python.exe -m unittest discover -s research_v2 -p test_protocol.py -v
.venv/Scripts/python.exe research_v2/verify_generators.py
.venv/Scripts/python.exe research_v2/audit_uae_legacy.py
.venv/Scripts/python.exe -u research_v2/audit_originals.py
.venv/Scripts/python.exe -u research_v2/bilstm_evaluation.py
```

`bilstm_evaluation.py` regenerates the baselines, trains all three models, saves predictions/models/scalers/history, and produces the final comparison. Each run overwrites its research results and invalidates prior completion tables/reports at startup. The report builder requires verification of the exact final comparison file by SHA256. Original notebooks and models are never modified. To run only the corrected baselines:

```powershell
.venv/Scripts/python.exe research_v2/baseline_evaluation.py
```

Dependencies for reproducing this environment are in `requirements.txt`; no installation was needed for the recorded run. Full environment details are in `results/environment.json`. CPU training takes substantially longer than inference. Defaults are 20 maximum epochs, batch size 64, four intra-op threads and one inter-op thread. Flags: `--epochs`, `--batch-size`, `--threads`. Set budgets before viewing test results; changing them creates a different experiment.

## Corrected protocol

`protocol.py` supplies identical windows and masks to every model. For N raw rows, test starts at floor(0.8*N), and validation starts at floor(0.85*floor(0.8*N)). Training uses approximately the first 68%, validation the next 12%, and testing the final 20%. Random Forest and Bi-LSTM fit on the same first region. Random Forest settings are fixed, and it does not use validation for tuning or refitting. This sacrifices some fitting data to make training exposure equal.

A window belongs to a partition only when its entire target horizon lies inside that partition. Boundary-crossing target windows are discarded. Inputs may contain earlier observations, including observations from the test period once they are available at a later forecast origin. This is rolling-origin evaluation with fixed weights, not a single forecast made at the beginning of the test period. Within-test forecast windows overlap, so errors are dependent; no independent-sample significance claim is made.

The previous baseline split 80/20 **after** making overlapping windows. Its last training target window and first test target window shared 23 engine targets or 7 tyre targets. Those former baseline numbers must not be combined with the corrected experiment. The corrected test boundary is based on raw timestamps and differs from the former window-based boundary.

Inputs are historical target values only, for both learned models. This deliberately changes the original 11-feature setup and isolates a common univariate benchmark; conclusions apply to this configuration, not every possible engineered-feature Bi-LSTM. Persistence repeats the last observation; seasonal naive repeats the previous day. The Bi-LSTM uses the original family: bidirectional LSTM(128), batch normalization, dropout(.2), bidirectional LSTM(64), batch normalization, dropout(.3), LSTM(32), Dense(64, relu), dropout(.2), Dense(horizon). Both bidirectional layers operate solely inside the observed past window.

MinMaxScaler fits only on raw fitting-region values. Training uses MSE/MAE, Adam, no shuffling, seed 42, deterministic TensorFlow operations and early stopping (validation loss, patience 5, best weights restored). No architecture or hyperparameter is selected against test scores. Reproducibility across other hardware/library versions is not guaranteed bit for bit.

Timestamps must be ordered, unique, complete and regularly spaced. Invalid data are rejected instead of silently dropped, deduplicated or resampled. Engine has hourly cadence: 168 input steps and 24 output steps. Tyres have three-hour cadence: 56 input steps and 8 output steps. Every final MAE and RMSE is in degrees Celsius or PSI after inverse scaling; R2 is dimensionless. Aggregate metrics flatten all origin/horizon pairs, and horizon-wise metrics keep each lead separate.

## Outputs

- `results/final_comparison.csv`: all four models and three datasets, including split metadata.
- `results/baseline_metrics.csv`, `results/bilstm_metrics.csv`, `results/bilstm_horizon_metrics.csv`.
- `results/<dataset>/`: saved model, scaler parameters, test truth/predictions, forecast starting rows, training history, metadata and dataset SHA256.
- `results/uae_legacy_audit.json`: direct reproduction of the older UAE engine result after in-memory Keras compatibility migration.
- `results/legacy_model_audit.json`: separately reproduced original evaluations; **not** aligned benchmark results.
- `results/notebook_evidence.json`: notebook source with zero-based cell references and stored text outputs.
- `AUDIT.md`: interpretation and provenance limitations.
- `REPORT_FOR_CHATGPT_REVIEW.md`: complete experiment report when the run finishes.

Saved `scaler.npz` arrays implement `scaled = raw * scale + min`; invert with `(scaled - min) / scale`. `test_predictions.npz` stores rows in source CSV order. Reload `model.keras` with `tf.keras.models.load_model(path, compile=False)` and provide shape `(windows, lookback_steps, 1)`.

## Data provenance

All three datasets have local synthetic generators, including `Tyre Temperature/generating_data.ipynb`. `verify_generators.py` reproduces all timestamps and target values to floating-point precision (maximum difference below 1.5e-14). None is real operational aviation-fleet data. The 2024 files end at midnight on December 31 rather than covering that entire final day.

Do not revise the paper until experiment results and the audit have been reviewed.
