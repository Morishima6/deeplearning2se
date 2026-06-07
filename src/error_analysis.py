"""Export false positives and false negatives for manual inspection."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from io_utils import read_jsonl
from paths import DATA_ROOT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pred", required=True)
    parser.add_argument("--data", default=f"{DATA_ROOT}/processed/devign_losver/test.jsonl")
    parser.add_argument("--out", default="reports/tables/error_cases.csv")
    parser.add_argument("--limit", type=int, default=40)
    return parser.parse_args()


def load_predictions(path: Path) -> dict[str, dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {str(row["id"]): row for row in csv.DictReader(handle)}


def main() -> None:
    args = parse_args()
    predictions = load_predictions(Path(args.pred))
    rows = read_jsonl(Path(args.data))

    cases: list[dict[str, Any]] = []
    for row in rows:
        row_id = str(row.get("id"))
        if row_id not in predictions:
            continue
        pred = predictions[row_id]
        label = int(pred["label"])
        prediction = int(pred["prediction"])
        if label == prediction:
            continue
        error_type = "FN" if label == 1 and prediction == 0 else "FP"
        risk_lines = row.get("risk_lines", [])
        cases.append(
            {
                "id": row.get("id"),
                "error_type": error_type,
                "label": label,
                "prediction": prediction,
                "prob_vulnerable": pred.get("prob_vulnerable"),
                "num_lines": row.get("metrics", {}).get("num_lines"),
                "num_dangerous_api": row.get("metrics", {}).get("num_dangerous_api"),
                "max_risk_score": row.get("metrics", {}).get("max_risk_score"),
                "risk_line_summary": " | ".join(
                    f"L{item['line_no']}:{item['score']}:{item['text'][:120]}" for item in risk_lines[:5]
                ),
                "code_excerpt": str(row.get("code", ""))[:1200],
            }
        )

    cases = sorted(cases, key=lambda item: (item["error_type"], str(item["id"])))[: args.limit]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(cases[0].keys()) if cases else ["id"])
        writer.writeheader()
        writer.writerows(cases)

    print(f"Exported {len(cases)} error cases to: {out_path}")


if __name__ == "__main__":
    main()
