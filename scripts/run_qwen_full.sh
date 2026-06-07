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

accelerate launch --multi_gpu --num_processes 2 --mixed_precision fp16 src/train_qwen_cls.py \
    --config configs/vanilla_qwen.yaml \
    --seed 42 \
    --cache-dir "$HF_HOME"

accelerate launch --multi_gpu --num_processes 2 --mixed_precision fp16 src/train_qwen_cls.py \
    --config configs/losver_light_tag.yaml \
    --seed 42 \
    --cache-dir "$HF_HOME"

accelerate launch --multi_gpu --num_processes 2 --mixed_precision fp16 src/train_qwen_cls.py \
    --config configs/losver_light_tag_prefix.yaml \
    --seed 42 \
    --cache-dir "$HF_HOME"
