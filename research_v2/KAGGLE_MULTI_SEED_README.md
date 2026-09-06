# Kaggle execution package for the IEEE multi-seed study

This notebook runs only Phase B of `IEEE_UPGRADE_PLAN.md`: the five prescribed
Bi-LSTM seeds (`11, 21, 42, 84, 168`) for the three AutoSense targets. It does
not change any scientific setting.

Before opening the notebook, upload the prepared single file
`research_v2/kaggle_multiseed_input_bundle.zip` as a private Kaggle Dataset.
The notebook extracts it automatically. Its internal layout is:

```text
<bundle-root>/
  research_v2/
    baseline_evaluation.py
    bilstm_evaluation.py
    protocol.py
    ieee_experiments/multiseed_bilstm.py
  FYP ML Training and Pipeline Code/
    Engine Temperature/karachi_2024_vehicle_temperature_data.csv
    TP_Generated/tyre_pressure_2024.csv
    Tyre Temperature/tyre_temp_2024.csv
```

Attach that private Dataset to a Kaggle notebook, enable Internet only if
Kaggle needs to install packages, and run
`ieee_experiments/kaggle_multiseed_bilstm.ipynb`. The notebook validates the
three input SHA256 values, executes the committed protocol from a writable
copy, and produces `autosense_multiseed_results.zip` for download.

After downloading, provide these two files back into this repository:

```text
research_v2/ieee_results/multiseed_bilstm_metrics.csv
research_v2/ieee_results/multiseed_summary.csv
```

Do not combine Kaggle rows with partial local rows. The notebook starts a
complete five-seed run in its own environment and records its environment and
source hashes in every output row.
