# Extended experiments

These experiments build on the corrected benchmark in [`BENCHMARK_REPORT.md`](BENCHMARK_REPORT.md). They test whether its conclusions hold under:

- more random seeds
- other architectures and feature sets
- a maintenance-style threshold-event evaluation
- dependence-aware uncertainty intervals
- an independent public dataset (NASA C-MAPSS FD001)

All designs, seeds, thresholds and splits were fixed before the runs. They are summarized in [`EXPERIMENT_PROTOCOL.md`](EXPERIMENT_PROTOCOL.md). Result files are in [`ieee_results/`](ieee_results/); see [`ieee_results/README.md`](ieee_results/README.md) for a description of each file.

## Summary

- **Seeds.** With five seeds, the Bi-LSTM's mean MAE is still well above the best baseline on every AutoSense target.
- **Architecture.** Neither LSTM nor Bi-LSTM is better on all targets.
- **Features.** Extra causal features help some model/target pairs and hurt others.
- **Threshold events.** The Bi-LSTM does not detect proxy threshold events usefully.
- **Bootstrap.** Block-bootstrap intervals favour the best baseline over the Bi-LSTM on all three targets.
- **C-MAPSS.** On the independent simulated benchmark, Random Forest, LSTM and Bi-LSTM perform almost the same. Errors are larger late in engine life.

## 1. How the results were accepted

The neural runs were trained on Kaggle GPUs. The raw output archives are kept unchanged in [`kaggle/`](kaggle/). [`validate_final_result_archives.py`](validate_final_result_archives.py) re-checks each archive without rerunning anything. It verifies:

- archive SHA256, expected files and row counts, and unique keys
- script, data and protocol hashes, and fixed model settings
- C-MAPSS engine separation and that every prediction file contains only test engines
- that each result file copied into `ieee_results/` is byte-identical to its archive copy

The Kaggle runs did not all use the same software versions:

| Run | TensorFlow | scikit-learn | Status |
|---|---:|---:|---|
| AutoSense five-seed Bi-LSTM | 2.18.0 | 1.9.0 | Accepted |
| Architecture ablation | 2.18.0 | 1.9.0 | Accepted |
| C-MAPSS FD001 forecasting | 2.20.0 | 1.6.1 | Accepted with environment deviation |
| C-MAPSS stage analysis | 2.18.0 | 1.9.0 | Accepted; uses forecasts made under 2.20.0 / 1.6.1 |
| Feature ablation | 2.20.0 | 1.6.1 | Accepted with environment deviation |

The original plan pinned TensorFlow 2.18.0 and scikit-learn 1.9.0. A strict check against that pin ([`ieee_results/final_integration_validation.json`](ieee_results/final_integration_validation.json)) rejected the C-MAPSS and feature-ablation runs *only* because of their versions; their structure passed every check. These runs were then accepted, by an explicit decision, without rerunning. The version difference is reported as a reproducibility limitation instead of a uniform environment being claimed. The acceptance record is [`ieee_results/accepted_integration_validation.json`](ieee_results/accepted_integration_validation.json). The five-seed rows also record NumPy 2.0.2 and pandas 2.2.2. Other runs did not record those packages, so their versions are not stated here.

## 2. Five-seed Bi-LSTM robustness

Seeds 11, 21, 42, 84 and 168; every other setting is identical to the benchmark ([`ieee_results/multiseed_summary.csv`](ieee_results/multiseed_summary.csv)).

| Target | MAE (mean ± sd) | RMSE (mean ± sd) | R² (mean ± sd) | Best baseline MAE |
|---|---:|---:|---:|---:|
| Engine temperature | 5.182 ± 0.665 °C | 6.343 ± 0.655 °C | 0.531 ± 0.099 | 1.708 °C (Random Forest) |
| Tyre pressure | 1.256 ± 0.221 PSI | 1.532 ± 0.260 PSI | 0.510 ± 0.164 | 0.558 PSI (Persistence) |
| Tyre temperature | 5.731 ± 0.889 °C | 7.030 ± 1.082 °C | −0.835 ± 0.536 | 2.897 °C (Random Forest) |

These figures show how much results vary between training seeds. They are not repeated-split validation or confidence intervals.

## 3. Architecture ablation: LSTM vs Bi-LSTM

