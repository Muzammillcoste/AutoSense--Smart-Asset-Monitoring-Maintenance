# IEEE upgrade final integration and validation report

## Scope, evidence ledger, and decision rule

This report audits the six result/source archives committed at
`e318489c9189a058fa86d34841128b5b1b824598` on branch
`research-paper-v2`. No new training, test-driven tuning, split change, or
model-setting change was performed for this review.

The executable validation record is
`research_v2/validate_final_result_archives.py`; its machine-readable output is
`research_v2/ieee_results/final_integration_validation.json`. It checks archive
contents and SHA256 values; expected row counts and unique keys; source, data,
protocol, sensor-selection, and split hashes; AutoSense seeds and horizons;
C-MAPSS split disjointness; each C-MAPSS prediction NPZ's engine IDs; and the
versions recorded by the results themselves. It is a no-training check.

Final-evidence packages are required to record the pinned environment:

| Dependency | Required version |
|---|---:|
| TensorFlow | 2.18.0 |
| scikit-learn | 1.9.0 |
| NumPy | 2.0.2 |
| pandas | 2.2.2 |

The existing per-row protocols record TensorFlow and scikit-learn in every
phase; the five-seed AutoSense results also record NumPy and pandas. The
architecture, C-MAPSS, and feature schemas pre-date per-row NumPy/pandas
fields, so no unrecorded version is inferred. The C-MAPSS and feature results
are rejected independently on their explicitly recorded TensorFlow and
scikit-learn mismatches.

| Archive / phase | Structural validation | Recorded TensorFlow / scikit-learn | Final status |
|---|---|---|---|
| `autosense_multiseed_results.zip` | 15 detailed + 3 summary rows; 5 fixed seeds | 2.18.0 / 1.9.0 | **accepted** |
| `architecture_ablation_results.zip` | 6 unique dataset/model/seed rows | 2.18.0 / 1.9.0 | **accepted** |
| `cmapss_fd001_forecasting_results.zip` | 55 metrics, 550 horizon rows, 44 NPZs; no engine leakage | 2.20.0 / 1.6.1 | **rejected** |
| `cmapss_stage_analysis_results.zip` | 132 unique stage rows, matching forecast/data hashes | 2.18.0 / 1.9.0 | **rejected dependency** |
| `feature_ablation_results.zip` | 18 unique configuration/model/seed rows | 2.20.0 / 1.6.1 | **rejected** |
| `paper_overleaf.zip` | expected TeX/source files | n/a | source is identical to committed `paper/` |

The full SHA256 values of the six archives are preserved in
`final_integration_validation.json`. The rejected ZIPs remain committed as
audit artifacts and have **not** been copied into `ieee_results` as accepted
evidence. Existing accepted artifacts are not overwritten.

## Accepted AutoSense five-seed robustness results

All 15 predeclared Bi-LSTM runs are present: each synthetic AutoSense dataset
uses seeds 11, 21, 42, 84, and 168 with the committed chronological split,
train-only scaling, 168-hour lookback, and 24-hour horizon. Values are mean ±
sample standard deviation across seeds.

| Dataset | MAE | RMSE | R² |
|---|---:|---:|---:|
| Engine temperature | 5.182 ± 0.665 °C | 6.343 ± 0.655 °C | 0.531 ± 0.099 |
| Tyre pressure | 1.256 ± 0.221 PSI | 1.532 ± 0.260 PSI | 0.510 ± 0.164 |
| Tyre temperature | 5.731 ± 0.889 °C | 7.030 ± 1.082 °C | −0.835 ± 0.536 |

These are seed-variation estimates, not a repeated-split or hyperparameter
selection exercise. In particular, the negative mean tyre-temperature R² does
not support a blanket Bi-LSTM-superiority claim.

## Accepted seed-42 architecture ablation

The ablation uses the same source/data hashes, chronological origins,
train-only scaler policy, 20-epoch cap, batch size 64, patience 5, and no
shuffle for LSTM and Bi-LSTM. It is a first-pass seed-42 comparison, not a
multi-seed architecture ranking.

| Dataset | LSTM MAE / RMSE / R² | Bi-LSTM MAE / RMSE / R² |
|---|---:|---:|
| Engine temperature | 9.539 °C / 11.776 °C / −0.604 | 6.199 °C / 7.356 °C / 0.374 |
| Tyre pressure | 1.298 PSI / 1.556 PSI / 0.506 | 1.182 PSI / 1.439 PSI / 0.577 |
| Tyre temperature | 4.402 °C / 5.325 °C / −0.034 | 6.366 °C / 7.758 °C / −1.194 |

Thus, under this fixed first pass, Bi-LSTM is lower-error for engine
temperature and tyre pressure, while LSTM is lower-error for tyre temperature.
No test result was used to select an architecture.

## Accepted proxy threshold-event evaluation

Thresholds are derived from the training region and label forecast excursions
outside those proxy bounds. They are not component-failure labels, certified
engineering thresholds, or maintenance-effectiveness measurements.

- Engine temperature (event prevalence 0.106): seasonal naive F1 = 0.372;
  Random Forest and Bi-LSTM F1 = 0 under this proxy rule.
