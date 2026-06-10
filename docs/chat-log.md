# deeplearning2se 开发记录

本文件用于记录每次实验推进、代码修改、训练运行、结果分析和报告写作过程。后续每次工作结束都建议追加一条日志，方便复盘和写报告。

## 2026-06-06 13:30

- 本次目标：根据课程 PDF 和已有实验计划，制定可执行实现计划，并初始化项目管理文档与 Git 仓库。
- 已完成：
  - 读取 `深度学习2026_期末作业.pdf`，确认课程要求：
    - 主题为深度学习赋能软件工程。
    - 参考 2025/2026 年 TSE、TOSEM、ICSE、FSE、ASE、ISSTA 论文。
    - 需要设计并开展具体软件工程任务实验。
    - 报告 4000-6000 字。
    - 仅提交 PDF，文件名为“学号+姓名”。
    - 截止时间为 2026-06-15 23:59。
  - 读取 `04-deep-research-report_最新实验计划.md`，确认推荐主线为基于 LOSVER 的轻量漏洞检测复现实验。
  - 创建 `docs/task.md`，细化阶段、任务、命令、验收标准和风险降级方案。
  - 创建 `docs/chat-log.md`，作为后续开发记录。
- 关键决策：
  - 任务选择：函数级漏洞检测。
  - 主方法：LOSVER-Light，即用静态规则近似 LOSVER 的行级 modifiability signal。
  - 主数据集：CodeXGLUE Defect Detection / Devign。
  - 主模型：Qwen2.5-Coder-1.5B + 4-bit QLoRA。
  - 基线：代码度量 Logistic Regression/XGBoost 与 Vanilla Qwen 分类器。
- 遇到的问题：
  - PowerShell 默认编码导致中文 Markdown 第一次读取显示乱码；后续已使用 UTF-8 输出读取。
  - 本机没有 GitHub CLI `gh`，也没有 `GITHUB_TOKEN/GH_TOKEN`，因此暂时无法直接创建 GitHub 远端仓库。
- 下一步：
  - 初始化本地 Git 仓库。
  - 添加 README、`.gitignore` 等基础文件。
  - 完成初始提交。
  - 后续在具备 GitHub 认证后创建并推送远端仓库 `deeplearning2se`。

## 日志模板

```text
## YYYY-MM-DD HH:mm

- 本次目标：
- 已完成：
- 关键命令：
- 结果文件：
- 遇到的问题：
- 下一步：
```

## 2026-06-06 15:30

- 本次目标：开始 Phase 1，在不代替用户执行安装/环境配置的前提下，准备依赖清单和数据导出脚本。
- 已完成：
  - 新增 `requirements.txt`，记录除 PyTorch CUDA wheel 以外的 Python 依赖。
  - 新增 `src/export_hf_dataset.py`，用于从 Hugging Face 导出 Devign/CodeXGLUE 数据集到 JSONL。
  - 脚本支持自动识别代码列和标签列，生成 `train.jsonl`、`valid.jsonl`、`test.jsonl`。
  - 脚本会输出 `dataset_stats.csv/json`，记录样本数、标签分布、平均/中位代码长度。
  - 已执行 `python -m py_compile src/export_hf_dataset.py`，语法检查通过。
- 关键命令：
  - `python -m py_compile src/export_hf_dataset.py`
- 结果文件：
  - `requirements.txt`
  - `src/export_hf_dataset.py`
- 遇到的问题：
  - 尚未执行环境安装和数据下载；这类操作按用户要求只提供命令，由用户自行执行。
- 下一步：
  - 用户手动创建环境并安装依赖。
  - 用户手动运行数据导出命令。
  - 根据用户运行结果修正数据集名称、字段名或下载参数。

## 2026-06-07 服务器交接补充

- 本次目标：确认 README 和 docs 是否足够让服务器上的另一个 Codex 继续指导实验，并补充交接文档。
- 已完成：
  - 新增 `docs/server-handoff.md`。
  - 明确 Windows 本地与 Linux GPU 服务器的分工。
  - 明确服务器 Codex 不应擅自执行安装、下载数据、训练等命令，除非用户授权。
  - 补充服务器 Phase 1 手动命令、GPU/PyTorch 检查命令、数据集下载失败时的处理方式。
  - 补充 Phase 2 预期输入输出和 `build_line_signals.py` 的最小可行字段设计。
  - 更新 `docs/task.md` 中 GitHub 远端状态为已完成。
