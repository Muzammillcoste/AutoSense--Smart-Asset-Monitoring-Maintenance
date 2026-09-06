# IEEE-Level Upgrade Plan

## Objective

Upgrade the current research paper from a strong undergraduate/FYP preprint into a substantially more competitive research submission by adding stronger empirical evidence, clearer scientific novelty, better external validation, stronger statistical analysis, and tighter system-to-decision evaluation.

The current paper is scientifically defensible but still limited by synthetic data, one fixed chronological holdout, one seed, limited baselines, and prototype-only deployment evidence. The next phase should address those weaknesses before arXiv submission and before considering an IEEE venue.

The goal is not to make the paper look stronger through wording. The goal is to make the evidence stronger.

---

# Main research question for the upgraded paper

Primary question:

**How should forecasting models be selected for threshold-based predictive-maintenance workflows when model complexity, forecast horizon, and operational alert usefulness are evaluated under a reproducible protocol?**

This moves the paper beyond a simple model comparison and gives the work a stronger research contribution:

1. forecast accuracy comparison;
2. robustness across seeds/configurations;
3. feature/architecture ablation;
4. threshold-event usefulness;
5. external/public-data validation;
6. integration of the selected model into the maintenance workflow.

---

# Phase 1 — Strengthen the forecasting experiment

## 1. Multi-seed neural evaluation

The current neural results use one seed.

Run the Bi-LSTM with at least 5 fixed seeds:

- 11
- 21
- 42
- 84
- 168

Keep the protocol, architecture, epoch budget, validation split and test period fixed.

Report:

- mean MAE
- standard deviation of MAE
- mean RMSE
- standard deviation of RMSE
- mean R²
- standard deviation of R²

Do not tune against test results.

Add:

`research_v2/ieee_experiments/multiseed_bilstm.py`

Outputs:

- `research_v2/ieee_results/multiseed_bilstm_metrics.csv`
- `research_v2/ieee_results/multiseed_summary.csv`

---

## 2. Architecture ablation

The current network is a relatively large mixed recurrent stack.

Evaluate at minimum:

- unidirectional LSTM
- Bi-LSTM

Optionally include:

- simple MLP autoregressor
- GRU

Use the same historical information and the same split.

The scientific purpose is to test whether bidirectionality or recurrent complexity adds value.

Do not include architectures merely to increase the number of models.

Output:

`research_v2/ieee_results/architecture_ablation.csv`

---

## 3. Feature ablation

The current aligned benchmark uses historical target values only.

Add a controlled feature study comparing:

### Configuration A
Target history only.

### Configuration B
Target history + deterministic calendar features:

- hour sin/cos
- day-of-week sin/cos
- month sin/cos

### Configuration C
Target history + calendar + causal lag/rolling features where valid.

Important:

- features must be causal;
- rolling windows must use past data only;
- scaler/statistics must be fitted using fitting data only;
- feature design must be fixed before test evaluation.

This ablation should be run for Random Forest and the neural model where practical.

Output:

`research_v2/ieee_results/feature_ablation.csv`

---

# Phase 2 — Add decision-level predictive-maintenance evaluation

Forecast MAE alone is not enough to show usefulness for threshold-based maintenance.

Add a threshold-event evaluation.

## Event definition

For each forecast origin, define a future threshold event from actual values over the next 24 hours.

Because validated engineering safety limits are unavailable, do not invent safety thresholds.

Instead use training-derived proxy thresholds, for example:

- upper threshold = 95th percentile of fitting-region target values;
- lower threshold = 5th percentile where a low value is meaningful.

Define these clearly as **proxy anomaly/maintenance thresholds**, not certified safety limits.

Possible target rules:

- engine temperature: upper-tail threshold;
- tyre temperature: upper-tail threshold;
- tyre pressure: both lower- and upper-tail thresholds.

Thresholds must be computed from fitting data only.

## Model alert rule

A model predicts an event if any forecast step crosses the threshold during the 24-hour horizon.

Compare:

- Persistence
- Seasonal naive
- Random Forest
- Bi-LSTM

