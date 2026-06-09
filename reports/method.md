# 方法设计

本章介绍本文提出的 LOSVER-Light 方法。该方法受 ASE 2025 论文 LOSVER 的启发，核心思想是：函数级漏洞检测模型不应只被动读取完整函数，而应获得显式的局部代码信号，从而更容易关注潜在脆弱代码区域。考虑到课程项目的时间和复现成本，本文没有完整复现 LOSVER 原论文中的 line-level modifiability localization 阶段，而是设计了一个可复现、轻量级、无需额外标注的静态行级风险评分方法，并将其转化为 Qwen2.5-Coder 的输入提示。

## 1. 方法概览

LOSVER-Light 的整体流程包括四个步骤。

1. 对每个函数按行切分，并对每一行计算静态风险分数。
2. 按分数从高到低选择 top-k 风险行，默认 `top_k=5`。
3. 基于风险行构造不同输入形式，包括原始函数、行级标签输入和风险行摘要输入。
4. 使用 Qwen2.5-Coder-1.5B + 4-bit QLoRA 训练函数级二分类模型，并在验证集上选择最优 F1 阈值。

方法流程可以概括为：

```text
原始函数代码
  -> 按行切分
  -> 静态风险评分
  -> top-k 风险行选择
  -> 构造 text_vanilla / text_tag / text_tag_prefix
  -> Qwen2.5-Coder + QLoRA 二分类训练
  -> 验证集选阈值
  -> 测试集评估
```

相比直接将函数代码输入模型，LOSVER-Light 的关键区别在于它显式注入了“哪些行更值得关注”的先验。该先验不是人工标注，也不是测试标签泄露，而是由训练、验证和测试样本各自的代码文本独立计算得到，因此不会使用真实漏洞标签信息。

## 2. 行级风险评分

LOSVER-Light 将函数代码按换行符切分为若干代码行。对于每一行代码，方法根据静态启发式规则计算风险分数。评分规则关注软件漏洞检测中常见的局部风险模式，包括危险 API、指针/数组访问、复杂控制流、错误处理、I/O 或进程相关接口、长行、符号密度以及未检查的敏感调用。

具体来说，行级评分由以下几类信号组成。

**表 1 行级风险评分规则**

| 信号类型 | 触发条件 | 分数 | 设计动机 |
|---|---|---:|---|
| dangerous_api | 出现 `strcpy`、`memcpy`、`sprintf`、`gets`、`malloc`、`free` 等敏感 API | `3.0 + 0.5 * (命中数 - 1)` | 内存拷贝、字符串处理和手动内存管理常与漏洞相关 |
| pointer_or_array | 出现 `->`、`*`、`[`、`]` | `1.5` | 指针解引用和数组访问容易涉及越界、空指针或生命周期问题 |
| branch_or_loop | 出现 `if`、`else`、`for`、`while`、`switch`、`case`、`do` | `1.0` | 复杂控制流可能隐藏边界条件和状态依赖 |
| error_handling | 出现 `return`、`goto`、`NULL`、`errno`、`EINVAL`、`ENOMEM` | `0.8` | 错误处理路径常与资源释放和异常状态相关 |
| io_or_process_api | 出现 `system`、`popen`、`exec`、`open`、`read`、`write`、`recv`、`send` | `0.8` | I/O、进程和系统调用是安全敏感接口 |
| long_line | 去除空白后长度不少于 100 | `0.8` | 很长的代码行通常包含复杂表达式或多重操作 |
| medium_long_line | 去除空白后长度不少于 80 | `0.4` | 中等长行作为弱复杂度信号 |
| symbol_dense | 符号密度不少于 0.28 | `0.8` | 高符号密度常见于指针、宏、位运算和复杂表达式 |
| moderately_symbol_dense | 符号密度不少于 0.20 | `0.4` | 中等符号密度作为弱风险信号 |
| unchecked_sensitive_call | 命中危险 API 且该行缺少 `if`、`assert`、`return`、`NULL` 等检查相关 token | `0.7` | 未检查的敏感调用风险更高 |

每一行的最终分数是上述信号分数之和。空行直接赋值为 0，不参与风险行候选。得到所有候选行后，方法按 `(风险分数降序, 行号升序)` 排序，选取前 `top_k` 行作为风险行。排序时保留行号、分数、原始文本和触发原因，后续输入构造和错例分析都使用这些信息。

