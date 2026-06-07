"""Train a Logistic Regression baseline on LOSVER-Light code metrics."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from io_utils import read_jsonl


DEFAULT_FEATURES = (
    "num_lines",
    "num_nonempty_lines",
    "num_chars",
    "num_tokens",
    "num_unique_tokens",
    "avg_line_length",
    "max_line_length",
    "num_dangerous_api",
    "num_branch_loop",
    "num_pointer_array",
    "num_error_handling",
    "symbol_density",
    "num_risk_lines",
    "max_risk_score",
    "avg_risk_score",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", default="data/processed/devign_losver/train.jsonl")
    parser.add_argument("--valid", default="data/processed/devign_losver/valid.jsonl")
    parser.add_argument("--test", default="data/processed/devign_losver/test.jsonl")
    parser.add_argument("--out-dir", default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-iter", type=int, default=1000)
    return parser.parse_args()


def load_xy(path: Path) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]]]:
    rows = read_jsonl(path)
    if not rows:
        raise ValueError(f"No rows found in {path}")

    x_values: list[list[float]] = []
    y_values: list[int] = []
    for row in rows:
        metrics = row["metrics"]
        x_values.append([float(metrics[name]) for name in DEFAULT_FEATURES])
        y_values.append(int(row["label"]))
    return np.asarray(x_values, dtype=np.float32), np.asarray(y_values, dtype=np.int64), rows


def find_best_threshold(y_true: np.ndarray, y_score: np.ndarray) -> tuple[float, float]:
    thresholds = np.linspace(0.05, 0.95, 181)
    best_threshold = 0.5
    best_f1 = -1.0
    for threshold in thresholds:
        y_pred = (y_score >= threshold).astype(int)
        current_f1 = f1_score(y_true, y_pred, zero_division=0)
        if current_f1 > best_f1:
            best_f1 = current_f1
            best_threshold = float(threshold)
    return best_threshold, float(best_f1)


def compute_metrics(y_true: np.ndarray, y_score: np.ndarray, threshold: float) -> dict[str, Any]:
    y_pred = (y_score >= threshold).astype(int)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = [int(value) for value in cm.ravel()]

    result = {
        "threshold": round(threshold, 4),
        "accuracy": round(accuracy_score(y_true, y_pred), 6),
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 6),
        "recall": round(recall_score(y_true, y_pred, zero_division=0), 6),
        "f1": round(f1_score(y_true, y_pred, zero_division=0), 6),
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
    }

    if len(np.unique(y_true)) == 2:
        result["roc_auc"] = round(roc_auc_score(y_true, y_score), 6)
        result["pr_auc"] = round(average_precision_score(y_true, y_score), 6)
    else:
        result["roc_auc"] = None
        result["pr_auc"] = None
    return result


def write_predictions(rows: list[dict[str, Any]], y_score: np.ndarray, threshold: float, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["id", "label", "prob_vulnerable", "prediction", "num_lines", "num_dangerous_api", "max_risk_score"],
        )
        writer.writeheader()
        for row, score in zip(rows, y_score):
            metrics = row["metrics"]
            writer.writerow(
                {
                    "id": row.get("id"),
                    "label": int(row["label"]),
                    "prob_vulnerable": round(float(score), 8),
                    "prediction": int(score >= threshold),
                    "num_lines": metrics["num_lines"],
                    "num_dangerous_api": metrics["num_dangerous_api"],
                    "max_risk_score": metrics["max_risk_score"],
                }
            )


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir or f"outputs/run_metrics_seed{args.seed}")
    out_dir.mkdir(parents=True, exist_ok=True)

    x_train, y_train, _ = load_xy(Path(args.train))
    x_valid, y_valid, valid_rows = load_xy(Path(args.valid))
    x_test, y_test, test_rows = load_xy(Path(args.test))

    model = Pipeline(
        steps=[
            ("scale", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=args.max_iter,
                    random_state=args.seed,
                    solver="liblinear",
                ),
            ),
        ]
    )
    model.fit(x_train, y_train)

    valid_scores = model.predict_proba(x_valid)[:, 1]
    threshold, valid_best_f1 = find_best_threshold(y_valid, valid_scores)
    test_scores = model.predict_proba(x_test)[:, 1]

    metrics = {
        "model": "LogisticRegression",
        "seed": args.seed,
        "features": list(DEFAULT_FEATURES),
        "valid_best_f1": round(valid_best_f1, 6),
        "valid": compute_metrics(y_valid, valid_scores, threshold),
        "test": compute_metrics(y_test, test_scores, threshold),
    }

    (out_dir / "eval.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    write_predictions(valid_rows, valid_scores, threshold, out_dir / "valid_predictions.csv")
    write_predictions(test_rows, test_scores, threshold, out_dir / "test_predictions.csv")

    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"Outputs written to: {out_dir}")


if __name__ == "__main__":
    main()

