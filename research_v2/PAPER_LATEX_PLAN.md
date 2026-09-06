# Paper Rewrite and Figure Generation Plan

## Goal

Produce a revised, publication-ready LaTeX version of the research paper using only the corrected experiment results and verifiable prototype evidence from the repository.

The rewritten paper must reflect the actual findings from `research_v2` rather than preserving the old Bi-LSTM superiority narrative.

The final paper should present the work as:

**an integrated IoT-to-enterprise predictive-maintenance prototype with a rigorous comparative study of multi-step sensor forecasting methods.**

The forecasting task should be framed as:

**24-hour multi-step sensor forecasting for threshold-based predictive maintenance.**

Do not claim direct failure prediction, RUL prediction, real-fleet operational validation, or measured downtime reduction unless there is explicit evidence.

---

# Source of truth

Use these as the scientific source of truth:

- `research_v2/results/final_comparison.csv`
- `research_v2/results/bilstm_horizon_metrics.csv`
- `research_v2/results/baseline_metrics.csv`
- `research_v2/results/bilstm_metrics.csv`
- `research_v2/results/<dataset>/test_predictions.npz`
- `research_v2/results/<dataset>/metadata.json`
- `research_v2/REPORT_FOR_CHATGPT_REVIEW.md`
- `research_v2/AUDIT.md`
- `research_v2/results/generator_verification.json`
- `research_v2/results/legacy_model_audit.json`
- `research_v2/results/uae_legacy_audit.json`

Use the original paper only for:

- author names and affiliations;
- hardware/system descriptions that remain verifiable;
- original architecture and workflow context;
- existing screenshots/figures that are still valid prototype evidence;
- reference list as a starting point.

Do not copy old numerical ML claims unless independently supported by the corrected results.

---

# Branch and file rules

Work only on:

`research-paper-v2`

Do not modify `main`.

Do not delete the original PDF, notebooks, models, or screenshots.

Create the new paper under:

`research_v2/paper/`

Suggested structure:

```text
research_v2/paper/
    main.tex
    references.bib
    figures/
    tables/
    build/
```

Keep figure-generation code under:

`research_v2/figure_generation/`

Suggested files:

```text
research_v2/figure_generation/
    generate_model_comparison.py
    generate_engine_forecast.py
    generate_horizon_metrics.py
    generate_architecture_diagram.py   # optional if code-generated
```

All generated figures should be deterministic and reproducible from committed data.

---

# LaTeX format

Use an IEEE conference-style LaTeX layout unless a more appropriate venue format is already present in the repository.

Preferred document class:

```latex
\documentclass[conference]{IEEEtran}
```

Use conventional IEEE-style sections such as:

1. Introduction
2. Related Work
3. System Architecture
4. Forecasting Methodology
5. Experimental Setup
6. Results and Discussion
7. Prototype Integration and Workflow Validation
8. Limitations
9. Conclusion and Future Work

Do not use placeholder headings such as `SOME FEATURES`.

Remove placeholder IEEE copyright/footer text unless a real conference requires it.

---

# Proposed title

Use one of the following as the working title:

**Benchmarking Multi-Step Sensor Forecasting for Threshold-Based Predictive Maintenance: An Integrated IoT-to-Enterprise Framework**

Alternative:

**An IoT-to-Enterprise Framework for Predictive Maintenance with Comparative Multi-Step Sensor Forecasting**

Prefer the first unless layout/title length becomes problematic.

---

# Core scientific narrative

The revised paper should make the following sequence clear:

1. A prototype IoT pipeline monitors vehicle location, engine temperature, tyre pressure and tyre temperature.
2. The system connects monitoring data to forecast-generation and threshold-based maintenance logic.
3. Alerts feed an enterprise maintenance workflow implemented with Salesforce Cases/Flow.
4. The forecasting layer is benchmarked rigorously using persistence, seasonal naive, Random Forest and Bi-LSTM.
5. On the corrected synthetic benchmark, simpler methods outperform Bi-LSTM on all three targets.
6. Therefore, model complexity alone is not sufficient; benchmark-based model selection is important in predictive-maintenance pipelines.
7. The system contribution is the integration of telemetry, forecasting, threshold logic and enterprise workflow, not a claim that Bi-LSTM is universally superior.