Seed 42. The LSTM is the one-directional counterpart of the benchmark Bi-LSTM (same layer sizes) ([`ieee_results/architecture_ablation.csv`](ieee_results/architecture_ablation.csv)).

| Target | Model | MAE | RMSE | R² | Epochs (best) |
|---|---|---:|---:|---:|---:|
| Engine temperature (°C) | LSTM | 9.539 | 11.776 | −0.604 | 6 (1) |
| | Bi-LSTM | **6.199** | 7.356 | 0.374 | 11 (6) |
| Tyre pressure (PSI) | LSTM | 1.298 | 1.556 | 0.506 | 20 (19) |
| | Bi-LSTM | **1.182** | 1.439 | 0.577 | 20 (20) |
| Tyre temperature (°C) | LSTM | **4.402** | 5.325 | −0.034 | 11 (6) |
| | Bi-LSTM | 6.366 | 7.758 | −1.194 | 9 (4) |

The Bi-LSTM has lower error on the first two targets and the LSTM on the third. With one seed this is not an architecture ranking, and both models remain worse than the best baseline.

## 4. Causal feature ablation

Seed 42, Random Forest and LSTM ([`ieee_results/feature_ablation.csv`](ieee_results/feature_ablation.csv)). Feature sets:

- **F0**: target history only (the benchmark setting).
- **F1**: F0 plus calendar features: sine and cosine of hour, day of week and month.
- **F2**: F1 plus a true 24-hour lag and a trailing 72-hour mean, both measured in clock time and using past values only.

Early windows without enough history for F2 are dropped; no test forecast origin is lost.

| Target | Model | F0 | F1 | F2 |
|---|---|---:|---:|---:|
| Engine temperature (°C) | Random Forest | 1.709 | 1.710 | **1.673** |
| | LSTM | 9.539 | 7.127 | **5.142** |
| Tyre pressure (PSI) | Random Forest | **0.736** | 0.803 | 0.836 |
| | LSTM | **1.212** | 2.401 | 2.279 |
| Tyre temperature (°C) | Random Forest | 2.897 | 5.040 | **2.757** |
| | LSTM | **4.394** | 4.531 | 4.598 |

Feature effects depend on the target and the model. F2 helps engine temperature for both models, hurts tyre pressure, and gives mixed results for tyre temperature. This run used TensorFlow 2.20.0. Its F0 LSTM values therefore differ slightly from the architecture-ablation LSTM for the tyre targets (1.212 vs 1.298 PSI, 4.394 vs 4.402 °C), even though the settings are the same.

## 5. Proxy threshold-event evaluation

Accuracy metrics alone do not show whether forecasts would trigger useful alerts. Each forecast origin is therefore scored as an event if any value in the next 24 hours crosses a threshold. The thresholds are percentiles of the training data only:

| Target | Rule | Threshold(s) |
|---|---|---|
| Engine temperature | above 95th percentile | 107.8 °C |
| Tyre pressure | below 5th or above 95th percentile | 28.97 PSI / 34.87 PSI |
| Tyre temperature | above 95th percentile | 40.13 °C |

These are **statistical proxy thresholds, not engineering or safety limits**, and the events are not component failures ([`ieee_results/threshold_event_metrics.csv`](ieee_results/threshold_event_metrics.csv), [`threshold_event_confusions.csv`](ieee_results/threshold_event_confusions.csv)).

| Target (event rate) | Model | Precision | Recall | F1 | Specificity | Balanced accuracy |
|---|---|---:|---:|---:|---:|---:|
| Engine temperature (10.6%) | Persistence | 0.429 | 0.016 | 0.031 | 0.997 | 0.507 |
| | Seasonal naive | 0.400 | 0.348 | **0.372** | 0.938 | **0.643** |
| | Random Forest | 0 | 0 | 0 | 1.000 | 0.500 |
| | Bi-LSTM | 0 | 0 | 0 | 1.000 | 0.500 |
| Tyre pressure (47.9%) | Persistence | 0.974 | 0.801 | 0.879 | 0.980 | 0.891 |
| | Seasonal naive | 0.881 | 0.906 | **0.893** | 0.887 | **0.897** |
| | Random Forest | 0.994 | 0.588 | 0.739 | 0.997 | 0.793 |
| | Bi-LSTM | 0 | 0 | 0 | 1.000 | 0.500 |
| Tyre temperature (67.0%) | Persistence | 0.800 | 0.176 | 0.288 | 0.911 | 0.543 |
| | Seasonal naive | 0.763 | 0.775 | 0.769 | 0.513 | **0.644** |
| | Random Forest | 0 | 0 | 0 | 1.000 | 0.500 |
| | Bi-LSTM | 0.670 | 1.000 | **0.802** | 0 | 0.500 |

