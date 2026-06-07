# 服务器实验交接说明

本文档用于把项目交接给服务器上的另一个 Codex 或实验执行者。阅读顺序建议：

1. `README.md`
2. `docs/task.md`
3. `docs/server-handoff.md`
4. `docs/chat-log.md`

## 1. 当前状态

- GitHub 仓库：`https://github.com/Morishima6/deeplearning2se.git`
- 当前阶段：Phase 1，环境准备与数据导出。
- 已完成：
  - 本地项目初始化。
  - GitHub 创建并推送。
  - `requirements.txt` 已准备。
  - `src/export_hf_dataset.py` 已准备并通过语法检查。
  - `docs/task.md` 与 `docs/chat-log.md` 已创建。
- 尚未完成：
  - 服务器环境安装。
  - Devign/CodeXGLUE 数据下载。
  - Phase 2 行级风险信号脚本。

## 2. 重要协作规则

如果在服务器上使用 Codex，请遵守以下规则：

- 安装、配环境、下载数据、跑训练等操作不要由 Codex 擅自执行，除非用户明确授权。
- Codex 可以编写和修改脚本、配置、README、docs，并维护 git commit。
- `data/`、`outputs/`、模型权重、训练日志默认不提交到普通 Git。
- 可提交的结果文件优先放在：
  - `reports/tables/*.csv`
  - `reports/tables/*.json`
  - `reports/figures/*.png`
  - `docs/*.md`
- 每次阶段推进后，更新：
  - `docs/task.md`
  - `docs/chat-log.md`

## 3. 推荐工作流

```text
Windows 本地
  维护文档、写报告、查看图表、必要时代码修改

GitHub
  同步代码与轻量结果

Linux 服务器
  安装环境、下载数据、训练模型、生成结果
```

服务器不要把完整 `data/`、`outputs/`、adapter 权重直接提交到普通 Git。如果需要保存 adapter，建议单独压缩留在服务器、网盘或后续使用 Git LFS。

## 4. 服务器 Phase 1 手动命令

在服务器上手动执行：

```bash
git clone https://github.com/Morishima6/deeplearning2se.git
cd deeplearning2se

conda create -n dlse python=3.10 -y
conda activate dlse

pip install torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0 --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
```

检查 GPU 与 PyTorch：

```bash
nvidia-smi
python - <<'PY'
import torch
print("torch:", torch.__version__)
print("cuda available:", torch.cuda.is_available())
print("cuda version:", torch.version.cuda)
print("gpu count:", torch.cuda.device_count())
for i in range(torch.cuda.device_count()):
    print(i, torch.cuda.get_device_name(i))
PY
```

导出数据：

```bash
python src/export_hf_dataset.py \
  --dataset google/code_x_glue_cc_defect_detection \
  --out data/raw/devign_hf \
  --stats-out reports/tables
```

成功后应出现：

```text
data/raw/devign_hf/train.jsonl
data/raw/devign_hf/valid.jsonl
data/raw/devign_hf/test.jsonl
data/raw/devign_hf/dataset_stats.csv
reports/tables/dataset_stats.csv
```

## 5. 数据集命令失败时的处理

Hugging Face 数据集 ID 可能因为镜像、缓存或版本变化而不同。如果上面的 `--dataset` 报错，先不要改研究方案，按下面顺序尝试。

### 5.1 只把报错交给 Codex

最稳方式：把完整错误输出贴给 Codex，让它调整 `src/export_hf_dataset.py` 或数据集 ID。

### 5.2 可尝试的替代 dataset ID

按顺序尝试：

```bash
python src/export_hf_dataset.py \
  --dataset google/code_x_glue_cc_defect_detection \
  --out data/raw/devign_hf \
  --stats-out reports/tables \
  --trust-remote-code
```

```bash
python src/export_hf_dataset.py \
  --dataset code_x_glue_cc_defect_detection \
  --out data/raw/devign_hf \
  --stats-out reports/tables
```

