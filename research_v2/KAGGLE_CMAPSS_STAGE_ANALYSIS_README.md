# Kaggle: NASA C-MAPSS FD001 degradation-stage analysis

Run this only after C-MAPSS forecasting has completed and its output ZIP has
been downloaded.

## Upload and attach

Create one private Kaggle Dataset containing these two files, unchanged:

- `research_v2/kaggle_cmapss_stage_analysis_input_bundle.zip`
- `cmapss_fd001_forecasting_results.zip` downloaded from the forecasting run

Attach that Dataset in Kaggle's Input panel. GPU is optional because this
phase does not train models; it only checks and stratifies stored held-out
forecasts.

## Run

Import and run
`research_v2/ieee_experiments/kaggle_cmapss_stage_analysis.ipynb` in order.
It checks the stage script, plan, NASA FD001, split hashes, and all 44 expected
forecast artifacts before calculating the fixed early/mid/late normalized-life
bins. It expects exactly 132 output rows.

Download `cmapss_stage_analysis_results.zip` and extract into
`research_v2/ieee_results/`:

- `cmapss_stage_metrics.csv`
- `kaggle_cmapss_stage_analysis_run_manifest.json`
