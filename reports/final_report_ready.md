# 基于行级风险信号的轻量级函数漏洞检测方法研究：以 LOSVER-Light 为例

## 摘要

漏洞检测是深度学习赋能软件工程的重要任务。函数级漏洞检测虽然便于建模和评估，但模型容易依赖函数长度、危险 API、指针操作等浅层模式，也难以定位真正关键的漏洞代码行。本文参考 ASE 2025 论文 LOSVER 的行级信号思想，设计了轻量方法 LOSVER-Light：先用静态规则为函数内每一行计算风险分数，选取 top-k 风险行，再通过 `<MOD>` 标签或风险行摘要将局部风险信号注入 Qwen2.5-Coder-1.5B 分类器。实验在 CodeXGLUE Defect Detection / Devign 数据集上进行。结果显示，LOSVER-Light Tag 在测试集上达到 F1=0.687276、ROC-AUC=0.760319、PR-AUC=0.757150，相比 Vanilla Qwen 分别提升 0.039916、0.073366 和 0.077507。消融实验表明 `top_k=5` 是较合理折中，人工错例分析说明长函数、领域语义和底层指针操作仍是主要难点。

## 1. 引言与相关工作

传统漏洞检测依赖静态分析、规则匹配和人工审计，优点是可解释，但在真实项目中容易受到路径爆炸、调用关系和误报率影响。深度学习为漏洞检测提供了新的路径：代码模型可以从大规模语料中学习 API 使用、控制流、错误处理和缺陷模式。不过，漏洞检测并不是普通文本分类。一个函数是否存在漏洞，往往取决于少数关键行、边界条件、资源生命周期或跨函数上下文。函数级二分类数据集虽然方便实验，却可能让模型学习到“长函数、危险 API、指针多就更像漏洞”的 shortcut。

本文以 ASE 2025 论文 LOSVER 为主要参考。LOSVER 的核心观点是，漏洞检测模型不应只读取完整函数，还应获得显式的行级信号，从而关注更可能与漏洞相关的位置。FSE 2025 的 Lost-in-the-End 指出，大模型在长代码漏洞定位中可能受到输入位置影响；ISSTA 2025 的 Inter-procedural Semantic Completion 强调跨函数语义对漏洞检测的重要性；ISSTA 2025 的 Top Score on the Wrong Exam 反思了函数级漏洞检测 benchmark 的外部效度；ICSE 2026 的 code metrics 视角说明 LLM 预测可能与传统代码度量相关；TSE 2025 的可解释漏洞检测工作则提示二分类结果本身不足以支持开发者使用。

因此，本文将自身定位为 LOSVER 思想的课程级轻量复现实验，而不是完整论文级系统复现。本文关注四个问题：RQ1，行级风险信号是否提升检测性能；RQ2，不同信号注入方式是否影响效果；RQ3，代码度量基线能解释多少性能；RQ4，风险行数量 top-k 是否存在较优区间。

## 2. 深度学习技术原理与方法

本文使用的深度学习核心是代码语言模型微调。Qwen2.5-Coder-1.5B 已在大规模代码语料上预训练，能够把函数代码 token 编码为上下文表示；在漏洞检测中，再接一个二分类头，输出函数为 vulnerable 的概率。由于全量微调 1.5B 参数成本较高，本文采用 4-bit QLoRA：基础模型权重量化为 NF4，训练时只更新少量 LoRA 低秩矩阵。LoRA 将权重更新近似为低秩分解，在保持模型主体冻结的同时学习任务相关适配参数，从而显著降低显存和训练成本。本文设置 LoRA rank=16、alpha=32、dropout=0.05，目标模块包括 `q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj`。

LOSVER-Light 的方法流程为：函数按行切分，逐行计算静态风险分数，选择 top-k 风险行，构造输入文本，再训练 Qwen 分类器。风险评分关注十类信号：敏感 API，如 `strcpy`、`memcpy`、`sprintf`、`malloc`、`free`；指针和数组符号，如 `->`、`*`、`[`、`]`；分支循环，如 `if`、`for`、`while`、`switch`；错误处理 token，如 `return`、`goto`、`NULL`；I/O 或系统接口，如 `open`、`read`、`write`、`recv`、`send`；此外还考虑长行、符号密度和未检查的敏感调用。所有候选行按风险分数降序、行号升序排序，默认选择 `top_k=5`。

