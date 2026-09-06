"""Build the review handoff from completed, verified experiment artifacts."""
import hashlib
import json
import subprocess
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "results"

def table(df):
    def val(v):
        return f"{v:.6f}" if isinstance(v, float) else str(v)
    return "| " + " | ".join(df.columns) + " |\n| " + " | ".join(["---"]*len(df.columns)) + " |\n" + "\n".join("| " + " | ".join(val(v) for v in row) + " |" for row in df.itertuples(index=False,name=None))

def main():
    df = pd.read_csv(OUT/"final_comparison.csv").sort_values("Dataset", kind="stable")
    hr = pd.read_csv(OUT/"bilstm_horizon_metrics.csv")
    verification = json.loads((OUT/"verification.json").read_text(encoding="utf-8"))
    assert len(df) == 12 and len(verification) == 3
    assert all(v["Comparison SHA256"] == hashlib.sha256((OUT/"final_comparison.csv").read_bytes()).hexdigest() for v in verification)
    env = json.loads((OUT/"environment.json").read_text(encoding="utf-8"))
    effects=[]
    for name,group in df.groupby("Dataset",sort=False):
        base=group[group.Model != "Bi-LSTM"].sort_values("MAE").iloc[0]
        bi=group[group.Model == "Bi-LSTM"].iloc[0]
        effects.append({"Dataset":name,"Best baseline by MAE":base.Model,"Baseline MAE":base.MAE,
                        "Bi-LSTM MAE":bi.MAE,"MAE improvement (%)":100*(base.MAE-bi.MAE)/base.MAE})
    effects=pd.DataFrame(effects)
    effects.to_csv(OUT/"mae_comparison.csv",index=False)
    wins=int((effects["MAE improvement (%)"]>0).sum())
    split=df[df.Model=="Bi-LSTM"]
    capped = split.loc[split["Best epoch"] == split["Max epochs"], "Dataset"].tolist()
    cap_note = ("Best validation performance occurred at the epoch cap for: " + ", ".join(capped) +
                ". Convergence is not established for these models; additional training might improve performance. "
                "No further tuning was performed after observing test scores.") if capped else ""
    git_diff=subprocess.run(["git","diff","--stat"],cwd=HERE.parent,capture_output=True,text=True).stdout.strip()
    source_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob("*.py")}
    (OUT/"source_hashes.json").write_text(json.dumps(source_hashes,indent=2),encoding="utf-8")
    report="""## REPORT FOR CHATGPT REVIEW

The experiment and legacy-metric audit are complete. This is a single-seed, fixed-budget benchmark of **24-hour multi-step sensor forecasting for threshold-based predictive maintenance** on three demonstrably synthetic datasets. It does not establish direct failure prediction, remaining useful life or operational downtime benefits. The paper has not been rewritten.

### Final aggregate metrics

MAE and RMSE use the listed physical unit; R2 is dimensionless. All metrics flatten the same forecast-origin/horizon pairs for each dataset.

"""+table(df[["Dataset","Model","MAE","RMSE","R2","Unit"]])+"\n\n### Comparison against the best baseline\n\n"+table(effects)+f"""

Positive improvement means lower Bi-LSTM MAE; negative means degradation. Formula: 100 * (best baseline MAE - Bi-LSTM MAE) / best baseline MAE. Bi-LSTM beats the best baseline by MAE on **{wins} of 3** targets in this run. Report every target and metric, including failures to outperform. This establishes a result for the recorded configuration only; it cannot establish that the architecture can never perform better. No significance or general superiority claim is supported by one seed and one chronological test period.

### Timing and split boundaries

"""+table(split[["Dataset","Rows","Sampling interval (h)","Lookback steps","Horizon steps","Train windows","Validation windows","Test windows"]])+"\n\n"+table(split[["Dataset","Train first target","Train last target","Validation first target","Validation last target","Test first target","Test last target"]])+"""

Split raw rows first: test starts at floor(0.8*N); validation starts at floor(0.85*floor(0.8*N)). Both learned models fit only the first approximately 68% of rows. Validation is approximately 12%, and final test is 20%. Only windows whose complete targets lie within their partition are retained. The first test forecast can use earlier training/validation observations as history. Later forecast origins can use newly observed test history, without retraining. Overlapping errors inside a test partition are dependent; the number of windows is not an independent sample count.

The former baseline split overlapping windows and exposed H-1 test target timestamps to Random Forest fitting (23 engine, 7 tyre). It also used a different test boundary. Its old numbers are superseded, not mixed with these results. No test labels enter fitting or scaling in the corrected pipeline. Metadata and prediction checks confirm alignment across all four models.

### Architecture, selection and environment

All new Bi-LSTMs use historical target values only (one feature), identical information to the autoregressive Random Forest. The original 11-feature notebook setup is not replicated as the main benchmark. Architecture: bidirectional LSTM(128, return_sequences), batch normalization, dropout(.2), bidirectional LSTM(64, return_sequences), batch normalization, dropout(.3), LSTM(32), Dense(64, relu), dropout(.2), Dense(horizon). This retains the original layer sizes and family. Bidirectionality is confined to observed history.

Adam with MSE loss and MAE training metric; no classification metrics. MinMaxScaler fits only the fitting region. Seed 42, no shuffle, deterministic TensorFlow operations, oneDNN disabled. Early stopping monitors validation loss with patience 5 and restores best weights. A fixed 20-epoch maximum and batch size 64 were chosen before the test evaluation; no test-driven tuning or reduced LSTM units were used. Random Forest: 300 trees, depth 16, minimum leaf 2, seed 42.

"""+table(split[["Dataset","Epochs run","Best epoch","Training seconds"]])+"\n\n"+cap_note+"\n\n```json\n"+json.dumps(env,indent=2)+"\n```\n\n"+"""Pinned direct requirements and the complete `results/environment_freeze.txt` record include Keras 3.15.1 and h5py 3.16.0. No packages were installed or changed. Legacy scaler loading warned about scikit-learn 1.6.1 versus current 1.9.0; all three scaler transformations were independently reconstructed and matched. TensorFlow emitted an ignored unknown dataset-op attribute warning; the run completed and persisted predictions were verified. Cross-platform bitwise identity is not claimed.

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

"""+table(hr)+"""

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

All work remains on `research-paper-v2`. No commit, push or history rewrite was made, so there are no new commit hashes. Tracked-file diff summary follows; newly created files are listed above and are not included by ordinary `git diff --stat` until staged.

```text
"""+git_diff+"\n```\n"
    (HERE/"REPORT_FOR_CHATGPT_REVIEW.md").write_text(report,encoding="utf-8")
    print(effects.to_string(index=False))
    print("Saved",HERE/"REPORT_FOR_CHATGPT_REVIEW.md")

if __name__ == "__main__":
    main()