这一评分方法有两个特点。第一，它是透明的，所有风险来源都能回溯到具体行和具体规则。第二，它是轻量的，不需要额外训练一个行级定位模型，适合课程项目和有限算力条件下的可复现实验。但它也有明显局限：启发式规则只能捕捉表面风险模式，无法可靠理解跨函数数据流、项目级状态不变量和领域协议语义。

## 3. 输入构造

基于同一份预处理结果，本文构造三种输入字段，用于比较不同程度的行级信号注入。

### 3.1 Vanilla 输入

Vanilla 输入直接使用原始函数代码，不添加任何行级标记：

```text
text_vanilla = 原始函数代码
```

这一组作为现代代码大模型基线，用于衡量 Qwen2.5-Coder 在没有显式行级提示时的函数级漏洞检测能力。

### 3.2 Tag 输入

Tag 输入在 top-k 风险行前后加入 `<MOD>` 和 `</MOD>` 标记，其他代码行保持不变：

```text
普通代码行
<MOD> 高风险代码行 </MOD>
普通代码行
```

这种形式保留了风险行在原函数中的位置和上下文，只向模型提供局部关注提示。它是本文的主要 LOSVER-Light 方法，因为它最接近“在原始代码上下文中突出可疑行”的思想，不会额外打乱函数结构。

### 3.3 Tag+Prefix 输入

Tag+Prefix 输入在 Tag 输入前添加一个风险行摘要。摘要列出每条风险行的行号、风险分数、触发原因和行内容：

```text
Risk lines:
- L12 score=4.5 reasons=dangerous_api,pointer_or_array: memcpy(dst, src, len);
- L38 score=2.9 reasons=branch_or_loop,pointer_or_array: if (buf[i] == 0) {

原始函数代码，其中 top-k 风险行带有 <MOD> 标记
```

该输入形式更显式地告诉模型哪些行被启发式规则认为危险。设计它的目的不是默认认为它一定更好，而是检验“更强的风险提示”是否会进一步提升漏洞检测性能。后续实验表明，Prefix 形式虽然提高了召回率，但也引入了更多误报，说明风险提示过强时可能放大启发式规则噪声。

## 4. 代码度量基线

为了判断深度模型是否真正利用了代码语义，本文还构造了一个非深度学习基线。该基线不读取原始 token 序列，而是从函数和风险行中提取 15 个手工特征，再训练 Logistic Regression 分类器。

**表 2 Metrics-Baseline 特征**

| 特征 | 含义 |
|---|---|
| `num_lines` | 函数总行数 |
| `num_nonempty_lines` | 非空行数 |
| `num_chars` | 字符数 |
| `num_tokens` | 词法 token 数 |
| `num_unique_tokens` | 不同 token 数 |
| `avg_line_length` | 平均非空行长度 |
| `max_line_length` | 最大行长度 |
| `num_dangerous_api` | 敏感 API 出现次数 |
| `num_branch_loop` | 分支和循环关键字出现次数 |
| `num_pointer_array` | 指针和数组符号出现次数 |
| `num_error_handling` | 错误处理 token 出现次数 |
| `symbol_density` | 全函数符号密度 |
| `num_risk_lines` | 风险行数量 |
| `max_risk_score` | 最大风险行分数 |
| `avg_risk_score` | 平均风险行分数 |

模型使用 `StandardScaler` 标准化特征，再使用 `LogisticRegression(class_weight="balanced", solver="liblinear")` 训练。这个基线的作用不是追求最强性能，而是检验 Devign 函数级漏洞检测任务中浅层代码度量能达到什么水平。如果一个简单度量模型也能获得较高 F1，就说明数据中可能存在长度、复杂度、API 使用等浅层模式；如果它的 ROC-AUC 较低或误报严重，则说明这些浅层模式不足以形成可靠分类边界。

## 5. Qwen2.5-Coder + QLoRA 训练

深度学习模型采用 `Qwen/Qwen2.5-Coder-1.5B` 作为代码骨干模型，并使用 `AutoModelForSequenceClassification` 加二分类头完成函数级漏洞检测。由于直接全量微调 1.5B 参数模型成本较高，本文采用 4-bit QLoRA 进行参数高效微调。

量化配置如下：