本文构造三种输入。Vanilla 输入直接使用原始函数代码 `text_vanilla`。Tag 输入在 top-k 风险行前后加入 `<MOD>` 和 `</MOD>`，形成 `text_tag`，保留风险行在原函数中的上下文位置。Tag+Prefix 输入在 Tag 前添加风险行摘要，列出行号、分数、触发原因和代码内容，形成 `text_tag_prefix`。此外，本文还构造 Metrics-Baseline，从函数中提取 15 个代码度量特征，如行数、token 数、危险 API 数量、控制流数量、指针数组符号数量、符号密度、最大风险分数等，并训练 Logistic Regression。

## 3. 实验设计

实验使用 CodeXGLUE Defect Detection / Devign 数据集，任务是输入 C/C++ 函数并判断是否存在漏洞。本文采用官方划分：训练集 21854 条，验证集 2732 条，测试集 2732 条。测试集中安全样本 1477 条，漏洞样本 1255 条。三个划分平均函数行数约 110 行，中位数约 57 行，说明存在明显长函数长尾。

主实验比较四组方法：Metrics-Baseline、Vanilla Qwen、LOSVER-Light Tag 和 LOSVER-Light Tag+Prefix。三组 Qwen 方法使用相同骨干、训练参数和数据划分，只改变输入字段，因此差异主要来自行级风险信号的注入方式。消融实验在 LOSVER-Light Tag 上比较 `top_k=3/5/8`。

评价指标包括 Accuracy、Precision、Recall、F1、ROC-AUC、PR-AUC 和混淆矩阵。阈值不固定为 0.5，而是在验证集上枚举 0.05 到 0.95，选择 F1 最高的阈值，再用于测试集。训练环境为 2×NVIDIA RTX 3090，Python 3.10，PyTorch 2.4.0，Transformers 4.48.0，PEFT 0.14.0，Accelerate 1.0.1，bitsandbytes 0.43.3。Qwen 训练使用 `max_length=512`、epoch=3、per-device batch size=4、gradient accumulation=4、learning rate=2e-4、fp16，随机种子为 42。

## 4. 实验结果与分析

表 1 给出主实验测试集结果。LOSVER-Light Tag 取得最佳综合表现，F1=0.687276、ROC-AUC=0.760319、PR-AUC=0.757150。相比 Vanilla Qwen，它的 F1 提升 0.039916，ROC-AUC 提升 0.073366，PR-AUC 提升 0.077507，说明显式行级风险信号能够帮助模型更好地区分安全函数和漏洞函数。

**表 1 主实验测试集结果**

| 方法 | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|---|---:|---:|---:|---:|---:|---:|
| Metrics-Baseline | 0.463397 | 0.461113 | **0.996813** | 0.630544 | 0.560892 | 0.536395 |
| Vanilla Qwen | 0.572108 | 0.520874 | 0.854980 | 0.647360 | 0.686953 | 0.679643 |
| LOSVER-Light Tag | **0.648243** | **0.580858** | 0.841434 | **0.687276** | **0.760319** | **0.757150** |
| LOSVER-Light Tag+Prefix | 0.608346 | 0.544493 | 0.901992 | 0.679064 | 0.756535 | 0.750676 |

从混淆矩阵看，LOSVER-Light Tag 将 Vanilla Qwen 的 FP 从 987 降到 762，TN 从 490 提升到 715，说明 `<MOD>` 标签主要改善了误报控制。Tag+Prefix 的 Recall 达到 0.901992，但 FP 增加到 947，Precision 下降到 0.544493，说明风险行摘要过强时会放大启发式噪声。Metrics-Baseline 的 F1 为 0.630544，但 ROC-AUC 只有 0.560892，且 FP 高达 1462，说明代码度量能捕捉浅层信号，却难以可靠区分安全低层代码和真实漏洞。

表 2 给出 top-k 消融。`top_k=5` 在 F1、Accuracy 和 ROC-AUC 上表现最好。`top_k=3` 的 Recall 降到 0.805578，说明风险行过少会遗漏关键上下文；`top_k=8` 的 Recall 提升到 0.859761，但 Precision 降到 0.567298，说明更多风险行会引入噪声。

**表 2 top-k 消融实验结果**

