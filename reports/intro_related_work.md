# 引言与相关工作

## 1. 引言

软件漏洞检测是“深度学习赋能软件工程”中最具代表性的任务之一。传统静态分析方法通常依赖人工设计的规则、数据流分析和程序语义建模，优点是可解释、可控，但在真实软件系统中容易受到语言特性、项目规模、调用关系和误报率的影响。近年来，预训练语言模型和大语言模型被广泛用于代码理解任务，为漏洞检测提供了新的技术路径：模型可以从大规模代码语料中学习 API 使用模式、控制流结构、错误处理习惯和潜在缺陷模式，从而减少完全手写规则的成本。

然而，漏洞检测并不是普通文本分类任务。一个函数是否存在漏洞，往往取决于少数关键代码行、边界条件、资源生命周期、调用上下文或项目级不变量。函数级二分类数据集虽然便于训练和评估，但也会隐藏真实漏洞成因：模型只看到一个函数片段，却需要判断其中是否存在安全缺陷。在这种设置下，模型可能学习到一些表面相关模式，例如函数更长、指针更多、危险 API 更多、控制流更复杂，就更倾向于预测为漏洞。这样的模式有时有用，但并不等价于真正理解漏洞。

本文选择函数级漏洞检测作为课程项目任务，并以 ASE 2025 论文 LOSVER: Line-Level Modifiability Signal-Guided Vulnerability Detection and Classification 为主要方法来源。LOSVER 的核心观点是：漏洞检测模型不应只接收完整函数代码，还应获得显式的行级信号，使模型能够关注更可能与漏洞相关的位置。本文在有限时间和算力条件下实现一个轻量版本 LOSVER-Light：使用静态规则为每一行代码计算风险分数，选取 top-k 风险行，并将这些行以 `<MOD>` 标签或风险行摘要形式注入到 Qwen2.5-Coder 的输入中。

本文的实验目标不是完整复现 LOSVER 原论文，而是验证其核心思想在轻量实现中是否成立。具体而言，本文关注以下问题：第一，行级风险信号是否能提升函数级漏洞检测模型的性能；第二，行级信号应该以何种形式注入模型输入；第三，简单代码度量基线是否能解释一部分检测结果；第四，风险行数量是否存在信息量与噪声之间的折中。

本文的主要工作包括：

1. 设计并实现一个可复现的 LOSVER-Light 预处理流程，从函数代码中提取行级风险信号。
2. 使用 Qwen2.5-Coder-1.5B + 4-bit QLoRA 在 Devign 函数级漏洞检测数据集上训练 Vanilla、Tag 和 Tag+Prefix 三组模型。
3. 构造 Logistic Regression + 代码度量特征的非深度基线，用于分析浅层代码模式的影响。
4. 补充 top-k 消融实验和人工错例分析，解释行级信号的有效边界。

## 2. 学习式漏洞检测与函数级基准

学习式漏洞检测通常将代码片段映射为向量表示，再通过分类器判断其是否存在漏洞。早期方法多使用手工特征、图神经网络或代码预训练模型；近期研究则开始使用更大规模的代码语言模型和通用大语言模型。函数级二分类是其中最常见的实验设置：给定一个函数，预测它是否包含安全缺陷。这种形式工程上简单，便于构造 train/valid/test 划分，也便于报告 Accuracy、F1、AUC 等指标。

但函数级基准也受到越来越多质疑。ISSTA 2025 的 Top Score on the Wrong Exam: On Benchmarking in Machine Learning for Vulnerability Detection 指出，过去数年许多 ML4VD 工作都把漏洞检测简化为“给定函数是否存在安全缺陷”的二分类问题，但这种定义可能并不能充分衡量模型在真实漏洞检测中的能力。真实漏洞往往依赖跨函数调用、配置、补丁历史和运行时环境，而函数级标签容易让模型利用数据集偏差或 shortcut。

