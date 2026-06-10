# deeplearning2se 实验执行计划与进度

> 项目主题：深度学习赋能软件工程  
> 课程要求：参考 2025/2026 年 TSE、TOSEM、ICSE、FSE、ASE、ISSTA 论文，围绕一个具体软件工程任务开展实验，撰写 4000-6000 字 PDF 报告。  
> 截止时间：2026-06-15 23:59  
> 当前推荐选题：基于 ASE 2025 LOSVER 思想的函数级漏洞检测轻量复现实验（LOSVER-Light）

## 0. 当前项目状态

- [x] 读取课程 PDF 要求。
- [x] 读取已有实验计划 `04-deep-research-report_最新实验计划.md`。
- [x] 确定主线任务：函数级漏洞检测。
- [x] 确定主方法来源：LOSVER 的行级信号引导思想。
- [x] 创建 `docs/task.md` 记录开发进度。
- [x] 创建 `docs/chat-log.md` 记录开发过程。
- [x] 初始化本地 Git 仓库。
- [x] 创建 GitHub 远端仓库 `deeplearning2se` 并推送。
- [x] 补充服务器实验交接说明 `docs/server-handoff.md`。

GitHub 远端：`https://github.com/Morishima6/deeplearning2se.git`

## 1. 研究目标

### 1.1 题目建议

基于行级风险信号的轻量级函数漏洞检测方法研究：以 LOSVER-Light 为例

### 1.2 核心思想

LOSVER 的关键思想是：在函数级漏洞检测中，模型不应只被动读取整段函数代码，而应获得显式的行级关注信号。原论文使用 line-level modifiability signal localization；本课程项目采用可复现的静态规则评分近似该阶段，生成 top-k 风险行，并将其转化为输入提示。

### 1.3 研究问题

- RQ1：与原始函数输入相比，加入行级风险信号的 LOSVER-Light 是否能提升函数级漏洞检测性能？
- RQ2：不同信号注入形式是否影响效果？例如只加 `<MOD>` 标签，还是增加风险行前缀摘要？
- RQ3：简单代码度量基线与 LLM/LoRA 方法相比能达到什么水平？它是否揭示了数据集中的浅层模式或 benchmark shortcut？

## 2. 文献与写作定位

### 2.1 主参考论文

- LOSVER: Line-Level Modifiability Signal-Guided Vulnerability Detection and Classification, ASE 2025.

报告中的用法：

- 作为主方法来源。
- 强调“行级信号引导函数级检测”的研究动机。
- 说明本项目是轻量化受启发实现，不是完整论文级复现。

### 2.2 辅助论文

- Enhancing Vulnerability Detection via Inter-procedural Semantic Completion, ISSTA 2025.
- Large Language Models for In-File Vulnerability Localization can be Lost in the End, FSE 2025.
- Top Score on the Wrong Exam: On Benchmarking in Machine Learning for Vulnerability Detection, ISSTA 2025.
- LLM-based Vulnerability Discovery through the Lens of Code Metrics, ICSE 2026.
- Towards Explainable Vulnerability Detection With Large Language Models, TSE 2025.

报告中的用法：

- 解释函数级漏洞检测的上下文不足问题。
- 解释输入组织、长度和信息位置可能影响模型效果。
- 支撑代码度量基线的必要性。
- 支撑结果不提升时的研究讨论：模型可能依赖浅层模式，而不是充分理解真实漏洞因果关系。

## 3. 数据集、模型与实验组

### 3.1 主数据集

- 数据集：CodeXGLUE Defect Detection / Devign。
- 任务：输入 C 函数代码，二分类判断是否存在漏洞。
- 推荐划分：使用数据集官方 train/validation/test 划分。

### 3.2 可选外部验证

- 数据集：PrimeVul 小型平衡子集。
- 触发条件：主实验和报告初稿已经完成，仍有至少半天余量。
- 用途：只做 sanity check，不作为主实验。

### 3.3 模型与基线

