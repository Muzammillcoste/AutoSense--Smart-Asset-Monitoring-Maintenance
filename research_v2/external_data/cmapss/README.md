# NASA C-MAPSS FD001 data

The raw C-MAPSS files are not committed to this repository. To rerun the C-MAPSS experiments, download the official archive from NASA and place these files in this folder:

| File | Needed for |
|---|---|
| `train_FD001.txt` | Forecasting and stage analysis; the only file used for modelling |
| `test_FD001.txt` | Checking that the archive is complete |
| `RUL_FD001.txt` | Checking that the archive is complete |
| `CMAPSSData.zip` | Optional copy of the source archive |

## Where the data came from

The data were downloaded from https://data.nasa.gov/docs/legacy/CMAPSSData.zip on 2026-09-06. Expected SHA256 hashes:

| File | SHA256 |
|---|---|
| `CMAPSSData.zip` | `74bef434a34db25c7bf72e668ea4cd52afe5f2cfe44367c55a82bfd91a5a34f` |
| `train_FD001.txt` | `963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8` |
| `test_FD001.txt` | `3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851` |
| `RUL_FD001.txt` | `a19c8ec94931949d0485bdc35118206e9c81c4547b422efb9cf86f4ceddbceca` |

These details, the citation and NASA's usage note are also recorded in [`../../ieee_results/provenance.json`](../../ieee_results/provenance.json).

**Citation:** A. Saxena and K. Goebel (2008), *Turbofan Engine Degradation Simulation Data Set*, NASA Prognostics Data Repository, NASA Ames Research Center.

## How the data are used

- **Why only the training file.** The engines in `train_FD001.txt` run to failure, so every forecast window has a complete future trajectory. The official test trajectories stop before failure, and nothing is forecast beyond that point.
- **What the data are.** C-MAPSS is simulator output, not measured flight telemetry. The study uses it to forecast sensor values, not to predict remaining useful life.
- **Committed copy.** A copy of `train_FD001.txt` is included in the two C-MAPSS input bundles in [`../../kaggle/`](../../kaggle/), which were used for the Kaggle runs.
