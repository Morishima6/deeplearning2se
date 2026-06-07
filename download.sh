#!/usr/bin/env bash
set -euo pipefail

export DLSE_DATA_ROOT=/mnt/sda/gzx/data/deeplearning2se
export DLSE_MODEL_ROOT=/mnt/sda/gzx/models/deeplearning2se
export HF_HOME=/mnt/sda/gzx/models/huggingface
export HF_DATASETS_CACHE=/mnt/sda/gzx/models/huggingface/datasets
export TRANSFORMERS_CACHE=/mnt/sda/gzx/models/huggingface/transformers
export HF_ENDPOINT=${HF_ENDPOINT:-https://hf-mirror.com}

mkdir -p "$DLSE_DATA_ROOT" "$DLSE_MODEL_ROOT" "$HF_HOME" "$HF_DATASETS_CACHE" "$TRANSFORMERS_CACHE"

# python src/export_hf_dataset.py \
#     --dataset google/code_x_glue_cc_defect_detection \
#     --fallback-dataset code_x_glue_cc_defect_detection \
#     --out "$DLSE_DATA_ROOT/raw/devign_hf" \
#     --cache-dir "$HF_DATASETS_CACHE" \
#     --stats-out reports/tables

# python src/build_line_signals.py \
#     --in "$DLSE_DATA_ROOT/raw/devign_hf" \
#     --out "$DLSE_DATA_ROOT/processed/devign_losver" \
#     --top_k 5 \
#     --stats-out reports/tables

# python src/extract_code_metrics.py \
#     --in "$DLSE_DATA_ROOT/processed/devign_losver" \
#     --out reports/tables/code_metrics.csv

python src/train_metrics_baseline.py \
    --train "$DLSE_DATA_ROOT/processed/devign_losver/train.jsonl" \
    --valid "$DLSE_DATA_ROOT/processed/devign_losver/valid.jsonl" \
    --test "$DLSE_DATA_ROOT/processed/devign_losver/test.jsonl" \
    --out-dir "$DLSE_MODEL_ROOT/outputs/run_metrics_seed42" \
    --seed 42
