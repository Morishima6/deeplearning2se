# deeplearning2se

课程项目：深度学习赋能软件工程。

本仓库计划实现一个基于 ASE 2025 LOSVER 思想的轻量级函数漏洞检测实验。核心问题是：显式的行级风险信号是否能帮助代码大模型进行函数级漏洞检测。

## Project Plan

详细执行计划见 [docs/task.md](docs/task.md)。

开发与实验记录见 [docs/chat-log.md](docs/chat-log.md)。

服务器交接说明见 [docs/server-handoff.md](docs/server-handoff.md)。

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