本文接受函数级二分类作为课程项目的实验载体，但不把它视为真实漏洞发现的完整替代。为避免只报告一个模型分数，本文加入了代码度量基线和人工错例分析：前者用于检查模型是否依赖函数长度、危险 API、指针操作等浅层模式；后者用于观察模型在长函数、错误处理、低层系统代码和领域语义场景中的失败原因。

## 3. 行级信号与漏洞定位

漏洞通常不是均匀分布在整个函数中的。即使一个函数被标记为 vulnerable，真正触发漏洞的代码往往只涉及少数关键行，例如未检查的缓冲区拷贝、错误的边界条件、异常路径中的资源释放、错误的指针生命周期或状态更新。因此，让模型知道“哪些行更值得关注”是一个自然的研究方向。

LOSVER 正是基于这一动机提出的。其题目中的 Line-Level Modifiability Signal-Guided 强调，漏洞检测模型可以由行级可修改性信号引导，而不是完全依赖模型自己在完整函数中搜索重要位置。本文保留这一核心思想，但将原论文中更复杂的 line-level modifiability localization 简化为静态风险评分。这样做的好处是可复现、无需额外行级标注、工程风险低；不足是启发式规则不能等价于真实漏洞行，也不能捕捉完整语义。

与 LOSVER 相关的另一个方向是文件内或行级漏洞定位。FSE 2025 的 Large Language Models for In-File Vulnerability Localization Can Be “Lost in the End” 研究了大语言模型在文件内漏洞定位中的位置敏感问题，指出模型处理长代码上下文时可能受到漏洞位置影响。这类研究说明，输入组织方式本身会影响模型检测和定位能力。本文的 Tag 与 Tag+Prefix 对比正是围绕这一问题展开：风险行提示应保留在原始上下文中，还是应被提前汇总到输入开头。

## 4. 跨函数语义与上下文不足

函数级漏洞检测的另一类挑战是上下文不足。很多漏洞并不能只靠单个函数片段判断。例如，某个参数是否已经被调用者检查、某个指针是否拥有所有权、某个缓冲区长度是否来自可信来源，都可能依赖跨函数语义。ISSTA 2025 的 Enhancing Vulnerability Detection via Inter-procedural Semantic Completion 强调了跨过程语义补全对漏洞检测的重要性，其核心动机是单个函数内部信息不足时，需要补充被调用函数或调用关系中的语义。

本文没有实现跨函数补全，而是明确将任务范围限制在函数级输入内。这一限制与 Devign 数据集设置一致，也使实验能够在课程周期内完成。但在方法设计和结果分析中，本文保留了这一局限：LOSVER-Light 的行级风险信号只能在函数内部产生作用，无法补全外部调用上下文。因此，当漏洞依赖编解码状态、页表遍历、虚拟机执行循环或项目级不变量时，模型仍可能出现漏报。

## 5. 代码度量、浅层模式与可解释性

近年来，研究者开始反思大模型漏洞检测是否真正理解了漏洞语义。ICSE 2026 的 LLM-based Vulnerability Discovery through the Lens of Code Metrics 从代码度量视角分析 LLM 漏洞检测，指出模型预测可能与传统代码度量存在较强相关性。当修改某些代码度量时，LLM 预测也可能随之变化。这类发现提醒我们：即使使用大模型，也不能默认认为模型一定学到了深层安全语义。

因此，本文将代码度量基线纳入实验设计。Metrics-Baseline 使用函数行数、字符数、token 数、危险 API 数量、指针数组访问、分支循环、错误处理和风险行统计等 15 个特征训练 Logistic Regression。它的作用不是追求最优性能，而是作为解释工具：如果简单度量模型表现接近深度模型，说明 benchmark 可能存在较强浅层模式；如果它误报严重、ROC-AUC 较低，则说明浅层特征虽然有信号，但不足以可靠完成漏洞检测。

