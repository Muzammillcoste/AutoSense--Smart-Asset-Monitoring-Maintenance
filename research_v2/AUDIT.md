# Audit of the originally reported results

The original project report and paper draft stated three forecasting errors and a downtime claim. This audit traces each one to the notebook that produced it, reproduces it from the saved model, and states what it actually measures. None of the original files was modified.

## Summary

| Original claim | What it actually is | Physical-unit equivalent | Status |
|---|---|---|---|
| Engine MAE **0.1795 °C** | Normalized (0–1 scaled) MAE from an older notebook that uses a *UAE* dataset, not the Karachi data | ≈ 17.86 °C | Not a valid °C result |
| Tyre-pressure MAE **0.2368 MPa** | Normalized MAE from a notebook trained on 10% of the data | 1.838 PSI | Neither PSI nor MPa |
| Tyre-temperature MAE **0.344 °C** | No matching value found; the matching notebook gives normalized MAE 0.3414 | 6.984 °C (for 0.3414) | Source unresolved |
| **10–15% downtime reduction** | A stated goal; never measured | – | Unsupported |

The original notebooks also had several methodological problems (listed under "Methodological issues" below). For these reasons, all models were retrained under a single corrected protocol; see [`BENCHMARK_REPORT.md`](BENCHMARK_REPORT.md).

## Method

- **Notebook evidence.** [`results/notebook_evidence.json`](results/notebook_evidence.json) stores the source and saved text outputs of each original notebook. Cell numbers in this document are **zero-based** and refer to that file. Saved outputs are historical evidence, not new training runs.
- **Reproduction scripts.**
  - [`audit_originals.py`](audit_originals.py) rebuilds each notebook's feature function, checks the saved scaler against a newly fitted one, loads the saved model (`compile=False`) and repeats its original test evaluation. Output: [`results/legacy_model_audit.json`](results/legacy_model_audit.json).
  - [`audit_uae_legacy.py`](audit_uae_legacy.py) does the same for the older UAE engine model. Output: [`results/uae_legacy_audit.json`](results/uae_legacy_audit.json).

## Engine temperature: the 0.1795 °C value

**Source.** `Engine Temperature/Training_LSTM.ipynb`:

- Cell 1 reads `vehicle_engine_temperature_UAE_Vehicle0018.csv`, not the Karachi dataset.
- Cells 6–9 split the engineered rows 80/20, fit a MinMaxScaler on the training part and build scaled targets.
- Cell 15 runs `model.evaluate(X_test, y_test)` and stores MAE **0.1794579178094864**, which rounds to 0.1795.

No inverse scaling happens before this metric is computed. Cells 16–18 inverse-transform predictions only for a later plot.

**Meaning.** 0.1795 is a dimensionless, normalized MAE, not degrees Celsius. The first target's training range in that file is 99.54479405 °C, so the value corresponds to about **17.86410147 °C**. This assumes the stored output came from exactly this local file and preprocessing.

**Reproduction.** A fresh inference run (`audit_uae_legacy.py`) over 1,122 legacy test windows gives:

| Metric | Value |
|---|---:|
| Normalized MAE | 0.1794579465 |
| MAE | 17.86410433 °C |
| RMSE | 22.24166435 |
| R² | −0.78475507 |

**Keras migration.** Loading the old model needed an in-memory configuration migration; the original weights and files are unchanged. The migration:

- removes `time_major=False` while keeping the batch-major layout
- turns single-element batch-normalization axis lists into scalars
- renames the input-shape key

**Problems with this data and setup.**

- **Not a clean series.** The UAE file has 6,000 rows, mostly at 3-hour cadence. At raw row 2,600 the timestamps jump backwards to 1 January 2024. Fixed-cadence windows that cross this jump are invalid.
- **Different window lengths.** The notebook uses **40** input samples (nominally 120 h, not one week) and **24** output samples (nominally 72 h, not 24 h).
- **Duplicates but no leakage.** The training data contain duplicate timestamps. However, after the notebook drops its first 71 rows, no timestamp appears in both training and test, so the duplicates are not evidence of test leakage.

The metric's origin is confirmed, but this setup is not used as a benchmark.

## Engine temperature: the actual Karachi model

**Source.** `Engine Temperature/Training_LSTM_Karachi.ipynb`, cells 1–11:

- Uses the synthetic hourly Karachi data, with 168 inputs, 24 outputs and 11 features.
- Its stored normalized MAE is **0.0322**, not 0.1795.
- The saved model `Final_Temp_Prediction_Model.h5` has input shape (None, 168, 11) and 24 outputs.
- The saved scaler's feature names, scale and offset match the reconstruction within numerical tolerance.

**Reproduction.** A fresh run over 1,546 original test windows, starting 26 October at 15:00, gives:

| Metric | Value |
|---|---:|
| Normalized MAE | 0.03223978 |
| MAE | 1.73429680 °C |
| RMSE | 2.30579606 |
| R² | 0.93795178 |

This test period and feature set differ from the corrected benchmark, so the numbers are not comparable with it.

## Tyre pressure: the 0.2368 MPa value

**Source.** `TP_Generated/Training_LSTM_TP.ipynb`:

- Cell 1 reads `tyre_pressure_2024.csv`; the target is `Tyre_Pressure_PSI`.
- Cell 5 uses a **10/90** train/test split, not 80/20.
- Cells 6–8 scale the data and build windows of 56 inputs and 8 outputs.
- Cell 12 reports **0.2368** on normalized targets, before any inverse transformation.