---

# Final benchmark values to use

Use the values from `research_v2/results/final_comparison.csv` directly.

### Engine temperature

- Persistence MAE: 10.156758 °C
- Seasonal naive MAE: 2.623008 °C
- Random Forest MAE: 1.708059 °C
- Bi-LSTM MAE: 6.199389 °C

### Tyre pressure

- Persistence MAE: 0.558283 PSI
- Seasonal naive MAE: 0.780869 PSI
- Random Forest MAE: 0.735564 PSI
- Bi-LSTM MAE: 1.177751 PSI

### Tyre temperature

- Persistence MAE: 5.785863 °C
- Seasonal naive MAE: 3.897419 °C
- Random Forest MAE: 2.896952 °C
- Bi-LSTM MAE: 6.453655 °C

Include RMSE and R² in a table, but avoid overcrowding figures with all metrics.

Do not describe these as operational fleet measurements; all three benchmark datasets are synthetic.

---

# Figures to generate

## Figure 1 — System architecture

Create a clean architecture diagram showing:

```text
Vehicle Sensors
   ↓
ESP32-S3
   ↓
Telemetry/API
   ↓
Swift Platform / Data Layer
   ↓
Forecasting Service
   ↓
Threshold / Alert Logic
   ↓
Salesforce Case / Maintenance Workflow
   ↓
Resolution / Status Feedback
   ↓
Dashboard
```

Include GPS, DS18B20 and BLE TPMS as small labels under the sensor layer if visually clean.

Do not label Salesforce as ERP. Use:

**Salesforce maintenance/service workflow layer**

unless separate evidence establishes a true ERP subsystem.

Preferred output:

`research_v2/paper/figures/system_architecture.pdf`

Use vector output where possible.

---

## Figure 2 — Forecasting model MAE comparison

Generate a publication-quality comparison of the four models.

Because target units differ, do not put raw engine/tyre-temperature °C and tyre-pressure PSI values onto a single shared numeric axis.

Preferred design:

- three separate panels;
- one panel per target;
- four bars in each panel:
  - Persistence
  - Seasonal Naive
  - Random Forest
  - Bi-LSTM

Y-axis units:

- Engine Temperature: MAE (°C)
- Tyre Pressure: MAE (PSI)
- Tyre Temperature: MAE (°C)

Use exact values from `final_comparison.csv`.

Do not manually type numbers if the script can read the CSV.

Save as:

`research_v2/paper/figures/model_mae_comparison.pdf`

Also save PNG preview if useful.

---

## Figure 3 — Representative 24-hour engine forecast comparison

Use the saved test predictions under:

`research_v2/results/engine_temperature/`

Plot one representative forecast window containing:

- Actual
- Random Forest
- Bi-LSTM

X-axis:

`Forecast Horizon (h)`

1 through 24.

Y-axis:

`Engine Temperature (°C)`

### Window-selection rule

Do not cherry-pick a visually flattering example.

Choose a deterministic representative window using one of these rules:

1. the test window whose Random Forest MAE is closest to the median Random Forest window MAE;
2. if Random Forest per-window predictions are unavailable, use the middle test forecast origin chronologically;
3. document the chosen rule in figure-generation code.

If Random Forest predictions are not currently persisted, modify the evaluation pipeline to save them rather than reconstructing them inconsistently.

Save as:

`research_v2/paper/figures/engine_24h_forecast_comparison.pdf`

---

## Figure 4 — Horizon-wise forecast error

Generate horizon-wise MAE curves from the corrected evaluation.

Preferred figure:

- three panels, one per dataset;
- compare Random Forest and Bi-LSTM if both horizon-wise results are available;
- optionally add persistence if the figure remains readable.

Engine x-axis:

1, 2, ..., 24 hours