Report:

- precision
- recall
- F1 score
- balanced accuracy if useful
- event prevalence
- false positive rate
- mean/median lead time for correctly predicted events where definable

Do not present this as real failure prediction.

Call it:

**forecast-based proxy threshold-event detection**.

Create:

`research_v2/ieee_experiments/threshold_event_evaluation.py`

Outputs:

- `research_v2/ieee_results/threshold_event_metrics.csv`
- `research_v2/ieee_results/threshold_event_thresholds.json`

This is one of the most important upgrades because it connects numerical forecasts to the maintenance decision layer.

---

# Phase 3 — External/public-data validation

The largest weakness of the current paper is that all three datasets are synthetic.

For a stronger IEEE-oriented submission, add at least one public real or experimentally measured predictive-maintenance/sensor dataset.

The external dataset does not need to be aviation-specific if the paper is explicit that it is used for external validation of the forecasting methodology.

Selection criteria:

- genuinely measured data preferred;
- clear timestamp or sequential ordering;
- sensor time-series suitable for forecasting;
- sufficient length for train/validation/test partitions;
- public and citable;
- license/terms allow academic use;
- avoid another purely synthetic benchmark if possible.

The selected dataset should be documented with:

- official source URL;
- citation;
- license/terms;
- target variable(s);
- sampling interval;
- preprocessing rules;
- missing-data handling;
- train/validation/test protocol.

Run at least:

- Persistence
- Seasonal naive if meaningful
- Random Forest
- LSTM/Bi-LSTM

Use the same research principle: strong baselines first.

Do not force a 24-hour horizon if the external dataset cadence/domain makes that arbitrary. Define the horizon in a domain-appropriate way and explain it.

Create a dedicated external-validation section in the paper.

---

# Phase 4 — Statistical uncertainty and comparison

The current test windows overlap, so ordinary independent-sample tests are inappropriate.

Use a dependence-aware uncertainty method.

Preferred practical option:

**moving-block bootstrap over forecast origins**

for differences in MAE between models.

For each target/model comparison:

- estimate mean MAE difference;
- 95% confidence interval;
- clearly document block length and bootstrap repetitions.

Do not claim significance unless the method and assumptions are defensible.

At minimum compare:

- best baseline vs Bi-LSTM;
- Random Forest vs Persistence where relevant.

Create:

`research_v2/ieee_experiments/bootstrap_comparison.py`

Output:

`research_v2/ieee_results/bootstrap_mae_differences.csv`

---

# Phase 5 — Align the deployed prototype with the corrected benchmark

The current paper correctly notes that the offline corrected benchmark has not replaced the legacy model path in the prototype.

For a stronger system paper, integrate the selected model from the corrected benchmark into the FastAPI/service path.

Do this without pretending it is a real fleet deployment.

Required evidence:

1. use the selected benchmark model in the inference endpoint;
2. feed a saved test input through the API;
3. verify API prediction equals offline prediction within numerical tolerance;
4. measure local inference/API latency over many repeated requests;
5. report median and p95 latency;
6. record hardware/environment;
7. do not claim network/cloud/operational latency from local measurements.

Suggested script:

`research_v2/ieee_experiments/api_consistency_and_latency.py`

Outputs:

- `research_v2/ieee_results/api_consistency.json`
- `research_v2/ieee_results/api_latency.csv`

This converts the architecture from a conceptual bridge into reproducible end-to-end software evidence.

---

# Phase 6 — Stronger related work

The current paper has too few references for a competitive research submission.

Target roughly 20–30 high-quality references, prioritizing:

- predictive maintenance surveys;
- time-series forecasting for industrial sensors;
- LSTM/Bi-LSTM in predictive maintenance;
- Random Forest or tree-based forecasting baselines;
- industrial IoT architectures;
- fleet/vehicle maintenance monitoring;
- threshold/anomaly-event prediction;
- enterprise maintenance/workflow integration;
- any directly relevant aviation ground-support or vehicle-maintenance studies.

Use original publisher/DOI metadata where possible.

