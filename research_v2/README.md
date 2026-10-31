# Research V2: multi-step sensor forecasting benchmark

Re-evaluation of the AutoSense forecasting models, carried out in 2026 after the final-year project. It asks whether a Bi-LSTM forecasts sensor readings 24 hours ahead better than simple baselines when every model uses the same data, partitions and information.

It evaluates **sensor forecasting for threshold-based maintenance only**. It does not evaluate failure prediction, remaining useful life, downtime reduction or a real-fleet deployment.

## Manuscript

**M. Rizvi, W. Raza, H. Naseer, F. Niaz**, *Benchmarking Multi-Step Sensor Forecasting for Threshold-Based Predictive Maintenance: An Integrated IoT-to-Enterprise Framework*, preprint, Zenodo, 2026, [doi:10.5281/zenodo.22665260](https://doi.org/10.5281/zenodo.22665260).

- PDF (11 pages): [`paper/build/main.pdf`](paper/build/main.pdf)
- LaTeX source: [`paper/main.tex`](paper/main.tex), with [`references.bib`](paper/references.bib), [`tables/`](paper/tables/) and [`figures/`](paper/figures/)

## Main findings

**Corrected benchmark, seed 42, synthetic data** ([`results/final_comparison.csv`](results/final_comparison.csv)). Test-set MAE in physical units:

| Target | Persistence | Seasonal naive | Random Forest | Bi-LSTM |
|---|---:|---:|---:|---:|
| Engine temperature (°C) | 10.157 | 2.623 | **1.708** | 6.199 |
| Tyre pressure (PSI) | **0.558** | 0.781 | 0.736 | 1.178 |
| Tyre temperature (°C) | 5.786 | 3.897 | **2.897** | 6.454 |

- **The Bi-LSTM beats the best baseline on none of the three targets.** Random Forest has the lowest MAE for both temperatures and persistence for tyre pressure.
- **Five Bi-LSTM seeds** (11, 21, 42, 84, 168): MAE 5.182 ± 0.665 °C (engine), 1.256 ± 0.221 PSI (pressure), 5.731 ± 0.889 °C (tyre temperature). These numbers show seed-to-seed variation. They are not repeated-split validation.
- **Architecture ablation** (seed 42, LSTM / Bi-LSTM MAE): 9.539 / 6.199 °C, 1.298 / 1.182 PSI, 4.402 / 6.366 °C. Neither architecture is better on every target.
- **Feature ablation**: causal lag and rolling features (F2) lower LSTM engine MAE from 9.539 to 5.142 °C, but raise Random Forest tyre-pressure MAE from 0.736 to 0.836 PSI. The effect depends on the target and model.
- **Proxy threshold events** (thresholds from training data, not fault labels): the Bi-LSTM scores F1 = 0 on engine temperature and tyre pressure. On tyre temperature it scores F1 0.802, but its false-positive rate is 1.0 and its specificity 0, so it does not tell events from non-events.
- **Moving-block bootstrap** (2,000 replications), MAE(best baseline) − MAE(Bi-LSTM): [−5.033, −3.955] °C, [−0.845, −0.356] PSI, [−3.732, −3.392] °C. All three intervals exclude zero in favour of the baseline. They account for dependence between windows, but they are not i.i.d. significance tests.
- **NASA C-MAPSS FD001** (simulated turbofan data, engine-disjoint 70/15/15 split, 30-cycle history, 10-cycle horizon). Normalized macro MAE for the multivariate configuration C1: Random Forest 0.03406, LSTM 0.03460, Bi-LSTM 0.03483 (R² 0.889 / 0.886 / 0.885). On this benchmark the three models perform almost the same.

Detailed reports:

- [`REPORT_FOR_CHATGPT_REVIEW.md`](REPORT_FOR_CHATGPT_REVIEW.md): corrected-benchmark report (all metrics, splits, timing, environment). `build_report.py` writes it under this fixed name.
- [`IEEE_UPGRADE_REPORT.md`](IEEE_UPGRADE_REPORT.md): extended experiments, recorded software environments and acceptance checks.
- [`AUDIT.md`](AUDIT.md): audit of the metrics reported originally. For example, the original "0.1795 °C" engine MAE was a normalized value that corresponds to about 17.86 °C.

## Methodology

- **Data.** Three synthetic 2024 series: engine temperature (hourly), tyre pressure and tyre temperature (both 3-hourly). The generator notebooks reproduce them to floating-point precision ([`verify_generators.py`](verify_generators.py)). None is recorded fleet data.
- **Protocol** ([`protocol.py`](protocol.py)). Raw rows are split chronologically: about 68% train, 12% validation and 20% test. A window belongs to a partition only when its whole target horizon lies inside it. Each model sees seven days of history and forecasts a 24-hour horizon (168→24 hourly steps, 56→8 three-hourly steps).
- **Training.** Inputs are target history only. MinMax scaling is fitted on training rows. There is no shuffling, and early stopping uses validation loss. Nothing is tuned on test scores. Every model receives identical windows and masks.
- **Extended experiments.** These are defined in [`CODEX_IEEE_EXECUTION_PLAN.md`](CODEX_IEEE_EXECUTION_PLAN.md) before they were run. That file is the pre-registration document; its SHA256 is recorded in the C-MAPSS results, so it must not be edited. The scripts are in [`ieee_experiments/`](ieee_experiments/). Kaggle inputs and raw outputs are in [`kaggle/`](kaggle/).

## Limitations

- All AutoSense data are synthetic. There is no validation on real fleet data, no failure or RUL target, no certified alert performance and no measured downtime reduction.
- C-MAPSS is simulator output, not physical flight telemetry. It is used for sensor forecasting only, not RUL estimation.
- Test windows overlap, so their errors are dependent. The main benchmark uses one chronological test period. On AutoSense data, only the Bi-LSTM is run with several seeds.
- The C-MAPSS and feature-ablation runs used TensorFlow 2.20.0 and scikit-learn 1.6.1, while the other runs used 2.18.0 and 1.9.0. Bit-for-bit reproduction across hardware or library versions is not guaranteed.
- The benchmark models are retrained univariate models. They are not the 11-feature models deployed in the prototype ([`../Models and scripts/`](../Models%20and%20scripts/)).

## Folder layout

| Path | Contents |
|---|---|
| `protocol.py`, `baseline_evaluation.py`, `bilstm_evaluation.py` | Shared protocol, baselines, Bi-LSTM training |
| `test_protocol.py`, `verify_generators.py`, `verify_results.py` | Protocol tests, data-generator check, check of saved results |
| `audit_originals.py`, `audit_uae_legacy.py` | Reproduce the originally reported metrics |
| `build_report.py`, `validate_final_result_archives.py` | Benchmark report builder, Kaggle-archive validator |
| [`results/`](results/) | Corrected benchmark: metrics, saved models, scalers, predictions, environment, audit evidence |
| [`ieee_experiments/`](ieee_experiments/) | Multi-seed, ablation, threshold-event, bootstrap and C-MAPSS scripts and Kaggle notebooks |
| [`ieee_results/`](ieee_results/) | Outputs of the extended experiments, C-MAPSS split and sensor selection, provenance and validation ledgers |
| [`kaggle/`](kaggle/) | Kaggle input bundles, raw result archives and run guide |
| [`figure_generation/`](figure_generation/) | Benchmark figures (`generate_all.py`) and baseline export |
| [`paper/`](paper/) | Manuscript source, figures, tables and compiled PDF |
| [`external_data/cmapss/`](external_data/cmapss/) | Where to place the NASA FD001 files (not committed) |

The experiment scripts, `protocol.py` and the C-MAPSS split and sensor-selection files have SHA256 hashes recorded in the result files. Editing them breaks that provenance link.

## Reproduction

Python 3.11. Install [`requirements.txt`](requirements.txt); the figure scripts also need [`figure_generation/requirements.txt`](figure_generation/requirements.txt). Run from the repository root.

Checks that use the saved results (no training):

```sh
python -m unittest discover -s research_v2 -p test_protocol.py -v   # protocol tests (4)
python research_v2/verify_generators.py        # regenerate the synthetic CSVs and compare
python research_v2/verify_results.py           # recompute metrics from saved predictions, reload models
python research_v2/audit_originals.py          # reproduce the original notebook metrics
python research_v2/audit_uae_legacy.py         # reproduce the legacy UAE engine metric
python research_v2/validate_final_result_archives.py --output <scratch>.json   # validate Kaggle archives
```

`verify_generators.py`, `verify_results.py` and the two audit scripts rewrite their JSON records in `results/`. Without `--output`, the validator overwrites `ieee_results/final_integration_validation.json`.

Full retraining (CPU, slow; overwrites `results/` and the report):

```sh
python research_v2/bilstm_evaluation.py        # baselines + Bi-LSTM; flags --epochs --batch-size --threads
python research_v2/build_report.py             # rebuild REPORT_FOR_CHATGPT_REVIEW.md
```

Extended experiments: the multi-seed, ablation and C-MAPSS runs were trained on Kaggle (see [`kaggle/README.md`](kaggle/README.md)). The C-MAPSS runs need the NASA files described in [`external_data/cmapss/README.md`](external_data/cmapss/README.md). These scripts run locally on CPU and overwrite their outputs in `ieee_results/` and `paper/`. The threshold-event script refits the fixed baselines; the others read saved results:

```sh
python research_v2/ieee_experiments/threshold_event_evaluation.py
python research_v2/ieee_experiments/bootstrap_comparison.py
python research_v2/ieee_experiments/generate_ieee_tables.py
python research_v2/ieee_experiments/generate_ieee_figures.py
python research_v2/figure_generation/generate_all.py
```

The manuscript was compiled with XeTeX (`paper/main.tex` → `paper/build/main.pdf`).