Tyre x-axis:

3, 6, 9, ..., 24 hours

Y-axis:

MAE in physical units.

If horizon-wise baseline predictions are not saved, extend the analysis code to compute them from the same aligned test predictions. Do not fabricate or approximate them from aggregate metrics.

Save as:

`research_v2/paper/figures/horizon_mae_comparison.pdf`

---

## Optional Figure 5 — Error distribution

Only create this if space allows and it adds value beyond Figure 4.

Preferred form:

- absolute-error boxplot or violin plot;
- Random Forest vs Bi-LSTM;
- separate panel per target.

Do not use the old normalized-error histogram.

Save as:

`research_v2/paper/figures/error_distribution_comparison.pdf`

This figure is optional and should be omitted if it crowds the paper.

---

# Existing figures/screenshots to retain

Retain prototype figures only if still supported by the repository/project evidence.

Preferred retained evidence:

1. Hardware schematic / PCB figure
2. Salesforce Vehicle Alert / Case screenshot
3. Sensor Data View / threshold-monitoring screenshot
4. Dashboard screenshots only if space permits

Do not keep all four dashboard screenshots individually if they consume too much space.

Prefer combining dashboard screenshots into one composite figure with sublabels:

- (a) Real-time fleet map
- (b) Sensor view
- (c) Forecast view
- (d) Salesforce maintenance case

Suggested final combined figure:

`research_v2/paper/figures/prototype_interfaces.pdf`

If source images are too low resolution, reuse them only temporarily and leave a TODO noting that higher-resolution originals are needed.

---

# Figures to remove from the old paper

Remove/replace the old figures that support invalid or obsolete ML claims:

- old Bi-LSTM-only 24-hour engine forecast;
- old training/validation MAE chart as a main scientific result;
- old normalized prediction-error histogram;
- redundant temperature actual-vs-predicted plot if new comparative forecast plot is present.

Training curves may be retained in supplementary material or appendix only if useful.

---

# Tables to create

## Table I — Dataset and protocol summary

Columns:

- Target
- Dataset type
- Rows
- Sampling interval
- Lookback
- Forecast horizon
- Train windows
- Validation windows
- Test windows
- Unit

Clearly mark all three datasets as synthetic.

---

## Table II — Main model comparison

Columns:

- Target
- Model
- MAE
- RMSE
- R²

Use `final_comparison.csv` directly.

Bold the best MAE/RMSE per target only if scientifically appropriate.

Do not bold Bi-LSTM unless it actually wins a metric.

---

## Optional Table III — Legacy audit summary

Include only if the paper has enough space and the audit itself is part of the contribution.

Possible columns:

- Old paper claim
- Actual provenance
- Correct interpretation

Examples:

- `0.1795°C` → normalized MAE from older UAE engine notebook → not physical °C
- `0.2368 MPa` → normalized tyre-pressure MAE → not MPa
- `0.344°C` → exact provenance unresolved

If this table makes the paper feel like a correction note rather than a research paper, keep these details in methodology/limitations instead.

---

# Section-by-section rewrite plan

## Abstract

Rewrite completely.

The abstract should include:

- system objective;
- IoT hardware and telemetry stack;
- 24-hour forecasting benchmark;
- four compared models;
- actual best-model findings;
- Salesforce maintenance workflow integration;
- limitation that evaluation uses synthetic datasets.

Do not include:

- old 0.1795°C claim;
- 0.2368 MPa;
- 0.344°C;
- 10–15% downtime reduction;
- statements that Bi-LSTM forecasts failures with high accuracy.

---

## Introduction

Keep the predictive-maintenance motivation, but remove unsupported operational claims.

End the introduction with explicit contributions such as:

1. an end-to-end IoT-to-maintenance workflow prototype;
2. a standardized 24-hour forecasting benchmark across three sensor variables;
3. comparison of simple, classical and deep-learning forecasting methods;
4. integration of threshold alerts with Salesforce maintenance Cases;
5. evidence that model complexity does not guarantee better performance on the evaluated synthetic sensor data.

