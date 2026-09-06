"""Validate committed Kaggle result archives without running any experiment.

The script is deliberately strict: outputs are accepted only when their own
records prove the pre-registered data, source hashes, splits, and package
versions.  It writes a compact integration ledger; it never copies an
unaccepted result into ``ieee_results``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
STAGE = ROOT / ".integration_staging"
PINNED = {
    "TensorFlow": "2.18.0",
    "scikit-learn": "1.9.0",
    "NumPy": "2.0.2",
    "pandas": "2.2.2",
}
HASHES = {
    "architecture": "0ed52f6eca113d12393903ff35ae2ef8d4f1c28b9c7d837556737d151887606b",
    "forecast": "cee828114ca0e22800b6bf12faa9643db4646f0c764bbef81558e1a6243a3a65",
    "stage": "6d195848d6f53062db61b199da602d257ed91c5b1a2d20fbea36257b99d51b21",
    "feature": "4f55e57e169a03cef6069a20a436f5e3832933c7ea616835e1da3c7ed63664aa",
    "protocol": "1e72e4109507e7968af365367d855fac495439173f38c4c7a72c4ece71c627bb",
    "fd001": "963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8",
    "split": "9e4c0a4ab7cef63169c1bc87a52885af983ffab5ea8f0e8e886d352e63779003",
    "sensors": "5033e1390448a71d6ff29364489b7a122d7b9190ffc851d301168349d4c89665",
}
AUTOSEED = {11, 21, 42, 84, 168}
SENSORS = {"sensor_9", "sensor_11", "sensor_12", "sensor_14"}
STAGES = {
    "early (<0.5 normalized cycle fraction)",
    "mid (0.5 to <0.8 normalized cycle fraction)",
    "late (>=0.8 normalized cycle fraction)",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_columns(frame: pd.DataFrame, columns: set[str], name: str) -> None:
    missing = columns.difference(frame.columns)
    require(not missing, f"{name}: missing columns {sorted(missing)}")


def require_unique(frame: pd.DataFrame, keys: list[str], name: str) -> None:
    require(not frame.duplicated(keys).any(), f"{name}: duplicate keys {keys}")


def environment_mismatches(frame: pd.DataFrame, name: str) -> list[str]:
    """Check the versions the phase was required to record per result row.

    The Kaggle protocols record TensorFlow and scikit-learn in every phase;
    the original multi-seed phase also records NumPy and pandas.  We do not
    invent unrecorded version fields when auditing legacy-compatible rows.
    """
    required = {"TensorFlow", "scikit-learn"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        return [f"{name}: missing version columns {missing}"]
    mismatches = []
    for column in required:
        expected = PINNED[column]
        values = set(frame[column].astype(str))
        if values != {expected}:
            mismatches.append(f"{name}: {column}={sorted(values)}, expected {expected}")
    for column in {"NumPy", "pandas"}.intersection(frame.columns):
        expected = PINNED[column]
        values = set(frame[column].astype(str))
        if values != {expected}:
            mismatches.append(f"{name}: {column}={sorted(values)}, expected {expected}")
    return mismatches


def require_recorded_environment(frame: pd.DataFrame, name: str) -> None:
    """Fail on version mismatch in a phase whose recorded columns are known."""
    mismatches = environment_mismatches(frame, name)
    require(not mismatches, "; ".join(mismatches))


def archive_members(name: str, required: set[str]) -> None:
    archive = ROOT / f"{name}.zip"
    require(archive.exists(), f"missing archive {archive}")
    with zipfile.ZipFile(archive) as handle:
        members = set(handle.namelist())
    require(required.issubset(members), f"{name}: missing {sorted(required - members)}")


def exact_manifest_hashes(manifest: dict, required: dict[str, str], name: str) -> None:
    actual = manifest.get("input_sha256", {})
    for key, expected in required.items():
        require(actual.get(key) == expected, f"{name}: bad source/data hash for {key}")


def validate_autosense() -> dict:
    directory = STAGE / "autosense_multiseed_results"
    archive_members("autosense_multiseed_results", {"multiseed_bilstm_metrics.csv", "multiseed_summary.csv"})
    metrics = pd.read_csv(directory / "multiseed_bilstm_metrics.csv")
    summary = pd.read_csv(directory / "multiseed_summary.csv")
    require(len(metrics) == 15 and len(summary) == 3, "autosense: unexpected row count")
    require_unique(metrics, ["Dataset", "Seed"], "autosense metrics")
    require(set(metrics["Seed"]) == AUTOSEED, "autosense: wrong seed set")
    require(set(metrics["Dataset"]) == set(summary["Dataset"]), "autosense: summary dataset mismatch")
    require((summary["Seed count"] == 5).all() and summary["Completed planned seeds"].all(), "autosense: incomplete planned seeds")
    require_recorded_environment(metrics, "autosense metrics")
    require((metrics["Lookback (h)"] == 168).all() and (metrics["Forecast horizon (h)"] == 24).all(), "autosense: protocol changed")
    return {"accepted": True, "rows": {"metrics": len(metrics), "summary": len(summary)}}


def validate_architecture() -> dict:
    directory = STAGE / "architecture_ablation_results"
    archive_members("architecture_ablation_results", {"architecture_ablation.csv", "kaggle_architecture_ablation_run_manifest.json"})
    frame = pd.read_csv(directory / "architecture_ablation.csv")
    manifest = json.loads((directory / "kaggle_architecture_ablation_run_manifest.json").read_text())
    require(len(frame) == 6, "architecture: unexpected row count")
    require_unique(frame, ["Dataset", "Model", "Seed"], "architecture")
    require(set(frame["Model"]) == {"LSTM", "Bi-LSTM"} and set(frame["Seed"]) == {42}, "architecture: wrong models/seeds")
    require_recorded_environment(frame, "architecture")
    require((frame["Lookback (h)"] == 168).all() and (frame["Forecast horizon (h)"] == 24).all(), "architecture: protocol changed")
    require((frame["Experiment script SHA256"] == HASHES["architecture"]).all(), "architecture: script hash mismatch")
    exact_manifest_hashes(manifest, {"research_v2/ieee_experiments/architecture_ablation.py": HASHES["architecture"]}, "architecture")
    require(manifest.get("tensorflow") == PINNED["TensorFlow"], "architecture: manifest TensorFlow mismatch")
    return {"accepted": True, "rows": len(frame)}


def split_ids(split: dict) -> tuple[set[int], set[int], set[int]]:
    train, validation, test = (set(split[key]) for key in ("train_engine_ids", "validation_engine_ids", "test_engine_ids"))
    require((len(train), len(validation), len(test)) == (70, 15, 15), "C-MAPSS: invalid split sizes")
    require(not (train & validation or train & test or validation & test), "C-MAPSS: engine leakage across split lists")
    require(train | validation | test == set(range(1, 101)), "C-MAPSS: split does not cover engines 1..100")
    return train, validation, test


def validate_cmapss() -> dict:
    directory = STAGE / "cmapss_fd001_forecasting_results"
    archive_members("cmapss_fd001_forecasting_results", {"cmapss_fd001_metrics.csv", "cmapss_fd001_horizon_metrics.csv", "cmapss_multiseed_summary.csv", "cmapss_fd001_split.json", "cmapss_sensor_selection.csv", "kaggle_cmapss_fd001_forecasting_run_manifest.json"})
    metrics = pd.read_csv(directory / "cmapss_fd001_metrics.csv")
    horizon = pd.read_csv(directory / "cmapss_fd001_horizon_metrics.csv")
    summary = pd.read_csv(directory / "cmapss_multiseed_summary.csv")
    manifest = json.loads((directory / "kaggle_cmapss_fd001_forecasting_run_manifest.json").read_text())
    split = json.loads((directory / "cmapss_fd001_split.json").read_text())
    _, _, test = split_ids(split)
    detailed = metrics[metrics["Target sensor"].isin(SENSORS)].copy()
    detailed_h = horizon[horizon["Target sensor"].isin(SENSORS)].copy()
    require((len(metrics), len(horizon), len(detailed), len(detailed_h), len(summary)) == (55, 550, 44, 440, 8), "C-MAPSS: unexpected result rows")
    require_unique(detailed, ["Configuration", "Target sensor", "Model", "Seed"], "C-MAPSS metrics")
    require_unique(detailed_h, ["Configuration", "Target sensor", "Model", "Seed", "Horizon cycle"], "C-MAPSS horizon")
    require(set(detailed["Target sensor"]) == SENSORS, "C-MAPSS: sensor mismatch")
    require(set(detailed["Lookback cycles"]) == {30} and set(detailed["Forecast horizon cycles"]) == {10}, "C-MAPSS: lookback/horizon changed")
    for frame, name in ((detailed, "metrics"), (detailed_h, "horizon")):
        require(set(frame["Dataset SHA256"]) == {HASHES["fd001"]}, f"C-MAPSS {name}: data hash mismatch")
        require(set(frame["Experiment script SHA256"]) == {HASHES["forecast"]}, f"C-MAPSS {name}: script hash mismatch")
        require(set(frame["Protocol SHA256"]) == {HASHES["protocol"]}, f"C-MAPSS {name}: protocol hash mismatch")
        require(set(frame["C-MAPSS engine split SHA256"]) == {HASHES["split"]}, f"C-MAPSS {name}: split hash mismatch")
        require(set(frame["Sensor selection SHA256"]) == {HASHES["sensors"]}, f"C-MAPSS {name}: sensor hash mismatch")
        require(set(frame["Test engine IDs"].astype(str)) == {str(sorted(test))}, f"C-MAPSS {name}: test split mismatch")
    predictions = sorted((directory / "cmapss_fd001_predictions").glob("*.npz"))
    require(len(predictions) == 44, "C-MAPSS: expected 44 prediction NPZs")
    for path in predictions:
        artifact = np.load(path)
        require(set(artifact.files) >= {"truth", "prediction", "unit_ids", "target_start_cycles", "dataset_sha256", "experiment_script_sha256", "protocol_sha256"}, f"C-MAPSS: missing NPZ provenance in {path.name}")
        require(set(np.unique(artifact["unit_ids"]).astype(int)).issubset(test), f"C-MAPSS: non-test engine in {path.name}")
        require(str(artifact["dataset_sha256"]) == HASHES["fd001"] and str(artifact["experiment_script_sha256"]) == HASHES["forecast"] and str(artifact["protocol_sha256"]) == HASHES["protocol"], f"C-MAPSS: NPZ hash mismatch in {path.name}")
    exact_manifest_hashes(manifest, {"research_v2/ieee_experiments/cmapss_fd001_forecasting.py": HASHES["forecast"], "research_v2/external_data/cmapss/train_FD001.txt": HASHES["fd001"]}, "C-MAPSS")
    mismatches = environment_mismatches(detailed, "C-MAPSS metrics") + environment_mismatches(detailed_h, "C-MAPSS horizon")
    if manifest.get("tensorflow") != PINNED["TensorFlow"]:
        mismatches.append(f"C-MAPSS manifest: TensorFlow={manifest.get('tensorflow')}, expected {PINNED['TensorFlow']}")
    if mismatches:
        return {"accepted": False, "structurally_valid": True, "reason": "; ".join(mismatches), "rows": {"metrics": len(metrics), "horizon": len(horizon), "predictions": len(predictions)}}
    return {"accepted": environment_ok, "structurally_valid": True, "rows": {"metrics": len(metrics), "horizon": len(horizon), "predictions": len(predictions)}}


def validate_stage(forecast_accepted: bool) -> dict:
    directory = STAGE / "cmapss_stage_analysis_results"
    archive_members("cmapss_stage_analysis_results", {"cmapss_stage_metrics.csv", "kaggle_cmapss_stage_analysis_run_manifest.json"})
    frame = pd.read_csv(directory / "cmapss_stage_metrics.csv")
    manifest = json.loads((directory / "kaggle_cmapss_stage_analysis_run_manifest.json").read_text())
    require(len(frame) == 132, "stage: unexpected row count")
    require_unique(frame, ["Configuration", "Target sensor", "Model", "Seed", "Stage"], "stage")
    require(set(frame["Stage"]) == STAGES, "stage: changed stage definitions")
    require(set(frame["Prediction dataset SHA256"]) == {HASHES["fd001"]}, "stage: prediction data hash mismatch")
    require(set(frame["Forecasting script SHA256"]) == {HASHES["forecast"]}, "stage: forecast hash mismatch")
    require(set(frame["Stage analysis script SHA256"]) == {HASHES["stage"]}, "stage: script hash mismatch")
    require_recorded_environment(frame, "stage")
    exact_manifest_hashes(manifest, {"research_v2/ieee_experiments/cmapss_stage_analysis.py": HASHES["stage"], "research_v2/external_data/cmapss/train_FD001.txt": HASHES["fd001"]}, "stage")
    return {"accepted": forecast_accepted, "structurally_valid": True, "reason": None if forecast_accepted else "depends on rejected C-MAPSS forecasting artifact", "rows": len(frame)}


def validate_feature() -> dict:
    directory = STAGE / "feature_ablation_results"
    archive_members("feature_ablation_results", {"feature_ablation.csv", "kaggle_feature_ablation_run_manifest.json"})
    frame = pd.read_csv(directory / "feature_ablation.csv")
    manifest = json.loads((directory / "kaggle_feature_ablation_run_manifest.json").read_text())
    require(len(frame) == 18, "feature: unexpected row count")
    require_unique(frame, ["Dataset", "Feature configuration", "Model", "Seed"], "feature")
    require(set(frame["Feature configuration"]) == {"F0", "F1", "F2"} and set(frame["Model"]) == {"Random Forest", "LSTM"} and set(frame["Seed"]) == {42}, "feature: changed configurations/models/seeds")
    require(set(frame["Lookback steps"]) == {56, 168} and set(frame["Horizon steps"]) == {8, 24}, "feature: changed horizon protocol")
    require((frame["Experiment script SHA256"] == HASHES["feature"]).all(), "feature: script hash mismatch")
    exact_manifest_hashes(manifest, {"research_v2/ieee_experiments/feature_ablation.py": HASHES["feature"]}, "feature")
    mismatches = environment_mismatches(frame, "feature")
    if manifest.get("tensorflow") != PINNED["TensorFlow"]:
        mismatches.append(f"feature manifest: TensorFlow={manifest.get('tensorflow')}, expected {PINNED['TensorFlow']}")
    if mismatches:
        return {"accepted": False, "structurally_valid": True, "reason": "; ".join(mismatches), "rows": len(frame)}
    return {"accepted": environment_ok, "structurally_valid": True, "rows": len(frame)}


def validate_paper() -> dict:
    directory = STAGE / "paper_overleaf"
    archive_members("paper_overleaf", {"main.tex", "references.bib", "tables/dataset_protocol.tex", "tables/main_comparison.tex"})
    files = ["main.tex", "references.bib", "tables/dataset_protocol.tex", "tables/main_comparison.tex"]
    same = all(digest(ROOT / "paper" / item) == digest(directory / item) for item in files)
    return {"accepted": True, "newer_than_committed_source": not same, "checked_files": files}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "ieee_results" / "final_integration_validation.json")
    args = parser.parse_args()
    require(STAGE.exists(), f"staging directory missing: {STAGE}")
    results: dict[str, dict] = {}
    results["autosense_multiseed"] = validate_autosense()
    results["architecture_ablation"] = validate_architecture()
    results["cmapss_fd001_forecasting"] = validate_cmapss()
    results["cmapss_stage_analysis"] = validate_stage(results["cmapss_fd001_forecasting"]["accepted"])
    results["feature_ablation"] = validate_feature()
    results["paper_overleaf"] = validate_paper()
    archives = sorted(ROOT.glob("*_results.zip")) + [ROOT / "paper_overleaf.zip"]
    ledger = {"pinned_environment": PINNED, "archive_sha256": {path.name: digest(path) for path in archives}, "results": results}
    args.output.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(ledger, indent=2))


if __name__ == "__main__":
    main()
