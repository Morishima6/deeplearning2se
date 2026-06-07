# deeplearning2se

课程项目：深度学习赋能软件工程。

本仓库计划实现一个基于 ASE 2025 LOSVER 思想的轻量级函数漏洞检测实验。核心问题是：显式的行级风险信号是否能帮助代码大模型进行函数级漏洞检测。

## Project Plan

详细执行计划见 [docs/task.md](docs/task.md)。

开发与实验记录见 [docs/chat-log.md](docs/chat-log.md)。

服务器交接说明见 [docs/server-handoff.md](docs/server-handoff.md)。

项目协作规范见 [AGENTS.md](AGENTS.md)。

## Current Direction

- Task: function-level vulnerability detection.
- Main idea: LOSVER-Light, a lightweight approximation of line-level modifiability signal guided vulnerability detection.
- Dataset: CodeXGLUE Defect Detection / Devign.
- Backbone: Qwen2.5-Coder-1.5B with 4-bit QLoRA.
- Baselines:
  - code metrics + Logistic Regression or XGBoost;
  - vanilla Qwen sequence classification;
  - LOSVER-Light Tag;
  - LOSVER-Light Tag+Prefix.

## Planned Structure

```text
configs/      experiment configs
data/         local datasets, ignored by git
docs/         task plan and development logs
outputs/      experiment outputs, ignored by git
reports/      final figures, tables, and report assets
src/          implementation scripts
```

## GitHub

Recommended repository name: `deeplearning2se`.

The local repository can be linked with:

```bash
git remote add origin https://github.com/Morishima6/deeplearning2se.git
git push -u origin main
```

Remote creation requires GitHub authentication, for example `gh auth login` or a valid GitHub token.

## Phase 1 Commands

Environment setup and dataset download should be run manually on the Linux GPU server:

```bash
conda create -n dlse python=3.10 -y
conda activate dlse
pip install torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0 --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
python src/export_hf_dataset.py --dataset google/code_x_glue_cc_defect_detection --out data/raw/devign_hf --stats-out reports/tables
```

## Phase 2/3 Commands

数据导出成功后，在服务器上继续手动执行：

```bash
python src/build_line_signals.py \
  --in data/raw/devign_hf \
  --out data/processed/devign_losver \
  --top_k 5 \
  --stats-out reports/tables

python src/extract_code_metrics.py \
  --in data/processed/devign_losver \
  --out reports/tables/code_metrics.csv

python src/train_metrics_baseline.py \
  --train data/processed/devign_losver/train.jsonl \
  --valid data/processed/devign_losver/valid.jsonl \
  --test data/processed/devign_losver/test.jsonl \
  --seed 42
```

成功后应重点保留：

```text
reports/tables/line_signal_stats.csv
reports/tables/code_metrics.csv
outputs/run_metrics_seed42/eval.json
outputs/run_metrics_seed42/test_predictions.csv
```

汇总结果与导出错例：

```bash
python src/evaluate.py --runs "outputs/run_*" --out reports/tables/main_results.csv
python src/error_analysis.py \
  --pred outputs/run_metrics_seed42/test_predictions.csv \
  --data data/processed/devign_losver/test.jsonl \
  --out reports/tables/error_cases.csv
python src/plot_results.py \
  --results reports/tables/main_results.csv \
  --out reports/figures/main_results.png
```

## QLoRA Commands

先跑 smoke test：

```bash
accelerate launch --mixed_precision fp16 src/train_qwen_cls.py \
  --config configs/vanilla_qwen.yaml \
  --seed 42 \
  --max-train-samples 512 \
  --max-eval-samples 256
```

确认无 OOM 后再跑完整实验：

```bash
accelerate launch --multi_gpu --mixed_precision fp16 --num_processes 2 src/train_qwen_cls.py \
  --config configs/vanilla_qwen.yaml \
  --seed 42

accelerate launch --multi_gpu --mixed_precision fp16 --num_processes 2 src/train_qwen_cls.py \
  --config configs/losver_light_tag.yaml \
  --seed 42

accelerate launch --multi_gpu --mixed_precision fp16 --num_processes 2 src/train_qwen_cls.py \
  --config configs/losver_light_tag_prefix.yaml \
  --seed 42
```