- Metrics-Baseline：Logistic Regression 或 XGBoost，输入为手工代码度量特征。
- Vanilla-LLM：Qwen2.5-Coder-1.5B + QLoRA，输入为原始函数代码。
- LOSVER-Light Tag：在 top-k 风险行前后加入 `<MOD>` 标记。
- LOSVER-Light Tag+Prefix：在输入前缀中列出 top-k 风险行摘要，同时保留 `<MOD>` 标记。
- Optional：最好配置使用第二随机种子复跑。

## 4. 仓库结构

计划结构如下：

```text
deeplearning2se/
  README.md
  requirements.txt
  accelerate_config.yaml
  configs/
    vanilla_qwen.yaml
    losver_light_tag.yaml
    losver_light_tag_prefix.yaml
    metrics_baseline.yaml
  data/
    raw/
    processed/
  docs/
    task.md
    chat-log.md
  src/
    export_hf_dataset.py
    build_line_signals.py
    extract_code_metrics.py
    train_metrics_baseline.py
    train_qwen_cls.py
    evaluate.py
    error_analysis.py
    plot_results.py
    utils_seed.py
  outputs/
  reports/
    figures/
    tables/
```

注意：`data/`、`outputs/`、模型权重和日志默认不提交到 Git。服务器大文件统一存放到 `/mnt/sda/gzx/data/deeplearning2se` 和 `/mnt/sda/gzx/models/deeplearning2se`，Hugging Face cache 使用 `/mnt/sda/gzx/models/huggingface`。

## 5. 阶段计划

### Phase 1：项目与环境准备

目标：让仓库、环境和数据下载流程跑通。

- [ ] 创建并激活环境。
- [ ] 安装 PyTorch CUDA 12.1 版本。
- [ ] 安装 Transformers、Datasets、PEFT、Accelerate、bitsandbytes、scikit-learn 等依赖。
- [x] 写 `requirements.txt`。
- [x] 写 `src/export_hf_dataset.py`。
- [ ] 下载并保存 Devign 官方划分。
- [x] 写数据检查逻辑，输出每个 split 的样本数、标签分布、平均函数长度。

推荐命令：

```bash
conda create -n dlse python=3.10 -y
conda activate dlse
pip install torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0 --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
python src/export_hf_dataset.py \
  --dataset google/code_x_glue_cc_defect_detection \
  --out "$DLSE_DATA_ROOT/raw/devign_hf" \
  --cache-dir "$HF_DATASETS_CACHE" \
  --stats-out reports/tables
```

服务器实际运行时优先使用外部存储：

```bash
export DLSE_DATA_ROOT=/mnt/sda/gzx/data/deeplearning2se
export DLSE_MODEL_ROOT=/mnt/sda/gzx/models/deeplearning2se
export HF_HOME=/mnt/sda/gzx/models/huggingface
export HF_DATASETS_CACHE=/mnt/sda/gzx/models/huggingface/datasets
export TRANSFORMERS_CACHE=/mnt/sda/gzx/models/huggingface/transformers
mkdir -p "$DLSE_DATA_ROOT" "$DLSE_MODEL_ROOT" "$HF_HOME" "$HF_DATASETS_CACHE" "$TRANSFORMERS_CACHE"

python src/export_hf_dataset.py \
  --dataset google/code_x_glue_cc_defect_detection \
  --out "$DLSE_DATA_ROOT/raw/devign_hf" \
  --cache-dir "$HF_DATASETS_CACHE" \
  --stats-out reports/tables
```

验收标准：

- [ ] `python src/export_hf_dataset.py ...` 能成功生成 `$DLSE_DATA_ROOT/raw/devign_hf/`。
- [ ] `reports/tables/dataset_stats.csv` 中有 split、label count、平均长度等统计。
- [x] README 中能说明如何复现数据准备。

### Phase 2：LOSVER-Light 行级信号与代码度量

目标：生成可解释、可复现的风险行标注和代码度量特征。

- [x] 实现 `src/build_line_signals.py`。
- [x] 风险行评分至少包含危险 API、指针/数组、复杂条件、循环、行长度、符号密度等特征。
- [x] 支持 `--top_k` 参数，默认 `top_k=5`。
- [x] 生成三种文本输入字段：`text_vanilla`、`text_tag`、`text_tag_prefix`。
- [x] 实现 `src/extract_code_metrics.py`。
- [ ] 输出处理后的 `train.jsonl`、`valid.jsonl`、`test.jsonl`。

