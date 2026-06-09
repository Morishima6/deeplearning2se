#!/usr/bin/env bash
set -euo pipefail

export DLSE_MODEL_ROOT=/mnt/sda/gzx/models/deeplearning2se

python src/evaluate.py \
    --runs \
    "$DLSE_MODEL_ROOT/outputs/run_losver_tag_seed42" \
    "$DLSE_MODEL_ROOT/outputs/run_losver_tag_topk3_seed42" \
    "$DLSE_MODEL_ROOT/outputs/run_losver_tag_topk8_seed42" \
    "$DLSE_MODEL_ROOT/outputs/run_losver_tag_maxlen768_seed42" \
    --out reports/tables/ablation_results.csv

