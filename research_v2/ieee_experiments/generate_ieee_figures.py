"""Generate grayscale-safe vector IEEE-upgrade figures from committed CSV results."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib-cache"))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUT = ROOT / "paper" / "figures" / "ieee_upgrade"
RESULTS = ROOT / "ieee_results"
HATCHES = ["", "//", "xx", "..", "\\\\"]
COLORS = ["#f2f2f2", "#bdbdbd", "#737373", "#252525", "#ffffff"]


def save(fig: plt.Figure, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(); fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight"); fig.savefig(OUT / f"{name}.png", dpi=300, bbox_inches="tight"); plt.close(fig)


def robustness() -> None:
    frame = pd.read_csv(RESULTS / "multiseed_summary.csv")
    fig, ax = plt.subplots(figsize=(3.45, 2.35))
    x = np.arange(len(frame)); ax.bar(x, frame["MAE mean"], yerr=frame["MAE std"], color="#737373", edgecolor="black", capsize=3, hatch="//")
    ax.set_xticks(x, [v.replace("_", "\n") for v in frame.Dataset]); ax.set_ylabel("MAE (native unit)")
    ax.set_title("Bi-LSTM initialization robustness"); ax.grid(axis="y", alpha=.25)
    save(fig, "multiseed_robustness")


def ablations() -> None:
    architecture = pd.read_csv(RESULTS / "architecture_ablation.csv")
    features = pd.read_csv(RESULTS / "feature_ablation.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.55))
    for ax, frame, label_col, title in [(axes[0], architecture, "Model", "Architecture ablation (seed 42)"),
                                        (axes[1], features, "Feature configuration", "Feature ablation")]:
        labels = list(dict.fromkeys(frame[label_col])); datasets = list(dict.fromkeys(frame.Dataset)); width = .8 / len(labels); x = np.arange(len(datasets))
        for j, label in enumerate(labels):
            subset = frame[frame[label_col].eq(label)].set_index("Dataset").reindex(datasets)
            ax.bar(x + (j - (len(labels)-1)/2)*width, subset.MAE, width, label=label, color=COLORS[j], edgecolor="black", hatch=HATCHES[j])
        ax.set_xticks(x, [v.replace("_", "\n") for v in datasets]); ax.set_ylabel("MAE (native unit)"); ax.set_title(title); ax.grid(axis="y", alpha=.25); ax.legend(fontsize=6)
    save(fig, "architecture_feature_ablation")


def threshold_events() -> None:
    frame = pd.read_csv(RESULTS / "threshold_event_metrics.csv")
    fig, axes = plt.subplots(1, 3, figsize=(7.1, 2.25), sharey=True)
    for ax, (dataset, group) in zip(axes, frame.groupby("Dataset", sort=False)):
        x = np.arange(len(group)); ax.bar(x, group.F1, color=COLORS[:len(group)], edgecolor="black")
        for bar, hatch in zip(ax.patches, HATCHES): bar.set_hatch(hatch)
        ax.set_xticks(x, [m.replace(" (previous 24 h)", "").replace(" ", "\n") for m in group.Model], fontsize=6)
        ax.set_title(dataset.replace("_", " "), fontsize=8); ax.grid(axis="y", alpha=.25)
    axes[0].set_ylabel("Event F1"); fig.suptitle("Training-derived proxy threshold events", y=1.02, fontsize=10)
    save(fig, "threshold_event_evaluation")


def cmapss() -> None:
    metrics = pd.read_csv(RESULTS / "cmapss_fd001_metrics.csv")
    horizon = pd.read_csv(RESULTS / "cmapss_fd001_horizon_metrics.csv")
    targets = [t for t in metrics["Target sensor"].dropna().unique() if t != "MACRO_AVERAGE_NORMALIZED"]
    fig, axes = plt.subplots(2, 2, figsize=(7.1, 4.4)); axes = axes.ravel()
    for ax, target in zip(axes, targets):
        group = metrics[(metrics.Configuration.eq("C1")) & (metrics["Target sensor"].eq(target))]
        group = group[(group.Model.ne("Bi-LSTM")) | (group.Seed.eq(42))]
        x = np.arange(len(group)); ax.bar(x, group.MAE, color=COLORS[:len(group)], edgecolor="black")
        for bar, hatch in zip(ax.patches, HATCHES): bar.set_hatch(hatch)
        ax.set_xticks(x, group.Model, rotation=30, ha="right", fontsize=6); ax.set_title(target); ax.set_ylabel("MAE (sensor unit)"); ax.grid(axis="y", alpha=.25)
    save(fig, "cmapss_external_validation")
    fig, ax = plt.subplots(figsize=(3.45, 2.35))
    group = horizon[(horizon.Configuration.eq("C1")) & (horizon["Target sensor"].eq(targets[0]))]
    group = group[(group.Model.ne("Bi-LSTM")) | (group.Seed.eq(42))]
    for j, (model, series) in enumerate(group.groupby("Model", sort=False)):
        ax.plot(series["Horizon cycle"], series.MAE, marker="o", markersize=2, color=COLORS[j+1], linestyle=["-", "--", ":"][j], label=model)
    ax.set_xlabel("Forecast horizon (cycles)"); ax.set_ylabel("MAE (sensor unit)"); ax.set_title(f"FD001 horizon error: {targets[0]}"); ax.grid(alpha=.25); ax.legend(fontsize=6)
    save(fig, "cmapss_horizon_mae")


def stage() -> None:
    frame = pd.read_csv(RESULTS / "cmapss_stage_metrics.csv")
    targets = list(dict.fromkeys(frame["Target sensor"])); fig, axes = plt.subplots(2, 2, figsize=(7.1, 4.4)); axes = axes.ravel()
    for ax, target in zip(axes, targets):
        group = frame[(frame["Target sensor"].eq(target)) & ((frame.Model != "Bi-LSTM") | (frame.Seed == 42))]
        pivot = group.pivot_table(index="Stage", columns="Model", values="MAE", aggfunc="mean")
        x = np.arange(len(pivot)); width = .8 / len(pivot.columns)
        for j, model in enumerate(pivot.columns): ax.bar(x + (j-(len(pivot.columns)-1)/2)*width, pivot[model], width, label=model, color=COLORS[j], edgecolor="black", hatch=HATCHES[j])
        ax.set_xticks(x, [s.split(" ")[0] for s in pivot.index]); ax.set_title(target); ax.set_ylabel("MAE (sensor unit)"); ax.grid(axis="y", alpha=.25)
    axes[0].legend(fontsize=6); save(fig, "cmapss_stage_error")


def main() -> None:
    plt.rcParams.update({"font.size": 8, "pdf.fonttype": 42, "ps.fonttype": 42})
    robustness(); ablations(); threshold_events(); cmapss(); stage()
    print(f"Saved IEEE-upgrade figures to {OUT}")


if __name__ == "__main__":
    main()
