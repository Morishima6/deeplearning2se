"""Export a Hugging Face vulnerability dataset to JSONL files.

The default target is CodeXGLUE Defect Detection / Devign. The script keeps
the interface flexible because Hugging Face dataset identifiers may differ
between mirrors or local caches.
"""

from __future__ import annotations

import argparse
import csv
import json
import urllib.request
from collections import Counter
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable

from datasets import Dataset, DatasetDict, load_dataset

from paths import DATA_ROOT, HF_CACHE_DIR


CODE_COLUMNS = ("func", "code", "function", "source", "input", "text")
LABEL_COLUMNS = ("target", "label", "labels", "is_vulnerable", "vul")
FALLBACK_DATASETS = ("code_x_glue_cc_defect_detection",)
PARQUET_SPLITS = {
    "train": "train-00000-of-00001.parquet",
    "validation": "validation-00000-of-00001.parquet",
    "test": "test-00000-of-00001.parquet",
}
RAW_GITHUB_BASE_URL = (
    "https://raw.githubusercontent.com/madlag/CodeXGLUE/main/"
    "Code-Code/Defect-detection/dataset"
)
RAW_FILES = ("function.json", "train.txt", "valid.txt", "test.txt")
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
        "--fallback-dataset",
        action="append",
        default=[],
        help="Fallback Hugging Face dataset path. Can be passed multiple times.",
    )
    parser.add_argument(
        "--parquet-base-url",
        default=None,
        help="Fallback base URL for direct parquet files.",
    )
    parser.add_argument(
        "--raw-base-url",
        default=RAW_GITHUB_BASE_URL,
        help="Fallback base URL for CodeXGLUE raw function.json and split txt files.",
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


def default_parquet_base_url() -> str:
    import os

    endpoint = os.environ.get("HF_ENDPOINT", "https://huggingface.co").rstrip("/")
    return f"{endpoint}/datasets/google/code_x_glue_cc_defect_detection/resolve/main/data"


def load_dataset_from_parquet_urls(args: argparse.Namespace, load_kwargs: dict[str, Any]) -> DatasetDict:
    base_url = (args.parquet_base_url or default_parquet_base_url()).rstrip("/")
    data_files = {split: f"{base_url}/{filename}" for split, filename in PARQUET_SPLITS.items()}
    print(f"Loading dataset from parquet files under: {base_url}")
    dataset = load_dataset("parquet", data_files=data_files, **load_kwargs)
    if not isinstance(dataset, DatasetDict):
        raise TypeError(f"Expected a DatasetDict with train/valid/test splits, got {type(dataset)}")
    return dataset


def download_file(url: str, out_path: Path) -> None:
    if out_path.exists() and out_path.stat().st_size > 0:
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading: {url}")
    urllib.request.urlretrieve(url, out_path)


def load_index_file(path: Path) -> set[int]:
    indexes: set[int] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                indexes.add(int(line))
    return indexes


def load_dataset_from_raw_github(args: argparse.Namespace) -> DatasetDict:
    cache_root = Path(args.cache_dir or HF_CACHE_DIR) / "codexglue_defect_raw"
    base_url = args.raw_base_url.rstrip("/")
    for filename in RAW_FILES:
        download_file(f"{base_url}/{filename}", cache_root / filename)

    functions = json.loads((cache_root / "function.json").read_text(encoding="utf-8"))
    split_indexes = {
        "train": load_index_file(cache_root / "train.txt"),
        "valid": load_index_file(cache_root / "valid.txt"),
        "test": load_index_file(cache_root / "test.txt"),
    }

    split_rows: dict[str, list[dict[str, Any]]] = {split: [] for split in split_indexes}
    for idx, row in enumerate(functions):
        output = dict(row)
        output["idx"] = idx
        output.setdefault("id", idx)
        for split, indexes in split_indexes.items():
            if idx in indexes:
                split_rows[split].append(output)
                break

    print(f"Loaded dataset from raw GitHub files under: {base_url}")
    return DatasetDict({split: Dataset.from_list(rows) for split, rows in split_rows.items()})


def load_dataset_with_fallback(args: argparse.Namespace, load_kwargs: dict[str, Any]) -> DatasetDict:
    candidates = [args.dataset]
    for dataset_name in [*args.fallback_dataset, *FALLBACK_DATASETS]:
        if dataset_name not in candidates:
            candidates.append(dataset_name)

    errors: list[str] = []
    for dataset_name in candidates:
        try:
            if args.config:
                dataset = load_dataset(dataset_name, args.config, **load_kwargs)
            else:
                dataset = load_dataset(dataset_name, **load_kwargs)
            print(f"Loaded dataset: {dataset_name}")
            if not isinstance(dataset, DatasetDict):
                raise TypeError(f"Expected a DatasetDict with train/valid/test splits, got {type(dataset)}")
            return dataset
        except Exception as exc:
            errors.append(f"{dataset_name}: {exc.__class__.__name__}: {exc}")

    try:
        return load_dataset_from_parquet_urls(args, load_kwargs)
    except Exception as exc:
        errors.append(f"direct parquet: {exc.__class__.__name__}: {exc}")

    try:
        return load_dataset_from_raw_github(args)
    except Exception as exc:
        errors.append(f"raw github: {exc.__class__.__name__}: {exc}")

    joined_errors = "\n".join(errors)
    raise RuntimeError(f"Failed to load all dataset candidates:\n{joined_errors}")


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

    dataset = load_dataset_with_fallback(args, load_kwargs)

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