风险行评分建议：

```text
score(line) =
  dangerous_api_weight
  + pointer_array_weight
  + branch_loop_weight
  + length_weight
  + symbol_density_weight
  + missing_check_hint_weight
```

验收标准：

- [ ] 随机抽查 20 个函数，风险行标注没有明显格式错误。
- [ ] 标签没有泄露到输入文本中。
- [ ] 三种输入形式长度统计已记录。

### Phase 3：Metrics-Baseline

目标：先得到一个快速、稳定的非深度基线。

- [x] 实现 `src/train_metrics_baseline.py`。
- [x] 支持 Logistic Regression。
- [ ] 可选支持 XGBoost；如安装困难则跳过。
- [x] 使用验证集选择最佳 F1 阈值。
- [x] 在测试集报告 Accuracy、Precision、Recall、F1、ROC-AUC、PR-AUC、Confusion Matrix。

推荐命令：

```bash
python src/train_metrics_baseline.py \
  --train "$DLSE_DATA_ROOT/processed/devign_losver/train.jsonl" \
  --valid "$DLSE_DATA_ROOT/processed/devign_losver/valid.jsonl" \
  --test "$DLSE_DATA_ROOT/processed/devign_losver/test.jsonl" \
  --out-dir "$DLSE_MODEL_ROOT/outputs/run_metrics_seed42" \
  --seed 42
```

验收标准：

- [ ] `$DLSE_MODEL_ROOT/outputs/run_metrics_seed42/eval.json` 存在。
- [ ] `$DLSE_MODEL_ROOT/outputs/run_metrics_seed42/test_predictions.csv` 存在。
- [x] 指标表可直接放入报告。
- [x] Metrics-Baseline 已完成：测试集 F1=0.630544，ROC-AUC=0.560892，PR-AUC=0.536395。

### Phase 4：Qwen2.5-Coder QLoRA 训练链路

目标：跑通 Vanilla-LLM 的 smoke test 和 full run。

- [x] 写 `configs/vanilla_qwen.yaml`。
- [x] 实现 `src/train_qwen_cls.py`。
- [x] 处理 tokenizer pad token。
- [x] 配置 4-bit quantization。
- [x] 配置 LoRA target modules。
- [x] 支持 `--max_train_samples`、`--max_eval_samples` 做 smoke test。
- [x] 先跑小样本 smoke test，确认 loss 下降、无 OOM。
- [ ] 再跑 full Vanilla-LLM。
- [x] full Vanilla-LLM 已完成：测试集 F1=0.647360，ROC-AUC=0.686953。

推荐 smoke test：

```bash
accelerate launch --mixed_precision fp16 src/train_qwen_cls.py \
  --config configs/vanilla_qwen.yaml \
  --seed 42 \
  --cache-dir "$HF_HOME" \
  --max_train_samples 512 \
  --max_eval_samples 256
```

推荐 full run：

```bash
accelerate launch --multi_gpu --mixed_precision fp16 --num_processes 2 src/train_qwen_cls.py \
  --config configs/vanilla_qwen.yaml \
  --seed 42 \
  --cache-dir "$HF_HOME"
```

验收标准：

- [ ] smoke test 正常结束。
- [ ] full run 生成 adapter、eval.json、test_predictions.csv。
- [ ] 训练日志记录 GPU、batch、max_length、seed。

### Phase 5：LOSVER-Light 主实验

目标：跑完 Tag 和 Tag+Prefix 两组主方法。

- [x] 写 `configs/losver_light_tag.yaml`。
- [x] 写 `configs/losver_light_tag_prefix.yaml`。
- [x] 训练 LOSVER-Light Tag，seed=42。
- [x] 训练 LOSVER-Light Tag+Prefix，seed=42。
- [x] 汇总 Vanilla、Tag、Tag+Prefix 与 Metrics-Baseline。
- [x] 新增 `run_qwen_full.sh` 和 `collect_results.sh`，用于正式三组实验和结果汇总。

