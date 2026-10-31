# Experiment protocol for the extended study

This document fixed the design of the extended experiments *before* they were run. It lists the seeds, model settings, thresholds, data splits and the decisions that test results were not allowed to change. The results are in [`EXTENDED_EXPERIMENTS.md`](EXTENDED_EXPERIMENTS.md).

## The original protocol file

The protocol was first written as a step-by-step task plan for an AI coding agent (Codex), named `CODEX_IEEE_EXECUTION_PLAN.md`. Its SHA256 is recorded in every C-MAPSS result row and Kaggle manifest as the "Protocol SHA256":

```text
1e72e4109507e7968af365367d855fac495439173f38c4c7a72c4ece71c627bb
```

The unchanged original is kept inside both C-MAPSS input bundles in [`kaggle/`](kaggle/). The scientific content is summarized below. To check the recorded hash, run from the repository root:

```sh
unzip -p research_v2/kaggle/kaggle_cmapss_fd001_forecasting_input_bundle.zip research_v2/CODEX_IEEE_EXECUTION_PLAN.md | sha256sum
```

The C-MAPSS scripts read this file from `research_v2/` in order to record its hash. Their code is hash-recorded, so it is left unchanged. To run them outside Kaggle, extract it first (the file is git-ignored):

```sh
unzip -j research_v2/kaggle/kaggle_cmapss_fd001_forecasting_input_bundle.zip research_v2/CODEX_IEEE_EXECUTION_PLAN.md -d research_v2
```

## Research question

> How should forecasting models be selected for threshold-based predictive-maintenance workflows when model complexity, forecast horizon, robustness and maintenance-alert usefulness are evaluated under a reproducible protocol?

The study remains about **multi-step sensor forecasting for threshold-based maintenance**. It makes no claim of failure prediction or remaining-useful-life (RUL) prediction for the AutoSense data.

## Rules for every experiment

- Keep the corrected benchmark ([`BENCHMARK_REPORT.md`](BENCHMARK_REPORT.md)) and its results unchanged. New outputs go to `ieee_results/`.
- Use the same chronological split, windows and target-period separation as the benchmark ([`protocol.py`](protocol.py)).
- Fit scalers and other statistics on training data only. Do not shuffle.
- Do not tune any model, feature, threshold, sensor choice or split on validation or test results. Do not change settings after seeing test results.
- Report every result, including results where Bi-LSTM loses. The aim is a rigorous evaluation, not a predetermined winner.

## Planned studies

The "Outcome" lines record how each study was actually carried out.

### 1. Multi-seed Bi-LSTM

- **Design.** Seeds 11, 21, 42, 84 and 168. Everything else is unchanged: architecture, single target-history input, 20-epoch cap, batch size 64, early stopping with patience 5. Report the per-seed MAE, RMSE and R², the epochs run, the best epoch and the training time, then the mean and standard deviation per target.
- **Outcome.** Run as planned (15 runs).

### 2. Architecture ablation

- **Design.** Compare an LSTM with the Bi-LSTM under identical inputs, horizon, origins, scaler policy and training budget. The LSTM is the one-directional version of the same stack:
  - LSTM(128, return sequences), batch normalization, dropout 0.2
  - LSTM(64, return sequences), batch normalization, dropout 0.3
  - LSTM(32), Dense(64, ReLU), dropout 0.2, Dense(horizon)

  GRU and MLP models were optional. If runtime was limited, seed 42 alone was allowed, with the limitation stated.
- **Outcome.** LSTM and Bi-LSTM, seed 42 only; GRU and MLP were not run.

### 3. Causal feature ablation

- **Design.**
  - **F0**: target history only.
  - **F1**: F0 plus sine/cosine of hour, day of week and month.
  - **F2**: F1 plus a 24-hour lag and a trailing 72-hour mean, both measured in clock time.

  Clock time is converted to sample counts using each series' cadence. Features may use past values only (no centred windows), and all statistics are fitted on training data. Evaluate Random Forest and an LSTM.
- **Outcome.** Run as planned, seed 42.

### 4. Proxy threshold-event evaluation

- **Design.** Thresholds are percentiles of training data only:
  - the 95th percentile for engine temperature and tyre temperature
  - the 5th and 95th percentiles for tyre pressure

  These are called *training-derived proxy thresholds*, never safety thresholds. An actual event occurs when any true value in the next 24 h crosses a threshold. A predicted event occurs when any forecast value does. Score persistence, seasonal naive, Random Forest and Bi-LSTM on:
  - prevalence, precision, recall, F1 and specificity
  - false-positive rate, balanced accuracy and confusion counts
  - lead time for true positives, with the sign convention stated

  These events are not component failures.
