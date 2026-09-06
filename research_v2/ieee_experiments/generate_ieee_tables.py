"""Generate IEEE manuscript result tables directly from accepted CSV artifacts."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "ieee_results"
OUT = ROOT / "paper" / "tables" / "ieee_upgrade"


def label(dataset: str) -> str:
    return {"engine_temperature": "Engine temperature", "tyre_pressure": "Tyre pressure", "tyre_temperature": "Tyre temperature"}[dataset]


def unit(value: str) -> str:
    return "\\degC" if str(value).replace("Â", "") == "°C" else str(value)


def write(name: str, headers: list[str], rows: list[list[str]], alignment: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    lines = [f"\\begin{{tabular}}{{{alignment}}}", "\\toprule", " & ".join(headers) + r" \\", "\\midrule"]
    lines.extend(" & ".join(row) + r" \\" for row in rows)
    lines.extend(["\\bottomrule", "\\end{tabular}"])
    (OUT / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def robustness() -> None:
    frame = pd.read_csv(RESULTS / "multiseed_summary.csv")
    rows = [[label(row.Dataset), f"{row['MAE mean']:.3f} $\\pm$ {row['MAE std']:.3f}",
             f"{row['RMSE mean']:.3f} $\\pm$ {row['RMSE std']:.3f}",
             f"{row['R2 mean']:.3f} $\\pm$ {row['R2 std']:.3f}", unit(row.Unit)]
            for _, row in frame.iterrows()]
    write("multiseed_robustness.tex", ["Dataset", "MAE", "RMSE", "$R^2$", "Unit"], rows, "lrrrr")


def architecture() -> None:
    frame = pd.read_csv(RESULTS / "architecture_ablation.csv")
    rows = []
    for dataset, group in frame.groupby("Dataset", sort=False):
        indexed = group.set_index("Model")
        rows.append([label(dataset), f"{indexed.loc['LSTM', 'MAE']:.3f}", f"{indexed.loc['Bi-LSTM', 'MAE']:.3f}",
                     f"{indexed.loc['LSTM', 'R2']:.3f}", f"{indexed.loc['Bi-LSTM', 'R2']:.3f}", unit(indexed.loc['LSTM', 'Unit'])])
    write("architecture_ablation.tex", ["Dataset", "LSTM MAE", "Bi-LSTM MAE", "LSTM $R^2$", "Bi-LSTM $R^2$", "Unit"], rows, "lrrrrr")


def feature() -> None:
    frame = pd.read_csv(RESULTS / "feature_ablation.csv")
    rows = []
    for (dataset, model), group in frame.groupby(["Dataset", "Model"], sort=False):
        indexed = group.set_index("Feature configuration")
        model_label = "RF" if model == "Random Forest" else model
        rows.append([label(dataset), model_label, *(f"{indexed.loc[key, 'MAE']:.3f}" for key in ("F0", "F1", "F2")), unit(indexed.Unit.iloc[0])])
    write("feature_ablation.tex", ["Dataset", "Model", "F0 MAE", "F1 MAE", "F2 MAE", "Unit"], rows, "llrrrr")


def threshold() -> None:
    frame = pd.read_csv(RESULTS / "threshold_event_metrics.csv")
    rows = []
    for _, row in frame.iterrows():
        model = row.Model.replace("Seasonal naive (previous 24 h)", "Seasonal naive")
        rows.append([label(row.Dataset), model, f"{row['Precision']:.3f}", f"{row['Recall']:.3f}", f"{row['F1']:.3f}", f"{row['False positive rate']:.3f}"])
    write("threshold_events.tex", ["Dataset", "Model", "Precision", "Recall", "F1", "FPR"], rows, "llrrrr")


def cmapss() -> None:
    frame = pd.read_csv(RESULTS / "cmapss_fd001_metrics.csv")
    frame = frame[frame["Target sensor"].eq("MACRO_AVERAGE_NORMALIZED")]
    rows = [[row.Configuration, row.Model, str(int(row.Seed)), f"{row['Normalized MAE']:.5f}",
             f"{row['Normalized RMSE']:.5f}", f"{row.R2:.5f}"] for _, row in frame.iterrows()]
    write("cmapss_macro_forecasting.tex", ["Configuration", "Model", "Seed", "NMAE", "NRMSE", "$R^2$"], rows, "llrrrr")


def manifest() -> None:
    sources = [
        "multiseed_summary.csv", "architecture_ablation.csv", "feature_ablation.csv",
        "threshold_event_metrics.csv", "cmapss_fd001_metrics.csv", "cmapss_stage_metrics.csv",
    ]
    data = {name: __import__("hashlib").sha256((RESULTS / name).read_bytes()).hexdigest() for name in sources}
    (OUT / "asset_manifest.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    robustness(); architecture(); feature(); threshold(); cmapss(); manifest()
    print(f"Saved IEEE-upgrade tables to {OUT}")


if __name__ == "__main__":
    main()
