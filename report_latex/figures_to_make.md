# 需要手工制作并替换的报告图

LaTeX 文件 `report_latex/final_report.tex` 中已经用 `\figuretodo{...}` 标出占位位置。你可以先直接编译占位版；如果想让报告更精致，再按下面列表制作图片并替换占位框。

## 图 1：LOSVER-Light 整体流程图

- LaTeX 标签：`fig:method-flow`
- 建议路径：`report_latex/imgs/final/method_flow.png`
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

## 图 3：top-k 消融趋势图

- LaTeX 标签：`fig:topk-ablation`
- 建议路径：`report_latex/imgs/final/topk_ablation.png`
- 数据来源：`reports/tables/ablation_results.csv`
- 建议形式：折线图或柱状图。
- 横轴：top-k=3/5/8。
- 纵轴：F1、Precision、Recall。

## 图 4：人工错例类别分布图

- LaTeX 标签：`fig:error-analysis`
- 建议路径：`report_latex/imgs/final/error_analysis.png`
- 数据来源：`reports/tables/manual_error_summary.csv`
- 建议形式：水平柱状图。
- 内容：长函数、上下文依赖、错误处理误报、弱行级信号等类别数量。

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
