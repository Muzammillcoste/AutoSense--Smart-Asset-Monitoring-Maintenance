# Corrected benchmark report

This report covers the main experiment of the study: a single-seed, fixed-budget comparison of four models for 24-hour multi-step forecasting on three synthetic sensor series. It evaluates forecast accuracy only. It does not evaluate failure prediction, remaining useful life or any effect on maintenance downtime.

The extended experiments (more seeds, ablations, threshold events, bootstrap intervals, NASA C-MAPSS) are reported in [`EXTENDED_EXPERIMENTS.md`](EXTENDED_EXPERIMENTS.md). The audit of the metrics reported originally is in [`AUDIT.md`](AUDIT.md).

## 1. Results

Test-set metrics, seed 42 ([`results/final_comparison.csv`](results/final_comparison.csv)). MAE and RMSE are in physical units after inverse scaling; R² has no unit. Each value pools every forecast origin and every horizon step of the test partition.

| Target | Model | MAE | RMSE | R² |
|---|---|---:|---:|---:|
| Engine temperature (°C) | Persistence | 10.157 | 12.474 | −0.799 |
| | Seasonal naive (previous 24 h) | 2.623 | 3.449 | 0.862 |
| | **Random Forest** | **1.708** | **2.262** | **0.941** |
| | Bi-LSTM | 6.199 | 7.356 | 0.374 |
| Tyre pressure (PSI) | **Persistence** | **0.558** | **0.979** | **0.804** |
| | Seasonal naive (previous 24 h) | 0.781 | 1.241 | 0.686 |
| | Random Forest | 0.736 | 1.003 | 0.795 |
| | Bi-LSTM | 1.178 | 1.443 | 0.575 |
| Tyre temperature (°C) | Persistence | 5.786 | 7.105 | −0.840 |
| | Seasonal naive (previous 24 h) | 3.897 | 4.964 | 0.102 |
| | **Random Forest** | **2.897** | **3.680** | **0.507** |
| | Bi-LSTM | 6.454 | 7.862 | −1.253 |

### Bi-LSTM against the best baseline

Change in MAE = 100 × (baseline MAE − Bi-LSTM MAE) / baseline MAE. A negative value means the Bi-LSTM is worse ([`results/mae_comparison.csv`](results/mae_comparison.csv)).

| Target | Best baseline | Baseline MAE | Bi-LSTM MAE | Change in MAE |
|---|---|---:|---:|---:|
| Engine temperature | Random Forest | 1.708 °C | 6.199 °C | −262.9% |
| Tyre pressure | Persistence | 0.558 PSI | 1.178 PSI | −111.0% |
| Tyre temperature | Random Forest | 2.897 °C | 6.454 °C | −122.8% |

The Bi-LSTM has a higher MAE than the best baseline on all three targets. This result holds for the recorded configuration: one seed, one chronological test period, a fixed training budget and no hyperparameter search. It does not show that a Bi-LSTM could never do better. It also does not support any claim that one model is superior in general.

### Error by forecast horizon (Bi-LSTM MAE)

Full horizon-wise MAE, RMSE and R² are in [`results/bilstm_horizon_metrics.csv`](results/bilstm_horizon_metrics.csv); the baseline equivalents are in [`paper/data/baseline_horizon_metrics.csv`](paper/data/baseline_horizon_metrics.csv). The tyre series are 3-hourly, so they have values only every third hour.

| Lead (h) | Engine (°C) | Tyre pressure (PSI) | Tyre temperature (°C) |
|---:|---:|---:|---:|
| 1 | 4.053 | | |
| 2 | 4.882 | | |
| 3 | 4.968 | 0.959 | 7.218 |
| 4 | 4.318 | | |
| 5 | 5.204 | | |
| 6 | 5.923 | 1.130 | 7.220 |
| 7 | 5.698 | | |
| 8 | 6.842 | | |
| 9 | 6.852 | 1.077 | 5.337 |
| 10 | 7.690 | | |
| 11 | 7.346 | | |
| 12 | 7.663 | 1.156 | 4.977 |
| 13 | 8.300 | | |
| 14 | 8.353 | | |
| 15 | 8.406 | 1.178 | 7.749 |
| 16 | 7.426 | | |
| 17 | 6.521 | | |
| 18 | 6.971 | 1.272 | 8.633 |
| 19 | 6.538 | | |
| 20 | 5.974 | | |
| 21 | 5.487 | 1.264 | 5.886 |
| 22 | 4.364 | | |
| 23 | 4.584 | | |
| 24 | 4.423 | 1.386 | 4.609 |

