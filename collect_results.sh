#!/usr/bin/env bash
set -euo pipefail

export DLSE_DATA_ROOT=/mnt/sda/gzx/data/deeplearning2se
export DLSE_MODEL_ROOT=/mnt/sda/gzx/models/deeplearning2se

python src/evaluate.py --runs "$DLSE_MODEL_ROOT/outputs/run_*_seed42" --out reports/tables/main_results.csv

python src/error_analysis.py \
    --pred "$DLSE_MODEL_ROOT/outputs/run_losver_prefix_seed42/test_predictions.csv" \
    --data "$DLSE_DATA_ROOT/processed/devign_losver/test.jsonl" \
    --out reports/tables/error_cases.csv

python src/plot_results.py \
    --results reports/tables/main_results.csv \
    --out reports/figures/main_results.png

