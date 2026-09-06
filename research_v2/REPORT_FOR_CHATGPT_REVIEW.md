## REPORT FOR CHATGPT REVIEW

The experiment and legacy-metric audit are complete. This is a single-seed, fixed-budget benchmark of **24-hour multi-step sensor forecasting for threshold-based predictive maintenance** on three demonstrably synthetic datasets. It does not establish direct failure prediction, remaining useful life or operational downtime benefits. The paper has not been rewritten.

### Final aggregate metrics

MAE and RMSE use the listed physical unit; R2 is dimensionless. All metrics flatten the same forecast-origin/horizon pairs for each dataset.

| Dataset | Model | MAE | RMSE | R2 | Unit |
| --- | --- | --- | --- | --- | --- |
| engine_temperature | Persistence | 10.156758 | 12.474404 | -0.799333 | °C |
| engine_temperature | Seasonal naive (previous 24 h) | 2.623008 | 3.448518 | 0.862489 | °C |
| engine_temperature | Random Forest | 1.708059 | 2.262048 | 0.940834 | °C |
| engine_temperature | Bi-LSTM | 6.199389 | 7.355912 | 0.374330 | °C |
| tyre_pressure | Persistence | 0.558283 | 0.979149 | 0.804345 | PSI |
| tyre_pressure | Seasonal naive (previous 24 h) | 0.780869 | 1.241001 | 0.685705 | PSI |
| tyre_pressure | Random Forest | 0.735564 | 1.003171 | 0.794627 | PSI |
| tyre_pressure | Bi-LSTM | 1.177751 | 1.443047 | 0.575034 | PSI |
| tyre_temperature | Persistence | 5.785863 | 7.105415 | -0.839973 | °C |
| tyre_temperature | Seasonal naive (previous 24 h) | 3.897419 | 4.963815 | 0.102026 | °C |
| tyre_temperature | Random Forest | 2.896952 | 3.679638 | 0.506550 | °C |
| tyre_temperature | Bi-LSTM | 6.453655 | 7.862411 | -1.252911 | °C |

### Comparison against the best baseline

| Dataset | Best baseline by MAE | Baseline MAE | Bi-LSTM MAE | MAE improvement (%) |
| --- | --- | --- | --- | --- |
| engine_temperature | Random Forest | 1.708059 | 6.199389 | -262.949408 |
| tyre_pressure | Persistence | 0.558283 | 1.177751 | -110.959644 |
| tyre_temperature | Random Forest | 2.896952 | 6.453655 | -122.773976 |

Positive improvement means lower Bi-LSTM MAE; negative means degradation. Formula: 100 * (best baseline MAE - Bi-LSTM MAE) / best baseline MAE. Bi-LSTM beats the best baseline by MAE on **0 of 3** targets in this run. Report every target and metric, including failures to outperform. This establishes a result for the recorded configuration only; it cannot establish that the architecture can never perform better. No significance or general superiority claim is supported by one seed and one chronological test period.

### Timing and split boundaries

| Dataset | Rows | Sampling interval (h) | Lookback steps | Horizon steps | Train windows | Validation windows | Test windows |
| --- | --- | --- | --- | --- | --- | --- | --- |
| engine_temperature | 8761 | 1.000000 | 168 | 24 | 5765 | 1029 | 1730 |
| tyre_pressure | 2921 | 3.000000 | 56 | 8 | 1922 | 344 | 578 |
| tyre_temperature | 2921 | 3.000000 | 56 | 8 | 1922 | 344 | 578 |

| Dataset | Train first target | Train last target | Validation first target | Validation last target | Test first target | Test last target |
| --- | --- | --- | --- | --- | --- | --- |
| engine_temperature | 2024-01-08 00:00:00 | 2024-09-05 03:00:00 | 2024-09-05 04:00:00 | 2024-10-18 23:00:00 | 2024-10-19 00:00:00 | 2024-12-31 00:00:00 |
| tyre_pressure | 2024-01-08 00:00:00 | 2024-09-05 00:00:00 | 2024-09-05 03:00:00 | 2024-10-18 21:00:00 | 2024-10-19 00:00:00 | 2024-12-31 00:00:00 |
| tyre_temperature | 2024-01-08 00:00:00 | 2024-09-05 00:00:00 | 2024-09-05 03:00:00 | 2024-10-18 21:00:00 | 2024-10-19 00:00:00 | 2024-12-31 00:00:00 |

Split raw rows first: test starts at floor(0.8*N); validation starts at floor(0.85*floor(0.8*N)). Both learned models fit only the first approximately 68% of rows. Validation is approximately 12%, and final test is 20%. Only windows whose complete targets lie within their partition are retained. The first test forecast can use earlier training/validation observations as history. Later forecast origins can use newly observed test history, without retraining. Overlapping errors inside a test partition are dependent; the number of windows is not an independent sample count.