- **Bi-LSTM fails.** It predicts no event at all for engine temperature and tyre pressure. For tyre temperature it predicts an event at every origin: its F1 of 0.802 only reflects the 67.0% event rate, with specificity 0, so it does not separate events from non-events.
- **Random Forest misses temperature events.** Although it has the lowest temperature MAE, its forecasts never cross the temperature thresholds.
- **Seasonal naive does best.** It is the most balanced alert source on all three targets.

## 6. Moving-block bootstrap intervals

Test windows overlap, so ordinary independent-sample tests do not apply. The intervals below come from a moving-block bootstrap over forecast origins. It uses 2,000 replications, seed 42, and non-circular contiguous blocks of 48 hours (48 hourly origins or 16 three-hourly origins). The statistic is MAE(A) − MAE(B); a negative value favours model A ([`ieee_results/bootstrap_mae_differences.csv`](ieee_results/bootstrap_mae_differences.csv)).

| Target | A vs B | Observed | 95% interval |
|---|---|---:|---|
| Engine temperature | Random Forest vs Bi-LSTM | −4.491 °C | [−5.033, −3.955] |
| | Random Forest vs Persistence | −8.449 °C | [−8.563, −8.327] |
| Tyre pressure | Persistence vs Bi-LSTM | −0.619 PSI | [−0.845, −0.356] |
| | Random Forest vs Persistence | +0.177 PSI | [+0.078, +0.261] |
| Tyre temperature | Random Forest vs Bi-LSTM | −3.557 °C | [−3.732, −3.392] |
| | Random Forest vs Persistence | −2.889 °C | [−3.014, −2.754] |

The best-baseline-versus-Bi-LSTM comparisons were declared in advance. All six intervals exclude zero. The best baseline beats the Bi-LSTM on every target. Random Forest beats persistence on both temperatures but not on tyre pressure. These intervals take the dependence between windows into account. They are not independent-sample significance tests, and they say nothing about maintenance benefit.

## 7. External benchmark: NASA C-MAPSS FD001

**Data.** C-MAPSS FD001 is a public, **simulator-generated** turbofan-degradation dataset (Saxena and Goebel, 2008). It is not measured flight telemetry. Only `train_FD001.txt` is used: its 100 engines run to failure, so complete future trajectories exist. The source URL, access date and file hashes are in [`ieee_results/provenance.json`](ieee_results/provenance.json). The raw files are not committed; see [`external_data/cmapss/README.md`](external_data/cmapss/README.md). This study **forecasts sensor values; it does not estimate remaining useful life (RUL)**.

**Split.** Engines are assigned by a seed-42 permutation: 70 train, 15 validation and 15 test. No engine appears in two partitions ([`ieee_results/cmapss_fd001_split.json`](ieee_results/cmapss_fd001_split.json)). The test engines are 9, 13, 14, 15, 20, 23, 36, 37, 42, 48, 54, 65, 66, 67 and 78.

**Sensor selection** (training engines only; [`ieee_results/cmapss_sensor_selection.csv`](ieee_results/cmapss_sensor_selection.csv)):

1. Near-constant sensors are removed (14 of 21 sensors remain).
2. The remaining sensors are ranked by the median, across training engines, of the absolute Spearman correlation between sensor value and cycle.

The top four are sensor 9 (0.826), sensor 11 (0.813), sensor 14 (0.811) and sensor 12 (0.803).

**Task.** Each model takes 30 cycles of history and forecasts the next 10 cycles of one sensor. There are two input settings:

- **C0**: the target sensor's own history.
- **C1**: three operational settings plus the four selected sensors.

Scalers are fitted on training engines only. Metrics are normalized and macro-averaged over the four sensors ([`ieee_results/cmapss_fd001_metrics.csv`](ieee_results/cmapss_fd001_metrics.csv)).