**Saved model.** It has the correct input (None, 56, 11) and 8 outputs: seven days of history and a 24-hour forecast at 3-hour cadence. Its saved scaler matches a reconstruction from the 10% training split.

**Reproduction.** A fresh run over 2,501 legacy test windows gives:

| Metric | Value |
|---|---:|
| Normalized MAE | 0.23684705 |
| MAE | 1.83820315 PSI |
| RMSE | 2.20478211 PSI |
| R² | −0.11054434 |

Neither "0.2368 PSI" nor "0.2368 MPa" is justified; no PSI-to-MPa conversion occurs anywhere in this path.

**Other notebook.** A separate notebook, `Tyre Pressure/Training_TP.ipynb`, is not the source of 0.2368. It:

- reads `tire_pressure_dataset_DXB_vehicle.csv` (5-hour cadence)
- uses 35 inputs and 24 outputs (175 h and 120 h)
- stores normalized MAE **0.0602**

## Tyre temperature: the 0.344 °C value

**Source.** `Tyre Temperature/Training_LSTM_Tyre_Temp.ipynb`, cells 6–14:

- Also uses a 10/90 split, 56 inputs and 8 outputs.
- The saved `Final_Tyre_Temp_Prediction_Model.h5` and `scaler_TTemp.pkl` match the notebook preprocessing. This holds even though cell 19 names a different scaler file (`scaler_TP.pkl`).

**Reproduction.** The stored normalized MAE of **0.3414** reproduces as 0.34135299 over 2,501 legacy windows:

| Metric | Value |
|---|---:|
| Normalized MAE | 0.34135299 |
| MAE | 6.98365678 °C |
| RMSE | 8.47299948 |
| R² | −0.98293088 |

The paper draft reports **0.344 °C**. That value cannot be obtained by ordinary rounding of 0.34135299, and no notebook produces it. Its source remains unresolved, and it is not used as a physical-unit result.

## Methodological issues found

1. **Train/test label overlap in the earlier baseline script.** The previous `research_v2/baseline_evaluation.py` split the data *after* building overlapping windows. The last training target window and the first test target window shared H − 1 timestamps: 23 hourly engine labels, or 7 three-hourly tyre labels. Random Forest therefore saw labels from the start of its test period. [`test_protocol.py`](test_protocol.py) reproduces this overlap. The corrected baselines were rerun.
2. **No such overlap in the original notebooks.** The original training notebooks split rows *before* creating windows, so the mechanism in issue 1 does not occur there.
3. **Validation contamination in the original notebooks.** `validation_split=0.1` acts on overlapping training windows, so targets on either side of the training/validation boundary share H − 1 timestamps. The scalers were also fitted before validation data were set aside, so they include validation extremes. Validation was therefore not strictly held out. This is contamination of validation, not proof of test leakage.
4. **Shuffling.** The original `model.fit` calls omit `shuffle=False`, so training windows were shuffled by default. The new pipeline disables shuffling explicitly.
5. **Misleading feature names.** In the tyre notebooks, `shift(24)` is a 72-hour lag, and `rolling(72)` is 72 samples (nine days at 3-hour cadence), not three days. These features look only backwards in time; only their names are wrong.
6. **Demonstration notebooks are not validation.**
   - The testing-pipeline notebooks generate hourly dummy tyre inputs, although the models were trained on 3-hourly data.
   - They label 8 one-hour-spaced outputs as 24-hour forecasts.
   - The engine demo generates only 168 rows. Feature warm-up then drops 71 of them, leaving too few for a full 168-step history.

   None of these plots provides a held-out forecast MAE.
7. **Plots misalign forecasts.** Some plotting routines join overlapping multi-step forecasts as if they were one continuous series, or align predictions to timestamps before their input window ends. The plots therefore cannot confirm the stated horizon or accuracy.
8. **Classification metrics on a regression task.** The older engine notebook compiles accuracy, precision and recall alongside MAE. These metrics are not valid measures of continuous forecast quality.

## Why the benchmark retrains all models

All three saved models have the correct input and output lengths, and their preprocessing can be reconstructed. None needs retraining because of a shape error. They were retrained anyway, for four reasons:

- to give every model the same training data
- to remove the validation contamination
- to give the Random Forest and the Bi-LSTM identical inputs
- to avoid mixing 10%-trained tyre models with an 80%-trained engine model

The architecture keeps the original 128/64/32 LSTM family. The input changes deliberately from 11 features to 1.

## Data provenance

All three local generator notebooks reproduce the benchmark CSVs, including timestamps, to floating-point precision (maximum absolute difference below 1.5 × 10⁻¹⁴). The checks are run by [`verify_generators.py`](verify_generators.py) and recorded in [`results/generator_verification.json`](results/generator_verification.json). The tyre-temperature generator is `Tyre Temperature/generating_data.ipynb`. All three datasets are therefore synthetic and must not be described as sensor-collected or operational fleet data.

## Consequences for the manuscript

The revised manuscript makes the following changes:

- **Accuracy claims.** It replaces the three original accuracy claims with results from the corrected, aligned benchmark.
- **Removed claims.** It drops the downtime-reduction claim, direct failure prediction and any claim of operational aviation validation, since this audit supports none of them.
- **Salesforce.** It describes Salesforce as a maintenance and service workflow layer. No evidence of a separate ERP component was found.
- **Evidence kept separate.** It reports prototype integration evidence separately from forecast accuracy.