Engine error peaks at 13–15 h and falls again towards 24 h. Tyre-pressure error mostly grows with lead time (0.959 PSI at 3 h, 1.386 PSI at 24 h). Tyre-temperature error varies with no clear trend.

## 2. Data and partitions

All three series are synthetic. The generator notebooks in the repository reproduce every timestamp and value to floating-point precision (maximum difference below 1.5 × 10⁻¹⁴; [`results/generator_verification.json`](results/generator_verification.json)). The tyre-temperature generator is `Tyre Temperature/generating_data.ipynb`. Dataset SHA256 hashes are stored in each experiment's metadata.

| Target | Rows | Interval | Input steps | Output steps | Train windows | Validation windows | Test windows |
|---|---:|---:|---:|---:|---:|---:|---:|
| Engine temperature | 8,761 | 1 h | 168 | 24 | 5,765 | 1,029 | 1,730 |
| Tyre pressure | 2,921 | 3 h | 56 | 8 | 1,922 | 344 | 578 |
| Tyre temperature | 2,921 | 3 h | 56 | 8 | 1,922 | 344 | 578 |

Every model gets seven days of history and forecasts the next 24 hours.

| Target | Train targets | Validation targets | Test targets |
|---|---|---|---|
| Engine temperature | 2024-01-08 00:00 – 2024-09-05 03:00 | 2024-09-05 04:00 – 2024-10-18 23:00 | 2024-10-19 00:00 – 2024-12-31 00:00 |
| Tyre pressure | 2024-01-08 00:00 – 2024-09-05 00:00 | 2024-09-05 03:00 – 2024-10-18 21:00 | 2024-10-19 00:00 – 2024-12-31 00:00 |
| Tyre temperature | 2024-01-08 00:00 – 2024-09-05 00:00 | 2024-09-05 03:00 – 2024-10-18 21:00 | 2024-10-19 00:00 – 2024-12-31 00:00 |

**How the split works** ([`protocol.py`](protocol.py)):

1. **Raw rows are split before any windowing.** For *N* rows, the test partition starts at row ⌊0.8 *N*⌋ and validation starts at ⌊0.85 ⌊0.8 *N*⌋⌋. That gives about 68% training, 12% validation and 20% test.
2. **Windows stay inside one partition.** A window is kept only if its whole target horizon lies inside one partition, so no target timestamp is shared between partitions.
3. **Evaluation uses a rolling origin with fixed weights.** A forecast may use earlier observations as input, including test observations that are already in the past at that forecast origin. The model is never retrained during the test period.
4. **Errors are dependent.** Test windows overlap, so the number of windows is not a count of independent samples.

**What changed from the earlier baseline script.** The earlier baseline split the data 80/20 *after* creating overlapping windows. The last training window and the first test window shared 23 engine target timestamps or 7 tyre target timestamps, so Random Forest saw labels from the start of its test period. That script also used a different test boundary. Its numbers are superseded and are not mixed with these results. In the corrected pipeline no test value enters fitting or scaling. Metadata and prediction checks confirm that all four models use the same windows.

## 3. Models and training

- **Inputs.** Both learned models use target history only (one feature), so the Random Forest and the Bi-LSTM receive identical information. The original 11-feature notebook setup is not used for the main benchmark.
- **Baselines.** Persistence repeats the last observed value. Seasonal naive repeats the values from 24 hours earlier.
- **Random Forest.** 300 trees, maximum depth 16, minimum 2 samples per leaf, seed 42. It is fitted on the training partition only; validation is not used to tune or refit it.
- **Bi-LSTM.** The architecture keeps the layer sizes of the original project:
  - Bidirectional LSTM(128, return sequences), batch normalization, dropout 0.2
  - Bidirectional LSTM(64, return sequences), batch normalization, dropout 0.3
  - LSTM(32), Dense(64, ReLU), dropout 0.2, Dense(horizon)

  Bidirectional processing runs over the observed input window only.
- **Training.** Adam optimizer, MSE loss and MAE metric (no classification metrics). MinMax scaling is fitted on the training region. Seed 42, no shuffling, deterministic TensorFlow operations, oneDNN disabled. Early stopping monitors validation loss with patience 5 and restores the best weights.
- **Budget.** A maximum of 20 epochs and a batch size of 64 were fixed before any test result was seen. Nothing was tuned on test scores.