漏洞检测的可解释性也很重要。TSE 2025 的 Towards Explainable Vulnerability Detection with Large Language Models 关注大语言模型漏洞检测解释能力，说明仅给出二分类结果不足以支持开发者使用。本文没有训练解释生成模型，但通过行级风险原因、风险行摘要和人工错例分类提高了实验可解释性。每个 `<MOD>` 行都保留触发原因，例如 dangerous_api、pointer_or_array、branch_or_loop 等，使报告能够分析模型为何被某类代码误导。

## 6. 本文定位

综合上述研究，本文将自身定位为一个 LOSVER 思想的课程级轻量复现实验，而不是完整论文级系统复现。与原始 LOSVER 相比，本文不训练额外的行级定位模型，也不使用代码修改历史建模行级可修改性；与跨函数语义补全方法相比，本文不引入调用图或被调用函数摘要；与可解释漏洞检测方法相比，本文不生成自然语言漏洞解释。本文的重点是验证一个更小但清晰的问题：当我们以简单、透明、可复现的方式提供行级风险提示时，现代代码大模型的函数级漏洞检测性能是否会提高。

这种定位有三个优点。

第一，它与课程要求中的“参考近两年高水平软件工程论文开展实验”相匹配。LOSVER 提供核心方法动机，FSE 2025 和 ISSTA 2025 相关工作提供输入组织、上下文不足和基准局限的讨论背景，ICSE 2026 的代码度量视角则支撑本文加入浅层基线。

第二，它工程上可落地。Qwen2.5-Coder-1.5B + 4-bit QLoRA 可以在 2×RTX 3090 上完成训练；静态风险评分和输入构造可以完全复现；所有实验结果都能通过 CSV、JSON 和脚本记录。

第三，它能产生可讨论的结果，而不是只追求单一最高分。本文不仅报告主实验结果，还分析 Tag 与 Prefix 的差异、top-k 风险行数量的折中、Metrics-Baseline 的误报问题，以及人工错例中的长函数、低层指针操作、错误处理和领域语义失败案例。这使实验更接近一个小型实证研究，而不是简单模型调用。

## 7. 参考文献入口

- Doha Nam, Jongmoon Baik. LOSVER: Line-Level Modifiability Signal-Guided Vulnerability Detection and Classification. ASE 2025 Research Papers. https://conf.researchr.org/details/ase-2025/ase-2025-papers/39/LOSVER-Line-Level-Modifiability-Signal-Guided-Vulnerability-Detection-and-Classifica
- Enhancing Vulnerability Detection via Inter-procedural Semantic Completion. ISSTA 2025 Research Papers. https://conf.researchr.org/details/issta-2025/issta-2025-papers/37/Enhancing-Vulnerability-Detection-via-Inter-procedural-Semantic-Completion
- Francesco Sovrano, Adam Bauer, Alberto Bacchelli. Large Language Models for In-File Vulnerability Localization Can Be “Lost in the End”. Proceedings of the ACM on Software Engineering, FSE 2025. https://doi.org/10.1145/3715758
- Niklas Risse, Jing Liu, Marcel Böhme. Top Score on the Wrong Exam: On Benchmarking in Machine Learning for Vulnerability Detection. ISSTA 2025 Research Papers. https://conf.researchr.org/details/issta-2025/issta-2025-papers/18/Top-Score-on-the-Wrong-Exam-On-Benchmarking-in-Machine-Learning-for-Vulnerability-De
- Felix Weissberg et al. LLM-based Vulnerability Discovery through the Lens of Code Metrics. ICSE 2026 Research Track. https://conf.researchr.org/details/icse-2026/icse-2026-research-track/57/LLM-based-Vulnerability-Discovery-through-the-Lens-of-Code-Metrics
- Towards Explainable Vulnerability Detection with Large Language Models. IEEE Transactions on Software Engineering, 2025. https://doi.org/10.1109/TSE.2025.3605442
