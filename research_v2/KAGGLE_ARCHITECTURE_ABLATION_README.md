# Kaggle: AutoSense architecture ablation

## Upload and attach

Create a private Kaggle Dataset containing exactly
`research_v2/kaggle_architecture_ablation_input_bundle.zip`, then attach that
Dataset in the notebook **Input** panel. Do not unzip or alter the bundle.

Enable a GPU accelerator. The experiment is small but trains six recurrent
networks and will use GPU when available.

## Run

Import and run
`research_v2/ieee_experiments/kaggle_architecture_ablation.ipynb` in order.
It validates all seven source/data SHA256 hashes before it trains the fixed
seed-42 LSTM/Bi-LSTM comparison. It expects exactly six result rows.

Download `architecture_ablation_results.zip` from Kaggle Output. Extract its
contents into `research_v2/ieee_results/` locally:

- `architecture_ablation.csv`
- `kaggle_architecture_ablation_run_manifest.json`

Do not merge it with any partial/local ablation CSV.
