#!/usr/bin/env bash
set -Eeuo pipefail

trap 'echo "[ERROR] Failed at line ${LINENO}: ${BASH_COMMAND}" >&2' ERR
trap 'echo "[ERROR] Received SIGHUP. Run this script inside tmux/screen or with nohup." >&2; exit 129' HUP
trap 'echo "[ERROR] Received SIGINT/SIGTERM. Top-k ablation stopped before completion." >&2; exit 130' INT TERM

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

echo "[INFO] Top-k ablation started at $(date '+%Y-%m-%d %H:%M:%S')"
echo "[INFO] Data root: $DLSE_DATA_ROOT"
echo "[INFO] Model root: $DLSE_MODEL_ROOT"
echo "[INFO] HF_HOME: $HF_HOME"

echo "[STEP 1/4] Build LOSVER-Light signals with top_k=3"
python src/build_line_signals.py \
    --in "$DLSE_DATA_ROOT/raw/devign_hf" \
    --out "$DLSE_DATA_ROOT/processed/devign_losver_topk3" \
    --top_k 3 \
    --stats-out reports/tables \
    --stats-name line_signal_stats_topk3
echo "[DONE 1/4] top_k=3 signal data ready"

echo "[STEP 2/4] Build LOSVER-Light signals with top_k=8"
python src/build_line_signals.py \
    --in "$DLSE_DATA_ROOT/raw/devign_hf" \
    --out "$DLSE_DATA_ROOT/processed/devign_losver_topk8" \
    --top_k 8 \
    --stats-out reports/tables \
    --stats-name line_signal_stats_topk8
echo "[DONE 2/4] top_k=8 signal data ready"

echo "[STEP 3/4] Train Qwen LOSVER-Light with top_k=3"
accelerate launch --multi_gpu --num_processes 2 --num_machines 1 --mixed_precision fp16 --dynamo_backend no src/train_qwen_cls.py \
    --config configs/losver_light_tag_topk3.yaml \
    --seed 42 \
    --cache-dir "$HF_HOME"
echo "[DONE 3/4] top_k=3 Qwen run finished"

echo "[STEP 4/4] Train Qwen LOSVER-Light with top_k=8"
accelerate launch --multi_gpu --num_processes 2 --num_machines 1 --mixed_precision fp16 --dynamo_backend no src/train_qwen_cls.py \
    --config configs/losver_light_tag_topk8.yaml \
    --seed 42 \
    --cache-dir "$HF_HOME"
echo "[DONE 4/4] top_k=8 Qwen run finished"
echo "[INFO] Top-k ablation completed at $(date '+%Y-%m-%d %H:%M:%S')"