---

## Related Work

Separate literature into:

- predictive maintenance and fleet monitoring;
- IoT-based maintenance architectures;
- time-series forecasting for equipment/sensor signals;
- enterprise maintenance workflow integration.

Do not overstate cited work as directly validating this specific system.

Review references for accuracy and relevance.

Do not invent bibliographic entries.

---

## System Architecture

Describe:

- ESP32-S3;
- GPS;
- DS18B20;
- BLE TPMS;
- data transmission;
- Swift dashboard/platform;
- forecasting service;
- threshold logic;
- Salesforce Case and Flow integration.

Use the new architecture figure.

Replace the phrase `ERP Integration` with `Enterprise Maintenance Workflow Integration` unless actual ERP functionality is demonstrated.

---

## Forecasting Methodology

This section should describe the corrected experiment, not the old notebooks.

Include:

- three synthetic datasets;
- timestamp validation;
- sampling intervals;
- 7-day lookback in true clock time;
- 24-hour forecast horizon;
- chronological partitioning;
- no target overlap across train/validation/test boundaries;
- train-only scaler fitting;
- no shuffle;
- seed 42;
- persistence baseline;
- seasonal naive baseline;
- Random Forest;
- Bi-LSTM architecture;
- MAE, RMSE and R².

Clarify that the benchmark uses historical target values only for learned models to align information access.

---

## Experimental Setup

Include environment details only as much as useful:

- Python 3.11.9
- TensorFlow 2.18.0
- NumPy 2.0.2
- pandas 2.2.2
- scikit-learn 1.9.0
- CPU execution
- fixed 20-epoch max
- early stopping
- batch size 64

Avoid making the paper read like a software log.

---

## Results and Discussion

This is the most important rewritten section.

Use Table II plus Figures 2–4.

State directly:

- Random Forest achieved the lowest MAE for engine temperature;
- Persistence achieved the lowest MAE for tyre pressure;
- Random Forest achieved the lowest MAE for tyre temperature;
- Bi-LSTM did not outperform the best baseline on any of the three targets in this fixed experimental setup.

Do not present this as failure of the entire system.

Interpretation should focus on:

- synthetic structure may favor simpler autoregressive/seasonal models;
- deep-learning capacity does not automatically improve forecasting;
- baseline benchmarking is necessary before selecting complex models;
- one fixed run does not prove Bi-LSTM can never perform better;
- tyre-pressure Bi-LSTM reached the epoch cap, so convergence is not fully established.

Do not perform test-driven tuning after seeing results unless a new experimental protocol is defined before running it.

---

## Prototype Integration and Workflow Validation

Keep verifiable system-integration evidence:

- sensor data transmission;
- dashboard ingestion;
- forecast endpoint integration;
- Salesforce alert/Case creation;
- status feedback loop.

Be precise about what was tested.

Do not claim measured operational downtime reduction.

If latency values are retained, verify their provenance before including them.

---

## Limitations

Create an explicit limitations section.

Include:

- synthetic datasets;
- no external real-fleet validation;
- one chronological holdout period;
- one random seed;
- limited training budget;
- no full hyperparameter search;
- overlapping forecast origins yield dependent errors;
- no maintenance-outcome labels;
- no direct failure/RUL prediction;
- no measured downtime/cost reduction;
- no uncertainty intervals.

This section is mandatory.

---

## Conclusion

Conclusion should say that the work demonstrates an integrated prototype and comparative forecasting evaluation.

The strongest result is not `Bi-LSTM achieved high accuracy`.

Instead state that:

- the end-to-end prototype is technically feasible;
- simple baselines outperformed Bi-LSTM in the corrected synthetic-data benchmark;
- forecasting model selection should be evidence-driven;
- future work should prioritize real fleet data and external validation.

---

## Future Work

Prioritize:

1. real-world fleet data collection;
2. genuine failure/maintenance labels;
3. external validation;
4. uncertainty-aware forecasting;
5. richer CAN bus features;
6. model selection/tuning conducted under a pre-declared protocol;
7. potentially Transformers only after strong baselines remain established;
8. measured maintenance outcomes and cost/downtime studies.

