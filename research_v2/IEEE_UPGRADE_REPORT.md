# IEEE upgrade: results-integrity review

## Scope and commit identity

- Starting commit: `4b0d64e0c6bd06f19f4c7131a8baac9fc44076fa`.
- Branch: `research-paper-v2`.
- Final source/infrastructure commit assessed: `b9a5fe9 Fix C-MAPSS stage provenance hash`.
- Preserved corrected benchmark: `test_protocol.py` passed four tests and
  `verify_results.py` verified split alignment, persisted predictions,
  aggregate/horizon metrics, and model reloads for all three targets.

## Environment and import audit

All downloaded Kaggle ZIPs were checked for expected files, row counts, unique
keys, source/data hashes, split metadata, and C-MAPSS prediction-engine IDs.

| Run | Python | TensorFlow | scikit-learn | Devices | Status |
|---|---:|---:|---:|---|---|
| Five-seed AutoSense Bi-LSTM | 3.12.13 | 2.18.0 | 1.9.0 | CPU + 2 GPUs | accepted earlier |
| Architecture ablation | 3.12.13 | 2.18.0 | 1.9.0 | CPU + 2 GPUs | compliant |
| C-MAPSS forecasting | 3.12.13 | 2.20.0 | 1.6.1 | CPU + 2 GPUs | **not compliant** |
| C-MAPSS stage analysis | 3.12.13 | 2.18.0 | 1.9.0 | CPU + 1 GPU | derived from non-compliant forecast |
| Feature ablation | 3.12.13 | 2.20.0 | 1.6.1 | CPU + 1 GPU | **not compliant** |

The C-MAPSS and feature runs recorded TensorFlow 2.20.0 / scikit-learn 1.6.1,
not the specified TensorFlow 2.18.0 / scikit-learn 1.9.0. This is an
environment deviation, not test-driven tuning, but these outputs cannot serve
as final protocol-compliant evidence. Retain their ZIPs for audit and rerun
them under the pinned environment before publication claims.

## Files created or modified

- Accepted import: `ieee_results/architecture_ablation.csv` and its Kaggle
  manifest.
- Verified from the downloaded ZIPs but not integrated into final evidence
  pending rerun: `feature_ablation.csv`, C-MAPSS metrics/horizon/summary CSVs,
  44 C-MAPSS prediction NPZs, stage metrics, and their Kaggle manifests.
- Preparation added the four Kaggle notebooks, input bundles, phase READMEs,
  source/split/hash safeguards, and a stage-provenance fix.
- The original corrected artifacts in `research_v2/results/` were unchanged.

## AutoSense five-seed Bi-LSTM robustness

All 15 predeclared runs were present: three datasets times seeds `11`, `21`,
`42`, `84`, and `168`; hashes, split metadata, and summaries agreed.

| Dataset | MAE mean ± sd | RMSE mean ± sd | R² mean ± sd |
|---|---:|---:|---:|
| Engine temperature | 5.182 ± 0.665 °C | 6.343 ± 0.655 °C | 0.531 ± 0.099 |
| Tyre pressure | 1.256 ± 0.221 PSI | 1.532 ± 0.260 PSI | 0.510 ± 0.164 |
| Tyre temperature | 5.731 ± 0.889 °C | 7.030 ± 1.082 °C | -0.835 ± 0.536 |

This reports seed variation; no seed was selected as a winner.

## Architecture ablation (accepted)

The seed-42 first pass used identical train/validation/test origins,
train-only scaling, 20-epoch cap, batch size 64, no shuffle, and patience 5.
It is not a seed-robust architecture ranking.

| Dataset | LSTM MAE / R² | Bi-LSTM MAE / R² |
|---|---:|---:|
| Engine temperature | 9.539 °C / -0.604 | 6.199 °C / 0.374 |
| Tyre pressure | 1.298 PSI / 0.506 | 1.182 PSI / 0.577 |
| Tyre temperature | 4.402 °C / -0.034 | 6.366 °C / -1.194 |

## Feature ablation (audit-only; rerun required)

The archive has 18 unique rows (three datasets × F0/F1/F2 × Random
Forest/LSTM), causal F2 construction, and no discarded standard test origins.
It is excluded from final claims because of the recorded dependency versions.
Provisional results show F2 Random Forest engine-temperature MAE 1.673 °C;
this is not publication-ready until reproduced in the pinned environment.

## Threshold-event evaluation

These are training-derived proxy maintenance/anomaly thresholds, not safety
thresholds or component-failure labels.

- Engine-temperature prevalence 0.106: seasonal naive F1 0.372; Random Forest
  and Bi-LSTM F1 0 under this proxy rule.
- Tyre-pressure prevalence 0.479: seasonal naive F1 0.893, persistence F1
  0.879, and Bi-LSTM F1 0.
- Tyre-temperature prevalence 0.670: Bi-LSTM F1 0.802 but false-positive rate
  1.0 and specificity 0.0, so it is not a useful discriminative detector.

