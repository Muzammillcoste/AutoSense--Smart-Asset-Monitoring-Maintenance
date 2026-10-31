# Kaggle runs: input bundles and result archives

The extended experiments were trained on Kaggle GPUs. This folder holds, for
each run, the exact input bundle that was uploaded and the result archive that
was downloaded:

| Run | Input bundle | Result archive | Notebook |
|---|---|---|---|
| AutoSense five-seed Bi-LSTM | `kaggle_multiseed_input_bundle.zip` | `autosense_multiseed_results.zip` | `ieee_experiments/kaggle_multiseed_bilstm.ipynb` |
| Architecture ablation | `kaggle_architecture_ablation_input_bundle.zip` | `architecture_ablation_results.zip` | `ieee_experiments/kaggle_architecture_ablation.ipynb` |
| Feature ablation | `kaggle_feature_ablation_input_bundle.zip` | `feature_ablation_results.zip` | `ieee_experiments/kaggle_feature_ablation.ipynb` |
| C-MAPSS FD001 forecasting | `kaggle_cmapss_fd001_forecasting_input_bundle.zip` | `cmapss_fd001_forecasting_results.zip` | `ieee_experiments/kaggle_cmapss_fd001_forecasting.ipynb` |
| C-MAPSS stage analysis | `kaggle_cmapss_stage_analysis_input_bundle.zip` | `cmapss_stage_analysis_results.zip` | `ieee_experiments/kaggle_cmapss_stage_analysis.ipynb` |

The result archives are the provenance for the CSVs in `../ieee_results/`.
`../validate_final_result_archives.py` checks their hashes, row counts, keys,
settings and C-MAPSS engine separation, and confirms that every imported file
in `../ieee_results/` is byte-identical to its archive copy. Do not edit or
re-zip these files.

Each notebook checks the SHA256 of every bundle file before it trains. Paths
below are relative to `research_v2/`.

The two C-MAPSS bundles also contain the original pre-registered protocol
file, `research_v2/CODEX_IEEE_EXECUTION_PLAN.md`, whose hash is recorded in the
C-MAPSS results. Its content is summarized in
[`../EXPERIMENT_PROTOCOL.md`](../EXPERIMENT_PROTOCOL.md).

## AutoSense five-seed Bi-LSTM

This run is study 1 of [`../EXPERIMENT_PROTOCOL.md`](../EXPERIMENT_PROTOCOL.md):
the five prescribed Bi-LSTM seeds (`11, 21, 42, 84, 168`) for the three
AutoSense targets. It does not change any scientific setting.

Upload `kaggle/kaggle_multiseed_input_bundle.zip` as a private Kaggle Dataset.
The notebook extracts it automatically. Its internal layout is:

```text
<bundle-root>/
  research_v2/
    baseline_evaluation.py
    bilstm_evaluation.py
    protocol.py
    ieee_experiments/multiseed_bilstm.py
  FYP ML Training and Pipeline Code/
    Engine Temperature/karachi_2024_vehicle_temperature_data.csv
    TP_Generated/tyre_pressure_2024.csv
    Tyre Temperature/tyre_temp_2024.csv
```

Attach that private Dataset to a Kaggle notebook, enable Internet only if
Kaggle needs to install packages, and run
`ieee_experiments/kaggle_multiseed_bilstm.ipynb`. The notebook validates the
three input SHA256 values, executes the committed protocol from a writable
copy, and produces `autosense_multiseed_results.zip` for download.

Its contents go to:

```text
research_v2/ieee_results/multiseed_bilstm_metrics.csv
research_v2/ieee_results/multiseed_summary.csv
```

Do not combine Kaggle rows with partial local rows. The notebook starts a
complete five-seed run in its own environment and records its environment and
source hashes in every output row.

## Architecture ablation

Create a private Kaggle Dataset containing exactly
`kaggle/kaggle_architecture_ablation_input_bundle.zip`, then attach that
Dataset in the notebook **Input** panel. Do not unzip or alter the bundle.

Enable a GPU accelerator. The experiment is small but trains six recurrent
networks and will use GPU when available.

Import and run `ieee_experiments/kaggle_architecture_ablation.ipynb` in order.
It validates all seven source/data SHA256 hashes before it trains the fixed
seed-42 LSTM/Bi-LSTM comparison. It expects exactly six result rows.

Download `architecture_ablation_results.zip` from Kaggle Output. Extract its
contents into `research_v2/ieee_results/`:

- `architecture_ablation.csv`
- `kaggle_architecture_ablation_run_manifest.json`

Do not merge it with any partial/local ablation CSV.

## Causal feature ablation

Create a private Kaggle Dataset containing exactly
`kaggle/kaggle_feature_ablation_input_bundle.zip`, then attach it in the
Kaggle notebook Input panel. Do not unzip or change bundle contents.

Enable a GPU accelerator. The fixed experiment trains nine LSTMs and fits nine
Random Forests across the three AutoSense targets and F0/F1/F2 configurations.

Import and run `ieee_experiments/kaggle_feature_ablation.ipynb` in order. It
checks all input hashes before training, requires 18 unique result rows, and
asserts that F2's causal lag/rolling-feature policy discards no standard test
origins.

Download `feature_ablation_results.zip` and extract into
`research_v2/ieee_results/`:

- `feature_ablation.csv`
- `kaggle_feature_ablation_run_manifest.json`

Do not append this output to a partial/local feature-ablation CSV.

## NASA C-MAPSS FD001 forecasting

Create a private Kaggle Dataset containing exactly
`kaggle/kaggle_cmapss_fd001_forecasting_input_bundle.zip`, and attach it
as a notebook Input. The bundle contains the authoritative NASA
`train_FD001.txt`, committed 70/15/15 engine split, and pre-registered sensor
selection. Do not substitute a mirror or edit/unzip the bundle.

Enable a GPU accelerator. This is the heaviest prepared run: it fits C0/C1
models for four fixed sensors, including the declared three Bi-LSTM seeds.

Import and run `ieee_experiments/kaggle_cmapss_fd001_forecasting.ipynb` in
order. It validates the NASA data, execution-plan, split, and selection SHA256
hashes before fitting. It enforces the fixed sensors `sensor_9`, `sensor_11`,
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

## NASA C-MAPSS FD001 degradation-stage analysis

Run this only after C-MAPSS forecasting has completed and its output ZIP has
been downloaded.

Create one private Kaggle Dataset containing these two files, unchanged:

- `kaggle/kaggle_cmapss_stage_analysis_input_bundle.zip`
- `cmapss_fd001_forecasting_results.zip` downloaded from the forecasting run

Attach that Dataset in Kaggle's Input panel. GPU is optional because this
phase does not train models; it only checks and stratifies stored held-out
forecasts.

Import and run `ieee_experiments/kaggle_cmapss_stage_analysis.ipynb` in order.
It checks the stage script, plan, NASA FD001, split hashes, and all 44 expected
forecast artifacts before calculating the fixed early/mid/late normalized-life
bins. It expects exactly 132 output rows.

Download `cmapss_stage_analysis_results.zip` and extract into
`research_v2/ieee_results/`:

- `cmapss_stage_metrics.csv`
- `kaggle_cmapss_stage_analysis_run_manifest.json`