```text
load_in_4bit = true
quant_type = nf4
double_quant = true
compute_dtype = float16
```

LoRA 配置如下：

```text
r = 16
alpha = 32
dropout = 0.05
target_modules = q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj
```

训练超参数如下：

**表 3 QLoRA 训练超参数**

| 参数 | 取值 |
|---|---|
| backbone | `Qwen/Qwen2.5-Coder-1.5B` |
| max_length | 512 |
| epochs | 3 |
| per-device train batch size | 4 |
| per-device eval batch size | 4 |
| gradient accumulation steps | 4 |
| learning rate | 0.0002 |
| weight decay | 0.01 |
| warmup ratio | 0.05 |
| mixed precision | fp16 |
| seed | 42 |
| evaluation strategy | 每个 epoch 在验证集评估 |
| best model metric | validation F1 |

训练时如果 tokenizer 没有 `pad_token`，则将 `pad_token` 设置为 `eos_token`。模型关闭 `use_cache`，并启用 gradient checkpointing 以降低显存占用。为了避免 QLoRA、gradient checkpointing 和 DDP 在双卡训练时出现 reentrant backward 冲突，gradient checkpointing 显式设置 `use_reentrant=False`。

## 6. 阈值选择与评估

模型输出漏洞类别的概率分数后，本文不直接使用固定阈值 0.5。具体做法是：

1. 在验证集上枚举 0.05 到 0.95 之间的阈值，步长为 0.005。
2. 对每个阈值计算验证集 F1。
3. 选择验证集 F1 最高的阈值。
4. 使用该阈值在测试集上计算 Accuracy、Precision、Recall、F1 和混淆矩阵。
5. 同时根据连续概率分数计算 ROC-AUC 和 PR-AUC。

这样做的原因是漏洞检测通常存在明显的 precision-recall trade-off。固定 0.5 阈值不一定能反映模型在实际报警场景中的最佳使用方式，而验证集选阈值可以更公平地比较不同模型的可用分类边界。所有方法都使用相同阈值选择策略，因此比较是统一的。

## 7. 与原始 LOSVER 的区别

本文方法是 LOSVER 思想的轻量化实现，而不是完整论文复现。两者主要区别如下。

**表 4 LOSVER 与 LOSVER-Light 对比**

| 维度 | 原始 LOSVER | 本文 LOSVER-Light |
|---|---|---|
| 行级信号来源 | line-level modifiability signal localization | 静态启发式风险评分 |
| 是否需要额外定位模型 | 需要 | 不需要 |
| 是否使用代码修改历史/行级可修改性建模 | 是原论文核心之一 | 否 |
| 下游任务 | 漏洞检测与分类 | 函数级漏洞二分类 |
| 输入增强方式 | 利用定位到的行级信号引导 PLM | 使用 `<MOD>` 标签和风险行摘要提示 Qwen |
| 复现目标 | 完整论文级系统 | 课程项目中的可复现轻量验证 |

这种简化是有意设计的。一方面，完整复现 LOSVER 需要更复杂的行级监督、定位模型和实验设置，超出课程项目周期；另一方面，本文关注的问题是“显式行级局部信号是否能帮助函数级漏洞检测”。因此，只要静态风险评分能够稳定地产生可解释的局部提示，就可以作为 LOSVER 核心思想的轻量实验载体。

需要强调的是，LOSVER-Light 的启发式风险行并不等价于真实漏洞行，也不等价于原论文中的 modifiability signal。它可能将正常的错误处理、资源释放、I/O 解析或低层指针操作标记为风险行，也可能漏掉依赖领域语义的真实漏洞。因此，本文在实验部分专门加入了 top-k 消融和人工错例分析，用来检验这种轻量信号的有效边界。

## 8. 方法小结

LOSVER-Light 的核心贡献不是提出复杂的新模型结构，而是在函数级漏洞检测中引入一个透明、可复现的行级风险提示机制。它将传统静态启发式规则与代码大模型微调结合起来：静态规则负责提供可解释的局部关注信号，Qwen2.5-Coder 负责从完整函数上下文中学习漏洞判别边界。这样的设计既保留了 LOSVER 论文“行级信号引导漏洞检测”的关键思想，又避免了完整复现带来的工程复杂度，适合在有限时间和有限算力条件下完成严谨的课程实验。
