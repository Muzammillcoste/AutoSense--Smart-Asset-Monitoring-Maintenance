# Research V2 Execution Plan

## Objective

Turn the existing FYP research work into a scientifically defensible, reproducible experimental pipeline suitable for revising the research paper and preparing a possible preprint submission.

The project is an aviation ground-support-fleet predictive-maintenance prototype combining:

- IoT sensors / ESP32 hardware
- time-series forecasting models
- a monitoring/dashboard layer
- Salesforce-based enterprise maintenance workflows

The paper currently makes claims around Bi-LSTM forecasting for:

- engine temperature
- tyre pressure
- tyre temperature

Before revising the paper, verify the ML results properly and compare them against simple baselines under the same evaluation protocol.

### Core research question

**Does the Bi-LSTM forecasting approach provide a meaningful improvement over simpler time-series baselines for 24-hour-ahead sensor forecasting in this predictive-maintenance prototype?**

The ML task should be framed as:

**multi-step sensor forecasting for threshold-based predictive maintenance.**

Do not frame this work as direct equipment failure prediction or remaining useful life prediction unless the data and models explicitly support that claim.

---

## Why this work is needed

The original notebooks and paper contain methodological inconsistencies that must not be carried into the revised paper:

- different datasets have different sampling intervals;
- some notebooks interpret sample counts as hours;
- regression models previously used inappropriate classification metrics in some places;
- some paper metrics may have incorrect units;
- the original paper lacks baseline comparisons;
- some datasets are synthetic, so the paper must not imply real operational fleet data;
- old reported MAE values cannot be trusted until their evaluation logic and inverse scaling are audited;
- deployment/integration evidence must be separated from forecasting-accuracy evidence.

The goal is a clean apples-to-apples benchmark.

---

## Branch and repository rules

Repository:

`AutoSense---Smart-Asset-Monitoring-Maintenance`

Work only on:

`research-paper-v2`

Rules:

- Do not modify `main`.
- Do not rewrite git history.
- Do not delete original notebooks or saved models.
- Keep new research work under `research_v2/` whenever practical.
- Commit changes only to `research-paper-v2`.

---

## Existing work already completed

On branch `research-paper-v2`, there is:

`research_v2/baseline_evaluation.py`

It evaluates:

1. Persistence
2. Seasonal naive
3. Random Forest

using:

- chronological 80/20 split
- 7-day lookback
- true 24-hour forecast horizon
- sampling interval inferred from timestamps
- MAE
- RMSE
- R²

### Current baseline results

#### Engine temperature

Sampling interval: 1 hour

| Model | MAE | RMSE | R² |
|---|---:|---:|---:|
| Persistence | 10.154697 °C | 12.471393 | -0.804369 |
| Seasonal naive | 2.618820 °C | 3.447653 | 0.862107 |
| Random Forest | 1.672950 °C | 2.224658 | 0.942585 |

#### Tyre pressure

Sampling interval: 3 hours

| Model | MAE | RMSE | R² |
|---|---:|---:|---:|
| Persistence | 0.561938 PSI | 0.983938 | 0.801552 |
| Seasonal naive | 0.787098 PSI | 1.247241 | 0.681131 |
| Random Forest | 0.649521 PSI | 0.920395 | 0.826355 |

#### Tyre temperature

Sampling interval: 3 hours

| Model | MAE | RMSE | R² |
|---|---:|---:|---:|
| Persistence | 5.794802 °C | 7.117293 | -0.838433 |
| Seasonal naive | 3.897779 °C | 4.971588 | 0.102967 |
| Random Forest | 2.898011 °C | 3.661618 | 0.513409 |

---

## Important dataset facts

### Engine temperature

Relevant dataset:

`FYP ML Training and Pipeline Code/Engine Temperature/karachi_2024_vehicle_temperature_data.csv`

Facts:

- synthetic dataset;
- hourly sampling;
- generated with deterministic daily/yearly structure, noise, spikes, trend, and weather-period effects;
- must not be described as historical operational fleet data.

For this dataset:

- 24 samples = 24 hours
- 168 samples = 7 days

### Tyre pressure

Relevant generated dataset:

`FYP ML Training and Pipeline Code/TP_Generated/tyre_pressure_2024.csv`

Facts:

- sampling interval is 3 hours;
- target is in PSI.

Therefore:

- 8 samples = 24 hours
- 56 samples = 7 days

The current paper reports tyre-pressure MAE in MPa. This is likely a unit issue and must be verified from the evaluation code before retaining any claim.

### Tyre temperature

Relevant dataset:

`FYP ML Training and Pipeline Code/Tyre Temperature/tyre_temp_2024.csv`

Facts:

- sampling interval is 3 hours.

Therefore:

- 8 samples = 24 hours
- 56 samples = 7 days

---

## Existing saved models

### Engine temperature

`FYP ML Training and Pipeline Code/Engine Temperature/Final_Temp_Prediction_Model.h5`

### Tyre pressure

`FYP ML Training and Pipeline Code/TP_Generated/Final_TP_Prediction_Model.h5`

### Tyre temperature

`FYP ML Training and Pipeline Code/Tyre Temperature/Final_Tyre_Temp_Prediction_Model.h5`

Related scaler files also exist.

Duplicate models/scalers exist under:

`Models and scripts/model_scaler/`

Prefer the original model/scaler paths under the FYP ML directories unless there is a specific reason not to.

---

## Existing notebook architecture

The engine Bi-LSTM training notebook uses approximately:

- 168-hour lookback
- 24-step output for hourly engine data
- engineered temporal features
- 24-hour lag
- 72-hour rolling mean
- stacked Bidirectional LSTM layers
- final Dense(24)
- chronological split
- MinMaxScaler fit on train only

This high-level setup is reasonable for the hourly engine dataset.

Do not assume the same sample-count interpretation is correct for tyre datasets because they are 3-hour sampled.

---

# Primary task

Create a reproducible Bi-LSTM evaluation pipeline that allows fair comparison with the existing baselines.

Create:

`research_v2/bilstm_evaluation.py`

The script should evaluate all three targets.

---

## Evaluation requirements

Use the same high-level protocol as the baseline script:

- chronological split
- no shuffling
- no test leakage
- 7-day lookback in clock time
- 24-hour forecast horizon in clock time
- infer sampling interval from timestamps
- convert hours to sample counts
- MAE
- RMSE
- R²

Correct time/sample mappings:

| Dataset | Sampling | Lookback | Horizon |
|---|---:|---:|---:|
| Engine temperature | 1 h | 168 steps | 24 steps |
| Tyre pressure | 3 h | 56 steps | 8 steps |
| Tyre temperature | 3 h | 56 steps | 8 steps |

---

## Critical decision: reuse saved models or retrain?

First inspect the saved models and original training notebooks.

Determine whether each saved model's input and output shapes are compatible with the correct true-time protocol above.

If a saved model was trained using 24 output samples on a 3-hour dataset, it predicts 72 hours rather than 24 hours.

In that case:

1. document the mismatch;
2. do not misleadingly report it as a 24-hour model;
3. retrain a corrected Bi-LSTM for that dataset with an 8-step output horizon;
4. use the corrected model for the fair benchmark.

If the saved engine model is compatible with a 168-step input and 24-step output, it may be evaluated directly only if preprocessing and feature ordering can be reconstructed exactly.

If exact preprocessing cannot be guaranteed, retrain using the clean standardized pipeline.

Scientific reproducibility is more important than preserving old model files.

---

## Preferred standardized training approach

If retraining is required, use a clean common experimental structure.

Preferred alignment with the current baseline split:

- final 20% is untouched test data;
- first 80% is the training region;
- reserve the last 10–15% of the training region for validation.

Alternative 70/10/20 split is acceptable if clearly documented, but final model-vs-baseline comparisons must use aligned test periods whenever possible.

Rules:

- do not fit scalers on validation or test data;
- do not shuffle time series;
- use deterministic/fixed random seeds;
- document all split boundaries.

Suggested seeds:

```python
random.seed(42)
np.random.seed(42)
tf.random.set_seed(42)
```

---

## Features

At minimum, use historical target values.

Optional engineered temporal features from the original notebooks may be reproduced:

- hour sin/cos
- day-of-week sin/cos
- month sin/cos
- weekend
- rush-hour where appropriate
- previous-day lag
- rolling mean

Rules:

- every feature must use only information available at or before prediction time;
- no future-derived rolling windows;
- no leakage from test data;
- avoid unnecessary complexity that makes the comparison harder to explain;
- prefer a consistent feature-engineering design across datasets, adjusted only for cadence.

---

## Model architecture

Stay close to the original Bi-LSTM family rather than inventing an unrelated model.

A reasonable reference architecture is:

- Bidirectional LSTM(128, return_sequences=True)
- BatchNormalization
- Dropout
- Bidirectional LSTM(64, return_sequences=True)
- BatchNormalization
- Dropout
- LSTM(32)
- Dense(64, activation='relu')
- Dropout
- Dense(horizon_steps)

Loss:

`mse`

Training metric:

`mae`

Do not use classification metrics such as:

- accuracy
- precision
- recall

Use `EarlyStopping` with best-weight restoration.

Suggested settings:

- monitor `val_loss`
- patience around 5–8
- `restore_best_weights=True`

Keep local CPU runtime reasonable.

If the original large model is too slow:

1. first reduce epochs and use EarlyStopping;
2. only then moderately reduce LSTM units;
3. document any architecture change explicitly;
4. do not silently replace the model with something scientifically different.

---

## Metrics

All final reported metrics must be computed after converting predictions back to original physical units.

Report:

- MAE
- RMSE
- R²

For the main aggregate comparison, flatten across all forecast horizons to match the baseline evaluation.

Also output horizon-wise metrics if practical.

### Horizon examples

Engine:

`t+1h ... t+24h`

Tyre datasets:

`t+3h, t+6h, ... t+24h`

---

## Required output files

Generate:

`research_v2/results/bilstm_metrics.csv`

Suggested columns:

- Dataset
- Model
- MAE
- RMSE
- R2
- Sampling interval (h)
- Lookback (h)
- Forecast horizon (h)
- Lookback steps
- Horizon steps
- Test windows
- Unit
- Model source
- Retrained

Also generate, if practical:

`research_v2/results/bilstm_horizon_metrics.csv`

Then create:

`research_v2/results/final_comparison.csv`

combining:

- Persistence
- Seasonal naive
- Random Forest
- Bi-LSTM

for all three datasets.

If `research_v2/results/baseline_metrics.csv` is not available locally, run:

```powershell
python research_v2/baseline_evaluation.py
```

---

# Additional audit task

Inspect the original notebooks that produced or supported the paper metrics.

### Engine

- `FYP ML Training and Pipeline Code/Engine Temperature/Testing_Pipeline.ipynb`
- `FYP ML Training and Pipeline Code/Engine Temperature/Training_LSTM_Karachi.ipynb`
- relevant engine training notebooks if needed

### Tyre pressure

- `FYP ML Training and Pipeline Code/TP_Generated/Testing_Pipeline_TP.ipynb`
- `FYP ML Training and Pipeline Code/TP_Generated/Training_LSTM_TP.ipynb`
- inspect `FYP ML Training and Pipeline Code/Tyre Pressure/Training_TP.ipynb` if relevant to the reported result

### Tyre temperature

- `FYP ML Training and Pipeline Code/Tyre Temperature/Testing_Pipeline_Temp.ipynb`
- `FYP ML Training and Pipeline Code/Tyre Temperature/Training_LSTM_Tyre_Temp.ipynb`

Determine exactly:

- how MAE was calculated;
- whether predictions were inverse-transformed;
- whether MAE was in normalized units or physical units;
- which dataset was used;
- what forecast horizon was actually predicted;
- what the sampling interval was;
- whether sample counts were mislabeled as hours;
- whether there was demonstrable data leakage;
- whether paper values can be reproduced.

---

## High-priority metric audit

### Engine MAE ≈ 0.1795 °C

This value appears unusually low relative to the synthetic dataset noise and requires careful audit.

Do not accuse the old model of leakage unless the exact mechanism is demonstrated.

Possible explanations to test include:

- normalized MAE being reported as °C;
- incorrect or incomplete inverse transformation;
- different dataset/evaluation path;
- overlapping-window effects;
- highly predictable synthetic structure;
- another evaluation artifact.

### Tyre pressure MAE ≈ 0.2368 MPa

The relevant generated tyre-pressure dataset uses PSI.

Verify whether:

- `0.2368` is actually PSI;
- it was mislabeled as MPa;
- a conversion occurred somewhere;
- the paper result came from a different tyre-pressure dataset.

Do not retain MPa unless the code proves it.

---

## Reproducibility requirements

At runtime, print a concise summary including:

- Python version
- TensorFlow version
- NumPy version
- dataset path
- number of rows
- sampling interval
- lookback steps
- horizon steps
- train/validation/test sizes
- model input/output shape
- whether a saved model or retrained model was used

Save all final results to CSV.

---

## Environment

Preferred Python:

`3.11`

Existing requirements file:

`Models and scripts/requirements.txt`

Current dependencies include:

- numpy==2.0.2
- pandas==2.2.2
- tensorflow==2.18.0
- requests==2.32.3
- scikit-learn

If a research-specific requirements file is needed, add:

`research_v2/requirements.txt`

Do not unnecessarily break the existing environment.

### Windows compatibility

The user may execute this project from PowerShell on Windows.

Use `pathlib.Path` for paths.

Paths contain spaces, so avoid fragile shell/string assumptions.

Do not rely on Linux-only shell syntax in required run instructions.

---

# Scientific decision rules

After the experiment:

- compare Bi-LSTM against the best baseline for each dataset;
- calculate percentage MAE improvement where appropriate;
- do not claim superiority if Bi-LSTM does not outperform the best baseline;
- if Bi-LSTM wins on only one or two targets, report that explicitly;
- if a simple persistence model beats Bi-LSTM on tyre pressure, report that honestly;
- do not cherry-pick metrics or datasets;
- favor reproducible findings over old paper claims.

The revised paper must be built around what the experiments actually show.

---

# Research-paper implications

Do not rewrite the paper yet. Finish the experiment and audit first.

Once final metrics are reliable, the paper should follow these principles:

- frame the ML contribution as sensor forecasting for threshold-based predictive maintenance;
- explicitly state which datasets are synthetic;
- remove unsupported `10–15% downtime reduction` claims unless real measured evidence exists;
- describe Salesforce as an enterprise maintenance/service workflow layer rather than ERP unless a true ERP component is present;
- remove classification metrics from regression evaluation;
- report correct physical units;
- explain true sampling intervals;
- compare Bi-LSTM against credible baselines;
- include limitations;
- separate prototype deployment evidence from ML accuracy evidence;
- avoid implying operational aviation deployment when evidence supports a prototype/use-case demonstration only.

---

# Deliverables

When the work is complete, provide:

1. files created/modified;
2. exact commands used;
3. environment details;
4. whether saved models were usable or retraining was required;
5. final metrics table;
6. baseline-vs-Bi-LSTM comparison;
7. percentage improvement/degradation relative to the best baseline;
8. audit of old paper metrics;
9. identified methodological problems;
10. unresolved issues or blockers;
11. recommended paper claims;
12. claims that must be removed or rewritten;
13. git diff summary;
14. commit hash(es), if commits were made.

---

# Execution behavior

Do not stop at the first error.

Diagnose environment or code issues, fix them on `research-paper-v2`, rerun, and continue until either:

- final results are available; or
- there is a concrete blocker that genuinely requires user input.

Do not ask the user to manually perform steps that can reasonably be handled within the repository/task environment.

---

# Final reporting format

End all work with a section titled exactly:

## REPORT FOR CHATGPT REVIEW

Include in that section:

- final aggregate metrics for all models and all three datasets;
- horizon-wise metrics if produced;
- saved-model vs retraining decisions;
- exact explanation of old reported MAE values where determinable;
- unit corrections;
- sampling/horizon corrections;
- evidence of any leakage or explicit statement that leakage was not demonstrated;
- methodological decisions;
- strongest scientifically defensible conclusions;
- paper claims that should not be retained;
- remaining uncertainties.

The user will paste this report into ChatGPT for scientific review and research-paper rewriting.