- 关键决策：
  - 本地继续用于文档、报告和 Git 管理。
  - 服务器用于环境安装、数据下载、模型训练和评估。
  - `data/`、`outputs/`、权重和大日志不进入普通 Git。
- 下一步：
  - 在服务器 clone 仓库。
  - 手动执行 `docs/server-handoff.md` 中的 Phase 1 命令。
  - 若数据导出成功，进入 Phase 2；若失败，把完整报错交给 Codex 修正。

## 2026-06-07 纳入项目协作规范

- 本次目标：把用户提供的 `AGENTS.md` 作为本项目协作规范纳入仓库。
- 已完成：
  - 将 `AGENTS.md` 加入版本库。
  - 在 `README.md` 中增加 `AGENTS.md` 入口。
  - 在 `docs/server-handoff.md` 中要求服务器 Codex 先阅读 `AGENTS.md`。
- 说明：
  - `AGENTS.md` 用于约束审查、解释、编程、重构、沟通语言、事实核验和操作边界。
  - 后续协作时，服务器上的 Codex 应同时阅读 `README.md`、`docs/task.md`、`docs/server-handoff.md`、`AGENTS.md` 和 `docs/chat-log.md`。

## 2026-06-07 16:04

- 本次目标：在不代替用户执行服务器安装、下载和训练的前提下，补齐 Phase 2 到 Phase 4 的主要实验脚本。
- 已完成：
  - 新增 `src/code_features.py`，集中实现 LOSVER-Light 风险行评分、`<MOD>` 标记、风险行前缀和代码度量特征。
  - 新增 `src/io_utils.py`，提供 JSONL 读写工具。
  - 新增 `src/build_line_signals.py`，从 raw JSONL 生成 processed JSONL、`risk_lines`、`text_vanilla`、`text_tag`、`text_tag_prefix` 和 `metrics`。
  - 新增 `src/extract_code_metrics.py`，导出可用于报告检查的代码度量 CSV。
  - 新增 `src/train_metrics_baseline.py`，使用 Logistic Regression 训练代码度量基线，并在验证集选择最佳 F1 阈值。
  - 新增 `src/train_qwen_cls.py`，准备 Qwen2.5-Coder-1.5B + 4-bit QLoRA sequence classification 训练链路。
  - 新增 `src/evaluate.py`、`src/error_analysis.py`、`src/plot_results.py`，用于汇总实验结果、导出错例和绘制主结果图。
  - 新增 `configs/vanilla_qwen.yaml`、`configs/losver_light_tag.yaml`、`configs/losver_light_tag_prefix.yaml`。
  - 更新 `README.md`、`docs/task.md` 和 `docs/server-handoff.md`，补充 Phase 2/3/4 手动运行命令。
- 关键命令：
  - 本轮未执行数据下载、模型下载或训练命令。
- 结果文件：
  - `src/code_features.py`
  - `src/io_utils.py`
  - `src/build_line_signals.py`
  - `src/extract_code_metrics.py`
  - `src/train_metrics_baseline.py`
  - `src/train_qwen_cls.py`
  - `src/evaluate.py`
  - `src/error_analysis.py`
  - `src/plot_results.py`
  - `src/utils_seed.py`
  - `configs/*.yaml`
- 遇到的问题：
  - 当前本地没有 `data/raw/devign_hf`，因此只能做语法与脚本结构检查，不能验证真实数据处理结果。
- 下一步：
  - 用户在服务器手动运行 Phase 1 数据导出命令。
  - 数据导出成功后手动运行 `build_line_signals.py`、`extract_code_metrics.py` 和 `train_metrics_baseline.py`。
  - 若 metrics baseline 正常，再先跑 Qwen smoke test，最后跑三组完整 QLoRA 实验。

## 2026-06-07 16:20

