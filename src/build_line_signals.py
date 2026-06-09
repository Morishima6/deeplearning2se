"""Build LOSVER-Light line-risk signals for JSONL vulnerability data."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import mean, median
from typing import Any

from code_features import add_mod_tags, build_prefix, extract_metrics, rank_risk_lines
from io_utils import read_jsonl, write_jsonl
from paths import DATA_ROOT


SPLITS = ("train", "valid", "test")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-dir", "--in", dest="in_dir", default=f"{DATA_ROOT}/raw/devign_hf")
    parser.add_argument("--out-dir", "--out", dest="out_dir", default=f"{DATA_ROOT}/processed/devign_losver")
    parser.add_argument("--top-k", "--top_k", dest="top_k", type=int, default=5)
    parser.add_argument("--stats-out", default="reports/tables")
    parser.add_argument("--stats-name", default="line_signal_stats")
    return parser.parse_args()


def process_row(row: dict[str, Any], top_k: int) -> dict[str, Any]:
    code = str(row["code"])
    risk_lines = rank_risk_lines(code, top_k=top_k)
    text_tag = add_mod_tags(code, risk_lines)
    output = dict(row)
    output["label"] = int(row["label"])
    output["risk_lines"] = risk_lines
    output["text_vanilla"] = code
    output["text_tag"] = text_tag
    output["text_tag_prefix"] = build_prefix(text_tag, risk_lines)
    output["metrics"] = extract_metrics(code, risk_lines)
    return output


def summarize_split(rows: list[dict[str, Any]]) -> dict[str, Any]:
    label_counts = Counter(int(row["label"]) for row in rows)
    risk_line_counts = [len(row["risk_lines"]) for row in rows]
    max_risk_scores = [row["metrics"]["max_risk_score"] for row in rows]
    vanilla_lengths = [len(row["text_vanilla"]) for row in rows]
    tag_lengths = [len(row["text_tag"]) for row in rows]
    prefix_lengths = [len(row["text_tag_prefix"]) for row in rows]

    return {
        "num_samples": len(rows),
        "num_safe": label_counts.get(0, 0),
        "num_vulnerable": label_counts.get(1, 0),
        "avg_risk_lines": round(mean(risk_line_counts), 3) if rows else 0.0,
        "median_risk_lines": round(median(risk_line_counts), 3) if rows else 0.0,
        "avg_max_risk_score": round(mean(max_risk_scores), 3) if rows else 0.0,
        "avg_vanilla_chars": round(mean(vanilla_lengths), 2) if rows else 0.0,
        "avg_tag_chars": round(mean(tag_lengths), 2) if rows else 0.0,
        "avg_tag_prefix_chars": round(mean(prefix_lengths), 2) if rows else 0.0,
    }


def write_stats(stats: dict[str, dict[str, Any]], out_dir: Path, stats_out: Path | None, stats_name: str) -> None:
    fieldnames = [
        "split",
        "num_samples",
        "num_safe",
        "num_vulnerable",
        "avg_risk_lines",
        "median_risk_lines",
        "avg_max_risk_score",
        "avg_vanilla_chars",
        "avg_tag_chars",
        "avg_tag_prefix_chars",
    ]
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"{stats_name}.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for split, values in stats.items():
            writer.writerow({"split": split, **values})

    json_path = out_dir / f"{stats_name}.json"
    json_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")

    if stats_out is not None:
        stats_out.mkdir(parents=True, exist_ok=True)
        (stats_out / f"{stats_name}.csv").write_text(
            csv_path.read_text(encoding="utf-8"), encoding="utf-8", newline="\n"
        )
        (stats_out / f"{stats_name}.json").write_text(
            json_path.read_text(encoding="utf-8"), encoding="utf-8"
        )


def main() -> None:
    args = parse_args()
    in_dir = Path(args.in_dir)
    out_dir = Path(args.out_dir)
    stats: dict[str, dict[str, Any]] = {}

    for split in SPLITS:
        rows = read_jsonl(in_dir / f"{split}.jsonl")
        processed = [process_row(row, top_k=args.top_k) for row in rows]
        write_jsonl(processed, out_dir / f"{split}.jsonl")
        stats[split] = summarize_split(processed)

    stats_out = Path(args.stats_out) if args.stats_out else None
    write_stats(stats, out_dir, stats_out, args.stats_name)
    print(f"Processed data written to: {out_dir}")
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