推荐命令：

```bash
accelerate launch --multi_gpu --mixed_precision fp16 --num_processes 2 src/train_qwen_cls.py \
  --config configs/losver_light_tag.yaml \
  --seed 42 \
  --cache-dir "$HF_HOME"

accelerate launch --multi_gpu --mixed_precision fp16 --num_processes 2 src/train_qwen_cls.py \
  --config configs/losver_light_tag_prefix.yaml \
  --seed 42 \
  --cache-dir "$HF_HOME"
```

验收标准：

- [ ] 三组 LLM 实验均完成测试集评估。
- [x] 三组 LLM 实验均完成测试集评估。
- [x] `reports/tables/main_results.csv` 已生成。
- [x] 能回答 RQ1 和 RQ2。

### Phase 6：消融、稳定性与误差分析

目标：用最少额外成本补强报告可信度。

- [ ] 选择验证集表现最好的一组，用 seed=3407 复跑。
- [x] 增加 `top_k=3/8` 消融，验证风险行数量对 LOSVER-Light Tag 的影响。
- [x] 实现 `src/error_analysis.py`，导出误报/漏报案例。
- [x] 按错误类型标注 24 个代表性样本，覆盖 FP/FN。
- [x] 实现 `src/evaluate.py` 汇总结果表。
- [x] 实现 `src/plot_results.py` 生成结果柱状图。
- [x] 生成主结果柱状图和 top-k 消融柱状图。
- [x] 实现 `src/manual_error_review.py`，生成可人工标注的错例分析表。
- [x] 准备 `top_k=3/8` 消融脚本和配置。
- [x] 准备 `max_length=768` 可选配置，但默认不执行。

推荐命令：

```bash
python src/evaluate.py --runs "$DLSE_MODEL_ROOT/outputs/run_*" --out reports/tables/main_results.csv
python src/error_analysis.py \
  --pred "$DLSE_MODEL_ROOT/outputs/run_losver_prefix_seed42/test_predictions.csv" \
  --data "$DLSE_DATA_ROOT/processed/devign_losver/test.jsonl" \
  --out reports/tables/error_cases.csv
python src/plot_results.py --results reports/tables/main_results.csv --out reports/figures/main_results.png
```

当前推荐优先级：

```bash
# 1. 先做人工错例分析表，人工填写 manual_category/manual_note
bash scripts/prepare_manual_error_review.sh

# 2. 如时间允许，再跑 top_k=3/8 消融
bash scripts/run_topk_ablation.sh
bash scripts/collect_ablation_results.sh

# 3. max_length=768 仅作为可选配置，不默认执行
```

验收标准：

- [x] 能回答 RQ3。
- [x] 有主结果表、主结果图、消融表和消融图。
- [x] 错例分析能解释方法失败原因。

当前消融结论：

- `top_k=5` 是主实验中的最佳设置，测试集 F1=0.687276。
- `top_k=3` 风险行过少，测试集 Recall 从 0.841434 降到 0.805578，F1 降到 0.675576。
- `top_k=8` 相比 `top_k=5` Recall 更高，达到 0.859761，但 Precision 从 0.580858 降到 0.567298，F1 略降到 0.683560。
- 说明行级风险信号存在信息量与噪声之间的折中：过少会漏掉关键漏洞上下文，过多会引入非关键风险行并增加误报。

### Phase 7：报告写作与提交

目标：完成 4000-6000 字 PDF 报告。

- [x] 写引言。
- [x] 写相关工作。
- [x] 写深度学习技术原理。
- [x] 写 LOSVER-Light 方法。
- [x] 写实验设计：RQ、Dataset、Baseline、Metric、Environment。
- [x] 写实验结果与分析。
- [x] 写局限性与未来工作。
- [x] 写结论。
- [x] 合并最终报告初稿并控制在 4000-6000 中文字符范围内。
- [x] 校对引用、表编号、实验数字。
- [ ] 导出 PDF，命名为 `学号+姓名.pdf`。

建议报告结构：

```text
1. 引言
2. 相关工作
3. 技术背景与方法
4. 实验设计
5. 实验结果与分析
6. 局限性与未来工作
7. 结论
参考文献
```

