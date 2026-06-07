"""Plot a compact F1/Accuracy bar chart from main_results.csv."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="reports/tables/main_results.csv")
    parser.add_argument("--out", default="reports/figures/main_results.png")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.results)
    if df.empty:
        raise ValueError(f"No rows in {args.results}")

    labels = df["run"].astype(str).tolist()
    x_pos = range(len(df))
    width = 0.36

    plt.figure(figsize=(max(8, len(df) * 1.6), 4.8))
    plt.bar([x - width / 2 for x in x_pos], df["accuracy"], width=width, label="Accuracy")
    plt.bar([x + width / 2 for x in x_pos], df["f1"], width=width, label="F1")
    plt.xticks(list(x_pos), labels, rotation=20, ha="right")
    plt.ylim(0, 1)
    plt.ylabel("Score")
    plt.legend()
    plt.tight_layout()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=200)
    print(f"Figure written to: {out_path}")


if __name__ == "__main__":
    main()