Complete values are retained in `threshold_event_metrics.csv` and
`threshold_event_confusions.csv`.

## Moving-block bootstrap

The completed analysis used 2,000 seed-42 non-circular moving-block
replications (48 forecast origins for engine temperature; 16 for tyre data;
each covers 48 clock hours). Negative MAE(A) − MAE(B) favors A.

| Dataset | Comparison | Observed difference | 95% interval |
|---|---|---:|---:|
| Engine temperature | Random Forest − Bi-LSTM | -4.491 | [-5.033, -3.955] |
| Tyre pressure | Persistence − Bi-LSTM | -0.619 | [-0.845, -0.356] |
| Tyre temperature | Random Forest − Bi-LSTM | -3.557 | [-3.732, -3.392] |

Every interval excludes zero. They are dependence-aware intervals, not i.i.d.
significance-test claims.

## NASA C-MAPSS FD001 provenance and split

- Official source: `https://data.nasa.gov/docs/legacy/CMAPSSData.zip`, accessed
  2026-09-06; archive SHA256
  `74bef434a34db25c7bf72e668ea4cd52afe5f2cfe44367c55a82bfd91a5a34f`.
- `train_FD001.txt` SHA256:
  `963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8`.
- Citation: A. Saxena and K. Goebel (2008), *Turbofan Engine Degradation
  Simulation Data Set*, NASA Prognostics Data Repository.
- C-MAPSS is simulator-generated, not measured commercial-flight telemetry;
  only complete `train_FD001.txt` trajectories forecast future sensors.

Seed-42 engine split:

- Train (70): `1,2,3,4,5,6,8,10,11,16,17,18,19,21,22,24,25,26,27,28,29,30,32,33,34,38,39,40,41,43,44,46,47,49,51,52,53,56,57,58,60,61,62,63,64,69,70,71,72,73,74,76,77,79,80,81,82,84,85,87,88,90,92,93,94,95,96,97,98,100`.
- Validation (15): `7,12,31,35,45,50,55,59,68,75,83,86,89,91,99`.
- Test (15): `9,13,14,15,20,23,36,37,42,48,54,65,66,67,78`.

Training-only selected sensors: `sensor_9` (0.825900), `sensor_11`
(0.813457), `sensor_14` (0.810603), and `sensor_12` (0.803065), where values
are median within-engine absolute Spearman correlations with cycle.

## C-MAPSS forecasting and stages (audit-only; rerun required)

The forecast archive is structurally valid: 55 metrics rows, 550 horizon rows,
eight Bi-LSTM summary rows, and 44 prediction artifacts. Every prediction used
a test engine with fixed C0/C1, 30-cycle history, and 10-cycle horizon. The
stage archive is structurally valid: 132 rows (44 artifacts × three fixed
early/mid/late bins), no duplicate keys, and matching prediction/data hashes.

Rerun forecasting and the dependent stage analysis under the pinned
environment before final interpretation. The current audit-only C1 Random
Forest macro normalized MAE/RMSE are 0.03406/0.04278; they are not final model
claims.

## API, paper, and build status

- API consistency and latency: not run; deferred until review.
- References added: none in this checkpoint.
- Paper sections updated: none; `main.tex` was intentionally not rewritten.
- LaTeX build/page count: not run.

## Strongest defensible conclusions

1. Five-seed AutoSense results do not support a blanket Bi-LSTM-superiority
   claim.
2. Seed-42 architecture performance is dataset-dependent: Bi-LSTM is better
   on engine temperature and tyre pressure, while LSTM is better on tyre
   temperature; multi-seed architecture confirmation remains necessary.
3. Planned moving-block intervals favor the corrected baseline over Bi-LSTM on
   every AutoSense target.
4. Proxy-event F1 must be read alongside specificity and false-positive rate.

## Results not supporting the original hypothesis

- Bi-LSTM has negative mean R² on tyre temperature across five seeds.
- The predeclared corrected baseline has lower MAE than Bi-LSTM on all three
  AutoSense targets in the moving-block comparison.
- Seed-42 LSTM beats seed-42 Bi-LSTM on tyre temperature.

## Remaining blockers

1. Rerun C-MAPSS forecasting, dependent stage analysis, and feature ablation
   under TensorFlow 2.18.0/scikit-learn 1.9.0.
2. Complete API consistency/latency after review.
3. Complete multi-seed architecture confirmation, paper rewrite, citations,
   figures, LaTeX build, and page-budget review.
4. Do not overgeneralize synthetic AutoSense data or simulated C-MAPSS data to
   a real fleet-deployment claim.

**Ready for arXiv:** No — required environment-compliant reruns, paper
revision, and LaTeX validation remain.

**Ready for IEEE submission:** No — the arXiv blockers remain, plus required
methodological integration and submission-format review.

## REPORT FOR CHATGPT IEEE REVIEW