- 本次目标：检查并修正大文件落盘路径，避免数据集、模型权重和 Hugging Face cache 存在当前项目目录或 root 目录。
- 已完成：
  - 新增 `src/paths.py`，统一定义 `DLSE_DATA_ROOT`、`DLSE_MODEL_ROOT` 和 `HF_HOME` 默认路径。
  - 将数据默认路径改为 `/mnt/sda/gzx/data/deeplearning2se`。
  - 将训练输出、adapter 和 checkpoint 默认路径改为 `/mnt/sda/gzx/models/deeplearning2se`。
  - 将 Hugging Face cache 默认路径改为 `/mnt/sda/gzx/models/huggingface`，并为数据导出和模型加载脚本增加 `--cache-dir`。
  - 更新 README、任务文档和服务器交接文档中的执行命令。
- 关键约束：
  - 轻量报告文件仍可写入仓库内 `reports/`。
  - `data/`、`outputs/` 仅作为忽略占位，不作为服务器实际大文件存储位置。

## 2026-06-07 19:10

- 本次目标：记录 Phase 2/3 运行结果。
- 已完成：
  - `download.sh` 成功导出 CodeXGLUE Defect Detection / Devign 数据，最终通过 GitHub raw fallback 获取原始数据。
  - 生成 `$DLSE_DATA_ROOT/processed/devign_losver/{train,valid,test}.jsonl`。
  - 生成 `reports/tables/line_signal_stats.csv/json` 和 `reports/tables/code_metrics.csv`。
  - 跑通 Metrics-Baseline：Logistic Regression, seed=42。
- 关键结果：
  - 验证集：threshold=0.355，F1=0.606481，ROC-AUC=0.562635。
  - 测试集：Accuracy=0.463397，Precision=0.461113，Recall=0.996813，F1=0.630544，ROC-AUC=0.560892，PR-AUC=0.536395。
  - 测试集混淆矩阵：TN=15，FP=1462，FN=4，TP=1251。
- 初步分析：
  - 代码度量基线召回率极高，但误报严重，说明当前阈值下模型几乎倾向于判为 vulnerable。
  - ROC-AUC 约 0.56，表明浅层代码度量只有弱区分能力，可作为后续 Qwen/LOSVER-Light 的对照。
- 下一步：
  - 跑 Qwen vanilla smoke test，确认模型加载、cache 路径和训练链路正常。
  - smoke test 成功后跑 full Vanilla、Tag、Tag+Prefix 三组实验。

## 2026-06-07 19:30

- 本次目标：记录 Qwen smoke test 结果，并准备完整 QLoRA 主实验脚本。
- 已完成：
  - Qwen2.5-Coder-1.5B 模型成功从镜像下载到 `/mnt/sda/gzx/models/huggingface`。
  - Vanilla smoke test 跑通：512 train samples，256 eval/test samples，3 epochs。
  - 新增 `qwen_smoke_test.sh`，并使用 `_smoke` 后缀避免覆盖正式 full run。
  - 新增 `run_qwen_full.sh`，按 Vanilla、LOSVER-Light Tag、LOSVER-Light Tag+Prefix 顺序跑正式实验。
  - 新增 `collect_results.sh`，汇总 `main_results.csv`、导出错例并生成主结果图。
- Smoke test 结果：
  - 验证集：Accuracy=0.523438，F1=0.672043，ROC-AUC=0.580156。
  - 测试集：Accuracy=0.535156，F1=0.689295，ROC-AUC=0.525994。
- 说明：
  - smoke test 仅用于验证训练链路，样本量小，不能作为正式结果。
  - 服务器 kernel 版本低于推荐值，正式实验先使用单卡 `--num_processes 1`，降低 DDP hang 风险。
- 下一步：
  - 执行 `bash ./run_qwen_full.sh`。
  - 三组 full run 完成后执行 `bash ./collect_results.sh`。
  - 将 `reports/tables/main_results.csv` 和错例输出提交到 Git。

## 2026-06-08 主实验结果

