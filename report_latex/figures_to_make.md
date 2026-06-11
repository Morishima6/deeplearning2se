# 需要手工制作并替换的报告图

LaTeX 文件 `report_latex/final_report.tex` 中已经用 `\figuretodo{...}` 标出占位位置。你可以先直接编译占位版；如果想让报告更精致，再按下面列表制作图片并替换占位框。

## 图 1：LOSVER-Light 整体流程图

- LaTeX 标签：`fig:method-flow`
- Mermaid 源码：`report_latex/diagrams/losver_light_flow.mmd`
- 已导出/建议路径：`report_latex/imgs/final/method_flow.png`
- 可选 gpt-image-2 prompt：`report_latex/diagrams/method_flow_image2_prompt.md`
- 可选 gpt-image-2 纯 prompt：`report_latex/diagrams/method_flow_image2_prompt.txt`
- 可选 gpt-image-2 输出路径：`report_latex/imgs/final/method_flow_image2.png`
- 建议内容：
  - CodeXGLUE/Devign 原始函数
  - 行级风险评分
  - top-k 风险行
  - Vanilla / Tag / Tag+Prefix 三种输入
  - Qwen2.5-Coder + QLoRA 分类器
  - 指标与错例分析

## 图 2：主实验指标对比图

- LaTeX 标签：`fig:main-results`
- 建议路径：`report_latex/imgs/final/main_results.png`
- 数据来源：`reports/tables/main_results.csv`
- 建议形式：分组柱状图。
- 横轴：Metrics-Baseline、Vanilla Qwen、LOSVER-Light Tag、LOSVER-Light Tag+Prefix。
- 纵轴：F1、ROC-AUC、PR-AUC。
- 需要字段：
  - `run`
  - `f1`
  - `roc_auc`
  - `pr_auc`
- 推荐处理：
  - 将 `run_losver_tag_seed42` 显示为 `LOSVER-Light Tag`。
  - 将 `run_losver_prefix_seed42` 显示为 `LOSVER-Light Tag+Prefix`。
  - 将 `run_vanilla_seed42` 显示为 `Vanilla Qwen`。
  - 将 `run_metrics_seed42` 显示为 `Metrics-Baseline`。
- 视觉建议：
  - 使用 3 组指标并排柱状图。
  - 重点高亮 `LOSVER-Light Tag`。
  - 在柱顶标出三位小数。

## 图 3：top-k 消融趋势图

- LaTeX 标签：`fig:topk-ablation`
- 建议路径：`report_latex/imgs/final/topk_ablation.png`
- 数据来源：`reports/tables/ablation_results.csv`
- 建议形式：折线图或柱状图。
- 横轴：top-k=3/5/8。
- 纵轴：F1、Precision、Recall。
- 需要字段：
  - `run`
  - `precision`
  - `recall`
  - `f1`
- 推荐处理：
  - 从 `run_losver_tag_topk3_seed42` 解析出 `top_k=3`。
  - 从 `run_losver_tag_seed42` 解析出 `top_k=5`。
  - 从 `run_losver_tag_topk8_seed42` 解析出 `top_k=8`。
- 视觉建议：
  - 用折线图展示 Precision、Recall、F1 三条曲线。
  - 用竖向淡色背景或标注突出 `top_k=5`。
  - 图注中说明 `top_k=5` 在 F1 上最佳，体现信息量与噪声折中。

## 图 4：人工错例类别分布图

- LaTeX 标签：`fig:error-analysis`
- 建议路径：`report_latex/imgs/final/error_analysis.png`
- 数据来源：`reports/tables/manual_error_summary.csv`
- 建议形式：水平柱状图。
- 内容：长函数、上下文依赖、错误处理误报、弱行级信号等类别数量。
- 需要字段：
  - `manual_category`
  - `count`
  - `description`
- 推荐处理：
  - 按 `count` 降序排序。
  - `manual_category` 可以映射为更短的中文标签，例如：
    - `error_or_resource_management_false_alarm` -> 错误/资源管理误报
    - `long_function_or_truncation` -> 长函数或截断
    - `control_flow_or_pointer_false_alarm` -> 控制流/指针误报
    - `io_or_parser_false_alarm` -> I/O 或解析器误报
    - `semantic_or_context_dependent_vulnerability` -> 上下文依赖漏洞
    - `weak_or_misleading_line_signal` -> 弱/误导性行信号
    - `benign_wrapper_or_accessor` -> 良性包装函数
    - `dangerous_api_missed_in_long_function` -> 长函数中危险 API 漏报
- 视觉建议：
  - 使用水平柱状图，左侧为类别名，右侧为数量。
  - 在每个柱尾标注 `count`。
  - 颜色可以按 false positive / false negative 大致区分，或统一使用一种稳重颜色。

## 替换方式

制作好图片后，把 `final_report.tex` 中对应的 `\figuretodo{...}` 替换为：

```latex
\begin{figure}[H]
    \centering
    \includegraphics[width=0.86\textwidth]{imgs/final/main_results.png}
    \caption{主实验指标对比图}
    \label{fig:main-results}
\end{figure}
```

其他图同理。
