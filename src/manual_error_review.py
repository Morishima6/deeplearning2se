"""Prepare a compact manual error review sheet from prediction errors."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

from io_utils import read_jsonl
from paths import DATA_ROOT, MODEL_ROOT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pred", default=f"{MODEL_ROOT}/outputs/run_losver_tag_seed42/test_predictions.csv")
    parser.add_argument("--data", default=f"{DATA_ROOT}/processed/devign_losver/test.jsonl")
    parser.add_argument("--out", default="reports/tables/manual_error_review.csv")
    parser.add_argument("--summary-out", default="reports/tables/manual_error_summary.csv")
    parser.add_argument("--per-type", type=int, default=10)
    return parser.parse_args()


def load_predictions(path: Path) -> dict[str, dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {str(row["id"]): row for row in csv.DictReader(handle)}


def guess_category(row: dict[str, Any], error_type: str) -> str:
    metrics = row.get("metrics", {})
    risk_lines = row.get("risk_lines", [])
    num_lines = int(metrics.get("num_lines") or 0)
    num_api = int(metrics.get("num_dangerous_api") or 0)
    max_score = float(metrics.get("max_risk_score") or 0.0)

    if num_lines >= 180:
        return "long_function_or_truncation"
    if error_type == "FP" and num_api >= 1:
        return "dangerous_api_false_alarm"
    if error_type == "FP" and max_score >= 4.0:
        return "high_static_risk_false_alarm"
    if error_type == "FN" and max_score < 2.0:
        return "weak_or_missing_line_signal"
    if error_type == "FN" and num_api == 0:
        return "semantic_or_context_dependent_vulnerability"
    if risk_lines and all("dangerous_api" not in item.get("reasons", []) for item in risk_lines):
        return "control_flow_or_pointer_signal_only"
    return "needs_manual_review"


def risk_summary(risk_lines: list[dict[str, Any]], limit: int = 5) -> str:
    return " | ".join(
        f"L{item['line_no']}:{item['score']}:{','.join(item.get('reasons', []))}:{item['text'][:100]}"
        for item in risk_lines[:limit]
    )


def main() -> None:
    args = parse_args()
    predictions = load_predictions(Path(args.pred))
    rows = read_jsonl(Path(args.data))

    candidates: list[dict[str, Any]] = []
    for row in rows:
        row_id = str(row.get("id"))
        pred = predictions.get(row_id)
        if pred is None:
            continue
        label = int(pred["label"])
        prediction = int(pred["prediction"])
        if label == prediction:
            continue

        error_type = "FN" if label == 1 else "FP"
        category = guess_category(row, error_type)
        metrics = row.get("metrics", {})
        candidates.append(
            {
                "id": row.get("id"),
                "error_type": error_type,
                "auto_category": category,
                "manual_category": "",
                "label": label,
                "prediction": prediction,
                "prob_vulnerable": pred.get("prob_vulnerable"),
                "num_lines": metrics.get("num_lines"),
                "num_dangerous_api": metrics.get("num_dangerous_api"),
                "max_risk_score": metrics.get("max_risk_score"),
                "risk_line_summary": risk_summary(row.get("risk_lines", [])),
                "manual_note": "",
                "code_excerpt": str(row.get("code", ""))[:1800],
            }
        )

    selected: list[dict[str, Any]] = []
    for error_type in ("FN", "FP"):
        typed = [item for item in candidates if item["error_type"] == error_type]
        typed = sorted(typed, key=lambda item: (item["auto_category"], str(item["id"])))
        selected.extend(typed[: args.per_type])

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(selected[0].keys()) if selected else ["id"])
        writer.writeheader()
        writer.writerows(selected)

    counts = Counter(item["auto_category"] for item in candidates)
    summary_path = Path(args.summary_out)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["auto_category", "count"])
        writer.writeheader()
        for category, count in counts.most_common():
            writer.writerow({"auto_category": category, "count": count})

    print(f"Manual review sheet written to: {out_path}")
    print(f"Auto category summary written to: {summary_path}")


if __name__ == "__main__":
    main()

