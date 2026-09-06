"""Persist the original fixed baselines, checking against committed results.

This calls the same evaluation utility, not a separate implementation. No neural
training, parameter search, split change, or replacement of results is performed.
"""
import sys
import json
import hashlib
import subprocess
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research_v2"))
from baseline_evaluation import DATASETS, evaluate_dataset, metrics

OUT = ROOT / "research_v2/paper/data"
RESULTS = ROOT / "research_v2/results"

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    committed = pd.read_csv(RESULTS / "final_comparison.csv")
    sources = [RESULTS / "final_comparison.csv", RESULTS / "bilstm_horizon_metrics.csv"]
    report = {"source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "method": "unchanged baseline_evaluation.evaluate_dataset, seed 42; export only",
              "datasets": {}, "sources": {}}
    horizon_rows = []
    for name, cfg in DATASETS.items():
        print("Exporting fixed baselines:", name, flush=True)
        if "--reuse" in sys.argv:
            b = np.load(OUT / name / "baseline_predictions.npz")
            actual = pd.DataFrame([{"Model": label, **metrics(b["truth"], b[key])}
                for key, label in [("persistence", "Persistence"), ("seasonal_naive", "Seasonal naive (previous 24 h)"), ("random_forest", "Random Forest")]])
        else:
            actual = evaluate_dataset(name, cfg, prediction_dir=OUT)
        for _, row in actual.iterrows():
            expected = committed[(committed.Dataset == name) & (committed.Model == row.Model)].iloc[0]
            np.testing.assert_allclose(row[["MAE", "RMSE", "R2"]].to_numpy(float),
                expected[["MAE", "RMSE", "R2"]].to_numpy(float), rtol=1e-10, atol=1e-10)
        saved = np.load(RESULTS / name / "test_predictions.npz")
        baseline = np.load(OUT / name / "baseline_predictions.npz")
        np.testing.assert_array_equal(saved["target_start_rows"], baseline["target_start_rows"])
        np.testing.assert_array_equal(saved["truth"], baseline["truth"])
        meta = json.loads((RESULTS / name / "metadata.json").read_text())
        assert hashlib.sha256(cfg["path"].read_bytes()).hexdigest() == meta["SHA256"]
        for key, label in [("persistence", "Persistence"), ("seasonal_naive", "Seasonal naive"), ("random_forest", "Random Forest")]:
            for h in range(saved["truth"].shape[1]):
                horizon_rows.append({"Dataset": name, "Model": label,
                    "Horizon (h)": (h+1)*meta["Sampling interval (h)"], "Unit": meta["Unit"],
                    **metrics(saved["truth"][:, h], baseline[key][:, h])})
        report["datasets"][name] = {"aggregate_match": True, "truth_and_origins_match": True,
            "baseline_prediction_sha256": hashlib.sha256((OUT / name / "baseline_predictions.npz").read_bytes()).hexdigest()}
        sources.extend([cfg["path"], RESULTS / name / "test_predictions.npz", RESULTS / name / "metadata.json"])
    for path in sources:
        rel = path.relative_to(ROOT).as_posix()
        blob = subprocess.check_output(["git", "show", "HEAD:" + rel], cwd=ROOT)
        # Git's checkout conversion may change LF to CRLF for text files.
        checked = subprocess.check_output(["git", "hash-object", "--path="+rel, rel], cwd=ROOT, text=True).strip()
        expected = subprocess.check_output(["git", "rev-parse", "HEAD:"+rel], cwd=ROOT, text=True).strip()
        assert checked == expected, f"Uncommitted scientific input: {rel}"
        report["sources"][rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    pd.DataFrame(horizon_rows).to_csv(OUT / "baseline_horizon_metrics.csv", index=False)
    (OUT / "baseline_export_verification.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print("All baseline metrics reproduced; truth/origins and committed source bytes verified.")

if __name__ == "__main__":
    main()
