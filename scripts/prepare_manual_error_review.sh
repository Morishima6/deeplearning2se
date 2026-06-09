#!/usr/bin/env bash
set -euo pipefail

export DLSE_DATA_ROOT=/mnt/sda/gzx/data/deeplearning2se
export DLSE_MODEL_ROOT=/mnt/sda/gzx/models/deeplearning2se

python src/manual_error_review.py \
    --pred "$DLSE_MODEL_ROOT/outputs/run_losver_tag_seed42/test_predictions.csv" \
    --data "$DLSE_DATA_ROOT/processed/devign_losver/test.jsonl" \
    --out reports/tables/manual_error_review.csv \
    --summary-out reports/tables/manual_error_summary.csv \
    --per-type 12