| Target | Epochs run | Best epoch | Training time (s) |
|---|---:|---:|---:|
| Engine temperature | 11 | 6 | 1,213 |
| Tyre pressure | 20 | 20 | 339 |
| Tyre temperature | 9 | 4 | 177 |

For tyre pressure the best validation loss came at the 20-epoch cap, so that model may not have converged. More training might improve it. No change was made after the test scores were seen.

## 4. Original project models (for reference only)

The audit reloaded the three models saved by the original project and reproduced their stored notebook results. Their input shapes are engine (168, 11) → 24 and tyres (56, 11) → 8. Their scalers match a reconstruction of the notebook preprocessing. These are **legacy results on different test periods, features and splits**, so they are not part of the comparison above.

| Original model | Normalized MAE (reproduced) | Physical MAE | Setup |
|---|---:|---:|---|
| Karachi engine temperature | 0.03223978 | 1.734 °C | 80% training, 11 features, 1,546 test windows |
| Tyre pressure | 0.23684705 | 1.838 PSI | 10% training, 11 features, 2,501 test windows |
| Tyre temperature | 0.34135299 | 6.984 °C | 10% training, 11 features, 2,501 test windows |

The models were retrained for the benchmark for four reasons. Retraining gives every model the same training data and features. It removes the validation contamination found in the original notebooks. It lets the Random Forest and the Bi-LSTM use identical inputs. It also avoids mixing tyre models trained on 10% of the data with an engine model trained on 80%. The original tyre models already produced 8 outputs (24 hours at 3-hour cadence), so the horizon was not the problem. Two of their features had misleading names: `shift(24)` is a 72-hour lag, and `rolling(72)` covers nine days of 3-hourly samples.

[`AUDIT.md`](AUDIT.md) explains how the originally reported values (0.1795 °C, 0.2368 MPa and 0.344 °C) arose and what they correspond to in physical units.

## 5. Software environment

| Item | Version |
|---|---|
| Python | 3.11.9 |
| TensorFlow / Keras | 2.18.0 / 3.15.1 |
| NumPy / pandas | 2.0.2 / 2.2.2 |
| scikit-learn | 1.9.0 |
| h5py | 3.16.0 |
| Platform | Windows (10.0.26200), CPU only, 4 intra-op threads |

The full package list is in [`results/environment_freeze.txt`](results/environment_freeze.txt) and [`results/environment.json`](results/environment.json). The run emitted two warnings:

- **scikit-learn version.** Loading the original scalers warned about version 1.6.1 versus 1.9.0. All three scaler transformations were reconstructed independently and matched.
- **TensorFlow attribute.** TensorFlow warned about an unknown dataset-op attribute. The run completed and its saved predictions were verified.

Results are not guaranteed to be bit-for-bit identical on other hardware or library versions.

## 6. Verification

- **Protocol tests.** [`test_protocol.py`](test_protocol.py) passed 4 tests:
  - cadence, horizon and disjoint-label checks on the real data
  - rejection of invalid series
  - inverse-scaling to physical units
  - reproduction of the overlap flaw in the earlier baseline split
- **Result checks.** [`verify_results.py`](verify_results.py) recomputed every aggregate and horizon metric from the saved forecasts. It also checked the true targets against the source data, confirmed the common split and hash metadata, and reloaded all three saved models to reproduce example forecasts within floating-point tolerance. The output is in [`results/verification.json`](results/verification.json).

## 7. Limitations

- **Data.** All data are synthetic, there is no real-fleet validation, and no maintenance outcome was measured.
- **Seeds and partitions.** This report uses one seed and one chronological test period. Five-seed results are in [`EXTENDED_EXPERIMENTS.md`](EXTENDED_EXPERIMENTS.md).
- **Training budget.** The budget was limited and there was no hyperparameter search.
- **Uncertainty.** The errors are dependent, so this report gives no confidence intervals. Dependence-aware bootstrap intervals are reported separately.
- **Open question.** The source of the originally reported 0.344 °C tyre-temperature value is still unresolved.

## About this file

[`build_report.py`](build_report.py) generates the raw version of this report as `REPORT_FOR_CHATGPT_REVIEW.md`. The script's hash is recorded in [`results/source_hashes.json`](results/source_hashes.json), so its code (including that filename) is left unchanged. This file is the edited, human-readable version of that output, with the same numbers.