如果数据集字段名无法自动识别，可根据 `load_dataset` 打印的字段显式指定：

```bash
python src/export_hf_dataset.py \
  --dataset DATASET_ID_HERE \
  --code-column func \
  --label-column target \
  --out data/raw/devign_hf \
  --stats-out reports/tables
```

## 6. Phase 1 完成后应该做什么

Phase 1 完成条件：

- `data/raw/devign_hf/train.jsonl` 存在。
- `data/raw/devign_hf/valid.jsonl` 存在。
- `data/raw/devign_hf/test.jsonl` 存在。
- `reports/tables/dataset_stats.csv` 存在。
- `dataset_stats.csv` 中 train/valid/test 数量合理。

完成后建议提交轻量文件：

```bash
git status
git add reports/tables/dataset_stats.csv reports/tables/dataset_stats.json docs/task.md docs/chat-log.md
git commit -m "Record phase 1 dataset statistics"
git push
```

注意：如果 `reports/tables/*.csv` 被 `.gitignore` 忽略，需要先检查 `.gitignore`。当前 `.gitignore` 忽略了 `reports/**/*.png`、`reports/**/*.jpg`、`reports/**/*.xlsx`、`reports/**/*.pdf`，没有忽略 csv/json。

## 7. Phase 2 预期任务

Phase 2 要实现：

- `src/build_line_signals.py`
- 可选 `src/extract_code_metrics.py`

输入：

```text
data/raw/devign_hf/train.jsonl
data/raw/devign_hf/valid.jsonl
data/raw/devign_hf/test.jsonl
```

输出：

```text
data/processed/devign_losver/train.jsonl
data/processed/devign_losver/valid.jsonl
data/processed/devign_losver/test.jsonl
reports/tables/line_signal_stats.csv
```

每条处理后样本建议包含字段：

```json
{
  "id": "...",
  "code": "...",
  "label": 0,
  "risk_lines": [
    {
      "line_no": 12,
      "score": 5.5,
      "text": "strcpy(buf, input);",
      "reasons": ["dangerous_api", "pointer_or_array"]
    }
  ],
  "text_vanilla": "...",
  "text_tag": "...",
  "text_tag_prefix": "...",
  "metrics": {
    "num_lines": 40,
    "num_chars": 1200,
    "num_dangerous_api": 2
  }
}
```

风险行评分最小可行版本：

- dangerous API：`strcpy`、`strncpy`、`sprintf`、`gets`、`memcpy`、`malloc`、`free`、`realloc`、`scanf`
- 指针/数组：`*`、`->`、`[`、`]`
- 分支/循环：`if`、`else`、`for`、`while`、`switch`
- 错误处理：`return`、`goto`、`NULL`、`errno`
- 行长度和符号密度

## 8. 报告写作提醒

课程明确禁止直接复制粘贴 AI 生成内容。Codex 可以辅助形成结构、实验记录和草稿，但最终报告应由学生基于真实实验结果改写、核验和整合。

报告必须覆盖：

- 软件工程任务。
- 研究现状。
- 深度学习技术原理。
- 方法细节。
- 实验设计：RQ、Dataset、Baseline、Metric、Environment。
- 实验结果、分析和结论。

## 9. 给服务器 Codex 的最短指令

如果要让另一个 Codex 接着做，可以直接给它这段话：

```text
请阅读 README.md、docs/task.md、docs/server-handoff.md 和 docs/chat-log.md。
当前项目是深度学习课程大作业 deeplearning2se，主题是基于 LOSVER-Light 的函数级漏洞检测。
请不要擅自执行安装、配环境、下载数据或训练命令；这些命令只提供给我手动运行。
你可以编写脚本、配置和文档，并维护 git。
当前阶段是 Phase 1/Phase 2：先根据我手动运行 Phase 1 数据导出命令后的输出，修正数据脚本或继续实现 build_line_signals.py。
```
