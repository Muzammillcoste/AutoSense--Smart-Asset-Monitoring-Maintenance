# Codex Execution Plan: IEEE-Level Research Upgrade

## Mission

Upgrade the current corrected FYP paper into a substantially stronger research study suitable for serious preprint use and later IEEE submission consideration.

This task is not about polishing wording only. It is about strengthening the evidence base.

The current paper is already scientifically corrected, but its main limitations are:

- all three in-project benchmark datasets are synthetic;
- one chronological holdout;
- one neural random seed;
- limited architecture comparison;
- no controlled feature ablation;
- no decision-level threshold-event evaluation;
- no dependence-aware uncertainty analysis;
- corrected benchmark model is not yet integrated into the API path;
- Related Work is too small for an IEEE-oriented paper.

The upgraded study should address these weaknesses without changing results to force a preferred conclusion.

Work only on branch:

`research-paper-v2`

Never modify `main`.

Do not rewrite git history.

Keep new research files under:

`research_v2/ieee_experiments/`

and outputs under:

`research_v2/ieee_results/`

Do not delete the existing `research_v2/results` experiment artifacts.

---

# Scientific framing

Primary research question:

**How should forecasting models be selected for threshold-based predictive-maintenance workflows when model complexity, forecast horizon, robustness, and maintenance-alert usefulness are evaluated under a reproducible protocol?**

The upgraded paper should remain centered on:

**multi-step sensor forecasting for threshold-based predictive maintenance.**

Do not claim direct failure prediction or remaining useful life prediction for the original AutoSense datasets.

---

# Phase A — Preserve and verify the current corrected benchmark

Before new experiments:

1. verify the branch is `research-paper-v2`;
2. verify the current corrected benchmark files exist;
3. verify checks/tests already provided under `research_v2` still pass;
4. do not overwrite the current benchmark results unless the experiment protocol itself is intentionally versioned and documented.

Required current source files include:

- `research_v2/results/final_comparison.csv`
- `research_v2/results/bilstm_metrics.csv`
- `research_v2/results/bilstm_horizon_metrics.csv`
- `research_v2/results/<dataset>/test_predictions.npz`
- `research_v2/results/<dataset>/metadata.json`
- `research_v2/REPORT_FOR_CHATGPT_REVIEW.md`
- `research_v2/AUDIT.md`

Record the starting commit SHA in:

`research_v2/ieee_results/provenance.json`

---

# Phase B — Multi-seed Bi-LSTM robustness

## Goal

Test whether the current Bi-LSTM ranking is stable across initialization seeds.

## Fixed seeds

Use exactly:

- 11
- 21
- 42
- 84
- 168

## Rules

- same data protocol as corrected benchmark;
- same train/validation/test boundaries;
- no shuffling;
- same architecture;
- same features;
- same 20-epoch cap;
- same batch size 64;
- same early stopping rule;
- scaler fit only on fitting-region data;
- no test-driven tuning;
- do not change hyperparameters after observing test performance.

## Create

`research_v2/ieee_experiments/multiseed_bilstm.py`

## Save

`research_v2/ieee_results/multiseed_bilstm_metrics.csv`

Columns should include:

- Dataset
- Seed
- MAE
- RMSE
- R2
- Epochs run
- Best epoch
- Training seconds
- Unit

Also save:

`research_v2/ieee_results/multiseed_summary.csv`

with mean and standard deviation for MAE/RMSE/R² per dataset.

Do not replace the original single-seed benchmark table; this is an additional robustness study.

---

# Phase C — Architecture ablation

## Goal

Test whether bidirectionality or recurrent complexity materially improves results.

## Models

Evaluate at minimum:

1. LSTM
2. Bi-LSTM

Optional only if practical without excessive runtime:

3. GRU
4. MLP autoregressor

## Fairness rules

- same input history;
- same output horizon;
- same train/validation/test origins;
- same scaler policy;
- same training budget where applicable;
- same seed set if runtime permits, otherwise seed 42 for the first ablation pass and document this limitation.

Do not tune each architecture separately against test results.

## Suggested LSTM reference

Unidirectional counterpart to the current Bi-LSTM family:

- LSTM(128, return_sequences=True)
- BatchNormalization
- Dropout(0.2)
- LSTM(64, return_sequences=True)
- BatchNormalization
- Dropout(0.3)
- LSTM(32)
- Dense(64, relu)
- Dropout(0.2)
- Dense(horizon)