| top_k | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|---:|---:|---:|---:|---:|---:|---:|
| 3 | 0.644583 | **0.581703** | 0.805578 | 0.675576 | 0.755472 | 0.753953 |
| 5 | **0.648243** | 0.580858 | 0.841434 | **0.687276** | **0.760319** | 0.757150 |
| 8 | 0.634334 | 0.567298 | **0.859761** | 0.683560 | 0.758302 | **0.757988** |

人工错例分析抽样检查了 24 个错误样本，其中 12 个漏报、12 个误报。漏报主要来自长函数、领域语义依赖和弱行级信号，如编解码器、页表遍历和虚拟机执行循环。误报主要来自错误处理、资源释放、I/O 解析、短包装函数和正常低层指针操作。这说明 LOSVER-Light 可以帮助模型聚焦可疑位置，但不能替代真正的跨行、跨函数和领域语义理解。

## 5. 局限性与未来工作

本文存在五点局限。第一，LOSVER-Light 不是原始 LOSVER 的完整复现，静态风险评分不能等价于 line-level modifiability localization。第二，实验主要在 Devign 上进行，结果不能直接外推到真实工程漏洞发现。第三，主实验使用单一随机种子 `seed=42`，尚未进行多种子显著性检验。第四，静态规则可能把正常错误处理、资源释放、I/O 和指针操作误标为高风险。第五，`max_length=512` 对长函数仍然有限，部分漏洞上下文可能被截断或稀释。

未来可以从五个方向改进：使用代码修改历史或弱监督标签训练学习式行级定位器；引入调用图、数据流切片或 inter-procedural semantic completion 补充跨函数语义；在 PrimeVul、Big-Vul 等数据集上做外部验证；使用多个随机种子报告均值、标准差和显著性检验；结合解释生成模型，让系统不仅输出漏洞概率，还输出可疑行和自然语言原因。

## 6. 结论

本文基于 LOSVER 的行级信号思想实现了轻量方法 LOSVER-Light，并在 Devign 函数级漏洞检测任务上完成了基线、主方法、消融和错例分析。实验表明，行级风险信号能够有效提升 Qwen2.5-Coder 的漏洞检测能力，其中 LOSVER-Light Tag 相比 Vanilla Qwen 在 F1、ROC-AUC 和 PR-AUC 上均有明显提升。消融结果说明风险行数量存在信息量与噪声之间的折中，`top_k=5` 是较合理设置。代码度量基线和人工错例分析也表明，函数级漏洞检测中确实存在浅层模式，但仅靠这些模式无法可靠完成任务。总体而言，LOSVER-Light 证明了显式局部代码信号对代码大模型漏洞检测具有实际帮助，同时也说明真实漏洞检测仍需要更强的跨函数上下文建模和解释能力。

## 参考文献

[1] Doha Nam, Jongmoon Baik. LOSVER: Line-Level Modifiability Signal-Guided Vulnerability Detection and Classification. ASE 2025 Research Papers. https://conf.researchr.org/details/ase-2025/ase-2025-papers/39/LOSVER-Line-Level-Modifiability-Signal-Guided-Vulnerability-Detection-and-Classifica

[2] Enhancing Vulnerability Detection via Inter-procedural Semantic Completion. ISSTA 2025 Research Papers. https://conf.researchr.org/details/issta-2025/issta-2025-papers/37/Enhancing-Vulnerability-Detection-via-Inter-procedural-Semantic-Completion

[3] Francesco Sovrano, Adam Bauer, Alberto Bacchelli. Large Language Models for In-File Vulnerability Localization Can Be “Lost in the End”. Proceedings of the ACM on Software Engineering, FSE 2025. https://doi.org/10.1145/3715758

[4] Niklas Risse, Jing Liu, Marcel Böhme. Top Score on the Wrong Exam: On Benchmarking in Machine Learning for Vulnerability Detection. ISSTA 2025 Research Papers. https://conf.researchr.org/details/issta-2025/issta-2025-papers/18/Top-Score-on-the-Wrong-Exam-On-Benchmarking-in-Machine-Learning-for-Vulnerability-De

[5] Felix Weissberg et al. LLM-based Vulnerability Discovery through the Lens of Code Metrics. ICSE 2026 Research Track. https://conf.researchr.org/details/icse-2026/icse-2026-research-track/57/LLM-based-Vulnerability-Discovery-through-the-Lens-of-Code-Metrics

[6] Towards Explainable Vulnerability Detection with Large Language Models. IEEE Transactions on Software Engineering, 2025. https://doi.org/10.1109/TSE.2025.3605442