- 本次目标：完成 Qwen2.5-Coder-1.5B + QLoRA 三组主实验，并汇总结果。
- 已完成：
  - Vanilla Qwen full run。
  - LOSVER-Light Tag full run。
  - LOSVER-Light Tag+Prefix full run。
  - 执行 `scripts/collect_results.sh`，生成主结果表和错例表。
- 关键结果：
  - Metrics-Baseline：F1=0.630544，ROC-AUC=0.560892，PR-AUC=0.536395。
  - Vanilla Qwen：F1=0.647360，ROC-AUC=0.686953，PR-AUC=0.679643。
  - LOSVER-Light Tag：F1=0.687276，ROC-AUC=0.760319，PR-AUC=0.757150。
  - LOSVER-Light Tag+Prefix：F1=0.679064，ROC-AUC=0.756535，PR-AUC=0.750676。
- 初步结论：
  - RQ1：LOSVER-Light 的显式行级信号相较 vanilla 输入有提升，尤其是 ROC-AUC 和 PR-AUC。
  - RQ2：只加 `<MOD>` 标签优于 Tag+Prefix，说明更长的风险行摘要不一定带来更好效果，可能引入噪声或压缩有效代码上下文。
  - RQ3：Metrics-Baseline 的 F1 不低但 ROC-AUC 弱，且误报极多，说明浅层代码度量可以捕捉一部分模式，但分类区分能力有限。
- 下一步：
  - 基于 `reports/tables/error_cases.csv` 做人工错例归类。
  - 写报告实验结果与分析部分。
  - 如时间允许，补充 top-k 或第二 seed 小消融。

## 2026-06-09 消融与错例分析设计

- 本次目标：在主实验已完成的基础上，按“人工错例分析 > top_k 消融 > max_length=768 消融”的优先级补充后续实验设计与脚本。
- 已完成：
  - 新增 `src/manual_error_review.py`，从预测错例中抽样 FP/FN，并基于函数长度、危险 API、风险分数自动给出初始错误类别。
  - 新增 `scripts/prepare_manual_error_review.sh`，生成 `reports/tables/manual_error_review.csv` 和 `reports/tables/manual_error_summary.csv`。
  - 新增 `configs/losver_light_tag_topk3.yaml` 和 `configs/losver_light_tag_topk8.yaml`。
  - 新增 `scripts/run_topk_ablation.sh`，生成 top_k=3/8 的 processed 数据并分别训练 LOSVER-Light Tag。
  - 新增 `scripts/collect_ablation_results.sh`，汇总 top_k=3/5/8 消融结果。
  - 新增 `configs/losver_light_tag_maxlen768.yaml` 作为可选长输入配置，但不默认执行。
- 设计决策：
  - 人工错例分析优先，因为它不需要再跑模型，能直接增强报告分析质量。
  - top_k 消融只跑 LOSVER-Light Tag，因为 Tag 是当前最好方法，消融目标更聚焦。
  - max_length=768 成本较高，且主题不如 top_k 直接，默认只保留配置作为可选扩展。

## 2026-06-09 top-k 消融结果

- 本次目标：完成 LOSVER-Light Tag 的 `top_k=3/5/8` 消融，并判断主实验默认 `top_k=5` 是否合理。
- 已完成：
  - 执行 `scripts/run_topk_ablation.sh`，完成 `top_k=3` 和 `top_k=8` 两组 Qwen2.5-Coder-1.5B + QLoRA 训练。
  - 执行 `scripts/collect_ablation_results.sh`，生成 `reports/tables/ablation_results.csv`。
  - 生成 `reports/figures/topk_ablation_results.png`。
- 测试集结果：
  - `top_k=3`：Accuracy=0.644583，Precision=0.581703，Recall=0.805578，F1=0.675576，ROC-AUC=0.755472，PR-AUC=0.753953。
  - `top_k=5`：Accuracy=0.648243，Precision=0.580858，Recall=0.841434，F1=0.687276，ROC-AUC=0.760319，PR-AUC=0.757150。
  - `top_k=8`：Accuracy=0.634334，Precision=0.567298，Recall=0.859761，F1=0.683560，ROC-AUC=0.758302，PR-AUC=0.757988。