- Tyre pressure (0.479): seasonal naive F1 = 0.893; persistence F1 = 0.879;
  Bi-LSTM F1 = 0.
- Tyre temperature (0.670): Bi-LSTM F1 = 0.802, but false-positive rate = 1.0
  and specificity = 0.0, so it is not a useful discriminative detector.

All confusion/metric details are retained in
`ieee_results/threshold_event_confusions.csv` and
`ieee_results/threshold_event_metrics.csv`.

## Accepted moving-block bootstrap comparison

The predeclared analysis used 2,000 seed-42 non-circular moving-block
replications: 48 forecast origins for engine temperature and 16 for each tyre
series (each represents 48 clock hours). A negative MAE(A) − MAE(B) favors A.

| Dataset | Comparison | Observed MAE difference | 95% interval |
|---|---|---:|---:|
| Engine temperature | Random Forest − Bi-LSTM | −4.491 °C | [−5.033, −3.955] |
| Tyre pressure | Persistence − Bi-LSTM | −0.619 PSI | [−0.845, −0.356] |
| Tyre temperature | Random Forest − Bi-LSTM | −3.557 °C | [−3.732, −3.392] |

All three intervals exclude zero. They are dependence-aware uncertainty
intervals, not i.i.d. hypothesis-test or deployment-benefit claims.

## Rejected C-MAPSS FD001 forecast and stage results

The rejected forecast archive is structurally sound but not admissible final
evidence. It has the pre-registered 70/15/15 disjoint engine split, selected
training-only sensors `sensor_9`, `sensor_11`, `sensor_14`, and `sensor_12`, a
30-cycle lookback, 10-cycle horizon, and exactly 44 prediction artifacts.
Every NPZ contains only a test-set engine ID. Its data, script, protocol,
split, and sensor-selection hashes match the committed inputs. No external
validation result is nevertheless claimed, because every forecast/horizon row
and the forecast manifest record TensorFlow 2.20.0 and scikit-learn 1.6.1.

The stage archive has 132 rows (44 forecast artifacts × the fixed early,
mid, and late normalized-life bins) and its prediction-data and forecast-script
hashes match the rejected forecast archive. Although the stage run itself
records TensorFlow 2.18.0/scikit-learn 1.9.0, it is derived from a rejected
forecast artifact, so it is also rejected. C-MAPSS is a simulator-generated
turbofan degradation dataset, not commercial-flight telemetry; this work is
sensor forecasting and does not claim RUL prediction.

## Rejected feature ablation

The feature archive has the expected 18 rows: three AutoSense datasets × F0,
F1, F2 × Random Forest/LSTM, with seed 42 and the recorded causal feature
policy. It is excluded from final feature-effect claims because its rows and
manifest record TensorFlow 2.20.0/scikit-learn 1.6.1 rather than the pinned
environment. Its values are retained only inside the audit ZIP.

## Manuscript/source comparison and remaining limitations

`paper_overleaf.zip` contains the expected source/figure/table payload, but
the checked `main.tex`, `references.bib`, `tables/dataset_protocol.tex`, and
`tables/main_comparison.tex` SHA256 values exactly match the already committed
`research_v2/paper/` files. It therefore provides no newer manuscript source
to integrate. The manuscript is intentionally not updated with rejected
C-MAPSS, stage, or feature values.

The remaining limitations are material: all AutoSense series are synthetic;
there is no real commercial-fleet validation; the C-MAPSS simulator is not
flight telemetry; there are no AutoSense failure/RUL labels; proxy threshold
metrics are not certified alarm performance; and no maintenance downtime
reduction is measured. The accepted architecture comparison has only one seed.

## Required reruns before final manuscript integration

1. Run `research_v2/ieee_experiments/kaggle_cmapss_fd001_forecasting.ipynb`
   from its package-install/version-gate cell through the final ZIP. Its output
   must record TensorFlow 2.18.0 and scikit-learn 1.9.0 in every metrics and
   horizon row and its run manifest.
2. Only after that forecast ZIP passes validation, run
   `research_v2/ieee_experiments/kaggle_cmapss_stage_analysis.ipynb` against
   that new forecast ZIP. Its 132 rows must reference the newly accepted
   forecasting artifact hashes.
3. Independently run
   `research_v2/ieee_experiments/kaggle_feature_ablation.ipynb` from its
   version-gate cell. Its 18 rows and manifest must record TensorFlow 2.18.0
   and scikit-learn 1.9.0.

No rerun may alter seeds, splits, architectures, lookback/horizon, scaler
policy, epoch cap, batch size, early stopping, selected sensors, bootstrap, or
threshold rules. On receipt, replace only the corresponding ZIPs and rerun the
no-training validator before importing accepted outputs and regenerating
paper tables/figures.

**Ready for arXiv:** No — the required C-MAPSS, stage, and feature evidence is
not environment-compliant, and the manuscript cannot truthfully include it.

**Ready for IEEE submission:** No — the arXiv blocker remains, along with the
need to integrate compliant external-validation and feature-ablation evidence
and then rebuild the IEEE manuscript.

## REPORT FOR CHATGPT IEEE REVIEW
