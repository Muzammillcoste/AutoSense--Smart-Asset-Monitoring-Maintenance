# Research Paper v2 — Reproducible Evaluation

This folder contains the experiment framework for the revised predictive-maintenance paper.

## Why this revision is necessary

The original notebooks mix sampling intervals and sometimes interpret a fixed number of samples as a fixed number of hours. For example, a 24-sample lag is 24 hours only for hourly data; it becomes 72 hours for 3-hour data and 120 hours for 5-hour data. The revised evaluation therefore derives the sampling interval from timestamps and defines all lookback/forecast windows in clock hours.

The original model notebooks also report classification-style metrics such as accuracy, precision, and recall for continuous-value regression. The revised paper should instead report MAE, RMSE, and R².

## Baselines

`baseline_evaluation.py` evaluates three reproducible baselines on the synthetic 2024 datasets used in the project:

- Persistence: repeat the latest observed value.
- Seasonal naive: use the previous day's same-time pattern.
- Random Forest: nonlinear autoregressive baseline trained only on past target values.

All datasets use an 80/20 chronological split, a 7-day lookback, and a true 24-hour forecast horizon.

## Run

From the repository root:

```bash
python research_v2/baseline_evaluation.py
```

Dependencies:

```bash
pip install numpy pandas scikit-learn
```

The output is written to:

`research_v2/results/baseline_metrics.csv`

## Paper changes after baseline results

1. State clearly that the reported 2024 training/evaluation series are synthetic unless a real/public provenance can be documented.
2. Remove the unsupported claim of 10–15% downtime reduction.
3. Remove accuracy, precision, and recall from regression evaluation.
4. Correct all lag/lookback/horizon descriptions to reflect actual sampling intervals.
5. Compare Bi-LSTM against Persistence, Seasonal Naive, and Random Forest using MAE, RMSE, and R².
6. Add a limitations section covering synthetic data, lack of real-fleet validation, and generalization risk.
7. Present Salesforce/Swift as the deployment/action layer rather than evidence of predictive accuracy.

## Minimum result table for the paper

| Target | Model | MAE | RMSE | R² |
|---|---|---:|---:|---:|
| Engine temperature | Persistence |  |  |  |
| Engine temperature | Seasonal naive |  |  |  |
| Engine temperature | Random Forest |  |  |  |
| Engine temperature | Bi-LSTM |  |  |  |
| Tyre pressure | Persistence |  |  |  |
| Tyre pressure | Seasonal naive |  |  |  |
| Tyre pressure | Random Forest |  |  |  |
| Tyre pressure | Bi-LSTM |  |  |  |
| Tyre temperature | Persistence |  |  |  |
| Tyre temperature | Seasonal naive |  |  |  |
| Tyre temperature | Random Forest |  |  |  |
| Tyre temperature | Bi-LSTM |  |  |  |
