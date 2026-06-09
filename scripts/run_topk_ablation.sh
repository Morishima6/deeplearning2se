#!/usr/bin/env bash
set -euo pipefail

export DLSE_DATA_ROOT=/mnt/sda/gzx/data/deeplearning2se
export DLSE_MODEL_ROOT=/mnt/sda/gzx/models/deeplearning2se
export HF_HOME=/mnt/sda/gzx/models/huggingface
export HF_DATASETS_CACHE=/mnt/sda/gzx/models/huggingface/datasets
export HF_ENDPOINT=${HF_ENDPOINT:-https://hf-mirror.com}
export HF_HUB_DISABLE_IMPLICIT_TOKEN=1

unset HF_TOKEN
unset HUGGINGFACE_HUB_TOKEN
unset HUGGING_FACE_HUB_TOKEN
mkdir -p "$DLSE_DATA_ROOT" "$DLSE_MODEL_ROOT" "$HF_HOME" "$HF_DATASETS_CACHE"

python src/build_line_signals.py \
    --in "$DLSE_DATA_ROOT/raw/devign_hf" \
    --out "$DLSE_DATA_ROOT/processed/devign_losver_topk3" \
    --top_k 3 \
    --stats-out reports/tables \
    --stats-name line_signal_stats_topk3

python src/build_line_signals.py \
    --in "$DLSE_DATA_ROOT/raw/devign_hf" \
    --out "$DLSE_DATA_ROOT/processed/devign_losver_topk8" \
    --top_k 8 \
    --stats-out reports/tables \
    --stats-name line_signal_stats_topk8

accelerate launch --multi_gpu --num_processes 2 --mixed_precision fp16 src/train_qwen_cls.py \
    --config configs/losver_light_tag_topk3.yaml \
    --seed 42 \
    --cache-dir "$HF_HOME"

accelerate launch --multi_gpu --num_processes 2 --mixed_precision fp16 src/train_qwen_cls.py \
    --config configs/losver_light_tag_topk8.yaml \
    --seed 42 \
    --cache-dir "$HF_HOME"