The former baseline split overlapping windows and exposed H-1 test target timestamps to Random Forest fitting (23 engine, 7 tyre). It also used a different test boundary. Its old numbers are superseded, not mixed with these results. No test labels enter fitting or scaling in the corrected pipeline. Metadata and prediction checks confirm alignment across all four models.

### Architecture, selection and environment

All new Bi-LSTMs use historical target values only (one feature), identical information to the autoregressive Random Forest. The original 11-feature notebook setup is not replicated as the main benchmark. Architecture: bidirectional LSTM(128, return_sequences), batch normalization, dropout(.2), bidirectional LSTM(64, return_sequences), batch normalization, dropout(.3), LSTM(32), Dense(64, relu), dropout(.2), Dense(horizon). This retains the original layer sizes and family. Bidirectionality is confined to observed history.

Adam with MSE loss and MAE training metric; no classification metrics. MinMaxScaler fits only the fitting region. Seed 42, no shuffle, deterministic TensorFlow operations, oneDNN disabled. Early stopping monitors validation loss with patience 5 and restores best weights. A fixed 20-epoch maximum and batch size 64 were chosen before the test evaluation; no test-driven tuning or reduced LSTM units were used. Random Forest: 300 trees, depth 16, minimum leaf 2, seed 42.

| Dataset | Epochs run | Best epoch | Training seconds |
| --- | --- | --- | --- |
| engine_temperature | 11.000000 | 6.000000 | 1213.125000 |
| tyre_pressure | 20.000000 | 20.000000 | 339.078000 |
| tyre_temperature | 9.000000 | 4.000000 | 177.000000 |

Best validation performance occurred at the epoch cap for: tyre_pressure. Convergence is not established for these models; additional training might improve performance. No further tuning was performed after observing test scores.

```json
{
  "Python": "3.11.9",
  "TensorFlow": "2.18.0",
  "NumPy": "2.0.2",
  "pandas": "2.2.2",
  "scikit-learn": "1.9.0",
  "Platform": "Windows-10-10.0.26200-SP0",
  "Devices": [
    "PhysicalDevice(name='/physical_device:CPU:0', device_type='CPU')"
  ],
  "Arguments": {
    "epochs": 20,
    "batch_size": 64,
    "threads": 4
  }
}
```

Pinned direct requirements and the complete `results/environment_freeze.txt` record include Keras 3.15.1 and h5py 3.16.0. No packages were installed or changed. Legacy scaler loading warned about scikit-learn 1.6.1 versus current 1.9.0; all three scaler transformations were independently reconstructed and matched. TensorFlow emitted an ignored unknown dataset-op attribute warning; the run completed and persisted predictions were verified. Cross-platform bitwise identity is not claimed.

### Saved models and old paper claims

All three designated saved models are shape-compatible: engine `(168,11)->24`, tyres `(56,11)->8`. All saved scaler feature names and transformations match reconstructed notebook preprocessing. Fresh inference reproduced the stored notebook MAEs. They are **legacy audit results on different test periods**, not entries in the common comparison:

| Legacy target | Normalized MAE reproduced | Physical MAE | Explanation |
| --- | --- | --- | --- |
| Karachi engine | 0.03223978 | 1.73429680 degrees Celsius | Original 80% training, 11 features, 1,546 test windows |
| Generated tyre pressure | 0.23684705 | 1.83820315 PSI | Original 10% training, 11 features, 2,501 test windows |
| Tyre temperature | 0.34135299 | 6.98365678 degrees Celsius | Original 10% training, 11 features, 2,501 test windows |

Retraining was chosen to standardize fitting exposure and features, eliminate validation contamination, and provide an aligned benchmark. The designated tyre models did **not** mistakenly output 24 samples: they already output 8. Their lag names were incorrect: shift(24) is 72 hours, and rolling(72) is nine days of observations at three-hour cadence.

The paper's engine **0.1795 degrees Celsius** matches the stored normalized MAE 0.1794579178094864 in the older `Engine Temperature/Training_LSTM.ipynb`, which reads a UAE dataset rather than Karachi. Scaling had not been inverted for that evaluation. Multiplying by the reconstructed target range 99.54479405 gives about 17.86410147 degrees Celsius conditional on that exact local data/output pairing; fresh evaluation of the old UAE weights after an explicit in-memory Keras compatibility migration also reproduces normalized MAE 0.1794579465 and physical MAE 17.86410433 degrees Celsius (RMSE 22.24166435, R2 -0.78475507, 1,122 windows). The migration removes obsolete batch-major configuration, converts singleton batch-normalization axes to scalars, and renames input shape keys; original model weights/files are unchanged. This confirms metric provenance, but is not a replacement benchmark. That notebook uses 40 input samples and 24 outputs on predominantly three-hour data: nominally 120 hours of input and 72 hours of output. The data also have a timestamp reset and internal duplicates. No train/test timestamp intersection was demonstrated for that split.

