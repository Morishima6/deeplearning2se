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