Keep parameter differences transparent.

## Create

`research_v2/ieee_experiments/architecture_ablation.py`

## Save

`research_v2/ieee_results/architecture_ablation.csv`

Include parameter count and training time.

---

# Phase D — Feature ablation

## Goal

Determine whether simple causal feature engineering improves learned models.

## Configurations

### F0 — target history only

Current benchmark information set.

### F1 — target history + deterministic calendar features

For the AutoSense synthetic datasets only:

- hour sin/cos
- day-of-week sin/cos
- month sin/cos

### F2 — target history + calendar + causal lag/rolling features

Where cadence makes the feature meaningful:

- previous 24-hour target lag in clock time;
- trailing 72-hour mean in clock time.

Convert clock time to sample counts using inferred cadence.

Do not use misleading names such as `shift(24)` unless it actually means 24 hours.

## Leakage rules

- all rolling features trailing only;
- no centered rolling windows;
- no future target values;
- scaling/statistics fitted using fitting data only;
- preserve target-period disjointness.

## Evaluate

At minimum:

- Random Forest
- LSTM or Bi-LSTM

## Create

`research_v2/ieee_experiments/feature_ablation.py`

## Save

`research_v2/ieee_results/feature_ablation.csv`

---

# Phase E — Forecast-based threshold-event evaluation

## Motivation

Forecast MAE alone does not demonstrate maintenance-alert usefulness.

Add a decision-level evaluation without inventing engineering safety thresholds.

## Threshold definition

Compute thresholds from fitting-region target values only.

Use proxy statistical thresholds, clearly labelled as such.

Recommended default:

### Engine temperature

upper proxy threshold = 95th percentile of fitting-region values.

### Tyre temperature

upper proxy threshold = 95th percentile.

### Tyre pressure

lower proxy threshold = 5th percentile;
upper proxy threshold = 95th percentile.

Do not call these safety thresholds.

Call them:

**training-derived proxy maintenance/anomaly thresholds**.

## Actual future event

At each test forecast origin, define the actual event as whether any true target value in the next 24-hour horizon crosses the relevant threshold.

## Predicted event

A forecasting model predicts an event if any predicted value in the same horizon crosses the threshold.

Evaluate:

- Persistence
- Seasonal naive
- Random Forest
- Bi-LSTM

## Report

For each dataset/model:

- event prevalence
- precision
- recall
- F1
- specificity
- false positive rate
- balanced accuracy
- confusion matrix counts

Where meaningful, estimate lead time for true-positive forecasts:

- earliest predicted threshold crossing relative to earliest actual threshold crossing;
- clearly define sign convention.

Do not interpret these events as real component failures.

## Create

`research_v2/ieee_experiments/threshold_event_evaluation.py`

## Save

- `research_v2/ieee_results/threshold_event_metrics.csv`
- `research_v2/ieee_results/threshold_event_thresholds.json`
- `research_v2/ieee_results/threshold_event_confusions.csv`

---

# Phase F — Dependence-aware uncertainty analysis

## Motivation

Forecast windows overlap, so ordinary i.i.d. significance tests are inappropriate.

Use moving-block bootstrap over test forecast origins.

## Compare

At minimum:

- best baseline vs Bi-LSTM for each AutoSense dataset;
- Random Forest vs Persistence where relevant.

## Statistic

Difference in pooled MAE:

`MAE(model_A) - MAE(model_B)`

Clearly state which sign favors which model.

## Bootstrap

Recommended:

- 2,000 bootstrap replications;
- block length chosen conservatively relative to forecast horizon;
- document exact block length in units of forecast origins and clock time;
- fixed bootstrap seed 42.

If runtime is too high, 1,000 replications is acceptable with explicit documentation.

## Output

- observed MAE difference
- bootstrap mean difference
- 2.5th percentile
- 97.5th percentile
- whether CI excludes zero

Do not overclaim formal significance beyond this dependence-aware interval.

## Create

`research_v2/ieee_experiments/bootstrap_comparison.py`

## Save

`research_v2/ieee_results/bootstrap_mae_differences.csv`

---

# Phase G — External validation using NASA C-MAPSS FD001

## Why FD001

Use NASA C-MAPSS FD001 as the primary external aviation/prognostics benchmark.

Important wording:

- C-MAPSS is simulator-generated engine degradation data, not measured commercial-fleet telemetry;
- it is nevertheless an external, canonical aviation prognostics benchmark independent of the custom AutoSense generators.