| Input | Model | Seed | Normalized MAE | Normalized RMSE | R² |
|---|---|---:|---:|---:|---:|
| C0 | Persistence | – | 0.04722 | 0.05988 | 0.785 |
| | Random Forest | 42 | **0.03472** | **0.04362** | **0.884** |
| | LSTM | 42 | 0.03582 | 0.04490 | 0.877 |
| | Bi-LSTM | 11 / 42 / 84 | 0.03543 / 0.03574 / 0.03654 | 0.04442 / 0.04481 / 0.04582 | 0.880 / 0.878 / 0.872 |
| C1 | Random Forest | 42 | **0.03406** | **0.04278** | **0.889** |
| | LSTM | 42 | 0.03460 | 0.04341 | 0.886 |
| | Bi-LSTM | 11 / 42 / 84 | 0.03499 / 0.03483 / 0.03505 | 0.04387 / 0.04366 / 0.04393 | 0.885 / 0.885 / 0.884 |

- **Models are close.** On this dataset all learned models beat persistence. Their normalized MAE lies within about 5% of each other for C0 and 3% for C1.
- **Random Forest is lowest.** It has the lowest error, but the margin is small.
- **Multivariate input helps slightly.** C1 is slightly better than C0.

Per-sensor results by horizon are in [`cmapss_fd001_horizon_metrics.csv`](ieee_results/cmapss_fd001_horizon_metrics.csv), and the Bi-LSTM seed summary is in [`cmapss_multiseed_summary.csv`](ieee_results/cmapss_multiseed_summary.csv).

## 8. C-MAPSS error by degradation stage

The held-out forecasts are grouped by how far each engine is through its life (cycle ÷ final cycle): early (< 0.5), mid (0.5 to < 0.8) and late (≥ 0.8). The bins were fixed in advance. Remaining life is used only for this grouping, never as a prediction target ([`ieee_results/cmapss_stage_metrics.csv`](ieee_results/cmapss_stage_metrics.csv), 132 rows).

MAE in raw sensor units, input setting C1, seed 42:

| Sensor | Model | Early | Mid | Late |
|---|---|---:|---:|---:|
| sensor 9 | Random Forest | 3.394 | 3.631 | 4.052 |
| | LSTM | 3.692 | 3.799 | 4.211 |
| | Bi-LSTM | 3.583 | 3.719 | 4.242 |
| sensor 11 | Random Forest | 0.084 | 0.085 | 0.091 |
| | LSTM | 0.087 | 0.086 | 0.089 |
| | Bi-LSTM | 0.087 | 0.086 | 0.088 |
| sensor 12 | Random Forest | 0.244 | 0.261 | 0.271 |
| | LSTM | 0.249 | 0.260 | 0.267 |
| | Bi-LSTM | 0.245 | 0.262 | 0.270 |
| sensor 14 | Random Forest | 2.728 | 2.785 | 2.990 |
| | LSTM | 2.838 | 2.872 | 2.919 |
| | Bi-LSTM | 2.968 | 3.112 | 3.363 |

Across all 44 model/sensor/seed/input combinations, late-life MAE is higher than early-life MAE in 41. Forecasting gets harder as engines degrade, for every model type.

## 9. Limitations

- **AutoSense data.** The series are synthetic. There is no real-fleet validation, no failure or RUL target, no certified alert performance and no measured downtime reduction.
- **C-MAPSS.** It is simulator output, not physical flight telemetry.
- **Software versions.** The C-MAPSS and feature-ablation runs used different TensorFlow and scikit-learn versions from the other runs.
- **Seeds.** The architecture and feature ablations use one seed.
- **Planned but not reported.** The API-consistency and latency check (`ieee_experiments/api_consistency_and_latency.py`) has no committed results. The manuscript makes no latency or integration-reliability claim.

## 10. Manuscript

All results above are included in the manuscript ([`paper/build/main.pdf`](paper/build/main.pdf), 11 pages, built from [`paper/main.tex`](paper/main.tex)). The scripts [`ieee_experiments/generate_ieee_tables.py`](ieee_experiments/generate_ieee_tables.py) and [`generate_ieee_figures.py`](ieee_experiments/generate_ieee_figures.py) create its tables and figures directly from the result files. [`paper/tables/ieee_upgrade/asset_manifest.json`](paper/tables/ieee_upgrade/asset_manifest.json) records the input hashes. An earlier Overleaf archive, `paper_overleaf.zip`, held nothing newer than the paper sources. It has been removed from the repository; its hash remains in the two validation records.
