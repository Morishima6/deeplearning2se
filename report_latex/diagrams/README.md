# Mermaid 图源码

## LOSVER-Light 整体流程图

- Mermaid 源码：`report_latex/diagrams/losver_light_flow.mmd`
- 导出 PNG：`report_latex/imgs/final/method_flow.png`
- LaTeX 建议引用路径：`imgs/final/method_flow.png`

如果需要重新导出，可以使用 Mermaid CLI：

```bash
mmdc -i report_latex/diagrams/losver_light_flow.mmd -o report_latex/imgs/final/method_flow.png -b white -w 1800 -H 1050
```

或在 `report_latex/` 目录下执行：

```bash
mmdc -i diagrams/losver_light_flow.mmd -o imgs/final/method_flow.png -b white -w 1800 -H 1050
```
