"""Generate polished report figures from experiment CSV files."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


RUN_LABELS = {
    "run_metrics_seed42": "Metrics\nBaseline",
    "run_vanilla_seed42": "Vanilla\nQwen",
    "run_losver_tag_seed42": "LOSVER-Light\nTag",
    "run_losver_prefix_seed42": "LOSVER-Light\nTag+Prefix",
}

RUN_ORDER = [
    "run_metrics_seed42",
    "run_vanilla_seed42",
    "run_losver_tag_seed42",
    "run_losver_prefix_seed42",
]

METRIC_LABELS = {
    "f1": "F1",
    "roc_auc": "ROC-AUC",
    "pr_auc": "PR-AUC",
    "precision": "Precision",
    "recall": "Recall",
}

ERROR_LABELS = {
    "error_or_resource_management_false_alarm": "Error/resource\nfalse alarm",
    "long_function_or_truncation": "Long function\nor truncation",
    "control_flow_or_pointer_false_alarm": "Control-flow /\npointer false alarm",
    "io_or_parser_false_alarm": "I/O or parser\nfalse alarm",
    "semantic_or_context_dependent_vulnerability": "Context-dependent\nvulnerability",
    "weak_or_misleading_line_signal": "Weak/misleading\nline signal",
    "benign_wrapper_or_accessor": "Benign wrapper\nor accessor",
    "dangerous_api_missed_in_long_function": "Dangerous API\nmissed in long function",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--main-results", default="reports/tables/main_results.csv")
    parser.add_argument("--ablation-results", default="reports/tables/ablation_results.csv")
    parser.add_argument("--error-summary", default="reports/tables/manual_error_summary.csv")
    parser.add_argument("--out-dir", default="report_latex/imgs/final")
    parser.add_argument("--dpi", type=int, default=320)
    return parser.parse_args()


def configure_style() -> None:
    sns.set_theme(style="whitegrid", context="paper")
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#2f3a45",
            "axes.labelcolor": "#1f2933",
            "xtick.color": "#1f2933",
            "ytick.color": "#1f2933",
            "text.color": "#1f2933",
            "axes.titleweight": "bold",
            "font.family": "DejaVu Sans",
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.12,
        }
    )


def save_fig(path: Path, dpi: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=dpi)
    plt.close()
    print(f"Figure written to: {path}")


def annotate_bars(ax: plt.Axes, fmt: str = "{:.3f}", fontsize: int = 8) -> None:
    for container in ax.containers:
        ax.bar_label(container, fmt=fmt, padding=2, fontsize=fontsize, color="#27313d")


def plot_main_results(csv_path: Path, out_path: Path, dpi: int) -> None:
    df = pd.read_csv(csv_path)
    df["method"] = df["run"].map(RUN_LABELS).fillna(df["run"])
    order = [RUN_LABELS[item] for item in RUN_ORDER if item in set(df["run"])]
    metrics = ["f1", "roc_auc", "pr_auc"]

    long_df = df.melt(
        id_vars=["run", "method"],
        value_vars=metrics,
        var_name="metric",
        value_name="score",
    )
    long_df["metric"] = long_df["metric"].map(METRIC_LABELS)

    palette = {
        "F1": "#4C78A8",
        "ROC-AUC": "#59A14F",
        "PR-AUC": "#F28E2B",
    }

    plt.figure(figsize=(8.4, 4.9))
    ax = sns.barplot(
        data=long_df,
        x="method",
        y="score",
        hue="metric",
        order=order,
        palette=palette,
        edgecolor="#2f3a45",
        linewidth=0.7,
    )

    if "LOSVER-Light\nTag" in order:
        tag_idx = order.index("LOSVER-Light\nTag")
        ax.axvspan(tag_idx - 0.48, tag_idx + 0.48, color="#F7DC6F", alpha=0.15, zorder=0)
        ax.text(
            tag_idx,
            0.807,
            "best overall",
            ha="center",
            va="top",
            fontsize=8,
            color="#8A5A00",
            fontweight="bold",
            clip_on=True,
        )

    annotate_bars(ax, fontsize=7)
    ax.set_title("Main Test Results")
    ax.set_xlabel("")
    ax.set_ylabel("Score")
    ax.set_ylim(0.45, 0.82)
    ax.legend(title="", ncol=3, loc="upper left", frameon=True, framealpha=0.94)
    ax.grid(axis="y", color="#d9dee7", linewidth=0.7)
    ax.grid(axis="x", visible=False)
    sns.despine(ax=ax, left=False, bottom=False)
    plt.tight_layout()
    save_fig(out_path, dpi)


def parse_top_k(run: str) -> int:
    match = re.search(r"topk(\d+)", run)
    if match:
        return int(match.group(1))
    return 5


def plot_topk_ablation(csv_path: Path, out_path: Path, dpi: int) -> None:
    df = pd.read_csv(csv_path)
    df["top_k"] = df["run"].map(parse_top_k)
    df = df.sort_values("top_k")
    metrics = ["precision", "recall", "f1"]
    long_df = df.melt(
        id_vars=["top_k"],
        value_vars=metrics,
        var_name="metric",
        value_name="score",
    )
    long_df["metric"] = long_df["metric"].map(METRIC_LABELS)

    palette = {
        "Precision": "#B07AA1",
        "Recall": "#E15759",
        "F1": "#4C78A8",
    }

    plt.figure(figsize=(7.2, 4.7))
    ax = sns.lineplot(
        data=long_df,
        x="top_k",
        y="score",
        hue="metric",
        style="metric",
        markers=True,
        dashes=False,
        linewidth=2.4,
        markersize=8,
        palette=palette,
    )

    ax.axvline(5, color="#F2C94C", linewidth=8, alpha=0.18, zorder=0)
    best_f1 = df.loc[df["f1"].idxmax()]
    ax.scatter([best_f1["top_k"]], [best_f1["f1"]], s=120, color="#1F4E79", zorder=5)
    ax.annotate(
        "best F1",
        xy=(best_f1["top_k"], best_f1["f1"]),
        xytext=(best_f1["top_k"] + 0.25, best_f1["f1"] + 0.012),
        arrowprops={"arrowstyle": "->", "color": "#1F4E79", "lw": 1.0},
        fontsize=8,
        color="#1F4E79",
        fontweight="bold",
    )

    for _, row in long_df.iterrows():
        ax.text(
            row["top_k"],
            row["score"] + 0.006,
            f"{row['score']:.3f}",
            ha="center",
            va="bottom",
            fontsize=7,
            color="#27313d",
        )

    ax.set_title("Top-k Ablation for LOSVER-Light Tag")
    ax.set_xlabel("Number of marked risky lines (top-k)")
    ax.set_ylabel("Score")
    ax.set_xticks([3, 5, 8])
    ax.set_ylim(0.54, 0.89)
    ax.legend(title="", loc="lower right", frameon=True, framealpha=0.92)
    ax.grid(axis="y", color="#d9dee7", linewidth=0.7)
    ax.grid(axis="x", visible=False)
    sns.despine(ax=ax, left=False, bottom=False)
    plt.tight_layout()
    save_fig(out_path, dpi)


def plot_error_summary(csv_path: Path, out_path: Path, dpi: int) -> None:
    df = pd.read_csv(csv_path)
    df["label"] = df["manual_category"].map(ERROR_LABELS).fillna(df["manual_category"])
    df = df.sort_values(["count", "label"], ascending=[True, True])

    false_positive_categories = {
        "error_or_resource_management_false_alarm",
        "control_flow_or_pointer_false_alarm",
        "io_or_parser_false_alarm",
        "benign_wrapper_or_accessor",
    }
    colors = [
        "#D95F02" if category in false_positive_categories else "#4C78A8"
        for category in df["manual_category"]
    ]

    plt.figure(figsize=(8.2, 5.2))
    ax = plt.gca()
    bars = ax.barh(df["label"], df["count"], color=colors, edgecolor="#2f3a45", linewidth=0.6)
    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 0.08,
            bar.get_y() + bar.get_height() / 2,
            f"{int(width)}",
            va="center",
            ha="left",
            fontsize=8,
            color="#27313d",
            fontweight="bold",
        )

    ax.set_title("Manual Error Analysis Categories")
    ax.set_xlabel("Number of reviewed cases")
    ax.set_ylabel("")
    ax.set_xlim(0, max(df["count"]) + 0.9)
    ax.grid(axis="x", color="#d9dee7", linewidth=0.7)
    ax.grid(axis="y", visible=False)

    from matplotlib.patches import Patch

    legend_items = [
        Patch(facecolor="#D95F02", edgecolor="#2f3a45", label="Mostly false positives"),
        Patch(facecolor="#4C78A8", edgecolor="#2f3a45", label="Mostly false negatives / weak signals"),
    ]
    ax.legend(handles=legend_items, loc="lower right", frameon=True, framealpha=0.92)
    sns.despine(ax=ax, left=False, bottom=False)
    plt.tight_layout()
    save_fig(out_path, dpi)


def main() -> None:
    args = parse_args()
    configure_style()

    out_dir = Path(args.out_dir)
    plot_main_results(Path(args.main_results), out_dir / "main_results.png", args.dpi)
    plot_topk_ablation(Path(args.ablation_results), out_dir / "topk_ablation.png", args.dpi)
    plot_error_summary(Path(args.error_summary), out_dir / "error_analysis.png", args.dpi)


if __name__ == "__main__":
    main()