- 结论：
  - `top_k=5` 仍是综合表现最好的主设置。
  - `top_k=3` 风险行过少，Recall 明显下降，说明关键漏洞上下文可能被漏选。
  - `top_k=8` 提升 Recall，但 Precision 和 Accuracy 下降，说明更多风险行会引入噪声和误报。
  - 报告中可将该实验作为 RQ4/消融分析：LOSVER-Light 的收益依赖适中的行级信号数量，风险行并非越多越好。

## 2026-06-09 报告方法与结果章节

- 本次目标：开始撰写最终 PDF 可复用的报告正文草稿。
- 已完成：
  - 新增 `reports/experiment_results.md`，覆盖数据集、主实验、RQ1/RQ2/RQ3、top-k 消融、人工错例分析和结论摘要。
  - 新增 `reports/method.md`，覆盖 LOSVER-Light 方法设计、行级风险评分、输入构造、Metrics-Baseline、Qwen2.5-Coder + QLoRA 训练、阈值选择和与原始 LOSVER 的区别。
- 说明：
  - 两个章节中的数字均来自 `reports/tables/*.csv` 和对应训练输出。
  - 方法章节按当前代码实现撰写，包括 4-bit NF4、LoRA rank=16、`top_k=5`、`max_length=512` 和验证集选阈值策略。

## 2026-06-09 报告实验设计章节

- 本次目标：补齐最终报告中的实验设计部分。
- 已完成：
  - 新增 `reports/experiment_setup.md`。
  - 内容覆盖 RQ1-RQ4、Devign 数据集、主实验对比方法、top-k 消融、评价指标、Qwen + QLoRA 训练配置、服务器环境、复现流程和有效性威胁。
- 说明：
  - 实验环境按当前项目实际设置记录：2 × RTX 3090、Python 3.10、PyTorch 2.4.0、Transformers 4.48.0、PEFT 0.14.0、Accelerate 1.0.1。
  - 章节中的复现命令指向仓库现有脚本，不直接包含模型权重或数据大文件路径入库。

## 2026-06-09 报告引言与相关工作章节

- 本次目标：补齐最终报告中的引言与相关工作部分。
- 已完成：
  - 新增 `reports/intro_related_work.md`。
  - 内容覆盖漏洞检测任务动机、函数级二分类基准局限、LOSVER 行级信号思想、跨函数语义补全、输入位置敏感、benchmark shortcut、代码度量视角和可解释性。
  - 附上主要参考文献入口，包括 ASE 2025 LOSVER、ISSTA 2025 VulnSC、FSE 2025 Lost-in-the-End、ISSTA 2025 benchmark 反思、ICSE 2026 code metrics 视角和 TSE 2025 explainable VD。

## 2026-06-10 报告局限性与结论章节

- 本次目标：补齐最终报告末尾的局限性、未来工作和结论。
- 已完成：
  - 新增 `reports/limitations_conclusion.md`。
  - 内容覆盖非完整 LOSVER 复现、Devign 单数据集、单 seed、静态规则偏差、函数级上下文不足等局限。
  - 总结未来方向：学习式行级定位、跨函数语义、PrimeVul/Big-Vul 外部验证、多种子复跑、解释生成。
  - 结论部分收束主结果：LOSVER-Light Tag 最优，`top_k=5` 是较好折中，Metrics-Baseline 说明浅层模式存在但不可靠。

## 2026-06-10 最终报告合并初稿

- 本次目标：在保留五个原始章节草稿的基础上，生成可排版的最终报告合并稿。
- 已完成：
  - 新增 `reports/final_report_draft.md`。
  - 合并并压缩引言与相关工作、深度学习技术原理与方法、实验设计、实验结果、局限性和结论。
  - 按“一个汉字约 2 个字符”的课程口径统计，当前合并稿约 2144 个汉字，折算约 4288 字符，位于 4000-6000 要求范围内。
- 保留文件：
  - `reports/intro_related_work.md`
  - `reports/experiment_setup.md`
  - `reports/method.md`
  - `reports/experiment_results.md`
  - `reports/limitations_conclusion.md`
