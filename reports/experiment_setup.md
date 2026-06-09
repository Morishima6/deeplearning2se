# 实验设计

本章说明本文的研究问题、数据集、对比方法、评价指标、实验环境和复现流程。实验设计的目标不是追求最大规模训练，而是在课程项目周期内围绕一个明确的软件工程任务，验证 LOSVER 论文中“行级信号引导漏洞检测”这一核心思想是否能在轻量实现中产生效果。

## 1. 研究问题

本文围绕函数级漏洞检测任务设置四个研究问题。

**RQ1：显式行级风险信号是否能提升函数级漏洞检测性能？**

该问题对应 LOSVER 的核心主张。函数级漏洞检测模型通常直接读取整段函数代码，但漏洞相关信息往往只集中在少数关键行。本文通过比较 Vanilla Qwen 和 LOSVER-Light Tag，验证将 top-k 风险行用 `<MOD>` 标记显式突出后，模型是否能获得更好的 F1、ROC-AUC 和 PR-AUC。

**RQ2：不同信号注入形式是否影响效果？**

仅加入行内 `<MOD>` 标签是一种较弱提示；在输入前额外列出风险行摘要则是一种更强提示。本文比较 LOSVER-Light Tag 和 LOSVER-Light Tag+Prefix，分析更显式的风险行摘要是否带来进一步收益，或者是否会因为放大启发式噪声而增加误报。

**RQ3：简单代码度量基线能达到什么水平？**

近年来的漏洞检测研究反复指出，函数级二分类数据集中可能存在浅层模式，例如函数长度、危险 API、指针操作和控制流复杂度。本文使用 Logistic Regression + 手工代码度量作为非深度基线，用来检查浅层代码特征能解释多少检测性能。

**RQ4：风险行数量 top-k 是否存在最优区间？**

LOSVER-Light 的核心参数是风险行数量 `top_k`。如果 `top_k` 过小，模型可能漏掉关键漏洞上下文；如果 `top_k` 过大，则可能引入普通低层代码、错误处理或 I/O 逻辑等噪声。本文在最佳主方法 LOSVER-Light Tag 上比较 `top_k=3/5/8`，验证行级提示数量的影响。

## 2. 数据集

实验使用 CodeXGLUE Defect Detection / Devign 数据集。该数据集是函数级漏洞检测常用基准，任务形式为二分类：输入一个 C/C++ 函数，输出该函数是否存在漏洞。本文使用官方 train/valid/test 划分，避免重新划分导致不可比或数据泄露。

**表 1 数据集划分统计**

| Split | 样本数 | 安全样本 | 漏洞样本 | 平均行数 | 中位行数 | 平均字符数 |
|---|---:|---:|---:|---:|---:|---:|
| Train | 21854 | 11836 | 10018 | 112.44 | 57.0 | 2031.38 |
| Valid | 2732 | 1545 | 1187 | 109.32 | 57.0 | 1982.55 |
| Test | 2732 | 1477 | 1255 | 112.30 | 59.0 | 2006.05 |

训练集、验证集和测试集的标签分布较接近，漏洞样本约占 43% 到 46%。函数长度分布存在明显长尾：平均行数约为 110 行，但中位数约为 57 行。这说明一部分函数非常长，容易造成输入截断或关键信息稀释，也为后续错例分析中的“长函数/截断”问题提供了背景。

## 3. 对比方法

本文比较四组主实验方法和一组消融实验。

**表 2 主实验方法**

| 方法 | 模型 | 输入 | 目的 |
|---|---|---|---|
| Metrics-Baseline | Logistic Regression | 15 个手工代码度量特征 | 检查浅层代码模式能达到的基线水平 |
| Vanilla Qwen | Qwen2.5-Coder-1.5B + QLoRA | 原始函数代码 `text_vanilla` | 现代代码大模型基线 |
| LOSVER-Light Tag | Qwen2.5-Coder-1.5B + QLoRA | 带 `<MOD>` 标签的 `text_tag` | 验证行级风险信号是否有效 |
| LOSVER-Light Tag+Prefix | Qwen2.5-Coder-1.5B + QLoRA | 风险行摘要 + `<MOD>` 标签 `text_tag_prefix` | 验证更强提示是否进一步提升效果 |