Do not imply that a more complex model is automatically the next best step.

---

# Citation and reference rules

- Preserve useful references from the original paper only where they actually support the text.
- Verify every reference entry for author/title/year/venue before finalizing.
- Prefer DOI or official publisher metadata where available.
- Do not fabricate citations.
- Do not cite a generic deep-learning textbook for claims specific to Bi-LSTM predictive-maintenance performance unless appropriate.
- Separate system-component datasheet citations from scientific-method citations.

If web verification is unavailable to Codex, flag uncertain references for later review rather than guessing.

---

# LaTeX quality rules

- Use proper `\label{}` and `\ref{}` for every figure/table.
- Use `booktabs` for tables if compatible with IEEE format.
- Keep figures readable at single-column or double-column width.
- Prefer PDF/vector figures for plots.
- Keep raster screenshots at sufficient resolution.
- Ensure axis labels remain readable after IEEE two-column scaling.
- Do not use tiny legends.
- Avoid excessive colors; plots must remain interpretable in grayscale.
- Use consistent terminology throughout:
  - engine temperature
  - tyre pressure
  - tyre temperature
  - multi-step forecasting
  - threshold-based predictive maintenance
  - enterprise maintenance workflow
- Use either British `tyre` consistently or change everything to `tire`; do not mix styles.

---

# Build and verification

Codex should compile the LaTeX locally if a LaTeX environment is available.

Preferred commands:

```powershell
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

or use `latexmk` if installed.

Check:

- no undefined references;
- no missing citations;
- no figure overflow;
- no table overflow;
- no missing images;
- no placeholder text;
- no `XXX-X-XXXX` IEEE footer;
- no obsolete metrics;
- no unsupported downtime reduction claim;
- no use of `ERP` for Salesforce unless explicitly justified.

---

# Deliverables

Codex should create or update:

1. `research_v2/paper/main.tex`
2. `research_v2/paper/references.bib`
3. `research_v2/paper/figures/system_architecture.pdf`
4. `research_v2/paper/figures/model_mae_comparison.pdf`
5. `research_v2/paper/figures/engine_24h_forecast_comparison.pdf`
6. `research_v2/paper/figures/horizon_mae_comparison.pdf`
7. optional error-distribution figure if useful
8. figure-generation Python scripts
9. any LaTeX tables/data helper files
10. compiled PDF if LaTeX is available
11. a concise review report

Do not modify the old research paper PDF in place.

---

# Final Codex report

At completion, produce a section titled exactly:

## REPORT FOR CHATGPT PAPER REVIEW

Include:

- files created/modified;
- final title;
- full section structure;
- figures created and their data sources;
- deterministic rule used to select representative forecast window;
- tables created;
- claims removed from old paper;
- claims retained;
- claims newly introduced;
- any references that need external verification;
- LaTeX build status;
- page count;
- warnings/overfull boxes;
- unresolved issues;
- commit hash.

Also state explicitly whether the final LaTeX paper contains any of the following prohibited/obsolete claims:

- `0.1795°C` engine MAE
- `0.2368 MPa` tyre-pressure MAE
- `0.344°C` tyre-temperature MAE as validated physical error
- `10–15% downtime reduction`
- Bi-LSTM superiority over baselines
- direct failure prediction
- real-fleet operational validation

The expected answer for all of these should be `No`, unless new verified evidence is provided.

---

# Execution behavior

Work end-to-end rather than stopping after generating scripts.

Run the figure-generation code.

Compile the LaTeX if possible.

Fix obvious LaTeX/layout errors.

Do not alter scientific results to make the paper look stronger.

Do not tune models further in this task.

If a required figure cannot be generated because prediction data are missing, modify the research evaluation utilities only enough to persist the already-defined aligned predictions; do not change the experiment itself.

Keep every scientific figure traceable to committed `research_v2/results` data.
