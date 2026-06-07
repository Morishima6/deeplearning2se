"""Collect eval.json files from experiment runs into one CSV table."""

from __future__ import annotations

import argparse
import csv
import glob
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", nargs="+", required=True)
    parser.add_argument("--out", default="reports/tables/main_results.csv")
    return parser.parse_args()


def load_eval(run_dir: Path) -> dict[str, Any] | None:
    eval_path = run_dir / "eval.json"
    if not eval_path.exists():
        return None
    return json.loads(eval_path.read_text(encoding="utf-8"))


def main() -> None:
    args = parse_args()
    run_dirs: list[Path] = []
    for pattern in args.runs:
        matches = [Path(path) for path in glob.glob(pattern)]
        run_dirs.extend(matches if matches else [Path(pattern)])

    rows: list[dict[str, Any]] = []
    for run_dir in sorted(set(run_dirs)):
        result = load_eval(run_dir)
        if result is None:
            continue
        test = result["test"]
        rows.append(
            {
                "run": run_dir.name,
                "model": result.get("model"),
                "text_field": result.get("text_field", "metrics"),
                "seed": result.get("seed"),
                "threshold": test.get("threshold"),
                "accuracy": test.get("accuracy"),
                "precision": test.get("precision"),
                "recall": test.get("recall"),
                "f1": test.get("f1"),
                "roc_auc": test.get("roc_auc"),
                "pr_auc": test.get("pr_auc"),
                "tn": test.get("tn"),
                "fp": test.get("fp"),
                "fn": test.get("fn"),
                "tp": test.get("tp"),
            }
        )

    if not rows:
        raise ValueError("No eval.json files found from --runs")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Collected {len(rows)} runs into: {out_path}")


if __name__ == "__main__":
    main()