- **Outcome.** Run as planned.

### 5. Dependence-aware uncertainty

- **Design.** Moving-block bootstrap over test forecast origins. Use 2,000 replications, seed 42, and a block length chosen conservatively relative to the horizon, stated in both origins and hours. The statistic is MAE(A) − MAE(B), with the sign convention stated. Compare the best baseline with the Bi-LSTM for each target, and Random Forest with persistence. Report the observed difference, the bootstrap mean, the 2.5th and 97.5th percentiles, and whether the interval excludes zero. Do not claim significance beyond this interval.
- **Outcome.** Run as planned, with 48-hour blocks.

### 6. External data: NASA C-MAPSS FD001

- **Design.** Acquire FD001 from an official NASA source. Record the URL, access date, hashes, citation and usage terms, and never use an unverified mirror. Describe the data as *simulator-generated*, not measured flight data. Use only `train_FD001.txt` (run-to-failure engines). Do not forecast beyond the truncation point of the official test files.
- **Outcome.** Acquired from data.nasa.gov ([`ieee_results/provenance.json`](ieee_results/provenance.json)).

### 7. C-MAPSS engine split

- **Design.** Split by engine, never by row or window: a seed-42 permutation gives 70 train, 15 validation and 15 test engines. Save the engine IDs and the dataset hash before any model is fitted. No engine may appear in two partitions.
- **Outcome.** Saved in [`ieee_results/cmapss_fd001_split.json`](ieee_results/cmapss_fd001_split.json).

### 8. C-MAPSS sensor selection

- **Design.** Use training engines only:
  1. Drop near-constant sensors.
  2. Rank the rest by the median, across engines, of the absolute within-engine Spearman correlation between sensor value and cycle.
  3. Keep the top four, breaking ties by sensor index.

  Never select sensors using validation or test engines.
- **Outcome.** Sensors 9, 11, 14 and 12 ([`ieee_results/cmapss_sensor_selection.csv`](ieee_results/cmapss_sensor_selection.csv)).

### 9. C-MAPSS forecasting

- **Design.** Use 30 cycles of history to forecast 10 cycles, without padding and without windows that cross engines. There are two input settings:
  - **C0**: target history only; models are persistence, Random Forest, LSTM and Bi-LSTM.
  - **C1**: three operational settings plus the four sensors; models are Random Forest, LSTM and Bi-LSTM.

  Seasonal naive is excluded unless a real cycle seasonality is shown. Fit scalers on training engines. Report per-sensor MAE, RMSE and R², the normalized macro-average and horizon-wise MAE, and save predictions by engine and origin.
- **Outcome.** Run as planned, with 44 prediction files.

### 10. C-MAPSS degradation stages

- **Design.** Group the test forecasts by normalized life (cycle ÷ final cycle): early (< 0.5), mid (0.5 to < 0.8) and late (≥ 0.8). Remaining life is used for grouping only. It is never a model target.
- **Outcome.** Run as planned (132 rows).

### 11. C-MAPSS Bi-LSTM seeds

- **Design.** At least seeds 11, 42 and 84 (all five if runtime allows). Report the mean ± standard deviation.
- **Outcome.** Seeds 11, 42 and 84.

### 12. API consistency and latency

- **Design.** Send saved test windows through a research inference wrapper and check that its output matches the offline predictions. Then time at least 200 local requests and report the median, p90, p95 and p99 latency, the device and the Python version. Make no cloud or production latency claim.
- **Outcome.** The scripts exist ([`ieee_experiments/api_consistency_and_latency.py`](ieee_experiments/api_consistency_and_latency.py), [`research_inference.py`](ieee_experiments/research_inference.py)). No results were committed, and the manuscript reports none.

### 13. Related work and figures

- **Design.** Aim for 20–30 verified, preferably peer-reviewed references, with no padding and no unverified metadata. Add a compact comparison table. Generate figures from the committed results as grayscale-readable vector PDFs, without values typed in by hand.
- **Outcome.** The manuscript cites 11 verified sources; figures are generated by [`ieee_experiments/generate_ieee_figures.py`](ieee_experiments/generate_ieee_figures.py).

## Claims ruled out in advance

The manuscript does not state any of the following:

- **Original metrics:** 0.1795 °C as a physical engine MAE, 0.2368 MPa as a tyre-pressure MAE, or 0.344 °C as a validated tyre-temperature MAE.
- **Outcome claims:** a 10–15% downtime reduction, or validation on an operational aviation fleet.
- **Prediction claims:** direct failure or RUL prediction on AutoSense data, or certified safety thresholds.
- **Model claims:** Bi-LSTM superiority without supporting evidence.
- **Data claims:** that C-MAPSS is physically measured flight data.