The paper's pressure **0.2368 MPa** is normalized MAE, neither PSI nor MPa. No MPa conversion was found in the matching evaluation path. The physical legacy error is approximately 1.8382 PSI. The paper's tyre-temperature **0.344 degrees Celsius** does not match the reproduced 0.3414 normalized result by ordinary rounding; its exact source remains unresolved.

Original notebook train/test windows were formed separately, so the baseline's train/test label-overlap mechanism is not established in those notebooks. However, `validation_split=0.1` on overlapping training windows shares H-1 labels across fitting/validation, and scalers were fitted before validation was reserved. This is demonstrated validation contamination, not an accusation of test leakage. The new pipeline removes both problems. The testing notebooks use synthetic dummy inputs and inconsistent tyre forecast timestamps; these plots are not a separate MAE validation experiment. Full cell references and details are in `AUDIT.md` and `results/notebook_evidence.json`.

### Provenance and defensible paper framing

All three local generators reproduce their CSVs to floating-point precision, including timestamps (maximum difference below 1.5e-14). The tyre generator is `Tyre Temperature/generating_data.ipynb`. All data are synthetic. Reproduction records are in `results/generator_verification.json`; dataset SHA256s are in experiment metadata.

Use the final table to state explicitly which models perform best on each target. Present the work as a prototype for multi-step sensor forecasting linked to threshold-based maintenance workflows. Separate IoT/dashboard/Salesforce integration evidence from forecasting accuracy. Describe Salesforce as a maintenance/service workflow layer unless there is separate evidence for an ERP component.

Remove or rewrite the three old physical-unit MAE claims, unsupported 10-15% downtime reduction, classification metrics used for regression, direct failure/RUL prediction, and assertions of operational aviation-fleet validation. Do not use synthetic dummy demonstrations as evidence of real operational generalization.

Limitations: synthetic generators and one seed; one chronological holdout; limited training budget; no hyperparameter search; no uncertainty intervals or statistically independent forecast errors; no real-fleet external validation; no measured maintenance outcomes. The exact source of the paper's 0.344 value remains unresolved. No remaining execution blocker exists.

### Horizon-wise metrics