Avoid padding the bibliography with loosely related citations.

Related Work should compare:

- problem setting;
- data type;
- model type;
- evaluation metrics;
- real vs synthetic data;
- whether maintenance decisions/outcomes are evaluated;
- whether end-to-end integration is demonstrated.

A compact comparison table may be useful.

---

# Phase 7 — Rewrite the novelty/contribution statement

After the new experiments, the paper should no longer be positioned as merely:

"we built IoT + Bi-LSTM + Salesforce."

A stronger framing would be:

**A reproducible evaluation framework connecting multi-step sensor forecasting to threshold-based maintenance decisions and enterprise workflows, with controlled baseline, architecture, feature, robustness, and external-validation studies.**

Possible contribution list after completion:

1. end-to-end IoT-to-enterprise maintenance prototype;
2. corrected cadence-aware multi-step forecasting protocol;
3. controlled comparison of simple, tree-based, and recurrent models;
4. architecture and feature ablation;
5. multi-seed robustness analysis;
6. threshold-event evaluation connecting forecast quality to maintenance-alert usefulness;
7. external public-dataset validation;
8. reproducible API consistency/latency validation.

Only include contributions actually completed.

---

# Phase 8 — Paper structure for IEEE-oriented version

Recommended structure:

1. Introduction
2. Related Work
3. System Architecture
4. Forecasting and Decision Framework
5. Experimental Protocol
6. Synthetic Benchmark Results
7. Robustness and Ablation Studies
8. Threshold-Event Evaluation
9. External Dataset Validation
10. Prototype Integration and API Validation
11. Discussion
12. Limitations
13. Conclusion

If conference page limits require compression, merge adjacent sections while retaining the evidence.

---

# Figures/tables for upgraded paper

Recommended figures:

1. system architecture;
2. aggregate forecasting comparison;
3. horizon-wise error;
4. representative forecast;
5. multi-seed/ablation summary;
6. threshold-event performance;
7. external-validation result;
8. prototype/API integration diagram or consistency result.

Recommended tables:

1. dataset/protocol summary;
2. main forecasting metrics;
3. robustness/ablation metrics;
4. threshold-event metrics;
5. external validation;
6. related-work comparison if space allows.

Avoid one full page per screenshot.

---

# What must remain prohibited

Do not reintroduce:

- old normalized MAEs as physical units;
- unsupported 10–15% downtime reduction;
- claims of real aviation-fleet deployment;
- claims of direct failure/RUL prediction from forecast-only data;
- claims that Bi-LSTM is superior unless new controlled evidence actually supports it;
- invented engineering safety thresholds;
- test-driven tuning disguised as validation.

---

# Recommended order of execution

1. Multi-seed Bi-LSTM.
2. Architecture ablation.
3. Feature ablation.
4. Threshold-event evaluation.
5. Moving-block bootstrap comparison.
6. External/public dataset selection and validation.
7. Corrected model integration into API path.
8. Expand related work.
9. Rewrite paper.
10. Final IEEE-style review.
11. Only then prepare arXiv submission.

---

# Minimum bar before arXiv

Before uploading the upgraded paper to arXiv, aim to have at least:

- current corrected benchmark;
- multi-seed robustness;
- one controlled ablation;
- threshold-event evaluation;
- stronger related work;
- improved layout;
- clearly documented limitations.

External real/public-data validation is strongly preferred before presenting the work as IEEE-competitive.

---

# Stronger bar before IEEE submission

For an IEEE-oriented submission, strongly prefer all of the following:

- external measured/public dataset;
- multi-seed robustness;
- feature or architecture ablation;
- dependence-aware uncertainty analysis;
- threshold-event evaluation;
- corrected model integrated into the API path;
- stronger literature review;
- compact, polished IEEE layout;
- no unsupported deployment claims.

---

# Execution rule

Do not optimize for a predetermined conclusion.

If simpler models continue to outperform deep learning, report that result and build the contribution around reproducible model selection and decision-level evaluation.

The scientific value comes from the quality of the protocol and evidence, not from forcing a deep-learning win.