验收标准：

- [ ] 字数在 4000-6000 字。
- [ ] 明确包含课程要求中的所有项目。
- [ ] 不直接翻译论文。
- [ ] 不直接复制粘贴 AI 生成内容；所有生成草稿都经过人工改写、核验和补充实验结果。
- [ ] PDF 可打开，图表清晰，文件名正确。

## 6. 推荐配置

### 6.1 QLoRA 超参数

| 项目 | 推荐值 |
|---|---|
| backbone | `Qwen/Qwen2.5-Coder-1.5B` |
| task | sequence classification, `num_labels=2` |
| quantization | 4-bit QLoRA |
| LoRA rank | 16 |
| LoRA alpha | 32 |
| LoRA dropout | 0.05 |
| target modules | `q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj` |
| max_length | 512 |
| per-device batch size | 4 |
| gradient accumulation | 4 |
| learning rate | 2e-4 |
| weight decay | 0.01 |
| warmup ratio | 0.05 |
| epochs | 3 |
| seed | 42, optional 3407 |
| early stopping | validation F1, patience=2 |

### 6.2 指标

- Accuracy
- Precision
- Recall
- F1
- ROC-AUC
- PR-AUC
- Confusion Matrix

阈值策略：在验证集上搜索使 F1 最大的阈值，并使用该阈值评估测试集。

## 7. 风险与降级方案

### 7.1 环境风险

- `transformers` 过低可能无法识别 Qwen2。
- `bitsandbytes` 与 CUDA 不匹配可能导致 4-bit 加载失败。
- 双卡 DDP 可能 hang。

处理：

- 固定依赖版本。
- 先跑 smoke test。
- 双卡不稳定时，改单卡并降低 batch/max_length。

### 7.2 显存风险

触发：OOM。

处理顺序：

1. `max_length=512` 降到 `384`。
2. `per_device_batch_size=4` 降到 `2`。
3. `gradient_accumulation=4` 提高到 `8`。
4. 只保留 Vanilla 与 LOSVER-Light Tag 两组。

### 7.3 时间风险

如果只剩 2-3 天：

- 保留 Metrics-Baseline。
- 保留 Vanilla-LLM。
- 保留 LOSVER-Light Tag。
- 取消 Tag+Prefix、PrimeVul、第二 seed。

报告仍然完整，因为它仍包含 baseline、主方法、评估和分析。

### 7.4 结果风险

如果 LOSVER-Light 没有提升：

- 不视为失败。
- 报告中重点分析：静态近似信号可能噪声较高；函数级 benchmark 可能存在浅层模式；代码度量基线若较强，则支持相关工作中对 benchmark shortcut 的担忧。

## 8. 每日执行节奏

| 日期 | 重点 | 目标产物 |
|---|---|---|
| 2026-06-06 | 仓库、计划、环境准备 | `docs/task.md`、`docs/chat-log.md`、Git 初始提交 |
| 2026-06-07 | 数据下载与行级信号 | Devign raw/processed 数据，风险行样例 |
| 2026-06-08 | Metrics-Baseline 与训练链路 | metrics 指标，Qwen smoke test |
| 2026-06-09 | Vanilla-LLM full run | vanilla 测试结果 |
| 2026-06-10 | LOSVER-Light 主实验 | Tag 与 Tag+Prefix 测试结果 |
| 2026-06-11 | 稳定性、消融、误差分析 | 汇总表、错例、图 |
| 2026-06-12 | 报告初稿 | 4000+ 字初稿 |
| 2026-06-13 | 报告修订与图表 | 完整报告和图表 |
| 2026-06-14 | PDF 导出与最终检查 | 可提交 PDF |
| 2026-06-15 | 预留缓冲 | Moodle 提交 |

## 9. 进度记录模板

每完成一个阶段，在本文件中勾选任务，并在 `docs/chat-log.md` 追加一条记录：

```text
## YYYY-MM-DD HH:mm

- 本次目标：
- 已完成：
- 关键命令：
- 结果文件：
- 遇到的问题：
- 下一步：
```
