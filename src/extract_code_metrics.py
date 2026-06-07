"""Export code metrics from processed LOSVER-Light JSONL files."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from code_features import extract_metrics, rank_risk_lines
from io_utils import read_jsonl
from paths import DATA_ROOT


SPLITS = ("train", "valid", "test")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-dir", "--in", dest="in_dir", default=f"{DATA_ROOT}/processed/devign_losver")
    parser.add_argument("--out", default="reports/tables/code_metrics.csv")
    parser.add_argument("--top-k", "--top_k", dest="top_k", type=int, default=5)
    return parser.parse_args()


def get_metrics(row: dict[str, Any], top_k: int) -> dict[str, Any]:
    if "metrics" in row:
        return row["metrics"]
    code = str(row["code"])
    return extract_metrics(code, rank_risk_lines(code, top_k=top_k))


def main() -> None:
    args = parse_args()
    in_dir = Path(args.in_dir)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for split in SPLITS:
        for row in read_jsonl(in_dir / f"{split}.jsonl"):
            metrics = get_metrics(row, top_k=args.top_k)
            rows.append(
                {
                    "split": split,
                    "id": row.get("id"),
                    "label": int(row["label"]),
                    **metrics,
                }
            )

    if not rows:
        raise ValueError(f"No rows found under {in_dir}")

    fieldnames = list(rows[0].keys())
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Metrics exported to: {out_path}")


if __name__ == "__main__":
    main()
