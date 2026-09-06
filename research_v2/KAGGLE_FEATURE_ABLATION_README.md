# Kaggle: AutoSense causal feature ablation

## Upload and attach

Create a private Kaggle Dataset containing exactly
`research_v2/kaggle_feature_ablation_input_bundle.zip`, then attach it in the
Kaggle notebook Input panel. Do not unzip or change bundle contents.

Enable a GPU accelerator. The fixed experiment trains nine LSTMs and fits nine
Random Forests across the three AutoSense targets and F0/F1/F2 configurations.

## Run

Import and run
`research_v2/ieee_experiments/kaggle_feature_ablation.ipynb` in order. It
checks all input hashes before training, requires 18 unique result rows, and
asserts that F2's causal lag/rolling-feature policy discards no standard test
origins.

Download `feature_ablation_results.zip` and extract into
`research_v2/ieee_results/`:

- `feature_ablation.csv`
- `kaggle_feature_ablation_run_manifest.json`

Do not append this output to a partial/local feature-ablation CSV.
