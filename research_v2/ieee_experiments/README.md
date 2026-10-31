# Extended-experiment scripts

These scripts produce the results in [`../EXTENDED_EXPERIMENTS.md`](../EXTENDED_EXPERIMENTS.md), following the design in [`../EXPERIMENT_PROTOCOL.md`](../EXPERIMENT_PROTOCOL.md). They write to [`../ieee_results/`](../ieee_results/) and never touch the corrected benchmark in [`../results/`](../results/).

The AutoSense scripts reuse the shared protocol ([`../protocol.py`](../protocol.py)), the baselines ([`../baseline_evaluation.py`](../baseline_evaluation.py)) and the Bi-LSTM definition ([`../bilstm_evaluation.py`](../bilstm_evaluation.py)).

The scripts record their own SHA256 hash in every output row, so do not edit them. The folder name is also kept, because recorded file paths refer to it.

## Scripts

| Script | What it does | Output (in `ieee_results/`) | Where it ran |
|---|---|---|---|
| `multiseed_bilstm.py` | Bi-LSTM with seeds 11, 21, 42, 84 and 168 (`--resume`, `--threads`, `--verbose`) | `multiseed_bilstm_metrics.csv`, `multiseed_summary.csv` | Kaggle GPU |
| `architecture_ablation.py` | LSTM vs Bi-LSTM, seed 42 (`--threads`, `--quiet`) | `architecture_ablation.csv` | Kaggle GPU |
| `feature_ablation.py` | F0/F1/F2 feature sets for Random Forest and LSTM | `feature_ablation.csv` | Kaggle GPU |
| `threshold_event_evaluation.py` | Proxy threshold-event scoring of all four models; refits the fixed baselines | `threshold_event_*.csv/json`, `threshold_event_predictions/` | CPU |
| `bootstrap_comparison.py` | Moving-block bootstrap of MAE differences, using saved forecasts | `bootstrap_mae_differences.csv` | CPU |
| `cmapss_fd001_forecasting.py` | C-MAPSS FD001 engine split, sensor selection and forecasting; `--prepare-only` stops after the split and selection | `cmapss_fd001_*`, `cmapss_multiseed_summary.csv`, `cmapss_sensor_selection.csv`, `cmapss_fd001_predictions/` | Kaggle GPU |
| `cmapss_stage_analysis.py` | C-MAPSS forecast error by degradation stage, using the saved predictions | `cmapss_stage_metrics.csv` | Kaggle |
| `api_consistency_and_latency.py`, `research_inference.py` | Planned check of an inference wrapper and its latency | none committed; not reported | not run |
| `generate_ieee_tables.py` | LaTeX result tables for the manuscript | `../paper/tables/ieee_upgrade/` | CPU |
| `generate_ieee_figures.py` | Grayscale-safe PDF/PNG figures for the manuscript | `../paper/figures/ieee_upgrade/` | CPU |

The `kaggle_*.ipynb` notebooks run the Kaggle scripts from the input bundles in [`../kaggle/`](../kaggle/); see [`../kaggle/README.md`](../kaggle/README.md).

## C-MAPSS requirements

- **Data.** The C-MAPSS scripts need the official NASA FD001 files in [`../external_data/cmapss/`](../external_data/cmapss/); see the README there.
- **Protocol file.** They also hash the original protocol file `research_v2/CODEX_IEEE_EXECUTION_PLAN.md`. On Kaggle the input bundle supplies it. To run locally, extract it from the bundle as described in [`../EXPERIMENT_PROTOCOL.md`](../EXPERIMENT_PROTOCOL.md).
