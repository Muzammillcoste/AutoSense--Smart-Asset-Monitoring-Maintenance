# Audit of original results

Evidence: `results/notebook_evidence.json` contains notebook source and stored text outputs with **zero-based** cell numbers. `audit_originals.py` reconstructs the feature function, checks the saved scaler against a newly fitted scaler, loads each designated model with `compile=False`, and reproduces its original test evaluation. The original files are unchanged. Stored notebook text is historical evidence, not a fresh training run.

## Reported engine MAE 0.1795 degrees Celsius

`Engine Temperature/Training_LSTM.ipynb`, cell 1, reads `vehicle_engine_temperature_UAE_Vehicle0018.csv`, not the Karachi dataset. Cells 6-9 split the engineered rows 80/20, fit MinMaxScaler on training, and build scaled targets. Cell 15 calls `model.evaluate(X_test, y_test)` and stores MAE **0.1794579178094864**, rounded to **0.1795**. No inverse transformation occurs before this metric. Cells 16-18 inverse-transform predictions for a later example plot; this does not convert the earlier MAE.

Thus 0.1795 is dimensionless normalized MAE, not degrees Celsius. Reconstructing that notebook's first target training range from the local CSV gives 99.54479405 degrees Celsius; the stored unrounded MAE corresponds algebraically to about **17.86410147 degrees Celsius** if the notebook output belongs to precisely that local file/preprocessing. A separate fresh inference run (`audit_uae_legacy.py`) also reproduces normalized MAE **0.1794579465**, physical MAE **17.86410433 degrees Celsius**, RMSE **22.24166435**, and R2 **-0.78475507** over 1,122 legacy test windows. The old Keras model requires explicit in-memory configuration migration: remove `time_major=False` while retaining batch-major layout, convert singleton batch-normalization axis lists to scalars, and rename the input shape key. Original weights and files are unchanged. This confirms the metric provenance, but the flawed legacy protocol must not become the new paper benchmark.

The local UAE file has 6,000 rows, predominantly three-hour cadence, with a backward timestamp jump at raw row 2,600 to January 1, 2024. It is not a clean monotonic series. The notebook uses **40** input samples (nominally 120 hours, not a week) and **24** output samples (nominally 72 hours, not 24). The discontinuity invalidates fixed-cadence windows that cross it. There are duplicate timestamps inside the fitting data, but no train/test timestamp intersection was found for this notebook's raw-row split after dropping its first 71 rows. This is not evidence of test leakage from the duplicated timestamps.

## Actual designated Karachi engine model

`Engine Temperature/Training_LSTM_Karachi.ipynb`, cells 1-11, uses the synthetic hourly Karachi file, 168 inputs, 24 outputs and 11 features. Stored normalized MAE is **0.0322**, not 0.1795. `Final_Temp_Prediction_Model.h5` has input `(None,168,11)` and 24 outputs. The saved scaler's feature names, scale and offset match reconstruction exactly within numerical comparison tolerance.

Fresh legacy-path inference reproduces normalized MAE **0.03223978**, equivalent to **1.73429680 degrees Celsius**, RMSE **2.30579606**, R2 **0.93795178** over 1,546 original test windows beginning October 26 at 15:00. This is a different test period and feature setup from the new common benchmark.

## Reported tyre-pressure MAE 0.2368 MPa

`TP_Generated/Training_LSTM_TP.ipynb`, cell 1, reads `tyre_pressure_2024.csv`, whose target is `Tyre_Pressure_PSI`. Cell 5 uses a **10/90**, not 80/20, train/test split. Cells 6-8 scale and build 56-input/8-output windows. Cell 12 reports **0.2368** on normalized targets before subsequent inverse-transformed plotting.

The designated saved model already has the correct input `(None,56,11)` and 8 outputs: at three-hour cadence this is seven days of history and a 24-hour forecast. Its saved scaler matches the 10%-training reconstruction. Fresh inference reproduces normalized MAE **0.23684705**, corresponding to **1.83820315 PSI**, RMSE **2.20478211 PSI**, R2 **-0.11054434** over 2,501 legacy test windows. Neither 0.2368 PSI nor 0.2368 MPa is justified. No PSI-to-MPa conversion occurs in this evaluation path.