| Dataset | Model | Horizon (h) | Unit | MAE | RMSE | R2 |
| --- | --- | --- | --- | --- | --- | --- |
| engine_temperature | Bi-LSTM | 1.000000 | °C | 4.052678 | 5.056518 | 0.703638 |
| engine_temperature | Bi-LSTM | 2.000000 | °C | 4.882379 | 5.862761 | 0.602587 |
| engine_temperature | Bi-LSTM | 3.000000 | °C | 4.967528 | 5.877851 | 0.601311 |
| engine_temperature | Bi-LSTM | 4.000000 | °C | 4.318208 | 5.246349 | 0.682871 |
| engine_temperature | Bi-LSTM | 5.000000 | °C | 5.203736 | 6.168944 | 0.562292 |
| engine_temperature | Bi-LSTM | 6.000000 | °C | 5.923099 | 6.923004 | 0.449167 |
| engine_temperature | Bi-LSTM | 7.000000 | °C | 5.697576 | 6.749195 | 0.476988 |
| engine_temperature | Bi-LSTM | 8.000000 | °C | 6.842155 | 7.800212 | 0.301605 |
| engine_temperature | Bi-LSTM | 9.000000 | °C | 6.852280 | 8.007234 | 0.264115 |
| engine_temperature | Bi-LSTM | 10.000000 | °C | 7.690452 | 8.595982 | 0.151662 |
| engine_temperature | Bi-LSTM | 11.000000 | °C | 7.346246 | 8.427056 | 0.184189 |
| engine_temperature | Bi-LSTM | 12.000000 | °C | 7.662681 | 8.731857 | 0.122954 |
| engine_temperature | Bi-LSTM | 13.000000 | °C | 8.299639 | 9.281784 | 0.007218 |
| engine_temperature | Bi-LSTM | 14.000000 | °C | 8.353456 | 9.456865 | -0.032737 |
| engine_temperature | Bi-LSTM | 15.000000 | °C | 8.405643 | 9.564363 | -0.058518 |
| engine_temperature | Bi-LSTM | 16.000000 | °C | 7.425792 | 8.540827 | 0.154149 |
| engine_temperature | Bi-LSTM | 17.000000 | °C | 6.521268 | 7.489455 | 0.348380 |
| engine_temperature | Bi-LSTM | 18.000000 | °C | 6.970641 | 7.950914 | 0.264367 |
| engine_temperature | Bi-LSTM | 19.000000 | °C | 6.538483 | 7.580408 | 0.330221 |
| engine_temperature | Bi-LSTM | 20.000000 | °C | 5.973697 | 7.027887 | 0.423705 |
| engine_temperature | Bi-LSTM | 21.000000 | °C | 5.486924 | 6.544470 | 0.500349 |
| engine_temperature | Bi-LSTM | 22.000000 | °C | 4.364179 | 5.300173 | 0.672387 |
| engine_temperature | Bi-LSTM | 23.000000 | °C | 4.583617 | 5.592333 | 0.635782 |
| engine_temperature | Bi-LSTM | 24.000000 | °C | 4.422980 | 5.531864 | 0.644337 |
| tyre_pressure | Bi-LSTM | 3.000000 | PSI | 0.959175 | 1.201516 | 0.707527 |
| tyre_pressure | Bi-LSTM | 6.000000 | PSI | 1.129784 | 1.397760 | 0.603305 |
| tyre_pressure | Bi-LSTM | 9.000000 | PSI | 1.077377 | 1.329198 | 0.640715 |
| tyre_pressure | Bi-LSTM | 12.000000 | PSI | 1.155853 | 1.408666 | 0.595747 |
| tyre_pressure | Bi-LSTM | 15.000000 | PSI | 1.177564 | 1.428590 | 0.583218 |
| tyre_pressure | Bi-LSTM | 18.000000 | PSI | 1.272340 | 1.543987 | 0.512095 |
| tyre_pressure | Bi-LSTM | 21.000000 | PSI | 1.263542 | 1.522603 | 0.524170 |
| tyre_pressure | Bi-LSTM | 24.000000 | PSI | 1.386374 | 1.663580 | 0.430364 |
| tyre_temperature | Bi-LSTM | 3.000000 | °C | 7.217599 | 8.541203 | -1.665020 |
| tyre_temperature | Bi-LSTM | 6.000000 | °C | 7.220416 | 8.631778 | -1.716028 |
| tyre_temperature | Bi-LSTM | 9.000000 | °C | 5.337181 | 6.606467 | -0.592151 |
| tyre_temperature | Bi-LSTM | 12.000000 | °C | 4.977498 | 6.160333 | -0.384095 |
| tyre_temperature | Bi-LSTM | 15.000000 | °C | 7.749257 | 9.136789 | -2.046478 |
| tyre_temperature | Bi-LSTM | 18.000000 | °C | 8.632871 | 9.980747 | -2.640644 |
| tyre_temperature | Bi-LSTM | 21.000000 | °C | 5.885695 | 7.137126 | -0.857257 |
| tyre_temperature | Bi-LSTM | 24.000000 | °C | 4.608726 | 5.608065 | -0.136135 |

### Files, commands and verification

Created: `bilstm_evaluation.py`, `protocol.py`, `audit_originals.py`, `audit_uae_legacy.py`, `verify_generators.py`, `test_protocol.py`, `verify_results.py`, `build_report.py`, `requirements.txt`, `AUDIT.md`, `.gitignore` under `research_v2/`, this report, and generated `results/` artifacts. Modified: `research_v2/baseline_evaluation.py` and `research_v2/README.md`. The pre-existing untracked root `.gitignore` was left untouched. Original notebooks, models and the paper are unchanged.

Exact execution commands from the repository root (PowerShell):

```powershell
.venv/Scripts/python.exe -u research_v2/bilstm_evaluation.py > research_v2/training_run.log 2>&1
.venv/Scripts/python.exe -u research_v2/audit_originals.py > research_v2/audit_run.log 2>&1
.venv/Scripts/python.exe -u research_v2/audit_originals.py
.venv/Scripts/python.exe research_v2/verify_generators.py
.venv/Scripts/python.exe research_v2/audit_uae_legacy.py
.venv/Scripts/python.exe -m unittest discover -s research_v2 -p test_protocol.py -v
.venv/Scripts/python.exe -m pip freeze > research_v2/results/environment_freeze.txt
.venv/Scripts/python.exe research_v2/verify_results.py
.venv/Scripts/python.exe research_v2/build_report.py
git diff --check
```

Four protocol tests passed: actual-data cadence/horizon and disjoint-label checks, invalid-series rejection, physical-unit inverse-transform checks, and reproduction of the old baseline overlap mechanism. Post-run verification recomputed all aggregate and horizon metrics from persisted forecasts, checked true targets against source data, verified common split/hash metadata, and reloaded all three saved models to reproduce example forecasts within floating-point tolerance. Verification results are stored in `results/verification.json`.


