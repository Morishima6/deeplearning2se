"""Export a Hugging Face vulnerability dataset to JSONL files.

The default target is CodeXGLUE Defect Detection / Devign. The script keeps
the interface flexible because Hugging Face dataset identifiers may differ
between mirrors or local caches.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable

from datasets import Dataset, DatasetDict, load_dataset

from paths import DATA_ROOT, HF_CACHE_DIR


CODE_COLUMNS = ("func", "code", "function", "source", "input", "text")
LABEL_COLUMNS = ("target", "label", "labels", "is_vulnerable", "vul")
SPLIT_ALIASES = {
    "train": ("train",),
    "valid": ("validation", "valid", "dev"),
    "test": ("test",),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        default="google/code_x_glue_cc_defect_detection",
        help="Hugging Face dataset path.",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Optional Hugging Face dataset config name.",
    )
    parser.add_argument(
        "--out",
        default=f"{DATA_ROOT}/raw/devign_hf",
        help="Output directory for JSONL splits and stats.",
    )
    parser.add_argument(
        "--cache-dir",
        default=HF_CACHE_DIR,
        help="Hugging Face dataset cache directory. Keep it outside the project/root.",
    )
    parser.add_argument(
        "--stats-out",
        default="reports/tables",
        help="Directory that receives a copy of dataset_stats.csv/json for reports.",
    )
    parser.add_argument(
        "--code-column",
        default=None,
        help="Code/function column name. Auto-detected if omitted.",
    )
    parser.add_argument(
        "--label-column",
        default=None,
        help="Binary label column name. Auto-detected if omitted.",
    )
    parser.add_argument(
        "--trust-remote-code",
        action="store_true",
        help="Pass trust_remote_code=True to datasets.load_dataset.",
    )
    return parser.parse_args()


def detect_column(columns: Iterable[str], candidates: tuple[str, ...], kind: str) -> str:
    columns = list(columns)
    for candidate in candidates:
        if candidate in columns:
            return candidate
    raise ValueError(f"Could not detect {kind} column from columns: {columns}")


def normalize_split_name(dataset: DatasetDict, target: str) -> str:
    available = set(dataset.keys())
    for alias in SPLIT_ALIASES[target]:
        if alias in available:
            return alias
    raise ValueError(f"Could not find split for {target}. Available splits: {sorted(available)}")


def normalize_label(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "vulnerable", "unsafe"}:
            return 1
        if lowered in {"0", "false", "no", "benign", "safe"}:
            return 0
    raise ValueError(f"Unsupported label value: {value!r}")


def write_jsonl(split: Dataset, out_path: Path, code_column: str, label_column: str) -> dict[str, Any]:
    label_counts: Counter[int] = Counter()
    line_counts: list[int] = []
    char_counts: list[int] = []

    with out_path.open("w", encoding="utf-8", newline="\n") as handle:
        for idx, row in enumerate(split):
            code = str(row[code_column])
            label = normalize_label(row[label_column])
            line_count = len(code.splitlines())
            char_count = len(code)

            output = {
                "id": row.get("id", idx),
                "code": code,
                "label": label,
            }
            for optional_key in ("project", "commit_id", "cwe", "cve", "file_name"):
                if optional_key in row:
                    output[optional_key] = row[optional_key]

            handle.write(json.dumps(output, ensure_ascii=False) + "\n")
            label_counts[label] += 1
            line_counts.append(line_count)
            char_counts.append(char_count)

    return {
        "num_samples": sum(label_counts.values()),
        "num_safe": label_counts.get(0, 0),
        "num_vulnerable": label_counts.get(1, 0),
        "avg_lines": round(mean(line_counts), 2) if line_counts else 0,
        "median_lines": round(median(line_counts), 2) if line_counts else 0,
        "avg_chars": round(mean(char_counts), 2) if char_counts else 0,
        "median_chars": round(median(char_counts), 2) if char_counts else 0,
    }


def write_stats(stats: dict[str, dict[str, Any]], out_dir: Path, stats_out_dir: Path | None) -> None:
    csv_path = out_dir / "dataset_stats.csv"
    fieldnames = [
        "split",
        "num_samples",
        "num_safe",
        "num_vulnerable",
        "avg_lines",
        "median_lines",
        "avg_chars",
        "median_chars",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for split_name, values in stats.items():
            writer.writerow({"split": split_name, **values})

    json_path = out_dir / "dataset_stats.json"
    json_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")

    if stats_out_dir is not None:
        stats_out_dir.mkdir(parents=True, exist_ok=True)
        report_csv = stats_out_dir / "dataset_stats.csv"
        report_json = stats_out_dir / "dataset_stats.json"
        report_csv.write_text(csv_path.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
        report_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    load_kwargs: dict[str, Any] = {}
    if args.cache_dir:
        load_kwargs["cache_dir"] = args.cache_dir
    if args.trust_remote_code:
        load_kwargs["trust_remote_code"] = True

    if args.config:
        dataset = load_dataset(args.dataset, args.config, **load_kwargs)
    else:
        dataset = load_dataset(args.dataset, **load_kwargs)

    if not isinstance(dataset, DatasetDict):
        raise TypeError(f"Expected a DatasetDict with train/valid/test splits, got {type(dataset)}")

    train_split_name = normalize_split_name(dataset, "train")
    first_split = dataset[train_split_name]
    code_column = args.code_column or detect_column(first_split.column_names, CODE_COLUMNS, "code")
    label_column = args.label_column or detect_column(first_split.column_names, LABEL_COLUMNS, "label")

    stats: dict[str, dict[str, Any]] = {}
    for target_split in ("train", "valid", "test"):
        source_split = normalize_split_name(dataset, target_split)
        out_path = out_dir / f"{target_split}.jsonl"
        stats[target_split] = write_jsonl(dataset[source_split], out_path, code_column, label_column)

    stats_out_dir = Path(args.stats_out) if args.stats_out else None
    write_stats(stats, out_dir, stats_out_dir)
    print(f"Dataset exported to: {out_dir}")
    print(f"Code column: {code_column}")
    print(f"Label column: {label_column}")
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
