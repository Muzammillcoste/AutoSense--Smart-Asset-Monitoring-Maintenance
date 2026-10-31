# Extended-experiment results

Outputs of the experiments reported in [`../EXTENDED_EXPERIMENTS.md`](../EXTENDED_EXPERIMENTS.md), together with their provenance records. The folder keeps its original name because the scripts and recorded file paths refer to it.

Files from Kaggle runs are byte-identical copies of the archives in [`../kaggle/`](../kaggle/); [`../validate_final_result_archives.py`](../validate_final_result_archives.py) checks this.

## AutoSense experiments

| File | Experiment | Produced by |
|---|---|---|
| `multiseed_bilstm_metrics.csv` | Bi-LSTM metrics for each target and seed (5 seeds × 3 targets) | `multiseed_bilstm.py` (Kaggle) |
| `multiseed_summary.csv` | Mean and standard deviation across seeds | `multiseed_bilstm.py` (Kaggle) |
| `architecture_ablation.csv` | LSTM vs Bi-LSTM, seed 42 | `architecture_ablation.py` (Kaggle) |
| `feature_ablation.csv` | F0/F1/F2 feature sets × Random Forest/LSTM | `feature_ablation.py` (Kaggle) |
| `threshold_event_thresholds.json` | Proxy thresholds derived from training data | `threshold_event_evaluation.py` |
| `threshold_event_metrics.csv` | Precision, recall, F1, specificity and lead time per model | `threshold_event_evaluation.py` |
| `threshold_event_confusions.csv` | Confusion-matrix counts | `threshold_event_evaluation.py` |
| `threshold_event_predictions/<target>/baseline_predictions.npz` | Baseline forecasts used for event scoring | `threshold_event_evaluation.py` |
| `bootstrap_mae_differences.csv` | Moving-block bootstrap intervals for MAE differences | `bootstrap_comparison.py` |

## NASA C-MAPSS FD001

| File | Contents |
|---|---|
| `provenance.json` | NASA source URL, access date, archive and file hashes, citation, usage note, and the commit the work started from |
| `cmapss_fd001_split.json` | Engine split fixed before training (70/15/15, seed 42) |
| `cmapss_sensor_selection.csv` | Sensor variance filter and Spearman ranking (training engines only) |
| `cmapss_fd001_metrics.csv` | Per-sensor and macro-averaged metrics for each input setting, model and seed |
| `cmapss_fd001_horizon_metrics.csv` | Metrics at each of the 10 forecast cycles |
| `cmapss_multiseed_summary.csv` | Bi-LSTM mean and standard deviation over seeds 11, 42 and 84 |
| `cmapss_fd001_predictions/*.npz` | 44 prediction files: truth, prediction, engine IDs, start cycles and provenance hashes |
| `cmapss_stage_metrics.csv` | Error by degradation stage (early/mid/late life) |

The split and sensor-selection files were saved before any model was trained. Their SHA256 hashes are recorded in every C-MAPSS result row, so they must not be changed.

## Run records and validation ledgers

| File | Contents |
|---|---|
| `kaggle_*_run_manifest.json` | Kaggle environment and input-file hashes for each run |
| `final_integration_validation.json` | Strict check against the originally pinned environment (TensorFlow 2.18.0, scikit-learn 1.9.0). It rejects the C-MAPSS and feature runs *only* because their versions differ; they are structurally valid. |
| `accepted_integration_validation.json` | Acceptance record: every archive accepted in its recorded environment, with the deviations noted |

Both ledgers also list `paper_overleaf.zip`. That redundant archive has since been removed; the ledgers are kept unchanged as historical records. Similarly, `provenance.json` refers to `REPORT_FOR_CHATGPT_REVIEW.md`, the earlier name of [`../BENCHMARK_REPORT.md`](../BENCHMARK_REPORT.md).
