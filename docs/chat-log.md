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