Metrics-Baseline 使用函数长度、token 数、危险 API 数量、指针/数组符号数量、控制流数量、错误处理 token、符号密度和风险行统计等特征。它的目的不是替代深度模型，而是作为研究对照：如果简单度量表现很强，说明数据集中存在可被浅层模式利用的信号；如果其 ROC-AUC 或误报控制较差，则说明这些信号不足以形成可靠判别边界。

三组 Qwen 模型使用相同骨干、相同训练参数和相同数据划分，只改变输入字段。因此，Vanilla、Tag 和 Tag+Prefix 之间的差异主要来自行级风险信号的注入方式，而不是模型规模或训练策略差异。

**表 3 消融实验**

| 消融项 | 设置 | 目的 |
|---|---|---|
| `top_k` | 3、5、8 | 分析风险行数量对 LOSVER-Light Tag 的影响 |

消融实验只在 LOSVER-Light Tag 上进行，因为主实验中 Tag 是综合表现最好的行级信号注入方式。这样可以控制实验成本，并将分析重点集中在行级风险信号数量本身。

## 4. 评价指标

本文报告以下评价指标。

| 指标 | 含义 | 在漏洞检测中的作用 |
|---|---|---|
| Accuracy | 总体分类正确率 | 衡量整体预测正确程度 |
| Precision | 预测为漏洞的样本中真实漏洞比例 | 反映误报控制能力 |
| Recall | 真实漏洞中被检出的比例 | 反映漏报控制能力 |
| F1 | Precision 和 Recall 的调和平均 | 在误报和漏报之间做综合比较 |
| ROC-AUC | 基于所有阈值的排序能力 | 衡量模型区分安全/漏洞样本的整体能力 |
| PR-AUC | Precision-Recall 曲线下面积 | 更关注漏洞类别的检出质量 |
| Confusion Matrix | TN、FP、FN、TP | 具体分析误报和漏报来源 |

阈值选择采用验证集策略。具体而言，对模型输出的漏洞概率，在验证集上枚举 0.05 到 0.95 的阈值并选择 F1 最高者，然后将该阈值用于测试集。这样做可以避免固定 0.5 阈值带来的偶然性，也更符合漏洞检测中根据应用需求调节报警阈值的实际场景。ROC-AUC 和 PR-AUC 使用连续概率分数计算，不依赖单一阈值。

## 5. 训练设置

深度学习实验使用 Qwen2.5-Coder-1.5B 作为骨干模型，并采用 4-bit QLoRA 微调。主要超参数如下。

**表 4 Qwen + QLoRA 训练配置**

| 参数 | 取值 |
|---|---|
| backbone | `Qwen/Qwen2.5-Coder-1.5B` |
| task head | sequence classification, `num_labels=2` |
| quantization | 4-bit NF4, double quantization |
| LoRA rank | 16 |
| LoRA alpha | 32 |
| LoRA dropout | 0.05 |
| LoRA target modules | `q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj` |
| max_length | 512 |
| epochs | 3 |
| per-device train batch size | 4 |
| per-device eval batch size | 4 |
| gradient accumulation steps | 4 |
| learning rate | 2e-4 |
| weight decay | 0.01 |
| warmup ratio | 0.05 |
| mixed precision | fp16 |
| seed | 42 |

所有主实验都使用相同训练设置。训练过程中每个 epoch 在验证集上评估一次，`metric_for_best_model` 设为验证集 F1，并保存最佳模型。最终测试集结果来自最佳 checkpoint 在测试集上的预测。

Metrics-Baseline 使用 `StandardScaler` 标准化特征，并训练 `LogisticRegression(class_weight="balanced", solver="liblinear")`。同样使用验证集选择最佳 F1 阈值，再在测试集上报告指标。

## 6. 实验环境

实验在一台 Linux GPU 服务器上完成，主要硬件和软件环境如下。

**表 5 实验环境**

| 项目 | 配置 |
|---|---|
| GPU | 2 × NVIDIA RTX 3090 |
| Python | 3.10，conda 环境 `dlse` |
| PyTorch | 2.4.0，CUDA 12.1 wheel |
| transformers | 4.48.0 |
| datasets | 2.21.0 |
| peft | 0.14.0 |
| accelerate | 1.0.1 |
| bitsandbytes | 0.43.3 |
| scikit-learn | 1.5.1 |
| pandas | 2.2.2 |
| matplotlib | 3.9.2 |

为了避免仓库膨胀，数据集、模型权重和 Hugging Face cache 不保存在项目目录中。实验统一使用外部路径：

