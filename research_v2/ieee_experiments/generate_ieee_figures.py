"""Generate grayscale-safe IEEE figures only from accepted result artifacts."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib-cache"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


OUT = ROOT / "paper" / "figures" / "ieee_upgrade"
RESULTS = ROOT / "ieee_results"
HATCHES = ["", "//", "xx", "..", "\\\\"]
COLORS = ["#f2f2f2", "#bdbdbd", "#737373", "#252525", "#ffffff"]
DATASET_LABELS = {
    "engine_temperature": "Engine temperature",
    "tyre_pressure": "Tyre pressure",
    "tyre_temperature": "Tyre temperature",
}


def save(fig: plt.Figure, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def robustness() -> None:
    frame = pd.read_csv(RESULTS / "multiseed_summary.csv")
    fig, axes = plt.subplots(1, 3, figsize=(7.1, 2.25))
    for ax, (_, row) in zip(axes, frame.iterrows()):
        ax.bar([0], [row["MAE mean"]], yerr=[row["MAE std"]], capsize=3,
               color=COLORS[2], edgecolor="black", hatch="//")
        ax.set_xlim(-.75, .75); ax.set_xticks([])
        ax.set_title(DATASET_LABELS[row.Dataset], fontsize=8)
        ax.set_ylabel(f"MAE ({row.Unit})")
        ax.grid(axis="y", alpha=.25)
    fig.suptitle("Bi-LSTM five-seed robustness (mean ± sample SD)", y=1.02, fontsize=10)
    save(fig, "multiseed_robustness")


def ablations() -> None:
    architecture = pd.read_csv(RESULTS / "architecture_ablation.csv")
    feature = pd.read_csv(RESULTS / "feature_ablation.csv")
    datasets = list(architecture.Dataset.drop_duplicates())
    fig, axes = plt.subplots(2, 3, figsize=(7.1, 4.0))
    for col, dataset in enumerate(datasets):
        ax = axes[0, col]
        group = architecture[architecture.Dataset.eq(dataset)]
        labels = list(group.Model)
        ax.bar(np.arange(len(group)), group.MAE, color=COLORS[:len(group)], edgecolor="black")
        for bar, hatch in zip(ax.patches, HATCHES):
            bar.set_hatch(hatch)
        ax.set_xticks(np.arange(len(group)), labels, fontsize=7)
        ax.set_title(DATASET_LABELS[dataset], fontsize=8)
        ax.set_ylabel(f"MAE ({group.Unit.iloc[0]})")
        ax.grid(axis="y", alpha=.25)
    for col, dataset in enumerate(datasets):
        ax = axes[1, col]
        group = feature[feature.Dataset.eq(dataset)]
        group = group.assign(
            _feature=pd.Categorical(group["Feature configuration"], ["F0", "F1", "F2"], ordered=True),
            _model=pd.Categorical(group.Model, ["Random Forest", "LSTM"], ordered=True),
        ).sort_values(["_feature", "_model"])
        labels = [f"{row['Feature configuration']} {'RF' if row.Model == 'Random Forest' else 'LSTM'}" for _, row in group.iterrows()]
        ax.bar(np.arange(len(group)), group.MAE, color=[COLORS[i % 2] for i in range(len(group))], edgecolor="black")
        for index, bar in enumerate(ax.patches):
            bar.set_hatch(HATCHES[index % 2])
        ax.set_xticks(np.arange(len(group)), labels, rotation=45, ha="right", fontsize=6)
        ax.set_ylabel(f"MAE ({group.Unit.iloc[0]})")
        ax.grid(axis="y", alpha=.25)
    axes[0, 0].annotate("Architecture (seed 42)", xy=(0, 1.16), xycoords="axes fraction", fontsize=8)
    axes[1, 0].annotate("Causal feature configurations (seed 42)", xy=(0, 1.16), xycoords="axes fraction", fontsize=8)
    save(fig, "architecture_feature_ablation")


def threshold_events() -> None:
    frame = pd.read_csv(RESULTS / "threshold_event_metrics.csv")
    fig, axes = plt.subplots(1, 3, figsize=(7.1, 2.35), sharey=True)
    for ax, (dataset, group) in zip(axes, frame.groupby("Dataset", sort=False)):
        x = np.arange(len(group))
        ax.bar(x, group.F1, color=COLORS[:len(group)], edgecolor="black")
        for bar, hatch in zip(ax.patches, HATCHES):
            bar.set_hatch(hatch)
        labels = [model.replace("Seasonal naive (previous 24 h)", "Seasonal")
                        .replace("Random Forest", "RF").replace(" ", "\n") for model in group.Model]
        ax.set_xticks(x, labels, fontsize=6)
        ax.set_title(f"{DATASET_LABELS[dataset]}\nprevalence={group['Event prevalence'].iloc[0]:.3f}", fontsize=7)
        ax.grid(axis="y", alpha=.25)
    axes[0].set_ylabel("F1 (proxy event)")
    fig.suptitle("Training-derived threshold-event evaluation", y=1.04, fontsize=10)
    save(fig, "threshold_event_evaluation")


def cmapss() -> None:
    metrics = pd.read_csv(RESULTS / "cmapss_fd001_metrics.csv")
    horizon = pd.read_csv(RESULTS / "cmapss_fd001_horizon_metrics.csv")
    targets = ["sensor_9", "sensor_11", "sensor_14", "sensor_12"]
    fig, axes = plt.subplots(2, 2, figsize=(7.1, 4.1)); axes = axes.ravel()
    for ax, target in zip(axes, targets):
        group = metrics[(metrics.Configuration.eq("C1")) & (metrics["Target sensor"].eq(target))]
        group = group[(group.Model.ne("Bi-LSTM")) | (group.Seed.eq(42))]
        x = np.arange(len(group))
        ax.bar(x, group["Normalized MAE"], color=COLORS[:len(group)], edgecolor="black")
        for bar, hatch in zip(ax.patches, HATCHES):
            bar.set_hatch(hatch)
        ax.set_xticks(x, group.Model, rotation=25, ha="right", fontsize=6)
        ax.set_title(target, fontsize=8); ax.set_ylabel("Normalized MAE")
        ax.grid(axis="y", alpha=.25)
    save(fig, "cmapss_external_validation")
    fig, ax = plt.subplots(figsize=(3.45, 2.35))
    group = horizon[(horizon.Configuration.eq("C1")) & (horizon["Target sensor"].eq("sensor_9"))]
    group = group[(group.Model.ne("Bi-LSTM")) | (group.Seed.eq(42))]
    for j, (model, series) in enumerate(group.groupby("Model", sort=False)):
        ax.plot(series["Horizon cycle"], series["Normalized MAE"], marker="o", markersize=2,
                color=COLORS[j + 1], linestyle=["-", "--", ":"][j], label=model)
    ax.set_xlabel("Forecast horizon (cycles)"); ax.set_ylabel("Normalized MAE")
    ax.set_title("FD001 C1 horizon error: sensor_9"); ax.grid(alpha=.25); ax.legend(fontsize=6)
    save(fig, "cmapss_horizon_mae")


def stage() -> None:
    frame = pd.read_csv(RESULTS / "cmapss_stage_metrics.csv")
    targets = ["sensor_9", "sensor_11", "sensor_14", "sensor_12"]
    fig, axes = plt.subplots(2, 2, figsize=(7.1, 4.1)); axes = axes.ravel()
    order = ["early (<0.5 normalized cycle fraction)", "mid (0.5 to <0.8 normalized cycle fraction)", "late (>=0.8 normalized cycle fraction)"]
    for ax, target in zip(axes, targets):
        group = frame[(frame.Configuration.eq("C1")) & (frame["Target sensor"].eq(target))]
        group = group[(group.Model.ne("Bi-LSTM")) | (group.Seed.eq(42))]
        pivot = group.pivot(index="Stage", columns="Model", values="MAE").reindex(order)
        x = np.arange(len(pivot)); width = .8 / len(pivot.columns)
        for j, model in enumerate(pivot.columns):
            ax.bar(x + (j - (len(pivot.columns) - 1) / 2) * width, pivot[model], width,
                   label=model, color=COLORS[j], edgecolor="black", hatch=HATCHES[j])
        ax.set_xticks(x, ["Early", "Mid", "Late"], fontsize=7)
        ax.set_title(target, fontsize=8); ax.set_ylabel("MAE (native sensor unit)")
        ax.grid(axis="y", alpha=.25)
    axes[0].legend(fontsize=6)
    save(fig, "cmapss_stage_error")


def main() -> None:
    plt.rcParams.update({"font.size": 8, "pdf.fonttype": 42, "ps.fonttype": 42})
    robustness(); ablations(); threshold_events(); cmapss(); stage()
    print(f"Saved IEEE-upgrade figures to {OUT}")


if __name__ == "__main__":
    main()
