# Kaggle: NASA C-MAPSS FD001 forecasting

## Upload and attach

Create a private Kaggle Dataset containing exactly
`research_v2/kaggle_cmapss_fd001_forecasting_input_bundle.zip`, and attach it
as a notebook Input. The bundle contains the authoritative NASA
`train_FD001.txt`, committed 70/15/15 engine split, and pre-registered sensor
selection. Do not substitute a mirror or edit/unzip the bundle.

Enable a GPU accelerator. This is the heaviest prepared run: it fits C0/C1
models for four fixed sensors, including the declared three Bi-LSTM seeds.

## Run

Import and run
`research_v2/ieee_experiments/kaggle_cmapss_fd001_forecasting.ipynb` in order.
It validates the NASA data, execution-plan, split, and selection SHA256 hashes
before fitting. It enforces the fixed sensors `sensor_9`, `sensor_11`,
`sensor_14`, `sensor_12`, 30-cycle history, 10-cycle horizon, and engine
disjoint 70/15/15 partition.

Download `cmapss_fd001_forecasting_results.zip`. Extract into
`research_v2/ieee_results/`:

- `cmapss_fd001_metrics.csv`
- `cmapss_fd001_horizon_metrics.csv`
- `cmapss_multiseed_summary.csv`
- `cmapss_fd001_predictions/` (all 44 NPZ prediction artifacts)
- `kaggle_cmapss_fd001_forecasting_run_manifest.json`

The ZIP also contains copies of the registered split and selection for audit;
do not replace the committed copies unless their hashes match exactly.