```bash
DLSE_DATA_ROOT=/mnt/sda/gzx/data/deeplearning2se
DLSE_MODEL_ROOT=/mnt/sda/gzx/models/deeplearning2se
HF_HOME=/mnt/sda/gzx/models/huggingface
HF_DATASETS_CACHE=/mnt/sda/gzx/models/huggingface/datasets
```

仓库内只保存源码、配置、轻量结果表、报告草稿和必要图表。模型 checkpoint、adapter、原始数据和日志文件不纳入 Git 管理。

## 7. 复现流程

完整复现实验可以分为五个阶段。

**阶段一：下载并导出数据**

```bash
bash scripts/download.sh
```

该脚本将 Devign 数据导出到 `$DLSE_DATA_ROOT/raw/devign_hf`，并生成数据统计表。

**阶段二：构建行级风险信号和度量特征**

```bash
python src/build_line_signals.py \
  --in "$DLSE_DATA_ROOT/raw/devign_hf" \
  --out "$DLSE_DATA_ROOT/processed/devign_losver" \
  --top_k 5 \
  --stats-out reports/tables

python src/extract_code_metrics.py \
  --in "$DLSE_DATA_ROOT/processed/devign_losver" \
  --out reports/tables/code_metrics.csv
```

**阶段三：训练代码度量基线**

```bash
python src/train_metrics_baseline.py \
  --train "$DLSE_DATA_ROOT/processed/devign_losver/train.jsonl" \
  --valid "$DLSE_DATA_ROOT/processed/devign_losver/valid.jsonl" \
  --test "$DLSE_DATA_ROOT/processed/devign_losver/test.jsonl" \
  --out-dir "$DLSE_MODEL_ROOT/outputs/run_metrics_seed42" \
  --seed 42
```

**阶段四：训练三组 Qwen 主实验**

```bash
bash scripts/run_qwen_full.sh
bash scripts/collect_results.sh
```

第一条命令依次训练 Vanilla Qwen、LOSVER-Light Tag 和 LOSVER-Light Tag+Prefix；第二条命令汇总主结果、导出错例并生成主结果图。

**阶段五：执行 top-k 消融和人工错例分析**

```bash
bash scripts/prepare_manual_error_review.sh
bash scripts/run_topk_ablation.sh
bash scripts/collect_ablation_results.sh
```

其中人工错例分析脚本会生成待人工标注的错例表；本实验已对其中 24 个样本填写 `manual_category` 和 `manual_note`，用于报告中的错误原因分析。

## 8. 有效性威胁

本文实验存在以下有效性威胁。

第一，LOSVER-Light 并不是原始 LOSVER 的完整复现。原论文中的 line-level modifiability signal localization 被本文替换为静态启发式风险评分。因此，实验只能说明轻量级行级风险提示在 Devign 上有效，不能直接等同于原论文完整方法的效果。

第二，实验主要在 Devign 数据集上完成。Devign 是常用函数级漏洞检测基准，但函数级标签无法完整表达项目级上下文、跨函数调用、补丁历史和真实漏洞触发路径。因此，模型在该数据集上的提升不一定能直接推广到真实工程漏洞发现。

第三，训练主要使用单一随机种子 seed=42。虽然主实验和消融实验都保持了统一 seed 和统一配置，但未进行多种子统计显著性检验。考虑到课程项目时间限制，本文将人工错例分析和 top-k 消融作为补充证据，而不是声称结果具有完整统计稳定性。

第四，静态风险评分可能引入启发式偏差。例如，错误处理、资源释放、I/O 解析、指针操作和低层系统代码常被标记为风险行，但它们在安全函数中也大量存在。这种偏差既是方法的局限，也是实验中需要通过消融和错例分析解释的对象。

## 9. 实验设计小结

本文实验设计围绕“行级风险信号是否能帮助函数级漏洞检测”这一核心问题展开。主实验通过相同骨干模型下的 Vanilla、Tag 和 Tag+Prefix 对比回答 RQ1 和 RQ2；Metrics-Baseline 回答 RQ3，检查浅层代码度量的解释力；top-k 消融回答 RQ4，分析风险行数量的敏感性；人工错例分析进一步解释方法失败原因。整体设计覆盖了基线、主方法、消融和误差分析四类证据，能够较完整地支撑课程报告中的实验结论。