The separate `Tyre Pressure/Training_TP.ipynb` reads `tire_pressure_dataset_DXB_vehicle.csv` (five-hour cadence), uses 35 inputs and 24 outputs (175 and 120 hours), and stores normalized MAE **0.0602**, not 0.2368. It is not the matching source for the reported 0.2368 value.

## Tyre temperature

`Tyre Temperature/Training_LSTM_Tyre_Temp.ipynb`, cells 6-14, likewise uses 10% training and 90% test, 56 inputs and 8 outputs. Saved `Final_Tyre_Temp_Prediction_Model.h5` and `scaler_TTemp.pkl` match the notebook preprocessing, despite cell 19 specifying a different scaler output filename (`scaler_TP.pkl`). Stored normalized MAE **0.3414** reproduces as **0.34135299**, giving physical MAE **6.98365678 degrees Celsius**, RMSE **8.47299948**, R2 **-0.98293088** over 2,501 legacy windows.

The actual paper DOCX reports **0.344 degrees Celsius**, not 0.3414. The exact 0.344 value was not established by this matching notebook and cannot be explained as ordinary rounding of 0.34135299. Its provenance remains unresolved; it must not be retained as a physical-unit result.

## Demonstrated methodological defects and leakage distinctions

- The former `research_v2/baseline_evaluation.py` split overlapping supervised windows. Last training / first test labels shared H-1 timestamps: 23 hourly engine labels, or 7 three-hour tyre labels. Random Forest therefore saw labels from the start of its nominal test period. This exact overlap is checked by `test_protocol.py`. Corrected baselines must be rerun.
- Original training notebooks create train/test windows separately after splitting rows, so that particular train/test target-overlap mechanism is **not** demonstrated in those notebooks.
- Their `validation_split=0.1` acts on overlapping training windows. Targets across the fitting/validation boundary share H-1 timestamps; scalers were also fitted before reserving validation, so they include validation-region extrema. Validation is not strictly held out. This is validation contamination, not proof of test leakage.
- Original `model.fit` calls omit `shuffle=False`; the default array-training behavior shuffles fitting windows. The new pipeline explicitly disables shuffling.
- Tyre `shift(24)` means a 72-hour lag, not the named 24-hour lag; `rolling(72)` means 72 observations at three-hour cadence (nine days by sample-count convention), not the named three days. These trailing features are causal despite inaccurate names.
- Testing-pipeline notebooks generate hourly dummy tyre inputs despite models trained on three-hour cadence and assign eight output timestamps spaced one hour apart while labeling them 24-hour predictions. Engine dummy generation makes only 168 rows and feature warm-up drops 71, leaving too few for a full 168-input history. These demonstration plots do not provide held-out forecast MAE.
- Some legacy plotting routines flatten overlapping multi-step forecasts as if contiguous or align predictions to timestamps before their input windows end. Plot labels cannot validate the reported forecast horizon or accuracy.
- Engine's older notebook compiles classification metrics alongside regression MAE. Accuracy, precision and recall from that setup are not valid evidence of continuous sensor-forecast quality.

## Saved-model decision for the new benchmark

All three designated models have correct true-time input/output lengths and reconstructable preprocessing. None requires retraining solely for a horizon shape mismatch. They are evaluated above as legacy artifacts. Retraining all three for the main benchmark standardizes training exposure, removes validation contamination, gives equal historical-target inputs to Random Forest and Bi-LSTM, and prevents mixing the old 10%-trained tyre models with the 80%-trained engine model. The architecture remains the original 128/64/32 LSTM family, while its input feature count changes from 11 to 1 explicitly.

## Provenance and claims

All three local generation notebooks reproduce the benchmark CSV timestamps and target values to floating-point precision (maximum absolute difference below 1.5e-14), as verified by `verify_generators.py` and recorded in `results/generator_verification.json`. The tyre-temperature generator is `Tyre Temperature/generating_data.ipynb`. All three datasets are therefore demonstrably synthetic; do not describe them as sensor-collected or operational fleet data.

The paper DOCX contains 0.1795 degrees Celsius, 0.2368 MPa, 0.344 degrees Celsius and an estimated 10-15% downtime reduction claim. This audit supplies no measured downtime reduction or failure/RUL validation. Rewrite those accuracy claims around the new aligned experiment; remove unsupported downtime, direct failure prediction, and operational aviation validation claims. Describe Salesforce as a maintenance/service workflow layer unless separate ERP evidence establishes otherwise. Keep prototype integration evidence separate from forecast accuracy.