Do not describe it as physically measured real-flight data.

## Dataset acquisition

Prefer an official NASA-hosted or authoritative C-MAPSS source.

Record:

- source URL;
- access date;
- archive/file hash;
- dataset citation;
- license/usage notes if available.

If internet access is unavailable, do not substitute an unknown mirror silently.

Stop with a concrete blocker requesting the FD001 archive from the user.

Expected classic files include:

- `train_FD001.txt`
- `test_FD001.txt`
- `RUL_FD001.txt`

For the main forecasting external-validation experiment, use `train_FD001.txt` because its engines run to failure and therefore provide complete future sensor trajectories.

Do not use official `test_FD001.txt` for future-sensor forecasting beyond its truncation point.

## Data columns

Parse standard C-MAPSS columns:

- unit number
- cycle
- 3 operational settings
- 21 sensor measurements

Validate engine/cycle ordering.

Do not create windows that cross engine boundaries.

---

# Phase H — C-MAPSS engine-level partitioning

## Critical rule

Split by engine unit, never by rows or windows.

No engine may appear in more than one partition.

Use deterministic engine-level split from `train_FD001`:

- 70 engines train
- 15 engines validation
- 15 engines test

Use a seeded permutation with seed 42 and save exact engine IDs.

Save:

`research_v2/ieee_results/cmapss_fd001_split.json`

Include:

- train engine IDs
- validation engine IDs
- test engine IDs
- dataset hash

Do not alter the split after observing test results.

---

# Phase I — C-MAPSS target sensor selection

Do not manually cherry-pick sensors based on test behavior.

Use a training-only deterministic sensor-selection procedure.

## Step 1 — remove near-constant sensors

Using train-engine data only, compute variance for all 21 sensors.

Remove sensors below a documented small variance threshold or use a relative near-zero-variance criterion.

## Step 2 — degradation relevance score

For remaining sensors:

1. within each training engine, compute Spearman correlation between sensor value and cycle;
2. take the median absolute correlation across training engines;
3. rank sensors descending by this score.

Select the top 4 sensors.

Save ranking and scores to:

`research_v2/ieee_results/cmapss_sensor_selection.csv`

Do not use validation/test sensors to select channels.

If ties occur, break by sensor index ascending.

---

# Phase J — C-MAPSS forecasting task

## Task

Forecast future sensor trajectories in engine-cycle units.

Use:

- lookback = 30 cycles
- forecast horizon = 10 cycles

A valid window must have 30 observed past cycles and 10 future target cycles within the same engine.

Do not pad short engines.

## Feature configurations

### C0 — target-history only

For each selected target sensor, forecast it from its own previous 30 cycles.

### C1 — multivariate history

Use:

- 3 operational settings
- the selected top 4 sensors

as the observed 30-cycle input.

Predict one selected target sensor at a time over the next 10 cycles.

This provides a controlled external feature-ablation study.

## Models

For C0:

- Persistence
- Random Forest
- LSTM
- Bi-LSTM

For C1:

- Random Forest
- LSTM
- Bi-LSTM

Seasonal naive should not be used unless a genuine cycle-period seasonality is established from training data; otherwise omit it.

## Scaling

Fit scalers only on train-engine data.

Do not use validation/test engines in scaler fitting.

## Metrics

Per target sensor:

- MAE
- RMSE
- R²

Also report:

- macro-average across selected sensors;
- horizon-wise MAE over 1–10 cycles.

Do not pool sensors with different scales into a physical-unit metric unless normalized explicitly and labelled as normalized.

## Create

`research_v2/ieee_experiments/cmapss_fd001_forecasting.py`

## Save

- `research_v2/ieee_results/cmapss_fd001_metrics.csv`
- `research_v2/ieee_results/cmapss_fd001_horizon_metrics.csv`
- `research_v2/ieee_results/cmapss_fd001_predictions/`

Store predictions and truth by engine ID and forecast origin.

---

# Phase K — C-MAPSS degradation-stage analysis

Because FD001 train engines run to failure, derive true remaining cycles for analysis only:

`RUL_at_cycle = max_cycle_for_engine - current_cycle`

Do not turn the paper into an RUL-prediction paper.

Use RUL only to stratify forecasting error by degradation stage.

Create three pre-declared bins using training-engine trajectory proportions or fixed normalized-life fractions.

Preferred normalized-life bins:

- early: normalized cycle fraction < 0.5
- mid: 0.5 to < 0.8
- late: >= 0.8

where:

`normalized cycle fraction = cycle / max_cycle_for_engine`

For held-out test engines, max cycle is known because these are run-to-failure trajectories from `train_FD001` reserved by engine ID.

Report MAE by stage for each model and selected sensor.

This tests whether models degrade differently near end-of-life.

Create:

`research_v2/ieee_experiments/cmapss_stage_analysis.py`

Save:

`research_v2/ieee_results/cmapss_stage_metrics.csv`

---

# Phase L — Multi-seed external neural evaluation

For the C-MAPSS Bi-LSTM, run at least seeds:

- 11
- 42
- 84

If runtime is acceptable, use all five standard seeds from Phase B.

Report mean ± std across seeds.

Do not rerun baselines unnecessarily.

Save:

`research_v2/ieee_results/cmapss_multiseed_summary.csv`

---

# Phase M — API consistency and latency validation

## Goal

Align the corrected selected AutoSense model with the inference/service layer.

Do not modify the original prototype destructively.

Create a versioned research endpoint or wrapper under `research_v2` if safer.

## Model choice

Use the empirically selected corrected benchmark model per target.

Current corrected benchmark indicates:

- Random Forest for engine temperature;
- Persistence for tyre pressure by MAE;
- Random Forest for tyre temperature.

If new robustness/ablation results materially change the recommended model, document the selection rule before replacing this mapping.

## Consistency test

For saved held-out test windows:

1. load exact input;
2. call the API inference path;
3. compare API output to offline prediction artifact;
4. assert tolerance suitable for floating-point serialization.

## Latency test

Run at least 200 local inference/API requests after warm-up.

Report:

- median latency
- p90
- p95
- p99
- min/max if useful

Record:

- CPU/device
- Python version
- local-only environment

Do not claim internet/cloud/production latency.

Create:

`research_v2/ieee_experiments/api_consistency_and_latency.py`

Save:

- `research_v2/ieee_results/api_consistency.json`
- `research_v2/ieee_results/api_latency.csv`
- `research_v2/ieee_results/api_latency_summary.json`

---

# Phase N — Expand Related Work

The current paper has too few references.

Target 20–30 high-quality references.

Research categories:

1. predictive maintenance surveys;
2. industrial sensor forecasting;
3. LSTM/Bi-LSTM for predictive maintenance;
4. tree-based forecasting/baselines;
5. C-MAPSS prognostics literature;
6. industrial IoT architectures;
7. fleet/vehicle maintenance monitoring;
8. threshold/anomaly-event prediction;
9. enterprise maintenance workflow integration;
10. aviation/ground-support maintenance if credible literature exists.

Rules:

- prefer peer-reviewed original papers;
- verify DOI/title/authors/year/venue;
- avoid citation padding;
- do not fabricate metadata;
- use official publisher or DOI metadata where possible;
- arXiv can be cited when it is the actual source/preprint, but peer-reviewed versions are preferable when available.

Create a compact related-work comparison table with columns such as:

- Study
- Domain
- Data provenance
- Task
- Models
- Metrics
- Real/simulated data
- Decision/workflow evaluation

Only include rows that can be verified.

---

# Phase O — Upgrade figures

Create publication-quality plots from the new results.

Required new figures:

## 1. Multi-seed robustness

Mean ± std MAE for Bi-LSTM across AutoSense targets.

## 2. Architecture/feature ablation

Compact grouped comparison.

## 3. Threshold-event evaluation

Prefer precision/recall/F1 panel or F1 plus event prevalence.

## 4. C-MAPSS external validation

Per-sensor model comparison or macro-average plus horizon-wise curve.

## 5. C-MAPSS degradation-stage error

Early vs mid vs late-life MAE.

All plots must:

- be readable in IEEE two-column layout;
- remain understandable in grayscale;
- use vector PDF output where possible;
- be generated from committed CSV/NPZ results;
- not manually type scientific values that can be read programmatically.

Create generation code under:

`research_v2/ieee_experiments/generate_ieee_figures.py`

Save figures under:

`research_v2/paper/figures/ieee_upgrade/`

---

# Phase P — Rewrite the paper only after experiments finish

Do not rewrite the paper prematurely.

First produce a scientific report.

After results are complete, update:

`research_v2/paper/main.tex`

The upgraded structure should approximately be:

1. Introduction
2. Related Work
3. System Architecture
4. Forecasting and Decision Framework
5. Experimental Protocol
6. AutoSense Synthetic Benchmark Results
7. Robustness and Ablation Studies
8. Threshold-Event Evaluation
9. External Validation on C-MAPSS FD001
10. Prototype/API Validation
11. Discussion
12. Limitations
13. Conclusion

Compress sections if page limits require it.

---

# Phase Q — Claims discipline

Never reintroduce:

- `0.1795°C` as physical engine MAE;
- `0.2368 MPa` as tyre-pressure MAE;
- `0.344°C` as validated physical tyre-temperature MAE;
- 10–15% downtime reduction;
- operational aviation-fleet validation;
- direct failure/RUL prediction for AutoSense;
- certified safety-threshold claims;
- Bi-LSTM superiority unless supported by new evidence;
- claims that C-MAPSS is physically measured flight data.

If C-MAPSS is used, describe it accurately as an external NASA C-MAPSS simulated engine-degradation benchmark.

---

# Phase R — Runtime management

This is a large task. Work in checkpoints.

After each major phase:

1. save outputs;
2. write a concise status entry to:

`research_v2/ieee_results/PROGRESS.md`

3. commit changes to `research-paper-v2`.

Suggested commit checkpoints:

1. `Add IEEE experiment infrastructure`
2. `Add multiseed and ablation results`
3. `Add threshold-event and bootstrap analysis`
4. `Add C-MAPSS external validation`
5. `Add API consistency and latency validation`
6. `Expand related work and IEEE figures`
7. `Upgrade paper with extended experiments`

Do not commit environment caches, virtual environments, or huge unnecessary artifacts.

If trained model binaries are very large, save only what is required for reproducibility and document regeneration instructions.

---

# Phase S — Failure handling

Do not stop at the first code error.

Diagnose and fix ordinary code/environment issues.

Stop only when user input is genuinely required, such as:

- C-MAPSS archive cannot be accessed;
- required external service credentials are unavailable;
- a software dependency cannot be installed without system privileges;
- runtime would exceed practical limits and a scientific tradeoff needs approval.

If C-MAPSS download is the blocker, state exactly which files are needed and where the user should place them, for example:

`research_v2/external_data/cmapss/`

Do not silently use a random Kaggle/GitHub copy if provenance cannot be verified.

---

# Phase T — Required final scientific report

Before final paper rewrite, create:

`research_v2/IEEE_UPGRADE_REPORT.md`

End it with exactly:

## REPORT FOR CHATGPT IEEE REVIEW

Include:

1. starting commit SHA;
2. final commit SHA;
3. environment;
4. all files created/modified;
5. AutoSense multi-seed results;
6. architecture ablation results;
7. feature ablation results;
8. threshold-event metrics;
9. moving-block bootstrap intervals;
10. C-MAPSS source/provenance;
11. C-MAPSS engine split IDs;
12. selected C-MAPSS sensors and selection scores;
13. C-MAPSS forecasting results;
14. degradation-stage results;
15. C-MAPSS neural seed robustness;
16. API consistency results;
17. latency summary;
18. references added;
19. strongest defensible scientific conclusions;
20. results that did not support the original hypothesis;
21. unresolved limitations;
22. exact paper sections updated;
23. LaTeX build status;
24. page count if compiled;
25. remaining blockers before arXiv;
26. remaining blockers before IEEE submission.

Also include a compact final recommendation:

- **Ready for arXiv:** Yes / No / Conditional
- **Ready for IEEE submission:** Yes / No / Conditional

with reasons.

---

# Execution priority if Codex runtime/limit is reached

If the full plan cannot be completed in one session, prioritize in this order:

1. Multi-seed AutoSense Bi-LSTM
2. Threshold-event evaluation
3. Architecture ablation
4. Moving-block bootstrap
5. C-MAPSS FD001 acquisition + engine-level split
6. C-MAPSS forecasting benchmark
7. C-MAPSS degradation-stage analysis
8. Feature ablation
9. API consistency/latency
10. Related Work expansion
11. Paper rewrite

Always commit completed work before stopping.

---

# Final execution instruction

Do not optimize for a predetermined deep-learning result.

If persistence or Random Forest remains superior, report that result clearly.

The upgraded paper should derive its value from rigorous evaluation, robustness, external validation, decision-level analysis, and reproducible integration—not from forcing Bi-LSTM to win.
